from __future__ import annotations

import errno
import json
import sqlite3
import subprocess

from interface.backend.benchmark import BenchmarkIdentity, BenchmarkJournal
from interface.backend.benchmark.models import BenchmarkErrorCode, BenchmarkJobState
from interface.backend.tests.adapter_support import configuration
from interface.backend.tests.test_benchmark_service import _setup


def _subprocess_error(stderr: str) -> subprocess.CalledProcessError:
    return subprocess.CalledProcessError(
        1,
        ["python", "synthetic-runner.py"],
        output="token=stdout-secret /srv/private/stdout",
        stderr=stderr,
    )


def _write_generation(runners) -> None:
    runners.generation(BenchmarkIdentity.create(configuration(), 42))
    runners.calls.clear()


def _transformers_generation_error(root: BaseException) -> BaseException:
    generation_error_type = type(
        "GenerationError",
        (RuntimeError,),
        {"__module__": "transformers.generation.utils"},
    )
    try:
        raise root
    except BaseException as cause:
        try:
            raise generation_error_type("generation failed") from cause
        except BaseException as error:
            return error


def test_generation_subprocess_enospc_without_loading_provenance_is_generation_error(tmp_path):
    service, _, _, runners, _ = _setup(tmp_path)
    runners.error = _subprocess_error("OSError: [Errno 28] No space left on device")
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.state is BenchmarkJobState.FAILED
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.SQL_GENERATION_ERROR
    assert "espaço suficiente em disco" in snapshot.error.message
    assert "Benchmark" in snapshot.error.message


def test_generation_subprocess_cuda_oom_without_loading_provenance_is_generation_error(tmp_path):
    service, _, _, runners, _ = _setup(tmp_path)
    runners.error = _subprocess_error("torch.cuda.OutOfMemoryError: CUDA out of memory")
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.SQL_GENERATION_ERROR
    assert "memória suficiente na GPU" in snapshot.error.message
    assert "Benchmark" in snapshot.error.message


def test_generation_subprocess_generic_is_sql_generation_error(tmp_path):
    service, _, _, runners, _ = _setup(tmp_path)
    runners.error = _subprocess_error("RuntimeError: generation failed")
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.SQL_GENERATION_ERROR
    assert "stderr" not in snapshot.error.message.lower()


def test_generation_direct_enospc_is_generation_error_not_archive_error(tmp_path):
    service, _, _, runners, _ = _setup(tmp_path)
    runners.error = OSError(errno.ENOSPC, "synthetic")
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.SQL_GENERATION_ERROR
    assert snapshot.error.retryable is True


def test_generation_enospc_with_model_loading_provenance_is_model_load_error(tmp_path):
    service, _, _, runners, _ = _setup(tmp_path)
    runners.error = _subprocess_error(
        "snapshot_download: OSError: [Errno 28] No space left on device"
    )
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.MODEL_LOAD_ERROR
    assert "baixar ou carregar" in snapshot.error.message


def test_generation_cuda_oom_with_model_loading_provenance_is_model_load_error(tmp_path):
    service, _, _, runners, _ = _setup(tmp_path)
    runners.error = _subprocess_error(
        "from_pretrained: torch.cuda.OutOfMemoryError: CUDA out of memory"
    )
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.MODEL_LOAD_ERROR
    assert "carregar este modelo" in snapshot.error.message


def test_transformers_generation_cuda_oom_is_not_model_loading_provenance(tmp_path):
    service, _, _, runners, _ = _setup(tmp_path)
    runners.error = _transformers_generation_error(RuntimeError("CUDA out of memory"))
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.SQL_GENERATION_ERROR
    assert snapshot.error.message == (
        "Não há memória suficiente na GPU para concluir a geração do Benchmark."
    )


def test_transformers_generation_enospc_is_not_model_loading_provenance(tmp_path):
    service, _, _, runners, _ = _setup(tmp_path)
    runners.error = _transformers_generation_error(
        OSError(errno.ENOSPC, "No space left on device")
    )
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.SQL_GENERATION_ERROR
    assert snapshot.error.message == (
        "Não há espaço suficiente em disco para concluir a geração do Benchmark. "
        "Libere espaço no servidor e tente novamente."
    )


def test_generation_postgresql_connection_failure_is_database_error(tmp_path):
    service, _, _, runners, _ = _setup(tmp_path)
    runners.error = _subprocess_error("could not connect to server: Connection refused")
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.DATABASE_CONNECTION_ERROR


def test_generation_textual_sqlstate_class_08_is_database_error(tmp_path):
    service, _, _, runners, _ = _setup(tmp_path)
    runners.error = _subprocess_error("psycopg failure (SQLSTATE 08006)")
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.DATABASE_CONNECTION_ERROR


def test_generation_generic_network_without_hugging_face_provenance_is_generation_error(tmp_path):
    service, _, _, runners, _ = _setup(tmp_path)
    runners.error = _subprocess_error("Temporary failure in name resolution")
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.SQL_GENERATION_ERROR
    assert "baixar" not in snapshot.error.message.lower()


def test_generation_hugging_face_repository_errors_remain_model_load_error(tmp_path):
    for index, error_name in enumerate(("RepositoryNotFoundError", "GatedRepoError")):
        service, _, _, runners, _ = _setup(tmp_path / str(index))
        runners.error = _subprocess_error(f"huggingface_hub.errors.{error_name}: synthetic")
        snapshot = service.run(configuration(), seed=42)
        assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.MODEL_LOAD_ERROR
        assert snapshot.error.retryable is False


def test_generation_arbitrary_entry_not_found_type_is_not_model_load_error(tmp_path):
    arbitrary_error = type(
        "EntryNotFoundError",
        (RuntimeError,),
        {"__module__": "arbitrary.package"},
    )("missing")
    service, _, _, runners, _ = _setup(tmp_path)
    runners.error = arbitrary_error
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.SQL_GENERATION_ERROR


def test_execution_subprocess_database_connection_error(tmp_path):
    service, _, _, runners, _ = _setup(tmp_path)
    _write_generation(runners)
    runners.execution_error = _subprocess_error("could not connect to server: Connection refused")
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.DATABASE_CONNECTION_ERROR


def test_execution_subprocess_timeout(tmp_path):
    service, _, _, runners, _ = _setup(tmp_path)
    _write_generation(runners)
    runners.execution_error = _subprocess_error("canceling statement due to statement timeout")
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.QUERY_TIMEOUT


def test_execution_subprocess_syntax_and_generic_are_separate(tmp_path):
    first, _, _, first_runners, _ = _setup(tmp_path / "syntax")
    _write_generation(first_runners)
    first_runners.execution_error = _subprocess_error('syntax error at or near "FROM"')
    syntax = first.run(configuration(), seed=42)
    assert syntax.error and syntax.error.code is BenchmarkErrorCode.SQL_SYNTAX_ERROR

    second, _, _, second_runners, _ = _setup(tmp_path / "generic")
    _write_generation(second_runners)
    second_runners.execution_error = _subprocess_error("unexpected executor failure")
    generic = second.run(configuration(), seed=42)
    assert generic.error and generic.error.code is BenchmarkErrorCode.QUERY_EXECUTION_ERROR


def test_journal_persists_only_public_error_and_recovers_old_payload_without_retryable(tmp_path):
    service, _, journal, runners, _ = _setup(tmp_path)
    runners.error = _subprocess_error("token=secret /srv/private generation failed")
    snapshot = service.run(configuration(), seed=42)

    with sqlite3.connect(journal._path) as connection:
        raw = connection.execute(
            "SELECT payload FROM benchmark_jobs WHERE job_id = ?",
            (snapshot.job_id,),
        ).fetchone()[0]
        payload = json.loads(raw)
        assert set(payload["error"]) == {"code", "message", "retryable"}
        assert all(value not in raw for value in ("secret", "/srv/private", "stderr", "stdout"))

        payload["error"].pop("retryable")
        connection.execute(
            "UPDATE benchmark_jobs SET payload = ? WHERE job_id = ?",
            (json.dumps(payload), snapshot.job_id),
        )

    recovered = BenchmarkJournal(journal._path).get(snapshot.job_id)
    assert recovered.error and isinstance(recovered.error.retryable, bool)
