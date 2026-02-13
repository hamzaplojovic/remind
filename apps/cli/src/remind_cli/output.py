"""Output formatting layer for Remind CLI.

Provides a cohesive editorial design language matching the remind.hamzaplojovic.blog website:
- Coral-red for accents and errors
- Sage green for success
- Amber for warnings and priority highlights
- Clean typography with uppercase labels, generous spacing
- Solid/dotted rules as dividers — no emoji clutter
"""

import json
import sys
from contextlib import contextmanager
from typing import Generator

from rich.console import Console
from rich.table import Table
from rich.theme import Theme
from rich.text import Text

# ── Brand Theme ──────────────────────────────────────────────────────
_THEME = Theme(
    {
        "brand": "bold",
        "accent": "#e8503a",
        "success": "#52b788",
        "warning": "#f0c674",
        "error": "#e8503a",
        "muted": "#b0a99e",
        "label": "bold #b0a99e",
        "value": "bold",
        "hint": "dim italic",
        "rule": "#b0a99e",
        "header.title": "bold",
        "header.label": "bold #e8503a",
        "table.header": "bold #b0a99e",
        "priority.high": "bold #e8503a",
        "priority.medium": "#f0c674",
        "priority.low": "#52b788",
    }
)

console = Console(theme=_THEME, highlight=False)
_stderr = Console(theme=_THEME, highlight=False, file=sys.stderr)

# ── Branding ─────────────────────────────────────────────────────────
BRAND = Text.assemble(("remind", "bold"), (".", "accent"))
RULE_CHAR = "─"
DOT_CHAR = "·"


# ── Primitives ───────────────────────────────────────────────────────

def brand() -> None:
    """Print the remind. brand mark with a blank line after."""
    console.print()
    console.print(BRAND)


def rule(width: int = 44) -> None:
    """Print a solid horizontal rule."""
    console.print(f"[rule]{RULE_CHAR * width}[/rule]")


def dot_rule(width: int = 44) -> None:
    """Print a dotted horizontal rule."""
    dots = f" {DOT_CHAR}" * (width // 2)
    console.print(f"[rule]{dots}[/rule]")


def blank() -> None:
    """Print a blank line."""
    console.print()


def header(title: str) -> None:
    """Print an uppercase section header in accent color."""
    console.print()
    console.print(BRAND)
    console.print(f"[header.label]{title.upper()}[/header.label]")
    rule()


def label_value(label: str, value: str, label_width: int = 18) -> None:
    """Print a label-value pair: LABEL  value."""
    padded = label.upper().ljust(label_width)
    console.print(f"  [label]{padded}[/label] {value}")


# ── Messaging ────────────────────────────────────────────────────────

def success(message: str) -> None:
    """Print a success message: ✓ message."""
    console.print(f"  [success]✓[/success] {message}")


def error(message: str) -> None:
    """Print an error message: ✗ message."""
    _stderr.print(f"  [error]✗[/error] {message}")


def warning(message: str) -> None:
    """Print a warning message: ! message."""
    _stderr.print(f"  [warning]![/warning] {message}")


def info(message: str) -> None:
    """Print an info message (muted)."""
    console.print(f"  [muted]{message}[/muted]")


def hint(message: str) -> None:
    """Print a hint/suggestion (dim italic)."""
    console.print(f"  [hint]{message}[/hint]")


def text(message: str) -> None:
    """Print plain text with indent."""
    console.print(f"  {message}")


def ai_suggestion(suggestion: str) -> None:
    """Print an AI suggestion with accent styling."""
    console.print(f"  [label]AI[/label]  [accent]{suggestion}[/accent]")


# ── Priority ─────────────────────────────────────────────────────────

def format_priority(priority_value: str) -> str:
    """Return Rich markup for a priority level."""
    styles = {
        "high": "[priority.high]HIGH[/priority.high]",
        "medium": "[priority.medium]MED[/priority.medium]",
        "low": "[priority.low]LOW[/priority.low]",
    }
    return styles.get(priority_value, f"[muted]{priority_value.upper()}[/muted]")


# ── Tables ───────────────────────────────────────────────────────────

def reminders_table(rows: list[dict]) -> None:
    """Print a branded reminders table.

    Args:
        rows: List of dicts with keys: id, text, due, priority, done (optional)
    """
    table = Table(
        show_header=True,
        header_style="table.header",
        show_edge=False,
        show_lines=False,
        padding=(0, 2),
        pad_edge=True,
    )
    table.add_column("ID", style="muted", width=5, justify="right")
    has_done = any("done" in r for r in rows)
    if has_done:
        table.add_column("", width=2)
    table.add_column("TEXT", min_width=20)
    table.add_column("DUE", style="muted", min_width=14)
    table.add_column("PRI", min_width=6)

    for row in rows:
        cells = [str(row["id"])]
        if has_done:
            done_mark = "[success]✓[/success]" if row.get("done") else "[muted]○[/muted]"
            cells.append(done_mark)
        cells.append(row["text"])
        cells.append(row.get("due", ""))
        cells.append(format_priority(row.get("priority", "medium")))
        table.add_row(*cells)

    console.print()
    console.print(table)
    blank()
    info(f"{len(rows)} reminder{'s' if len(rows) != 1 else ''}")


def key_value_table(data: dict[str, str], title: str | None = None) -> None:
    """Print a clean key-value table (for reports, settings, etc.)."""
    table = Table(
        show_header=bool(title),
        header_style="table.header",
        show_edge=False,
        show_lines=False,
        padding=(0, 2),
        pad_edge=True,
        title=title,
        title_style="header.label",
    )
    table.add_column("", style="label", min_width=22)
    table.add_column("")

    for key, value in data.items():
        table.add_row(key.upper(), str(value))

    console.print()
    console.print(table)


# ── JSON ─────────────────────────────────────────────────────────────

def print_json(data: object) -> None:
    """Pretty-print JSON data."""
    console.print_json(json.dumps(data, indent=2, default=str))


# ── Spinner ──────────────────────────────────────────────────────────

@contextmanager
def spinner(message: str) -> Generator[None, None, None]:
    """Show a branded spinner during an operation."""
    with console.status(f"[muted]{message}[/muted]", spinner="dots"):
        yield


# ── Command Helpers ──────────────────────────────────────────────────

def command_row(cmd: str, desc: str, cmd_width: int = 30) -> None:
    """Print a single command + description row for help screens."""
    padded = cmd.ljust(cmd_width)
    console.print(f"  [accent]{padded}[/accent] [muted]{desc}[/muted]")
