"""
Configuration management for Manufactor.

Handles loading and saving user configuration from JSON files.
Provides default values and validation for required paths.
"""

import os
import json
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Manages application configuration stored in JSON format.

    Handles:
    - Loading configuration from JSON file
    - Providing default values for missing settings
    - Saving configuration changes
    - Validating configuration values
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to the config file. If None, uses default location.
        """
        if config_path is None:
            # Default config location: project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(project_root, "config.json")

        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.

        Returns:
            Dictionary with default configuration
        """
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        return {
            "paths": {
                "deck_path": os.path.join(os.path.dirname(project_root), "Decks"),
                "cockatrice_path": os.path.join(
                    os.path.expanduser("~"),
                    "Library",
                    "Application Support",
                    "Cockatrice",
                    "Cockatrice"
                )
            }
        }

    def _load_config(self):
        """Load configuration from JSON file or create with defaults."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self._config = json.load(f)

                # Merge with defaults to ensure all required keys exist
                defaults = self._get_default_config()
                self._merge_defaults(defaults)

            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
                print("Using default configuration.")
                self._config = self._get_default_config()
        else:
            # Create new config file with defaults
            self._config = self._get_default_config()
            self.save_config()

    def _merge_defaults(self, defaults: Dict[str, Any]):
        """
        Merge default values into config for any missing keys.

        Args:
            defaults: Default configuration dictionary
        """
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value
            elif isinstance(value, dict) and isinstance(self._config[key], dict):
                # Recursively merge nested dictionaries
                for subkey, subvalue in value.items():
                    if subkey not in self._config[key]:
                        self._config[key][subkey] = subvalue

    def save_config(self) -> bool:
        """
        Save current configuration to JSON file.

        Returns:
            True if save successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=4)
            return True
        except (IOError, OSError) as e:
            print(f"Error saving config to {self.config_path}: {e}")
            return False

    def get_deck_path(self) -> str:
        """
        Get the configured deck path.

        Returns:
            Path to the deck directory
        """
        return self._config.get("paths", {}).get("deck_path", "")

    def set_deck_path(self, path: str) -> bool:
        """
        Set the deck path and save configuration.

        Args:
            path: New deck path

        Returns:
            True if saved successfully
        """
        if "paths" not in self._config:
            self._config["paths"] = {}

        self._config["paths"]["deck_path"] = path
        return self.save_config()

    def get_cockatrice_path(self) -> str:
        """
        Get the configured Cockatrice path.

        Returns:
            Path to the Cockatrice directory
        """
        return self._config.get("paths", {}).get("cockatrice_path", "")

    def set_cockatrice_path(self, path: str) -> bool:
        """
        Set the Cockatrice path and save configuration.

        Args:
            path: New Cockatrice path

        Returns:
            True if saved successfully
        """
        if "paths" not in self._config:
            self._config["paths"] = {}

        self._config["paths"]["cockatrice_path"] = path
        return self.save_config()

    def get_config(self) -> Dict[str, Any]:
        """
        Get the entire configuration dictionary.

        Returns:
            Copy of configuration dictionary
        """
        return self._config.copy()

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration with new values.

        Args:
            updates: Dictionary of updates to apply

        Returns:
            True if saved successfully
        """
        self._config.update(updates)
        return self.save_config()

    def validate_paths(self) -> Dict[str, bool]:
        """
        Validate that configured paths exist.

        Returns:
            Dictionary mapping path names to existence status
        """
        return {
            "deck_path": os.path.isdir(self.get_deck_path()),
            "cockatrice_path": os.path.isdir(self.get_cockatrice_path())
        }

    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to default values.

        Returns:
            True if saved successfully
        """
        self._config = self._get_default_config()
        return self.save_config()


# Global config instance
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """
    Get the global configuration instance.

    Returns:
        Global ConfigManager instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
