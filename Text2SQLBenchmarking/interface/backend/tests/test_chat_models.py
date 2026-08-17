from interface.backend.chat.models import ChatJobSnapshot, ChatJobState
from interface.backend.domain.capabilities import ConfigurationSelection


def test_snapshot_is_public_and_never_contains_question():
    snapshot = ChatJobSnapshot.accepted(ConfigurationSelection("sih_database", "raw_model", "Qwen/Qwen2.5-Coder-7B-Instruct", "default"))
    assert snapshot.state is ChatJobState.ACCEPTED
    assert "question" not in snapshot.as_dict()


def test_snapshot_is_immutable():
    snapshot = ChatJobSnapshot.accepted(ConfigurationSelection("sih_database", "raw_model", "Qwen/Qwen2.5-Coder-7B-Instruct", "default"))
    assert snapshot.update(state=ChatJobState.FAILED).state is ChatJobState.FAILED
