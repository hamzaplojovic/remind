# Remind CLI

A terminal-native reminder engine with AI-powered suggestions, desktop notifications, and Claude Code integration.

Runs on **macOS** and **Linux**. Requires Python 3.12+.

---

## Installation

**Recommended** (isolated environment via [uv](https://docs.astral.sh/uv/)):

```bash
uv tool install remind-cli
```

**Via pip:**

```bash
pip install remind-cli
```

**One-line installer:**

```bash
curl -fsSL remind.hamzaplojovic.blog/install | sh
```

Verify the installation:

```bash
remind --version
```

---

## Quick Start

```bash
# Create a reminder
remind add "Deploy v2.0 to production" --due "friday 3pm" --priority high

# List active reminders
remind list

# Mark a reminder as done
remind done 1

# Search by keyword
remind search "deploy"
```

---

## Commands

| Command | Description |
|---------|-------------|
| `add` | Create a reminder. Flags: `--due`, `--priority`, `--project`, `--no-ai` |
| `list` | Show active reminders. Flags: `--all`, `--priority`, `--json` |
| `done` | Mark a reminder as complete by ID |
| `search` | Full-text search across all reminders |
| `login` | Authenticate with a license token |
| `register` | Sign up and purchase a plan via Polar checkout |
| `settings` | View or modify configuration. Flags: `--view`, `--set` |
| `usage` | View AI usage statistics for the current billing period |
| `scheduler` | Run the background notification daemon. Flag: `--run` |
| `doctor` | Run diagnostic checks on your Remind installation |
| `upgrade` | View available plans or change your current plan |
| `update` | Self-update to the latest version |
| `mcp` | Start the MCP server for Claude Code integration |
| `uninstall` | Remove Remind configuration from your system |

Run `remind <command> --help` for detailed usage on any command.

---

## Claude Code / MCP Integration

Remind ships with a built-in [Model Context Protocol](https://modelcontextprotocol.io/) server, giving Claude Code direct access to your reminders.

### Setup

Add the following to your `.claude/settings.json`:

```json
{
  "mcpServers": {
    "remind": {
      "command": "remind",
      "args": ["mcp"]
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `add_reminder` | Create a reminder with optional due date, priority, and project |
| `list_reminders` | List active or all reminders |
| `complete_reminder` | Mark a reminder as done |
| `search_reminders` | Search reminders by text |
| `update_reminder` | Modify an existing reminder |
| `delete_reminder` | Permanently remove a reminder |
| `agent_reminder` | Schedule Claude Code to execute a task autonomously at a future time |

---

## Pricing

All plans include the full CLI feature set. Plans differ by the number of AI-powered suggestions per month.

| Plan | Price | AI Suggestions |
|------|-------|----------------|
| Free | $0 | 5 / month |
| Indie | $5 / month | 100 / month |
| Pro | $15 / month | 1,000 / month |
| Team | $50 / month | 5,000 / month |

Register from the terminal:

```bash
remind register
```

---

## Links

- **Website:** [remind.hamzaplojovic.blog](https://remind.hamzaplojovic.blog)
- **Documentation:** [remind.hamzaplojovic.blog/docs](https://remind.hamzaplojovic.blog/docs/)
- **GitHub:** [github.com/hamzaplojovic/remind](https://github.com/hamzaplojovic/remind)
- **Issues:** [github.com/hamzaplojovic/remind/issues](https://github.com/hamzaplojovic/remind/issues)
- **PyPI:** [pypi.org/project/remind-cli](https://pypi.org/project/remind-cli/)

---

## License

MIT

<img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=d183fc32-8844-4bb4-b7af-1b2fa945b8a2" />
