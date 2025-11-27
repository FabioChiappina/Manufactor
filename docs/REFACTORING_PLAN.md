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

### ✅ Phase 2a: Core Class Extraction
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

### ✅ Phase 2b: Documentation
**Status**: Complete
**Commit**: `e6df63b`

Created comprehensive documentation:
- `REFACTORING_PLAN.md` - Detailed refactoring roadmap
- Updated main `README.md` with refactoring references
- Documented all completed and planned phases
- Migration strategy and design decisions

---

### ✅ Phase 2c: Complex Class Extraction
**Status**: Complete
**Commit**: `345c325`

Extracted remaining complex classes from `game_elements.py`:

#### 1. **src/core/card.py** (~487 lines)
- Complete Card class with all properties and validation
- Type checking methods (is_creature, is_artifact, etc.)
- Frame filename generation
- JSON serialization
- Dependencies: Mana, CardSet, paths

#### 2. **src/token_generation/token_parser.py** (~320 lines)
- Extracted `Card.get_tokens_from_rules_text()` static method
- Token parsing from rules text
- Common token detection
- Lazy Card import to avoid circular dependencies

#### 3. **src/core/deck.py** (~304 lines)
- Deck class with card collection management
- Statistics calculation (curve, colors, etc.)
- JSON import/export
- `from_deck_folder()` factory method
- Dependencies: Card, CardSet, Mana, paths

**Challenges Resolved**:
- Circular dependency between Card and token parsing resolved with lazy import
- All modules tested independently
- Full backward compatibility maintained

---

### ✅ Phase 3: Rendering Split
**Status**: Complete
**Commit**: `7652e07`

Split `build_card.py` (~827 lines) into rendering modules:

#### 1. **src/rendering/layout_constants.py** (~50 lines)
- POSITION_* constants (card name, type line, rules text, etc.)
- MAX_HEIGHT_* and MAX_WIDTH_* constraints
- SIZE constants (card dimensions, symbols)
- Color constants (BLACK, WHITE)

#### 2. **src/utils/file_utils.py** (~30 lines)
- `find_cards_with_card_name()` - Artwork file matching
- Unicode normalization for file system compatibility

#### 3. **src/rendering/card_renderer.py** (~767 lines)
- Complete CardDraw class
- Image composition and layering
- `create_card_image_from_Card()` - Full card rendering
- `create_printing_image_from_Card()` - Print-ready images
- All text and symbol rendering methods

**Testing**: All rendering imports verified
**Exports**: Updated `__init__.py` files for clean imports

---

### ✅ Phase 4: CLI and Integration
**Status**: Complete
**Commit**: `cece7a4`

Organized command-line tools and external integrations:

#### 1. **src/integration/cockatrice.py** (~287 lines)
- Extracted `update_cockatrice()` from build_deck.py
- XML generation for custom cards and tokens
- Deck file (.cod) export for Cockatrice
- Image copying to Cockatrice directories
- Token management with duplicate handling

#### 2. **src/cli/build_deck.py** (~77 lines)
- Moved from root with updated imports
- CLI argument parsing (--deck, --automatic-tokens)
- `create_images_from_Deck()` function
- Orchestrates deck building pipeline
- Usage: `python3 -m src.cli.build_deck --deck "DeckName"`

#### 3. **src/cli/prepare_reprints.py** (~57 lines)
- Moved from root with updated imports
- Reprint preparation utilities
- Front/back card pairing support
- Usage: `python3 -m src.cli.prepare_reprints "OutputDir"`

**Import Updates**:
- All imports migrated to new module structure
- `game_elements.Deck` → `from src.core.deck import Deck`
- `paths.DECK_PATH` → `from src.utils.paths import DECK_PATH`
- `build_card.create_card_image_from_Card` → `from src.rendering.card_renderer import create_card_image_from_Card`

**Testing**: CLI functionality verified with `--help` flag

### ✅ Phase 5: Services Layer
**Status**: Complete
**Commit**: `TBD`

Created comprehensive business logic layer to bridge UI and core functionality:

#### 1. **src/services/card_builder.py** (~280 lines)
Complete CardBuilder class with:
- `create_card_from_form_data()` - Creates Card from UI form data
- `validate_card_data()` - Validates form inputs with error messages
- `get_suggested_frame()` - Suggests appropriate frame based on properties
- `infer_colors_from_mana()` - Extracts color identity from mana cost
- `calculate_mana_value()` - Calculates mana value (CMC)
- `get_default_card_data()` - Provides type-specific defaults
- Smart validation for creature stats, planeswalker loyalty, mana costs

#### 2. **src/services/image_generator.py** (~207 lines)
Complete ImageGenerator class with:
- `generate_deck_images()` - Generates all card/token images with progress tracking
- `generate_single_card_image()` - Generates individual card images
- Directory management and file organization
- Token image generation with automatic JSON regeneration
- Progress callback support for UI integration

#### 3. **src/services/deck_manager.py** (~217 lines)
Complete DeckManager class with:
- `load_deck_from_folder()` and `load_deck_from_json()` - Deck loading
- `get_deck_statistics()` - Comprehensive deck analysis
- `print_deck_summaries()` - Console output for deck stats
- `list_available_decks()` - Browse available decks
- `create_deck_folder()` - Create new deck with proper structure
- Mana curve and color distribution analysis

#### 4. **src/services/cockatrice_exporter.py** (~154 lines)
Complete CockatriceExporter class with:
- `export_deck()` - Full Cockatrice export with options
- `validate_export_paths()` - Path validation with error reporting
- `get_export_info()` - Preview export details
- `is_cockatrice_available()` - Check configuration status
- `get_cockatrice_deck_path()` - Get .cod file path

#### 5. **src/services/settings_manager.py** (~206 lines)
Complete SettingsManager class with:
- `get_deck_path()` and `set_deck_path()` - Deck path management
- `get_cockatrice_path()` and `set_cockatrice_path()` - Cockatrice configuration
- `validate_paths()` - Validate all configured paths
- `get_validation_errors()` - Get validation error messages
- `create_missing_directories()` - Auto-create missing directories
- `reset_to_defaults()` - Reset configuration

**CLI Integration**:
- Updated `src/cli/build_deck.py` to use services layer
- Removed direct core/rendering imports
- Improved error handling and user feedback
- Better progress reporting

**Exports**:
- Updated `src/services/__init__.py` with all five services
- Clean API for GUI development

---

## Planned Phases

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

### ✅ Phase 7: GUI Development - Basic UI
**Status**: In Progress (Basic homepage complete)
**Commit**: `TBD`

Built initial web-based user interface using Gradio:

#### Framework Selection
- **Chosen**: Gradio (web-based UI framework)
- **Rationale**:
  - Rapid prototyping with minimal code
  - Python-native (no JavaScript required)
  - Built-in web server
  - Easy to extend and customize
  - Modern, responsive design out of the box

#### 1. **src/ui/app.py** (~75 lines)
- `create_ui()` - Main Gradio interface builder
- `launch_ui()` - Server launcher with configuration
- Basic homepage with tabs (Home, About)
- Placeholder structure for future features

#### Installation
Updated `requirements.txt`:
- Added `gradio>=4.0.0`
- Successfully installed with all dependencies

#### Usage
```bash
source venv/bin/activate
python3 -m src.ui.app
```
Opens web interface at `http://localhost:7860`

#### Future Enhancements (Phase 7 continuation)
- Card creation form
- Deck management interface
- Image preview
- Cockatrice export options
- Settings configuration UI

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

- [ ] All tests passing (Phase 6)
- [x] No circular dependencies (Resolved with lazy imports)
- [x] Clear module boundaries (Phases 1-5 complete)
- [x] Services layer implemented (Phase 5 complete)
- [ ] GUI prototype working (Phase 7)
- [x] Documentation complete (README and REFACTORING_PLAN updated)
- [x] Original CLI still functional (Legacy scripts maintained)
- [x] New modular CLI working with services layer (`python3 -m src.cli.build_deck`)

### Progress Summary

**Completed: Phases 1-5** ✅
- Project structure established
- All core classes extracted and modular
- Rendering code organized
- CLI and integration code separated
- Services layer implemented (CardBuilder, ImageGenerator, DeckManager, CockatriceExporter, SettingsManager)
- CLI refactored to use services
- Full backward compatibility maintained

**Remaining: Phases 6-7** 📋
- Unit tests
- GUI development

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
