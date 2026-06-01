"""Tests for the local REPL execution environment."""
import pytest

from whiz.repl.base import BaseEnvironment
from whiz.repl.core import LocalREPL, HistoryEntry


# --- HistoryEntry ---

class TestHistoryEntry:
    def test_creation(self):
        entry = HistoryEntry(code="x = 1", output="1", error=None)
        assert entry.code == "x = 1"
        assert entry.output == "1"
        assert entry.error is None

    def test_with_error(self):
        entry = HistoryEntry(code="1/0", output="", error="ZeroDivisionError: division by zero")
        assert entry.error == "ZeroDivisionError: division by zero"

    def test_has_error(self):
        ok = HistoryEntry(code="x=1", output="1", error=None)
        assert not ok.has_error
        bad = HistoryEntry(code="1/0", output="", error="ZeroDivisionError")
        assert bad.has_error


# --- LocalREPL ---

class TestLocalREPL:
    def test_simple_evaluation(self):
        repl = LocalREPL()
        result = repl.exec_code("2 + 2")
        assert result == "4"

    def test_variable_persists_across_turns(self):
        repl = LocalREPL()
        repl.exec_code("x = 42")
        result = repl.exec_code("x * 2")
        assert result == "84"

    def test_multiline_code(self):
        repl = LocalREPL()
        result = repl.exec_code("def add(a, b):\n    return a + b\n\nadd(3, 4)")
        assert result == "7"

    def test_stdout_capture(self):
        repl = LocalREPL()
        result = repl.exec_code("print('hello')")
        assert "hello" in result

    def test_stderr_capture(self):
        repl = LocalREPL()
        result = repl.exec_code("import sys; print('err', file=sys.stderr)")
        assert "err" in result

    def test_syntax_error_formatted(self):
        repl = LocalREPL()
        result = repl.exec_code("def broken(")
        assert "SyntaxError" in result

    def test_runtime_error_formatted(self):
        repl = LocalREPL()
        result = repl.exec_code("1 / 0")
        assert "ZeroDivisionError" in result

    def test_name_error(self):
        repl = LocalREPL()
        result = repl.exec_code("undefined_var")
        assert "NameError" in result

    def test_stdlib_available(self):
        repl = LocalREPL()
        result = repl.exec_code("import subprocess; print('ok')")
        assert "ok" in result

    def test_pathlib_available(self):
        repl = LocalREPL()
        result = repl.exec_code("from pathlib import Path; p = Path('/tmp'); print(p.name)")
        assert "tmp" in result

    def test_json_available(self):
        repl = LocalREPL()
        result = repl.exec_code("import json; print(json.dumps({'a': 1}))")
        assert '"a"' in result

    def test_re_available(self):
        repl = LocalREPL()
        result = repl.exec_code("import re; m = re.search(r'\\d+', 'abc123'); print(m.group())")
        assert "123" in result

    def test_history_tracked(self):
        repl = LocalREPL()
        repl.exec_code("x = 1")
        repl.exec_code("y = 2")
        assert len(repl.history) == 2
        assert repl.history[0].code == "x = 1"
        assert repl.history[1].code == "y = 2"

    def test_history_includes_output(self):
        repl = LocalREPL()
        repl.exec_code("x = 42")
        # Assignments produce no output
        assert repl.history[0].output == ""
        # But expressions do
        repl.exec_code("x")
        assert repl.history[1].output == "42"

    def test_history_includes_errors(self):
        repl = LocalREPL()
        repl.exec_code("1/0")
        assert repl.history[0].has_error
        assert "ZeroDivisionError" in repl.history[0].error

    def test_namespace_isolated(self):
        repl1 = LocalREPL()
        repl2 = LocalREPL()
        repl1.exec_code("x = 100")
        result = repl2.exec_code("x")
        assert "NameError" in result

    def test_clear_resets_state(self):
        repl = LocalREPL()
        repl.exec_code("x = 42")
        repl.clear()
        assert len(repl.history) == 0
        # After clear, x is no longer defined
        result = repl.exec_code("x")
        assert "NameError" in result

    def test_token_estimate_empty(self):
        repl = LocalREPL()
        assert repl.token_estimate() == 0

    def test_token_estimate_grows(self):
        repl = LocalREPL()
        repl.exec_code("x = 1")
        assert repl.token_estimate() > 0

    def test_get_namespace_copy(self):
        repl = LocalREPL()
        repl.exec_code("my_var = 'hello'")
        ns = repl.get_namespace()
        assert ns["my_var"] == "hello"
        # Should be a copy -- mutations don't affect REPL
        ns["my_var"] = "mutated"
        result = repl.exec_code("my_var")
        assert "hello" in result

    def test_import_blocklist_raises(self):
        repl = LocalREPL(blocked_imports=["os"])
        result = repl.exec_code("import os")
        assert "ImportError" in result or "blocked" in result.lower()

    def test_deep_recursion_blocked(self):
        repl = LocalREPL()
        result = repl.exec_code("def f(): f()\nf()")
        assert "RecursionError" in result

    def test_output_truncation(self):
        repl = LocalREPL(max_output_lines=5)
        result = repl.exec_code("\n".join([f"print('line {i}')" for i in range(100)]))
        assert len(result.split("\n")) <= 10  # some buffer for truncation marker


# --- BaseEnvironment ---

class TestBaseEnvironment:
    def test_base_exec_raises(self):
        env = BaseEnvironment()
        with pytest.raises(NotImplementedError):
            env.exec_code("1 + 1")

    def test_base_get_namespace_raises(self):
        env = BaseEnvironment()
        with pytest.raises(NotImplementedError):
            env.get_namespace()
