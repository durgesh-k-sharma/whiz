"""Orchestrator: the outer agent loop that drives RLM sessions."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from whiz.context.indexer import CodebaseIndex
from whiz.models.base import BaseModel
from whiz.repl.core import LocalREPL
from whiz.logging.trajectory import TrajectoryLogger
from whiz.agent.code_extraction import extract_code
from whiz.agent.tools import inject_tools
from whiz.agent.loop_base import SubLLMManager, RecursionError


SYSTEM_PROMPT = """You are Whiz. Answer the user's task.
Available Python tools: search(), read_files(), edit_file(), run_tests(), sub_llm()
When done, call complete("your answer").
Reply with:"""


@dataclass
class SessionEvent:
    round_num: int
    code: str
    output: str
    error: str | None = None


@dataclass
class SessionResult:
    success: bool
    value: Any
    rounds: int
    trajectory: list[SessionEvent]
    error: str | None = None


class Orchestrator:
    """Outer agent loop: manages a full RLM session."""

    def __init__(
        self,
        model: BaseModel,
        project_root: Path,
        max_rounds: int = 100,
        round_timeout: int = 60,
        verbose: bool = False,
        log_dir: Path | None = None,
        max_recursion_depth: int = 5,
        sub_model: str | None = None,
        compaction_threshold: int = 4000,
        dry_run: bool = False,
        auto_commit: bool = False,
    ):
        self.model = model
        self.project_root = Path(project_root).resolve()
        self.max_rounds = max_rounds
        self.round_timeout = round_timeout
        self.verbose = verbose
        self.log_dir = log_dir
        self.max_recursion_depth = max_recursion_depth
        self.sub_model = sub_model
        self.compaction_threshold = compaction_threshold
        self.dry_run = dry_run
        self.auto_commit = auto_commit
        self._trajectory: list[SessionEvent] = []
        self._recursion_mgr = SubLLMManager(max_depth=max_recursion_depth)

    def run(self, prompt: str) -> SessionResult:
        """Run a complete session for the given prompt."""
        self._trajectory = []
        logger = TrajectoryLogger(log_dir=self.log_dir, verbose=self.verbose)

        index = CodebaseIndex.from_root(self.project_root)

        repl = LocalREPL(max_output_lines=100)
        self._inject_context(repl, index, prompt)
        inject_tools(
            repl=repl,
            model=self.model,
            project_root=self.project_root,
            recursion_mgr=self._recursion_mgr,
            max_rounds=self.max_rounds,
        )

        from whiz.agent.compaction import CompactionTrigger, Compactor
        compaction_trigger = CompactionTrigger(threshold=self.compaction_threshold)
        compactor = Compactor(model=self.model)

        for round_num in range(1, self.max_rounds + 1):
            if compaction_trigger.should_compact(repl):
                compactor.compact(repl)
                logger.log(round_num, "compaction", "Context compacted")

            code = self._call_llm(repl, round_num, logger)
            if code is None:
                continue

            logger.log(round_num, "code", code, verbose_only=True)

            raw_output = repl.exec_code(code)

            has_error = False
            error_msg = None
            try:
                entry = repl.history[-1]
                if entry.has_error:
                    has_error = True
                    error_msg = entry.error
            except IndexError:
                pass

            event = SessionEvent(
                round_num=round_num,
                code=code,
                output=raw_output,
                error=error_msg,
            )
            self._trajectory.append(event)

            if has_error:
                logger.log(round_num, "error", error_msg if error_msg else "unknown error", verbose_only=True)
            else:
                logger.log(round_num, "output", raw_output, verbose_only=True)

            ns = repl.get_namespace()
            if "_done" in ns:
                value = ns.get("_done_value")
                logger.log(round_num, "complete", str(value))
                if self.auto_commit:
                    self._auto_commit(value)
                logger.save()
                return SessionResult(
                    success=True,
                    value=value,
                    rounds=round_num,
                    trajectory=list(self._trajectory),
                )

        logger.save()
        return SessionResult(
            success=False,
            value=None,
            rounds=self.max_rounds,
            trajectory=list(self._trajectory),
            error=f"Max rounds ({self.max_rounds}) exceeded without completion",
        )

    def _auto_commit(self, value: Any) -> None:
        """Create a git commit. Uses a simple message, no extra LLM call."""
        import subprocess
        try:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=str(self.project_root),
                capture_output=True,
                timeout=30,
            )
            commit_msg = f"Whiz: {str(value)[:72]}"
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(self.project_root),
                capture_output=True,
                timeout=30,
            )
        except Exception:
            pass  # Auto-commit is best-effort

    def _inject_context(self, repl: LocalREPL, index: CodebaseIndex, prompt: str) -> None:
        """Inject codebase context and user prompt into the REPL."""
        variables = index.to_repl_variables()
        variables["user_prompt"] = prompt
        for name, value in variables.items():
            repl._namespace[name] = value

    def _call_llm(self, repl: LocalREPL, round_num: int, logger: TrajectoryLogger) -> str | None:
        """Build messages and call the LLM. Returns code to execute, or None."""
        messages = self._build_messages(repl)
        response = self.model.chat_completion(messages, model="")
        return extract_code(response.content)

    def _build_messages(self, repl: LocalREPL) -> list[dict[str, str]]:
        """Build the message list for the LLM from REPL history."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for entry in repl.history:
            if entry.code.strip():
                messages.append({"role": "assistant", "content": entry.code})
            output = entry.output
            if entry.has_error:
                output = f"Error: {entry.error}"
            if output.strip():
                messages.append({"role": "user", "content": output})
        return messages
