from fastapi import APIRouter, Depends
from interface.backend.domain.capabilities import ApplicationMode, validate_configuration
from interface.backend.chat.service import ChatServiceError
from ..dependencies import ApiContainer, get_container
from ..errors import ApiError
from ..schemas import AcceptedChatResponse, ChatJobResponse, ChatRequest

router = APIRouter(prefix="/chat/jobs")

@router.post("", status_code=202, response_model=AcceptedChatResponse)
def create_job(request: ChatRequest, container: ApiContainer = Depends(get_container)):
    if not request.question.strip(): raise ApiError("INVALID_REQUEST", "A pergunta informada não é válida.", 422)
    validation = validate_configuration(request.configuration(), ApplicationMode.CHAT)
    if not validation.is_valid:
        error = validation.error; raise ApiError(error.code.value, error.message, 400)  # type: ignore[union-attr]
    if container.chat_executor is None: raise ApiError("INTERNAL_ERROR", "O serviço de Chat não está disponível.", 500)
    accepted = container.chat_executor.submit(request.question, request.configuration()).snapshot
    return AcceptedChatResponse(job_id=accepted.job_id, state=accepted.state.value, created_at=accepted.created_at, poll=f"/api/v1/chat/jobs/{accepted.job_id}", snapshot=accepted.as_dict())

@router.get("/{job_id}", response_model=ChatJobResponse)
def get_job(job_id: str, container: ApiContainer = Depends(get_container)):
    snapshot = container.chat.get(job_id) if container.chat is not None else None
    if snapshot is None: raise ApiError("JOB_NOT_FOUND", "O job de Chat não foi encontrado.", 404)
    return ChatJobResponse(job=snapshot.as_dict())
