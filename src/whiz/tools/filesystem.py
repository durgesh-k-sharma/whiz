"""Filesystem tools: read_files, edit_file, run_tests."""
from __future__ import annotations

import subprocess
from pathlib import Path


def _safe_path(project_root: Path, file_path: str) -> Path | None:
    """Resolve a path relative to project_root, ensuring it stays within the project."""
    root = Path(project_root).resolve()
    target = (root / file_path).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target


class ReadFilesTool:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def read_files(self, paths: list[str]) -> str:
        results = []
        for p in paths:
            target = _safe_path(self.project_root, p)
            if target is None:
                results.append(f"Error: '{p}' is outside the project root")
                continue
            if not target.exists():
                results.append(f"Error: '{p}' not found")
                continue
            try:
                content = target.read_text(errors="replace")
                results.append(f"--- {p} ---\n{content}")
            except (PermissionError, OSError) as e:
                results.append(f"Error reading '{p}': {e}")
        return "\n\n".join(results)


class EditFileTool:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def edit_file(self, path: str, content: str) -> str:
        target = _safe_path(self.project_root, path)
        if target is None:
            return f"Error: '{path}' is outside the project root (not allowed)"
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            return f"OK: wrote {len(content)} bytes to {path}"
        except (PermissionError, OSError) as e:
            return f"Error writing '{path}': {e}"


class RunTestsTool:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def run_tests(self, command: str | None = None) -> str:
        if command is None:
            # Auto-detect test runner
            if (self.project_root / "pytest.ini").exists() or (self.project_root / "pyproject.toml").exists():
                command = "pytest -x -q"
            elif (self.project_root / "setup.py").exists():
                command = "python setup.py test"
            else:
                command = "pytest -x -q"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.project_root),
            )
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            return output.strip()
        except subprocess.TimeoutExpired:
            return "Error: tests timed out after 120s"
        except FileNotFoundError:
            return f"Error: command not found: {command}"
