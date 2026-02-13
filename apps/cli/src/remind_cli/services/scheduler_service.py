"""Scheduler service for running background reminders."""

import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

from remind_database import DatabaseConfig, DatabaseSession
from remind_cli import output
from remind_cli.notifications import NotificationManager
from remind_cli.services.reminder_service import ReminderService

AGENT_PATTERN = re.compile(r"^\[AGENT:(.+?)\]\s*(.+)$")


class SchedulerRunner:
    """Background scheduler for sending reminders."""

    def __init__(self):
        """Initialize scheduler runner."""
        # Initialize database
        db_config = DatabaseConfig()
        self.db_session = DatabaseSession(db_config)
        self.notifications = NotificationManager(strict=False)
        self.running = False
        self.check_interval_seconds = 1
        self.nudge_intervals_minutes = [30, 60, 120]  # 30min, 1hr, 2hr
        self.notified_ids: set[int] = set()  # reminders already notified
        self.last_nudge_times: dict[int, datetime] = {}

    def start(self) -> None:
        """Start the scheduler daemon."""
        self.running = True

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        output.info(f"Scheduler started. Checking every {self.check_interval_seconds}s")

        try:
            while self.running:
                self._check_and_notify()
                time.sleep(self.check_interval_seconds)
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

                # Get overdue reminders (only notify once per reminder)
                overdue = reminder_service.get_overdue_reminders()
                for reminder in overdue:
                    if reminder.id not in self.notified_ids:
                        self._send_notification(reminder)
                        self.notified_ids.add(reminder.id)

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
        """Send initial notification for a due reminder, or execute agent task."""
        match = AGENT_PATTERN.match(reminder.text)
        if match:
            self._execute_agent_task(reminder, match.group(1), match.group(2))
            return

        try:
            self.notifications.notify_reminder_due(
                reminder.text,
                sound=True,
            )
        except Exception as e:
            output.error(f"Error sending notification: {e}")

    def _execute_agent_task(self, reminder, cwd: str, task: str) -> None:
        """Execute a Claude Code agent task."""
        output.info(f"Executing agent task #{reminder.id}: {task} (in {cwd})")
        try:
            self.notifications.notify_reminder_due(
                f"Agent starting: {task}",
                sound=True,
            )
            result = subprocess.run(
                ["claude", "-p", task, "--dangerously-skip-permissions"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )
            if result.returncode == 0:
                output.info(f"Agent task #{reminder.id} completed successfully")
                self.notifications.notify_reminder_due(
                    f"Agent completed: {task}",
                    sound=True,
                )
            else:
                output.error(f"Agent task #{reminder.id} failed: {result.stderr[:200]}")
                self.notifications.notify_reminder_due(
                    f"Agent failed: {task}",
                    sound=True,
                )
        except subprocess.TimeoutExpired:
            output.error(f"Agent task #{reminder.id} timed out after 10 minutes")
            self.notifications.notify_reminder_due(
                f"Agent timed out: {task}",
                sound=True,
            )
        except FileNotFoundError:
            output.error(f"Claude CLI not found. Install it to use agent reminders.")
        except Exception as e:
            output.error(f"Agent task error: {e}")

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
