"""CLI utilities for Remind: output modes, exit codes, error formatting."""

from difflib import get_close_matches

import typer

from remind.models import Reminder
from remind.output import format_as_json

# Exit codes matching standard conventions
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_INVALID_INPUT = 2
EXIT_NOT_FOUND = 3

# Global output mode state
_quiet_mode = False


def set_quiet_mode(enabled: bool) -> None:
    """Set quiet mode globally.

    Args:
        enabled: Whether to enable quiet mode
    """
    global _quiet_mode
    _quiet_mode = enabled


def is_quiet() -> bool:
    """Check if quiet mode is enabled.

    Returns:
        True if quiet mode is enabled
    """
    return _quiet_mode


def echo(message: str, **kwargs) -> None:
    """Output message respecting quiet mode.

    Args:
        message: Message to output
        **kwargs: Additional arguments for typer.echo()

    Example:
        echo("✓ Reminder added")  # Suppressed in quiet mode
    """
    if not is_quiet():
        typer.echo(message, **kwargs)


def echo_json(data: "Reminder | list[Reminder]") -> None:
    """Output JSON (always, ignoring quiet mode).

    Args:
        data: Single Reminder or list of Reminders to output

    Example:
        reminders = db.list_active_reminders()
        echo_json(reminders)
    """
    typer.echo(format_as_json(data))


def format_error(
    message: str,
    hint: str | None = None,
    suggestions: list[str] | None = None,
) -> str:
    """Format error with hints and suggestions.

    Args:
        message: Main error message
        hint: Optional helpful hint
        suggestions: Optional list of suggestions

    Returns:
        Formatted error string

    Example:
        error_msg = format_error(
            f"Invalid priority: {priority}",
            hint="Valid values: high, medium, low",
            suggestions=["high", "medium", "low"]
        )
    """
    output = f"✗ {message}"

    if hint:
        output += f"\n💡 Hint: {hint}"

    if suggestions:
        output += "\n\nDid you mean?"
        for suggestion in suggestions:
            output += f"\n  • {suggestion}"

    return output


def find_similar(invalid: str, valid_options: list[str], cutoff: float = 0.6) -> list[str]:
    """Fuzzy match for suggestions using difflib.

    Args:
        invalid: Invalid input string
        valid_options: List of valid options to match against
        cutoff: Similarity threshold (0.0-1.0, default 0.6)

    Returns:
        List of up to 3 similar options

    Example:
        suggestions = find_similar("hih", ["high", "medium", "low"])
        # Returns: ["high"]
    """
    return get_close_matches(
        invalid.lower(),
        [opt.lower() for opt in valid_options],
        n=3,
        cutoff=cutoff,
    )
