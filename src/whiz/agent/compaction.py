"""Context compaction: LLM-based summarization of REPL history."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from whiz.models.base import BaseModel
from whiz.repl.core import LocalREPL, HistoryEntry

COMPACTION_PROMPT = """You are a context compaction assistant. Summarize the following REPL session history into a compact summary.

Preserve:
- Variable names and their current values (especially computed results)
- Key observations about the codebase
- Any data that will be needed for future reasoning

Discard:
- Verbose file contents (just note which files were read)
- Intermediate print output that's no longer relevant
- Full tracebacks (just note the error type)

History to summarize:
{history}

Provide a concise summary (under 500 words):
"""


class CompactionTrigger:
    """Determines when compaction should occur based on REPL token estimate."""

    def __init__(self, threshold: int = 4000):
        self.threshold = threshold

    def should_compact(self, repl: LocalREPL) -> bool:
        return repl.token_estimate() >= self.threshold


class Compactor:
    """Compacts REPL history using an LLM summarization pass."""

    def __init__(self, model: BaseModel):
        self.model = model

    def compact(self, repl: LocalREPL) -> bool:
        """Compact REPL history. Returns True if compaction was performed."""
        if not repl.history:
            return False

        # Build history text for the summarizer
        history_text = self._format_history(repl.history)
        prompt = COMPACTION_PROMPT.format(history=history_text)

        try:
            response = self.model.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="",
            )
            summary = response.content
        except Exception:
            # Compaction failed -- don't crash, just return
            return False

        # Preserve the namespace (variables)
        preserved_ns = repl.get_namespace()

        # Clear history
        repl.history.clear()

        # Add compaction marker and summary
        repl.history.append(HistoryEntry(
            code="# compaction",
            output=f"Previous context summarized:\n{summary}",
            error=None,
        ))

        # Restore namespace
        for name, value in preserved_ns.items():
            repl._namespace[name] = value

        return True

    def _format_history(self, history: list[HistoryEntry]) -> str:
        lines = []
        for i, entry in enumerate(history):
            if entry.code.strip() and not entry.code.startswith("# compaction"):
                lines.append(f"[Turn {i + 1}]")
                lines.append(f"Code: {entry.code}")
                if entry.output.strip():
                    lines.append(f"Output: {entry.output}")
                if entry.has_error:
                    lines.append(f"Error: {entry.error}")
                lines.append("")
        return "\n".join(lines) if lines else "(empty history)"
