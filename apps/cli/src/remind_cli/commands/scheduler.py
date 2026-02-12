"""Scheduler command - manage background reminder service."""

import typer

from remind_cli import output
from remind_cli.services.daemon_service import DaemonService
from remind_cli.services.scheduler_service import run_scheduler


def scheduler(
    enable: bool = typer.Option(False, "--enable", help="Enable scheduler"),
    disable: bool = typer.Option(False, "--disable", help="Disable scheduler"),
    status: bool = typer.Option(False, "--status", help="Show scheduler status"),
    run: bool = typer.Option(False, "--run", help="Run scheduler (internal)"),
) -> None:
    """Manage background reminder scheduler.

    The scheduler runs in the background to send notifications for due reminders.

    Examples:
      remind scheduler --status
      remind scheduler --enable
      remind scheduler --disable
    """
    try:
        daemon = DaemonService()

        if run:
            # Internal: Run the scheduler daemon
            run_scheduler()

        elif enable:
            if daemon.is_installed():
                output.info("Scheduler already enabled")
                output.blank()
                return

            with output.spinner("Installing background scheduler"):
                success = daemon.install()

            if success:
                output.blank()
                output.success("Scheduler installed and started")
                output.info("Will check reminders every 5 minutes")
                output.info("View logs with: tail -f ~/.remind/logs/scheduler.log")
                output.blank()
            else:
                output.blank()
                output.error("Failed to install scheduler")
                raise typer.Exit(1)

        elif disable:
            if not daemon.is_installed():
                output.info("Scheduler not installed")
                output.blank()
                return

            with output.spinner("Disabling scheduler"):
                success = daemon.uninstall()

            if success:
                output.blank()
                output.success("Scheduler disabled")
                output.info("Background reminders stopped")
                output.blank()
            else:
                output.blank()
                output.error("Failed to disable scheduler")
                raise typer.Exit(1)

        elif status:
            output.header("SCHEDULER STATUS")
            if daemon.is_installed():
                output.label_value("Status", "✓ Installed")
                output.label_value("Check interval", "5 minutes")
            else:
                output.label_value("Status", "✗ Not installed")
            output.blank()
            if not daemon.is_installed():
                output.hint("Use --enable to start the scheduler")
            else:
                output.hint("Use --disable to stop the scheduler")
            output.blank()

        else:
            output.header("SCHEDULER")
            output.hint("Use --status to see current status")
            if daemon.is_installed():
                output.hint("Use --disable to stop background reminders")
            else:
                output.hint("Use --enable to start background reminders")
            output.blank()

    except typer.Exit:
        raise
    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
