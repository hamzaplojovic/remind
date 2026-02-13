"""Reminder service - business logic for reminder operations."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from remind_shared import Reminder, PriorityLevel, ValidationError
from remind_database import ReminderRepository


class ReminderService:
    """Service layer for reminder operations."""

    def __init__(self, session: Session):
        """Initialize reminder service with database session."""
        self.session = session

    def create_reminder(
        self,
        text: str,
        due_at: datetime,
        priority: PriorityLevel = PriorityLevel.MEDIUM,
        project_context: str | None = None,
        ai_suggested_text: str | None = None,
        allow_past_due: bool = False,
    ) -> Reminder:
        """Create a new reminder.

        Args:
            text: Reminder text
            due_at: Due datetime
            priority: Priority level
            project_context: Optional project context
            ai_suggested_text: Optional AI-generated text
            allow_past_due: If True, allows creating reminders with past-due dates (for testing)

        Returns:
            Created reminder

        Raises:
            ValidationError: If text is empty or too long
        """
        if not text or len(text) > 1000:
            raise ValidationError("Reminder text too long")

        # Handle timezone-aware and naive datetimes
        now = datetime.now(timezone.utc)
        due_utc = due_at.astimezone(timezone.utc) if due_at.tzinfo else due_at.replace(tzinfo=timezone.utc)

        if due_utc < now and not allow_past_due:
            raise ValidationError("Due date must be in the future")

        repo = ReminderRepository(self.session)
        return repo.create(
            text=text,
            due_at=due_at,
            priority=priority,
            project_context=project_context,
            ai_suggested_text=ai_suggested_text,
        )

    def get_reminder(self, reminder_id: int) -> Reminder:
        """Get a reminder by ID.

        Raises:
            ValidationError: If reminder not found
        """
        repo = ReminderRepository(self.session)
        reminder = repo.get_by_id(reminder_id)
        if not reminder:
            raise ValidationError(f"Reminder {reminder_id} not found")
        return reminder

    def list_active_reminders(self) -> list[Reminder]:
        """List all active (not done) reminders."""
        repo = ReminderRepository(self.session)
        return repo.list_active()

    def list_all_reminders(self) -> list[Reminder]:
        """List all reminders including done ones."""
        repo = ReminderRepository(self.session)
        return repo.list_all()

    def mark_reminder_done(self, reminder_id: int) -> Reminder:
        """Mark a reminder as done.

        Raises:
            ValidationError: If reminder not found
        """
        repo = ReminderRepository(self.session)
        reminder = repo.mark_done(reminder_id)
        if not reminder:
            raise ValidationError(f"Reminder {reminder_id} not found")
        return reminder

    def search_reminders(self, query: str) -> list[Reminder]:
        """Search reminders by text."""
        repo = ReminderRepository(self.session)
        return repo.search(query)

    def update_reminder(
        self,
        reminder_id: int,
        text: str | None = None,
        due_at: datetime | None = None,
        priority: PriorityLevel | None = None,
        project_context: str | None = None,
    ) -> Reminder:
        """Update a reminder's fields.

        Args:
            reminder_id: ID of the reminder to update
            text: New text (optional)
            due_at: New due date (optional)
            priority: New priority (optional)
            project_context: New project context (optional)

        Returns:
            Updated reminder

        Raises:
            ValidationError: If reminder not found or validation fails
        """
        if text is not None and (not text or len(text) > 1000):
            raise ValidationError("Reminder text must be 1-1000 characters")

        repo = ReminderRepository(self.session)
        reminder = repo.update(
            reminder_id=reminder_id,
            text=text,
            due_at=due_at,
            priority=priority,
            project_context=project_context,
        )
        if not reminder:
            raise ValidationError(f"Reminder {reminder_id} not found")
        return reminder

    def delete_reminder(self, reminder_id: int) -> bool:
        """Delete a reminder permanently."""
        repo = ReminderRepository(self.session)
        return repo.delete(reminder_id)

    def get_overdue_reminders(self) -> list[Reminder]:
        """Get all overdue reminders."""
        repo = ReminderRepository(self.session)
        return repo.get_overdue()

    def get_upcoming_reminders(self, hours: int = 24) -> list[Reminder]:
        """Get reminders due within the next N hours."""
        repo = ReminderRepository(self.session)
        return repo.get_upcoming(hours)

    def get_project_reminders(self, project: str, include_done: bool = False) -> list[Reminder]:
        """Get reminders filtered by project context."""
        repo = ReminderRepository(self.session)
        return repo.get_by_project(project, include_done)

    def snooze_reminder(self, reminder_id: int, duration: timedelta) -> Reminder:
        """Snooze a reminder by a relative duration from now."""
        repo = ReminderRepository(self.session)
        new_due = datetime.now() + duration
        reminder = repo.update(reminder_id=reminder_id, due_at=new_due)
        if not reminder:
            raise ValidationError(f"Reminder {reminder_id} not found")
        return reminder

    def bulk_complete(self, reminder_ids: list[int]) -> list[Reminder]:
        """Complete multiple reminders at once."""
        repo = ReminderRepository(self.session)
        return repo.bulk_mark_done(reminder_ids)

    def get_summary(self) -> dict:
        """Get a structured summary of all reminders."""
        repo = ReminderRepository(self.session)
        overdue = repo.get_overdue()
        due_today = repo.get_due_today()
        due_this_week = repo.get_due_this_week()
        by_priority = repo.count_by_priority()
        by_project = repo.count_by_project()
        active = repo.list_active()

        # due_today includes overdue — separate them
        today_only = [r for r in due_today if r.id not in {o.id for o in overdue}]

        return {
            "total_active": len(active),
            "overdue_count": len(overdue),
            "overdue": overdue,
            "due_today_count": len(today_only),
            "due_today": today_only,
            "due_this_week_count": len(due_this_week),
            "by_priority": by_priority,
            "by_project": by_project,
        }
