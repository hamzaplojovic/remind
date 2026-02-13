"""MCP server for Remind CLI — exposes reminder tools to Claude Code and other MCP clients."""

import os
from datetime import datetime, timezone

from dateparser import parse as dateparser_parse
from fastmcp import FastMCP

from remind_database import DatabaseConfig, DatabaseSession
from remind_shared import PriorityLevel
from remind_cli.services.reminder_service import ReminderService

mcp = FastMCP("Remind")


def _get_db_session() -> DatabaseSession:
    """Create a database session using default config."""
    return DatabaseSession(DatabaseConfig())


@mcp.tool
def add_reminder(
    text: str,
    due: str | None = None,
    priority: str = "medium",
    project: str | None = None,
) -> str:
    """Add a new reminder with optional due date, priority, and project context.

    Args:
        text: The reminder text (e.g., "buy milk", "deploy v2.0")
        due: Natural language due date (e.g., "tomorrow 5pm", "in 2 hours", "next friday").
             If omitted, tries to parse a date from the text.
        priority: Priority level — "high", "medium", or "low". Defaults to "medium".
        project: Optional project context to group reminders (e.g., "work", "personal").

    Returns:
        Confirmation message with reminder details.
    """
    try:
        priority_level = PriorityLevel(priority.lower())
    except ValueError:
        return f"Invalid priority: {priority}. Use: high, medium, low"

    # Parse due date
    due_dt = None
    if due:
        due_dt = dateparser_parse(due)
        if not due_dt:
            return f"Could not parse due date: {due}"

    if due_dt is None:
        due_dt = dateparser_parse(text, settings={"PREFER_DATES_FROM": "future"})
    if due_dt is None:
        due_dt = datetime.now()

    db_session = _get_db_session()
    try:
        with db_session.get_session() as session:
            service = ReminderService(session)
            reminder = service.create_reminder(
                text=text,
                due_at=due_dt,
                priority=priority_level,
                project_context=project,
            )
        return (
            f"Reminder #{reminder.id} saved.\n"
            f"Text: {reminder.text}\n"
            f"Due: {reminder.due_at}\n"
            f"Priority: {priority_level.value}"
        )
    except Exception as e:
        return f"Error creating reminder: {e}"
    finally:
        db_session.close()


@mcp.tool
def list_reminders(include_done: bool = False) -> str:
    """List all reminders. Shows active (not completed) reminders by default.

    Args:
        include_done: If True, also show completed reminders. Defaults to False.

    Returns:
        Formatted list of reminders with ID, text, due date, priority, and status.
    """
    db_session = _get_db_session()
    try:
        with db_session.get_session() as session:
            service = ReminderService(session)
            reminders = service.list_all_reminders() if include_done else service.list_active_reminders()

        if not reminders:
            return "No reminders found."

        lines = []
        now = datetime.now(timezone.utc)
        for r in reminders:
            status = ""
            if r.done_at:
                status = " [DONE]"
            else:
                due_utc = r.due_at.replace(tzinfo=timezone.utc) if r.due_at.tzinfo is None else r.due_at
                if due_utc < now:
                    status = " [OVERDUE]"

            project_tag = f" ({r.project_context})" if r.project_context else ""
            lines.append(
                f"#{r.id} [{r.priority.value.upper()}] {r.text}{project_tag} — due: {r.due_at}{status}"
            )

        return "\n".join(lines)
    finally:
        db_session.close()


@mcp.tool
def complete_reminder(reminder_id: int) -> str:
    """Mark a reminder as done/completed.

    Args:
        reminder_id: The ID number of the reminder to complete (e.g., 1, 5, 12).

    Returns:
        Confirmation that the reminder was completed.
    """
    db_session = _get_db_session()
    try:
        with db_session.get_session() as session:
            service = ReminderService(session)
            reminder = service.mark_reminder_done(reminder_id)
        return f"Completed: #{reminder.id} — {reminder.text}"
    except Exception as e:
        return f"Error: {e}"
    finally:
        db_session.close()


@mcp.tool
def search_reminders(query: str) -> str:
    """Search reminders by text content.

    Args:
        query: Search term to find in reminder text (case-insensitive).

    Returns:
        Matching reminders or a message if none found.
    """
    db_session = _get_db_session()
    try:
        with db_session.get_session() as session:
            service = ReminderService(session)
            results = service.search_reminders(query)

        if not results:
            return f"No reminders matching '{query}'."

        lines = []
        for r in results:
            status = " [DONE]" if r.done_at else ""
            lines.append(f"#{r.id} [{r.priority.value.upper()}] {r.text} — due: {r.due_at}{status}")

        return "\n".join(lines)
    finally:
        db_session.close()


@mcp.tool
def delete_reminder(reminder_id: int) -> str:
    """Permanently delete a reminder.

    Args:
        reminder_id: The ID number of the reminder to delete.

    Returns:
        Confirmation that the reminder was deleted.
    """
    db_session = _get_db_session()
    try:
        with db_session.get_session() as session:
            service = ReminderService(session)
            deleted = service.delete_reminder(reminder_id)
        if deleted:
            return f"Deleted reminder #{reminder_id}."
        return f"Reminder #{reminder_id} not found."
    except Exception as e:
        return f"Error: {e}"
    finally:
        db_session.close()


@mcp.tool
def agent_reminder(
    task: str,
    due: str,
    project_path: str | None = None,
) -> str:
    """Schedule Claude Code to autonomously execute a task at a specific time.

    WARNING: This creates a reminder that will run Claude Code with --dangerously-skip-permissions
    at the scheduled time. Claude will have full read/write/execute access to the project directory.

    The reminder is stored locally. When the scheduler fires it, it will execute:
        claude -p "<task>" --dangerously-skip-permissions

    Args:
        task: The task description for Claude to execute (e.g., "refactor the auth module",
              "run tests and fix failures", "review yesterday's git diff").
        due: When to execute — natural language (e.g., "in 2 hours", "tomorrow 9am", "every friday").
        project_path: The project directory to run Claude in. Defaults to the current working directory.

    Returns:
        Confirmation with details about the scheduled agent task.
    """
    due_dt = dateparser_parse(due)
    if not due_dt:
        return f"Could not parse due date: {due}"

    cwd = project_path or os.getcwd()

    # Store as a reminder with special agent prefix
    agent_text = f"[AGENT:{cwd}] {task}"

    db_session = _get_db_session()
    try:
        with db_session.get_session() as session:
            service = ReminderService(session)
            reminder = service.create_reminder(
                text=agent_text,
                due_at=due_dt,
                priority=PriorityLevel.HIGH,
                project_context=f"agent:{os.path.basename(cwd)}",
            )

        return (
            f"Agent reminder #{reminder.id} scheduled.\n"
            f"Task: {task}\n"
            f"When: {reminder.due_at}\n"
            f"Directory: {cwd}\n"
            f"\n"
            f"WARNING: At the scheduled time, this will execute:\n"
            f"  claude -p \"{task}\" --dangerously-skip-permissions\n"
            f"  (in {cwd})\n"
            f"\n"
            f"Claude will have full permissions to read, write, and execute in this directory."
        )
    except Exception as e:
        return f"Error creating agent reminder: {e}"
    finally:
        db_session.close()


def run_mcp_server() -> None:
    """Entry point for the MCP server."""
    mcp.run()
