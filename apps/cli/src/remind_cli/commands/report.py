"""Report command - show usage and statistics."""

from datetime import datetime, timezone

import typer

from remind_cli.services.config_service import ConfigService
from remind_cli import output


def report(
    format: str = typer.Option("table", "--format", "-f", help="Output format (table, json)"),
) -> None:
    """Show usage statistics and reminder insights.

    Examples:
      remind report
      remind report --format json
    """
    try:
        config_service = ConfigService()
        token = config_service.get_license_token()

        if not token:
            output.error("Not logged in. Use 'remind login <token>' first")
            raise typer.Exit(1)

        # TODO: Fetch real data from backend API
        stats = {
            "Total reminders": "24",
            "Completed this month": "18",
            "Overdue": "2",
            "Due today": "3",
            "AI suggestions used": "12",
        }

        if format == "json":
            output.print_json(stats)
        else:
            output.header("USAGE REPORT")

            output.key_value_table(stats)

            output.blank()
            output.rule()

            # Determine tier and show quota
            if "pro" in token:
                plan_info = "Pro — 1,000 AI suggestions/month"
            elif "enterprise" in token:
                plan_info = "Enterprise — Unlimited"
            else:
                plan_info = "Free — 5 AI suggestions/month"

            output.label_value("Plan", plan_info)
            output.label_value(
                "Generated",
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            )
            output.blank()

    except typer.Exit:
        raise
    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
