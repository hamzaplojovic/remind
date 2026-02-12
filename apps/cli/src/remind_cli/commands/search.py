"""Search command - find reminders."""

import typer

from remind_database import DatabaseConfig, DatabaseSession
from remind_cli.services.reminder_service import ReminderService
from remind_cli import output


def search(
    query: str = typer.Argument(..., help="Search query"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Search reminders by text.

    Examples:
      remind search grocery
      remind search 'buy groceries' --json
    """
    try:
        db_config = DatabaseConfig()
        db_session = DatabaseSession(db_config)

        with db_session.get_session() as session:
            reminder_service = ReminderService(session)
            reminders = reminder_service.search_reminders(query)

        if not reminders:
            output.info(f"No reminders matching '{query}'")
            return

        if json_output:
            data = [
                {
                    "id": r.id,
                    "text": r.text,
                    "due_at": r.due_at.isoformat(),
                    "priority": r.priority.value,
                }
                for r in reminders
            ]
            output.print_json(data)
        else:
            rows = [
                {
                    "id": r.id,
                    "text": r.text[:50] + "..." if len(r.text) > 50 else r.text,
                    "due": r.due_at.strftime("%Y-%m-%d %H:%M"),
                    "priority": r.priority.value,
                }
                for r in reminders
            ]
            output.reminders_table(rows)

    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
