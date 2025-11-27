"""
Card building service for MTG card creation.

Provides high-level API for creating and validating cards from form data.
Acts as a bridge between UI and core Card class.
"""

from typing import Dict, List, Optional, Any
from src.core.card import Card
from src.core.mana import Mana


class CardBuilder:
    """
    Service for building and validating cards from form inputs.

    Handles:
    - Card creation from UI form data
    - Card data validation
    - Frame suggestions based on card properties
    - Default value inference
    """

    def __init__(self):
        """Initialize the CardBuilder service."""
        pass

    def create_card_from_form_data(self, form_data: Dict[str, Any]) -> Card:
        """
        Create a Card instance from form data.

        Args:
            form_data: Dictionary containing card properties from UI form

        Returns:
            Initialized Card instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields
        validation_errors = self.validate_card_data(form_data)
        if validation_errors:
            raise ValueError("Invalid card data: " + ", ".join(validation_errors))

        # Extract and clean form data
        card_data = self._prepare_card_data(form_data)

        # Create and return Card instance
        return Card(**card_data)

    def validate_card_data(self, form_data: Dict[str, Any]) -> List[str]:
        """
        Validate card data from form inputs.

        Args:
            form_data: Dictionary containing card properties

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Required field: name
        if not form_data.get('name'):
            errors.append("Card name is required")

        # Required field: cardtype
        if not form_data.get('cardtype'):
            errors.append("Card type is required")

        # Validate mana cost format if provided
        mana = form_data.get('mana', '')
        if mana and not self._is_valid_mana_cost(mana):
            errors.append(f"Invalid mana cost format: {mana}")

        # Validate creature stats
        if self._is_creature_type(form_data.get('cardtype', '')):
            power = form_data.get('power')
            toughness = form_data.get('toughness')

            if power is None or power == '':
                errors.append("Creatures require power")
            if toughness is None or toughness == '':
                errors.append("Creatures require toughness")

        # Validate planeswalker loyalty
        if self._is_planeswalker_type(form_data.get('cardtype', '')):
            if not form_data.get('loyalty') and form_data.get('loyalty') != 0:
                errors.append("Planeswalkers require starting loyalty")

        return errors

    def get_suggested_frame(self, colors: List[str], cardtype: str,
                           legendary: bool = False) -> str:
        """
        Suggest an appropriate frame based on card properties.

        Args:
            colors: List of color identities
            cardtype: Card type string
            legendary: Whether the card is legendary

        Returns:
            Suggested frame filename pattern (without extension)
        """
        # Determine color
        if not colors:
            color = 'c'  # Colorless
        elif len(colors) == 1:
            color = colors[0].lower()
        elif len(colors) == 2:
            color = 'gld'  # Gold/multicolor
        else:
            color = 'gld'

        # Determine type
        cardtype_lower = cardtype.lower()
        if 'creature' in cardtype_lower:
            type_part = 'creature'
        elif 'artifact' in cardtype_lower:
            type_part = 'artifact'
        elif 'enchantment' in cardtype_lower:
            type_part = 'enchantment'
        elif 'planeswalker' in cardtype_lower:
            type_part = 'planeswalker'
        elif 'land' in cardtype_lower:
            type_part = 'land'
        else:
            type_part = 'spell'  # Default for instants/sorceries

        # Build frame name
        frame_parts = [color, type_part]

        # Add legendary suffix if applicable
        if legendary:
            frame_parts.append('legendary')

        return '_'.join(frame_parts)

    def infer_colors_from_mana(self, mana_cost: str) -> List[str]:
        """
        Infer color identity from mana cost.

        Args:
            mana_cost: Mana cost string (e.g., "{2}{U}{R}")

        Returns:
            List of color letters
        """
        try:
            return Mana.get_colors(mana_cost)
        except:
            return []

    def calculate_mana_value(self, mana_cost: str) -> int:
        """
        Calculate mana value (CMC) from mana cost.

        Args:
            mana_cost: Mana cost string (e.g., "{2}{U}{R}")

        Returns:
            Mana value as integer
        """
        try:
            return Mana.get_mana_value(mana_cost)
        except:
            return 0

    def get_default_card_data(self, cardtype: str) -> Dict[str, Any]:
        """
        Get default values for a card based on its type.

        Args:
            cardtype: Card type string

        Returns:
            Dictionary of default values
        """
        defaults = {
            'mana': '',
            'rulestext': '',
            'flavortext': '',
            'complete': False
        }

        # Type-specific defaults
        cardtype_lower = cardtype.lower()

        if 'creature' in cardtype_lower:
            defaults['power'] = '1'
            defaults['toughness'] = '1'

        if 'planeswalker' in cardtype_lower:
            defaults['loyalty'] = '3'

        if 'land' in cardtype_lower:
            defaults['mana'] = ''  # Lands typically have no mana cost

        return defaults

    def _prepare_card_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare and clean form data for Card constructor.

        Args:
            form_data: Raw form data

        Returns:
            Cleaned data ready for Card constructor
        """
        # Create a copy to avoid modifying input
        card_data = {}

        # Copy all fields, filtering out empty values
        for key, value in form_data.items():
            if value is not None and value != '':
                card_data[key] = value

        # Apply type-specific defaults if not provided
        if 'cardtype' in card_data:
            defaults = self.get_default_card_data(card_data['cardtype'])
            for key, default_value in defaults.items():
                if key not in card_data:
                    card_data[key] = default_value

        return card_data

    def _is_valid_mana_cost(self, mana: str) -> bool:
        """
        Check if mana cost string is valid format.

        Args:
            mana: Mana cost string

        Returns:
            True if valid, False otherwise
        """
        try:
            Mana.get_mana_value(mana)
            return True
        except:
            return False

    def _is_creature_type(self, cardtype: str) -> bool:
        """
        Check if card type includes Creature.

        Args:
            cardtype: Card type string

        Returns:
            True if creature, False otherwise
        """
        return 'creature' in cardtype.lower()

    def _is_planeswalker_type(self, cardtype: str) -> bool:
        """
        Check if card type includes Planeswalker.

        Args:
            cardtype: Card type string

        Returns:
            True if planeswalker, False otherwise
        """
        return 'planeswalker' in cardtype.lower()
