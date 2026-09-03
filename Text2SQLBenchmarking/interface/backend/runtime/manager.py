"""Gerenciamento síncrono de um único adapter carregado."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from numbers import Real
from pathlib import Path
from time import monotonic
from typing import Callable, Protocol

from interface.backend.diagnostics import log_runtime_event
from interface.backend.adapters.base import BaseGeneratorAdapter
from interface.backend.adapters.factory import create_adapter
from interface.backend.adapters.paths import project_root as default_project_root
from interface.backend.adapters.workspace import RuntimeWorkspace, WorkspaceLifecycleOwner
from interface.backend.runtime.key import RuntimeKey
from interface.backend.runtime.workspace_cleanup import cleanup_backend_workspace


class RuntimeState(str, Enum):
    EMPTY = "EMPTY"
    LOADING = "LOADING"
    READY = "READY"
    RELEASING = "RELEASING"
    FAILED = "FAILED"


class RuntimeManagerErrorCode(str, Enum):
    RUNTIME_LOAD_ERROR = "RUNTIME_LOAD_ERROR"
    RUNTIME_RELEASE_ERROR = "RUNTIME_RELEASE_ERROR"
    RUNTIME_CLEANUP_ERROR = "RUNTIME_CLEANUP_ERROR"
    RUNTIME_TOKEN_MISMATCH = "RUNTIME_TOKEN_MISMATCH"
    RUNTIME_UNAVAILABLE = "RUNTIME_UNAVAILABLE"


class RuntimeManagerError(RuntimeError):
    """Erro de domínio seguro para operações de ciclo de vida."""

    def __init__(
        self,
        code: RuntimeManagerErrorCode,
        public_message: str,
        internal_detail: str,
    ) -> None:
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message
        self.internal_detail = internal_detail


class ManagedAdapter(Protocol):
    workspace: RuntimeWorkspace

    def load(self) -> None: ...

    def release(self) -> None: ...


AdapterFactory = Callable[[RuntimeKey, RuntimeWorkspace, str | None], ManagedAdapter]
WorkspaceFactory = Callable[[], RuntimeWorkspace]
WorkspaceCleanup = Callable[[RuntimeWorkspace], None]
MonotonicClock = Callable[[], float]


def _default_workspace_factory() -> RuntimeWorkspace:
    return RuntimeWorkspace.create(project_root=default_project_root())


def _default_adapter_factory(
    key: RuntimeKey,
    workspace: RuntimeWorkspace,
    hf_token: str | None,
) -> BaseGeneratorAdapter:
    return create_adapter(
        key.configuration,
        key.mode,
        random_seed=key.random_seed,
        hf_token=hf_token,
        workspace=workspace,
    )


@dataclass
class _LoadedRuntime:
    key: RuntimeKey
    adapter: ManagedAdapter | None
    workspace: RuntimeWorkspace | None
    adapter_released: bool = False
    workspace_cleaned: bool = False


class ModelManager:
    """Retém no máximo um runtime e libera somente por chamada explícita.

    A serialização do uso fica a cargo do coordenador operacional, pois a
    operação real de adapter muda o cwd.
    """

    def __init__(
        self,
        *,
        adapter_factory: AdapterFactory = _default_adapter_factory,
        workspace_factory: WorkspaceFactory = _default_workspace_factory,
        clock: MonotonicClock = monotonic,
        workspace_cleanup: WorkspaceCleanup = cleanup_backend_workspace,
        ttl_seconds: float = 600.0,
    ) -> None:
        if (
            isinstance(ttl_seconds, bool)
            or not isinstance(ttl_seconds, Real)
            or not math.isfinite(ttl_seconds)
            or ttl_seconds < 0
        ):
            raise ValueError("ttl_seconds deve ser um número finito não negativo")
        self._adapter_factory = adapter_factory
        self._workspace_factory = workspace_factory
        self._clock = clock
        self._workspace_cleanup = workspace_cleanup
        self._ttl_seconds = ttl_seconds
        self._state = RuntimeState.EMPTY
        self._runtime: _LoadedRuntime | None = None
        self._last_used: float | None = None

    @property
    def state(self) -> RuntimeState:
        return self._state

    @property
    def current_key(self) -> RuntimeKey | None:
        return self._runtime.key if self._runtime else None

    @property
    def last_used(self) -> float | None:
        return self._last_used

    @property
    def adapter(self) -> ManagedAdapter | None:
        return self._runtime.adapter if self._runtime else None

    def mark_used(self) -> None:
        """Reinicia o marco de inatividade após uma operação concluída.

        Deve ser chamado sob exclusão global depois de geração, Chat ou
        Benchmark. O método não inicia trabalho, thread ou timer.
        """

        if self._state is not RuntimeState.READY or self._runtime is None:
            raise RuntimeManagerError(
                RuntimeManagerErrorCode.RUNTIME_UNAVAILABLE,
                "Não há runtime carregado para atualizar.",
                "mark_used sem runtime READY",
            )
        self._last_used = self._clock()

    def get_or_load(self, key: RuntimeKey, *, hf_token: str | None) -> ManagedAdapter:
        """Obtém runtime igual ou troca-o por uma nova chave canônica."""

        if not key.matches_token(hf_token):
            raise RuntimeManagerError(
                RuntimeManagerErrorCode.RUNTIME_TOKEN_MISMATCH,
                "A configuração do runtime não é válida.",
                "fingerprint de token divergente",
            )
        if self._state is RuntimeState.READY and self._runtime is not None:
            if self._runtime.key == key:
                self._last_used = self._clock()
                return self._runtime.adapter
            log_runtime_event("runtime.switch.begin", key=key)
            self._release_current()
        elif self._state is RuntimeState.FAILED:
            # Uma falha cuja compensação terminou não pode inutilizar o
            # processo. FAILED só permanece quando há resíduo rastreável.
            if self._runtime is None:
                self._state = RuntimeState.EMPTY
            else:
                raise RuntimeManagerError(
                    RuntimeManagerErrorCode.RUNTIME_UNAVAILABLE,
                    "O runtime anterior precisa de recuperação antes de nova carga.",
                    "runtime FAILED com resíduo de load/release anterior",
                )

        return self._load_new(key, hf_token)

    def _load_new(self, key: RuntimeKey, hf_token: str | None) -> ManagedAdapter:
        self._state = RuntimeState.LOADING
        workspace: RuntimeWorkspace | None = None
        adapter: ManagedAdapter | None = None
        stage = "workspace_create"
        try:
            log_runtime_event("runtime.new_workspace.begin", stage=stage, key=key)
            workspace = self._workspace_factory()
            log_runtime_event("runtime.new_workspace.end", stage=stage, key=key)
            stage = "adapter_create"
            log_runtime_event("runtime.adapter_create.begin", stage=stage, key=key)
            adapter = self._adapter_factory(key, workspace, hf_token)
            log_runtime_event("runtime.adapter_create.end", stage=stage, key=key)
            stage = "adapter_load"
            log_runtime_event("runtime.adapter_load.begin", stage=stage, key=key)
            adapter.load()
            log_runtime_event("runtime.adapter_load.end", stage=stage, key=key)
        except Exception as exc:
            log_runtime_event("runtime.load.failed", stage=stage, exception=exc, key=key)
            self._last_used = None
            cleanup_failures, residual = self._cleanup_failed_load(adapter, workspace, key=key)
            self._runtime = residual
            self._state = RuntimeState.FAILED if residual is not None else RuntimeState.EMPTY
            detail = [f"stage={stage}", f"exception={type(exc).__name__}", *cleanup_failures]
            raise RuntimeManagerError(
                RuntimeManagerErrorCode.RUNTIME_LOAD_ERROR,
                "Não foi possível carregar o runtime selecionado.",
                "; ".join(detail),
            ) from exc

        self._runtime = _LoadedRuntime(key=key, adapter=adapter, workspace=workspace)
        self._last_used = self._clock()
        self._state = RuntimeState.READY
        return adapter

    def _cleanup_failed_load(
        self,
        adapter: ManagedAdapter | None,
        workspace: RuntimeWorkspace | None,
        *,
        key: RuntimeKey,
    ) -> tuple[tuple[str, ...], _LoadedRuntime | None]:
        """Compensa um load falho sem perder resíduos recuperáveis."""

        adapter_released = adapter is None
        failures: list[str] = []
        if adapter is not None:
            try:
                log_runtime_event("runtime.release.begin", stage="failed_load_release", key=key)
                adapter.release()
                adapter_released = True
                log_runtime_event("runtime.release.end", stage="failed_load_release", key=key)
            except Exception as exc:
                failures.append(f"release={type(exc).__name__}")
                log_runtime_event("runtime.release.failed", stage="failed_load_release", exception=exc, key=key)
        workspace_cleaned = workspace is None or (
            workspace is not None
            and workspace.lifecycle_owner is WorkspaceLifecycleOwner.CALLER
        )
        if workspace is not None and not workspace_cleaned:
            try:
                log_runtime_event("runtime.workspace_cleanup.begin", stage="failed_load_cleanup", key=key)
                self._workspace_cleanup(workspace)
                workspace_cleaned = True
                log_runtime_event("runtime.workspace_cleanup.end", stage="failed_load_cleanup", key=key)
            except Exception as exc:
                failures.append(f"cleanup={type(exc).__name__}")
                log_runtime_event("runtime.workspace_cleanup.failed", stage="failed_load_cleanup", exception=exc, key=key)

        if adapter_released and workspace_cleaned:
            return tuple(failures), None
        return tuple(failures), _LoadedRuntime(
            key=key,
            adapter=None if adapter_released else adapter,
            workspace=None if workspace_cleaned else workspace,
            adapter_released=adapter_released,
            workspace_cleaned=workspace_cleaned,
        )

    def _release_current(self) -> None:
        runtime = self._runtime
        self._last_used = None
        if runtime is None:
            self._state = RuntimeState.EMPTY
            return

        self._state = RuntimeState.RELEASING
        release_error: Exception | None = None
        cleanup_error: Exception | None = None
        if runtime.adapter is not None and not runtime.adapter_released:
            try:
                log_runtime_event("runtime.release.begin", stage="runtime_release", key=runtime.key)
                runtime.adapter.release()
                log_runtime_event("runtime.release.end", stage="runtime_release", key=runtime.key)
            except Exception as exc:
                release_error = exc
                log_runtime_event("runtime.release.failed", stage="runtime_release", exception=exc, key=runtime.key)
            finally:
                if release_error is None:
                    runtime.adapter_released = True
                    runtime.adapter = None

        if (
            runtime.workspace is not None
            and runtime.workspace.lifecycle_owner is WorkspaceLifecycleOwner.BACKEND
            and not runtime.workspace_cleaned
        ):
            try:
                log_runtime_event("runtime.workspace_cleanup.begin", stage="runtime_cleanup", key=runtime.key)
                self._workspace_cleanup(runtime.workspace)
                runtime.workspace_cleaned = True
                log_runtime_event("runtime.workspace_cleanup.end", stage="runtime_cleanup", key=runtime.key)
            except Exception as exc:
                cleanup_error = exc
                log_runtime_event("runtime.workspace_cleanup.failed", stage="runtime_cleanup", exception=exc, key=runtime.key)
            finally:
                if cleanup_error is None:
                    runtime.workspace = None

        if release_error is None and cleanup_error is None:
            self._runtime = None
            self._state = RuntimeState.EMPTY
        else:
            self._runtime = runtime
            self._state = RuntimeState.FAILED
        if release_error is not None:
            raise RuntimeManagerError(RuntimeManagerErrorCode.RUNTIME_RELEASE_ERROR, "Não foi possível liberar completamente o runtime anterior.", f"falha no release: {type(release_error).__name__}") from release_error
        if cleanup_error is not None:
            raise RuntimeManagerError(RuntimeManagerErrorCode.RUNTIME_CLEANUP_ERROR, "Não foi possível limpar o ambiente isolado do runtime.", f"falha de limpeza: {type(cleanup_error).__name__}") from cleanup_error

    def expire_if_idle(self) -> bool:
        """Libera somente quando chamado explicitamente e o TTL venceu."""

        if self._state is not RuntimeState.READY or self._last_used is None:
            return False
        if self._clock() - self._last_used < self._ttl_seconds:
            return False
        self._release_current()
        return True

    def shutdown(self) -> None:
        """Libera o runtime atual; chamadas após sucesso são no-op."""

        self._release_current()
