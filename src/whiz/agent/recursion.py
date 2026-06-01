"""Sub-LLM recursion: child session dispatch."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def create_sub_llm_callable(
    model: Any,
    project_root: Path,
    recursion_mgr: Any,
    max_rounds: int = 50,
):
    """Create the sub_llm callable that gets injected into the REPL.

    Uses lazy imports to avoid circular dependency with Orchestrator.
    """

    def sub_llm(prompt: str, context: str = "") -> str:
        try:
            recursion_mgr.enter()
        except Exception as e:
            return f"RecursionError: {e}"

        try:
            # Lazy import to avoid circular dependency
            from whiz.agent.loop import Orchestrator

            child_orch = Orchestrator(
                model=model,
                project_root=project_root,
                max_rounds=max_rounds,
            )

            full_prompt = prompt
            if context:
                full_prompt = f"Context:\n{context}\n\nTask: {prompt}"

            result = child_orch.run(full_prompt)

            if result.success:
                return str(result.value) if result.value is not None else ""
            else:
                return f"Error: {result.error}"

        finally:
            recursion_mgr.exit()

    return sub_llm
