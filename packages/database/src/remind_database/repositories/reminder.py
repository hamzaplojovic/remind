"""Reminder repository for database access."""

from datetime import datetime, timedelta, timezone

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
            reminder.done_at = datetime.now()
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

    def update(
        self,
        reminder_id: int,
        text: str | None = None,
        due_at: datetime | None = None,
        priority: PriorityLevel | None = None,
        project_context: str | None = None,
    ) -> Reminder | None:
        """Update a reminder's fields. Only non-None fields are changed."""
        reminder = self.session.query(ReminderModel).filter_by(id=reminder_id).first()
        if not reminder:
            return None
        if text is not None:
            reminder.text = text
        if due_at is not None:
            reminder.due_at = due_at
        if priority is not None:
            reminder.priority = priority.value
        if project_context is not None:
            reminder.project_context = project_context
        self.session.commit()
        self.session.refresh(reminder)
        return reminder.to_pydantic()

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
        now = datetime.now()
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
        now = datetime.now()
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

    def get_by_project(self, project_context: str, include_done: bool = False) -> list[Reminder]:
        """Get reminders filtered by project context."""
        query = self.session.query(ReminderModel).filter(
            ReminderModel.project_context.ilike(f"%{project_context}%")
        )
        if not include_done:
            query = query.filter(ReminderModel.done_at.is_(None))
        reminders = query.order_by(ReminderModel.due_at).all()
        return [r.to_pydantic() for r in reminders]

    def bulk_mark_done(self, reminder_ids: list[int]) -> list[Reminder]:
        """Mark multiple reminders as done. Returns the ones that were completed."""
        now = datetime.now()
        reminders = (
            self.session.query(ReminderModel)
            .filter(ReminderModel.id.in_(reminder_ids))
            .filter(ReminderModel.done_at.is_(None))
            .all()
        )
        for r in reminders:
            r.done_at = now
        self.session.commit()
        for r in reminders:
            self.session.refresh(r)
        return [r.to_pydantic() for r in reminders]

    def get_due_today(self) -> list[Reminder]:
        """Get reminders due today (not done)."""
        now = datetime.now()
        end_of_day = now.replace(hour=23, minute=59, second=59)
        reminders = (
            self.session.query(ReminderModel)
            .filter(ReminderModel.due_at <= end_of_day)
            .filter(ReminderModel.done_at.is_(None))
            .order_by(ReminderModel.due_at)
            .all()
        )
        return [r.to_pydantic() for r in reminders]

    def get_due_this_week(self) -> list[Reminder]:
        """Get reminders due within the next 7 days (not done)."""
        now = datetime.now()
        end_of_week = now + timedelta(days=7)
        reminders = (
            self.session.query(ReminderModel)
            .filter(ReminderModel.due_at <= end_of_week)
            .filter(ReminderModel.done_at.is_(None))
            .order_by(ReminderModel.due_at)
            .all()
        )
        return [r.to_pydantic() for r in reminders]

    def count_by_priority(self) -> dict[str, int]:
        """Count active reminders grouped by priority."""
        from sqlalchemy import func
        results = (
            self.session.query(ReminderModel.priority, func.count())
            .filter(ReminderModel.done_at.is_(None))
            .group_by(ReminderModel.priority)
            .all()
        )
        return {priority: count for priority, count in results}

    def count_by_project(self) -> dict[str, int]:
        """Count active reminders grouped by project context."""
        from sqlalchemy import func
        results = (
            self.session.query(ReminderModel.project_context, func.count())
            .filter(ReminderModel.done_at.is_(None))
            .filter(ReminderModel.project_context.isnot(None))
            .group_by(ReminderModel.project_context)
            .all()
        )
        return {project: count for project, count in results}
