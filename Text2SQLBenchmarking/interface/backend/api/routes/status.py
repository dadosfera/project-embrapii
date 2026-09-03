from fastapi import APIRouter, Depends

from ..dependencies import ApiContainer, get_container
from ..schemas import StatusResponse

router = APIRouter()


@router.get("/status", response_model=StatusResponse)
@router.get("/system/status", response_model=StatusResponse)
def status(container: ApiContainer = Depends(get_container)) -> StatusResponse:
    operation = container.coordinator.status()
    key = container.model_manager.current_key
    job = container.benchmark.active() or container.benchmark.latest()
    return StatusResponse(
        is_busy=operation.is_busy,
        active_operation=operation.active_operation.value if operation.active_operation else None,
        model_state=container.model_manager.state.value,
        runtime_loaded=key is not None,
        runtime_configuration=(
            {"database": key.database.value, "library": key.library.value, "model_id": key.model_id, "context": key.context.value}
            if key else None
        ),
        benchmark_job=job.as_dict() if job else None,
    )
