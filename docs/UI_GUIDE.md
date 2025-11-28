# Manufactor Web UI Guide

This guide explains how to use the Gradio-based web interface for Magic Card Manufactor.

## Table of Contents
- [Getting Started](#getting-started)
- [Navigating the Interface](#navigating-the-interface)
- [My Decks Tab](#my-decks-tab)
- [Settings Tab](#settings-tab)
- [About Tab](#about-tab)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Launching the UI

1. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Start the web server**:
   ```bash
   python3 -m src.ui.app
   ```

3. **Access the interface**:
   - Gradio will display a URL in the terminal (usually `http://localhost:7860`)
   - If port 7860 is in use, it will automatically find another port (e.g., 7861, 7862)
   - Open this URL in your web browser
   - The interface should load automatically

4. **Stopping the server**:
   - Press `Ctrl+C` in the terminal
   - Then deactivate the virtual environment: `deactivate`

### First-Time Setup

When you first launch the UI, you should:
1. Navigate to the **Settings** tab
2. Configure your **Deck Path** (where your deck files are stored)
3. Configure your **Cockatrice Path** (if you use Cockatrice)
4. Click **Save Settings**

---

## Navigating the Interface

The UI uses a tabbed interface with three main sections:

### Tab Navigation
- **My Decks**: Browse and manage your card decks
- **Settings**: Configure paths and common tokens
- **About**: Project information and help

Simply click on any tab to switch views.

---

## My Decks Tab

The My Decks tab displays all your available decks in a card-based grid layout.

### Features

#### Deck Discovery
- Automatically scans your configured deck path for valid decks
- A valid deck must have:
  - A folder in the deck path (e.g., `/Decks/MyDeck/`)
  - A JSON file with the same name as the folder (e.g., `MyDeck.json`)

#### Deck Cards Display
Each deck is shown as a card with:
- **Background Image**: Card artwork displayed at 60% opacity with darkening filter
  - Uses the `deck_image` field from metadata if specified
  - Auto-selects the commander for Commander format decks
  - Falls back to the first card in the deck if no commander
  - Supports double-faced cards (uses front face artwork)
- **Deck Name**: The `deck_name` from metadata (falls back to folder name)
- **Card Count**: Number of cards in the deck (supports both old and new JSON formats)
- **Format**: Deck format if specified in metadata (e.g., Commander, Standard)
- **Description**: First 100 characters of the deck description (if available)
- **Path**: Full path to the deck JSON file (small, de-emphasized text)

#### Deck Card Styles
- Cards use a purple gradient background
- Hover effects (lift and shadow) to indicate interactivity
- Cards are arranged in a responsive grid (auto-fills based on screen width)
- Minimum card width: 280px

#### Refresh Button
- Click "🔄 Refresh Decks" to reload the deck list
- Useful after:
  - Adding new deck folders
  - Modifying deck JSON files
  - Changing the deck path in Settings

#### Deck Image Configuration
The background image for each deck card is determined by the `deck_image` field in the deck's metadata section:

```json
{
  "metadata": {
    "deck_name": "My Awesome Deck",
    "deck_image": "Cool Card Name",
    ...
  }
}
```

**Auto-Selection Rules** (when `deck_image` is absent or empty):
1. For Commander format decks: Uses the `commander` field
   - **Single commanders** (string): Uses that commander's artwork
   - **Partner commanders** (array with exactly 2 commanders): Creates a diagonal split composite image showing both commanders
     - Top-left half: First commander
     - Bottom-right half: Second commander
     - Images are automatically resized and blended with a diagonal split
   - For other partner combinations (3+ commanders): Uses the first commander
2. For other formats: Uses the first card in the deck's `cards` dictionary
3. **Double-Faced Cards**: Automatically handles cards with " / " in the name by searching for the front face artwork

**Artwork Location**: Images are loaded from the `Artwork/` subfolder within each deck folder.

**Supported Formats**: `.jpg`, `.jpeg`, `.png`, `.gif`

#### Configuration Status
If the deck path is not configured, the tab will show:
- A warning message
- Instructions to configure the path in Settings

If the deck path doesn't exist, the tab will show:
- An error message with the invalid path
- Instructions to update the path

If no valid decks are found, the tab will show:
- A message explaining what makes a valid deck folder

### Deck Details (Coming Soon)
- Currently, clicking on a deck card shows an alert message
- Future versions will navigate to a deck detail page showing:
  - Full deck information
  - Card list
  - Deck statistics
  - Image generation options
  - Export to Cockatrice button

---

## Settings Tab

The Settings tab provides configuration management for Manufactor.

### Path Configuration

Located at the top of the Settings tab.

#### Deck Path
- **Purpose**: Where your deck folders and card files are stored
- **Default**: `<project_parent>/Decks`
- **Example**: `/Users/yourname/Desktop/Artwork/Magic/Decks`

**To set**:
1. Enter the full path to your decks folder
2. Click **Save Settings**
3. Check the status message for validation results

#### Cockatrice Path
- **Purpose**: Root folder of your Cockatrice installation
- **Default** (macOS): `~/Library/Application Support/Cockatrice/Cockatrice`
- **Default** (Windows): `%APPDATA%/Cockatrice/Cockatrice`
- **Default** (Linux): `~/.local/share/Cockatrice/Cockatrice`

**To set**:
1. Enter the full path to your Cockatrice folder
2. Click **Save Settings**
3. Check the status message for validation results

#### Save Button
- Saves both paths to `config/config.json`
- Validates paths and shows warnings if they don't exist
- Displays success message when saved correctly

---

### Common Token Definitions

Located below Path Configuration in the Settings tab.

Common tokens are predefined token cards (like Treasure, Clue, Food) that can be automatically generated when building decks.

#### Viewing Current Tokens

The token table displays all configured tokens with these columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Name** | Token name | "Treasure" |
| **Card Type** | Card type | "Artifact" |
| **Subtype** | Card subtype | "Treasure" |
| **Rules Text** | Token abilities | "{T}, Sacrifice this artifact: Add one mana of any color." |
| **Colors** | Color identity | "" (empty for colorless) or "W, U" |
| **Frame** | Custom frame | "" (empty for default) or "2015" |

**Default Tokens**:
- Treasure
- Clue
- Food
- Blood
- Map
- Powerstone
- Junk (if added)

#### Adding New Tokens

1. Scroll to the **Add New Token** section
2. Fill in the token details:
   - **Token Name** (required): The name of the token
   - **Card Type**: Usually "Artifact" or "Creature"
   - **Subtype**: Usually matches the token name
   - **Rules Text**: The token's abilities (use MTG shorthand like `{T}`)
   - **Colors**: Comma-separated color codes or leave empty
     - Examples: "W, U" (White/Blue), "R" (Red), "" (colorless)
   - **Frame**: Optional custom frame name (leave empty for default)
3. Click **Add Token**
4. Check the status message and table for confirmation

**Color Codes**:
- W = White
- U = Blue
- B = Black
- R = Red
- G = Green
- Empty = Colorless

**Examples**:

*Creating a Spirit token*:
- Name: `Spirit`
- Card Type: `Creature`
- Subtype: `Spirit`
- Rules Text: `Flying`
- Colors: `W`
- Frame: *(leave empty)*

*Creating a Treasure token*:
- Name: `Treasure`
- Card Type: `Artifact`
- Subtype: `Treasure`
- Rules Text: `{T}, Sacrifice this artifact: Add one mana of any color.`
- Colors: *(leave empty)*
- Frame: *(leave empty)*

#### Deleting Tokens

1. Scroll to the **Delete Token** section
2. Enter the exact token name to delete (e.g., "Treasure")
3. Click **Delete Token**
4. Check the status message and table for confirmation

**Warning**: Deletion is immediate and cannot be undone. The token will be removed from `config/common_tokens.json`.

#### How Tokens Are Saved

- All tokens are saved to `config/common_tokens.json`
- This file is user-specific and not tracked in git
- A template is available at `config/common_tokens.example.json`
- Empty colors = `[]` array (colorless)
- Empty frame = field omitted from JSON (uses default)

**JSON Structure**:
```json
{
  "Treasure": {
    "name": "Treasure",
    "cardtype": "Artifact",
    "subtype": "Treasure",
    "rules": "{T}, Sacrifice this artifact: Add one mana of any color.",
    "token": 1,
    "colors": [],
    "rarity": "common"
  }
}
```

---

## About Tab

The About tab provides:
- Project overview
- List of upcoming features
- Technology stack information
- Current development phase

---

## Troubleshooting

### UI Won't Start

**Error**: `ModuleNotFoundError: No module named 'gradio'`
- **Solution**: Activate virtual environment and install dependencies
  ```bash
  source venv/bin/activate
  pip install -r requirements.txt
  ```

**Error**: `OSError: Cannot find empty port in range: 7860-7860`
- **Solution**: Port is already in use. Gradio will automatically try other ports (7861, 7862, etc.)
- Check terminal output for the actual URL to open

### Settings Not Saving

**Issue**: Paths don't persist after restart
- **Check**: Is `config/config.json` writable?
- **Solution**: Ensure you have write permissions to the `config/` folder

**Issue**: Validation warnings appear
- **Cause**: Paths don't exist or aren't accessible
- **Solution**:
  1. Create the directories if they don't exist
  2. Ensure paths are absolute (not relative)
  3. Use `~/` for home directory on macOS/Linux

### Token Management Issues

**Issue**: Can't add token with same name
- **Solution**: Delete the existing token first, then add the new version

**Issue**: Token doesn't appear in deck builds
- **Check**: Is the token name spelled exactly the same in your deck JSON?
- **Solution**: Token names are case-sensitive and must match exactly

### Browser Compatibility

Gradio works best with modern browsers:
- ✅ Chrome/Chromium (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge

If you experience issues, try:
1. Clearing browser cache
2. Using a different browser
3. Opening in an incognito/private window

### Performance

**Issue**: UI is slow to load
- **Cause**: Large number of tokens or slow file I/O
- **Solution**:
  1. Reduce number of tokens if possible
  2. Ensure disk has sufficient free space
  3. Check if antivirus is scanning project files

---

## Keyboard Shortcuts

### General
- `Ctrl+C` (in terminal): Stop the server
- `Ctrl+R` (in browser): Refresh the page
- `Tab`: Navigate between form fields

### Tab Navigation
- Click tab names to switch views
- Gradio doesn't support keyboard tab switching currently

---

## Tips and Best Practices

### Configuration
1. **Use absolute paths**: Avoid relative paths like `../Decks`
2. **Test paths first**: Create directories before configuring paths
3. **Backup tokens**: Keep a copy of `common_tokens.json` before making changes

### Token Management
1. **Consistent naming**: Use standard MTG token names (Treasure, Clue, etc.)
2. **Use shorthand**: MTG card syntax like `{T}`, `{1}`, etc.
3. **Empty for defaults**: Leave Colors and Frame empty unless you need custom values

### Workflow
1. Configure paths first (Settings tab)
2. Set up common tokens for your project
3. Use CLI or future UI features to build decks
4. Tokens will be automatically generated based on rules text

---

## Getting Help

### Documentation
- [README.md](../README.md) - Main project documentation
- [REFACTORING_PLAN.md](REFACTORING_PLAN.md) - Development roadmap
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration system details

### Issues
- Report bugs: https://github.com/anthropics/claude-code/issues
- Check existing issues before creating new ones

### CLI Alternative
If the UI isn't working, you can still use the CLI:
```bash
python3 -m src.cli.configure --show
python3 -m src.cli.build_deck --deck "YourDeck"
```

---

## Future Features

The following features are planned for the UI:

### My Decks Tab
- Deck browser with thumbnail previews
- Create new deck button
- Edit deck properties
- Generate images for entire deck
- Progress bar for batch operations
- Export to Cockatrice

### Card Editor
- Full card creation form
- Live preview of card image
- Validation and error checking
- Template selection

### Image Gallery
- View generated card images
- Zoom and pan
- Download individual cards
- Bulk export options

See [REFACTORING_PLAN.md](REFACTORING_PLAN.md) for the complete roadmap.
