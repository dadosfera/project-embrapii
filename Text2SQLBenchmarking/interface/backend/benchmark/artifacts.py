"""Detecção e arquivamento seguro dos Parquets convencionais do Benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import os
from pathlib import Path
import shutil
from typing import Callable

from interface.backend.domain.artifacts import ArtifactKind, ArtifactValidationError
from interface.backend.domain.capabilities import (
    ApplicationMode,
    ConfigurationSelection,
    resolve_legacy_token,
    validate_configuration,
)
from interface.backend.storage.parquet_reader import read_parquet_artifact

from .models import ArtifactState, FileSnapshot


class BenchmarkArtifactError(Exception):
    public_message = "Os artefatos do Benchmark não puderam ser preparados."

    def __init__(self, code: str, internal_detail: str) -> None:
        super().__init__(self.public_message)
        self.code = code
        self.internal_detail = internal_detail


@dataclass(frozen=True)
class BenchmarkIdentity:
    configuration: ConfigurationSelection
    seed: int
    legacy_token: str

    @classmethod
    def create(cls, configuration: ConfigurationSelection, seed: int) -> "BenchmarkIdentity":
        valid = validate_configuration(configuration, ApplicationMode.BENCHMARK)
        if not valid.is_valid:
            raise BenchmarkArtifactError("INVALID_REQUEST", "configuração não validada")
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise BenchmarkArtifactError("INVALID_REQUEST", "seed incompatível")
        token = resolve_legacy_token(configuration.library, configuration.context)
        if not token.is_valid or token.value is None:
            raise BenchmarkArtifactError("INVALID_REQUEST", "token legado indisponível")
        return cls(configuration=configuration, seed=seed, legacy_token=token.value)


@dataclass(frozen=True)
class ArtifactPaths:
    generation: Path
    execution: Path
    generation_relative: str
    execution_relative: str


@dataclass(frozen=True)
class ArtifactInspection:
    state: ArtifactState
    generation: FileSnapshot
    execution: FileSnapshot
    invalid_reason: str | None = None


@dataclass(frozen=True)
class ArchiveResult:
    history_directory: str
    generation: FileSnapshot
    execution: FileSnapshot


@dataclass(frozen=True)
class ArchivePreflight:
    sources: tuple[Path, ...]
    history_root: Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class BenchmarkArtifactStore:
    """Resolve somente caminhos catalogados e nunca segue links simbólicos."""

    def __init__(self, resources_root: Path) -> None:
        self._root = resources_root.absolute()
        if self._root.is_symlink():
            raise BenchmarkArtifactError("ARCHIVE_ERROR", "raiz de recursos é link")

    @property
    def resources_root(self) -> Path:
        return self._root

    def paths_for(self, identity: BenchmarkIdentity) -> ArtifactPaths:
        config = identity.configuration
        directory = self._root / config.database / config.model_id
        generation_name = f"queries_geradas_{identity.legacy_token}_{identity.seed}.parquet"
        generation = directory / generation_name
        execution = directory / generation_name.replace(".parquet", "_executado.parquet")
        self._assert_safe(generation, allow_missing=True)
        self._assert_safe(execution, allow_missing=True)
        return ArtifactPaths(
            generation=generation,
            execution=execution,
            generation_relative=generation.relative_to(self._root).as_posix(),
            execution_relative=execution.relative_to(self._root).as_posix(),
        )

    def snapshot(self, path: Path) -> FileSnapshot:
        self._assert_safe(path, allow_missing=True)
        relative = path.relative_to(self._root).as_posix()
        if not path.exists():
            return FileSnapshot(relative, False, None, None, None)
        stat = path.stat()
        return FileSnapshot(relative, True, stat.st_size, stat.st_mtime_ns, _sha256(path))

    def inspect(self, identity: BenchmarkIdentity) -> ArtifactInspection:
        paths = self.paths_for(identity)
        generation = self.snapshot(paths.generation)
        execution = self.snapshot(paths.execution)
        try:
            if generation.exists:
                artifact = read_parquet_artifact(paths.generation)
                if artifact.metadata.kind is not ArtifactKind.GENERATION:
                    return ArtifactInspection(ArtifactState.INVALID_RESULT, generation, execution, "geração tem estágio incompatível")
            if execution.exists:
                artifact = read_parquet_artifact(paths.execution)
                if artifact.metadata.kind is not ArtifactKind.EXECUTED:
                    return ArtifactInspection(ArtifactState.INVALID_RESULT, generation, execution, "execução tem estágio incompatível")
        except ArtifactValidationError:
            return ArtifactInspection(ArtifactState.INVALID_RESULT, generation, execution, "Parquet inválido")
        if execution.exists and not generation.exists:
            return ArtifactInspection(ArtifactState.INVALID_RESULT, generation, execution, "execução sem geração")
        if execution.exists:
            return ArtifactInspection(ArtifactState.COMPLETE, generation, execution)
        if generation.exists:
            return ArtifactInspection(ArtifactState.GENERATION_ONLY, generation, execution)
        return ArtifactInspection(ArtifactState.NOT_STARTED, generation, execution)

    def archive_existing(
        self,
        identity: BenchmarkIdentity,
        *,
        now: Callable[[], datetime],
        expected_generation: FileSnapshot | None = None,
        expected_execution: FileSnapshot | None = None,
    ) -> ArchiveResult:
        paths = self.paths_for(identity)
        preflight = self.preflight_archive(
            identity,
            expected_generation=expected_generation,
            expected_execution=expected_execution,
        )
        sources = preflight.sources
        stamp = now().strftime("%Y%m%d_%H%M%S")
        destination = self._new_history_directory(preflight.history_root, stamp)
        moved: list[tuple[Path, Path]] = []
        try:
            for source in sources:
                target = destination / source.name
                if target.exists() or target.is_symlink():
                    raise BenchmarkArtifactError("ARCHIVE_ERROR", "destino histórico existente")
                os.replace(source, target)
                moved.append((source, target))
        except Exception as exc:
            for source, target in reversed(moved):
                try:
                    os.replace(target, source)
                except Exception:
                    pass
            try:
                destination.rmdir()
            except OSError:
                pass
            if isinstance(exc, BenchmarkArtifactError):
                raise
            raise BenchmarkArtifactError("ARCHIVE_ERROR", f"movimento falhou: {type(exc).__name__}") from exc
        return ArchiveResult(
            history_directory=destination.relative_to(self._root).as_posix(),
            generation=self.snapshot(destination / paths.generation.name),
            execution=self.snapshot(destination / paths.execution.name),
        )

    def preflight_archive(
        self,
        identity: BenchmarkIdentity,
        *,
        expected_generation: FileSnapshot | None = None,
        expected_execution: FileSnapshot | None = None,
    ) -> ArchivePreflight:
        """Valida fontes e destino antes de criar diretório ou mover arquivos."""

        paths = self.paths_for(identity)
        current_generation = self.snapshot(paths.generation)
        current_execution = self.snapshot(paths.execution)
        if (
            expected_generation is not None
            and current_generation != expected_generation
        ) or (
            expected_execution is not None
            and current_execution != expected_execution
        ):
            raise BenchmarkArtifactError(
                "REEXECUTION_STATE_CHANGED",
                "snapshot mudou imediatamente antes do arquivamento",
            )

        sources = tuple(path for path in (paths.generation, paths.execution) if path.exists())
        for source in sources:
            self._assert_safe(source, allow_missing=False)
            if not source.is_file():
                raise BenchmarkArtifactError("ARCHIVE_ERROR", "fonte não é arquivo regular")

        experiment_directory = paths.generation.parent
        self._assert_safe(experiment_directory, allow_missing=False)
        if not experiment_directory.is_dir() or not os.access(
            experiment_directory, os.W_OK | os.X_OK
        ):
            raise BenchmarkArtifactError("ARCHIVE_ERROR", "diretório sem permissão de escrita")

        history_root = experiment_directory / "history"
        self._assert_safe(history_root, allow_missing=True)
        if history_root.exists():
            if not history_root.is_dir() or not os.access(history_root, os.W_OK | os.X_OK):
                raise BenchmarkArtifactError("ARCHIVE_ERROR", "history indisponível para escrita")

        destination_device = experiment_directory.stat().st_dev
        if any(source.stat().st_dev != destination_device for source in sources):
            raise BenchmarkArtifactError("ARCHIVE_ERROR", "arquivamento cruzaria filesystems")
        try:
            available_space = shutil.disk_usage(experiment_directory).free
        except OSError as exc:
            raise BenchmarkArtifactError("ARCHIVE_ERROR", "espaço do filesystem indisponível") from exc
        if available_space <= 0:
            raise BenchmarkArtifactError("ARCHIVE_ERROR", "filesystem sem espaço para estrutura histórica")
        return ArchivePreflight(sources=sources, history_root=history_root)

    def _new_history_directory(self, history_root: Path, stamp: str) -> Path:
        self._assert_safe(history_root, allow_missing=True)
        try:
            history_root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise BenchmarkArtifactError("ARCHIVE_ERROR", "falha ao criar history") from exc
        self._assert_safe(history_root, allow_missing=False)
        index = 0
        while True:
            suffix = "" if index == 0 else f"_{index:02d}"
            candidate = history_root / f"{stamp}{suffix}"
            if not candidate.exists() and not candidate.is_symlink():
                try:
                    candidate.mkdir()
                except OSError as exc:
                    raise BenchmarkArtifactError("ARCHIVE_ERROR", "falha ao criar diretório timestampado") from exc
                return candidate
            index += 1

    def _assert_safe(self, path: Path, *, allow_missing: bool) -> None:
        try:
            relative = path.absolute().relative_to(self._root)
        except ValueError as exc:
            raise BenchmarkArtifactError("ARCHIVE_ERROR", "caminho fora da raiz") from exc
        current = self._root
        if current.exists() and current.is_symlink():
            raise BenchmarkArtifactError("ARCHIVE_ERROR", "raiz de recursos é link")
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise BenchmarkArtifactError("ARCHIVE_ERROR", "link simbólico não permitido")
        if not allow_missing and not path.exists():
            raise BenchmarkArtifactError("ARCHIVE_ERROR", "artefato ausente")
