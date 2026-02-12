"""Integration tests for CLI commands - tests actual command execution."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

import pytest
from click.testing import CliRunner
from typer.testing import CliRunner as TyperCliRunner

from remind_database import DatabaseConfig, DatabaseSession
from remind_shared import PriorityLevel
from remind_cli.cli import app
from remind_cli.services.reminder_service import ReminderService


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        config = DatabaseConfig(db_path=db_path)
        session = DatabaseSession(config)
        yield session
        session.close()
        DatabaseSession.reset()


@pytest.fixture
def cli_runner(temp_db):
    """Create a CLI runner with temporary database."""
    return TyperCliRunner()


class TestAddCommand:
    """Integration tests for add command."""

    def test_add_basic_reminder(self, cli_runner, temp_db):
        """Test adding a basic reminder."""
        result = cli_runner.invoke(app, ["add", "Buy groceries"])
        assert result.exit_code == 0
        assert "Reminder saved" in result.stdout
        assert "Buy groceries" in result.stdout

    def test_add_with_due_date(self, cli_runner, temp_db):
        """Test adding reminder with due date."""
        result = cli_runner.invoke(
            app, ["add", "Call mom", "--due", "tomorrow 5pm"]
        )
        assert result.exit_code == 0
        assert "Reminder saved" in result.stdout

    def test_add_with_priority(self, cli_runner, temp_db):
        """Test adding reminder with priority."""
        result = cli_runner.invoke(
            app, ["add", "Urgent task", "--priority", "high"]
        )
        assert result.exit_code == 0
        assert "Reminder saved" in result.stdout
        assert "HIGH" in result.stdout

    def test_add_with_project(self, cli_runner, temp_db):
        """Test adding reminder with project context."""
        result = cli_runner.invoke(
            app, ["add", "Review PR", "--project", "work"]
        )
        assert result.exit_code == 0
        assert "Reminder saved" in result.stdout

    def test_add_multiple_reminders(self, cli_runner, temp_db):
        """Test adding multiple reminders."""
        result1 = cli_runner.invoke(app, ["add", "Task 1"])
        result2 = cli_runner.invoke(app, ["add", "Task 2"])
        result3 = cli_runner.invoke(app, ["add", "Task 3"])

        assert result1.exit_code == 0
        assert result2.exit_code == 0
        assert result3.exit_code == 0

        # Verify all were added
        list_result = cli_runner.invoke(app, ["list"])
        assert "Task 1" in list_result.stdout
        assert "Task 2" in list_result.stdout
        assert "Task 3" in list_result.stdout
        assert "3 reminder" in list_result.stdout

    def test_add_invalid_priority(self, cli_runner, temp_db):
        """Test adding reminder with invalid priority."""
        result = cli_runner.invoke(
            app, ["add", "Task", "--priority", "urgent"]
        )
        assert result.exit_code != 0
        # Error is printed to stderr but captured separately by test runner
        assert result.exit_code == 1


class TestListCommand:
    """Integration tests for list command."""

    def test_list_empty(self, cli_runner, temp_db):
        """Test list when no reminders exist."""
        result = cli_runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No reminders found" in result.stdout

    def test_list_active_reminders(self, cli_runner, temp_db):
        """Test listing active reminders."""
        # Add reminders
        cli_runner.invoke(app, ["add", "Active 1"])
        cli_runner.invoke(app, ["add", "Active 2"])

        result = cli_runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "Active 1" in result.stdout
        assert "Active 2" in result.stdout
        assert "2 reminder" in result.stdout

    def test_list_all_reminders(self, cli_runner, temp_db):
        """Test listing all reminders including done ones."""
        # Add and mark done
        cli_runner.invoke(app, ["add", "Active"])
        cli_runner.invoke(app, ["add", "Done task"])
        cli_runner.invoke(app, ["done", "2"])

        # List active only
        active_result = cli_runner.invoke(app, ["list"])
        assert "Active" in active_result.stdout
        assert "Done task" not in active_result.stdout

        # List all
        all_result = cli_runner.invoke(app, ["list", "--all"])
        assert "Active" in all_result.stdout
        assert "Done task" in all_result.stdout

    def test_list_json_output(self, cli_runner, temp_db):
        """Test list with JSON output."""
        cli_runner.invoke(app, ["add", "JSON test"])

        result = cli_runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0
        assert '"id"' in result.stdout
        assert '"text"' in result.stdout
        assert '"due_at"' in result.stdout
        assert '"priority"' in result.stdout

    def test_list_by_priority(self, cli_runner, temp_db):
        """Test filtering list by priority."""
        cli_runner.invoke(app, ["add", "High priority", "--priority", "high"])
        cli_runner.invoke(app, ["add", "Medium priority"])
        cli_runner.invoke(app, ["add", "Low priority", "--priority", "low"])

        result = cli_runner.invoke(app, ["list", "--priority", "high"])
        assert result.exit_code == 0
        assert "High priority" in result.stdout
        assert "Medium priority" not in result.stdout
        assert "Low priority" not in result.stdout


class TestDoneCommand:
    """Integration tests for done command."""

    def test_mark_done(self, cli_runner, temp_db):
        """Test marking a reminder as done."""
        cli_runner.invoke(app, ["add", "Complete me"])

        result = cli_runner.invoke(app, ["done", "1"])
        assert result.exit_code == 0
        assert "Done: Complete me" in result.stdout

    def test_mark_done_removes_from_active(self, cli_runner, temp_db):
        """Test that done reminder disappears from active list."""
        cli_runner.invoke(app, ["add", "Task"])

        # Mark done
        cli_runner.invoke(app, ["done", "1"])

        # Check not in active list
        result = cli_runner.invoke(app, ["list"])
        assert "Task" not in result.stdout
        assert "No reminders found" in result.stdout

    def test_mark_done_nonexistent(self, cli_runner, temp_db):
        """Test marking nonexistent reminder as done."""
        result = cli_runner.invoke(app, ["done", "999"])
        assert result.exit_code != 0
        # Error is printed to stderr but captured separately by test runner
        assert result.exit_code == 1

    def test_mark_done_multiple_times(self, cli_runner, temp_db):
        """Test marking multiple reminders as done."""
        cli_runner.invoke(app, ["add", "Task 1"])
        cli_runner.invoke(app, ["add", "Task 2"])
        cli_runner.invoke(app, ["add", "Task 3"])

        cli_runner.invoke(app, ["done", "1"])
        cli_runner.invoke(app, ["done", "2"])

        result = cli_runner.invoke(app, ["list"])
        assert "Task 1" not in result.stdout
        assert "Task 2" not in result.stdout
        assert "Task 3" in result.stdout


class TestSearchCommand:
    """Integration tests for search command."""

    def test_search_finds_reminders(self, cli_runner, temp_db):
        """Test searching for reminders."""
        cli_runner.invoke(app, ["add", "Buy groceries"])
        cli_runner.invoke(app, ["add", "Buy milk"])
        cli_runner.invoke(app, ["add", "Call mom"])

        result = cli_runner.invoke(app, ["search", "buy"])
        assert result.exit_code == 0
        assert "Buy groceries" in result.stdout
        assert "Buy milk" in result.stdout
        assert "Call mom" not in result.stdout

    def test_search_case_insensitive(self, cli_runner, temp_db):
        """Test that search is case-insensitive."""
        cli_runner.invoke(app, ["add", "IMPORTANT TASK"])

        result = cli_runner.invoke(app, ["search", "important"])
        assert result.exit_code == 0
        assert "IMPORTANT TASK" in result.stdout

    def test_search_no_results(self, cli_runner, temp_db):
        """Test search with no results."""
        cli_runner.invoke(app, ["add", "Task"])

        result = cli_runner.invoke(app, ["search", "nonexistent"])
        assert result.exit_code == 0
        assert "No reminders matching" in result.stdout

    def test_search_json_output(self, cli_runner, temp_db):
        """Test search with JSON output."""
        cli_runner.invoke(app, ["add", "Search test"])

        result = cli_runner.invoke(app, ["search", "search", "--json"])
        assert result.exit_code == 0
        assert '"id"' in result.stdout
        assert '"text"' in result.stdout


class TestSchedulerCommand:
    """Integration tests for scheduler command."""

    def test_scheduler_status(self, cli_runner, temp_db):
        """Test checking scheduler status."""
        result = cli_runner.invoke(app, ["scheduler", "--status"])
        assert result.exit_code == 0
        assert "SCHEDULER STATUS" in result.stdout

    def test_scheduler_help(self, cli_runner, temp_db):
        """Test scheduler help."""
        result = cli_runner.invoke(app, ["scheduler", "--help"])
        assert result.exit_code == 0
        assert "--enable" in result.stdout
        assert "--disable" in result.stdout
        assert "--status" in result.stdout


class TestCompleteWorkflow:
    """Integration tests for complete workflows."""

    def test_add_list_search_done_workflow(self, cli_runner, temp_db):
        """Test complete workflow: add → list → search → done."""
        # Add reminders
        add1 = cli_runner.invoke(app, ["add", "Buy groceries", "--priority", "high"])
        add2 = cli_runner.invoke(app, ["add", "Call mom", "--priority", "medium"])
        add3 = cli_runner.invoke(app, ["add", "Review PR", "--project", "work"])

        assert add1.exit_code == 0
        assert add2.exit_code == 0
        assert add3.exit_code == 0

        # List all
        list_result = cli_runner.invoke(app, ["list"])
        assert list_result.exit_code == 0
        assert "3 reminder" in list_result.stdout

        # Search
        search_result = cli_runner.invoke(app, ["search", "buy"])
        assert search_result.exit_code == 0
        assert "Buy groceries" in search_result.stdout
        assert "Call mom" not in search_result.stdout

        # Mark done
        done_result = cli_runner.invoke(app, ["done", "1"])
        assert done_result.exit_code == 0
        assert "Done: Buy groceries" in done_result.stdout

        # List active (should not include done)
        final_list = cli_runner.invoke(app, ["list"])
        assert "Buy groceries" not in final_list.stdout
        assert "Call mom" in final_list.stdout
        assert "Review PR" in final_list.stdout

    def test_multiple_operations_sequence(self, cli_runner, temp_db):
        """Test sequence of multiple operations."""
        # Add 5 reminders
        for i in range(1, 6):
            result = cli_runner.invoke(app, ["add", f"Task {i}"])
            assert result.exit_code == 0

        # Check count
        list_result = cli_runner.invoke(app, ["list"])
        assert "5 reminder" in list_result.stdout

        # Mark some done
        for task_id in [1, 3, 5]:
            result = cli_runner.invoke(app, ["done", str(task_id)])
            assert result.exit_code == 0

        # Check remaining
        list_result = cli_runner.invoke(app, ["list"])
        assert "Task 2" in list_result.stdout
        assert "Task 4" in list_result.stdout
        assert "Task 1" not in list_result.stdout
        assert "2 reminder" in list_result.stdout

        # Check all includes done
        all_result = cli_runner.invoke(app, ["list", "--all"])
        assert "5 reminder" in all_result.stdout


class TestNotificationSystem:
    """Integration tests for end-to-end notification system."""

    def test_scheduler_detects_overdue_reminders(self, temp_db):
        """Test that scheduler correctly detects overdue reminders."""
        from datetime import timezone, timedelta
        from remind_cli.services.reminder_service import ReminderService

        with temp_db.get_session() as session:
            service = ReminderService(session)

            # Create an overdue reminder (1 hour ago)
            now = datetime.now(timezone.utc)
            past_due = now - timedelta(hours=1)
            reminder = service.create_reminder(
                text="This reminder is overdue",
                due_at=past_due,
                priority=PriorityLevel.HIGH,
                allow_past_due=True,
            )
            assert reminder is not None

            # Verify scheduler can detect it
            overdue = service.get_overdue_reminders()
            assert len(overdue) == 1
            assert overdue[0].text == "This reminder is overdue"

    def test_scheduler_detects_upcoming_reminders(self, temp_db):
        """Test that scheduler correctly detects upcoming reminders."""
        from datetime import timezone, timedelta
        from remind_cli.services.reminder_service import ReminderService

        with temp_db.get_session() as session:
            service = ReminderService(session)

            # Create an upcoming reminder (30 minutes from now)
            now = datetime.now(timezone.utc)
            upcoming = now + timedelta(minutes=30)
            reminder = service.create_reminder(
                text="This reminder is upcoming",
                due_at=upcoming,
                priority=PriorityLevel.MEDIUM,
            )
            assert reminder is not None

            # Verify scheduler can detect it as upcoming (within next 24 hours)
            upcoming_reminders = service.get_upcoming_reminders(hours=24)
            assert len(upcoming_reminders) == 1
            assert upcoming_reminders[0].text == "This reminder is upcoming"

    def test_notification_flow_overdue_to_done(self, cli_runner, temp_db):
        """Test complete flow: create overdue → scheduler detects → mark done."""
        from datetime import timezone, timedelta
        from remind_cli.services.reminder_service import ReminderService

        with temp_db.get_session() as session:
            service = ReminderService(session)

            # Create overdue reminder
            now = datetime.now(timezone.utc)
            past_due = now - timedelta(minutes=5)
            service.create_reminder(
                text="Overdue task to complete",
                due_at=past_due,
                priority=PriorityLevel.HIGH,
                allow_past_due=True,
            )

            # Verify scheduler detects it
            overdue = service.get_overdue_reminders()
            assert len(overdue) == 1
            overdue_id = overdue[0].id

            # Mark it done via CLI
            result = cli_runner.invoke(app, ["done", str(overdue_id)])
            assert result.exit_code == 0
            assert "Done:" in result.stdout

            # Verify it's no longer in active list
            active = service.list_active_reminders()
            assert len(active) == 0

            # Verify it's in all list with done flag
            all_reminders = service.list_all_reminders()
            assert len(all_reminders) == 1
            assert all_reminders[0].done_at is not None
