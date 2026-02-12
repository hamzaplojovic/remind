"""Upgrade command - upgrade to paid plan."""

import typer

from remind_cli.services.config_service import ConfigService
from remind_cli import output


def _get_plan_display(config_service: ConfigService) -> str:
    """Get plan tier from stored config."""
    plan_tier = config_service.get_setting("plan_tier")
    if plan_tier:
        return plan_tier.capitalize()
    token = config_service.get_license_token()
    if not token:
        return "Free"
    for tier in ("team", "pro", "indie"):
        if tier in token:
            return tier.capitalize()
    return "Free"


def upgrade() -> None:
    """Upgrade to a paid Remind plan.

    Plans:
    - Free: 5 AI suggestions/month
    - Indie: 100 AI suggestions/month ($5/mo)
    - Pro: 1,000 AI suggestions/month ($15/mo)
    - Team: 5,000+ AI suggestions/month ($50/mo)

    Examples:
      remind upgrade
    """
    try:
        config_service = ConfigService()
        plan = _get_plan_display(config_service)

        output.header("PLANS")
        output.label_value("Current plan", plan)
        output.blank()
        output.dot_rule()
        output.blank()

        output.console.print("  [label]FREE              [/label] $0/mo      5 AI suggestions")
        output.console.print("  [label]INDIE             [/label] $5/mo      100 AI suggestions")
        output.console.print("  [label]PRO              [/label]  $15/mo     1,000 AI suggestions")
        output.console.print("  [label]TEAM             [/label]  $50/mo     5,000+ AI suggestions")

        output.blank()
        output.rule()
        output.hint("Visit https://remind.dev/upgrade to manage your plan")
        output.blank()

    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
