"""Integração mínima entre exclusão global e ciclo de vida do runtime."""

from __future__ import annotations

from typing import Callable, Protocol, TypeVar, runtime_checkable

from interface.backend.adapters.base import GenerationResult
from interface.backend.operations.coordinator import OperationCoordinator, OperationType
from interface.backend.runtime.key import RuntimeKey
from interface.backend.runtime.manager import ManagedAdapter, ModelManager


@runtime_checkable
class GenerativeAdapter(ManagedAdapter, Protocol):
    def generate(self, question: str) -> GenerationResult: ...


T = TypeVar("T")


class ExclusiveOperationService:
    """Entrada operacional que mantém ModelManager sob exclusão por processo.

    Oferece chamadas internas para que Chat, Benchmark e operações de lifecycle
    não contornem a exclusão global.
    """

    def __init__(self, manager: ModelManager, coordinator: OperationCoordinator) -> None:
        self._manager = manager
        self._coordinator = coordinator

    @property
    def coordinator(self) -> OperationCoordinator:
        return self._coordinator

    def ensure_runtime_loaded(
        self,
        key: RuntimeKey,
        *,
        hf_token: str | None,
    ) -> None:
        """Carrega ou reutiliza o runtime sem expor o adapter ao chamador."""

        def run() -> None:
            self._manager.get_or_load(key, hf_token=hf_token)

        self._coordinator.execute(OperationType.LOAD_RUNTIME, run)

    def generate(
        self,
        key: RuntimeKey,
        *,
        hf_token: str | None,
        question: str,
    ) -> GenerationResult:
        """Gera sob uma única posse, incluindo eventual carga do runtime."""

        def run() -> GenerationResult:
            adapter = self._manager.get_or_load(key, hf_token=hf_token)
            if not isinstance(adapter, GenerativeAdapter):
                raise TypeError("adapter carregado não suporta geração")
            result = adapter.generate(question)
            self._manager.mark_used()
            return result

        return self._coordinator.execute(OperationType.GENERATE, run)

    def _execute_with_runtime(
        self,
        operation: OperationType,
        key: RuntimeKey,
        *,
        hf_token: str | None,
        callback: Callable[[ManagedAdapter], T],
    ) -> T:
        """Base interna para serviços concretos de SQL e Benchmark.

        O callback só pode usar o adapter durante esta chamada. Nem ele nem o
        retorno podem expor ou reter o adapter fora da exclusão; esta função
        não é um contrato para a camada HTTP.
        """

        if operation not in (OperationType.CHAT, OperationType.EXECUTE_SQL, OperationType.BENCHMARK):
            raise ValueError("operação não suporta execução com runtime")

        def run() -> T:
            adapter = self._manager.get_or_load(key, hf_token=hf_token)
            result = callback(adapter)
            self._manager.mark_used()
            return result

        return self._coordinator.execute(operation, run)

    def run_chat(
        self, key: RuntimeKey, *, hf_token: str | None, question: str,
        callback: Callable[[str], T], on_acquired: Callable[[], None] | None = None,
        on_ready: Callable[[], None] | None = None,
        on_generating: Callable[[], None] | None = None,
    ) -> T:
        """Runs generation and the backend-owned SQL callback under one lease."""
        def run() -> T:
            if on_acquired is not None:
                on_acquired()
            adapter = self._manager.get_or_load(key, hf_token=hf_token)
            try:
                if on_ready is not None:
                    on_ready()
                if not isinstance(adapter, GenerativeAdapter):
                    raise TypeError("adapter carregado não suporta geração")
                if on_generating is not None:
                    on_generating()
                generated = adapter.generate(question)
                return callback(generated.sql)
            finally:
                # A loaded runtime remains eligible for the idle TTL even after a safe failure.
                self._manager.mark_used()
        return self._coordinator.execute(OperationType.CHAT, run)

    def expire_if_idle(self) -> bool:
        return self._coordinator.execute(
            OperationType.EXPIRE_RUNTIME,
            self._manager.expire_if_idle,
        )

    def shutdown(self) -> None:
        self._coordinator.execute(OperationType.SHUTDOWN, self._manager.shutdown)
