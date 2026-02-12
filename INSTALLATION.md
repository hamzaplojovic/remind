# Remind Installation Guide

## Overview

Remind can be installed via:
1. **Official Homebrew** (macOS/Linux) - Recommended
2. **Community Homebrew Tap** - Until in homebrew-core
3. **Curl Installation Script** - Cross-platform
4. **Direct GitHub Release** - Manual binary download
5. **From Source** - For development

## Quick Install

### macOS (Homebrew)
```bash
curl -sSL https://remind.dev/install.sh | bash
```

**What happens:**
1. ✓ Detects macOS platform
2. ✓ Checks for Homebrew (installs if needed)
3. ✓ Installs Remind CLI via Homebrew tap
4. ✓ Sets up background daemon (LaunchAgent)
5. ✓ Sends native notification: "Remind Installation Complete"
6. ✓ Sends daemon notification: "Background scheduler is running..."

### Linux (pip)
```bash
curl -sSL https://remind.dev/install.sh | bash
```

**What happens:**
1. ✓ Detects Linux platform
2. ✓ Checks for Python 3.12+
3. ✓ Installs Remind CLI via pip from GitHub
4. ✓ Installs dbus-python for notifications
5. ✓ Sets up background daemon (systemd user service)
6. ✓ Sends native notification: "Remind Installation Complete"
7. ✓ Sends daemon notification: "Background scheduler is running..."

## Installation Features

### Daemon Setup (Automatic)
Both macOS and Linux installations automatically set up and enable the background scheduler:

**macOS:**
- Uses LaunchAgent (`~/Library/LaunchAgents/com.remind.scheduler.plist`)
- Runs at system startup
- Logs to `~/.remind/logs/scheduler.log`

**Linux:**
- Uses systemd user service (`~/.config/systemd/user/remind-scheduler.service`)
- Runs at user login
- Logs to system journal

### Success Notifications

The installation script sends **two success notifications**:

1. **Installation Complete** (after verification)
   - macOS: "Installation complete! Daemon is running and ready to send reminders."
   - Linux: "Daemon is running and ready to send reminders"

2. **Daemon Started** (after scheduler setup)
   - macOS: "Background scheduler is running and will check for reminders every 5 minutes"
   - Linux: "Background scheduler is running and will check for reminders every 5 minutes"

### Notification System

The installation uses native OS notifications:

**macOS:**
```bash
osascript -e 'display notification "message" with title "Remind"'
```

**Linux:**
```bash
notify-send --app-name "Remind" "title" "message"
```

Both gracefully degrade if the notification system is unavailable.

## Daemon Management

After installation, manage the background scheduler with:

### Check Status
```bash
remind scheduler --status
```

Output:
```
╔════════════════════════════════╗
║     SCHEDULER STATUS           ║
╚════════════════════════════════╝

Status         ✓ Installed
Check interval 5 minutes

Use --disable to stop background reminders
```

### Disable Scheduler
```bash
remind scheduler --disable
```

### Enable Scheduler
```bash
remind scheduler --enable
```

### View Logs

**macOS:**
```bash
tail -f ~/.remind/logs/scheduler.log
```

**Linux:**
```bash
journalctl --user -u remind-scheduler.service -f
```

## Quick Start

After installation is complete:

```bash
# Add a reminder
remind add "Buy groceries" --due "tomorrow 5pm"

# View all reminders
remind list

# Mark reminder as done
remind done 1

# Check scheduler status
remind scheduler --status
```

## Troubleshooting

### Notifications not appearing

If you don't see the installation success notifications:

**macOS:**
- Check System Preferences → Notifications
- Ensure notifications are enabled for "Terminal" or your shell
- The notification should appear in Notification Center

**Linux:**
- Ensure `notify-send` is installed: `sudo apt install libnotify-bin`
- Check that the D-Bus session is running: `echo $DBUS_SESSION_BUS_ADDRESS`

### Daemon not starting reminders

Check if the daemon is running:

```bash
# macOS
launchctl list | grep com.remind

# Linux
systemctl --user status remind-scheduler.service
```

### Python version issues (Linux)

Requires Python 3.12+:
```bash
python3 --version
```

If you have Python 3.11 or lower, install Python 3.12:
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv
```

## Platform Support

| Feature | macOS | Linux |
|---------|-------|-------|
| CLI Installation | ✓ Homebrew | ✓ pip (GitHub) |
| Background Daemon | ✓ LaunchAgent | ✓ systemd |
| Notifications | ✓ Native AppleScript | ✓ D-Bus/notify-send |
| Installation Success Notification | ✓ Yes | ✓ Yes |
| Daemon Started Notification | ✓ Yes | ✓ Yes |
| Automatic Daemon Startup | ✓ On boot | ✓ On login |

## Installation Verification

The installation script automatically verifies:

1. ✓ Platform detection (macOS/Linux/ARM/x86)
2. ✓ Package manager availability (Homebrew/pip)
3. ✓ Python version (3.12+ for Linux)
4. ✓ `remind` command installed
5. ✓ Daemon installation
6. ✓ Notification delivery

All checks must pass for successful installation.
