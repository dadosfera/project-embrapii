"""Schemas públicos da API; não incluem tokens, paths internos ou adapters."""

from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, StrictInt, StrictStr

from interface.backend.benchmark import BenchmarkAction
from interface.backend.domain.capabilities import ConfigurationSelection


class BenchmarkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    database: StrictStr
    library: StrictStr
    model_id: StrictStr
    context: StrictStr
    seed: StrictInt
    action: BenchmarkAction = BenchmarkAction.RUN_MISSING_STAGES
    confirmation_token: StrictStr | None = Field(
        default=None,
        validation_alias=AliasChoices("confirmation_token", "confirmationToken"),
    )

    def configuration(self) -> ConfigurationSelection:
        return ConfigurationSelection(
            database=self.database,
            library=self.library,
            model_id=self.model_id,
            context=self.context,
        )


class ExperimentStatusRequest(BaseModel):
    """Parâmetros query canônicos para consultar um experimento existente."""

    model_config = ConfigDict(extra="forbid")

    database: StrictStr
    library: StrictStr
    model_id: StrictStr
    context: StrictStr
    # Query parameters chegam ao FastAPI como texto; a conversão para inteiro
    # preserva a convenção da API sem tornar toda consulta inválida.
    seed: int

    def configuration(self) -> ConfigurationSelection:
        return ConfigurationSelection(
            database=self.database,
            library=self.library,
            model_id=self.model_id,
            context=self.context,
        )


class ReexecutionIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    database: StrictStr
    library: StrictStr
    model_id: StrictStr
    context: StrictStr
    seed: StrictInt

    def configuration(self) -> ConfigurationSelection:
        return ConfigurationSelection(
            database=self.database,
            library=self.library,
            model_id=self.model_id,
            context=self.context,
        )


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: StrictStr
    database: StrictStr
    library: StrictStr
    model_id: StrictStr
    context: StrictStr

    def configuration(self) -> ConfigurationSelection:
        return ConfigurationSelection(database=self.database, library=self.library, model_id=self.model_id, context=self.context)


class AcceptedChatResponse(BaseModel):
    job_id: str
    state: str
    created_at: str
    poll: str
    snapshot: dict[str, Any]


class ChatJobResponse(BaseModel):
    job: dict[str, Any]


class ErrorBody(BaseModel):
    code: str
    message: str
    retryable: bool


class ErrorResponse(BaseModel):
    error: ErrorBody


class AcceptedBenchmarkResponse(BaseModel):
    job_id: str
    snapshot: dict[str, Any]
    poll: str = "/api/v1/benchmark/jobs/{job_id}"


class JobResponse(BaseModel):
    job: dict[str, Any] | None


class ExperimentStatusResponse(BaseModel):
    configuration: dict[str, str]
    seed: int
    artifact_state: str
    generation: dict[str, Any]
    execution: dict[str, Any]
    invalid_reason: str | None
    metrics: dict[str, dict[str, float | int | bool | None]] | None
    counts: dict[str, int] | None
    times: dict[str, float] | None


class ReexecutionIntentResponse(BaseModel):
    confirmationToken: str
    expiresInSeconds: float


class HealthResponse(BaseModel):
    status: str
    api_version: str
    journal_available: bool


class StatusResponse(BaseModel):
    is_busy: bool
    active_operation: str | None
    model_state: str
    runtime_loaded: bool
    runtime_configuration: dict[str, str] | None
    benchmark_job: dict[str, Any] | None
