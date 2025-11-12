"""
Cockatrice export service for MTG decks.

Provides high-level API for exporting decks to Cockatrice format with validation.
Acts as a bridge between UI and Cockatrice integration.
"""

import os
from typing import Dict, List, Optional
from src.core.deck import Deck
from src.integration.cockatrice import update_cockatrice
from src.utils.paths import COCKATRICE_PATH, COCKATRICE_MANUFACTOR_PATH, COCKATRICE_IMAGE_PATH, COCKATRICE_CUSTOMSETS_PATH, COCKATRICE_DECKS_PATH


class CockatriceExporter:
    """
    Service for exporting decks to Cockatrice.

    Handles:
    - Deck export to Cockatrice format
    - Path validation
    - Export options management
    - Error reporting
    """

    def __init__(self):
        """Initialize the CockatriceExporter service."""
        pass

    def export_deck(
        self,
        deck: Deck,
        xml_filepath: Optional[str] = None,
        json_filepath: Optional[str] = None,
        xml_filepath_tokens: Optional[str] = None,
        json_filepath_tokens: Optional[str] = None,
        replace_existing_custom_set: bool = True,
        replace_deck_files: bool = True
    ) -> bool:
        """
        Export a deck to Cockatrice format.

        Args:
            deck: The deck to export
            xml_filepath: Optional custom XML file path
            json_filepath: Optional custom JSON file path
            xml_filepath_tokens: Optional custom tokens XML path
            json_filepath_tokens: Optional custom tokens JSON path
            replace_existing_custom_set: Replace existing custom set files
            replace_deck_files: Replace existing deck .cod files

        Returns:
            True if export successful

        Raises:
            TypeError: If deck is not a Deck instance
            RuntimeError: If Cockatrice paths are invalid
        """
        if not isinstance(deck, Deck):
            raise TypeError("Input deck must be of type Deck.")

        # Validate paths before export
        validation_errors = self.validate_export_paths()
        if validation_errors:
            error_msg = "Cockatrice export validation failed:\n" + "\n".join(validation_errors)
            raise RuntimeError(error_msg)

        try:
            update_cockatrice(
                deck,
                xml_filepath=xml_filepath,
                json_filepath=json_filepath,
                xml_filepath_tokens=xml_filepath_tokens,
                json_filepath_tokens=json_filepath_tokens,
                replace_existing_custom_set=replace_existing_custom_set,
                replace_deck_files=replace_deck_files
            )
            return True
        except Exception as e:
            print(f"Error exporting to Cockatrice: {e}")
            return False

    def validate_export_paths(self) -> List[str]:
        """
        Validate that all required Cockatrice paths exist.

        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []

        # Check main Cockatrice path
        if not os.path.isdir(COCKATRICE_PATH):
            errors.append(f"Cockatrice directory not found: {COCKATRICE_PATH}")

        # Check required subdirectories
        required_paths = {
            'Image path': COCKATRICE_IMAGE_PATH,
            'Custom sets path': COCKATRICE_CUSTOMSETS_PATH,
            'Decks path': COCKATRICE_DECKS_PATH
        }

        for name, path in required_paths.items():
            if not os.path.isdir(path):
                errors.append(f"{name} not found: {path}")

        return errors

    def get_export_info(self, deck: Deck) -> Dict[str, any]:
        """
        Get information about what will be exported.

        Args:
            deck: The deck to get export info for

        Returns:
            Dictionary with export information
        """
        if not isinstance(deck, Deck):
            raise TypeError("Input deck must be of type Deck.")

        return {
            'deck_name': deck.name,
            'total_cards': len(deck.cards),
            'validation_errors': self.validate_export_paths(),
            'export_paths': {
                'manufactor_path': COCKATRICE_MANUFACTOR_PATH,
                'image_path': COCKATRICE_IMAGE_PATH,
                'customsets_path': COCKATRICE_CUSTOMSETS_PATH,
                'decks_path': COCKATRICE_DECKS_PATH
            }
        }

    def is_cockatrice_available(self) -> bool:
        """
        Check if Cockatrice is properly configured.

        Returns:
            True if Cockatrice paths are valid
        """
        return len(self.validate_export_paths()) == 0

    def get_cockatrice_deck_path(self, deck_name: str) -> str:
        """
        Get the path where a deck's .cod file will be saved.

        Args:
            deck_name: Name of the deck

        Returns:
            Path to the deck's .cod file
        """
        return os.path.join(COCKATRICE_DECKS_PATH, f"{deck_name}.cod")
