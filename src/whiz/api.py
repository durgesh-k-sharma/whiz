"""Library API: clean public interface for programmatic use."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from whiz.models.base import BaseModel, LLMResponse
from whiz.models.openai import OpenAIModel
from whiz.agent.loop import Orchestrator, SessionResult, SessionEvent
from whiz.agent.interactive import InteractiveSession
from whiz.config import Profile


class Session:
    """High-level public API for running Whiz sessions.

    Usage:
        session = Session(model=OpenAIModel(model="gpt-4o", api_key="..."))
        result = session.run("refactor the auth module")
        print(result.value)

        # Async:
        result = await session.arun("refactor the auth module")
    """

    def __init__(
        self,
        model: BaseModel | None = None,
        project_root: Path | str | None = None,
        max_rounds: int = 100,
        max_recursion_depth: int = 5,
        compaction_threshold: int = 4000,
        verbose: bool = False,
        dry_run: bool = False,
        auto_commit: bool = False,
        log_dir: Path | None = None,
    ):
        self.model = model or OpenAIModel()
        self.project_root = Path(project_root).resolve() if project_root else Path.cwd()
        self.max_rounds = max_rounds
        self.max_recursion_depth = max_recursion_depth
        self.compaction_threshold = compaction_threshold
        self.verbose = verbose
        self.dry_run = dry_run
        self.auto_commit = auto_commit
        self.log_dir = log_dir

    def run(self, prompt: str) -> SessionResult:
        """Run a synchronous session."""
        orch = Orchestrator(
            model=self.model,
            project_root=self.project_root,
            max_rounds=self.max_rounds,
            max_recursion_depth=self.max_recursion_depth,
            compaction_threshold=self.compaction_threshold,
            verbose=self.verbose,
            dry_run=self.dry_run,
            auto_commit=self.auto_commit,
            log_dir=self.log_dir,
        )
        return orch.run(prompt)

    async def arun(self, prompt: str) -> SessionResult:
        """Run an async session with interactive steering support."""
        session = InteractiveSession(
            model=self.model,
            project_root=self.project_root,
            max_rounds=self.max_rounds,
            max_recursion_depth=self.max_recursion_depth,
            compaction_threshold=self.compaction_threshold,
            verbose=self.verbose,
            log_dir=self.log_dir,
        )
        return await session.run(prompt)
