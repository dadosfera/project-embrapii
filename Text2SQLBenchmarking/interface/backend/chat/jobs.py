from __future__ import annotations

import threading
from time import monotonic
from typing import Callable

from .models import ChatJobSnapshot, ChatJobState, TERMINAL

_ALLOWED_TRANSITIONS: dict[ChatJobState, frozenset[ChatJobState]] = {
    ChatJobState.ACCEPTED: frozenset({ChatJobState.LOADING_MODEL, ChatJobState.GENERATING, ChatJobState.FAILED}),
    ChatJobState.LOADING_MODEL: frozenset({ChatJobState.GENERATING, ChatJobState.FAILED}),
    ChatJobState.GENERATING: frozenset({ChatJobState.VALIDATING_SQL, ChatJobState.FAILED}),
    ChatJobState.VALIDATING_SQL: frozenset({ChatJobState.EXECUTING, ChatJobState.FAILED}),
    ChatJobState.EXECUTING: frozenset({ChatJobState.SUCCEEDED, ChatJobState.FAILED}),
    ChatJobState.SUCCEEDED: frozenset(), ChatJobState.FAILED: frozenset(), ChatJobState.EXPIRED: frozenset(),
}

class InvalidChatJobTransition(ValueError): pass


class ChatJobs:
    def __init__(self, *, ttl_seconds: float = 900, clock: Callable[[], float] = monotonic) -> None:
        self._items: dict[str, ChatJobSnapshot] = {}
        self._terminal_at: dict[str, float] = {}
        self._ttl_seconds, self._clock = ttl_seconds, clock
        self._lock = threading.Lock()

    def add(self, snapshot: ChatJobSnapshot) -> None:
        with self._lock:
            self._cleanup_locked()
            self._items[snapshot.job_id] = snapshot

    def get(self, job_id: str) -> ChatJobSnapshot | None:
        with self._lock:
            self._cleanup_locked()
            return self._items.get(job_id)

    def update(self, job_id: str, **values: object) -> ChatJobSnapshot:
        with self._lock:
            self._cleanup_locked()
            current = self._items[job_id]
            state = values.get("state", current.state)
            if not isinstance(state, ChatJobState) or (state is not current.state and state not in _ALLOWED_TRANSITIONS[current.state]):
                raise InvalidChatJobTransition("transição de estado de Chat inválida")
            updated = current.update(**values)
            self._items[job_id] = updated
            if updated.state in TERMINAL and updated.state is not ChatJobState.EXPIRED:
                self._terminal_at.setdefault(job_id, self._clock())
            return updated

    def cleanup(self) -> tuple[str, ...]:
        with self._lock: return self._cleanup_locked()

    def _cleanup_locked(self) -> tuple[str, ...]:
        now, expired = self._clock(), []
        for job_id, finished in tuple(self._terminal_at.items()):
            if now - finished >= self._ttl_seconds:
                snapshot = self._items.get(job_id)
                if snapshot is not None:
                    self._items[job_id] = snapshot.update(state=ChatJobState.EXPIRED)
                    del self._items[job_id]
                del self._terminal_at[job_id]; expired.append(job_id)
        return tuple(expired)
