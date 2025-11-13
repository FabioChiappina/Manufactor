# Source Code Structure

This directory contains all the source code for Manufactor, organized into logical modules.

## Directory Overview

### `core/`
Core game logic and data models representing Magic: The Gathering concepts.
- `mana.py` - Mana cost parsing, color management, and utilities
- `card.py` - Card class representing individual MTG cards
- `deck.py` - Deck class for managing collections of cards with statistics
- `ability.py` - Keyword abilities and mechanics
- `set.py` - Set information and management

### `services/`
Business logic layer providing high-level APIs for operations.

Acts as an intermediary between the UI/CLI and the core logic, providing clean interfaces for:
- `image_generator.py` - Card image generation service with progress tracking
- `deck_manager.py` - Deck loading, management, and statistics
- `cockatrice_exporter.py` - Cockatrice export service with validation
- `settings_manager.py` - Application settings and configuration management

### `rendering/`
Image generation and visual rendering of cards.
- `card_renderer.py` - Main rendering logic (CardDraw class)
- `text_renderer.py` - Text writing and formatting
- `symbol_renderer.py` - Mana and set symbol placement
- `layout_constants.py` - Position and size constants for card layouts

### `token_generation/`
Automatic token detection and generation.
- `token_parser.py` - Parses card rules text to identify and generate token cards

### `integration/`
External software integration.
- `cockatrice.py` - Cockatrice XML and deck file generation
- Future: Support for other platforms (Tabletop Simulator, etc.)

### `utils/`
Shared utilities and helper functions.
- `paths.py` - Path configurations for assets and output directories (loads from config.json)
- `config.py` - Configuration management for user-specific settings
- `file_utils.py` - File operations and utilities

### `ui/`
Graphical user interface (future).
- `windows/` - Top-level application windows
- `widgets/` - Reusable UI components
- `dialogs/` - Dialog windows and popups
- `resources/` - UI-specific resources (styles, themes, icons)

### `cli/`
Command-line interface for power users and scripting.
- `build_deck.py` - Main deck building tool
- `prepare_reprints.py` - Reprint preparation utility
- `configure.py` - Configuration management tool for setting up paths

## Import Guidelines

### For code within `src/`
Use absolute imports from the `src` package:
```python
from src.core.card import Card
from src.utils.paths import ASSETS_PATH
from src.rendering.card_renderer import CardDraw
```

### For external scripts (at project root)
Import from the `src` package:
```python
from src.core.card import Card
from src.cli.build_deck import main
```

## Architecture Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Dependency Direction**: UI/CLI → Services → Core/Rendering/Integration
3. **Independence**: Core logic should not depend on UI or CLI code
4. **Testability**: Each module can be tested independently
5. **Extensibility**: Easy to add new card types, frames, or export formats
