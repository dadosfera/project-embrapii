"""Adapters uniformes e de importação leve para os geradores legados."""

from .base import (
    AdapterBehavior,
    AdapterError,
    AdapterErrorCode,
    BaseGeneratorAdapter,
    GenerationResult,
)
from .factory import create_adapter
from .premsql_agent import PremSQLAdapter
from .raw_model import RawModelAdapter
from .vanna_ai import VannaAIAdapter
from .xiyan_sql import XiYanSQLAdapter
from .workspace import RuntimeWorkspace, WorkspaceLifecycleOwner

__all__ = [
    "AdapterBehavior",
    "AdapterError",
    "AdapterErrorCode",
    "BaseGeneratorAdapter",
    "GenerationResult",
    "PremSQLAdapter",
    "RawModelAdapter",
    "VannaAIAdapter",
    "XiYanSQLAdapter",
    "RuntimeWorkspace",
    "WorkspaceLifecycleOwner",
    "create_adapter",
]
