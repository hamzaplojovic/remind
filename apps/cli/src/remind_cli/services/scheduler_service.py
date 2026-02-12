"""Scheduler service for running background reminders."""

import signal
import sys
import time
from datetime import datetime, timezone

from remind_database import DatabaseConfig, DatabaseSession
from remind_cli import output
from remind_cli.notifications import NotificationManager
from remind_cli.services.reminder_service import ReminderService


class SchedulerRunner:
    """Background scheduler for sending reminders."""

    def __init__(self):
        """Initialize scheduler runner."""
        # Initialize database
        db_config = DatabaseConfig()
        self.db_session = DatabaseSession(db_config)
        self.notifications = NotificationManager(strict=False)
        self.running = False
        self.check_interval_minutes = 5
        self.nudge_intervals_minutes = [30, 60, 120]  # 30min, 1hr, 2hr
        self.last_nudge_times: dict[int, datetime] = {}

    def start(self) -> None:
        """Start the scheduler daemon."""
        self.running = True

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        output.info(f"Scheduler started. Checking every {self.check_interval_minutes} minutes")

        try:
            while self.running:
                self._check_and_notify()
                time.sleep(self.check_interval_minutes * 60)
        except KeyboardInterrupt:
            self._shutdown()

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        output.info("Shutting down scheduler...")
        self.running = False
        self._shutdown()
        sys.exit(0)

    def _shutdown(self) -> None:
        """Clean shutdown."""
        try:
            self.db_session.close()
        except Exception:
            pass

    def _check_and_notify(self) -> None:
        """Check for due reminders and send notifications."""
        try:
            now = datetime.now(timezone.utc)

            with self.db_session.get_session() as session:
                reminder_service = ReminderService(session)

                # Get overdue reminders
                overdue = reminder_service.get_overdue_reminders()
                for reminder in overdue:
                    self._send_notification(reminder)

                # Get upcoming reminders (due within 24 hours but not yet due)
                upcoming = reminder_service.get_upcoming_reminders()
                for reminder in upcoming:
                    # Send nudges if premium
                    if self._should_nudge(reminder.id, reminder.due_at):
                        self._send_nudge(reminder)
                        self.last_nudge_times[reminder.id] = now

        except Exception as e:
            output.error(f"Error in scheduler check: {e}")

    def _send_notification(self, reminder) -> None:
        """Send initial notification for a due reminder."""
        try:
            self.notifications.notify_reminder_due(
                reminder.text,
                sound=True,
            )
        except Exception as e:
            output.error(f"Error sending notification: {e}")

    def _send_nudge(self, reminder) -> None:
        """Send nudge notification for an escalated reminder."""
        try:
            self.notifications.notify_nudge(
                reminder.text,
                sound=True,
            )
        except Exception as e:
            output.error(f"Error sending nudge: {e}")

    def _should_nudge(self, reminder_id: int, due_at: datetime) -> bool:
        """Check if a reminder should be nudged.

        Returns:
            True if enough time has passed since last nudge
        """
        now = datetime.now(timezone.utc)

        # Ensure due_at is timezone-aware (SQLite might return naive datetimes)
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)

        # First nudge: reminder hasn't been nudged yet but is overdue
        if reminder_id not in self.last_nudge_times:
            time_since_due_minutes = (now - due_at).total_seconds() / 60
            return time_since_due_minutes > self.nudge_intervals_minutes[0]

        last_nudge = self.last_nudge_times[reminder_id]
        time_since_nudge = (now - last_nudge).total_seconds() / 60

        # Check if next nudge interval has passed
        for interval in self.nudge_intervals_minutes:
            if time_since_nudge > interval:
                return True

        return False


def run_scheduler() -> None:
    """Entry point for running the scheduler as a daemon."""
    scheduler = SchedulerRunner()
    scheduler.start()
