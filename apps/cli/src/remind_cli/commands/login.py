"""Login command - authenticate with license token."""

import httpx
import typer

from remind_shared import AuthenticationError
from remind_cli.config import load_config
from remind_cli.services.config_service import ConfigService
from remind_cli import output


def _resolve_plan_tier(token: str, backend_url: str | None) -> str:
    """Query backend for actual plan tier. Falls back to token parsing."""
    if backend_url:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    f"{backend_url.rstrip('/')}/api/v1/usage/stats",
                    params={"license_token": token},
                )
                if resp.status_code == 200:
                    return resp.json().get("plan_tier", "free")
        except Exception:
            pass

    # Fallback: parse from token prefix
    for tier in ("team", "pro", "indie"):
        if tier in token:
            return tier
    return "free"


def login(token: str = typer.Argument(..., help="License token")) -> None:
    """Authenticate with Remind license token.

    Examples:
      remind login remind_indie_abc123xyz789
      remind login remind_pro_xyz789abc123
    """
    try:
        if not token.startswith("remind_"):
            raise AuthenticationError("Invalid token format. Must start with 'remind_'")

        config_service = ConfigService()
        config_service.set_license_token(token)

        # Resolve plan tier from backend
        config = load_config()
        plan_tier = _resolve_plan_tier(token, config.ai_backend_url)
        config_service.set_setting("plan_tier", plan_tier)

        tier_display = plan_tier.capitalize()

        output.blank()
        output.success("Logged in successfully")
        output.label_value("Plan", tier_display)
        output.blank()

        # Auto-install background scheduler
        try:
            from remind_cli.services.daemon_service import DaemonService

            daemon = DaemonService()
            if not daemon.is_installed():
                with output.spinner("Installing background scheduler"):
                    success = daemon.install()
                if success:
                    output.success("Background scheduler installed")
                    output.blank()
        except Exception:
            pass  # Non-critical — don't fail login over scheduler

    except AuthenticationError as e:
        output.error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
