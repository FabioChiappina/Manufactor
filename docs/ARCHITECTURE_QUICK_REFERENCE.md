# Manufactor Quick Reference

## Key File Locations

### Source Code
| Module | File | Size | Purpose |
|--------|------|------|---------|
| **Core** | `src/core/card.py` | ~855 lines | Card data model |
| | `src/core/deck.py` | ~480 lines | Deck management |
| | `src/core/mana.py` | ~473 lines | Mana parsing |
| **Rendering** | `src/rendering/card_renderer.py` | ~767 lines | Image generation |
| | `src/rendering/layout_constants.py` | ~50 lines | Position/sizing |
| **Services** | `src/services/deck_manager.py` | Service for deck operations |
| | `src/services/image_generator.py` | Service for image generation |
| | `src/services/settings_manager.py` | Config & path management |
| **CLI** | `src/cli/build_deck.py` | Main CLI entry point |
| **Integration** | `src/integration/cockatrice.py` | ~287 lines | Cockatrice export |

### Data Files
| File | Location | Purpose |
|------|----------|---------|
| Deck JSON | `Decks/DeckName/DeckName.json` | Deck metadata + cards + tokens |
| Common Tokens | `config/common_tokens.json` | Reusable token definitions |
| Config | `config/config.json` | User paths |
| Card Images | `Decks/DeckName/Cards/` | Rendered cards |
| Artwork | `Decks/DeckName/Artwork/` | Source images |

### Assets
| Asset | Location | Count |
|-------|----------|-------|
| Card Frames | `Assets/CardBorders/` | 76+ .jpg |
| Mana Symbols | `Assets/Symbols/` | PNG symbols |
| Set Symbols | `Assets/SetSymbols/` | PNG set icons |
| MDFC Indicator | `Assets/MDFC/` | PNG indicators |
| Fonts | `Assets/Fonts/` | TTF files |

---

## Deck JSON Schema

**Status:** ✅ **FULLY IMPLEMENTED** - Backward compatible with old format

### Full Deck Structure (New Format)
```json
{
  "metadata": {
    "folder_name": "DeckName",
    "deck_name": "Display Name",
    "description": "Deck description",
    "format": "Commander",
    "created": "2025-11-14T12:00:00Z",
    "last_modified": "2025-11-14T15:30:00Z",
    "author": "User",
    "tags": ["aggro", "red"],
    "commander": "Card Name"
  },
  "cards": { /* card objects */ },
  "tokens": { /* token objects */ }
}
```

### Card Object (Minimal)
```json
{
  "Card Name": {
    "name": "Card Name",
    "cardtype": "Creature",
    "power": "2",
    "toughness": "2"
  }
}
```

### Card Object (Complete)
```json
{
  "Card Name": {
    "name": "Card Name",
    "mana": "{1}{u}{r}",
    "cardtype": "Creature",
    "subtype": "Wizard",
    "power": "2",
    "toughness": "3",
    "rarity": "Uncommon",
    "rules": "Haste",
    "flavor": "Flavor text",
    "quantity": 4,
    "colors": ["u", "r"],
    "tags": ["Spellslinger"],
    "complete": 1,
    "real": 1,
    "legendary": 1,
    "artwork": "Artwork/CardName.jpg"
  }
}
```

### Token Object
```json
{
  "_TOKEN_Treasure": {
    "name": "Treasure",
    "cardtype": "Artifact",
    "subtype": "Treasure",
    "rules": "{T}, Sacrifice this artifact: Add one mana of any color.",
    "token": 1,
    "colors": [],
    "complete": 1,
    "quantity": 1,
    "source_cards": ["Card That Creates It"]
  }
}
```

### Common Tokens (config/common_tokens.json)
```json
{
  "Treasure": { /* full token definition */ },
  "Food": { /* full token definition */ },
  "Clue": { /* full token definition */ }
}
```

---

## Mana Symbols

### Standard
`{w}` White | `{u}` Blue | `{b}` Black | `{r}` Red | `{g}` Green | `{c}` Colorless

### Hybrid (Color/Color)
`{w/u}` `{u/b}` `{b/r}` `{r/g}` `{g/w}` `{w/b}` `{u/r}` `{b/g}` `{r/w}` `{g/u}`

### Hybrid (2/Color)
`{2/w}` `{2/u}` `{2/b}` `{2/r}` `{2/g}`

### Phyrexian
`{w/p}` `{u/p}` `{b/p}` `{r/p}` `{g/p}`

### Numeric & Variable
`{0}` - `{20}` Generic mana | `{x}` `{y}` `{z}` Variable

### Special
`{t}` Tap | `{q}` Untap | `{s}` Snow | `{e}` Exile mana (custom)

---

## Core Classes Quick API

### Card
```python
from src.core.card import Card

# Create
card = Card(name="Lightning Bolt", mana="{r}", cardtype="Instant", quantity=4, ...)

# Properties
card.name, card.mana, card.cardtype, card.power, card.toughness
card.rules, card.flavor, card.colors, card.complete, card.frame
card.quantity           # NEW: Number of copies in deck (default: 1)

# Methods
card.is_creature()          # Type check
card.is_white()             # Color check
card.is_azorius()           # Guild check
card.get_mana_value()       # Returns int (CMC)
card.get_colors()           # Returns ['w', 'u', ...]
card.get_frame_filename()   # Returns frame path
card.get_type_line()        # Returns complete type line
card.get_tokens()           # Returns (specialized_tokens, common_tokens)
```

### Deck
```python
from src.core.deck import Deck

# Load (auto-detects old vs new format)
deck = Deck.from_deck_folder("DeckName")
deck = Deck.from_json("path/to/deck.json", "SET", "DeckName")

# Properties
deck.cards              # List[Card]
deck.name               # str
deck.tags               # List[str]
deck.tokens             # Dict[str, Any] (new format)
deck.description        # str (new format)
deck.format             # str (new format)
deck.author             # str (new format)
deck.commander          # str (new format)

# Methods
deck.count_spells()
deck.count_lands()
deck.get_cardtypes()
deck.get_tokens(save_to_deck=True, save_legacy_file=False)  # NEW: populates deck.tokens
deck.to_json(filepath, use_new_format=True)  # NEW: export to JSON
deck.print_color_summary()
deck.print_mana_summary()
```

### Mana
```python
from src.core.mana import Mana

# Static methods
Mana.get_colors("{2}{u}{r}")           # ['u', 'r']
Mana.get_mana_value("{2}{u}{r}")       # 4
Mana.get_mana_symbols("{2}{u}{r}")     # {'2': 1, 'u': 1, 'r': 1}
Mana.sort("{r}{u}")                    # "{u}{r}" (WUBRG order)
Mana.is_monocolored("{r}")             # True
Mana.is_azorius("{w}{u}")              # True
```

---

## Rendering Quick API

### Create Card Image
```python
from src.rendering.card_renderer import create_card_image_from_Card
from src.core.card import Card

card = Card(...)
create_card_image_from_Card(card, save_path="path/to/Cards/")
```

### Create Printing Image
```python
from src.rendering.card_renderer import create_printing_image_from_Card

create_printing_image_from_Card(
    card, 
    saved_image_path="path/to/Cards/",
    save_path="path/to/Printing/"
)
```

### Using CardDraw Directly
```python
from src.rendering.card_renderer import CardDraw

card_draw = CardDraw(card, save_path="path/to/image.jpg")
card_draw.write_name()
card_draw.write_type_line()
card_draw.write_rules_text()
card_draw.paste_mana_symbols()
card_draw.paste_artwork("path/to/artwork.jpg")
card_draw.save()
```

---

## Services Quick API

### DeckManager
```python
from src.services.deck_manager import DeckManager

dm = DeckManager()
deck = dm.load_deck_from_folder("DeckName")
stats = dm.get_deck_statistics(deck)
decks = dm.list_available_decks()
```

### ImageGenerator
```python
from src.services.image_generator import ImageGenerator

ig = ImageGenerator()
cards_gen, tokens_gen = ig.generate_deck_images(
    deck,
    skip_complete=True,
    automatic_tokens=True,
    progress_callback=lambda cur, tot, name: print(f"{cur}/{tot}: {name}")
)
```

### SettingsManager
```python
from src.services.settings_manager import SettingsManager

sm = SettingsManager()
sm.get_deck_path()
sm.set_deck_path("/new/path")
errors = sm.get_validation_errors()
```

---

## CLI Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Build a deck
python3 -m src.cli.build_deck --deck "DeckName"
python3 -m src.cli.build_deck --deck "DeckName" --automatic-tokens 1

# Configuration
python3 -m src.cli.configure --show
python3 -m src.cli.configure --set-deck-path /path/to/Decks
python3 -m src.cli.configure --validate

# Prepare reprints
python3 -m src.cli.prepare_reprints "OutputDir"

# Deactivate when done
deactivate
```

---

## Frame Naming Convention

### Color Prefix
`w_`, `u_`, `b_`, `r_`, `g_`, `c_`, `wu_`, `ub_`, `br_`, `rg_`, `gw_`, etc. | `m_` (multicolor)

### Card Type
`creature`, `noncreature`, `artifact-creature`, `artifact-noncreature`, `land`, `enchantment-*`

### Special Type (if applicable)
`transform-front`, `transform-back`, `mdfc-front`, `mdfc-back`, `token-creature`, `saga`

### Legendary Suffix (if applicable)
`_legendary`

### Example Frames
- `r_creature.jpg` - Red creature
- `r_creature_legendary.jpg` - Red legendary creature
- `wu_noncreature.jpg` - White/blue spell
- `m_mdfc-front_creature.jpg` - Multicolor MDFC front creature
- `g_token_creature.jpg` - Green token creature

---

## Deck Folder Structure

```
Decks/
└── MyDeck/
    ├── MyDeck.json                    # Card definitions (required)
    ├── MyDeck_Tokens.json             # Generated tokens (auto-created)
    ├── Cards/                         # Generated card images
    │   ├── Lightning Bolt.jpg
    │   └── Sheoldred, the Apocalypse.jpg
    ├── Artwork/                       # Source artwork (required)
    │   ├── Lightning Bolt.jpg
    │   └── Sheoldred, the Apocalypse.jpg
    ├── Tokens/                        # Generated token images
    │   └── Treasure.jpg
    ├── Printing/                      # Print-ready versions
    │   ├── Lightning Bolt.jpg
    │   └── Sheoldred, the Apocalypse.jpg
    └── Reference/                     # Optional reference materials
```

---

## Architecture Layers

```
UI (Future)
    ↓
Services (DeckManager, ImageGenerator, SettingsManager)
    ↓
Core (Card, Deck, Mana, CardSet, Ability)
    ↓
Specialized (Rendering, Token Generation, Integration)
    ↓
Utilities (Paths, Config, File Utils)
```

---

## Common Tasks

### Load a Deck
```python
from src.core.deck import Deck
deck = Deck.from_deck_folder("DeckName")
```

### Generate All Card Images
```python
from src.services.image_generator import ImageGenerator
ig = ImageGenerator()
ig.generate_deck_images(deck, automatic_tokens=True)
```

### Get Deck Statistics
```python
from src.services.deck_manager import DeckManager
dm = DeckManager()
stats = dm.get_deck_statistics(deck)
dm.print_deck_summaries(deck)
```

### Check Configuration
```python
from src.services.settings_manager import SettingsManager
sm = SettingsManager()
validation = sm.validate_paths()
errors = sm.get_validation_errors()
```

### Create New Deck Folder
```python
from src.services.deck_manager import DeckManager
dm = DeckManager()
dm.create_deck_folder("NewDeck")
```

---

## Special Keywords in JSON

| Keyword | Purpose |
|---------|---------|
| `_basics` | Basic land definitions (special key, ignored from card creation) |
| `_common_tokens` | List of common token names (Treasure, Clue, Food, etc.) |
| `_TOKEN_*` | Token definitions (e.g., `_TOKEN_Treasure`) - auto-generated |
| `_COMMON_TOKENS` | List of common token names in tokens JSON - auto-generated |

---

## Important Paths (from src/utils/paths.py)

```python
PROJECT_ROOT = /Users/fabiochiappina/Desktop/Artwork/Magic/Manufactor
ASSETS_PATH = PROJECT_ROOT/Assets
CARD_BORDERS_PATH = ASSETS_PATH/CardBorders
SYMBOL_PATH = ASSETS_PATH/Symbols
SET_SYMBOL_PATH = ASSETS_PATH/SetSymbols
SAGA_SYMBOL_PATH = ASSETS_PATH/SagaSymbols
MDFC_INDICATOR_PATH = ASSETS_PATH/MDFC
FONT_PATHS = {...}
DECK_PATH = (from config/config.json)
COCKATRICE_PATH = (from config/config.json)
```

---

## Configuration File Format

**config/config.json:**
```json
{
    "paths": {
        "deck_path": "/path/to/Decks",
        "cockatrice_path": "/path/to/Cockatrice"
    }
}
```

**Default Paths:**
- Deck: `<project_parent>/Decks`
- Cockatrice (macOS): `~/Library/Application Support/Cockatrice/Cockatrice`
- Cockatrice (Windows): `%APPDATA%/Cockatrice/Cockatrice`
- Cockatrice (Linux): `~/.local/share/Cockatrice/Cockatrice`
