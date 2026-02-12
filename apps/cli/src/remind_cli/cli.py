"""CLI application factory - registers all commands."""

import typer

# Import all command modules
from remind_cli.commands.add import add
from remind_cli.commands.list import list_cmd
from remind_cli.commands.done import done
from remind_cli.commands.search import search
from remind_cli.commands.login import login
from remind_cli.commands.settings import settings
from remind_cli.commands.scheduler import scheduler
from remind_cli.commands.doctor import doctor
from remind_cli.commands.report import report
from remind_cli.commands.upgrade import upgrade
from remind_cli.commands.uninstall import uninstall


app = typer.Typer(help="Remind: AI-powered reminder CLI")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
) -> None:
    """Remind: AI-powered reminder CLI.

    Quick start:
      remind add 'Buy groceries' --due 'tomorrow 5pm'
      remind list
      remind done 1

    For help: remind <command> --help
    """
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
        output.command_row("remind login <token>", "Authenticate")
        output.command_row("remind settings", "View settings")
        output.command_row("remind scheduler --help", "Background reminders")
        output.command_row("remind doctor", "Diagnose issues")
        output.command_row("remind report", "Usage statistics")
        output.command_row("remind upgrade", "View plans")
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
app.command()(scheduler)
app.command()(doctor)
app.command()(report)
app.command()(upgrade)
app.command()(uninstall)
