"""Version check — notify user when a newer CLI version is available.

Checks PyPI at most once per day (cached in ~/.remind/version_check.json).
Non-blocking: never delays CLI execution on network failure.
"""

import json
import time
from pathlib import Path

import httpx

from remind_cli import __version__

_CACHE_FILE = Path.home() / ".remind" / "version_check.json"
_CHECK_INTERVAL = 86400  # 24 hours
_PYPI_URL = "https://pypi.org/pypi/remind-cli/json"


def _read_cache() -> dict:
    try:
        return json.loads(_CACHE_FILE.read_text())
    except Exception:
        return {}


def _write_cache(data: dict) -> None:
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(json.dumps(data))
    except Exception:
        pass


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse '1.2.3' into (1, 2, 3) for comparison."""
    try:
        return tuple(int(x) for x in v.strip().split("."))
    except Exception:
        return (0,)


def get_update_notice() -> str | None:
    """Return an update notice string if a newer version exists, else None.

    Checks PyPI at most once per day. Returns immediately on any failure.
    """
    cache = _read_cache()
    now = time.time()

    # Use cached result if fresh enough
    if now - cache.get("checked_at", 0) < _CHECK_INTERVAL:
        latest = cache.get("latest_version")
        if latest and _parse_version(latest) > _parse_version(__version__):
            return f"Update available: {__version__} → {latest}  (run: remind update)"
        return None

    # Fetch from PyPI (short timeout — never block the CLI)
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(_PYPI_URL)
            if resp.status_code != 200:
                return None
            latest = resp.json()["info"]["version"]
    except Exception:
        return None

    _write_cache({"latest_version": latest, "checked_at": now})

    if _parse_version(latest) > _parse_version(__version__):
        return f"Update available: {__version__} → {latest}  (run: remind update)"
    return None
