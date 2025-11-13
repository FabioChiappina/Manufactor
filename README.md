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

If you need to recreate the virtual environment from scratch, follow these steps:

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

This project requires the following Python packages:

- **Pillow** (>=10.0.0) - Image processing library for creating card images
- **num2words** (>=0.5.12) - Converts numbers to words for card text generation

All dependencies are listed in `requirements.txt`.

## Project Structure

This project has been refactored into a modular structure to prepare for GUI development. See [REFACTORING_PLAN.md](REFACTORING_PLAN.md) for detailed progress.

### New Modular Structure (`src/`)

The project is organized into clear, focused modules:

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

- **`src/utils/`** - Shared utilities
  - `paths.py` - Path configurations
  - `file_utils.py` - File system utilities

- **`src/services/`** - Business logic layer
  - `image_generator.py` - Card image generation service
  - `deck_manager.py` - Deck loading and statistics
  - `cockatrice_exporter.py` - Cockatrice export service

- **`src/ui/`** - GUI components (future)

See [src/README.md](src/README.md) for detailed module documentation.

**Note**: Legacy files (build_deck.py, build_card.py, game_elements.py, paths.py) have been removed. All functionality is now in the modular `src/` structure.

## Configuration

### First-Time Setup

When you first run Manufactor, a `config.json` file will be automatically created in the project root with default paths. You should update these paths to match your local system.

### Configuration File (`config.json`)

The configuration file stores local system paths:

```json
{
    "paths": {
        "deck_path": "/path/to/your/Decks",
        "cockatrice_path": "/path/to/Cockatrice/folder"
    }
}
```

**Important Notes:**
- The `config.json` file is user-specific and is not tracked by git (it's in `.gitignore`)
- A `config.example.json` file is provided as a template
- The `deck_path` is where all your deck folders and card files will be saved
- The `cockatrice_path` should point to your Cockatrice installation folder

### Managing Configuration

#### Using the CLI Tool

The easiest way to manage configuration is with the built-in CLI tool:

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

#### Programmatically (for GUI/scripts)

You can also manage settings programmatically:

```python
from src.services.settings_manager import SettingsManager

settings = SettingsManager()

# Get current paths
deck_path = settings.get_deck_path()
cockatrice_path = settings.get_cockatrice_path()

# Set new paths
settings.set_deck_path("/new/path/to/Decks")
settings.set_cockatrice_path("/new/path/to/Cockatrice")

# Validate paths
validation = settings.validate_paths()
errors = settings.get_validation_errors()
```

### Default Paths

- **Deck Path**: `<project_parent>/Decks` (e.g., if Manufactor is at `/Desktop/Magic/Manufactor`, decks will be at `/Desktop/Magic/Decks`)
- **Cockatrice Path** (macOS): `~/Library/Application Support/Cockatrice/Cockatrice`
- **Cockatrice Path** (Windows): `%APPDATA%/Cockatrice/Cockatrice`
- **Cockatrice Path** (Linux): `~/.local/share/Cockatrice/Cockatrice`

## Usage

### Using the New Modular CLI

The recommended way to use Manufactor is with the new modular structure:

```bash
# IMPORTANT: Activate virtual environment first
source venv/bin/activate

# Build a deck (from project root)
python3 -m src.cli.build_deck --deck "YourDeckName"

# With automatic token generation
python3 -m src.cli.build_deck --deck "YourDeckName" --automatic-tokens 1

# Prepare reprints
python3 -m src.cli.prepare_reprints "OutputDirectoryName"

# When done, deactivate the virtual environment
deactivate
```

**Important**: The new CLI requires the virtual environment to be activated to access dependencies (Pillow, num2words).

## Troubleshooting

### Virtual Environment Issues

If you encounter issues with the virtual environment:

1. Delete the existing `venv` folder:
   ```bash
   rm -rf venv
   ```

2. Follow the "Creating the Virtual Environment" steps above to recreate it.

### Package Installation Issues

If package installation fails:

1. Update pip:
   ```bash
   pip install --upgrade pip
   ```

2. Try installing packages individually:
   ```bash
   pip install Pillow
   pip install num2words
   ```
