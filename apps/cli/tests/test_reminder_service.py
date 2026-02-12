"""Tests for CLI ReminderService."""

from datetime import datetime, timedelta, timezone

import pytest

from remind_shared import ValidationError, PriorityLevel
from remind_cli.services.reminder_service import ReminderService


class TestReminderService:
    """Tests for reminder service."""

    def test_create_reminder(self, test_session):
        """Test creating a reminder."""
        service = ReminderService(test_session)
        now = datetime.now(timezone.utc)
        due_at = now + timedelta(days=1)

        reminder = service.create_reminder(
            text="Buy groceries",
            due_at=due_at,
            priority=PriorityLevel.MEDIUM,
        )

        assert reminder.id is not None
        assert reminder.text == "Buy groceries"
        assert reminder.priority == PriorityLevel.MEDIUM
        assert reminder.done_at is None

    def test_create_reminder_invalid_text_too_long(self, test_session):
        """Test creating reminder with text exceeding max length."""
        service = ReminderService(test_session)
        now = datetime.now(timezone.utc)
        due_at = now + timedelta(days=1)

        with pytest.raises(ValidationError, match="too long"):
            service.create_reminder(
                text="x" * 1001,  # Exceeds 1000 char limit
                due_at=due_at,
            )

    def test_create_reminder_past_date(self, test_session):
        """Test creating reminder with past due date."""
        service = ReminderService(test_session)
        now = datetime.now(timezone.utc)
        past_date = now - timedelta(days=1)

        with pytest.raises(ValidationError, match="future"):
            service.create_reminder(
                text="Past reminder",
                due_at=past_date,
            )

    def test_get_reminder(self, test_session):
        """Test getting a reminder by ID."""
        service = ReminderService(test_session)
        now = datetime.now(timezone.utc)
        due_at = now + timedelta(days=1)

        created = service.create_reminder(
            text="Test reminder",
            due_at=due_at,
        )

        retrieved = service.get_reminder(created.id)
        assert retrieved.id == created.id
        assert retrieved.text == "Test reminder"

    def test_get_reminder_not_found(self, test_session):
        """Test getting non-existent reminder."""
        service = ReminderService(test_session)

        with pytest.raises(ValidationError, match="not found"):
            service.get_reminder(999)

    def test_list_active_reminders(self, test_session):
        """Test listing active reminders."""
        service = ReminderService(test_session)
        now = datetime.now(timezone.utc)

        # Create one reminder
        service.create_reminder(
            text="Active reminder",
            due_at=now + timedelta(days=1),
        )

        # Create and mark one as done
        done_reminder = service.create_reminder(
            text="Done reminder",
            due_at=now + timedelta(days=1),
        )
        service.mark_reminder_done(done_reminder.id)

        active = service.list_active_reminders()
        assert len(active) == 1
        assert active[0].text == "Active reminder"

    def test_mark_reminder_done(self, test_session):
        """Test marking reminder as complete."""
        service = ReminderService(test_session)
        now = datetime.now(timezone.utc)
        due_at = now + timedelta(days=1)

        reminder = service.create_reminder(
            text="Complete me",
            due_at=due_at,
        )

        completed = service.mark_reminder_done(reminder.id)
        assert completed.done_at is not None

    def test_search_reminders(self, test_session):
        """Test searching reminders by text."""
        service = ReminderService(test_session)
        now = datetime.now(timezone.utc)
        due_at = now + timedelta(days=1)

        service.create_reminder(text="Buy groceries", due_at=due_at)
        service.create_reminder(text="Buy milk", due_at=due_at)
        service.create_reminder(text="Call mom", due_at=due_at)

        results = service.search_reminders("buy")
        assert len(results) == 2
        assert any("groceries" in r.text.lower() for r in results)
        assert any("milk" in r.text.lower() for r in results)

    def test_search_reminders_case_insensitive(self, test_session):
        """Test search is case-insensitive."""
        service = ReminderService(test_session)
        now = datetime.now(timezone.utc)
        due_at = now + timedelta(days=1)

        service.create_reminder(text="IMPORTANT TASK", due_at=due_at)

        results = service.search_reminders("important")
        assert len(results) == 1
        assert results[0].text == "IMPORTANT TASK"

    def test_delete_reminder(self, test_session):
        """Test deleting a reminder."""
        service = ReminderService(test_session)
        now = datetime.now(timezone.utc)
        due_at = now + timedelta(days=1)

        reminder = service.create_reminder(text="Delete me", due_at=due_at)
        service.delete_reminder(reminder.id)

        with pytest.raises(ValidationError, match="not found"):
            service.get_reminder(reminder.id)

    def test_get_overdue_reminders(self, test_session):
        """Test getting overdue reminders."""
        from remind_database.models import ReminderModel

        service = ReminderService(test_session)
        now = datetime.now(timezone.utc)

        # Create overdue reminder directly (bypass service validation)
        overdue_reminder = ReminderModel(
            text="Overdue task",
            due_at=now - timedelta(hours=1),
            priority="medium",
        )
        test_session.add(overdue_reminder)

        # Create future reminder through service
        service.create_reminder(
            text="Future task",
            due_at=now + timedelta(days=1),
        )
        test_session.commit()

        overdue = service.get_overdue_reminders()
        assert len(overdue) == 1
        assert overdue[0].text == "Overdue task"

    def test_get_upcoming_reminders(self, test_session):
        """Test getting upcoming reminders."""
        service = ReminderService(test_session)
        now = datetime.now(timezone.utc)

        # Create upcoming within 24 hours
        service.create_reminder(
            text="Due soon",
            due_at=now + timedelta(hours=2),
        )

        # Create far future
        service.create_reminder(
            text="Due later",
            due_at=now + timedelta(days=30),
        )

        upcoming = service.get_upcoming_reminders()
        assert len(upcoming) >= 1
        assert any("Due soon" in r.text for r in upcoming)
