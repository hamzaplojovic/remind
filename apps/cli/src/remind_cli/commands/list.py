"""List command - display reminders."""

from typing import Optional

import typer

from remind_database import DatabaseConfig, DatabaseSession
from remind_cli.services.reminder_service import ReminderService
from remind_cli import output


def list_cmd(
    all: bool = typer.Option(False, "--all", "-a", help="Show done reminders too"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="Filter by priority"),
) -> None:
    """List reminders.

    Examples:
      remind list                    # Active reminders
      remind list --all              # All reminders
      remind list --priority high    # High priority only
      remind list --json             # JSON format
    """
    try:
        db_config = DatabaseConfig()
        db_session = DatabaseSession(db_config)

        with db_session.get_session() as session:
            reminder_service = ReminderService(session)

            if all:
                reminders = reminder_service.list_all_reminders()
            else:
                reminders = reminder_service.list_active_reminders()

            if priority:
                reminders = [r for r in reminders if r.priority.value == priority.lower()]

        if json_output:
            data = [
                {
                    "id": r.id,
                    "text": r.text,
                    "due_at": r.due_at.isoformat(),
                    "priority": r.priority.value,
                    "done": r.done_at is not None,
                }
                for r in reminders
            ]
            output.print_json(data)
        else:
            if not reminders:
                output.info("No reminders found")
                return

            rows = [
                {
                    "id": r.id,
                    "text": r.text[:50] + "..." if len(r.text) > 50 else r.text,
                    "due": r.due_at.strftime("%Y-%m-%d %H:%M"),
                    "priority": r.priority.value,
                    "done": r.done_at is not None,
                }
                for r in reminders
            ]
            output.reminders_table(rows)

    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
