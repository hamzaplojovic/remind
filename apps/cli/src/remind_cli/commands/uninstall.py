"""Uninstall command - remove Remind from system."""

import typer

from remind_cli.services.config_service import ConfigService
from remind_cli import output


def uninstall(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Uninstall Remind from your system.

    This will:
    - Remove configuration and settings
    - Disable background scheduler
    - Remove CLI from PATH

    Your reminders will be preserved in the database.

    Examples:
      remind uninstall
      remind uninstall --yes
    """
    try:
        if not confirm:
            typer.confirm(
                "Are you sure you want to uninstall Remind? Reminders will be preserved.",
                abort=True,
            )

        config_service = ConfigService()
        config_service.config_file.unlink(missing_ok=True)

        output.blank()
        output.success("Uninstall complete")
        output.blank()
        output.text("Next steps:")
        output.text("  1. Remove 'remind' from your PATH")
        output.text("  2. Reminders preserved in ~/.remind/")
        output.blank()
        output.hint("To reinstall: https://remind.dev/install")
        output.blank()

    except typer.Abort:
        output.info("Cancelled.")
        raise typer.Exit(0)
    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
