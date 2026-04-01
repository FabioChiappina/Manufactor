# Magic Card Manufactor

A Python-based tool for creating custom Magic: The Gathering cards with automated image generation and Cockatrice integration.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Virtual Environment Setup

### Activating the Virtual Environment

Before running any Python scripts in this project, activate the virtual environment:

```bash
source venv/bin/activate
```

When activated, you'll see `(venv)` at the beginning of your command prompt.

### Deactivating the Virtual Environment

When you're done working on the project:

```bash
deactivate
```

### Creating the Virtual Environment (First-Time Setup)

If you need to recreate the virtual environment from scratch:

1. **Create a new virtual environment:**
   ```bash
   python3 -m venv venv
   ```

2. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation:**
   ```bash
   pip list
   ```

### Required Packages

- **Pillow** (>=10.0.0) - Image processing for card rendering
- **num2words** (>=0.5.12) - Number-to-word conversion for card text
- **Flask** (>=3.0.0) - Web framework for the UI

All dependencies are listed in `requirements.txt`.

## Project Structure

The project is organized into a modular, three-layer architecture:

```
UI Layer (Flask templates/routes)
    ↓
Services Layer (CardBuilder, ImageGenerator, DeckManager, etc.)
    ↓
Core Layer (Card, Deck, Mana, CardSet, Ability)
    ↓
Specialized Layers (Rendering, Token Generation, Integration, Utils)
```

### Module Overview (`src/`)

- **`src/core/`** - Game logic and data models
  - `mana.py` - Mana cost parsing and color identity
  - `card.py` - Card class with properties and validation
  - `deck.py` - Deck management and statistics
  - `card_set.py` - Set name handling
  - `ability.py` - Keyword abilities

- **`src/rendering/`** - Card image generation
  - `card_renderer.py` - CardDraw class and image creation
  - `layout_constants.py` - Position and sizing constants

- **`src/token_generation/`** - Token parsing from rules text
  - `token_parser.py` - Automatic token detection

- **`src/integration/`** - External software integration
  - `cockatrice.py` - Cockatrice XML and deck export

- **`src/cli/`** - Command-line interface tools
  - `build_deck.py` - Main deck building script
  - `prepare_reprints.py` - Reprint preparation utility
  - `configure.py` - Configuration management CLI

- **`src/utils/`** - Shared utilities
  - `paths.py` - Path configurations
  - `file_utils.py` - File system utilities

- **`src/services/`** - Business logic layer (bridge between UI and core)
  - `card_builder.py` - Card creation from form data
  - `image_generator.py` - Card image generation service
  - `deck_manager.py` - Deck loading and statistics
  - `cockatrice_exporter.py` - Cockatrice export service
  - `settings_manager.py` - Configuration management

- **`src/ui/`** - Flask web interface
  - `app.py` - Flask application and routes
  - `helpers.py` - UI helper functions (image encoding, deck loading, etc.)
  - `templates/` - HTML templates
  - `static/` - CSS and JavaScript assets

See [src/README.md](src/README.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed module documentation.

## Configuration

### First-Time Setup

When you first run Manufactor, a `config.json` file will be automatically created in `config/` with default paths. You should update these paths to match your local system.

### Configuration File (`config/config.json`)

```json
{
    "paths": {
        "deck_path": "/path/to/your/Decks",
        "cockatrice_path": "/path/to/Cockatrice/folder"
    }
}
```

**Notes:**
- `config/config.json` is user-specific and not tracked by git (see `.gitignore`)
- `config/config.example.json` is provided as a template
- `deck_path` is where all your deck folders and card files will be saved
- `cockatrice_path` should point to your Cockatrice installation folder

### Managing Configuration

#### Using the CLI Tool

```bash
# Show current configuration
python -m src.cli.configure --show

# Validate configured paths
python -m src.cli.configure --validate

# Set deck path
python -m src.cli.configure --set-deck-path ~/Documents/Magic/Decks

# Set Cockatrice path (macOS example)
python -m src.cli.configure --set-cockatrice-path "~/Library/Application Support/Cockatrice/Cockatrice"

# Reset to defaults
python -m src.cli.configure --reset
```

#### Programmatically (for scripts)

```python
from src.services.settings_manager import SettingsManager

settings = SettingsManager()

deck_path = settings.get_deck_path()
cockatrice_path = settings.get_cockatrice_path()

settings.set_deck_path("/new/path/to/Decks")
settings.set_cockatrice_path("/new/path/to/Cockatrice")

validation = settings.validate_paths()
errors = settings.get_validation_errors()
```

### Default Paths

- **Deck Path**: `<project_parent>/Decks` (e.g., if Manufactor is at `/Desktop/Magic/Manufactor`, decks will be at `/Desktop/Magic/Decks`)
- **Cockatrice Path** (macOS): `~/Library/Application Support/Cockatrice/Cockatrice`
- **Cockatrice Path** (Windows): `%APPDATA%/Cockatrice/Cockatrice`
- **Cockatrice Path** (Linux): `~/.local/share/Cockatrice/Cockatrice`

## Usage

### Using the Web UI

The primary way to use Manufactor is the Flask-based web interface:

```bash
# Activate virtual environment first
source venv/bin/activate

# Launch the web UI
python3 -m src.ui.app

# The UI will open at http://127.0.0.1:7860
# Press Ctrl+C to stop the server
deactivate
```

**Pages:**
- **My Decks** (`/`) - Grid view of all your decks with artwork backgrounds, completion status badges, and filter controls (All / Complete / Incomplete)
- **Deck Details** (`/deck/<name>`) - Commander card display, card image gallery with quantity badges, and a toggle to mark the deck complete
- **Card Editor** (`/deck/<name>/card/<card>/edit`) - Edit all card properties (name, cost, type, rules, power/toughness, etc.) and save back to the deck JSON
- **Settings** (`/settings`) - Configure deck path and Cockatrice path; manage common token definitions
- **About** (`/about`) - Project info, feature list, documentation links

For full UI documentation, see [docs/UI_GUIDE.md](docs/UI_GUIDE.md).

### Using the CLI

You can also use Manufactor from the command line:

```bash
# Activate virtual environment first
source venv/bin/activate

# Build a deck (from project root)
python3 -m src.cli.build_deck --deck "YourDeckName"

# With automatic token generation
python3 -m src.cli.build_deck --deck "YourDeckName" --automatic-tokens 1

# Prepare reprints
python3 -m src.cli.prepare_reprints "OutputDirectoryName"

deactivate
```

## Documentation

Detailed documentation lives in [docs/](docs/):

| File | Description |
|------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data models, rendering workflow |
| [ARCHITECTURE_QUICK_REFERENCE.md](docs/ARCHITECTURE_QUICK_REFERENCE.md) | API reference tables |
| [CODE_EXAMPLES.md](docs/CODE_EXAMPLES.md) | Practical usage examples |
| [REFACTORING_PLAN.md](docs/REFACTORING_PLAN.md) | Development roadmap and phase history |
| [CONFIGURATION.md](docs/CONFIGURATION.md) | Setup and path configuration details |
| [JSON_FORMAT.md](docs/JSON_FORMAT.md) | Deck and card JSON schema reference |
| [DOUBLE_FACED_CARDS.md](docs/DOUBLE_FACED_CARDS.md) | Transform / MDFC support |
| [SUBSPELLS.md](docs/SUBSPELLS.md) | Adventure and Omen card support |
| [SUPERTYPES.md](docs/SUPERTYPES.md) | Legendary, Basic, Snow fields |
| [REAL_CARDS.md](docs/REAL_CARDS.md) | Integration with real MTG cards |
| [UI_GUIDE.md](docs/UI_GUIDE.md) | Web interface user guide |
| [DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md) | Navigation guide for all docs |

## Features

- **Card Rendering** — 76+ frame templates covering all colors and card types, with automatic frame selection based on card properties
- **Double-Faced Cards** — Full support for transform and modal double-faced cards (MDFC)
- **Adventure / Omen Cards** — Subspell layout support
- **Token Generation** — Automatic token detection from rules text; configurable common token library
- **Deck Management** — JSON-based storage with card quantities, metadata, and statistics
- **Commander Support** — Single commander and partner commander (diagonal split image) display
- **Cockatrice Integration** — Export decks and card images to Cockatrice format
- **Web UI** — Multi-page Flask application with responsive design and artwork integration
- **Configuration** — User-specific settings with CLI and programmatic management

## Troubleshooting

### Virtual Environment Issues

```bash
# Delete and recreate the venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Package Installation Issues

```bash
pip install --upgrade pip
pip install Pillow
pip install num2words
pip install flask
```
