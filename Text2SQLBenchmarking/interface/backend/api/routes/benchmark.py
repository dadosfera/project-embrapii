from fastapi import APIRouter, Depends

from interface.backend.benchmark import (
    ArtifactState,
    BenchmarkIdentity,
    BenchmarkMetricsError,
    calculate_benchmark_metrics,
)
from interface.backend.domain.capabilities import ApplicationMode, validate_configuration
from interface.backend.storage.parquet_reader import read_parquet_artifact

from ..dependencies import ApiContainer, get_container
from ..errors import ApiError
from ..schemas import (
    AcceptedBenchmarkResponse,
    BenchmarkRequest,
    ExperimentStatusRequest,
    ExperimentStatusResponse,
    JobResponse,
    ReexecutionIntentRequest,
    ReexecutionIntentResponse,
)

router = APIRouter(prefix="/benchmark/jobs")
status_router = APIRouter(prefix="/benchmark/experiments")
intent_router = APIRouter(prefix="/benchmark/reexecution-intents")


@intent_router.post("", response_model=ReexecutionIntentResponse)
def create_reexecution_intent(
    request: ReexecutionIntentRequest,
    container: ApiContainer = Depends(get_container),
) -> ReexecutionIntentResponse:
    configuration = request.configuration()
    validation = validate_configuration(configuration, ApplicationMode.BENCHMARK)
    if not validation.is_valid:
        error = validation.error
        raise ApiError(error.code.value, error.message, 400)  # type: ignore[union-attr]
    intent = container.benchmark.create_reexecution_intent(
        configuration,
        seed=request.seed,
    )
    return ReexecutionIntentResponse(
        confirmationToken=intent.token,
        expiresInSeconds=intent.expires_in_seconds,
    )


@status_router.get("/status", response_model=ExperimentStatusResponse)
def experiment_status(
    request: ExperimentStatusRequest = Depends(),
    container: ApiContainer = Depends(get_container),
) -> ExperimentStatusResponse:
    """Inspeciona artefatos existentes, sem criar job nem adquirir operação pesada."""

    configuration = request.configuration()
    validation = validate_configuration(configuration, ApplicationMode.BENCHMARK)
    if not validation.is_valid:
        error = validation.error
        raise ApiError(error.code.value, error.message, 400)  # type: ignore[union-attr]

    identity = BenchmarkIdentity.create(configuration, request.seed)
    inspection = container.artifacts.inspect(identity)
    artifact_state = inspection.state
    invalid_reason = inspection.invalid_reason
    metrics = None
    counts = None
    times = None

    if artifact_state is ArtifactState.COMPLETE:
        try:
            aggregate = calculate_benchmark_metrics(
                read_parquet_artifact(container.artifacts.paths_for(identity).execution)
            )
        except BenchmarkMetricsError:
            artifact_state = ArtifactState.INVALID_RESULT
            invalid_reason = BenchmarkMetricsError.public_message
        else:
            metrics = aggregate.metrics_as_dict()
            counts = aggregate.counts.as_dict()
            times = aggregate.times.as_dict()

    return ExperimentStatusResponse(
        configuration={
            "database": configuration.database,
            "library": configuration.library,
            "model_id": configuration.model_id,
            "context": configuration.context,
        },
        seed=request.seed,
        artifact_state=artifact_state.value,
        generation=inspection.generation.as_dict(),
        execution=inspection.execution.as_dict(),
        invalid_reason=invalid_reason,
        metrics=metrics,
        counts=counts,
        times=times,
    )


@router.post("", status_code=202, response_model=AcceptedBenchmarkResponse)
def create_job(
    request: BenchmarkRequest,
    container: ApiContainer = Depends(get_container),
) -> AcceptedBenchmarkResponse:
    validation = validate_configuration(request.configuration(), ApplicationMode.BENCHMARK)
    if not validation.is_valid:
        error = validation.error
        raise ApiError(error.code.value, error.message, 400)  # type: ignore[union-attr]
    accepted = container.benchmark_executor.submit(
        request.configuration(),
        seed=request.seed,
        action=request.action,
        confirmation_token=request.confirmation_token,
    )
    job_id = accepted.snapshot.job_id
    return AcceptedBenchmarkResponse(
        job_id=job_id,
        snapshot=accepted.snapshot.as_dict(),
        poll=f"/api/v1/benchmark/jobs/{job_id}",
    )


@router.get("/latest", response_model=JobResponse)
def latest(container: ApiContainer = Depends(get_container)) -> JobResponse:
    snapshot = container.benchmark.latest()
    return JobResponse(job=snapshot.as_dict() if snapshot else None)


@router.get("/active", response_model=JobResponse)
def active(container: ApiContainer = Depends(get_container)) -> JobResponse:
    snapshot = container.benchmark.active()
    return JobResponse(job=snapshot.as_dict() if snapshot else None)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, container: ApiContainer = Depends(get_container)) -> JobResponse:
    return JobResponse(job=container.benchmark.get(job_id).as_dict())
