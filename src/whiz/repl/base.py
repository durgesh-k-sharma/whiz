"""Abstract base for REPL environment backends."""
from __future__ import annotations

from typing import Any


class BaseEnvironment:
    """All REPL environments must implement exec_code and get_namespace."""

    def exec_code(self, code: str) -> str:
        raise NotImplementedError

    def get_namespace(self) -> dict[str, Any]:
        raise NotImplementedError
