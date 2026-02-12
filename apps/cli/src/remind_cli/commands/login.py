"""Login command - authenticate with license token."""

import typer

from remind_shared import AuthenticationError
from remind_cli.services.config_service import ConfigService
from remind_cli import output


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

        # Determine plan tier from token
        if "pro" in token:
            plan_tier = "Pro"
        elif "enterprise" in token:
            plan_tier = "Enterprise"
        else:
            plan_tier = "Free"

        output.blank()
        output.success("Logged in successfully")
        output.label_value("Plan", plan_tier)
        output.label_value("Token stored", str(config_service.get_config_path()))
        output.blank()

    except AuthenticationError as e:
        output.error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
