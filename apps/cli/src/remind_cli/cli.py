"""CLI application factory - registers all commands."""

import typer

from remind_cli import __version__
from remind_cli.commands.add import add
from remind_cli.commands.list import list_cmd
from remind_cli.commands.done import done
from remind_cli.commands.search import search
from remind_cli.commands.login import login
from remind_cli.commands.settings import settings
from remind_cli.commands.doctor import doctor
from remind_cli.commands.usage import usage
from remind_cli.commands.register import register
from remind_cli.commands.upgrade import upgrade
from remind_cli.commands.update import update
from remind_cli.commands.uninstall import uninstall


def scheduler(
    run: bool = typer.Option(False, "--run", help="Run the scheduler daemon"),
) -> None:
    """Background scheduler daemon (internal use)."""
    if run:
        from remind_cli.services.scheduler_service import run_scheduler
        run_scheduler()
    else:
        typer.echo("Use --run to start the scheduler daemon")
        raise typer.Exit(1)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"remind {__version__}")
        raise typer.Exit()


app = typer.Typer(help="Remind: AI-powered reminder CLI")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
    version: bool = typer.Option(
        False, "--version", "-V", callback=version_callback, is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Remind: AI-powered reminder CLI.

    Quick start:
      remind add 'Buy groceries' --due 'tomorrow 5pm'
      remind list
      remind done 1

    For help: remind <command> --help
    """
    # Check for updates (non-blocking, cached, at most once/day)
    if not quiet:
        try:
            from remind_cli.version_check import get_update_notice

            notice = get_update_notice()
            if notice:
                from remind_cli import output as _out

                _out.blank()
                _out.warning(notice)
        except Exception:
            pass  # Never break CLI over version check

    if ctx.invoked_subcommand is None:
        from remind_cli import output

        output.brand()
        output.blank()
        output.console.print("  [header.label]QUICK START[/header.label]")
        output.blank()
        output.command_row("remind add 'task description'", "Create a reminder")
        output.command_row("remind list", "List all reminders")
        output.command_row("remind done 1", "Mark as complete")
        output.command_row("remind search 'keyword'", "Search reminders")
        output.blank()
        output.dot_rule()
        output.blank()
        output.console.print("  [header.label]MORE COMMANDS[/header.label]")
        output.blank()
        output.command_row("remind register", "Sign up for a plan")
        output.command_row("remind login <token>", "Authenticate")
        output.command_row("remind settings", "View settings")
        output.command_row("remind doctor", "Diagnose issues")
        output.command_row("remind usage", "Usage statistics")
        output.command_row("remind upgrade", "View plans")
        output.command_row("remind update", "Update CLI")
        output.blank()
        output.rule()
        output.hint("For detailed help: remind --help")
        output.blank()


# Register all commands
app.command()(add)
app.command(name="list")(list_cmd)
app.command()(done)
app.command()(search)
app.command()(login)
app.command()(settings)
app.command()(doctor)
app.command()(usage)
app.command()(register)
app.command()(upgrade)
app.command()(update)
app.command()(uninstall)
app.command(hidden=True)(scheduler)
