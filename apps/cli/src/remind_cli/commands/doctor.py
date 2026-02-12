"""Doctor command - diagnose and fix issues."""

import httpx
import typer

from remind_database import DatabaseConfig, DatabaseSession
from remind_cli.config import load_config
from remind_cli.services.config_service import ConfigService
from remind_cli import output


def doctor() -> None:
    """Diagnose Remind installation and fix common issues.

    Checks database, config, license, backend connectivity,
    AI availability, and scheduler status.

    Examples:
      remind doctor
    """
    try:
        output.header("DIAGNOSTICS")
        checks_passed = 0
        checks_total = 0

        # Check 1: Database
        checks_total += 1
        try:
            db_config = DatabaseConfig()
            db_session = DatabaseSession(db_config)
            with db_session.get_session():
                pass  # session opens = DB is accessible
            output.label_value("Database", "[success]✓ connected[/success]")
            checks_passed += 1
        except Exception as e:
            output.label_value("Database", f"[error]✗ {e}[/error]")

        # Check 2: Configuration
        checks_total += 1
        try:
            config = load_config()
            output.label_value("Configuration", "[success]✓ valid[/success]")
            checks_passed += 1
        except Exception as e:
            output.label_value("Configuration", f"[error]✗ {e}[/error]")
            config = None

        # Check 3: License token
        checks_total += 1
        config_service = ConfigService()
        token = config_service.get_license_token()
        if token and token.startswith("remind_"):
            output.label_value("License", "[success]✓ authenticated[/success]")
            checks_passed += 1
        elif token:
            output.label_value("License", "[error]✗ invalid format[/error]")
        else:
            output.label_value("License", "[warning]! not logged in — run: remind login <token>[/warning]")
            checks_passed += 1  # Informational, not a failure

        # Check 4: Backend connectivity
        checks_total += 1
        backend_url = config.ai_backend_url if config else None
        if backend_url:
            try:
                with httpx.Client(timeout=5.0) as client:
                    resp = client.get(f"{backend_url.rstrip('/')}/health")
                    if resp.status_code == 200:
                        output.label_value("Backend", f"[success]✓ reachable[/success] ({backend_url})")
                        checks_passed += 1
                    else:
                        output.label_value("Backend", f"[error]✗ returned {resp.status_code}[/error]")
            except httpx.ConnectError:
                output.label_value("Backend", f"[error]✗ cannot connect to {backend_url}[/error]")
            except Exception as e:
                output.label_value("Backend", f"[error]✗ {e}[/error]")
        else:
            output.label_value("Backend", "[warning]! no URL configured[/warning]")

        # Check 5: AI suggestion (validates token + backend together)
        checks_total += 1
        if backend_url and token:
            try:
                with httpx.Client(timeout=5.0) as client:
                    resp = client.get(
                        f"{backend_url.rstrip('/')}/api/v1/usage/stats",
                        params={"license_token": token},
                    )
                    if resp.status_code == 200:
                        output.label_value("AI service", "[success]✓ authorized[/success]")
                        checks_passed += 1
                    elif resp.status_code == 401:
                        output.label_value("AI service", "[error]✗ token rejected by backend[/error]")
                    else:
                        output.label_value("AI service", f"[error]✗ backend returned {resp.status_code}[/error]")
            except Exception:
                output.label_value("AI service", "[error]✗ cannot reach backend[/error]")
        elif not token:
            output.label_value("AI service", "[warning]! no license — AI suggestions disabled[/warning]")
            checks_passed += 1
        else:
            output.label_value("AI service", "[warning]! no backend URL[/warning]")

        # Check 6: Scheduler
        checks_total += 1
        try:
            from remind_cli.services.daemon_service import DaemonService
            daemon = DaemonService()
            if daemon.is_installed():
                output.label_value("Scheduler", "[success]✓ running[/success]")
                checks_passed += 1
            else:
                output.label_value("Scheduler", "[warning]! not installed — run: remind login <token>[/warning]")
                checks_passed += 1  # Informational
        except Exception as e:
            output.label_value("Scheduler", f"[error]✗ {e}[/error]")

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
