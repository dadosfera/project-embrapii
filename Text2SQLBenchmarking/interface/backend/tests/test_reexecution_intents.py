from __future__ import annotations

import pytest

from interface.backend.benchmark.artifacts import ArtifactInspection, BenchmarkIdentity
from interface.backend.benchmark.models import ArtifactState, BenchmarkErrorCode, FileSnapshot
from interface.backend.benchmark.reexecution import ReexecutionIntentError, ReexecutionIntentStore
from interface.backend.tests.adapter_support import configuration


class Clock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


def _snapshot(name: str, marker: str = "a") -> FileSnapshot:
    return FileSnapshot(f"sih_database/model/{name}.parquet", True, 10, 20, marker)


def _inspection(*, state=ArtifactState.COMPLETE, generation_marker="a", execution_marker="a") -> ArtifactInspection:
    return ArtifactInspection(
        state=state,
        generation=_snapshot("generation", generation_marker),
        execution=_snapshot("execution", execution_marker),
    )


def _store(clock: Clock) -> ReexecutionIntentStore:
    tokens = iter(("opaque-one", "opaque-two", "opaque-three"))
    return ReexecutionIntentStore(
        ttl_seconds=30,
        clock=clock,
        token_factory=lambda: next(tokens),
    )


def test_issues_opaque_intent_for_complete_result_and_consumes_once():
    clock = Clock()
    store = _store(clock)
    identity = BenchmarkIdentity.create(configuration(), 42)

    issued = store.issue(identity, _inspection())

    assert issued.token == "opaque-one"
    assert issued.expires_in_seconds == 30
    assert "sih_database" not in issued.token
    store.consume(issued.token, identity, _inspection())
    with pytest.raises(ReexecutionIntentError) as reused:
        store.consume(issued.token, identity, _inspection())
    assert reused.value.code is BenchmarkErrorCode.REEXECUTION_CONFIRMATION_REQUIRED


@pytest.mark.parametrize("state", [ArtifactState.NOT_STARTED, ArtifactState.GENERATION_ONLY, ArtifactState.INVALID_RESULT])
def test_refuses_intent_outside_complete_state(state):
    with pytest.raises(ReexecutionIntentError) as raised:
        _store(Clock()).issue(
            BenchmarkIdentity.create(configuration(), 42),
            _inspection(state=state),
        )
    assert raised.value.code is BenchmarkErrorCode.REEXECUTION_CONFIRMATION_REQUIRED


def test_token_is_bound_to_configuration_seed_and_both_snapshots():
    mismatch_cases = [
        (BenchmarkIdentity.create(configuration(database="datasus"), 42), _inspection()),
        (BenchmarkIdentity.create(configuration(), 43), _inspection()),
        (BenchmarkIdentity.create(configuration(), 42), _inspection(generation_marker="changed")),
        (BenchmarkIdentity.create(configuration(), 42), _inspection(execution_marker="changed")),
    ]
    for identity, inspection in mismatch_cases:
        clock = Clock()
        store = _store(clock)
        original = BenchmarkIdentity.create(configuration(), 42)
        token = store.issue(original, _inspection()).token
        with pytest.raises(ReexecutionIntentError) as raised:
            store.consume(token, identity, inspection)
        assert raised.value.code is BenchmarkErrorCode.REEXECUTION_STATE_CHANGED


def test_missing_invalid_and_expired_tokens_require_new_confirmation():
    clock = Clock()
    identity = BenchmarkIdentity.create(configuration(), 42)
    store = _store(clock)

    for token in (None, "invalid"):
        with pytest.raises(ReexecutionIntentError) as raised:
            store.consume(token, identity, _inspection())
        assert raised.value.code is BenchmarkErrorCode.REEXECUTION_CONFIRMATION_REQUIRED

    token = store.issue(identity, _inspection()).token
    clock.value = 30
    with pytest.raises(ReexecutionIntentError) as expired:
        store.consume(token, identity, _inspection())
    assert expired.value.code is BenchmarkErrorCode.REEXECUTION_CONFIRMATION_REQUIRED
