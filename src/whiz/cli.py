import click
import os
import sys
import asyncio
from pathlib import Path

from whiz.config import load_config, resolve_profile
from whiz.agent.loop import Orchestrator
from whiz.agent.interactive import InteractiveSession


def _create_model(profile):
    """Create a model backend from a resolved profile."""
    backend = profile.backend
    model_name = profile.model

    if backend == "openai":
        from whiz.models.openai import OpenAIModel
        return OpenAIModel(model=model_name, api_key=profile.api_key or None)
    elif backend == "anthropic":
        try:
            from whiz.models.anthropic import AnthropicModel
            return AnthropicModel(model=model_name, api_key=profile.api_key or None)
        except RuntimeError:
            # Fallback: use OpenAI-compatible interface if anthropic not installed
            from whiz.models.openai import OpenAIModel
            return OpenAIModel(model=model_name, api_key=profile.api_key or None)
    elif backend == "openrouter":
        from whiz.models.openai import OpenAIModel
        return OpenAIModel(
            model=model_name.replace("openrouter/", ""),
            base_url="https://openrouter.ai/api/v1",
            api_key=profile.api_key or os.environ.get("OPENROUTER_API_KEY", ""),
        )
    elif backend == "ollama":
        from whiz.models.ollama import OllamaModel
        return OllamaModel(model=model_name)
    else:
        raise RuntimeError(f"Unknown backend: {backend}")


@click.group(invoke_without_command=True)
@click.option("--profile", default=None, help="Configuration profile to use")
@click.option("--verbose", is_flag=True, default=False, help="Verbose output")
@click.option("--quiet", is_flag=True, default=False, help="Suppress output")
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without applying")
@click.pass_context
def main(ctx, profile, verbose, quiet, dry_run):
    """Whiz -- A Recursive Language Model coding agent."""
    ctx.ensure_object(dict)
    ctx.obj["profile"] = profile
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["dry_run"] = dry_run

    config = load_config()
    active = resolve_profile(config, profile_flag=profile)
    ctx.obj["config"] = config
    ctx.obj["active_profile"] = active

    if ctx.invoked_subcommand is None:
        # Default: enter interactive mode
        click.echo(f"Whiz v0.1.0 [{active.name}]")
        click.echo("Starting interactive mode... (not yet fully implemented)")
        click.echo("Use 'whiz run <prompt>' for one-shot mode.")
        click.echo("Use 'whiz interactive <prompt>' for interactive mode with steering.")


@main.command()
@click.argument("prompt")
@click.option("--profile", default=None, help="Configuration profile to use")
@click.option("--verbose", is_flag=True, default=False, help="Verbose output")
@click.option("--quiet", is_flag=True, default=False, help="Suppress output")
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without applying")
@click.option("--max-rounds", default=None, type=int, help="Max REPL rounds")
def run(prompt, profile, verbose, quiet, dry_run, max_rounds):
    """Run a one-shot task."""
    config = load_config()
    active = resolve_profile(config, profile_flag=profile)

    try:
        model = _create_model(active)
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    effective_max_rounds = max_rounds or active.max_repl_rounds

    orch = Orchestrator(
        model=model,
        project_root=click.get_current_context().obj.get("project_root") or Path.cwd(),
        max_rounds=effective_max_rounds,
        verbose=verbose,
    )

    result = orch.run(prompt)

    if not quiet:
        if result.success:
            click.echo(f"\nResult: {result.value}")
        else:
            click.echo(f"\nFailed: {result.error}", err=True)
        click.echo(f"Rounds: {result.rounds}")

    sys.exit(0 if result.success else 1)


@main.command()
@click.argument("prompt")
@click.option("--profile", default=None, help="Configuration profile to use")
@click.option("--verbose", is_flag=True, default=False, help="Verbose output")
@click.option("--quiet", is_flag=True, default=False, help="Suppress output")
@click.option("--max-rounds", default=None, type=int, help="Max REPL rounds")
def interactive(prompt, profile, verbose, quiet, max_rounds):
    """Run an interactive session with mid-session steering support."""
    config = load_config()
    active = resolve_profile(config, profile_flag=profile)

    try:
        model = _create_model(active)
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

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
