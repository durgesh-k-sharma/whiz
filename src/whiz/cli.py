import click
import os
import sys
import asyncio
from pathlib import Path

from whiz.config import load_config, resolve_profile
from whiz.agent.loop import Orchestrator
from whiz.agent.interactive import InteractiveSession


def _resolve_active(profile_flag):
    """Resolve the active profile from config."""
    config = load_config()
    return resolve_profile(config, profile_flag=profile_flag)


def _build_model(profile):
    """Create a model backend from a resolved profile."""
    backend = profile.backend
    model_name = profile.model
    api_key = (
        os.environ.get("OPENROUTER_API_KEY", "")
        or os.environ.get("ANTHROPIC_API_KEY", "")
        or os.environ.get("OPENAI_API_KEY", "")
    )

    if not api_key and backend != "ollama":
        click.echo(
            f"Error: No API key found for {backend}.\n"
            f"Set one of: OPENROUTER_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY",
            err=True,
        )
        sys.exit(1)

    if backend == "openai":
        from whiz.models.openai import OpenAIModel
        return OpenAIModel(model=model_name, api_key=api_key or None)
    elif backend == "anthropic":
        from whiz.models.anthropic import AnthropicModel
        return AnthropicModel(model=model_name, api_key=api_key or None)
    elif backend == "openrouter":
        from whiz.models.openai import OpenAIModel
        return OpenAIModel(
            model=model_name.replace("openrouter/", ""),
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    elif backend == "ollama":
        from whiz.models.ollama import OllamaModel
        return OllamaModel(model=model_name)
    else:
        raise RuntimeError(f"Unknown backend: {backend}")


def _execute_run(model, prompt, verbose, quiet, auto_commit, max_rounds, profile, dry_run=False):
    """Execute a one-shot run."""
    effective_max_rounds = max_rounds or profile.max_repl_rounds

    orch = Orchestrator(
        model=model,
        project_root=Path.cwd(),
        max_rounds=effective_max_rounds,
        verbose=verbose,
        dry_run=dry_run,
        auto_commit=auto_commit,
    )

    result = orch.run(prompt)

    if not quiet:
        if result.success:
            click.echo(f"\nResult: {result.value}")
        else:
            click.echo(f"\nFailed: {result.error}", err=True)
        click.echo(f"Rounds: {result.rounds}")

    sys.exit(0 if result.success else 1)


# --- Shared option decorators ---

def _profile_option(f):
    return click.option(
        "--profile", "profile_flag", default=None,
        help="Configuration profile (or-free, or-claude, or-gpt4o, or-auto)",
    )(f)

def _verbose_option(f):
    return click.option("--verbose", is_flag=True, default=False, help="Show REPL trace")(f)

def _quiet_option(f):
    return click.option("--quiet", is_flag=True, default=False, help="Suppress output")(f)


# --- CLI entry point ---

@click.group(invoke_without_command=True)
@_profile_option
@_verbose_option
@_quiet_option
@click.version_option(version="0.1.0")
@click.pass_context
def main(ctx, profile_flag, verbose, quiet):
    """Whiz -- A Recursive Language Model coding agent.

    Run a task:
        whiz run "find all TODO comments"

    Interactive mode:
        whiz interactive "explore the codebase"
    """
    ctx.ensure_object(dict)
    ctx.obj["profile_flag"] = profile_flag
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet

    if ctx.invoked_subcommand is None:
        # Default: enter interactive mode
        import asyncio
        from whiz.agent.interactive import InteractiveSession
        config = load_config()
        active = resolve_profile(config, profile_flag=profile_flag)
        model = _build_model(active)
        session = InteractiveSession(
            model=model,
            project_root=Path.cwd(),
            max_rounds=active.max_repl_rounds,
            max_recursion_depth=active.max_depth,
            verbose=verbose,
        )
        result = asyncio.run(session.run(""))
        sys.exit(0 if result.success else 1)


# --- run command ---

@main.command()
@click.argument("prompt")
@_profile_option
@_verbose_option
@_quiet_option
@click.option("--auto-commit", is_flag=True, default=False, help="Auto git-commit after")
@click.option("--max-rounds", default=None, type=int, help="Max REPL rounds")
@click.pass_context
def run(ctx, prompt, profile_flag, verbose, quiet, auto_commit, max_rounds):
    """Run a one-shot task.

    \b
    Examples:
        whiz run "find all TODO comments"
        whiz run --profile or-free "summarize this project"
        whiz run --verbose --auto-commit "refactor auth module"
    """
    if profile_flag is None:
        profile_flag = ctx.obj.get("profile_flag")
    active = _resolve_active(profile_flag)
    model = _build_model(active)
    _execute_run(model, prompt, verbose, quiet, auto_commit, max_rounds, active)


# --- interactive command ---

@main.command()
@click.argument("prompt")
@_profile_option
@_verbose_option
@_quiet_option
@click.option("--max-rounds", default=None, type=int, help="Max REPL rounds")
@click.pass_context
def interactive(ctx, prompt, profile_flag, verbose, quiet, max_rounds):
    """Run an interactive session with mid-session steering.

    \b
    Example:
        whiz interactive "explore the codebase"
    """
    if profile_flag is None:
        profile_flag = ctx.obj.get("profile_flag")
    active = _resolve_active(profile_flag)
    model = _build_model(active)

    effective_max_rounds = max_rounds or active.max_repl_rounds

    session = InteractiveSession(
        model=model,
        project_root=Path.cwd(),
        max_rounds=effective_max_rounds,
        max_recursion_depth=active.max_depth,
        verbose=verbose,
    )

    result = asyncio.run(session.run(prompt))

    if not quiet:
        if result.success:
            click.echo(f"\nResult: {result.value}")
        else:
            click.echo(f"\nFailed: {result.error}", err=True)
        click.echo(f"Rounds: {result.rounds}")

    sys.exit(0 if result.success else 1)
