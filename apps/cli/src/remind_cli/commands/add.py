"""Add command - create a new reminder."""

from datetime import datetime

import typer

from remind_shared import PriorityLevel, ValidationError
from remind_database import DatabaseConfig, DatabaseSession
from remind_cli.services.reminder_service import ReminderService
from remind_cli.services.ai_service import AIService
from remind_cli import output


def add(
    text: str = typer.Argument(..., help="Reminder text"),
    due: str | None = typer.Option(None, "--due", "-d", help="Due date/time (e.g., 'tomorrow 5pm')"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Priority: high, medium, low"),
    project: str | None = typer.Option(None, "--project", "-P", help="Project context"),
    allow_past_due: bool = typer.Option(False, "--allow-past-due", hidden=True, help="Allow past due dates (testing only)"),
) -> None:
    """Add a new reminder.

    Examples:
      remind add 'Buy groceries'
      remind add 'Call mom' --due 'tomorrow 5pm' --priority high
      remind add 'Review PR' --project work
    """
    try:
        from dateparser import parse as dateparser_parse

        # Parse due date
        if due:
            due_dt = dateparser_parse(due)
            if not due_dt:
                output.error(f"Could not parse due date: {due}")
                raise typer.Exit(1)
        else:
            due_dt = datetime.now()

        # Validate priority
        try:
            priority_level = PriorityLevel(priority.lower())
        except ValueError:
            output.error(f"Invalid priority: {priority}. Use: high, medium, low")
            raise typer.Exit(1)

        # Initialize services
        db_config = DatabaseConfig()
        db_session = DatabaseSession(db_config)

        # Get AI suggestion
        ai_text = None
        ai_service = AIService()
        try:
            with output.spinner("Getting AI suggestion"):
                ai_response = ai_service.suggest_reminder(text)
            ai_text = ai_response.suggested_text
            output.ai_suggestion(ai_text)
        except Exception as e:
            output.warning(f"AI suggestion failed: {e}")

        # Create reminder with context manager
        with db_session.get_session() as session:
            reminder_service = ReminderService(session)
            reminder = reminder_service.create_reminder(
                text=text,
                due_at=due_dt,
                priority=priority_level,
                project_context=project,
                ai_suggested_text=ai_text,
                allow_past_due=allow_past_due,
            )

        output.blank()
        output.success(f"Reminder saved (#{reminder.id})")
        output.label_value("Text", reminder.text)
        output.label_value("Due", str(reminder.due_at))
        output.label_value("Priority", priority_level.value.upper())
        output.blank()

    except ValidationError as e:
        output.error(str(e))
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
