"""Coordenação síncrona, por processo e sem fila de operações pesadas."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import threading
from typing import Callable, TypeVar


class OperationType(str, Enum):
    """Tipos públicos, limitados e não sensíveis de operação pesada."""

    LOAD_RUNTIME = "LOAD_RUNTIME"
    GENERATE = "GENERATE"
    CHAT = "CHAT"
    EXECUTE_SQL = "EXECUTE_SQL"
    BENCHMARK = "BENCHMARK"
    EXPIRE_RUNTIME = "EXPIRE_RUNTIME"
    SHUTDOWN = "SHUTDOWN"


class OperationErrorCode(str, Enum):
    RESOURCE_BUSY = "RESOURCE_BUSY"


class OperationCoordinatorError(RuntimeError):
    """Erro de domínio seguro do coordenador de exclusão."""

    def __init__(
        self,
        code: OperationErrorCode,
        public_message: str,
        internal_detail: str,
        *,
        active_operation: OperationType | None = None,
    ) -> None:
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message
        self.internal_detail = internal_detail
        self.active_operation = active_operation


@dataclass(frozen=True)
class OperationStatus:
    """Snapshot seguro do estado global do único processo backend."""

    active_operation: OperationType | None

    @property
    def is_busy(self) -> bool:
        return self.active_operation is not None

    def as_dict(self) -> dict[str, bool | str | None]:
        return {
            "is_busy": self.is_busy,
            "active_operation": (
                self.active_operation.value if self.active_operation is not None else None
            ),
        }


@dataclass(frozen=True)
class OperationLease:
    operation: OperationType
    owner_thread_id: int


T = TypeVar("T")


class OperationCoordinator:
    """Admite no máximo uma operação pesada sem aguardar disponibilidade.

    A exclusão vale somente para este processo. Uma implantação com múltiplos
    workers precisará manter worker único ou fornecer coordenação externa.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active_operation: OperationType | None = None
        self._owner_thread_id: int | None = None

    def status(self) -> OperationStatus:
        """Retorna apenas o tipo seguro da operação em andamento."""

        # Não adquirir ``_lock`` aqui: ele é retido durante a operação pesada.
        # A atribuição/leitura da referência é atômica no runtime Python visado,
        # e o snapshot pode omitir transitoriamente a operação entre aquisição
        # e publicação, mas nunca aguarda a operação terminar.
        return OperationStatus(active_operation=self._active_operation)

    def try_acquire(self, operation: OperationType) -> OperationLease:
        """Adquire sem bloqueio ou retorna ``RESOURCE_BUSY`` imediatamente."""

        if not isinstance(operation, OperationType):
            raise TypeError("operation deve ser OperationType")
        if not self._lock.acquire(blocking=False):
            active_operation = self._active_operation
            raise OperationCoordinatorError(
                OperationErrorCode.RESOURCE_BUSY,
                "Outra operação pesada está em andamento.",
                "lock global ocupado",
                active_operation=active_operation,
            )

        owner_thread_id = threading.get_ident()
        self._active_operation = operation
        self._owner_thread_id = owner_thread_id
        return OperationLease(operation=operation, owner_thread_id=owner_thread_id)

    def release(self, lease: OperationLease) -> None:
        """Libera uma posse válida, sempre no thread que a adquiriu."""

        if not isinstance(lease, OperationLease):
            raise TypeError("lease de operação inválida")
        if (
            self._owner_thread_id != lease.owner_thread_id
            or threading.get_ident() != lease.owner_thread_id
            or self._active_operation is not lease.operation
        ):
            raise RuntimeError("tentativa inválida de liberar operação")
        self._active_operation = None
        self._owner_thread_id = None
        self._lock.release()

    def execute(self, operation: OperationType, callback: Callable[[], T]) -> T:
        """Executa integralmente sob exclusão e a libera em qualquer saída."""

        lease = self.try_acquire(operation)
        try:
            return callback()
        finally:
            self.release(lease)
