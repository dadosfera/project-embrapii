import pytest

from interface.backend.chat.jobs import ChatJobs, InvalidChatJobTransition
from interface.backend.chat.models import ChatJobSnapshot, ChatJobState
from interface.backend.domain.capabilities import ConfigurationSelection


def test_jobs_store_and_replace_immutable_snapshots():
    jobs = ChatJobs(); item = ChatJobSnapshot.accepted(ConfigurationSelection("sih_database", "raw_model", "Qwen/Qwen2.5-Coder-7B-Instruct", "default"))
    jobs.add(item); assert jobs.get(item.job_id) == item
    assert jobs.update(item.job_id, state=ChatJobState.GENERATING).state is ChatJobState.GENERATING
    with pytest.raises(InvalidChatJobTransition):
        jobs.update(item.job_id, state=ChatJobState.ACCEPTED)


def test_terminal_jobs_expire_with_injected_monotonic_clock():
    now = [0.0]
    jobs = ChatJobs(ttl_seconds=900, clock=lambda: now[0])
    item = ChatJobSnapshot.accepted(ConfigurationSelection("sih_database", "raw_model", "Qwen/Qwen2.5-Coder-7B-Instruct", "default"))
    jobs.add(item)
    jobs.update(item.job_id, state=ChatJobState.GENERATING)
    jobs.update(item.job_id, state=ChatJobState.VALIDATING_SQL)
    jobs.update(item.job_id, state=ChatJobState.EXECUTING)
    jobs.update(item.job_id, state=ChatJobState.SUCCEEDED)
    now[0] = 899.0; assert jobs.get(item.job_id) is not None
    now[0] = 900.0; assert jobs.get(item.job_id) is None
