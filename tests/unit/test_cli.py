"""Tests for CLI entry points."""
import pytest
from click.testing import CliRunner

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

    def test_run_shows_profile(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run", "hello world"])
        assert result.exit_code == 0
        assert "Profile:" in result.output
        assert "balanced" in result.output

    def test_run_shows_prompt(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run", "fix the auth bug"])
        assert "Prompt:" in result.output
        assert "fix the auth bug" in result.output

    def test_default_interactive_mode(self):
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code == 0
        assert "Whiz v0.1.0" in result.output
        assert "Interactive mode not yet implemented" in result.output

    def test_profile_flag(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--profile", "balanced", "run", "hello"])
        assert result.exit_code == 0

    def test_dry_run_flag(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run", "--dry-run", "hello"])
        assert result.exit_code == 0

    def test_verbose_flag(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run", "--verbose", "hello"])
        assert result.exit_code == 0

    def test_quiet_flag(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run", "--quiet", "hello"])
        assert result.exit_code == 0
