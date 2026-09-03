from fastapi import APIRouter

from interface.backend.domain.capabilities import (
    list_contexts,
    list_databases,
    list_libraries,
    list_models,
    list_models_for_library,
    get_initial_configuration,
)
from interface.backend.domain.metrics import serialize_metric_registry

router = APIRouter()


@router.get("/catalog")
@router.get("/capabilities")
def catalog() -> dict[str, object]:
    libraries: list[dict[str, object]] = []
    for library in list_libraries():
        models = list_models_for_library(library.id.value).value or ()
        libraries.append(
            {
                "id": library.id.value,
                "label": library.label,
                "contexts": [context.value for context in library.contexts],
                "model_ids": [model.id for model in models],
                "availability": {
                    "chat": {
                        "available": library.chat.available,
                        "reason": (
                            {"code": library.chat.reason.code, "message": library.chat.reason.message}
                            if library.chat.reason else None
                        ),
                    },
                    "benchmark": {
                        "available": library.benchmark.available,
                        "reason": (
                            {"code": library.benchmark.reason.code, "message": library.benchmark.reason.message}
                            if library.benchmark.reason else None
                        ),
                    },
                },
                "order": library.order,
            }
        )
    return {
        "databases": [{"id": item.id.value, "label": item.label} for item in list_databases()],
        "libraries": libraries,
        "models": [
            {"id": model.id, "label": model.label, "family": model.family.value, "order": model.order}
            for model in list_models()
        ],
        "contexts": [{"id": item.id.value, "label": item.label} for item in list_contexts()],
        "metrics": serialize_metric_registry(),
        "initial_configuration": get_initial_configuration().__dict__,
    }
