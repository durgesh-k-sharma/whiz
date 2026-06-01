"""Local in-process REPL environment."""
from __future__ import annotations

import io
import sys
import math
import json
import re
import subprocess
import textwrap
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from whiz.repl.base import BaseEnvironment

ALLOWED_STDLIB = [
    "os", "sys", "json", "re", "math", "pathlib", "subprocess", "textwrap",
    "datetime", "collections", "itertools", "functools", "typing",
    "hashlib", "base64", "urllib", "io", "glob", "shutil", "tempfile",
    "csv", "string", "copy",
]

BLOCKED_BUILTINS = [
    "eval", "exec", "compile", "open",
    "globals", "locals", "vars", "dir",
    "getattr", "setattr", "delattr",
    "breakpoint", "exit", "quit",
    "memoryview", "property",
]


@dataclass
class HistoryEntry:
    code: str
    output: str
    error: str | None

    @property
    def has_error(self) -> bool:
        return self.error is not None


class LocalREPL(BaseEnvironment):
    """In-process Python REPL with persistent namespace."""

    def __init__(
        self,
        max_output_lines: int = 200,
        blocked_imports: list[str] | None = None,
    ):
        self.max_output_lines = max_output_lines
        self.blocked_imports = blocked_imports or []
        self.history: list[HistoryEntry] = []
        self._namespace = self._build_namespace()

    def _build_namespace(self) -> dict[str, Any]:
        ns: dict[str, Any] = {}
        ns["__builtins__"] = self._filtered_builtins()
        for mod_name in ALLOWED_STDLIB:
            try:
                ns[mod_name] = __import__(mod_name)
            except ImportError:
                pass
        ns["Path"] = Path
        return ns

    def _filtered_builtins(self) -> dict[str, Any]:
        import builtins
        return {
            name: getattr(builtins, name)
            for name in dir(builtins)
            if name not in BLOCKED_BUILTINS
        }

    def _is_import_blocked(self, code: str) -> str | None:
        import ast
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return None
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in self.blocked_imports:
                        return alias.name
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                if root in self.blocked_imports:
                    return node.module
        return None

    def exec_code(self, code: str) -> str:
        stripped = code.strip()
        if not stripped:
            return ""

        blocked = self._is_import_blocked(stripped)
        if blocked is not None:
            entry = HistoryEntry(code=stripped, output="", error=f"ImportError: import of '{blocked}' is blocked")
            self.history.append(entry)
            return entry.error

        try:
            parsed_exec = compile(stripped, "<repl>", "exec")
        except SyntaxError as e:
            error_msg = f"SyntaxError: {e.msg}"
            entry = HistoryEntry(code=stripped, output="", error=error_msg)
            self.history.append(entry)
            return error_msg

        # Try eval first (for single expressions like "2 + 2", "x * 2")
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        result_value = None
        error_msg = None
        used_exec = False

        try:
            parsed_eval = compile(stripped, "<repl>", "eval")
        except SyntaxError:
            parsed_eval = None

        try:
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                if parsed_eval is not None:
                    result_value = repr(eval(parsed_eval, self._namespace))
                else:
                    # Multi-statement code: try to extract last expression
                    import ast
                    tree = ast.parse(stripped)
                    if tree.body and isinstance(tree.body[-1], ast.Expr):
                        # Execute everything except the last expression
                        if len(tree.body) > 1:
                            prefix = ast.Module(body=tree.body[:-1], type_ignores=[])
                            prefix_obj = compile(prefix, "<repl>", "exec")
                            exec(prefix_obj, self._namespace)
                        # Evaluate the last expression for its value
                        last_expr = ast.Expression(body=tree.body[-1].value)
                        last_obj = compile(last_expr, "<repl>", "eval")
                        val = eval(last_obj, self._namespace)
                        if val is not None:
                            result_value = repr(val)
                    else:
                        used_exec = True
                        exec(parsed_exec, self._namespace)
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"

        stdout_text = stdout_buf.getvalue()
        stderr_text = stderr_buf.getvalue()

        output = ""
        if stdout_text:
            output = stdout_text.rstrip("\n")
        if result_value and not used_exec:
            output = (output + "\n" + result_value).strip() if output else result_value
        if stderr_text and not error_msg:
            stderr_text = stderr_text.rstrip("\n")
            output = (output + "\n" + stderr_text).strip() if output else stderr_text

        output = self._truncate_output(output)

        entry = HistoryEntry(code=stripped, output=output, error=error_msg)
        self.history.append(entry)
        return output if not error_msg else error_msg

    def _truncate_output(self, text: str) -> str:
        lines = text.split("\n")
        if len(lines) <= self.max_output_lines:
            return text
        kept = lines[:self.max_output_lines]
        return "\n".join(kept) + f"\n... [{len(lines) - self.max_output_lines} lines truncated]"

    def clear(self) -> None:
        self.history.clear()
        self._namespace = self._build_namespace()

    def get_namespace(self) -> dict[str, Any]:
        return dict(self._namespace)

    def token_estimate(self) -> int:
        total_chars = sum(
            len(entry.code) + len(entry.output) + (len(entry.error) if entry.error else 0)
            for entry in self.history
        )
        return total_chars // 4
