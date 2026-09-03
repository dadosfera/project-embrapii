from fastapi import APIRouter, Depends

from ..dependencies import ApiContainer, get_container
from ..schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(container: ApiContainer = Depends(get_container)) -> HealthResponse:
    # ``latest`` é uma checagem curta de que o journal continua disponível.
    container.journal.latest()
    return HealthResponse(status="ok", api_version="v1", journal_available=True)
