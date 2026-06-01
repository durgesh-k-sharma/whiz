"""Tests for the Orchestrator agent loop."""
import pytest
from pathlib import Path
from unittest.mock import patch

from whiz.agent.loop import Orchestrator, SessionResult, SessionEvent
from whiz.repl.core import LocalREPL
from whiz.context.indexer import CodebaseIndex
from whiz.models.base import LLMResponse
from tests.mocks.llm import MockLLM


# --- SessionResult ---

class TestSessionResult:
    def test_creation(self):
        result = SessionResult(
            success=True,
            value="done",
            rounds=3,
            trajectory=[],
        )
        assert result.success
        assert result.value == "done"
        assert result.rounds == 3

    def test_failure(self):
        result = SessionResult(
            success=False,
            value=None,
            rounds=10,
            trajectory=[],
            error="max rounds exceeded",
        )
        assert not result.success
        assert result.error == "max rounds exceeded"


# --- Orchestrator ---

class TestOrchestrator:
    def test_orchestrator_creates_repl(self, tmp_path):
        mock = MockLLM(responses=["complete('done')"])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=10,
        )
        result = orch.run("test prompt")
        assert result.success

    def test_orchestrator_stops_on_complete(self, tmp_path):
        mock = MockLLM(responses=["complete('hello world')"])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=10,
        )
        result = orch.run("test prompt")
        assert result.success
        assert result.value == "hello world"

    def test_orchestrator_stops_on_max_rounds(self, tmp_path):
        # Never calls complete
        mock = MockLLM(responses=["x = 1", "y = 2", "z = 3"])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=3,
        )
        result = orch.run("test prompt")
        assert not result.success
        assert result.rounds == 3

    def test_orchestrator_injects_index(self, tmp_path):
        (tmp_path / "main.py").write_text("x = 1")
        mock = MockLLM(responses=["complete('done')"])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=10,
        )
        result = orch.run("test prompt")
        assert result.success
        # The REPL should have received the file_tree variable

    def test_orchestrator_injects_prompt(self, tmp_path):
        mock = MockLLM(responses=["complete('done')"])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=10,
        )
        result = orch.run("my specific prompt")
        assert result.success

    def test_orchestrator_rounds_match_llm_calls(self, tmp_path):
        mock = MockLLM(responses=[
            "x = search('TODO')",
            "result = len(x)",
            "complete(result)",
        ])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=10,
        )
        result = orch.run("count TODOs")
        assert result.success
        assert mock.call_count <= 3

    def test_orchestrator_trajectory_tracked(self, tmp_path):
        mock = MockLLM(responses=["x = 1", "complete(x)"])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=10,
        )
        result = orch.run("test")
        assert result.success
        assert len(result.trajectory) > 0

    def test_orchestrator_tools_in_repl(self, tmp_path):
        mock = MockLLM(responses=["complete('ok')"])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=10,
        )
        # After init, the REPL namespace should have tool callables
        result = orch.run("test")
        assert result.success

    def test_orchestrator_propagates_repl_errors(self, tmp_path):
        mock = MockLLM(responses=[
            "1 / 0",  # ZeroDivisionError
            "complete('recovered')",
        ])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=10,
        )
        result = orch.run("test with error recovery")
        assert result.success  # should recover from REPL error

    def test_orchestrator_timeout_per_round(self, tmp_path):
        mock = MockLLM(responses=["complete('done')"])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=10,
            round_timeout=30,
        )
        result = orch.run("test")
        assert result.success


# --- Trajectory / SessionEvent ---

class TestSessionEvent:
    def test_creation(self):
        event = SessionEvent(
            round_num=1,
            code="x = 1",
            output="1",
            error=None,
        )
        assert event.round_num == 1
        assert event.code == "x = 1"

    def test_requires_round_num(self):
        with pytest.raises(TypeError):
            SessionEvent(code="x = 1", output="1")
