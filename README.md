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

- **`src/services/`** - Business logic layer (future)
- **`src/ui/`** - GUI components (future)

### Legacy Files (Root Level)

For backward compatibility, the original scripts remain at the root:
- `build_deck.py` - Legacy CLI (kept for compatibility)
- `build_card.py` - Legacy rendering code
- `game_elements.py` - Legacy core classes
- `paths.py` - Legacy path configuration

See [src/README.md](src/README.md) for detailed module documentation.

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

### Using Legacy Scripts (Deprecated)

For backward compatibility, the old scripts still work:

```bash
# Activate virtual environment first
source venv/bin/activate

# Build a deck
python build_deck.py -d "YourDeckName"
```

**Note**: Legacy scripts will be deprecated in a future version. Please migrate to the new CLI.

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
