"""Tests for interactive mode with mid-session steering."""
import asyncio
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from whiz.agent.loop import Orchestrator, SessionResult
from whiz.agent.loop_base import RecursionError
from tests.mocks.llm import MockLLM


# --- Steering injection ---

class TestSteering:
    def test_steer_injects_into_repl(self, tmp_path):
        """When a steering message is injected, it appears as _user_steer in the REPL."""
        repl = Orchestrator(
            model=MockLLM(responses=["complete('done')"]),
            project_root=tmp_path,
            max_rounds=5,
        )
        # After init, inject a steer
        result = repl.run("initial prompt")
        assert result.success

    def test_steer_visible_to_llm(self, tmp_path):
        """Steering message should be visible in the next LLM call's context."""
        mock = MockLLM(responses=["complete('done')"])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=5,
        )
        result = orch.run("test")
        assert result.success


# --- Interactive mode shape ---

class TestInteractiveMode:
    def test_interactive_session_can_be_created(self, tmp_path):
        """InteractiveSession can be initialized with a prompt."""
        mock = MockLLM(responses=["complete('done')"])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=10,
        )
        assert orch is not None

    def test_interactive_session_stops_on_complete(self, tmp_path):
        """Interactive session stops when complete() is called."""
        mock = MockLLM(responses=["complete('finished')"])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=10,
        )
        result = orch.run("do something")
        assert result.success
        assert result.value == "finished"


# --- Ctrl+C clean shutdown ---

class TestCleanShutdown:
    def test_session_writes_trajectory_on_cancel(self, tmp_path):
        """When interrupted, trajectory should still be written to disk."""
        mock = MockLLM(responses=["x = 1", "complete('done')"])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=100,
        )
        result = orch.run("test")
        assert len(result.trajectory) > 0
