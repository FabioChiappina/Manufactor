# Manufactor Code Examples

## Loading and Using Cards

### Load a Deck from Folder
```python
from src.core.deck import Deck

# Load deck from folder
deck = Deck.from_deck_folder("Test")

# Access cards
for card in deck.cards:
    print(f"{card.name}: {card.get_type_line()}")
```

### Load a Deck from JSON
```python
from src.core.deck import Deck

# Load directly from JSON (auto-detects old vs new format)
deck = Deck.from_json(
    "Decks/Test/Test.json",
    setname="TST",
    deck_name="Test Deck"
)

# Access new metadata fields (if loaded from new format)
print(f"Deck: {deck.name}")
print(f"Format: {deck.format}")
print(f"Description: {deck.description}")
print(f"Author: {deck.author}")
print(f"Commander: {deck.commander}")
```

### Create Cards Programmatically
```python
from src.core.card import Card

# Simple card
card = Card(
    name="Lightning Bolt",
    mana="{r}",
    cardtype="Instant",
    rarity="Uncommon",
    rules="Lightning Bolt deals 3 damage to any target.",
    quantity=4  # NEW: specify number of copies
)

# Complex card with all properties
card = Card(
    name="Sheoldred, the Apocalypse",
    mana="{2}{b}{b}",
    cardtype="Creature",
    subtype="Phyrexian Praetor",
    power="4",
    toughness="5",
    rarity="Mythic",
    rules="Deathtouch\nWhenever you draw a card, you gain 2 life.\nWhenever an opponent draws a card, they lose 2 life.",
    flavor="\"Gix failed. I shall not.\"",
    colors=["b"],
    tags=["LifeDrain"],
    legendary=1,
    quantity=1
)
```

### Export Deck to New JSON Format
```python
from src.core.deck import Deck
from datetime import datetime

# Load existing deck
deck = Deck.from_deck_folder("MyDeck")

# Set metadata fields
deck.description = "Fast aggressive red deck"
deck.format = "Modern"
deck.author = "PlayerName"
deck.commander = None  # or card name for Commander format
deck.setname = "MRD"  # Default set code for all cards in deck

# Export to new format
deck.to_json(
    filepath="Decks/MyDeck/MyDeck.json",
    use_new_format=True
)

# Or export to old format for backward compatibility
deck.to_json(
    filepath="Decks/MyDeck/MyDeck_old.json",
    use_new_format=False
)
```

### Working with Deck Tokens
```python
from src.core.deck import Deck

# Load deck
deck = Deck.from_deck_folder("MyDeck")

# Generate tokens and populate deck.tokens with source tracking
specialized_tokens, common_tokens = deck.get_tokens(
    save_to_deck=True,          # Populate self.tokens (new format)
    save_legacy_file=False       # Don't create separate _Tokens.json
)

# Access token information
print(f"\nDeck has {len(deck.tokens)} token types:")
for token_key, token_data in deck.tokens.items():
    name = token_data.get('name', 'Unknown')
    sources = token_data.get('source_cards', [])
    print(f"  {name}: created by {', '.join(sources)}")

# Save deck with tokens included
deck.to_json(filepath="Decks/MyDeck/MyDeck.json", use_new_format=True)
```

## Working with Card Properties

### Type Checking
```python
from src.core.card import Card

card = Card(name="Test", cardtype="Creature", power="2", toughness="2")

# Check card type
card.is_creature()      # True
card.is_land()          # False
card.is_spell()         # True
card.is_token()         # False
card.is_legendary()     # False

# Check special types
card.is_saga()          # False
card.is_vehicle()       # False
```

### Color Checking
```python
card = Card(name="Shock", mana="{u}{r}", cardtype="Instant")

# Basic color checks
card.is_white()         # False
card.is_blue()          # True
card.is_red()           # True
card.is_multicolored()  # True
card.is_monocolored()   # False

# Guild/shard checks
card.is_izzet()         # True (blue/red)
card.is_azorius()       # False
card.is_temur()         # False

# Get color list
card.get_colors()       # ['u', 'r']
```

### Mana Operations
```python
from src.core.mana import Mana

# Parse mana cost
mana_value = Mana.get_mana_value("{2}{u}{r}")  # 4
colors = Mana.get_colors("{2}{u}{r}")          # ['u', 'r']
symbols = Mana.get_mana_symbols("{2}{u}{r}")   # {'2': 1, 'u': 1, 'r': 1}

# Sort mana (WUBRG order)
sorted_mana = Mana.sort("{r}{u}{w}")           # "{w}{u}{r}"

# Color checks
Mana.is_monocolored("{r}")                     # True
Mana.is_multicolored("{u}{r}")                 # True
Mana.is_azorius("{w}{u}")                      # True
```

## Deck Statistics and Analysis

### Get Deck Statistics
```python
from src.services.deck_manager import DeckManager
from src.core.deck import Deck

deck = Deck.from_deck_folder("Test")

# Using DeckManager
dm = DeckManager()
stats = dm.get_deck_statistics(deck)

print(f"Total cards: {stats['total_cards']}")
print(f"Lands: {stats['total_lands']}")
print(f"Spells: {stats['total_spells']}")
print(f"Creatures: {stats['creatures']}")
print(f"Average Mana Value: {stats['average_mana_value']}")
```

### Print Summaries
```python
from src.services.deck_manager import DeckManager

deck = Deck.from_deck_folder("Test")
dm = DeckManager()

# Print all summaries
dm.print_deck_summaries(deck)

# Or call individual methods
deck.print_type_summary()        # Card type distribution
deck.print_color_summary()       # Color distribution
deck.print_mana_summary()        # Mana curve
deck.print_tag_summary()         # Tag categories
```

### Analyze Card Types
```python
from src.core.deck import Deck

deck = Deck.from_deck_folder("Test")

# Get card type counts
types = deck.get_cardtypes()
print(f"Creatures: {types['Creature']}")
print(f"Instants: {types['Instant']}")
print(f"Lands: {types['Land']}")

# Count specific types
spells = deck.count_spells()
lands = deck.count_lands()
print(f"Total spells: {spells}, Total lands: {lands}")
```

## Image Generation

### Generate Card Images
```python
from src.rendering.card_renderer import create_card_image_from_Card
from src.core.card import Card
import os

card = Card(
    name="Lightning Bolt",
    mana="{r}",
    cardtype="Instant",
    rules="Lightning Bolt deals 3 damage to any target."
)

# Create directory if needed
os.makedirs("output/Cards", exist_ok=True)

# Generate card image
create_card_image_from_Card(
    card,
    save_path="output/Cards/"
)
```

### Generate All Deck Images
```python
from src.services.image_generator import ImageGenerator
from src.core.deck import Deck

deck = Deck.from_deck_folder("Test")

ig = ImageGenerator()

# Generate with progress tracking
def progress_callback(current, total, card_name):
    print(f"[{current}/{total}] Generating {card_name}...")

cards_gen, tokens_gen = ig.generate_deck_images(
    deck,
    skip_complete=True,
    automatic_tokens=True,
    progress_callback=progress_callback
)

print(f"Generated {cards_gen} cards and {tokens_gen} tokens")
```

### Generate Printing Images
```python
from src.rendering.card_renderer import create_printing_image_from_Card
from src.core.card import Card

card = Card(
    name="Lightning Bolt",
    mana="{r}",
    cardtype="Instant"
)

# Generate print-ready version
create_printing_image_from_Card(
    card,
    saved_image_path="output/Cards/",
    save_path="output/Printing/"
)
```

### Use CardDraw Directly
```python
from src.rendering.card_renderer import CardDraw
from src.core.card import Card

card = Card(
    name="Lightning Bolt",
    mana="{r}",
    cardtype="Instant",
    rules="Lightning Bolt deals 3 damage to any target."
)

# Create and render card manually
card_draw = CardDraw(card, save_path="output/Lightning_Bolt.jpg")

# Step-by-step rendering
card_draw.write_name()
card_draw.write_type_line()
card_draw.write_rules_text()
card_draw.paste_mana_symbols()
card_draw.paste_set_symbol()
card_draw.paste_artwork("path/to/artwork.jpg")
card_draw.write_power_toughness()
card_draw.save()
```

## Token Generation

### Extract Tokens from Deck
```python
from src.core.deck import Deck

deck = Deck.from_deck_folder("Test")

# Get all tokens from deck (NEW: populates self.tokens with source tracking)
specialized_tokens, common_tokens = deck.get_tokens(
    save_to_deck=True,      # Populate self.tokens dict (recommended)
    save_legacy_file=False  # Optional: create separate _Tokens.json (old format)
)

# Analyze generated tokens
print(f"Total specialized tokens: {len(specialized_tokens)}")
for token in specialized_tokens:
    print(f"  {token['name']}: {token['cardtype']}")

print(f"\nTotal common tokens: {len(common_tokens)}")
print(f"Common tokens: {', '.join(common_tokens)}")

# Access tokens with source tracking (NEW FORMAT)
print(f"\nTokens in deck.tokens: {len(deck.tokens)}")
for token_key, token_data in deck.tokens.items():
    name = token_data.get('name', 'Unknown')
    sources = token_data.get('source_cards', [])
    print(f"  {name}: created by {', '.join(sources)}")
```

### Extract Tokens from Single Card
```python
from src.core.card import Card

card = Card(
    name="Bitterblossom",
    mana="{u/b}",
    cardtype="Enchantment",
    rules="At the beginning of your upkeep, you lose 1 life and create a 1/1 black Faerie Rogue creature token with flying."
)

# Get tokens created by this card
specialized_tokens, common_tokens = card.get_tokens()

print(f"Specialized tokens: {len(specialized_tokens)}")
for token in specialized_tokens:
    print(f"  - {token['name']}: {token.get('cardtype', 'Unknown')}")

print(f"Common tokens: {common_tokens}")
```

## Configuration Management

### Check and Update Settings
```python
from src.services.settings_manager import SettingsManager

sm = SettingsManager()

# Get current paths
deck_path = sm.get_deck_path()
cockatrice_path = sm.get_cockatrice_path()
print(f"Deck path: {deck_path}")
print(f"Cockatrice path: {cockatrice_path}")

# Validate paths
validation = sm.validate_paths()
for path_name, info in validation.items():
    print(f"{path_name}: exists={info['exists']}, writable={info['writable']}")

# Check for errors
errors = sm.get_validation_errors()
if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Configuration is valid!")
```

### Update Configuration
```python
from src.services.settings_manager import SettingsManager

sm = SettingsManager()

# Update paths
sm.set_deck_path("/new/path/to/Decks")
sm.set_cockatrice_path("/new/path/to/Cockatrice")

# Reset to defaults
sm.reset_to_defaults()

# Create missing directories
results = sm.create_missing_directories()
for path, success in results.items():
    status = "created" if success else "failed"
    print(f"{path}: {status}")
```

## Full Workflow Example

### Complete Deck Building Pipeline
```python
from src.core.deck import Deck
from src.services.image_generator import ImageGenerator
from src.services.deck_manager import DeckManager
from src.integration.cockatrice import update_cockatrice

# 1. Load the deck
print("Loading deck...")
deck = Deck.from_deck_folder("MyDeck")

# 2. Print statistics
print("\nDeck Statistics:")
dm = DeckManager()
dm.print_deck_summaries(deck)

# 3. Generate card images
print("\nGenerating card images...")
ig = ImageGenerator()
cards_gen, tokens_gen = ig.generate_deck_images(
    deck,
    skip_complete=True,
    automatic_tokens=True,
    progress_callback=lambda c, t, n: print(f"  {n}")
)
print(f"Generated {cards_gen} cards and {tokens_gen} tokens")

# 4. Export to Cockatrice
print("\nExporting to Cockatrice...")
update_cockatrice(deck)
print("Done!")
```

## JSON Examples

### NEW FORMAT: Complete Deck Structure
```json
{
  "metadata": {
    "folder_name": "MyDeck",
    "deck_name": "Red Deck Wins",
    "description": "Aggressive red deck",
    "format": "Modern",
    "created": "2025-11-14T12:00:00Z",
    "last_modified": "2025-11-14T15:30:00Z",
    "author": "PlayerName",
    "tags": ["aggro", "red"],
    "commander": null,
    "setname": "MRD"
  },
  "cards": {
    "Lightning Bolt": {
      "name": "Lightning Bolt",
      "mana": "{r}",
      "cardtype": "Instant",
      "rules": "Lightning Bolt deals 3 damage to any target.",
      "quantity": 4,
      "rarity": "uncommon",
      "complete": 1
    },
    "Mountain": {
      "name": "Mountain",
      "cardtype": "Land",
      "subtype": "Mountain",
      "basic": 1,
      "quantity": 20
    }
  },
  "tokens": {
    "_TOKEN_Treasure": {
      "name": "Treasure",
      "cardtype": "Artifact",
      "subtype": "Treasure",
      "rules": "{T}, Sacrifice this artifact: Add one mana of any color.",
      "token": 1,
      "quantity": 1,
      "complete": 1,
      "source_cards": ["Dockside Extortionist"]
    }
  }
}
```

### OLD FORMAT: Minimal Card Definition (Still Supported)
```json
{
  "Lightning Bolt": {
    "name": "Lightning Bolt",
    "cardtype": "Instant"
  }
}
```

### OLD FORMAT: Complete Card Definition (Still Supported)
```json
{
  "Sheoldred, the Apocalypse": {
    "name": "Sheoldred, the Apocalypse",
    "mana": "{2}{b}{b}",
    "cardtype": "Creature",
    "subtype": "Phyrexian Praetor",
    "rarity": "Mythic",
    "power": "4",
    "toughness": "5",
    "rules": "Deathtouch\nWhenever you draw a card, you gain 2 life.\nWhenever an opponent draws a card, they lose 2 life.",
    "flavor": "\"Gix failed. I shall not.\"",
    "complete": 1,
    "legendary": 1,
    "tags": ["LifeDrain"]
  }
}
```

### Multi-line Rules (Saga)
```json
{
  "The Kami War": {
    "name": "The Kami War",
    "mana": "{1}{w}{u}{b}{r}{g}",
    "cardtype": "Enchantment",
    "subtype": "Saga",
    "rarity": "Rare",
    "rules1": "Exile target nonland permanent an opponent controls.",
    "rules2": "Return up to one other target nonland permanent to its owner's hand. Then each opponent discards a card.",
    "rules3": "Exile this Saga, then return it to the battlefield transformed under your control.",
    "complete": 1
  }
}
```

### Double-Faced Card (Transform)
```json
{
  "Archangel Avacyn": {
    "name": "Archangel Avacyn",
    "mana": "{3}{w}{w}",
    "cardtype": "Creature",
    "subtype": "Angel",
    "rarity": "Mythic",
    "power": "4",
    "toughness": "4",
    "rules": "Flash\nFlying, vigilance\nWhen Archangel Avacyn enters the battlefield, creatures you control gain indestructible until end of turn.\nWhen a non-Angel creature you control dies, transform Archangel Avacyn at the beginning of the next upkeep.",
    "special": "transform-front",
    "related": "Avacyn, the Purifier",
    "complete": 1,
    "legendary": 1
  }
}
```

## Debugging Examples

### Check Card Frame Selection
```python
from src.core.card import Card

card = Card(
    name="Test Card",
    mana="{u}{r}",
    cardtype="Creature",
    power="2",
    toughness="2"
)

# See which frame will be used
frame_path = card.get_frame_filename()
print(f"Frame: {frame_path}")

# Manual frame check
from src.utils.paths import CARD_BORDERS_PATH
full_path = card.get_frame_filename(CARD_BORDERS_PATH)
print(f"Full path: {full_path}")
```

### Validate Card Data
```python
from src.core.card import Card

try:
    card = Card(
        name="Test",
        mana="{invalid}",  # This might cause issues
        cardtype="Creature"
    )
except TypeError as e:
    print(f"Type error: {e}")
except ValueError as e:
    print(f"Value error: {e}")
```

### List Available Decks
```python
from src.services.deck_manager import DeckManager

dm = DeckManager()
decks = dm.list_available_decks()

print("Available decks:")
for deck_name in decks:
    print(f"  - {deck_name}")
```
