"""Search tool: grep-backed codebase search with semantic-ready interface."""
from __future__ import annotations

import subprocess
from pathlib import Path


class SearchTool:
    """Search across the codebase.

    Backend-agnostic interface: starts as grep-backed, designed to be
    swapped for semantic/vector search without changing agent code.
    """

    def __init__(self, project_root: Path, backend: str = "grep", **kwargs):
        self.project_root = Path(project_root).resolve()
        self.backend = backend

    def search(self, query: str, max_results: int = 20) -> str:
        if self.backend == "grep":
            return self._grep_search(query, max_results)
        raise ValueError(f"Unknown search backend: {self.backend}")

    def _grep_search(self, query: str, max_results: int) -> str:
        try:
            result = subprocess.run(
                [
                    "grep", "-r", "-n", "--include=*.py", "--include=*.js",
                    "--include=*.ts", "--include=*.tsx", "--include=*.go",
                    "--include=*.rs", "--include=*.java", "--include=*.c",
                    "--include=*.cpp", "--include=*.h", "--include=*.md",
                    "--include=*.yaml", "--include=*.yml", "--include=*.json",
                    "--include=*.toml", "--include=*.cfg", "--include=*.txt",
                    "-F", query, str(self.project_root),
                ],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.project_root),
            )
        except FileNotFoundError:
            return "Error: grep not found on system"
        except subprocess.TimeoutExpired:
            return "Error: search timed out"

        if result.returncode == 1:  # grep: no matches
            return ""
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"

        lines = result.stdout.strip().split("\n")[:max_results]
        return "\n".join(lines)
