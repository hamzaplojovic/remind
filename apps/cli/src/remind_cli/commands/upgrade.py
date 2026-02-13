"""Upgrade command - upgrade to a higher plan."""

import webbrowser

import typer

from remind_cli.config import load_config
from remind_cli.services.config_service import ConfigService
from remind_cli import output

TIER_ORDER = ["free", "indie", "pro", "team"]

PLANS = {
    "free": {"price": "$0/mo", "limit": "5 AI suggestions"},
    "indie": {"price": "$5/mo", "limit": "100 AI suggestions"},
    "pro": {"price": "$15/mo", "limit": "1,000 AI suggestions"},
    "team": {"price": "$50/mo", "limit": "5,000+ AI suggestions"},
}


def _get_current_tier(config_service: ConfigService) -> str:
    """Get current plan tier."""
    plan_tier = config_service.get_setting("plan_tier")
    if plan_tier:
        return plan_tier.lower()
    token = config_service.get_license_token()
    if not token:
        return "free"
    for tier in ("team", "pro", "indie"):
        if tier in token:
            return tier
    return "free"


def upgrade() -> None:
    """Upgrade to a higher Remind plan.

    Shows only plans above your current tier and opens
    checkout in your browser.

    Examples:
      remind upgrade
    """
    try:
        config_service = ConfigService()
        current = _get_current_tier(config_service)
        current_idx = TIER_ORDER.index(current) if current in TIER_ORDER else 0

        config = load_config()
        backend_url = (config.ai_backend_url or "").rstrip("/")

        output.header("UPGRADE")
        output.label_value("Current plan", current.capitalize())
        output.blank()
        output.dot_rule()
        output.blank()

        # Only show higher tiers
        available = TIER_ORDER[current_idx + 1:]

        if not available:
            output.success("You're on the highest plan!")
            output.blank()
            return

        output.console.print("  Available upgrades:")
        output.blank()

        for i, plan in enumerate(available, 1):
            info = PLANS[plan]
            label = plan.upper().ljust(6)
            output.console.print(
                f"  [label]{i}[/label]  {label}  {info['price'].ljust(8)}  {info['limit']}"
            )

        output.blank()
        output.dot_rule()
        output.blank()

        if not backend_url:
            output.hint("Visit https://remind.hamzaplojovic.blog to upgrade")
            output.blank()
            return

        choice = typer.prompt(f"Enter plan number (1-{len(available)}) or 0 to cancel", type=int)

        if choice == 0:
            output.blank()
            return

        if choice < 1 or choice > len(available):
            output.error("Invalid choice")
            raise typer.Exit(1)

        plan = available[choice - 1]
        checkout_url = f"{backend_url}/api/v1/checkout/{plan}"

        output.blank()
        with output.spinner(f"Opening {plan.capitalize()} checkout"):
            webbrowser.open(checkout_url)

        output.success(f"Opened {plan.capitalize()} checkout in your browser")
        output.blank()
        output.hint("After payment, your plan will be upgraded automatically")
        output.blank()

    except typer.Exit:
        raise
    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
