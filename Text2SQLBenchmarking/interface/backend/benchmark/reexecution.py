"""Intenções efêmeras e vinculadas ao snapshot para reexecução segura."""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
import secrets
import threading
from time import monotonic
from typing import Callable

from .artifacts import ArtifactInspection, BenchmarkIdentity
from .models import ArtifactState, BenchmarkErrorCode, FileSnapshot


class ReexecutionIntentError(ValueError):
    def __init__(
        self,
        code: BenchmarkErrorCode,
        public_message: str,
        internal_detail: str,
    ) -> None:
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message
        self.internal_detail = internal_detail


@dataclass(frozen=True)
class ReexecutionIntent:
    token: str
    identity: BenchmarkIdentity
    generation: FileSnapshot
    execution: FileSnapshot
    expires_at: float


@dataclass(frozen=True)
class IssuedReexecutionIntent:
    token: str
    expires_in_seconds: float


class ReexecutionIntentStore:
    """Armazena tokens opacos em memória; nenhuma identidade entra no token."""

    def __init__(
        self,
        *,
        ttl_seconds: float = 300.0,
        clock: Callable[[], float] = monotonic,
        token_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
    ) -> None:
        if (
            isinstance(ttl_seconds, bool)
            or not isinstance(ttl_seconds, Real)
            or not math.isfinite(ttl_seconds)
            or ttl_seconds <= 0
        ):
            raise ValueError("ttl_seconds deve ser um número finito positivo")
        self._ttl_seconds = float(ttl_seconds)
        self._clock = clock
        self._token_factory = token_factory
        self._intents: dict[str, ReexecutionIntent] = {}
        self._lock = threading.Lock()

    def issue(
        self,
        identity: BenchmarkIdentity,
        inspection: ArtifactInspection,
    ) -> IssuedReexecutionIntent:
        if (
            inspection.state is not ArtifactState.COMPLETE
            or not inspection.generation.exists
            or not inspection.execution.exists
        ):
            raise ReexecutionIntentError(
                BenchmarkErrorCode.REEXECUTION_CONFIRMATION_REQUIRED,
                "A reexecução só pode ser confirmada para um resultado completo e válido.",
                "intenção solicitada fora do estado complete",
            )
        now = self._clock()
        with self._lock:
            self._remove_expired(now)
            token = self._token_factory()
            while token in self._intents:
                token = self._token_factory()
            self._intents[token] = ReexecutionIntent(
                token=token,
                identity=identity,
                generation=inspection.generation,
                execution=inspection.execution,
                expires_at=now + self._ttl_seconds,
            )
        return IssuedReexecutionIntent(token=token, expires_in_seconds=self._ttl_seconds)

    def consume(
        self,
        token: str | None,
        identity: BenchmarkIdentity,
        inspection: ArtifactInspection,
    ) -> None:
        if not token:
            self._confirmation_required("token ausente")
        now = self._clock()
        with self._lock:
            intent = self._intents.pop(token, None)
        if intent is None:
            self._confirmation_required("token desconhecido ou já utilizado")
        if intent.expires_at <= now:
            self._confirmation_required("token expirado")
        if (
            intent.identity != identity
            or inspection.state is not ArtifactState.COMPLETE
            or inspection.generation != intent.generation
            or inspection.execution != intent.execution
        ):
            raise ReexecutionIntentError(
                BenchmarkErrorCode.REEXECUTION_STATE_CHANGED,
                "Os artefatos do Benchmark mudaram. Confirme a reexecução novamente.",
                "identidade ou snapshots divergiram da intenção",
            )

    def _remove_expired(self, now: float) -> None:
        expired = [token for token, intent in self._intents.items() if intent.expires_at <= now]
        for token in expired:
            self._intents.pop(token, None)

    @staticmethod
    def _confirmation_required(detail: str) -> None:
        raise ReexecutionIntentError(
            BenchmarkErrorCode.REEXECUTION_CONFIRMATION_REQUIRED,
            "Confirme explicitamente a reexecução antes de iniciar o Benchmark.",
            detail,
        )
