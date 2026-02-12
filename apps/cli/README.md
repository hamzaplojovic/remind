# Remind CLI

AI-powered command-line reminder and notification engine.

## Quick Start

```bash
remind add "Buy groceries" --due "tomorrow 5pm"
remind list
remind done 1
```

## Features

- AI-powered reminder suggestions
- Smart scheduling and notifications
- Full-text search
- Cross-platform support (macOS, Linux, Windows)
- License-based plan tiers (Free, Pro, Enterprise)

## Installation

```bash
pip install remind-cli
```

Or build from source:

```bash
uv sync
uv run remind --help
```

## Commands

- `add` - Create a new reminder
- `list` - List all reminders
- `done` - Mark reminder as complete
- `search` - Search reminders by text
- `login` - Authenticate with license token
- `settings` - Manage configuration
- `report` - View usage statistics
- `scheduler` - Manage background scheduler
- `doctor` - Diagnose issues
- `upgrade` - View pricing plans
- `uninstall` - Remove Remind

## Documentation

See [../../REFACTORING_COMPLETE.md](../../REFACTORING_COMPLETE.md) for architecture and implementation details.
