import click

from whiz.config import load_config, resolve_profile


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

    # If no subcommand, enter interactive mode
    if ctx.invoked_subcommand is None:
        click.echo(f"Whiz v0.1.0 [{active.name}]")
        click.echo("Interactive mode not yet implemented. Use 'whiz run <prompt>'.")


@main.command()
@click.argument("prompt")
@click.option("--profile", default=None, help="Configuration profile to use")
@click.option("--verbose", is_flag=True, default=False, help="Verbose output")
@click.option("--quiet", is_flag=True, default=False, help="Suppress output")
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without applying")
def run(prompt, profile, verbose, quiet, dry_run):
    """Run a one-shot task."""
    config = load_config()
    active = resolve_profile(config, profile_flag=profile)
    click.echo(f"Profile: {active.name} ({active.backend}/{active.model})")
    click.echo(f"Prompt: {prompt}")
    click.echo("One-shot mode not yet implemented.")
