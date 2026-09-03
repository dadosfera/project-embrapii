"""Resolução server-side dos recursos de documentação e exemplos."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from interface.backend.domain.capabilities import ConfigurationSelection, ContextId


@dataclass(frozen=True)
class ContextResources:
    doc_path: str | None = None
    examples_path: str | None = None


@dataclass(frozen=True)
class _DatabaseResources:
    documentation: str
    examples: str


_RESOURCES = {
    "datasus": _DatabaseResources(
        documentation="datasets/datasus/datasus_documentation_resumida.md",
        examples="datasets/datasus/consultas_exemplo_reduzido.json",
    ),
    "sih_database": _DatabaseResources(
        documentation="datasets/sih_database/sih_documentation_resumida.md",
        examples="datasets/sih_database/exemplos.json",
    ),
}


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _required_file(root: Path, relative_path: str, resource_kind: str) -> str:
    from interface.backend.adapters.base import AdapterError, AdapterErrorCode

    candidate = (root / relative_path).resolve()
    if not candidate.is_file():
        raise AdapterError(
            AdapterErrorCode.CONTEXT_RESOURCE_NOT_FOUND,
            "Um recurso de contexto necessário não está disponível.",
            f"{resource_kind} ausente: {candidate}",
        )
    return str(candidate)


def resolve_context_resources(
    configuration: ConfigurationSelection,
    *,
    root: Path | None = None,
) -> ContextResources:
    """Resolve somente paths cadastrados; a configuração nunca contém paths."""

    context = ContextId(configuration.context)
    if context in (ContextId.DEFAULT, ContextId.NONE):
        return ContextResources()

    selected = _RESOURCES[configuration.database]
    selected_root = (root or project_root()).resolve()
    doc_path = None
    examples_path = None

    if context in (ContextId.DOCUMENTATION, ContextId.DOCUMENTATION_AND_EXAMPLES):
        doc_path = _required_file(
            selected_root,
            selected.documentation,
            "documentação",
        )
    if context in (ContextId.EXAMPLES, ContextId.DOCUMENTATION_AND_EXAMPLES):
        examples_path = _required_file(
            selected_root,
            selected.examples,
            "exemplos",
        )
    return ContextResources(doc_path=doc_path, examples_path=examples_path)
