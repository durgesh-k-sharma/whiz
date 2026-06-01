"""Codebase indexing: file tree generation and README extraction."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

IGNORE_DIRS = {
    ".git", "__pycache__", ".venv", "node_modules", ".next",
    "dist", "build", ".tox", ".mypy_cache", ".pytest_cache",
    ".egg-info", ".eggs", "venv", "env",
}
IGNORE_EXTENSIONS = {".pyc", ".pyo", ".so", ".o", ".a", ".dll", ".exe", ".class"}
MAX_README_LINES = 200
MAX_FILE_TREE_DEPTH = 4


@dataclass
class CodebaseIndex:
    root: Path
    file_tree: str = ""
    readme: str = ""

    @classmethod
    def from_root(cls, root: Path) -> CodebaseIndex:
        root = Path(root).resolve()
        instance = cls(root=root)
        instance.file_tree = instance._generate_tree(root)
        instance.readme = instance._read_readme(root)
        return instance

    def _generate_tree(self, root: Path, prefix: str = "", depth: int = 0) -> str:
        if depth > MAX_FILE_TREE_DEPTH:
            return f"{prefix}... (max depth)\n"

        lines = []
        try:
            entries = sorted(root.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
        except PermissionError:
            return ""

        dirs = [e for e in entries if e.is_dir() and e.name not in IGNORE_DIRS and not e.name.startswith(".")]
        files = [e for e in entries if e.is_file() and e.suffix not in IGNORE_EXTENSIONS and not e.name.startswith(".")]

        for d in dirs:
            rel = d.relative_to(root)
            lines.append(f"{prefix}├── {d.name}/")
            sub = self._generate_tree(d, prefix=f"{prefix}│   ", depth=depth + 1)
            if sub:
                lines.append(sub.rstrip("\n"))

        for i, f in enumerate(files):
            connector = "└──" if i == len(files) - 1 and not dirs else "├──"
            lines.append(f"{prefix}{connector} {f.name}")

        return "\n".join(lines)

    def _read_readme(self, root: Path) -> str:
        for name in ["README.md", "README.rst", "README.txt", "README"]:
            path = root / name
            if path.exists():
                try:
                    lines = path.read_text(errors="replace").split("\n")
                    if len(lines) > MAX_README_LINES:
                        kept = lines[:MAX_README_LINES]
                        return "\n".join(kept) + f"\n... [{len(lines) - MAX_README_LINES} lines truncated]"
                    return "\n".join(lines)
                except (PermissionError, OSError):
                    return ""
        return ""

    def to_repl_variables(self) -> dict[str, str]:
        return {
            "file_tree": self.file_tree,
            "readme": self.readme,
            "project_root": str(self.root),
        }
