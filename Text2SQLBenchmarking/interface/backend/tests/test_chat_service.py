from interface.backend.adapters.base import GenerationResult
from interface.backend.chat.jobs import ChatJobs
from interface.backend.chat.models import ChatJobState
from interface.backend.chat.service import ChatService, ChatServiceError, QueryResult
from interface.backend.domain.capabilities import ConfigurationSelection


CONFIG = ConfigurationSelection("sih_database", "raw_model", "Qwen/Qwen2.5-Coder-7B-Instruct", "default")


class Operations:
    def run_chat(self, _key, *, question, callback, on_acquired, on_generating, **_kwargs):
        on_acquired(); on_generating()
        return callback(self.sql)

    sql = "SELECT 1"


class Executor:
    def __init__(self, error=None): self.error, self.calls = error, 0
    def execute(self, _configuration, _sql):
        self.calls += 1
        if self.error: raise self.error
        return QueryResult(("x",), ((1,),), 1, 1, False)


class RecordingJobs(ChatJobs):
    def __init__(self):
        super().__init__(clock=lambda: 0)
        self.states: list[ChatJobState] = []

    def add(self, snapshot):
        super().add(snapshot)
        self.states.append(snapshot.state)

    def update(self, job_id, **values):
        snapshot = super().update(job_id, **values)
        self.states.append(snapshot.state)
        return snapshot

def test_query_result_contract_for_display_counts():
    empty=QueryResult((), (), 0, 0, False); full=QueryResult(("x",), tuple((i,) for i in range(200)), 200, 200, False); truncated=QueryResult(("x",), tuple((i,) for i in range(200)), 201, 200, True)
    assert (empty.row_count, empty.displayed_row_count, empty.truncated)==(0,0,False)
    assert (full.row_count, full.displayed_row_count, full.truncated)==(200,200,False)
    assert (truncated.row_count, truncated.displayed_row_count, truncated.truncated)==(201,200,True)


def test_service_runs_real_state_flow_and_preserves_configuration():
    ticks = iter((10.0, 12.0, 20.0, 23.0))
    operations, executor, jobs = Operations(), Executor(), RecordingJobs()
    service = ChatService(
        operations=operations,
        jobs=jobs,
        query_executor=executor,
        clock=lambda: next(ticks),
    )
    accepted = []
    result = service.run("pergunta", CONFIG, on_accepted=accepted.append)
    assert accepted[0].state is ChatJobState.ACCEPTED
    assert result.state is ChatJobState.SUCCEEDED
    assert jobs.states == [
        ChatJobState.ACCEPTED,
        ChatJobState.LOADING_MODEL,
        ChatJobState.GENERATING,
        ChatJobState.VALIDATING_SQL,
        ChatJobState.EXECUTING,
        ChatJobState.SUCCEEDED,
    ]
    assert result.configuration == CONFIG
    assert result.sql == "SELECT 1"
    assert result.columns == ("x",)
    assert result.rows == ((1,),)
    assert (result.row_count, result.displayed_row_count, result.truncated) == (1, 1, False)
    assert result.generation_time_seconds == 2.0
    assert result.execution_time_seconds == 3.0


def test_service_keeps_sql_when_guard_rejects_and_never_calls_database():
    operations, executor, jobs = Operations(), Executor(), ChatJobs()
    operations.sql = "SELECT lowrite(1, 'x')"
    result = ChatService(operations=operations, jobs=jobs, query_executor=executor).run("q", CONFIG, on_accepted=lambda _: None)
    assert result.state is ChatJobState.FAILED and result.error.code == "UNSAFE_SQL"
    assert result.sql == operations.sql and executor.calls == 0


def test_empty_generation_is_safe_generation_error():
    operations, executor = Operations(), Executor(); operations.sql = "  "
    result = ChatService(operations=operations, jobs=ChatJobs(), query_executor=executor).run("q", CONFIG, on_accepted=lambda _: None)
    assert result.state is ChatJobState.FAILED and result.error.code == "SQL_GENERATION_ERROR" and result.sql is None


def test_chat_never_publishes_qwen3_thinking_when_normalization_fails():
    operations, executor = Operations(), Executor()
    operations.sql = "<think>SELECT segredo FROM interno</think>sem consulta"
    result = ChatService(operations=operations, jobs=ChatJobs(), query_executor=executor).run("q", CONFIG, on_accepted=lambda _: None)
    assert result.state is ChatJobState.FAILED and result.error.code == "SQL_GENERATION_ERROR"
    assert result.sql is None and executor.calls == 0


def test_chat_examples_uses_fixed_seed_and_forwards_only_current_question():
    class RecordingOperations(Operations):
        def __init__(self):
            self.keys = []
            self.questions = []

        def run_chat(self, key, *, question, **kwargs):
            self.keys.append(key)
            self.questions.append(question)
            return super().run_chat(key, question=question, **kwargs)

    operations = RecordingOperations()
    configuration = ConfigurationSelection(
        "sih_database",
        "raw_model",
        "Qwen/Qwen2.5-Coder-7B-Instruct",
        "examples",
    )
    result = ChatService(
        operations=operations,
        jobs=ChatJobs(),
        query_executor=Executor(),
    ).run("somente a pergunta atual", configuration, on_accepted=lambda _: None)

    assert result.state is ChatJobState.SUCCEEDED
    assert operations.questions == ["somente a pergunta atual"]
    assert operations.keys[0].random_seed == 42
    assert operations.keys[0].context.value == "examples"
    assert operations.keys[0].legacy_token == "rawModel_exemplos"
