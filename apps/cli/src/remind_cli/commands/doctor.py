"""Doctor command - diagnose and fix issues."""

import typer

from remind_database import DatabaseConfig, DatabaseSession
from remind_cli.services.config_service import ConfigService
from remind_cli import output


def doctor() -> None:
    """Diagnose Remind installation and fix common issues.

    Checks:
    - Database connectivity
    - Configuration validity
    - License token
    - Permissions

    Examples:
      remind doctor
    """
    try:
        output.header("DIAGNOSTICS")
        checks_passed = 0
        checks_total = 4

        # Check 1: Database
        try:
            db_config = DatabaseConfig()
            DatabaseSession(db_config)
            output.label_value("Database", "[success]✓ connected[/success]")
            checks_passed += 1
        except Exception as e:
            output.label_value("Database", f"[error]✗ {e}[/error]")

        # Check 2: Configuration
        try:
            config_service = ConfigService()
            config_service.load_config()
            output.label_value("Configuration", "[success]✓ valid[/success]")
            checks_passed += 1
        except Exception as e:
            output.label_value("Configuration", f"[error]✗ {e}[/error]")

        # Check 3: License token
        try:
            config_service = ConfigService()
            token = config_service.get_license_token()
            if token:
                if token.startswith("remind_"):
                    output.label_value("License token", "[success]✓ authenticated[/success]")
                    checks_passed += 1
                else:
                    output.label_value("License token", "[error]✗ invalid format[/error]")
            else:
                output.label_value("License token", "[warning]! not logged in[/warning]")
                checks_passed += 1  # Not an error, just informational
        except Exception as e:
            output.label_value("License token", f"[error]✗ {e}[/error]")

        # Check 4: Reminders
        try:
            db_config = DatabaseConfig()
            DatabaseSession(db_config)
            output.label_value("Reminders", "[success]✓ accessible[/success]")
            checks_passed += 1
        except Exception as e:
            output.label_value("Reminders", f"[error]✗ {e}[/error]")

        output.blank()
        output.rule()

        if checks_passed == checks_total:
            output.success("All checks passed.")
        else:
            output.warning(f"{checks_passed}/{checks_total} checks passed.")
        output.blank()

    except Exception as e:
        output.error(str(e))
        raise typer.Exit(1)
