"""
External software integration.

Handles exporting cards and decks to external platforms:
- Cockatrice: XML generation and deck file creation
- Future: Support for other platforms (Tabletop Simulator, etc.)
"""

from src.integration.cockatrice import update_cockatrice

__all__ = ['update_cockatrice']
