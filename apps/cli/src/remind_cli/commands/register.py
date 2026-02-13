"""Register command - sign up for a Remind plan via Polar checkout."""

import webbrowser

import typer

from remind_cli.config import load_config
from remind_cli import output

PLANS = {
    "free": {"price": "$0/mo", "limit": "5 AI suggestions"},
    "indie": {"price": "$5/mo", "limit": "100 AI suggestions"},
    "pro": {"price": "$15/mo", "limit": "1,000 AI suggestions"},
    "team": {"price": "$50/mo", "limit": "5,000+ AI suggestions"},
}


def register() -> None:
    """Sign up for a Remind plan.

    Opens the Polar checkout page in your browser.
    After payment, you'll receive a license token via email.
    Use 'remind login <token>' to activate.

    Examples:
      remind register
    """
    try:
        config = load_config()
        backend_url = (config.ai_backend_url or "").rstrip("/")

        if not backend_url:
            output.error("Backend URL not configured")
            raise typer.Exit(1)

        output.header("REGISTER")
        output.blank()
        output.console.print("  Select a plan to open checkout in your browser:")
        output.blank()

        choices = list(PLANS.keys())
        for i, plan in enumerate(choices, 1):
            info = PLANS[plan]
            label = plan.upper().ljust(6)
            output.console.print(
                f"  [label]{i}[/label]  {label}  {info['price'].ljust(8)}  {info['limit']}"
            )

        output.blank()
        output.dot_rule()
        output.blank()

        choice = typer.prompt("Enter plan number (1-4)", type=int)

        if choice < 1 or choice > len(choices):
            output.error("Invalid choice")
            raise typer.Exit(1)

        plan = choices[choice - 1]
        checkout_url = f"{backend_url}/api/v1/checkout/{plan}"

        output.blank()
        with output.spinner(f"Opening {plan.capitalize()} checkout"):
            webbrowser.open(checkout_url)

        output.success(f"Opened {plan.capitalize()} checkout in your browser")
        output.blank()
        output.hint("After payment, check your email for a license token")
        output.hint("Then run: remind login <token>")
        output.blank()

    except typer.Exit:
        raise
    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
