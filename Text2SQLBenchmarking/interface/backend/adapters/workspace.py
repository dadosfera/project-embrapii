"""Workspace isolado para o estado relativo dos geradores legados."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path
import tempfile
from typing import Iterator


class WorkspaceLifecycleOwner(str, Enum):
    """Componente responsável por decidir quando o workspace será removido."""

    BACKEND = "backend"
    CALLER = "caller"


def _workspace_error(internal_detail: str):
    from interface.backend.adapters.base import AdapterError, AdapterErrorCode

    return AdapterError(
        AdapterErrorCode.RUNTIME_WORKSPACE_ERROR,
        "Não foi possível preparar o ambiente isolado do gerador.",
        internal_detail,
    )


@dataclass(frozen=True)
class RuntimeWorkspace:
    """Diretórios usados por uma instância de adapter.

    A troca temporária de ``cwd`` é global ao processo. Geradores reais só
    podem usar este escopo sob a exclusão de operação prevista para a Fase 5.
    Esta classe deliberadamente não implementa lock ou fila.
    """

    working_directory: Path
    project_root: Path
    local_models_directory: Path
    lifecycle_owner: WorkspaceLifecycleOwner

    @classmethod
    def create(
        cls,
        *,
        project_root: Path,
        runtime_directory: Path | None = None,
    ) -> RuntimeWorkspace:
        root = project_root.resolve()
        models_path = root / "local_models"
        if not models_path.is_dir():
            raise _workspace_error("cache local de modelos ausente")

        try:
            real_models = models_path.resolve(strict=True)
            runtime_root = root / "interface" / ".runtime" / "adapters"
            runtime_root.mkdir(parents=True, exist_ok=True)
            if runtime_directory is None:
                working_directory = Path(
                    tempfile.mkdtemp(prefix="adapter-", dir=runtime_root)
                ).resolve()
                owner = WorkspaceLifecycleOwner.BACKEND
            else:
                working_directory = runtime_directory.resolve()
                if (
                    working_directory == runtime_root
                    or not working_directory.is_relative_to(runtime_root)
                ):
                    raise _workspace_error(
                        "diretório de runtime fora da árvore isolada"
                    )
                if (
                    working_directory == real_models
                    or working_directory.is_relative_to(real_models)
                ):
                    raise _workspace_error(
                        "diretório de runtime não pode estar no cache de modelos"
                    )
                working_directory.mkdir(parents=True, exist_ok=True)
                owner = WorkspaceLifecycleOwner.CALLER
        except Exception as exc:
            from interface.backend.adapters.base import AdapterError

            if isinstance(exc, AdapterError):
                raise
            raise _workspace_error(
                f"falha ao criar diretório de runtime: {type(exc).__name__}"
            ) from exc

        workspace = cls(
            working_directory=working_directory,
            project_root=root,
            local_models_directory=real_models,
            lifecycle_owner=owner,
        )
        workspace.ensure_ready()
        return workspace

    def ensure_ready(self) -> None:
        """Valida o cache e cria somente o link necessário no workspace."""

        expected_models = self.project_root / "local_models"
        if not expected_models.is_dir() or not self.local_models_directory.is_dir():
            raise _workspace_error("cache local de modelos indisponível")

        try:
            real_expected_models = expected_models.resolve(strict=True)
            real_configured_models = self.local_models_directory.resolve(strict=True)
        except OSError as exc:
            raise _workspace_error("cache local de modelos inválido") from exc
        if real_expected_models != real_configured_models:
            raise _workspace_error("workspace referencia outro cache de modelos")

        runtime_root = (
            self.project_root / "interface" / ".runtime" / "adapters"
        ).resolve()
        resolved_working_directory = self.working_directory.resolve()
        if (
            resolved_working_directory == runtime_root
            or not resolved_working_directory.is_relative_to(runtime_root)
        ):
            raise _workspace_error("workspace fora da árvore isolada")

        try:
            resolved_working_directory.mkdir(parents=True, exist_ok=True)
            link = resolved_working_directory / "local_models"
            if link.is_symlink():
                try:
                    target = link.resolve(strict=True)
                except OSError as exc:
                    raise _workspace_error("link local_models inválido") from exc
                if target != real_configured_models:
                    raise _workspace_error("link local_models aponta para outro destino")
            elif link.exists():
                raise _workspace_error("local_models existente não é link simbólico")
            else:
                link.symlink_to(real_configured_models, target_is_directory=True)

            if (
                not link.is_symlink()
                or link.resolve(strict=True) != real_configured_models
            ):
                raise _workspace_error("link local_models não pôde ser validado")
        except Exception as exc:
            from interface.backend.adapters.base import AdapterError

            if isinstance(exc, AdapterError):
                raise
            raise _workspace_error(
                f"falha ao preparar workspace: {type(exc).__name__}"
            ) from exc

    @contextmanager
    def activate(self) -> Iterator[None]:
        """Muda o cwd somente durante a operação e sempre tenta restaurá-lo."""

        self.ensure_ready()
        try:
            previous_directory = Path.cwd()
            os.chdir(self.working_directory)
        except OSError as exc:
            raise _workspace_error(
                f"falha ao ativar workspace: {type(exc).__name__}"
            ) from exc

        try:
            yield
        finally:
            try:
                os.chdir(previous_directory)
            except OSError as exc:
                raise _workspace_error(
                    f"falha ao restaurar diretório corrente: {type(exc).__name__}"
                ) from exc
