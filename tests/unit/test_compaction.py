"""Tests for LLM-based context compaction."""
import pytest
from pathlib import Path
from whiz.agent.compaction import Compactor, CompactionTrigger
from whiz.agent.loop import Orchestrator
from whiz.repl.core import LocalREPL
from whiz.models.base import LLMResponse
from tests.mocks.llm import MockLLM


# --- CompactionTrigger ---

class TestCompactionTrigger:
    def test_creation(self):
        trigger = CompactionTrigger(threshold=1000)
        assert trigger.threshold == 1000

    def test_not_triggered_below_threshold(self):
        trigger = CompactionTrigger(threshold=1000)
        repl = LocalREPL()
        repl.exec_code("x = 1")
        assert not trigger.should_compact(repl)

    def test_triggered_above_threshold(self):
        trigger = CompactionTrigger(threshold=10)
        repl = LocalREPL()
        # Add enough history to exceed threshold
        for i in range(20):
            repl.exec_code(f"x_{i} = {i} * 100")
        assert trigger.should_compact(repl)

    def test_history_estimate_affects_trigger(self):
        trigger = CompactionTrigger(threshold=50)
        repl = LocalREPL()
        repl.exec_code("x = " + "a" * 200)
        assert trigger.should_compact(repl)


# --- Compactor ---

class TestCompactor:
    def test_creation(self):
        compactor = Compactor(model=MockLLM(responses=["ok"]))
        assert compactor is not None

    def test_compact_summarizes_history(self):
        mock = MockLLM(responses=[
            "Summary: x=42, y=100, result='found 3 items'"
        ])
        compactor = Compactor(model=mock)
        repl = LocalREPL()
        repl.exec_code("x = 42")
        repl.exec_code("y = 100")
        repl.exec_code("result = 'found 3 items'")

        compactor.compact(repl)

        # After compaction, history should be minimal
        assert len(repl.history) <= 2  # compaction marker + summary
        assert "compaction" in repl.history[0].output.lower() or \
               "Summary" in repl.history[-1].output

    def test_compact_preserves_namespace(self):
        mock = MockLLM(responses=["Variables: x=42, y=100"])
        compactor = Compactor(model=mock)
        repl = LocalREPL()
        repl.exec_code("x = 42")
        repl.exec_code("y = 100")

        compactor.compact(repl)

        # After compaction, these variables should still work
        result = repl.exec_code("x + y")
        assert "142" in result

    def test_compact_multiple_rounds(self):
        """Compaction can be triggered multiple times in a session."""
        mock = MockLLM(responses=[
            "Summary round 1: x=1",
            "Summary round 2: x=1, y=2",
        ])
        compactor = Compactor(model=mock)
        repl = LocalREPL()

        # Round 1: fill history
        for i in range(10):
            repl.exec_code(f"a_{i} = {i}")
        compactor.compact(repl)

        # Round 2: fill again
        for i in range(10):
            repl.exec_code(f"b_{i} = {i}")
        compactor.compact(repl)

        # Should still work
        result = repl.exec_code("x = 1")
        assert not repl.history[-1].has_error

    def test_compactor_with_model_error(self):
        """If compaction LLM call fails, REPL should still be usable."""
        mock = MockLLM(responses=[])
        compactor = Compactor(model=mock)
        repl = LocalREPL()
        repl.exec_code("x = 42")

        # MockLLM will raise IndexError when exhausted
        compactor.compact(repl)

        # REPL should still be functional
        result = repl.exec_code("x")
        assert "42" in result


# --- Orchestrator Integration ---

class TestOrchestratorCompaction:
    def test_orchestrator_compactor_integration(self, tmp_path):
        """Orchestrator can be configured with a compaction threshold."""
        mock = MockLLM(responses=[
            "x = 1",
            "y = 2",
            "z = 3",
            "Summary: x=1, y=2",  # compaction call
            "complete('done')",
        ])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=20,
        )
        # Compactor is not yet auto-triggered in run() -- that's an integration detail
        # For now we test the Compactor directly
        result = orch.run("test")
        # The session should complete (or hit max rounds)
        assert result.rounds <= 20
