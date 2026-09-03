"""Factory fechada sobre as quatro bibliotecas publicadas no catálogo."""

from __future__ import annotations

from pathlib import Path

from interface.backend.adapters.base import (
    AdapterError,
    AdapterErrorCode,
    BaseGeneratorAdapter,
    DatabaseConfigResolver,
    GeneratorFactory,
    SeedSetter,
    resolve_database_config_from_pipeline,
    set_pipeline_seed,
)
from interface.backend.adapters.paths import resolve_context_resources
from interface.backend.adapters.paths import project_root as default_project_root
from interface.backend.adapters.premsql_agent import (
    DEFAULT_GENERATOR_FACTORY as PREMSQL_FACTORY,
    PremSQLAdapter,
)
from interface.backend.adapters.raw_model import (
    DEFAULT_GENERATOR_FACTORY as RAW_MODEL_FACTORY,
    RawModelAdapter,
)
from interface.backend.adapters.vanna_ai import (
    DEFAULT_GENERATOR_FACTORY as VANNA_FACTORY,
    VannaAIAdapter,
)
from interface.backend.adapters.xiyan_sql import (
    DEFAULT_GENERATOR_FACTORY as XIYAN_FACTORY,
    XiYanSQLAdapter,
)
from interface.backend.adapters.workspace import RuntimeWorkspace
from interface.backend.domain.capabilities import (
    ApplicationMode,
    ConfigurationSelection,
    LibraryId,
    resolve_registry_name,
    validate_configuration,
)


_ADAPTERS = {
    LibraryId.RAW_MODEL.value: (RawModelAdapter, RAW_MODEL_FACTORY),
    LibraryId.VANNA_AI.value: (VannaAIAdapter, VANNA_FACTORY),
    LibraryId.PREMSQL_AGENT.value: (PremSQLAdapter, PREMSQL_FACTORY),
    LibraryId.XIYAN_SQL.value: (XiYanSQLAdapter, XIYAN_FACTORY),
}


def create_adapter(
    configuration: ConfigurationSelection,
    mode: ApplicationMode | str,
    *,
    random_seed: int,
    hf_token: str | None,
    generator_factory: GeneratorFactory | None = None,
    database_config_resolver: DatabaseConfigResolver = resolve_database_config_from_pipeline,
    seed_setter: SeedSetter = set_pipeline_seed,
    project_root: Path | None = None,
    workspace: RuntimeWorkspace | None = None,
    runtime_directory: Path | None = None,
) -> BaseGeneratorAdapter:
    """Cria adapters catalogados com dependências internas de runtime.

    ``workspace`` e ``runtime_directory`` são pontos de injeção exclusivos do
    backend; não fazem parte de qualquer contrato destinado a clientes HTTP.
    """

    try:
        selected_mode = ApplicationMode(mode)
    except ValueError as exc:
        raise AdapterError(
            AdapterErrorCode.UNSUPPORTED_COMBINATION,
            "A configuração selecionada não é suportada.",
            "modo desconhecido na factory",
        ) from exc

    validation = validate_configuration(configuration, selected_mode)
    if not validation.is_valid:
        detail = validation.error.code.value if validation.error else "erro desconhecido"
        raise AdapterError(
            AdapterErrorCode.UNSUPPORTED_COMBINATION,
            validation.error.message
            if validation.error
            else "A configuração selecionada não é suportada.",
            f"catálogo rejeitou configuração: {detail}",
        )

    registry = resolve_registry_name(configuration.model_id)
    if not registry.is_valid or registry.value is None:
        raise AdapterError(
            AdapterErrorCode.UNSUPPORTED_COMBINATION,
            "O modelo selecionado não está disponível.",
            "model_id validado sem registry_name",
        )

    adapter_class, default_factory = _ADAPTERS[configuration.library]
    if workspace is not None and runtime_directory is not None:
        raise AdapterError(
            AdapterErrorCode.RUNTIME_WORKSPACE_ERROR,
            "Não foi possível preparar o ambiente isolado do gerador.",
            "workspace e runtime_directory fornecidos simultaneamente",
        )

    if workspace is None:
        selected_root = (project_root or default_project_root()).resolve()
        selected_workspace = RuntimeWorkspace.create(
            project_root=selected_root,
            runtime_directory=runtime_directory,
        )
    else:
        selected_workspace = workspace
        selected_root = selected_workspace.project_root
        if project_root is not None and project_root.resolve() != selected_root:
            raise AdapterError(
                AdapterErrorCode.RUNTIME_WORKSPACE_ERROR,
                "Não foi possível preparar o ambiente isolado do gerador.",
                "raiz do workspace diverge da raiz injetada",
            )
        selected_workspace.ensure_ready()

    resources = resolve_context_resources(configuration, root=selected_root)
    selected_generator_factory = (
        default_factory if generator_factory is None else generator_factory
    )
    return adapter_class(
        configuration=configuration,
        mode=selected_mode,
        registry_name=registry.value,
        random_seed=random_seed,
        hf_token=hf_token,
        resources=resources,
        workspace=selected_workspace,
        generator_factory=selected_generator_factory,
        database_config_resolver=database_config_resolver,
        seed_setter=seed_setter,
    )
