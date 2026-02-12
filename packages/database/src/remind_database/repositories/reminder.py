"""Reminder repository for database access."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from remind_shared import PriorityLevel, Reminder
from remind_database.models import ReminderModel


class ReminderRepository:
    """Repository for reminder database operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(
        self,
        text: str,
        due_at: datetime,
        priority: PriorityLevel = PriorityLevel.MEDIUM,
        project_context: str | None = None,
        ai_suggested_text: str | None = None,
    ) -> Reminder:
        """Create a new reminder."""
        reminder = ReminderModel(
            text=text,
            due_at=due_at,
            priority=priority.value,
            project_context=project_context,
            ai_suggested_text=ai_suggested_text,
        )
        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)
        return reminder.to_pydantic()

    def get_by_id(self, reminder_id: int) -> Reminder | None:
        """Get a reminder by ID."""
        reminder = self.session.query(ReminderModel).filter_by(id=reminder_id).first()
        return reminder.to_pydantic() if reminder else None

    def list_active(self) -> list[Reminder]:
        """List all active (not done) reminders."""
        reminders = (
            self.session.query(ReminderModel)
            .filter(ReminderModel.done_at.is_(None))
            .order_by(ReminderModel.due_at)
            .all()
        )
        return [r.to_pydantic() for r in reminders]

    def list_all(self) -> list[Reminder]:
        """List all reminders including done ones."""
        reminders = self.session.query(ReminderModel).order_by(ReminderModel.due_at).all()
        return [r.to_pydantic() for r in reminders]

    def mark_done(self, reminder_id: int) -> Reminder | None:
        """Mark a reminder as done."""
        reminder = self.session.query(ReminderModel).filter_by(id=reminder_id).first()
        if reminder:
            reminder.done_at = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(reminder)
            return reminder.to_pydantic()
        return None

    def search(self, query: str) -> list[Reminder]:
        """Search reminders by text."""
        search_pattern = f"%{query}%"
        reminders = (
            self.session.query(ReminderModel)
            .filter(ReminderModel.text.ilike(search_pattern))
            .order_by(ReminderModel.due_at)
            .all()
        )
        return [r.to_pydantic() for r in reminders]

    def delete(self, reminder_id: int) -> bool:
        """Delete a reminder permanently."""
        reminder = self.session.query(ReminderModel).filter_by(id=reminder_id).first()
        if reminder:
            self.session.delete(reminder)
            self.session.commit()
            return True
        return False

    def get_overdue(self) -> list[Reminder]:
        """Get all overdue reminders (due_at < now and not done)."""
        now = datetime.now(timezone.utc)
        reminders = (
            self.session.query(ReminderModel)
            .filter(ReminderModel.due_at < now)
            .filter(ReminderModel.done_at.is_(None))
            .order_by(ReminderModel.due_at)
            .all()
        )
        return [r.to_pydantic() for r in reminders]

    def get_upcoming(self, hours: int = 24) -> list[Reminder]:
        """Get reminders due within the next N hours."""
        now = datetime.now(timezone.utc)
        from datetime import timedelta

        future = now + timedelta(hours=hours)
        reminders = (
            self.session.query(ReminderModel)
            .filter(ReminderModel.due_at >= now)
            .filter(ReminderModel.due_at <= future)
            .filter(ReminderModel.done_at.is_(None))
            .order_by(ReminderModel.due_at)
            .all()
        )
        return [r.to_pydantic() for r in reminders]
