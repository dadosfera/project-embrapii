"""Limpeza segura do estado efêmero de um runtime."""

from __future__ import annotations

import os
from pathlib import Path

from interface.backend.adapters.workspace import RuntimeWorkspace, WorkspaceLifecycleOwner


class WorkspaceCleanupError(RuntimeError):
    """Falha de limpeza cujo detalhe de filesystem não é público."""

    def __init__(self, internal_detail: str) -> None:
        super().__init__("Não foi possível limpar o ambiente isolado do gerador.")
        self.public_message = str(self)
        self.internal_detail = internal_detail


def _runtime_root(workspace: RuntimeWorkspace) -> Path:
    return (workspace.project_root / "interface" / ".runtime" / "adapters").resolve()


def _remove_tree_without_following_links(directory: Path) -> None:
    with os.scandir(directory) as entries:
        for entry in entries:
            entry_path = Path(entry.path)
            if entry.is_symlink():
                entry_path.unlink()
            elif entry.is_dir(follow_symlinks=False):
                _remove_tree_without_following_links(entry_path)
                entry_path.rmdir()
            else:
                entry_path.unlink()


def cleanup_backend_workspace(workspace: RuntimeWorkspace) -> None:
    """Remove somente workspace do backend, sem seguir links simbólicos."""

    if workspace.lifecycle_owner is WorkspaceLifecycleOwner.CALLER:
        return
    if workspace.lifecycle_owner is not WorkspaceLifecycleOwner.BACKEND:
        raise WorkspaceCleanupError("proprietário de workspace desconhecido")

    try:
        runtime_root = _runtime_root(workspace)
        working_directory = workspace.working_directory
        if working_directory.is_symlink():
            raise WorkspaceCleanupError("workspace não pode ser link simbólico")
        resolved_workspace = working_directory.resolve(strict=True)
        if (
            resolved_workspace == runtime_root
            or not resolved_workspace.is_relative_to(runtime_root)
        ):
            raise WorkspaceCleanupError("workspace fora da árvore de runtime")
        real_models = workspace.local_models_directory.resolve(strict=True)
        if resolved_workspace == real_models or real_models.is_relative_to(resolved_workspace):
            raise WorkspaceCleanupError("workspace não pode conter local_models real")

        _remove_tree_without_following_links(resolved_workspace)
        resolved_workspace.rmdir()
    except WorkspaceCleanupError:
        raise
    except Exception as exc:
        raise WorkspaceCleanupError(
            f"falha de limpeza: {type(exc).__name__}"
        ) from exc
