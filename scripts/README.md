# Scripts

This directory contains utility scripts for Manufactor.

## migrate_deck_to_new_format.py

Migrates deck JSON files from the old format to the new format with:
- Metadata section (deck info, commander, format, etc.)
- Front/back structure for all cards (including single-faced cards)
- Double-faced cards consolidated into single entries with "Front Name / Back Name" keys
- Tokens section with full definitions
- Basic lands as regular cards with `quantity` field

### Usage

```bash
python3 scripts/migrate_deck_to_new_format.py <deck_folder_path> [options]
```

### Options

- `--format <format>` - Deck format (Commander, Modern, etc.)
- `--description <text>` - Deck description
- `--setname <code>` - Default set code for cards (e.g., "RCH", "ANK")
- `--extract-tokens` - Extract and add token definitions from card rules text

### Example

```bash
python3 scripts/migrate_deck_to_new_format.py \
  /path/to/Decks/Richtofen \
  --format Commander \
  --description "Zombie tribal deck" \
  --setname RCH \
  --extract-tokens
```

### What it does

1. Loads main deck JSON and tokens JSON (if present)
2. Converts `_BASICS` to regular cards with `quantity` field
3. Consolidates double-faced cards (transform/MDFC) into single entries
4. Ensures all cards have `front` field for consistency
5. Combines all tokens into unified `tokens` section
6. Creates metadata section with deck information
7. Creates backups of original files
8. Saves migrated deck to new format

### Notes

- Creates backups with `_backup_old_format.json` suffix
- Handles both old format (flat card dict) and new format (already migrated)
- Automatically extracts common tokens (Treasure, Food, Clue, etc.) when `--extract-tokens` is used
- Safe to run multiple times (detects already-migrated cards)

See [docs/DOUBLE_FACED_CARDS.md](../docs/DOUBLE_FACED_CARDS.md) for details on the new format.
