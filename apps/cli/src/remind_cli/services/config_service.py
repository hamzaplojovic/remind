"""Configuration management service."""

import json
from pathlib import Path
from typing import Any


class ConfigService:
    """Service for managing CLI configuration."""

    def __init__(self):
        """Initialize config service."""
        self.config_dir = Path.home() / ".remind"
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(exist_ok=True)

    def get_config_path(self) -> str:
        """Get path to config file."""
        return str(self.config_file)

    def load_config(self) -> dict:
        """Load configuration from file."""
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_config(self, config: dict) -> None:
        """Save configuration to file."""
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

    def get_license_token(self) -> str | None:
        """Get stored license token."""
        config = self.load_config()
        return config.get("license_token")

    def set_license_token(self, token: str) -> None:
        """Save license token."""
        config = self.load_config()
        config["license_token"] = token
        self.save_config(config)

    def clear_license_token(self) -> None:
        """Clear stored license token."""
        config = self.load_config()
        config.pop("license_token", None)
        self.save_config(config)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting."""
        config = self.load_config()
        return config.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a configuration setting."""
        config = self.load_config()
        config[key] = value
        self.save_config(config)
