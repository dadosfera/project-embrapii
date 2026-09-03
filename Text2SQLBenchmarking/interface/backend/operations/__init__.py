"""Exclusão não bloqueante para operações pesadas da interface."""

from .coordinator import (
    OperationCoordinator,
    OperationCoordinatorError,
    OperationErrorCode,
    OperationLease,
    OperationStatus,
    OperationType,
)
from .service import ExclusiveOperationService

__all__ = [
    "ExclusiveOperationService",
    "OperationCoordinator",
    "OperationCoordinatorError",
    "OperationErrorCode",
    "OperationLease",
    "OperationStatus",
    "OperationType",
]
