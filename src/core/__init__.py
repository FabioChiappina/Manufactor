"""
Core game logic and data models for Magic: The Gathering cards.

This module contains the fundamental data structures representing MTG concepts:
- Mana: Mana cost parsing and color management
- Card: Individual card representation
- Deck: Collection of cards with statistics
- Ability: Keyword abilities and mechanics
- CardSet: Set information and management
"""

from src.core.mana import Mana
from src.core.card_set import CardSet
from src.core.ability import Ability, AbilityElements
from src.core.card import Card
from src.core.deck import Deck

__all__ = ['Mana', 'CardSet', 'Ability', 'AbilityElements', 'Card', 'Deck']
