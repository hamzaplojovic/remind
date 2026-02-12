"""Reminder service - business logic for reminder operations."""

from datetime import datetime, timezone

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
