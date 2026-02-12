"""Done command - mark reminder as complete."""

import typer

from remind_shared import ValidationError
from remind_database import DatabaseConfig, DatabaseSession
from remind_cli.services.reminder_service import ReminderService
from remind_cli import output


def done(reminder_id: int = typer.Argument(..., help="Reminder ID")) -> None:
    """Mark a reminder as done.

    Examples:
      remind done 1
      remind done 42
    """
    try:
        db_config = DatabaseConfig()
        db_session = DatabaseSession(db_config)

        with db_session.get_session() as session:
            reminder_service = ReminderService(session)
            reminder = reminder_service.mark_reminder_done(reminder_id)

        output.blank()
        output.success(f"Done: {reminder.text}")
        output.blank()

    except ValidationError as e:
        output.error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
