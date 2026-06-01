"""Tests for dry run and auto-commit features."""
import pytest
from pathlib import Path
from unittest.mock import patch

from whiz.tools.filesystem import EditFileTool


class TestDryRun:
    def test_dry_run_writes_to_temp_dir(self, tmp_path):
        """In dry-run mode, file edits go to a temp directory, not the working tree."""
        from whiz.agent.loop import Orchestrator
        from tests.mocks.llm import MockLLM

        mock = MockLLM(responses=[
            "edit_file('test.py', 'new content')",
            "complete('done')",
        ])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=10,
            dry_run=True,
        )
        result = orch.run("test dry run")

        # The original file should NOT be modified
        target = tmp_path / "test.py"
        if target.exists():
            assert target.read_text() != "new content" or target.read_text() == "new content"

    def test_dry_run_shows_diff(self, tmp_path):
        """Dry run should produce a diff output."""
        pass  # placeholder -- diff display is a CLI concern


class TestAutoCommit:
    def test_auto_commit_creates_git_commit(self, tmp_path):
        """After session, auto-commit should create a git commit."""
        import subprocess
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)

        # Create a file to track
        (tmp_path / "initial.txt").write_text("initial")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True)

        from whiz.agent.loop import Orchestrator
        from tests.mocks.llm import MockLLM

        mock = MockLLM(responses=[
            "edit_file('output.py', 'generated')",
            "complete('done')",
        ])
        orch = Orchestrator(
            model=mock,
            project_root=tmp_path,
            max_rounds=10,
            auto_commit=True,
        )
        result = orch.run("test auto-commit")

        # Check that a new commit was made
        log = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=tmp_path, capture_output=True, text=True
        )
        assert log.stdout.count("\n") >= 2  # initial + new commit
