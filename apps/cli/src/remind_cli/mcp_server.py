"""MCP server for Remind CLI — exposes reminder tools to Claude Code and other MCP clients."""

import os
from datetime import datetime, timedelta, timezone

from dateparser import parse as dateparser_parse
from fastmcp import FastMCP

from remind_database import DatabaseConfig, DatabaseSession
from remind_shared import PriorityLevel
from remind_cli.services.reminder_service import ReminderService
from remind_cli.config import load_config, save_config

mcp = FastMCP("Remind")

# Initialize once — singleton stays alive for the MCP server's lifetime
_db_session = DatabaseSession(DatabaseConfig())


def _get_db_session() -> DatabaseSession:
    """Return the long-lived database session."""
    return _db_session


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


@mcp.tool
def list_reminders(include_done: bool = False) -> str:
    """List all reminders. Shows active (not completed) reminders by default.

    Args:
        include_done: If True, also show completed reminders. Defaults to False.

    Returns:
        Formatted list of reminders with ID, text, due date, priority, and status.
    """
    db_session = _get_db_session()
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


@mcp.tool
def search_reminders(query: str) -> str:
    """Search reminders by text content.

    Args:
        query: Search term to find in reminder text (case-insensitive).

    Returns:
        Matching reminders or a message if none found.
    """
    db_session = _get_db_session()
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


@mcp.tool
def update_reminder(
    reminder_id: int,
    text: str | None = None,
    due: str | None = None,
    priority: str | None = None,
    project: str | None = None,
) -> str:
    """Update an existing reminder. Only provided fields are changed — omit fields to keep them unchanged.

    Works for both regular reminders and agent (Claude Code) reminders.

    Args:
        reminder_id: The ID number of the reminder to update.
        text: New reminder text. For agent reminders, use the format "[AGENT:/path] task description".
        due: New due date in natural language (e.g., "tomorrow 3pm", "in 1 hour").
        priority: New priority — "high", "medium", or "low".
        project: New project context.

    Returns:
        Confirmation with the updated reminder details.
    """
    priority_level = None
    if priority:
        try:
            priority_level = PriorityLevel(priority.lower())
        except ValueError:
            return f"Invalid priority: {priority}. Use: high, medium, low"

    due_dt = None
    if due:
        due_dt = dateparser_parse(due)
        if not due_dt:
            return f"Could not parse due date: {due}"

    db_session = _get_db_session()
    try:
        with db_session.get_session() as session:
            service = ReminderService(session)
            reminder = service.update_reminder(
                reminder_id=reminder_id,
                text=text,
                due_at=due_dt,
                priority=priority_level,
                project_context=project,
            )
        return (
            f"Updated reminder #{reminder.id}.\n"
            f"Text: {reminder.text}\n"
            f"Due: {reminder.due_at}\n"
            f"Priority: {reminder.priority.value}"
        )
    except Exception as e:
        return f"Error: {e}"


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


@mcp.tool
def get_context() -> str:
    """Get reminders filtered by project context (auto-detected from current directory).

    Returns:
        Formatted list of reminders for the current project.
    """
    cwd = os.getcwd()
    project_name = os.path.basename(cwd)

    db_session = _get_db_session()
    with db_session.get_session() as session:
        service = ReminderService(session)
        reminders = service.get_project_reminders(project_name)

    if not reminders:
        return f"No reminders found for project '{project_name}'."

    lines = [f"Project reminders for '{project_name}':"]
    now = datetime.now(timezone.utc)
    for r in reminders:
        status = ""
        if r.done_at:
            status = " [DONE]"
        else:
            due_utc = r.due_at.replace(tzinfo=timezone.utc) if r.due_at.tzinfo is None else r.due_at
            if due_utc < now:
                status = " [OVERDUE]"
        lines.append(f"#{r.id} [{r.priority.value.upper()}] {r.text} — {r.due_at}{status}")

    return "\n".join(lines)


@mcp.tool
def get_overdue() -> str:
    """Get all overdue reminders (not completed).

    Returns:
        Formatted list of overdue reminders or message if none.
    """
    db_session = _get_db_session()
    with db_session.get_session() as session:
        service = ReminderService(session)
        overdue = service.get_overdue_reminders()

    if not overdue:
        return "No overdue reminders."

    lines = [f"You have {len(overdue)} overdue reminder(s):"]
    for r in overdue:
        lines.append(f"#{r.id} [{r.priority.value.upper()}] {r.text} — due: {r.due_at}")

    return "\n".join(lines)


@mcp.tool
def get_upcoming(hours: int = 24) -> str:
    """Get reminders due within the next N hours.

    Args:
        hours: How many hours ahead to look (default 24).

    Returns:
        Formatted list of upcoming reminders.
    """
    db_session = _get_db_session()
    with db_session.get_session() as session:
        service = ReminderService(session)
        upcoming = service.get_upcoming_reminders(hours)

    if not upcoming:
        return f"No reminders due in the next {hours} hours."

    lines = [f"Reminders due in the next {hours} hours:"]
    for r in upcoming:
        lines.append(f"#{r.id} [{r.priority.value.upper()}] {r.text} — due: {r.due_at}")

    return "\n".join(lines)


@mcp.tool
def snooze_reminder(reminder_id: int, duration: str) -> str:
    """Snooze a reminder by a relative duration from now.

    Args:
        reminder_id: The ID of the reminder to snooze.
        duration: Duration (e.g., "2 hours", "1 day", "30 minutes").

    Returns:
        Confirmation with updated due date.
    """
    # Simple duration parsing
    duration_map = {
        "minute": 60,
        "hour": 3600,
        "day": 86400,
        "week": 604800,
    }

    try:
        parts = duration.lower().split()
        if len(parts) != 2:
            return "Duration format: '<number> <unit>' (e.g., '2 hours', '1 day')"

        amount = int(parts[0])
        unit = parts[1].rstrip("s")  # Remove trailing 's' from plural

        if unit not in duration_map:
            return f"Unknown unit: {unit}. Use: minute, hour, day, or week"

        seconds = amount * duration_map[unit]
        td = timedelta(seconds=seconds)

        db_session = _get_db_session()
        with db_session.get_session() as session:
            service = ReminderService(session)
            reminder = service.snooze_reminder(reminder_id, td)

        return f"Snoozed reminder #{reminder.id} until {reminder.due_at}"
    except ValueError:
        return "Invalid duration format. Use: '<number> <unit>' (e.g., '2 hours')"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool
def bulk_complete(reminder_ids: str) -> str:
    """Complete multiple reminders at once.

    Args:
        reminder_ids: Comma-separated reminder IDs (e.g., "1,5,12").

    Returns:
        Confirmation of completed reminders.
    """
    try:
        ids = [int(x.strip()) for x in reminder_ids.split(",")]
        db_session = _get_db_session()
        with db_session.get_session() as session:
            service = ReminderService(session)
            completed = service.bulk_complete(ids)

        if not completed:
            return f"No reminders found to complete for IDs: {reminder_ids}"

        lines = [f"Completed {len(completed)} reminder(s):"]
        for r in completed:
            lines.append(f"#{r.id} — {r.text}")

        return "\n".join(lines)
    except ValueError:
        return "Invalid format. Use comma-separated IDs: '1,5,12'"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool
def get_summary() -> str:
    """Get a structured summary of all reminders.

    Returns:
        Summary with overdue count, due today, due this week, by priority and project.
    """
    db_session = _get_db_session()
    with db_session.get_session() as session:
        service = ReminderService(session)
        summary = service.get_summary()

    lines = [
        f"📋 Reminder Summary",
        f"━━━━━━━━━━━━━━━━━━",
        f"",
        f"Total active: {summary['total_active']}",
        f"🔴 Overdue: {summary['overdue_count']}",
        f"📅 Due today: {summary['due_today_count']}",
        f"📆 Due this week: {summary['due_this_week_count']}",
        f"",
    ]

    if summary["by_priority"]:
        lines.append("By Priority:")
        for priority, count in sorted(summary["by_priority"].items()):
            lines.append(f"  {priority.upper()}: {count}")
        lines.append("")

    if summary["by_project"]:
        lines.append("By Project:")
        for project, count in sorted(summary["by_project"].items()):
            lines.append(f"  {project}: {count}")

    return "\n".join(lines)


@mcp.tool
def get_config(key: str | None = None) -> str:
    """Get configuration settings.

    Args:
        key: Optional specific setting key (e.g., 'timezone', 'notifications_enabled').
             If omitted, returns all settings.

    Returns:
        Configuration value(s).
    """
    try:
        config = load_config()
        if key:
            value = getattr(config, key, None)
            if value is None:
                return f"Setting '{key}' not found."
            return f"{key}: {value}"

        # Return all settings
        lines = ["Current Configuration:"]
        for field in config.model_fields:
            value = getattr(config, field)
            lines.append(f"  {field}: {value}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading config: {e}"


@mcp.tool
def set_config(key: str, value: str) -> str:
    """Set a configuration setting.

    Args:
        key: Setting key (e.g., 'timezone', 'notifications_enabled').
        value: New value (boolean settings use 'true'/'false').

    Returns:
        Confirmation of updated setting.
    """
    try:
        config = load_config()

        # Parse value based on field type
        field = config.model_fields.get(key)
        if not field:
            return f"Unknown setting: {key}"

        field_type = field.annotation
        if field_type is bool or str(field_type) == "<class 'bool'>":
            parsed_value = value.lower() in ("true", "1", "yes", "on")
        elif field_type is int or str(field_type) == "<class 'int'>":
            parsed_value = int(value)
        else:
            parsed_value = value

        setattr(config, key, parsed_value)
        save_config(config)
        return f"Updated {key} to {parsed_value}"
    except Exception as e:
        return f"Error: {e}"


def run_mcp_server() -> None:
    """Entry point for the MCP server."""
    mcp.run()
