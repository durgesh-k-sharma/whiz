"""Cloud sandbox stubs: Modal, E2B, Daytona, Prime."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from whiz.repl.base import BaseEnvironment


class ModalEnvironment(BaseEnvironment):
    def __init__(self, project_root: Path, **kwargs):
        self.project_root = Path(project_root).resolve()

    def exec_code(self, code: str) -> str:
        raise NotImplementedError(
            "Modal sandbox is not yet implemented. "
            "Install with: pip install modal"
        )

    def get_namespace(self) -> dict[str, Any]:
        return {}


class E2BDaytonaEnvironment(BaseEnvironment):
    def __init__(self, project_root: Path, provider: str = "e2b", **kwargs):
        self.project_root = Path(project_root).resolve()
        self.provider = provider

    def exec_code(self, code: str) -> str:
        raise NotImplementedError(
            f"{self.provider} sandbox is not yet implemented. "
            f"Install with: pip install {self.provider}"
        )

    def get_namespace(self) -> dict[str, Any]:
        return {}


class PrimeEnvironment(BaseEnvironment):
    def __init__(self, project_root: Path, **kwargs):
        self.project_root = Path(project_root).resolve()

    def exec_code(self, code: str) -> str:
        raise NotImplementedError(
            "Prime sandbox is not yet implemented. "
            "Install with: pip install prime-sandbox"
        )

    def get_namespace(self) -> dict[str, Any]:
        return {}
