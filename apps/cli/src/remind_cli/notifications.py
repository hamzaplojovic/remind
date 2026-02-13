"""Notification system for Remind."""

import math
import struct
import subprocess
import wave
import io
from collections.abc import Callable

from remind_cli.platform_utils import get_platform

try:
    from notifypy import Notify
except ImportError:
    Notify = None  # type: ignore

try:
    import simpleaudio as sa
except ImportError:
    sa = None  # type: ignore


def _generate_tone(frequency: float, duration_ms: int, volume: float = 0.5) -> bytes:
    """Generate a WAV tone in memory.

    Args:
        frequency: Tone frequency in Hz
        duration_ms: Duration in milliseconds
        volume: Volume from 0.0 to 1.0
    """
    sample_rate = 44100
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        # Apply fade in/out to avoid clicks (10ms fade)
        fade_samples = int(sample_rate * 0.01)
        if i < fade_samples:
            envelope = i / fade_samples
        elif i > num_samples - fade_samples:
            envelope = (num_samples - i) / fade_samples
        else:
            envelope = 1.0
        value = volume * envelope * math.sin(2 * math.pi * frequency * t)
        samples.append(int(value * 32767))

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return buf.getvalue()


def _generate_alert(urgency: str = "normal") -> bytes:
    """Generate an alert sound based on urgency level."""
    if urgency == "critical":
        # Sharp high-pitched beep
        return _generate_tone(880, 300, 0.7)
    elif urgency == "low":
        return _generate_tone(440, 200, 0.3)
    else:
        # Normal: pleasant two-tone chime
        return _generate_tone(660, 300, 0.5)


class NotificationManager:
    """Unified notification interface across platforms.

    Provides graceful degradation:
    - If notify-py unavailable: prints to console
    - If sound player unavailable: sends notification without sound
    """

    def __init__(self, app_name: str = "Remind", strict: bool = False):
        """Initialize notification manager."""
        self.app_name = app_name
        self.platform_info = get_platform()
        self.notifications_available = Notify is not None
        self.sound_available = sa is not None or self.platform_info.is_macos

        if not self.notifications_available and strict:
            raise ImportError("notify-py not installed. Install with: pip install notify-py")

    def is_available(self) -> bool:
        """Check if notifications can be sent."""
        return self.notifications_available

    def is_sound_available(self) -> bool:
        """Check if sound playback is available."""
        return self.sound_available

    def _play_sound(self, urgency: str = "normal") -> None:
        """Play an alert sound based on urgency. Best-effort, never raises."""
        if not self.sound_available:
            return

        if self.platform_info.is_macos:
            sounds = {
                "critical": "Glass",
                "normal": "Ping",
                "low": "Pop",
            }
            sound = sounds.get(urgency, "Ping")
            try:
                subprocess.run(
                    ["afplay", f"/System/Library/Sounds/{sound}.aiff"],
                    timeout=10,
                    capture_output=True,
                )
            except Exception:
                pass
        else:
            # Linux / other: use simpleaudio with generated tones
            self._play_sound_simpleaudio(urgency)

    def _play_sound_simpleaudio(self, urgency: str = "normal") -> None:
        """Play a generated alert tone via simpleaudio (ALSA on Linux)."""
        if sa is None:
            return
        try:
            wav_data = _generate_alert(urgency)
            wave_obj = sa.WaveObject.from_wave_file(io.BytesIO(wav_data))
            play_obj = wave_obj.play()
            play_obj.wait_done()
        except Exception:
            pass

    def notify(
        self,
        title: str,
        message: str,
        urgency: str = "normal",
        callback: Callable[[], None] | None = None,
        sound: bool = False,
    ) -> bool:
        """Send a native desktop notification.

        Returns:
            True if notification sent successfully, False otherwise.
        """
        # Play sound if enabled
        if sound:
            self._play_sound(urgency)

        try:
            if self.platform_info.is_macos:
                return self._notify_macos(title, message, urgency)
            elif self.platform_info.is_linux:
                return self._notify_linux(title, message, urgency)
            elif self.notifications_available:
                notification = Notify()
                notification.title = title
                notification.message = message
                notification.app_name = self.app_name
                notification.send()
                return True
            else:
                print(f"[{title}] {message}")
                return False
        except Exception as e:
            print(f"Warning: Error sending notification: {e}")
            return False

    def _notify_macos(self, title: str, message: str, urgency: str = "normal") -> bool:
        """Send macOS notification using AppleScript."""
        message_escaped = message.replace('"', '\\"')
        urgency_sound = {
            "critical": "Alarm",
            "normal": "Ping",
            "low": "Pop",
        }
        sound = urgency_sound.get(urgency, "Ping")
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
        """Send Linux notification using D-Bus, with notify-send fallback."""
        try:
            import dbus
            from dbus.exceptions import DBusException
        except ImportError:
            return self._notify_linux_notify_send(title, message, urgency)

        try:
            bus = dbus.SessionBus()
            notify_object = bus.get_object(
                "org.freedesktop.Notifications", "/org/freedesktop/Notifications"
            )
            notify_interface = dbus.Interface(notify_object, "org.freedesktop.Notifications")

            urgency_map = {"low": 0, "normal": 1, "critical": 2}
            dbus_urgency = urgency_map.get(urgency, 1)

            hints = {
                "urgency": dbus.Byte(dbus_urgency),
                "desktop-entry": dbus.String("remind"),
            }

            icon_map = {
                "low": "dialog-information",
                "normal": "appointment-soon",
                "critical": "dialog-warning",
            }
            icon = icon_map.get(urgency, "dialog-information")

            notify_interface.Notify(
                "Remind", 0, icon, title, message, [], hints, 5000,
            )
            return True
        except (DBusException, Exception):
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
                    "--urgency", urgency_str,
                    "--app-name", "Remind",
                    title,
                    message,
                ],
                timeout=5,
                capture_output=True,
                check=False,
            )
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def notify_reminder_due(
        self, reminder_text: str, sound: bool = False, callback: Callable | None = None
    ) -> bool:
        """Send a notification for a due reminder."""
        message = reminder_text[:150] + ("..." if len(reminder_text) > 150 else "")
        return self.notify(
            title="Remind",
            message=message,
            urgency="normal",
            callback=callback,
            sound=sound,
        )

    def notify_nudge(self, reminder_text: str, sound: bool = False) -> bool:
        """Send a nudge notification for an escalated reminder."""
        message = reminder_text[:150] + ("..." if len(reminder_text) > 150 else "")
        return self.notify(
            title="Remind - Still Due",
            message=message,
            urgency="critical",
            sound=sound,
        )

    @staticmethod
    def is_supported() -> bool:
        """Check if notifications are supported on this platform."""
        return Notify is not None
