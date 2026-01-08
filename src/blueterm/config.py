"""Configuration management for blueterm"""
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any

# TOML library imports (Python 3.11+ has tomllib built-in)
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore

try:
    import tomli_w
except ImportError:
    tomli_w = None  # type: ignore

from .api.exceptions import ConfigurationError


@dataclass
class Config:
    """Application configuration loaded from environment variables"""
    api_key: str
    default_region: str = "us-south"
    refresh_interval: int = 30  # seconds
    debug: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        """
        Load configuration from environment variables

        Environment Variables:
            IBMCLOUD_API_KEY: IBM Cloud API key (required)
            BLUETERM_DEFAULT_REGION: Default region on startup (optional, default: us-south)
            BLUETERM_REFRESH_INTERVAL: Auto-refresh interval in seconds (optional, default: 30)
            BLUETERM_DEBUG: Enable debug mode (optional, default: false)

        Returns:
            Config object

        Raises:
            ConfigurationError: If required environment variables are missing or invalid
        """
        api_key = os.environ.get("IBMCLOUD_API_KEY")
        if not api_key:
            raise ConfigurationError(
                "IBMCLOUD_API_KEY environment variable is required.\n"
                "Get your API key from: https://cloud.ibm.com/iam/apikeys\n"
                "Set it with: export IBMCLOUD_API_KEY=your-api-key-here"
            )

        # Parse optional configuration
        default_region = os.environ.get("BLUETERM_DEFAULT_REGION", "us-south")

        refresh_interval_str = os.environ.get("BLUETERM_REFRESH_INTERVAL", "30")
        try:
            refresh_interval = int(refresh_interval_str)
            if refresh_interval < 10:
                raise ValueError("Refresh interval must be at least 10 seconds")
        except ValueError as e:
            raise ConfigurationError(f"Invalid BLUETERM_REFRESH_INTERVAL: {e}")

        debug_str = os.environ.get("BLUETERM_DEBUG", "false").lower()
        debug = debug_str in ("1", "true", "yes", "on")

        return cls(
            api_key=api_key,
            default_region=default_region,
            refresh_interval=refresh_interval,
            debug=debug
        )

    def validate(self) -> None:
        """
        Validate configuration values

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.api_key or len(self.api_key) < 20:
            raise ConfigurationError("API key appears to be invalid (too short)")

        if self.refresh_interval < 10:
            raise ConfigurationError("Refresh interval must be at least 10 seconds")

    def __repr__(self) -> str:
        """Safe representation that doesn't expose API key"""
        masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "****"
        return (
            f"Config(api_key='{masked_key}', default_region='{self.default_region}', "
            f"refresh_interval={self.refresh_interval}, debug={self.debug})"
        )


@dataclass
class UserPreferences:
    """User preferences persisted to disk"""
    theme: str = "textual-dark"
    auto_refresh_enabled: bool = True
    last_region: Optional[str] = None

    _config_dir: Path = Path.home() / ".blueterm"
    _config_file: Path = _config_dir / "config.toml"

    @classmethod
    def load(cls) -> "UserPreferences":
        """
        Load user preferences from config file

        Returns:
            UserPreferences object (uses defaults if file doesn't exist)
        """
        prefs = cls()

        if not prefs._config_file.exists():
            return prefs

        if tomllib is None:
            # Can't read TOML, return defaults
            return prefs

        try:
            with open(prefs._config_file, "rb") as f:
                data = tomllib.load(f)
                prefs.theme = data.get("theme", prefs.theme)
                prefs.auto_refresh_enabled = data.get("auto_refresh_enabled", prefs.auto_refresh_enabled)
                prefs.last_region = data.get("last_region", prefs.last_region)
        except Exception:
            # If we can't load preferences, just use defaults
            pass

        return prefs

    def save(self) -> None:
        """
        Save user preferences to config file

        Creates ~/.blueterm/config.toml if it doesn't exist
        """
        if tomli_w is None:
            # Can't write TOML, skip saving
            return

        # Create config directory if it doesn't exist
        self._config_dir.mkdir(parents=True, exist_ok=True)

        # Prepare data to save (exclude private attributes)
        data: Dict[str, Any] = {
            "theme": self.theme,
            "auto_refresh_enabled": self.auto_refresh_enabled,
        }
        if self.last_region:
            data["last_region"] = self.last_region

        try:
            with open(self._config_file, "wb") as f:
                tomli_w.dump(data, f)
        except Exception:
            # If we can't save, it's not critical - just skip
            pass

    def update_theme(self, theme: str) -> None:
        """Update theme preference and save"""
        self.theme = theme
        self.save()

    def update_last_region(self, region: str) -> None:
        """Update last selected region and save"""
        self.last_region = region
        self.save()

    def toggle_auto_refresh(self) -> bool:
        """Toggle auto-refresh and save, returns new state"""
        self.auto_refresh_enabled = not self.auto_refresh_enabled
        self.save()
        return self.auto_refresh_enabled
