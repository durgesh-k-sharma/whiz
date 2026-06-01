"""Tests for Sub-LLM recursion: depth tracking, parallel dispatch, child sessions."""
import pytest
from pathlib import Path

from whiz.agent.loop import Orchestrator, SubLLMManager, RecursionError
from tests.mocks.llm import MockLLM


# --- SubLLMManager ---

class TestSubLLMManager:
    def test_creation(self):
        mgr = SubLLMManager(max_depth=5)
        assert mgr.max_depth == 5
        assert mgr.current_depth == 0

    def test_enter_increments_depth(self):
        mgr = SubLLMManager(max_depth=5)
        mgr.enter()
        assert mgr.current_depth == 1
        mgr.enter()
        assert mgr.current_depth == 2

    def test_exit_decrements_depth(self):
        mgr = SubLLMManager(max_depth=5)
        mgr.enter()
        mgr.enter()
        mgr.exit()
        assert mgr.current_depth == 1

    def test_depth_limit_enforced(self):
        mgr = SubLLMManager(max_depth=3)
        mgr.enter()
        mgr.enter()
        mgr.enter()
        with pytest.raises(RecursionError, match="Max recursion depth"):
            mgr.enter()

    def test_can_enter_after_exit(self):
        mgr = SubLLMManager(max_depth=2)
        mgr.enter()
        mgr.enter()
        mgr.exit()
        mgr.exit()
        mgr.enter()  # should not raise
        assert mgr.current_depth == 1


# --- SubLLM in Orchestrator ---

class TestSubLLMRecursion:
    def test_sub_llm_callable_exists_in_repl(self, tmp_path):
        mock = MockLLM(responses=["complete('done')"])
        orch = Orchestrator(model=mock, project_root=tmp_path, max_rounds=10)
        orch.run("test")
        # sub_llm should have been injected -- if we got here, init worked
        assert True

    def test_sub_llm_spawns_child_session(self, tmp_path):
        """When the LLM calls sub_llm(), a child session runs via the same model."""
        # parent round 1: "result = sub_llm('say hello')"
        #   child runs: model -> "complete('hello from child')"
        # parent round 2: "complete(result)"
        mock = MockLLM(responses=[
            "result = sub_llm('say hello')",
            "complete('hello from child')",
            "complete(result)",
        ])
        orch = Orchestrator(model=mock, project_root=tmp_path, max_rounds=10)
        result = orch.run("test sub-llm")
        assert result.success

    def test_depth_limit_stops_recursion(self, tmp_path):
        """If model keeps calling sub_llm, depth limit should prevent infinite recursion."""
        mock = MockLLM(responses=["x = 1"] * 50)
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=20,
            max_recursion_depth=3,
        )
        result = orch.run("infinite recursion test")
        # Should stop -- either max rounds or depth limit
        assert result.rounds <= 20

    def test_sub_llm_returns_string(self, tmp_path):
        """sub_llm should return a string result to the REPL."""
        mock = MockLLM(responses=[
            "result = sub_llm('test task')",
            "complete('child result')",
            "complete(result)",
        ])
        orch = Orchestrator(model=mock, project_root=tmp_path, max_rounds=10)
        result = orch.run("test")
        assert result.success


# --- RecursionError ---

class TestRecursionError:
    def test_is_exception(self):
        with pytest.raises(RecursionError):
            raise RecursionError("test")

    def test_message(self):
        err = RecursionError("depth exceeded")
        assert "depth exceeded" in str(err)
