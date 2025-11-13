# Configuration System

This document describes the configuration system implemented for Manufactor to manage user-specific paths and settings.

## Overview

The configuration system allows users to customize where Manufactor stores deck files and where it finds the Cockatrice installation. This replaces the previous hard-coded paths in `src/utils/paths.py`.

## Architecture

### Components

1. **`src/utils/config.py`** - Core configuration manager
   - Loads and saves JSON configuration files
   - Provides default values
   - Validates configuration

2. **`src/utils/paths.py`** - Path constants (updated)
   - Now loads user-configurable paths from config.json
   - Maintains static asset paths relative to project

3. **`src/services/settings_manager.py`** - Settings service layer
   - High-level API for managing settings
   - Path validation and verification
   - Designed for GUI integration

4. **`src/cli/configure.py`** - CLI configuration tool
   - User-friendly command-line interface
   - View, validate, and modify settings

5. **`config.json`** - User configuration file (gitignored)
   - Stores user-specific paths
   - Auto-created with defaults on first run

6. **`config.example.json`** - Template configuration
   - Committed to git as documentation
   - Shows expected structure

## Configuration File Format

```json
{
    "paths": {
        "deck_path": "/path/to/your/Decks",
        "cockatrice_path": "/path/to/Cockatrice/folder"
    }
}
```

### Configurable Paths

- **`deck_path`**: Where deck folders and card files are saved
  - Default: `<project_parent>/Decks`
  - Used by: DeckManager, file operations

- **`cockatrice_path`**: Root Cockatrice installation folder
  - Default (macOS): `~/Library/Application Support/Cockatrice/Cockatrice`
  - Used by: CockatriceExporter, Cockatrice integration

### Derived Paths

These are automatically computed from `cockatrice_path`:
- `COCKATRICE_MANUFACTOR_PATH`: `<cockatrice_path>/manufactor`
- `COCKATRICE_IMAGE_PATH`: `<cockatrice_path>/pics/CUSTOM`
- `COCKATRICE_CUSTOMSETS_PATH`: `<cockatrice_path>/customsets`
- `COCKATRICE_DECKS_PATH`: `<cockatrice_path>/decks`

## Usage Examples

### CLI Tool

```bash
# Show current configuration
python -m src.cli.configure --show

# Validate paths
python -m src.cli.configure --validate

# Set deck path
python -m src.cli.configure --set-deck-path ~/Documents/Magic/Decks

# Set Cockatrice path
python -m src.cli.configure --set-cockatrice-path "~/Library/Application Support/Cockatrice/Cockatrice"

# Reset to defaults
python -m src.cli.configure --reset
```

### Programmatic Usage

```python
from src.services.settings_manager import SettingsManager

# Initialize settings manager
settings = SettingsManager()

# Get current paths
deck_path = settings.get_deck_path()
cockatrice_path = settings.get_cockatrice_path()

# Update paths
settings.set_deck_path("/new/path/to/Decks")
settings.set_cockatrice_path("/new/path/to/Cockatrice")

# Validate configuration
validation = settings.validate_paths()
# Returns: {'deck_path': {'path': str, 'exists': bool, 'writable': bool}, ...}

errors = settings.get_validation_errors()
# Returns: List[str] of error messages

# Create missing directories
results = settings.create_missing_directories()

# Reset to defaults
settings.reset_to_defaults()
```

### Direct Config Access

```python
from src.utils.config import get_config

# Get config instance
config = get_config()

# Read values
deck_path = config.get_deck_path()
cockatrice_path = config.get_cockatrice_path()

# Update values
config.set_deck_path("/new/path")
config.save_config()

# Get entire config
all_config = config.get_config()
```

## GUI Integration

The `SettingsManager` service is designed for easy GUI integration:

```python
from src.services.settings_manager import SettingsManager

class SettingsDialog:
    def __init__(self):
        self.settings = SettingsManager()

    def load_settings(self):
        """Load current settings into UI"""
        self.deck_path_field.setText(self.settings.get_deck_path())
        self.cockatrice_path_field.setText(self.settings.get_cockatrice_path())

    def save_settings(self):
        """Save settings from UI"""
        try:
            self.settings.set_deck_path(self.deck_path_field.text())
            self.settings.set_cockatrice_path(self.cockatrice_path_field.text())

            # Validate after saving
            errors = self.settings.get_validation_errors()
            if errors:
                self.show_warnings(errors)
            else:
                self.show_success()
        except ValueError as e:
            self.show_error(str(e))

    def validate_ui(self):
        """Validate paths as user types"""
        validation = self.settings.validate_paths()

        # Update UI indicators
        self.update_path_indicator('deck_path', validation['deck_path'])
        self.update_path_indicator('cockatrice_path', validation['cockatrice_path'])
```

## Migration from Hard-coded Paths

### Before (Hard-coded)

```python
# src/utils/paths.py
DECK_PATH = os.path.join(os.path.dirname(PROJECT_ROOT), "Decks")
COCKATRICE_PATH = os.path.join("/", "Users", "fabiochiappina", "Library", "Application Support", "Cockatrice", "Cockatrice")
```

### After (Configurable)

```python
# src/utils/paths.py
from src.utils.config import get_config

_config = get_config()
DECK_PATH = _config.get_deck_path()
COCKATRICE_PATH = _config.get_cockatrice_path()
```

### Compatibility

All existing code that imports from `src.utils.paths` continues to work without modification. The paths are simply loaded from configuration instead of being hard-coded.

## Default Values

The system provides intelligent defaults:

1. **Deck Path**: `<project_parent>/Decks`
   - Example: If project is at `/Desktop/Magic/Manufactor`
   - Default deck path: `/Desktop/Magic/Decks`

2. **Cockatrice Path**: Platform-specific
   - macOS: `~/Library/Application Support/Cockatrice/Cockatrice`
   - Windows: `%APPDATA%/Cockatrice/Cockatrice`
   - Linux: `~/.local/share/Cockatrice/Cockatrice`

## Error Handling

The configuration system handles various error scenarios:

- **Missing config file**: Creates with defaults
- **Invalid JSON**: Falls back to defaults, shows warning
- **Missing keys**: Merges with defaults
- **Invalid paths**: Validation catches and reports issues
- **Permission errors**: Gracefully handles and reports

## Best Practices

1. **Always validate after user input**: Use `validate_paths()` or `get_validation_errors()`
2. **Check writability**: Not just existence - user needs write access
3. **Provide feedback**: Show validation errors to users
4. **Expand paths**: Use `os.path.expanduser()` for `~` support
5. **Reload after changes**: The settings manager automatically reloads the paths module

## Testing

The configuration system is fully testable:

```python
# Test with custom config location
from src.utils.config import ConfigManager

config = ConfigManager("/tmp/test_config.json")
config.set_deck_path("/test/decks")
assert config.get_deck_path() == "/test/decks"
```

## Future Enhancements

Possible future additions:

1. Additional configurable paths (custom assets, templates, etc.)
2. UI theme/appearance settings
3. Default export options
4. Recent files/decks list
5. Window size/position persistence
6. Export format preferences
7. Custom font paths
8. Auto-save settings
