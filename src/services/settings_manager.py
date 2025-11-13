"""
Settings management service for Manufactor.

Provides high-level API for managing application settings.
Acts as a bridge between UI and configuration system.
"""

import os
from typing import Dict, List, Optional
from src.utils.config import get_config


class SettingsManager:
    """
    Service for managing application settings.

    Handles:
    - Path configuration and validation
    - Settings persistence
    - Settings retrieval
    - Path validation
    """

    def __init__(self):
        """Initialize the SettingsManager service."""
        self.config = get_config()

    def get_deck_path(self) -> str:
        """
        Get the current deck path.

        Returns:
            Current deck path
        """
        return self.config.get_deck_path()

    def set_deck_path(self, path: str) -> bool:
        """
        Set a new deck path.

        Args:
            path: New deck path

        Returns:
            True if saved successfully

        Raises:
            ValueError: If path is empty
        """
        if not path or not path.strip():
            raise ValueError("Deck path cannot be empty")

        # Expand user home directory if present
        path = os.path.expanduser(path)

        # Save the configuration
        success = self.config.set_deck_path(path)

        # If successful, reload the paths module to update global variables
        if success:
            self._reload_paths_module()

        return success

    def get_cockatrice_path(self) -> str:
        """
        Get the current Cockatrice path.

        Returns:
            Current Cockatrice path
        """
        return self.config.get_cockatrice_path()

    def set_cockatrice_path(self, path: str) -> bool:
        """
        Set a new Cockatrice path.

        Args:
            path: New Cockatrice path

        Returns:
            True if saved successfully

        Raises:
            ValueError: If path is empty
        """
        if not path or not path.strip():
            raise ValueError("Cockatrice path cannot be empty")

        # Expand user home directory if present
        path = os.path.expanduser(path)

        # Save the configuration
        success = self.config.set_cockatrice_path(path)

        # If successful, reload the paths module to update global variables
        if success:
            self._reload_paths_module()

        return success

    def validate_paths(self) -> Dict[str, Dict[str, any]]:
        """
        Validate all configured paths.

        Returns:
            Dictionary with validation results for each path:
            {
                'deck_path': {'path': str, 'exists': bool, 'writable': bool},
                'cockatrice_path': {'path': str, 'exists': bool, 'writable': bool}
            }
        """
        deck_path = self.get_deck_path()
        cockatrice_path = self.get_cockatrice_path()

        return {
            'deck_path': {
                'path': deck_path,
                'exists': os.path.isdir(deck_path),
                'writable': os.access(deck_path, os.W_OK) if os.path.exists(deck_path) else False
            },
            'cockatrice_path': {
                'path': cockatrice_path,
                'exists': os.path.isdir(cockatrice_path),
                'writable': os.access(cockatrice_path, os.W_OK) if os.path.exists(cockatrice_path) else False
            }
        }

    def get_validation_errors(self) -> List[str]:
        """
        Get a list of validation errors for configured paths.

        Returns:
            List of error messages (empty if all valid)
        """
        errors = []
        validation = self.validate_paths()

        for path_name, info in validation.items():
            path = info['path']
            if not path:
                errors.append(f"{path_name.replace('_', ' ').title()} is not configured")
            elif not info['exists']:
                errors.append(f"{path_name.replace('_', ' ').title()} does not exist: {path}")
            elif not info['writable']:
                errors.append(f"{path_name.replace('_', ' ').title()} is not writable: {path}")

        return errors

    def create_missing_directories(self) -> Dict[str, bool]:
        """
        Attempt to create any missing configured directories.

        Returns:
            Dictionary mapping path names to creation success status
        """
        results = {}
        validation = self.validate_paths()

        for path_name, info in validation.items():
            if not info['exists'] and info['path']:
                try:
                    os.makedirs(info['path'], exist_ok=True)
                    results[path_name] = True
                except (OSError, PermissionError) as e:
                    print(f"Error creating {path_name}: {e}")
                    results[path_name] = False
            else:
                results[path_name] = info['exists']

        return results

    def reset_to_defaults(self) -> bool:
        """
        Reset all settings to default values.

        Returns:
            True if reset successful
        """
        success = self.config.reset_to_defaults()

        if success:
            self._reload_paths_module()

        return success

    def get_all_settings(self) -> Dict[str, any]:
        """
        Get all current settings.

        Returns:
            Dictionary with all settings
        """
        return self.config.get_config()

    def _reload_paths_module(self):
        """
        Reload the paths module to update global path variables.

        This ensures that changes to configuration are immediately
        reflected in the paths module without requiring application restart.
        """
        import importlib
        import src.utils.paths
        importlib.reload(src.utils.paths)
