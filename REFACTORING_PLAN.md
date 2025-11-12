# Manufactor Refactoring Plan

## Overview
This document tracks the progress of refactoring Manufactor from a single-file command-line tool into a well-organized application ready for GUI development.

## Goals
1. **Separation of Concerns**: Each module has a single, clear responsibility
2. **GUI-Ready Architecture**: Business logic separated from presentation
3. **Testability**: Independent modules that can be unit tested
4. **Maintainability**: Easy to locate and fix issues
5. **Extensibility**: Simple to add new card types, frames, or export formats

## Completed Phases

### ✅ Phase 1: Project Structure Setup
**Status**: Complete
**Commit**: `5182346`

Created comprehensive folder structure:
```
Manufactor/
├── src/
│   ├── core/           # Game logic and data models
│   ├── services/       # Business logic layer (future GUI bridge)
│   ├── rendering/      # Image generation
│   ├── token_generation/  # Token parsing
│   ├── integration/    # External software (Cockatrice)
│   ├── utils/          # Shared utilities
│   ├── ui/            # GUI components (future)
│   └── cli/           # Command-line tools
└── tests/             # Unit tests
```

**Changes**:
- Created all directories and `__init__.py` files with documentation
- Migrated `paths.py` → `src/utils/paths.py` with absolute path resolution
- Added `src/README.md` documenting architecture
- Updated `.gitignore`

---

### ✅ Phase 2 (Part A): Core Class Extraction
**Status**: Complete
**Commit**: `fda1203`

Extracted independent core classes from `game_elements.py`:

#### 1. **src/core/mana.py** (240 lines)
Complete Mana class with:
- Mana symbol parsing and validation
- Color identity calculation
- Mana value (CMC) computation
- Guild/shard color checking (Azorius, Bant, etc.)
- Mana cost sorting and normalization

#### 2. **src/core/card_set.py** (20 lines)
CardSet class for:
- Set name validation
- Conflict resolution with official MTG sets
- Renamed from `Set` to avoid Python built-in conflicts

#### 3. **src/core/ability.py** (30 lines)
Ability classes for:
- Keyword ability definitions
- Self-description and general description text
- AbilityElements collection (Decayed, Shadow, etc.)

**Testing**: All modules tested and working independently
**Backward Compatibility**: `game_elements.py` unchanged and still functional

---

## Planned Phases

### 🔄 Phase 2 (Part B): Large Class Extraction
**Status**: Planned
**Target**: Next phase

Extract remaining complex classes:

#### 1. **src/core/card.py** (~470 lines)
- Card class with all properties and validation
- Type checking methods (is_creature, is_artifact, etc.)
- Frame filename generation
- JSON serialization
- ⚠️ Dependencies: Mana, CardSet, Ability
- ⚠️ Excludes: `get_tokens_from_rules_text()` (move to token_parser)

#### 2. **src/token_generation/token_parser.py** (~320 lines)
- Extract `Card.get_tokens_from_rules_text()` static method
- Token parsing from rules text
- Common token detection
- ⚠️ Dependencies: Card, Mana, Ability

#### 3. **src/core/deck.py** (~305 lines)
- Deck class with card collection management
- Statistics calculation (curve, colors, etc.)
- JSON import/export
- `from_deck_folder()` factory method
- ⚠️ Dependencies: Card, CardSet, Mana

**Challenges**:
- Circular dependencies between Card and token parsing
- Card depends on Mana for frame generation
- Deck depends on Card
- All need JSON serialization

**Approach**:
1. Extract Card without token parsing method
2. Extract token_parser as standalone module that imports Card
3. Extract Deck
4. Update imports throughout codebase
5. Add token parsing method back to Card as a call to token_parser

---

### 📋 Phase 3: Rendering Split
**Status**: Planned

Split `build_card.py` (~827 lines) into rendering modules:

#### 1. **src/rendering/layout_constants.py**
- POSITION_* constants
- MAX_HEIGHT_* constants
- SIZE constants
- Color constants

#### 2. **src/utils/file_utils.py**
- `find_cards_with_card_name()`
- File system utilities

#### 3. **src/rendering/card_renderer.py**
- CardDraw class initialization
- Image composition
- `create_card_image_from_Card()`
- `create_printing_image_from_Card()`

#### 4. **src/rendering/text_renderer.py**
- `write_text()` and text sizing methods
- `write_name()`, `write_type_line()`, `write_rules_text()`
- `write_power_toughness()`
- Italics handling

#### 5. **src/rendering/symbol_renderer.py**
- `paste_mana_symbols()`
- `paste_set_symbol()`
- `paste_mdfc_indicator()`
- `paste_in_text_symbols()`
- `paste_artwork()`

---

### 📋 Phase 4: CLI and Integration
**Status**: Planned

Organize command-line tools and external integrations:

#### 1. **src/cli/build_deck.py**
- Move `build_deck.py` from root
- Keep CLI argument parsing
- Orchestrates deck building

#### 2. **src/integration/cockatrice.py**
- Extract `update_cockatrice()` from build_deck.py
- XML generation for cards and tokens
- Deck file export
- Path validation

#### 3. **src/cli/prepare_reprints.py**
- Move `prepare_reprints.py` from root
- Reprint preparation utilities

---

### 📋 Phase 5: Services Layer
**Status**: Planned

Create business logic layer to bridge UI and core logic:

#### 1. **src/services/card_builder.py**
```python
class CardBuilder:
    def create_card_from_form_data(form_data: dict) -> Card
    def validate_card_data(form_data: dict) -> List[str]
    def get_suggested_frame(colors, cardtype) -> str
```

#### 2. **src/services/image_generator.py**
```python
class ImageGenerator:
    def generate_card_image(card: Card, output_path: str) -> bool
    def generate_deck_images(deck: Deck, progress_callback) -> bool
    def preview_card(card: Card) -> Image
```

#### 3. **src/services/deck_builder.py**
```python
class DeckBuilder:
    def build_from_json(json_path: str) -> Deck
    def export_deck(deck: Deck, format: str) -> bool
    def get_deck_statistics(deck: Deck) -> dict
```

#### 4. **src/services/cockatrice_exporter.py**
```python
class CockatriceExporter:
    def export_deck(deck: Deck, options: dict) -> bool
    def validate_export_paths() -> List[str]
```

---

### 📋 Phase 6: Testing
**Status**: Planned

Add comprehensive unit tests:

- `tests/test_core/test_mana.py`
- `tests/test_core/test_card.py`
- `tests/test_core/test_deck.py`
- `tests/test_rendering/test_card_renderer.py`
- `tests/test_services/test_card_builder.py`

---

### 📋 Phase 7: GUI Development
**Status**: Future

Build graphical user interface:

- Choose UI framework (tkinter, PyQt, web-based)
- Implement `src/ui/windows/` components
- Implement `src/ui/widgets/` reusable components
- Connect to services layer

---

## Migration Strategy

### Import Path Changes

**Current (game_elements.py)**:
```python
from game_elements import Card, Deck, Mana
```

**New (after Phase 2)**:
```python
from src.core import Card, Deck, Mana, CardSet, Ability
```

**New (after Phase 3+)**:
```python
from src.core.card import Card
from src.rendering.card_renderer import CardDraw, create_card_image_from_Card
```

### Backward Compatibility

During transition:
- Keep `game_elements.py` as a facade that imports and re-exports from new modules
- Keep root-level `paths.py` importing from `src.utils.paths`
- Gradually migrate `build_deck.py` and `build_card.py` imports
- Eventually deprecate old import paths

---

## Success Metrics

- [ ] All tests passing
- [ ] No circular dependencies
- [ ] Clear module boundaries
- [ ] Services layer implemented
- [ ] GUI prototype working
- [ ] Documentation complete
- [ ] Original CLI still functional

---

## Notes

### Design Decisions

1. **CardSet over Set**: Renamed to avoid conflict with Python's built-in `set` type
2. **Services Layer**: Added to decouple UI from core logic, enabling both CLI and GUI
3. **Token Parsing**: Separated from Card class due to size and complexity
4. **Three-Layer Architecture**: UI → Services → Core ensures testability and flexibility

### Challenges Addressed

- **Circular Dependencies**: Resolved by extracting independent classes first (Mana, CardSet, Ability)
- **Large Classes**: Breaking Card and Deck into manageable pieces
- **Testing**: Structure enables isolated unit testing
- **GUI Integration**: Services layer provides clean API for UI development
