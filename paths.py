import os

ASSETS_PATH = os.path.join(".", "Assets")
CARD_BORDERS_PATH = os.path.join(ASSETS_PATH, "CardBorders")
SYMBOL_PATH = os.path.join(ASSETS_PATH, "Symbols")
SET_SYMBOL_PATH = os.path.join(ASSETS_PATH, "SetSymbols")
SAGA_SYMBOL_PATH = os.path.join(ASSETS_PATH, "SagaSymbols")
MDFC_INDICATOR_PATH = os.path.join(ASSETS_PATH, "MDFC")
FONT_PATHS = {"name":   os.path.join(ASSETS_PATH, "Fonts", "Beleren-Bold.ttf"),
              "token":  os.path.join(ASSETS_PATH, "Fonts", "Beleren-Small-Caps.ttf"),
              "type":   os.path.join(ASSETS_PATH, "Fonts", "Beleren-Bold.ttf"),
              "rules":  os.path.join(ASSETS_PATH, "Fonts", "MPlantin.ttf"),
              "flavor": os.path.join(ASSETS_PATH, "Fonts", "MPlantin-Italic.ttf")}

DECK_PATH = os.path.join("..", "Decks")

COCKATRICE_PATH = os.path.join("/", "Users", "fabiochiappina", "Library", "Application Support", "Cockatrice", "Cockatrice")
COCKATRICE_MANUFACTOR_PATH = os.path.join(COCKATRICE_PATH, "manufactor")
COCKATRICE_IMAGE_PATH = os.path.join(COCKATRICE_PATH, "pics", "CUSTOM")
COCKATRICE_CUSTOMSETS_PATH = os.path.join(COCKATRICE_PATH, "customsets")
COCKATRICE_DECKS_PATH = os.path.join(COCKATRICE_PATH, "decks")