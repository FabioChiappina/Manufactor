# Manufactor Web UI Guide

This guide explains how to use the Flask-based web interface for Magic Card Manufactor.

## Table of Contents
- [Getting Started](#getting-started)
- [Navigating the Interface](#navigating-the-interface)
- [My Decks Page](#my-decks-page)
- [Deck Details Page](#deck-details-page)
- [Card Editor](#card-editor)
- [Settings Page](#settings-page)
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
   - Flask will display a URL in the terminal (usually `http://localhost:7860`)
   - Open this URL in your web browser
   - The interface should load automatically

4. **Stopping the server**:
   - Press `Ctrl+C` in the terminal
   - Then deactivate the virtual environment: `deactivate`

### First-Time Setup

When you first launch the UI, you should:
1. Click **Settings** in the navigation menu
2. Configure your **Deck Path** (where your deck files are stored)
3. Configure your **Cockatrice Path** (if you use Cockatrice)
4. Click **Save Settings**

---

## Navigating the Interface

The UI uses a multi-page interface with navigation links:

### Navigation
- **My Decks**: Browse and manage your card decks
- **Settings**: Configure paths and common tokens
- **About**: Project information and help

Click on any navigation link to switch pages. Each deck card and card item is clickable and will navigate to its detail page.

---

## My Decks Page

The My Decks page (homepage) displays all your available decks in a card-based grid layout.

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

#### Filter Buttons
- **📚 All Decks**: Show all decks regardless of completion status (default)
- **✅ Complete**: Show only decks marked as complete (with `"complete": 1` in metadata)
- **⏳ Incomplete**: Show only decks marked as incomplete (with `"complete": 0` or missing the field)
- Use filters to quickly find decks based on their image generation status

#### Refresh Button
- Click "🔄 Refresh" to reload the deck list
- Resets filter to show all decks
- Useful after:
  - Adding new deck folders
  - Modifying deck JSON files
  - Changing the deck path in Settings
  - Updating deck completion status

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

---

## Deck Details Page

Clicking on a deck card navigates to the deck detail page.

### Features

#### Deck Information Card
- Shows deck metadata in a purple gradient card:
  - **Format**: Deck format (Commander, Standard, etc.)
  - **Total Cards**: Number of cards in the deck
  - **Commander(s)**: Commander card(s) for Commander format
  - **Status**: Complete or Incomplete
  - **Description**: Full deck description

#### Card Gallery
- Displays all cards in the deck as a visual image gallery
- Each card shows:
  - **Card Image**: Full card image from the `Cards/` subfolder within the deck folder
  - **Card Name**: Displayed below the image
  - **Card Type**: Type information (Creature, Instant, etc.)
  - **Subtype**: If applicable (e.g., Wizard, Dragon)
- **Image Sources**:
  - Images are loaded from `<deck_path>/<deck_name>/Cards/`
  - Supports `.jpg`, `.jpeg`, `.png`, and `.gif` formats
  - Handles double-faced cards (searches for front face if full name not found)
  - Shows "No Image" placeholder if card image is not found
- **Gallery Layout**:
  - Responsive grid that automatically adjusts to screen size
  - Cards maintain standard Magic card aspect ratio (5:7)
  - Hover effects for better interactivity
- Click any card to open the card editor

#### Navigation
- "Back to My Decks" link returns to the homepage
- Click any card image to open the card editor

---

## Card Editor

The card editor allows you to edit all properties of a card.

### Features

#### Editable Fields
- **Card Name**: The name of the card
- **Mana Cost**: Mana cost using MTG notation (e.g., {3}{U}{U})
- **Card Type**: Dropdown selection (Creature, Instant, Sorcery, etc.)
- **Subtype**: Card subtype (e.g., Wizard, Dragon)
- **Rules Text**: Card abilities and rules text
- **Power/Toughness**: For creatures
- **Rarity**: Dropdown selection (Common, Uncommon, Rare, Mythic)
- **Flavor Text**: Optional flavor text

#### Actions
- **Save Changes**: Saves the card data back to the deck's JSON file
- **Cancel**: Returns to the deck details page without saving

#### Navigation
- Breadcrumb trail shows: My Decks / Deck Name / Card Name
- Click any breadcrumb link to navigate back

---

## Settings Page

The Settings page provides configuration management for Manufactor.

### Path Configuration

Located at the top of the Settings page.

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

Located below Path Configuration in the Settings page.

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

## Troubleshooting

### UI Won't Start

**Error**: `ModuleNotFoundError: No module named 'flask'`
- **Solution**: Activate virtual environment and install dependencies
  ```bash
  source venv/bin/activate
  pip install -r requirements.txt
  ```

**Error**: Port already in use
- **Solution**: Kill the process using port 7860 or change the port in `src/ui/app.py`
- Check terminal output for any error messages

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

Flask works with all modern browsers:
- ✅ Chrome/Chromium (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge

If you experience issues, try:
1. Clearing browser cache
2. Using a different browser
3. Hard refreshing the page (Cmd+Shift+R or Ctrl+Shift+R)

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
- `Cmd+R` or `Ctrl+R` (in browser): Refresh the page
- `Tab`: Navigate between form fields
- `Enter`: Submit forms

### Navigation
- Click navigation links in header to switch pages
- Click deck cards to view deck details
- Click card items to edit cards
- Use browser back button to navigate backward

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
1. Configure paths first (Settings page)
2. Set up common tokens for your project
3. Browse your decks on the My Decks page
4. Click on decks to view details and edit cards
5. Use the card editor to modify card properties

---

## Getting Help

### Documentation
- [README.md](../README.md) - Main project documentation
- [REFACTORING_PLAN.md](REFACTORING_PLAN.md) - Development roadmap
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration system details

### Support
- Refer to the documentation in the `docs/` folder
- Check the UI_GUIDE.md for interface-related questions
- See CONFIGURATION.md for setup help

### CLI Alternative
If the UI isn't working, you can still use the CLI:
```bash
python3 -m src.cli.configure --show
python3 -m src.cli.build_deck --deck "YourDeck"
```

---

## Features Summary

### Current Features
- **Deck Browser**: View all decks with card artwork backgrounds
- **Deck Details**: Click deck cards to see full deck information
- **Card Gallery**: View all cards in a deck as an image gallery with full card images
- **Card Editor**: Edit all card properties via web interface
- **Filtering**: Filter decks by completion status
- **Partner Commanders**: Automatic diagonal split images for partner commanders
- **Settings Management**: Configure paths and manage common tokens
- **Token Management**: Add and delete common token definitions

### Planned Features
- Generate card images from web interface
- Live preview while editing cards
- Batch operations (render all cards, export deck)
- Export to Cockatrice directly from UI
- Image gallery viewer
- Deck creation and management

For the complete development roadmap, see [REFACTORING_PLAN.md](REFACTORING_PLAN.md).
