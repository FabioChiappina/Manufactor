"""
Path definitions for Manufactor.

Provides centralized path management for the application.
User-configurable paths (deck and Cockatrice) are loaded from config.json.
"""

import os
from src.utils.config import get_config

# Get the project root directory (two levels up from this file)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Static asset paths (relative to project structure)
ASSETS_PATH = os.path.join(PROJECT_ROOT, "Assets")
CARD_BORDERS_PATH = os.path.join(ASSETS_PATH, "CardBorders")
SYMBOL_PATH = os.path.join(ASSETS_PATH, "Symbols")
SET_SYMBOL_PATH = os.path.join(ASSETS_PATH, "SetSymbols")
SAGA_SYMBOL_PATH = os.path.join(ASSETS_PATH, "SagaSymbols")
MDFC_INDICATOR_PATH = os.path.join(ASSETS_PATH, "MDFC")
FONT_PATHS = {
    "name":   os.path.join(ASSETS_PATH, "Fonts", "Beleren-Bold.ttf"),
    "token":  os.path.join(ASSETS_PATH, "Fonts", "Beleren-Small-Caps.ttf"),
    "type":   os.path.join(ASSETS_PATH, "Fonts", "Beleren-Bold.ttf"),
    "rules":  os.path.join(ASSETS_PATH, "Fonts", "MPlantin.ttf"),
    "flavor": os.path.join(ASSETS_PATH, "Fonts", "MPlantin-Italic.ttf")
}

# Load configuration
_config = get_config()

# User-configurable paths (loaded from config.json)
DECK_PATH = _config.get_deck_path()
COCKATRICE_PATH = _config.get_cockatrice_path()

# Derived Cockatrice paths
COCKATRICE_MANUFACTOR_PATH = os.path.join(COCKATRICE_PATH, "manufactor")
COCKATRICE_IMAGE_PATH = os.path.join(COCKATRICE_PATH, "pics", "CUSTOM")
COCKATRICE_CUSTOMSETS_PATH = os.path.join(COCKATRICE_PATH, "customsets")
COCKATRICE_DECKS_PATH = os.path.join(COCKATRICE_PATH, "decks")