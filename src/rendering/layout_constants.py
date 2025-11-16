"""
Card layout constants for positioning and sizing elements.

All position and size constants used for rendering MTG card images.
Positions are (x, y) tuples in pixels, sizes are in pixels.
"""

# Position constants - where elements are placed on the card
POSITION_CARD_NAME = (66, 77)
POSITION_CARD_TYPE = (66, 609)
POSITION_TOKEN_CARD_TYPE = (66, POSITION_CARD_TYPE[1] + 115)
POSITION_SAGA_CARD_TYPE = (66, POSITION_CARD_TYPE[1] + 295)
POSITION_RULES_TEXT = (70, 649)
POSITION_TOKEN_RULES_TEXT = (70, POSITION_RULES_TEXT[1] + 110)
POSITION_SAGA_RULES_TEXT = (97, 306)
POSITION_SUBSPELL_MAIN_RULES_TEXT = (388, 648)  # Main card rules text for subspell cards (shifted right)

# Default subspell positions (Omen, Dream, and other non-Adventure subspells)
POSITION_SUBSPELL_NAME = (63, 657)  # Subspell name position
POSITION_SUBSPELL_TYPE = (63, 707)  # Subspell type line position
POSITION_SUBSPELL_RULES_TEXT = (63, 740)  # Subspell rules text position
POSITION_SUBSPELL_MANA_SYMBOL = (324, 662)  # Subspell mana symbols position

# Adventure-specific positions (slightly different from default)
POSITION_ADVENTURE_NAME = (63, 659)  # Adventure name position (2 pixels down from default)
POSITION_ADVENTURE_TYPE = (63, 707)  # Adventure type line position (same as default)
POSITION_ADVENTURE_RULES_TEXT = (63, 740)  # Adventure rules text position (same as default)
POSITION_ADVENTURE_MANA_SYMBOL = (324, 660)  # Adventure mana symbols position (2 pixels up from default)
POSITION_SET_SYMBOL = (634, 593)
POSITION_TOKEN_SET_SYMBOL = (634, POSITION_SET_SYMBOL[1] + 115)
POSITION_SAGA_SET_SYMBOL = (634, POSITION_SET_SYMBOL[1] + 295)
POSITION_POWER = (610, 947)
POSITION_TOUGHNESS = (651, 947)
POSITION_MANA_SYMBOL = (648, 61)
POSITION_FLAVOR_LINE = (82, None)
POSITION_SAGA_LINE = (84, None)
POSITION_SAGA_NUM_CHAPTERS = (250, 232)
POSITION_SAGA_CHAPTER_SYMBOLS = (31, None)

# Maximum height/width constraints for text and elements
MAX_HEIGHT_CARD_NAME = 44.5
MAX_HEIGHT_CARD_TYPE = 37.5
MAX_FONT_SIZE_RULES_TEXT_LETTERS = 37
MAX_HEIGHT_RULES_TEXT_BOX = 280
MAX_HEIGHT_TOKEN_RULES_TEXT_BOX = 165
MAX_HEIGHT_SAGA_RULES_TEXT_BOX = 537
MAX_WIDTH_RULES_TEXT_BOX = 596
MAX_WIDTH_SAGA_RULES_TEXT_BOX = 255
MAX_WIDTH_SUBSPELL_MAIN_RULES_TEXT_BOX = 290  # Half width for main card rules on subspell cards
MAX_WIDTH_SUBSPELL_NAME = 287  # Width for subspell name
MAX_WIDTH_SUBSPELL_TYPE = 290  # Width for subspell type line
MAX_WIDTH_SUBSPELL_RULES_TEXT_BOX = 290  # Width for subspell rules text
MAX_HEIGHT_SUBSPELL_NAME = 37.5  # Height for subspell name (default, same as type)
MAX_HEIGHT_SUBSPELL_TYPE = 37.5  # Height for subspell type
MAX_HEIGHT_SUBSPELL_RULES_TEXT_BOX = 193  # Height for subspell rules text
MAX_HEIGHT_ADVENTURE_NAME = 40  # Height for Adventure name (slightly taller)
MAX_WIDTH_CARD_NAME = 575
MAX_WIDTH_CARD_TYPE = 567
MAX_HEIGHT_POWER_TOUGHNESS = 39

# Card dimensions
CARD_WIDTH = 744
CARD_HEIGHT = 1039

# Symbol sizes
SET_SYMBOL_SIZE = 40
MANA_SYMBOL_SIZE = 37
SUBSPELL_MANA_SYMBOL_SIZE = 30  # Mana symbols for default subspells (Omen, Dream, etc.)
ADVENTURE_MANA_SYMBOL_SIZE = 31  # Mana symbols for adventure subspells (1 larger)
SPECIAL_SYMBOL_SIZE = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
