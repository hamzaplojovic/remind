"""Notification system for Remind."""

import subprocess
from collections.abc import Callable

from remind_cli.platform_capabilities import PlatformCapabilities
from remind_cli.platform_utils import get_platform

try:
    from notifypy import Notify
except ImportError:
    Notify = None  # type: ignore


class NotificationManager:
    """Unified notification interface across platforms.

    Provides graceful degradation:
    - If notify-py unavailable: prints to console
    - If sound player unavailable: sends notification without sound
    """

    def __init__(self, app_name: str = "Remind", strict: bool = False):
        """Initialize notification manager.

        Args:
            app_name: Application name for notifications
            strict: If True, raise error if notify-py unavailable.
                   If False, gracefully degrade to console output.

        Raises:
            ImportError: If strict=True and notify-py not available
        """
        self.app_name = app_name
        self.platform_info = get_platform()
        self.notifications_available = Notify is not None
        self.sound_available = PlatformCapabilities.test_sound_player(
            self.platform_info.get_sound_player()
        )

        if not self.notifications_available and strict:
            raise ImportError("notify-py not installed. Install with: pip install notify-py")

    def is_available(self) -> bool:
        """Check if notifications can be sent.

        Returns:
            True if notify-py is available
        """
        return self.notifications_available

    def is_sound_available(self) -> bool:
        """Check if sound playback is available.

        Returns:
            True if sound player is available
        """
        return self.sound_available

    def _play_sound(self, urgency: str = "normal") -> None:
        """Play an annoying alert sound based on urgency.

        Sound playback is best-effort - if the player is unavailable or
        playback fails, the notification is still sent without sound.

        Args:
            urgency: Sound urgency level ("low", "normal", "critical")
        """
        if not self.sound_available:
            return  # Sound player not available, skip silently

        if self.platform_info.is_macos:
            # Use system alert sounds on macOS
            sounds = {
                "critical": "Glass",  # Very annoying
                "normal": "Ping",  # Medium annoying
                "low": "Pop",  # Less annoying
            }
            sound = sounds.get(urgency, "Ping")
            try:
                subprocess.run(
                    ["afplay", f"/System/Library/Sounds/{sound}.aiff"],
                    timeout=10,
                    capture_output=True,
                )
            except subprocess.TimeoutExpired:
                pass  # Sound playback timed out but notification sent
            except FileNotFoundError:
                pass  # afplay not found, skip silently
            except Exception:
                pass  # Other errors, skip silently

        elif self.platform_info.is_linux:
            # Use freedesktop system sounds on Linux
            sounds = {
                "critical": "alarm-clock-elapsed",
                "normal": "dialog-warning",
                "low": "complete",
            }
            sound = sounds.get(urgency, "dialog-warning")
            try:
                subprocess.run(
                    ["paplay", f"/usr/share/sounds/freedesktop/stereo/{sound}.oga"],
                    timeout=10,
                    capture_output=True,
                )
            except subprocess.TimeoutExpired:
                pass  # Sound playback timed out but notification sent
            except FileNotFoundError:
                pass  # paplay not found, skip silently
            except Exception:
                pass  # Other errors, skip silently

    def notify(
        self,
        title: str,
        message: str,
        urgency: str = "normal",
        callback: Callable[[], None] | None = None,
        sound: bool = False,
    ) -> bool:
        """Send a native desktop notification.

        Args:
            title: Notification title
            message: Notification body
            urgency: "low", "normal", "critical"
            callback: Optional callback function when notification is clicked
            sound: Whether to play an annoying alert sound

        Returns:
            True if notification sent successfully, False otherwise.
            Returns False if notifications unavailable (graceful degradation).
        """
        # Play sound first if enabled and available
        if sound:
            self._play_sound(urgency)

        try:
            # Use platform-specific notification methods for better customization
            # macOS and Linux have built-in support via AppleScript and D-Bus
            if self.platform_info.is_macos:
                return self._notify_macos(title, message, urgency)
            elif self.platform_info.is_linux:
                return self._notify_linux(title, message, urgency)
            elif self.notifications_available:
                # For other platforms, use notify-py if available
                notification = Notify()
                notification.title = title
                notification.message = message
                notification.app_name = self.app_name
                notification.send()
                return True
            else:
                # Fallback to console if no notification system available
                emoji = {"low": "ℹ️", "normal": "🔔", "critical": "🚨"}
                print(f"{emoji.get(urgency, '🔔')} [{title}] {message}")
                return False
        except Exception as e:
            # Log error but don't fail - notification was attempted
            print(f"Warning: Error sending notification: {e}")
            return False

    def _notify_macos(self, title: str, message: str, urgency: str = "normal") -> bool:
        """Send a beautiful macOS notification using AppleScript.

        Displays reminder text prominently with a clean "Remind" branding.
        """
        # Escape quotes in strings
        message_escaped = message.replace('"', '\\"')

        # Use AppleScript for native macOS notifications with sound
        urgency_sound = {
            "critical": "Alarm",  # System alarm sound
            "normal": "Ping",     # Default notification sound
            "low": "Pop",         # Subtle sound
        }
        sound = urgency_sound.get(urgency, "Ping")

        # Simple, clean notification: "Remind" as title, reminder text as message
        # (title parameter is kept for signature compatibility but we use "Remind" for consistency)
        script = f'display notification "{message_escaped}" with title "Remind" sound name "{sound}"'

        try:
            subprocess.run(
                ["osascript", "-e", script],
                timeout=5,
                capture_output=True,
                check=False,
            )
            return True
        except Exception:
            return False

    def _notify_linux(self, title: str, message: str, urgency: str = "normal") -> bool:
        """Send a beautiful Linux notification using D-Bus/freedesktop."""
        try:
            import dbus
            from dbus.exceptions import DBusException
        except ImportError:
            # Fallback to notify-send if dbus not available
            return self._notify_linux_notify_send(title, message, urgency)

        try:
            # Connect to D-Bus session
            bus = dbus.SessionBus()
            notify_object = bus.get_object(
                "org.freedesktop.Notifications", "/org/freedesktop/Notifications"
            )
            notify_interface = dbus.Interface(notify_object, "org.freedesktop.Notifications")

            # Map urgency levels to D-Bus urgency (0=low, 1=normal, 2=critical)
            urgency_map = {"low": 0, "normal": 1, "critical": 2}
            dbus_urgency = urgency_map.get(urgency, 1)

            # Hints for better presentation
            hints = {
                "urgency": dbus.Byte(dbus_urgency),
                "desktop-entry": dbus.String("remind"),
            }

            # Add icon based on urgency
            icon_map = {
                "low": "dialog-information",
                "normal": "appointment-soon",
                "critical": "dialog-warning",
            }
            icon = icon_map.get(urgency, "dialog-information")

            # Send notification via D-Bus
            notify_interface.Notify(
                "Remind",  # app_name
                0,  # replaces_id (0 = new notification)
                icon,  # app_icon
                title,  # summary
                message,  # body
                [],  # actions
                hints,  # hints
                5000,  # timeout (5 seconds)
            )
            return True
        except (DBusException, Exception):
            # Fallback to notify-send
            return self._notify_linux_notify_send(title, message, urgency)

    def _notify_linux_notify_send(
        self, title: str, message: str, urgency: str = "normal"
    ) -> bool:
        """Fallback: Use notify-send command for Linux notifications."""
        try:
            urgency_map = {"low": "low", "normal": "normal", "critical": "critical"}
            urgency_str = urgency_map.get(urgency, "normal")

            subprocess.run(
                [
                    "notify-send",
                    "--urgency",
                    urgency_str,
                    "--app-name",
                    "Remind",
                    title,
                    message,
                ],
                timeout=5,
                capture_output=True,
                check=False,
            )
            return True
        except FileNotFoundError:
            # notify-send not available
            return False
        except Exception:
            return False

    def notify_reminder_due(
        self, reminder_text: str, sound: bool = False, callback: Callable | None = None
    ) -> bool:
        """Send a notification for a due reminder.

        Shows the reminder text prominently in the notification.
        """
        # Use reminder text directly - it's already the most important info
        message = reminder_text[:150] + ("..." if len(reminder_text) > 150 else "")
        return self.notify(
            title="Remind",  # Keep title simple and branded
            message=message,
            urgency="normal",
            callback=callback,
            sound=sound,
        )

    def notify_nudge(self, reminder_text: str, sound: bool = False) -> bool:
        """Send a nudge notification for an escalated reminder.

        Escalated notifications for reminders that have been due for a while.
        """
        message = reminder_text[:150] + ("..." if len(reminder_text) > 150 else "")
        return self.notify(
            title="Remind - Still Due",  # Make it clear this is an escalation
            message=message,
            urgency="critical",
            sound=sound,
        )

    @staticmethod
    def is_supported() -> bool:
        """Check if notifications are supported on this platform."""
        return Notify is not None
