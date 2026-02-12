"""Settings command - view and manage configuration."""

import typer

from remind_cli.config import load_config
from remind_cli.services.config_service import ConfigService
from remind_cli import output


def _get_plan_display(config_service: ConfigService) -> str:
    """Get plan tier from stored config, not token string."""
    plan_tier = config_service.get_setting("plan_tier")
    if plan_tier:
        return plan_tier.capitalize()
    token = config_service.get_license_token()
    if not token:
        return "Not logged in"
    # Legacy fallback
    for tier in ("team", "pro", "indie"):
        if tier in token:
            return tier.capitalize()
    return "Free"


def settings(
    view: bool = typer.Option(False, "--view", "-v", help="View all settings"),
    set_key: str | None = typer.Option(None, "--set", "-s", help="Set a key=value"),
) -> None:
    """View and manage Remind settings.

    Examples:
      remind settings
      remind settings --view
      remind settings --set notifications_enabled=false
    """
    try:
        config_service = ConfigService()

        if set_key:
            if "=" not in set_key:
                raise ValueError("Setting format must be key=value")

            key, value = set_key.split("=", 1)

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
            return

        # Show settings overview
        config = load_config()
        token = config_service.get_license_token()

        output.header("SETTINGS")

        # Account
        plan = _get_plan_display(config_service)
        output.label_value("Plan", plan)
        if token:
            masked = token[:12] + "..." + token[-4:]
            output.label_value("License", masked)
        else:
            output.label_value("License", "Not logged in")

        output.blank()
        output.dot_rule()
        output.blank()

        # AI
        ai_url = config.ai_backend_url or "Not configured"
        output.label_value("AI backend", ai_url)
        output.label_value("AI rephrasing", "Enabled" if config.ai_rephrasing_enabled else "Disabled")

        output.blank()
        output.dot_rule()
        output.blank()

        # Notifications
        output.label_value("Notifications", "Enabled" if config.notifications_enabled else "Disabled")
        output.label_value("Sound", "Enabled" if config.notification_sound_enabled else "Disabled")

        output.blank()
        output.dot_rule()
        output.blank()

        # Scheduler
        try:
            from remind_cli.services.daemon_service import DaemonService
            daemon = DaemonService()
            sched_status = "Running" if daemon.is_installed() else "Not installed"
        except Exception:
            sched_status = "Unknown"
        output.label_value("Scheduler", sched_status)

        # Paths
        output.label_value("Database", str(config_service.config_dir / "reminders.db"))
        output.label_value("Config", str(config_service.config_file))

        output.blank()

        if view:
            output.rule()
            output.blank()
            raw = config_service.load_config()
            output.print_json(raw)
            output.blank()

    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
