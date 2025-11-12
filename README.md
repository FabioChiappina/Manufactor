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

- `build_deck.py` - Main script for building deck images and updating Cockatrice
- `build_card.py` - Card image generation functionality
- `game_elements.py` - Core classes for Cards, Decks, Mana, and game elements
- `paths.py` - Path configurations for assets and output directories
- `prepare_reprints.py` - Utility for preparing reprint card images

## Usage

1. Activate the virtual environment (see above)
2. Run the main build script:
   ```bash
   python build_deck.py -d "YourDeckName"
   ```

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
