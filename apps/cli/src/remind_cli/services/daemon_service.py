"""Daemon scheduler service installation and management."""

import os
import subprocess
import sys
from pathlib import Path

from remind_cli.platform_utils import get_platform, get_logs_dir
from remind_cli.utils import ensure_dir, run_command


class DaemonService:
    """Install and manage background reminder scheduler."""

    def __init__(self):
        """Initialize daemon service."""
        self.platform = get_platform()

    def install(self) -> bool:
        """Install scheduler as a background service.

        Returns:
            True if installation successful, False otherwise
        """
        if self.platform.is_macos:
            return self._install_macos_agent()
        elif self.platform.is_linux:
            return self._install_linux_service()
        else:
            return False

    def uninstall(self) -> bool:
        """Uninstall scheduler background service.

        Returns:
            True if uninstallation successful, False otherwise
        """
        if self.platform.is_macos:
            return self._uninstall_macos_agent()
        elif self.platform.is_linux:
            return self._uninstall_linux_service()
        else:
            return False

    def is_installed(self) -> bool:
        """Check if scheduler service is installed.

        Returns:
            True if service is installed
        """
        if self.platform.is_macos:
            plist_path = Path.home() / "Library" / "LaunchAgents" / "com.remind.scheduler.plist"
            return plist_path.exists()
        elif self.platform.is_linux:
            service_path = (
                Path.home() / ".config" / "systemd" / "user" / "remind-scheduler.service"
            )
            return service_path.exists()
        return False

    def _install_macos_agent(self) -> bool:
        """Install macOS launchd agent.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the path to the remind binary
            remind_path = self._get_remind_path()
            if not remind_path:
                return False

            # Create LaunchAgent directory
            la_dir = ensure_dir(Path.home() / "Library" / "LaunchAgents")

            # Create plist file
            plist_path = la_dir / "com.remind.scheduler.plist"
            logs_dir = get_logs_dir()

            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.remind.scheduler</string>
    <key>Program</key>
    <string>{remind_path}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{remind_path}</string>
        <string>scheduler</string>
        <string>--run</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{logs_dir}/scheduler.log</string>
    <key>StandardErrorPath</key>
    <string>{logs_dir}/scheduler.error.log</string>
</dict>
</plist>
"""

            # Write plist file
            plist_path.write_text(plist_content)

            # Load the service
            try:
                run_command(["launchctl", "load", str(plist_path)])
                return True
            except subprocess.CalledProcessError:
                # If load fails, try unloading first (in case it's already there)
                try:
                    run_command(["launchctl", "unload", str(plist_path)], check=False)
                except Exception:
                    pass
                # Then load again
                run_command(["launchctl", "load", str(plist_path)])
                return True

        except Exception:
            return False

    def _install_linux_service(self) -> bool:
        """Install Linux systemd user service.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the path to the remind binary
            remind_path = self._get_remind_path()
            if not remind_path:
                return False

            # Create systemd user services directory
            sd_dir = ensure_dir(Path.home() / ".config" / "systemd" / "user")

            # Create service file
            service_path = sd_dir / "remind-scheduler.service"

            service_content = f"""[Unit]
Description=Remind - Background Reminder Scheduler
After=network.target

[Service]
Type=simple
ExecStart={remind_path} scheduler --run
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
"""

            # Write service file
            service_path.write_text(service_content)
            service_path.chmod(0o644)

            # Ensure logs directory exists
            get_logs_dir()

            # Reload and enable the service
            run_command(["systemctl", "--user", "daemon-reload"])
            run_command(["systemctl", "--user", "enable", "remind-scheduler.service"])
            run_command(["systemctl", "--user", "start", "remind-scheduler.service"])
            return True

        except subprocess.CalledProcessError:
            return False
        except Exception:
            return False

    def _uninstall_macos_agent(self) -> bool:
        """Uninstall macOS launchd agent.

        Returns:
            True if successful, False otherwise
        """
        try:
            plist_path = Path.home() / "Library" / "LaunchAgents" / "com.remind.scheduler.plist"

            if not plist_path.exists():
                return True  # Already uninstalled

            # Unload the service
            try:
                run_command(["launchctl", "unload", str(plist_path)])
            except subprocess.CalledProcessError:
                pass

            # Remove the plist file
            plist_path.unlink()
            return True

        except Exception:
            return False

    def _uninstall_linux_service(self) -> bool:
        """Uninstall Linux systemd user service.

        Returns:
            True if successful, False otherwise
        """
        try:
            service_path = (
                Path.home() / ".config" / "systemd" / "user" / "remind-scheduler.service"
            )

            if not service_path.exists():
                return True  # Already uninstalled

            # Stop and disable the service
            try:
                run_command(["systemctl", "--user", "stop", "remind-scheduler.service"])
                run_command(["systemctl", "--user", "disable", "remind-scheduler.service"])
                run_command(["systemctl", "--user", "daemon-reload"])
            except subprocess.CalledProcessError:
                pass

            # Remove the service file
            service_path.unlink()
            return True

        except Exception:
            return False

    @staticmethod
    def _get_remind_path() -> str | None:
        """Get the path to the remind binary.

        Returns:
            Path to remind binary, or None if not found
        """
        try:
            # Try to get the path from sys.argv[0]
            remind_path = os.path.abspath(sys.argv[0])
            if os.path.exists(remind_path) and os.access(remind_path, os.X_OK):
                return remind_path

            # Try to find remind in PATH
            result = run_command(["which", "remind"], check=False)
            if result.returncode == 0:
                return result.stdout.decode().strip()

            return None
        except Exception:
            return None
