"""Orchestrator: the outer agent loop that drives RLM sessions."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from whiz.context.indexer import CodebaseIndex
from whiz.models.base import BaseModel, LLMResponse
from whiz.repl.core import LocalREPL
from whiz.tools.search import SearchTool
from whiz.tools.filesystem import ReadFilesTool, EditFileTool, RunTestsTool
from whiz.logging.trajectory import TrajectoryLogger
from whiz.agent.recursion import create_sub_llm_callable


class RecursionError(Exception):
    """Raised when max recursion depth is exceeded."""
    pass


@dataclass
class SubLLMManager:
    """Tracks recursion depth across parent-child session trees."""
    max_depth: int = 5
    _depth: int = field(default=0, init=False, repr=False)

    @property
    def current_depth(self) -> int:
        return self._depth

    def enter(self) -> None:
        if self._depth >= self.max_depth:
            raise RecursionError(
                f"Max recursion depth ({self.max_depth}) exceeded. "
                f"Current depth: {self._depth}"
            )
        self._depth += 1

    def exit(self) -> None:
        if self._depth > 0:
            self._depth -= 1


SYSTEM_PROMPT = """You are Whiz, an AI coding agent with access to a Python REPL environment.

You can write arbitrary Python code to explore and manipulate the codebase. All your code runs in a persistent Python REPL where variables you define are remembered across turns.

Available tools (already imported and ready to use as Python variables):
- search(query: str) -> str — Search the codebase for a pattern. Returns matching file paths and lines.
- read_files(paths: list[str]) -> str — Read the contents of one or more files.
- edit_file(path: str, content: str) -> str — Write content to a file. Creates the file if it doesn't exist.
- run_tests(command: str | None = None) -> str — Run tests in the project. Auto-detects pytest if no command given.
- sub_llm(prompt: str, context: str = "") -> str — Spawn a sub-LLM to handle a sub-task. Returns the sub-LLM's response.
- complete(value) — Signal that you are done. The session will end and value will be returned.

Standard library modules are available: os, sys, json, re, math, pathlib, subprocess, etc.

The codebase has been indexed for you. The following variables are already in your REPL:
- file_tree — A tree listing of the project files
- readme — The project README (truncated if long)
- project_root — Absolute path to the project root

Write Python code to accomplish the task. When done, call complete(your_answer).
"""


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
    ):
        self.model = model
        self.project_root = Path(project_root).resolve()
        self.max_rounds = max_rounds
        self.round_timeout = round_timeout
        self.verbose = verbose
        self.log_dir = log_dir
        self.max_recursion_depth = max_recursion_depth
        self.sub_model = sub_model
        self._trajectory: list[SessionEvent] = []
        self._recursion_mgr = SubLLMManager(max_depth=max_recursion_depth)

    def run(self, prompt: str) -> SessionResult:
        """Run a complete session for the given prompt."""
        self._trajectory = []
        logger = TrajectoryLogger(log_dir=self.log_dir, verbose=self.verbose)

        # Build index
        index = CodebaseIndex.from_root(self.project_root)

        # Create REPL and inject tools + context
        repl = LocalREPL(max_output_lines=100)
        self._inject_context(repl, index, prompt)
        self._inject_tools(repl)

        # Inner loop
        for round_num in range(1, self.max_rounds + 1):
            code = self._call_llm(repl, round_num, logger)
            if code is None:
                continue

            logger.log(round_num, "code", code, verbose_only=True)

            # Execute in REPL
            raw_output = repl.exec_code(code)

            # Check for REPL error
            has_error = False
            error_msg = None
            output = raw_output
            try:
                entry = repl.history[-1]
                if entry.has_error:
                    has_error = True
                    error_msg = entry.error
                    output = entry.error
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
                logger.log(round_num, "output", output, verbose_only=True)

            # Check if complete was called
            ns = repl.get_namespace()
            if "_done" in ns:
                value = ns.get("_done_value")
                logger.log(round_num, "complete", str(value))
                logger.save()
                return SessionResult(
                    success=True,
                    value=value,
                    rounds=round_num,
                    trajectory=list(self._trajectory),
                )

        # Max rounds exceeded
        logger.save()
        return SessionResult(
            success=False,
            value=None,
            rounds=self.max_rounds,
            trajectory=list(self._trajectory),
            error=f"Max rounds ({self.max_rounds}) exceeded without completion",
        )

    def _inject_context(self, repl: LocalREPL, index: CodebaseIndex, prompt: str) -> None:
        """Inject codebase context and user prompt into the REPL."""
        variables = index.to_repl_variables()
        variables["user_prompt"] = prompt
        for name, value in variables.items():
            repl._namespace[name] = value

    def _inject_tools(self, repl: LocalREPL) -> None:
        """Inject tool callables into the REPL namespace."""
        def complete(value):
            repl._namespace["_done"] = True
            repl._namespace["_done_value"] = value
            return value

        sub_llm = create_sub_llm_callable(
            model=self.model,
            project_root=self.project_root,
            recursion_mgr=self._recursion_mgr,
            max_rounds=min(self.max_rounds, 50),
        )

        search_tool = SearchTool(project_root=self.project_root)
        read_tool = ReadFilesTool(project_root=self.project_root)
        edit_tool = EditFileTool(project_root=self.project_root)
        run_tests_tool = RunTestsTool(project_root=self.project_root)

        repl._namespace["search"] = search_tool.search
        repl._namespace["read_files"] = read_tool.read_files
        repl._namespace["edit_file"] = edit_tool.edit_file
        repl._namespace["run_tests"] = run_tests_tool.run_tests
        repl._namespace["sub_llm"] = sub_llm
        repl._namespace["complete"] = complete

    def _call_llm(self, repl: LocalREPL, round_num: int, logger: TrajectoryLogger) -> str | None:
        """Build messages and call the LLM. Returns code to execute, or None to skip."""
        messages = self._build_messages(repl)
        response = self.model.chat_completion(messages, model="")
        code = self._extract_code(response.content)
        return code

    def _build_messages(self, repl: LocalREPL) -> list[dict[str, str]]:
        """Build the message list for the LLM from REPL history."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add history as alternating assistant/user turns
        for entry in repl.history:
            if entry.code.strip():
                messages.append({"role": "assistant", "content": entry.code})
            output = entry.output
            if entry.has_error:
                output = f"Error: {entry.error}"
            if output.strip():
                messages.append({"role": "user", "content": output})

        return messages

    def _extract_code(self, content: str) -> str | None:
        """Extract executable Python code from the LLM response."""
        content = content.strip()
        if not content:
            return None

        # If the response is wrapped in markdown code blocks, extract from them
        if "```" in content:
            blocks = []
            in_block = False
            block_lines = []
            for line in content.split("\n"):
                if line.strip().startswith("```"):
                    if in_block:
                        blocks.append("\n".join(block_lines))
                        block_lines = []
                        in_block = False
                    else:
                        in_block = True
                elif in_block:
                    block_lines.append(line)
            if blocks:
                # Return the last code block
                return blocks[-1].strip()

        # No code blocks -- treat the whole response as code
        # But filter out plain English explanations
        try:
            compile(content, "<llm>", "exec")
            return content
        except SyntaxError:
            # Not valid Python -- try to find a Python-like line
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        compile(line, "<llm>", "exec")
                        return line
                    except SyntaxError:
                        continue
            # Last resort: return the content as-is, REPL will handle the error
            return content
