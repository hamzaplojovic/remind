"""Usage command - show real usage statistics from backend."""

import httpx
import typer

from remind_cli.config import load_config
from remind_cli.services.config_service import ConfigService
from remind_cli import output


def usage() -> None:
    """Show AI usage statistics and quota.

    Examples:
      remind usage
    """
    try:
        config_service = ConfigService()
        token = config_service.get_license_token()

        if not token:
            output.error("Not logged in. Use 'remind login <token>' first.")
            raise typer.Exit(1)

        config = load_config()
        backend_url = config.ai_backend_url

        if not backend_url:
            output.error("No backend URL configured.")
            raise typer.Exit(1)

        # Fetch real usage from backend
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    f"{backend_url.rstrip('/')}/api/v1/usage/stats",
                    params={"license_token": token},
                )

                if resp.status_code == 401:
                    output.error("Invalid license token. Try 'remind login <token>' again.")
                    raise typer.Exit(1)
                elif resp.status_code != 200:
                    output.error(f"Backend error: {resp.status_code}")
                    raise typer.Exit(1)

                data = resp.json()
        except httpx.ConnectError:
            output.error("Cannot reach backend. Is the server running?")
            raise typer.Exit(1)

        plan_tier = data.get("plan_tier", "free").capitalize()
        quota_used = data.get("ai_quota_used", 0)
        quota_total = data.get("ai_quota_total", 0)
        quota_remaining = data.get("ai_quota_remaining", 0)
        cost_cents = data.get("this_month_cost_cents", 0)
        rate_remaining = data.get("rate_limit_remaining", 0)

        output.header("USAGE")

        output.label_value("Plan", plan_tier)
        output.blank()
        output.dot_rule()
        output.blank()

        output.label_value("AI suggestions", f"{quota_used} / {quota_total}")
        output.label_value("Remaining", str(quota_remaining))
        output.label_value("Cost this month", f"${cost_cents / 100:.2f}")
        output.blank()
        output.dot_rule()
        output.blank()
        output.label_value("Rate limit left", str(rate_remaining))

        output.blank()

    except typer.Exit:
        raise
    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
