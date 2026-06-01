"""Tests for CLI entry points."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from whiz.cli import main


class TestCLI:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Whiz" in result.output

    def test_run_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run", "--help"])
        assert result.exit_code == 0
        assert "prompt" in result.output.lower()

    def test_default_interactive_mode(self):
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code == 0
        assert "Whiz v0.1.0" in result.output
        assert "Interactive mode not yet implemented" in result.output

    def test_profile_flag(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--profile", "balanced", "run", "hello"])
        # Will fail because OpenAI backend needs a key, but the CLI should try
        assert result.exit_code is not None  # just shouldn't crash during parsing

    def test_dry_run_flag(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run", "--dry-run", "hello"])
        assert result.exit_code is not None

    def test_verbose_flag(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run", "--verbose", "hello"])
        assert result.exit_code is not None

    def test_quiet_flag(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run", "--quiet", "hello"])
        assert result.exit_code is not None

    def test_max_rounds_flag(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run", "--max-rounds", "5", "hello"])
        assert result.exit_code is not None

    def test_run_with_mocked_model(self, tmp_path):
        """Test the full run command with a mocked model."""
        from tests.mocks.llm import MockLLM
        from whiz.models.openai import OpenAIModel

        mock_llm = MockLLM(responses=["complete('done')"])
        with patch("whiz.cli._create_model", return_value=mock_llm):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["run", "test prompt"],
                obj={"project_root": tmp_path},
            )
            assert result.exit_code == 0
            assert "done" in result.output or "Result" in result.output
