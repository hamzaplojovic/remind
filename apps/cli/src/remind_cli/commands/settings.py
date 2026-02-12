"""Settings command - view and manage configuration."""

import typer

from remind_cli.services.config_service import ConfigService
from remind_cli import output


def settings(
    view: bool = typer.Option(False, "--view", "-v", help="View all settings"),
    set_key: str | None = typer.Option(None, "--set", "-s", help="Set a key=value"),
) -> None:
    """View and manage Remind settings.

    Examples:
      remind settings --view
      remind settings --set debug=true
      remind settings --set ai_enabled=false
    """
    try:
        config_service = ConfigService()

        if view:
            config = config_service.load_config()
            if not config:
                output.info("No settings configured.")
                return
            output.print_json(config)

        elif set_key:
            if "=" not in set_key:
                raise ValueError("Setting format must be key=value")

            key, value = set_key.split("=", 1)

            # Parse value
            if value.lower() in ("true", "false"):
                parsed_value = value.lower() == "true"
            elif value.isdigit():
                parsed_value = int(value)
            else:
                parsed_value = value

            config_service.set_setting(key.strip(), parsed_value)
            output.blank()
            output.success(f"Set {key.strip()} = {parsed_value}")
            output.blank()

        else:
            token = config_service.get_license_token()
            output.blank()
            if token:
                if "pro" in token:
                    tier = "Pro"
                elif "enterprise" in token:
                    tier = "Enterprise"
                else:
                    tier = "Free"
                output.label_value("Plan", tier)
            else:
                output.label_value("Plan", "Not logged in")

            output.label_value("Config", str(config_service.get_config_path()))
            output.blank()
            output.hint("Use --view to see all settings")
            output.blank()

    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
