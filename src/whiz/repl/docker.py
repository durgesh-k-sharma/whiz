"""Docker-based REPL environment."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

from whiz.repl.base import BaseEnvironment


class DockerEnvironment(BaseEnvironment):
    """Runs REPL code in a Docker container."""

    def __init__(
        self,
        project_root: Path,
        image: str = "python:3.12-slim",
        container_timeout: int = 60,
    ):
        self.project_root = Path(project_root).resolve()
        self.image = image
        self.container_timeout = container_timeout

    def exec_code(self, code: str) -> str:
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                f.flush()
                code_file = f.name

            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    "-v", f"{self.project_root}:/workspace",
                    "-v", f"{code_file}:/code.py",
                    "-w", "/workspace",
                    self.image,
                    "python", "/code.py",
                ],
                capture_output=True,
                text=True,
                timeout=self.container_timeout,
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()
                return f"Error: {stderr}" if stderr else "Error: Docker execution failed"

            return result.stdout.strip()

        except FileNotFoundError:
            return "Error: Docker is not installed or not in PATH"
        except subprocess.TimeoutExpired:
            return f"Error: Docker container timed out after {self.container_timeout}s"
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"
        finally:
            try:
                Path(code_file).unlink()  # type: ignore[name-defined]
            except Exception:
                pass

    def get_namespace(self) -> dict[str, Any]:
        return {}
