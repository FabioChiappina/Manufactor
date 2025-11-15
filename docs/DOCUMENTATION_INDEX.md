# Manufactor Documentation Index

Complete documentation created for understanding the Manufactor codebase architecture.

## Quick Start

Start here to get oriented with the project:

1. **README.md** - Getting started guide with setup instructions
2. **ARCHITECTURE.md** - Comprehensive architecture guide (START HERE for deep dive)
3. **ARCHITECTURE_QUICK_REFERENCE.md** - Quick reference with API examples

## Documentation Files

### Primary Documentation (Read in Order)

#### 1. ARCHITECTURE.md (675 lines, 25KB)
Comprehensive guide covering:
- Project overview and status
- Cards and decks structure (JSON schema reference)
- Data models (Card, Deck, Mana, CardSet, Ability classes)
- Storage layer (JSON-based, no database)
- Card rendering workflow (CardDraw class, frame system)
- Token generation system
- Services layer (DeckManager, ImageGenerator, SettingsManager)
- File organization (source, assets, configuration)
- Complete workflow examples
- Architecture diagram
- Key technical decisions
- Current limitations

**Best for**: Understanding overall system design and data flow

#### 2. ARCHITECTURE_QUICK_REFERENCE.md (408 lines, 10KB)
Quick reference guide with:
- File location tables (source, data, assets)
- JSON card schema (minimal vs complete examples)
- Mana symbol reference
- Core classes quick API (Card, Deck, Mana)
- Rendering quick API
- Services quick API
- CLI commands
- Frame naming convention
- Deck folder structure
- Architecture layers
- Common tasks with code snippets
- Special JSON keywords
- Important path constants
- Configuration file format

**Best for**: Quick lookups and API reference

#### 3. CODE_EXAMPLES.md (380 lines, 12KB)
Practical code examples for:
- Loading and using cards
- Working with card properties (type/color checking)
- Mana operations
- Deck statistics and analysis
- Image generation
- Token generation
- Configuration management
- Full workflow example
- JSON examples
- Debugging examples

**Best for**: Getting hands-on with the API

### Supporting Documentation

#### 4. REFACTORING_PLAN.md
Detailed refactoring progress tracking:
- Overview of architectural improvements
- Completed phases (1-4)
- Planned phases (5-7)
- Migration strategy for old code
- Success metrics

**Best for**: Understanding refactoring progress and future plans

#### 5. CONFIGURATION.md
Configuration management guide:
- How to configure paths
- Configuration file format
- Default paths by OS
- CLI configuration tools
- Programmatic configuration

**Best for**: Setting up paths and configuration

#### 6. JSON_FORMAT.md
Complete JSON format reference:
- Deck structure (metadata/cards/tokens)
- Metadata fields
- Card fields (face-specific and card-level)
- Token fields
- Mana cost format
- Color codes
- Complete examples

**Best for**: JSON format reference when creating or editing decks

#### 7. DOUBLE_FACED_CARDS.md
Double-faced card documentation:
- Transform and MDFC support
- JSON structure with front/back objects
- Code architecture (CardFace class)
- Commander field (single and multiple)
- Benefits for web UI

**Best for**: Working with double-faced cards

#### 8. SUPERTYPES.md
Supertype field documentation:
- Legendary, Basic, Snow, Token fields
- How to use separate supertype fields
- Examples
- Backward compatibility

**Best for**: Understanding supertype fields

#### 9. README.md
Getting started guide with:
- Prerequisites
- Virtual environment setup
- Project structure overview
- Configuration instructions
- CLI usage
- Troubleshooting

**Best for**: First-time setup

---

## Reading Recommendations by Use Case

### I want to understand the overall architecture
1. ARCHITECTURE.md (sections 1-9)
2. ARCHITECTURE_QUICK_REFERENCE.md (Architecture Layers section)

### I want to write code that uses Manufactor
1. ARCHITECTURE_QUICK_REFERENCE.md (Core Classes Quick API)
2. CODE_EXAMPLES.md (all sections)
3. ARCHITECTURE.md (sections 3-6 as reference)

### I want to modify the rendering system
1. ARCHITECTURE.md (section 4: Card Rendering Workflow)
2. CODE_EXAMPLES.md (Image Generation section)
3. src/rendering/card_renderer.py (actual code)

### I want to add new card types or features
1. ARCHITECTURE.md (section 3: Data Models)
2. src/core/card.py (actual code)
3. ARCHITECTURE.md (section 10: Key Technical Decisions)

### I want to set up the project
1. README.md (Virtual Environment Setup)
2. CONFIGURATION.md (Configuration section)
3. ARCHITECTURE_QUICK_REFERENCE.md (Important Paths section)

### I want to create card definitions
1. JSON_FORMAT.md (complete format reference)
2. CODE_EXAMPLES.md (JSON Examples section)
3. DOUBLE_FACED_CARDS.md (for transform/MDFC cards)
4. SUPERTYPES.md (for legendary, basic, snow fields)

### I want to understand the refactoring
1. REFACTORING_PLAN.md (all sections)
2. ARCHITECTURE.md (section 10: Key Technical Decisions)

---

## Key Concepts at a Glance

### Data Flow
```
JSON File → Deck.from_json() → Card objects → CardDraw → PIL Image → PNG file
```

### Architecture Layers
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

### Card Definition (Minimal JSON)
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

### Main Classes
- **Card** (855 lines) - Single card representation
- **Deck** (480 lines) - Collection of cards + statistics
- **Mana** (473 lines) - All mana operations
- **CardDraw** (767 lines) - Image rendering

---

## File Locations

### Documentation (docs/ folder)
- ARCHITECTURE.md
- ARCHITECTURE_QUICK_REFERENCE.md
- CODE_EXAMPLES.md
- JSON_FORMAT.md
- DOUBLE_FACED_CARDS.md
- SUPERTYPES.md
- CONFIGURATION.md
- REFACTORING_PLAN.md
- DOCUMENTATION_INDEX.md (this file)

### Other Documentation
- README.md (repo root)
- scripts/README.md (utility scripts)

### Source Code
- src/core/card.py - Card data model
- src/core/deck.py - Deck management
- src/core/mana.py - Mana operations
- src/rendering/card_renderer.py - Image rendering
- src/services/ - Service layer (GUI bridge)
- src/cli/ - Command-line tools
- src/utils/ - Utilities

### Example Data
- Decks/Test/Test.json - Example deck
- Decks/Test/Test_Tokens.json - Example tokens
- Assets/CardBorders/ - Frame templates (76+ files)
- Assets/Symbols/ - Symbol images
- Assets/Fonts/ - TTF font files

---

## Quick API Reference

### Load a Deck
```python
from src.core.deck import Deck
deck = Deck.from_deck_folder("DeckName")
```

### Create a Card
```python
from src.core.card import Card
card = Card(name="...", mana="{r}", cardtype="Instant", ...)
```

### Generate Images
```python
from src.services.image_generator import ImageGenerator
ig = ImageGenerator()
ig.generate_deck_images(deck, automatic_tokens=True)
```

### Check Configuration
```python
from src.services.settings_manager import SettingsManager
sm = SettingsManager()
errors = sm.get_validation_errors()
```

### Parse Mana
```python
from src.core.mana import Mana
value = Mana.get_mana_value("{2}{u}{r}")  # 4
colors = Mana.get_colors("{2}{u}{r}")     # ['u', 'r']
```

---

## Common Tasks

| Task | File to Read | Method/Class |
|------|--------------|--------------|
| Load a deck | CODE_EXAMPLES.md | Deck.from_deck_folder() |
| Create a card | CODE_EXAMPLES.md | Card() constructor |
| Generate images | CODE_EXAMPLES.md | ImageGenerator.generate_deck_images() |
| Check paths | CONFIGURATION.md | SettingsManager.validate_paths() |
| Extract tokens | CODE_EXAMPLES.md | deck.get_tokens() |
| Render single card | CODE_EXAMPLES.md | CardDraw class |
| Analyze deck | CODE_EXAMPLES.md | DeckManager.get_deck_statistics() |
| Parse mana | CODE_EXAMPLES.md | Mana.get_*() methods |

---

## External Links

### Project Files
- config.json - User configuration (gitignored)
- requirements.txt - Python dependencies
- venv/ - Virtual environment

### Related Folders
- /Users/fabiochiappina/Desktop/Artwork/Magic/Decks/ - Deck definitions
- /Users/fabiochiappina/Desktop/Artwork/Magic/Manufactor/Assets/ - Card frames & symbols

---

## Version Information

- Project: Magic Card Manufactor
- Current Branch: refactor
- Status: Modular, CLI-ready, preparing for GUI
- Last Updated: 2024-11-14
- Python: 3.7+
- Key Dependencies: Pillow (image), num2words (text)

---

## Contributing

To modify or extend Manufactor:

1. Read ARCHITECTURE.md to understand the system
2. Check REFACTORING_PLAN.md for where your change fits
3. Follow the three-layer architecture (UI → Services → Core)
4. Add code examples to CODE_EXAMPLES.md
5. Update documentation if changing behavior

---

## Notes

- All paths are absolute to avoid relative path issues
- Configuration is user-specific (config.json is gitignored)
- Frame system uses naming convention: [color]_[type]_[special]_[legendary].jpg
- Cards stored as JSON for human readability and versioning
- No database layer - file-based storage only
- Three-layer architecture designed for future GUI development

---

## Generated Files

This index and the three comprehensive documentation files were generated via codebase exploration:

1. ARCHITECTURE.md - 675 lines
2. ARCHITECTURE_QUICK_REFERENCE.md - 408 lines  
3. CODE_EXAMPLES.md - 380 lines
4. DOCUMENTATION_INDEX.md (this file) - 300 lines

Total: 1,700+ lines of comprehensive documentation covering the complete codebase architecture, data structures, workflow, and usage examples.
