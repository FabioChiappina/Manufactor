"""
Deck management service for MTG card creation.

Provides high-level API for loading, managing, and analyzing decks.
Acts as a bridge between UI and core deck functionality.
"""

import os
from typing import Dict, List, Optional
from src.core.deck import Deck
from src.utils.paths import DECK_PATH


class DeckManager:
    """
    Service for managing MTG decks.

    Handles:
    - Deck loading from folders and JSON
    - Deck statistics and summaries
    - Deck directory management
    - Deck validation
    """

    def __init__(self):
        """Initialize the DeckManager service."""
        pass

    def load_deck_from_folder(self, deck_name: str) -> Deck:
        """
        Load a deck from its folder.

        Args:
            deck_name: Name of the deck to load

        Returns:
            Loaded Deck instance

        Raises:
            FileNotFoundError: If deck folder doesn't exist
        """
        deck_folder = self._normalize_deck_path(deck_name)

        if not os.path.isdir(deck_folder):
            raise FileNotFoundError(f"Deck folder not found: {deck_folder}")

        # Ensure required subdirectories exist
        self._ensure_deck_structure(deck_folder)

        return Deck.from_deck_folder(deck_folder)

    def load_deck_from_json(
        self,
        json_path: str,
        setname: str,
        deck_name: str
    ) -> Deck:
        """
        Load a deck from a JSON file.

        Args:
            json_path: Path to the JSON file
            setname: Set name for the deck
            deck_name: Name for the deck

        Returns:
            Loaded Deck instance

        Raises:
            FileNotFoundError: If JSON file doesn't exist
        """
        if not os.path.isfile(json_path):
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        return Deck.from_json(json_path, setname, deck_name)

    def get_deck_statistics(self, deck: Deck) -> Dict[str, any]:
        """
        Get comprehensive statistics for a deck.

        Args:
            deck: The deck to analyze

        Returns:
            Dictionary containing deck statistics
        """
        if not isinstance(deck, Deck):
            raise TypeError("Input must be of type Deck.")

        return {
            'name': deck.name,
            'total_cards': len(deck.cards),
            'total_lands': len([c for c in deck.cards if c.is_land()]),
            'total_spells': len([c for c in deck.cards if not c.is_land()]),
            'creatures': len([c for c in deck.cards if c.is_creature()]),
            'artifacts': len([c for c in deck.cards if c.is_artifact()]),
            'enchantments': len([c for c in deck.cards if c.is_enchantment()]),
            'instants': len([c for c in deck.cards if c.is_instant()]),
            'sorceries': len([c for c in deck.cards if c.is_sorcery()]),
            'planeswalkers': len([c for c in deck.cards if c.is_planeswalker()]),
            'colors': deck.colors,
            'average_mana_value': deck.get_average_mana_value(),
            'mana_curve': self._get_mana_curve(deck),
            'color_distribution': self._get_color_distribution(deck)
        }

    def print_deck_summaries(self, deck: Deck):
        """
        Print all deck summaries to console.

        Args:
            deck: The deck to print summaries for
        """
        if not isinstance(deck, Deck):
            raise TypeError("Input must be of type Deck.")

        deck.print_color_summary()
        deck.print_mana_summary()
        deck.print_type_summary()
        deck.print_tag_summary()

    def list_available_decks(self) -> List[str]:
        """
        List all available deck folders.

        Returns:
            List of deck names
        """
        if not os.path.isdir(DECK_PATH):
            return []

        decks = []
        for item in os.listdir(DECK_PATH):
            item_path = os.path.join(DECK_PATH, item)
            if os.path.isdir(item_path):
                # Check if it looks like a deck folder
                if os.path.isfile(os.path.join(item_path, item + '.json')):
                    decks.append(item)

        return sorted(decks)

    def create_deck_folder(self, deck_name: str) -> str:
        """
        Create a new deck folder with proper structure.

        Args:
            deck_name: Name for the new deck

        Returns:
            Path to the created deck folder
        """
        deck_folder = self._normalize_deck_path(deck_name)
        self._ensure_deck_structure(deck_folder)
        return deck_folder

    def _normalize_deck_path(self, deck_name: str) -> str:
        """
        Normalize deck name to proper path with capitalization.

        Args:
            deck_name: Raw deck name

        Returns:
            Normalized path to deck folder
        """
        # Capitalize each word
        normalized_name = ' '.join(
            word[0].upper() + word[1:] for word in deck_name.split()
        )
        return os.path.join(DECK_PATH, normalized_name)

    def _ensure_deck_structure(self, deck_folder: str):
        """
        Ensure deck folder has all required subdirectories.

        Args:
            deck_folder: Path to deck folder
        """
        required_dirs = ["Cards", "Artwork", "Printing", "Tokens"]

        for directory in required_dirs:
            dir_path = os.path.join(deck_folder, directory)
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path, exist_ok=True)

    def _get_mana_curve(self, deck: Deck) -> Dict[int, int]:
        """Get mana value distribution."""
        curve = {}
        for card in deck.cards:
            if not card.is_land():
                mv = card.get_mana_value()
                curve[mv] = curve.get(mv, 0) + 1
        return curve

    def _get_color_distribution(self, deck: Deck) -> Dict[str, float]:
        """Get color distribution percentages."""
        if not deck.colors:
            return {}

        color_counts = {color: 0 for color in deck.colors}
        total_colored_spells = 0

        for card in deck.cards:
            if not card.is_land() and card.colors:
                total_colored_spells += 1
                for color in card.colors:
                    if color in color_counts:
                        color_counts[color] += 1

        if total_colored_spells == 0:
            return {}

        return {
            color: (count / total_colored_spells) * 100
            for color, count in color_counts.items()
        }
