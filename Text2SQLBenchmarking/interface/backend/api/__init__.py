"""API HTTP inicial da interface, sem expor infraestrutura interna."""

from .app import create_app

__all__ = ["create_app"]
