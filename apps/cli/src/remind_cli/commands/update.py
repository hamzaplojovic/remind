"""Update command - update the CLI to the latest version."""

import os
import shutil
import subprocess
import sys

import typer

from remind_cli import __version__, output


def _detect_install_method() -> str:
    """Detect how remind was installed.

    Returns one of: 'pip', 'brew', 'binary', 'source'
    """
    # Check brew first
    if shutil.which("brew"):
        try:
            result = subprocess.run(
                ["brew", "list", "remind"],
                capture_output=True, timeout=5,
            )
            if result.returncode == 0:
                return "brew"
        except Exception:
            pass

    # Check if running from a uv tool install (uvx)
    remind_bin = shutil.which("remind")
    if remind_bin:
        resolved = os.path.realpath(remind_bin)
        if "/uv/tools/" in resolved or "/.local/share/uv/" in resolved:
            return "uv"

    # Check if running from a pip installed package
    if remind_bin:
        resolved = os.path.realpath(remind_bin)
        if "site-packages" in resolved or "/.venv/" in resolved or "/venv/" in resolved:
            return "pip"

    # Check if we're in a git repo (development/source install)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, timeout=3,
        )
        if result.returncode == 0:
            return "source"
    except Exception:
        pass

    # Standalone binary (no pip, no brew, no git)
    if remind_bin:
        return "binary"

    return "pip"  # safe default


def update() -> None:
    """Update Remind CLI to the latest version.

    Detects your installation method and runs the appropriate update.

    Examples:
      remind update
    """
    method = _detect_install_method()

    output.blank()
    output.info(f"Current version: {__version__}")
    output.info(f"Install method:  {method}")
    output.blank()

    if method == "brew":
        output.info("Updating via Homebrew...")
        output.blank()
        try:
            subprocess.run(["brew", "upgrade", "remind"], check=True)
            output.blank()
            output.success("Updated successfully.")
        except subprocess.CalledProcessError:
            output.error("Homebrew update failed. Try: brew upgrade remind")
            raise typer.Exit(1)

    elif method == "uv":
        output.info("Updating via uv...")
        output.blank()
        try:
            subprocess.run(
                ["uv", "tool", "upgrade", "remind-cli"],
                check=True,
            )
            output.blank()
            output.success("Updated successfully.")
        except subprocess.CalledProcessError:
            output.error("uv update failed. Try: uv tool upgrade remind-cli")
            raise typer.Exit(1)

    elif method == "pip":
        output.info("Updating via pip...")
        output.blank()
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "remind-cli"],
                check=True,
            )
            output.blank()
            output.success("Updated successfully.")
        except subprocess.CalledProcessError:
            output.error("pip update failed. Try: pip install --upgrade remind-cli")
            raise typer.Exit(1)

    elif method == "binary":
        output.info("Standalone binary detected.")
        output.blank()
        output.hint("Download the latest release from:")
        output.hint("  https://github.com/hamzaplojovic/remind/releases/latest")
        output.blank()

    elif method == "source":
        output.info("Source/dev install detected.")
        output.blank()
        output.hint("Run: git pull && uv sync")
        output.blank()

    else:
        output.error("Could not detect installation method.")
        output.hint("Try: pip install --upgrade remind-cli")
        raise typer.Exit(1)

    output.blank()
