"""
Generic migration script for converting old format deck JSONs to new format.

Usage:
    python3 migrate_deck_to_new_format.py <deck_folder_or_json_path> [options]

Examples:
    # Migrate from deck folder (auto-finds DeckName.json)
    python3 migrate_deck_to_new_format.py /path/to/Decks/MyDeck

    # Migrate from specific JSON file
    python3 migrate_deck_to_new_format.py /path/to/Decks/MyDeck/MyDeck.json

    # Specify output location
    python3 migrate_deck_to_new_format.py /path/to/Decks/MyDeck --output MyDeck_new.json

    # Specify metadata
    python3 migrate_deck_to_new_format.py /path/to/Decks/MyDeck --format Commander --description "My deck"

Features:
- Converts old flat JSON format to new metadata/cards/tokens structure
- Merges separate deck and tokens JSONs into single file
- Converts double-faced cards to front/back structure
- Converts _BASICS to regular land cards with quantity
- Converts tokens with source_cards tracking
- Optionally runs token extraction to add common tokens
- Creates backup of original files
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

def find_deck_files(deck_path: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Find main deck JSON and optional tokens JSON.

    Args:
        deck_path: Path to deck folder or JSON file

    Returns:
        Tuple of (main_json_path, tokens_json_path, deck_name)
    """
    path = Path(deck_path)

    # If path is a JSON file
    if path.is_file() and path.suffix == '.json':
        main_json = str(path)
        deck_name = path.stem
        deck_folder = path.parent

        # Look for tokens file
        tokens_json = deck_folder / f"{deck_name}_Tokens.json"
        if tokens_json.exists():
            return main_json, str(tokens_json), deck_name
        else:
            return main_json, None, deck_name

    # If path is a folder
    elif path.is_dir():
        deck_name = path.name

        # Look for DeckName.json
        main_json = path / f"{deck_name}.json"
        if not main_json.exists():
            return None, None, deck_name

        # Look for tokens file
        tokens_json = path / f"{deck_name}_Tokens.json"
        if tokens_json.exists():
            return str(main_json), str(tokens_json), deck_name
        else:
            return str(main_json), None, deck_name

    else:
        return None, None, ""


def migrate_deck(
    main_json_path: str,
    tokens_json_path: Optional[str] = None,
    output_path: Optional[str] = None,
    deck_name: Optional[str] = None,
    description: Optional[str] = None,
    format_name: Optional[str] = None,
    author: Optional[str] = None,
    tags: Optional[List[str]] = None,
    commander: Optional[str] = None,
    setname: Optional[str] = None,
    backup: bool = True,
    extract_tokens: bool = False
) -> Dict[str, Any]:
    """
    Migrate a deck from old format to new format.

    Args:
        main_json_path: Path to main deck JSON file
        tokens_json_path: Optional path to tokens JSON file
        output_path: Optional output path (defaults to overwriting main_json_path)
        deck_name: Deck name for metadata (defaults to filename)
        description: Deck description
        format_name: Deck format (e.g., "Commander", "Modern")
        author: Deck author
        tags: List of deck tags
        commander: Commander card name (for Commander format)
        setname: Default set code for cards
        backup: Whether to create backup of original files
        extract_tokens: Whether to run token extraction after migration

    Returns:
        Migrated deck data dictionary
    """
    print("=" * 70)
    print("DECK MIGRATION TO NEW FORMAT")
    print("=" * 70)

    # Determine deck name
    if deck_name is None:
        deck_name = Path(main_json_path).stem

    # Determine output path
    if output_path is None:
        output_path = main_json_path

    # Load main deck JSON
    print(f"\n1. Loading main deck JSON: {main_json_path}")
    with open(main_json_path, 'r') as f:
        main_data = json.load(f)

    # Check if already in new format
    if "metadata" in main_data and "cards" in main_data:
        print("  ⚠ Deck appears to already be in new format (has metadata section)")
        print("  Proceeding anyway - will preserve existing metadata where possible")
        cards_data = main_data.get("cards", {})
        existing_metadata = main_data.get("metadata", {})
        existing_tokens = main_data.get("tokens", {})
    else:
        cards_data = main_data
        existing_metadata = {}
        existing_tokens = {}

    # Load tokens JSON if provided
    tokens_data = {}
    if tokens_json_path and os.path.exists(tokens_json_path):
        print(f"2. Loading tokens JSON: {tokens_json_path}")
        with open(tokens_json_path, 'r') as f:
            tokens_data = json.load(f)
    else:
        print("2. No separate tokens JSON found (will use tokens from main JSON)")
        tokens_data = existing_tokens

    # Process cards
    print("\n3. Processing cards...")

    transform_pairs = {}
    single_faced_cards = {}
    processed_cards = set()
    basic_lands = {}

    for card_name, card_data in list(cards_data.items()):
        if card_name in processed_cards:
            continue

        # Handle _BASICS (convert to regular cards)
        if card_name.upper() == "_BASICS":
            print(f"  Converting _BASICS to regular land cards...")
            for land_name, quantity in card_data.items():
                basic_lands[land_name.capitalize()] = quantity
            processed_cards.add(card_name)
            continue

        # Skip _COMMON_TOKENS
        if card_name.upper() == "_COMMON_TOKENS":
            print(f"  Skipping _COMMON_TOKENS (tokens will be in tokens section)")
            processed_cards.add(card_name)
            continue

        # Check if card is already in new format (has front field)
        if "front" in card_data:
            # Already in new format - copy as-is
            if "back" in card_data:
                # Double-faced card already in new format
                transform_pairs[card_name] = {
                    "front": card_data["front"],
                    "front_name": card_data["front"]["name"],
                    "back": card_data["back"],
                    "back_name": card_data["back"]["name"],
                    "dfc_type": card_data.get("double_faced_type", "transform"),
                    "shared_fields": {k: v for k, v in card_data.items() if k not in ["front", "back", "double_faced_type"]}
                }
                processed_cards.add(card_name)
                print(f"  Already in new format (DFC): {card_name}")
            else:
                # Single-faced card already in new format
                single_faced_cards[card_name] = card_data
                processed_cards.add(card_name)
            continue

        # Check for double-faced cards in old format
        special = card_data.get("special", "")

        if "transform" in special.lower() or "mdfc" in special.lower():
            # Double-faced card
            related = card_data.get("related")
            dfc_type = "mdfc" if "mdfc" in special.lower() else "transform"

            if "front" in special.lower():
                # Front face - find its back
                back_name = related
                if back_name and back_name in cards_data:
                    pair_key = f"{card_name}:{back_name}"
                    transform_pairs[pair_key] = {
                        "front": card_data,
                        "front_name": card_name,
                        "back": cards_data[back_name],
                        "back_name": back_name,
                        "dfc_type": dfc_type
                    }
                    processed_cards.add(card_name)
                    processed_cards.add(back_name)
                    print(f"  Found {dfc_type} pair: {card_name} / {back_name}")
                else:
                    print(f"  Warning: Front face '{card_name}' missing back '{related}'")
                    single_faced_cards[card_name] = card_data
            elif "back" in special.lower():
                # Back face - check if already processed
                if card_name not in processed_cards:
                    print(f"  Warning: Back face '{card_name}' has no front")
                    single_faced_cards[card_name] = card_data
        else:
            # Single-faced card
            single_faced_cards[card_name] = card_data
            processed_cards.add(card_name)

    print(f"\n  Summary:")
    print(f"    - Single-faced cards: {len(single_faced_cards)}")
    print(f"    - Double-faced pairs: {len(transform_pairs)}")
    print(f"    - Basic lands: {len(basic_lands)}")

    # Build new cards section
    print("\n4. Building new cards section...")
    new_cards = {}

    # Add single-faced cards (with front field for consistency)
    for card_name, card_data in single_faced_cards.items():
        # Face-specific fields go in "front"
        front_dict = {"name": card_name}

        for field in ["mana", "cardtype", "subtype", "power", "toughness",
                     "rules", "rules1", "rules2", "rules3", "rules4", "rules5", "rules6",
                     "flavor", "legendary", "basic", "snow"]:
            if field in card_data:
                front_dict[field] = card_data[field]

        # Shared card-level fields at top level
        new_card = {"front": front_dict}

        for field in ["quantity", "complete", "real", "rarity", "colors", "tags",
                     "artwork", "artist", "setname", "token"]:
            if field in card_data:
                new_card[field] = card_data[field]

        new_cards[card_name] = new_card

    # Add double-faced pairs in new format
    for pair_key, pair_data in transform_pairs.items():
        front_card = pair_data["front"]
        back_card = pair_data["back"]
        front_name = pair_data["front_name"]
        back_name = pair_data["back_name"]
        dfc_type = pair_data["dfc_type"]

        dfc_key = f"{front_name} / {back_name}"

        # Check if this was already in new format (has shared_fields)
        if "shared_fields" in pair_data:
            # Already in new format - use as-is
            dfc_data = {
                "front": front_card,
                "back": back_card,
                "double_faced_type": dfc_type,
            }
            # Add shared fields
            dfc_data.update(pair_data["shared_fields"])
        else:
            # Converting from old format
            dfc_data = {
                "front": {"name": front_name},
                "back": {"name": back_name},
                "double_faced_type": dfc_type,
            }

            # Shared fields from front card
            for field in ["quantity", "complete", "real", "rarity", "colors", "tags", "artwork", "artist", "setname"]:
                if field in front_card:
                    dfc_data[field] = front_card[field]

            # Front face-specific fields
            for field in ["mana", "cardtype", "subtype", "power", "toughness",
                         "rules", "rules1", "rules2", "rules3", "rules4", "rules5", "rules6",
                         "flavor", "related_indicator", "legendary", "basic", "snow"]:
                if field in front_card:
                    dfc_data["front"][field] = front_card[field]

            # Back face-specific fields
            for field in ["mana", "cardtype", "subtype", "power", "toughness",
                         "rules", "rules1", "rules2", "rules3", "rules4", "rules5", "rules6",
                         "flavor", "related_indicator", "legendary", "basic", "snow"]:
                if field in back_card:
                    dfc_data["back"][field] = back_card[field]

        new_cards[dfc_key] = dfc_data

    # Add basic lands as regular cards (with front field for consistency)
    for land_name, quantity in basic_lands.items():
        new_cards[land_name] = {
            "front": {
                "name": land_name,
                "cardtype": "Land",
                "subtype": land_name,
                "basic": 1
            },
            "quantity": quantity,
            "complete": 1,
            "real": 1
        }

    print(f"  Total cards in new format: {len(new_cards)}")

    # Process tokens
    print("\n5. Processing tokens...")
    new_tokens = {}

    for token_key, token_data in tokens_data.items():
        if token_key.upper() == "_COMMON_TOKENS":
            # Skip - these will be extracted if extract_tokens is True
            continue

        # Convert 'related' field to 'source_cards'
        source_cards = token_data.get("related", token_data.get("source_cards", []))
        if isinstance(source_cards, str):
            source_cards = [source_cards]

        new_token = {
            "name": token_data.get("name", token_key),
            "cardtype": token_data.get("cardtype", "Token"),
            "token": 1,
            "quantity": 1,
            "complete": token_data.get("complete", 1),
            "source_cards": source_cards
        }

        # Add optional fields
        for field in ["subtype", "power", "toughness", "rules", "colors", "frame", "mana"]:
            if field in token_data:
                new_token[field] = token_data[field]

        new_tokens[token_key] = new_token

    print(f"  Total tokens: {len(new_tokens)}")

    # Build metadata
    print("\n6. Building metadata...")
    folder_name = Path(main_json_path).parent.name

    metadata = {
        "folder_name": existing_metadata.get("folder_name", folder_name),
        "deck_name": deck_name if deck_name else existing_metadata.get("deck_name", folder_name),
        "description": description if description else existing_metadata.get("description", ""),
        "format": format_name if format_name else existing_metadata.get("format", ""),
        "author": author if author else existing_metadata.get("author", ""),
        "tags": tags if tags else existing_metadata.get("tags", []),
        "commander": commander if commander else existing_metadata.get("commander"),
        "setname": setname if setname else existing_metadata.get("setname", "")
    }

    # Build final structure
    output_data = {
        "metadata": metadata,
        "cards": new_cards,
        "tokens": new_tokens
    }

    # Create backup if requested
    if backup and os.path.exists(output_path):
        backup_path = output_path.replace('.json', '_backup_old_format.json')
        print(f"\n7. Creating backup: {backup_path}")
        with open(backup_path, 'w') as f:
            json.dump(main_data, f, indent=2)

        # Backup tokens file if it exists
        if tokens_json_path and os.path.exists(tokens_json_path):
            tokens_backup = tokens_json_path.replace('.json', '_backup.json')
            print(f"   Creating tokens backup: {tokens_backup}")
            with open(tokens_backup, 'w') as f:
                json.dump(tokens_data, f, indent=2)

    # Save migrated deck
    print(f"\n8. Saving migrated deck: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✓ Migration complete!")
    print(f"  Output: {output_path}")
    print(f"  - Cards: {len(new_cards)}")
    print(f"  - Tokens: {len(new_tokens)}")

    # Summary stats
    dfc_count = sum(1 for v in new_cards.values() if "front" in v and "back" in v)
    single_count = len(new_cards) - dfc_count

    print(f"\n  Card breakdown:")
    print(f"    - Single-faced: {single_count}")
    print(f"    - Double-faced: {dfc_count}")
    print(f"    - Basic lands: {len(basic_lands)}")

    # Extract common tokens if requested
    if extract_tokens:
        print("\n9. Extracting common tokens from card rules text...")
        try:
            # Add project to path
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from src.core.deck import Deck

            # Load the migrated deck
            deck = Deck.from_json(output_path, setname=metadata.get("setname", ""), deck_name=deck_name)

            # Run token extraction
            specialized, common = deck.get_tokens(save_to_deck=True, save_legacy_file=False)
            print(f"  Found {len(specialized)} specialized tokens, {len(common)} common tokens")

            # Save deck with tokens
            deck.to_json(output_path, use_new_format=True)
            print(f"  Updated deck saved with extracted tokens")

        except Exception as e:
            print(f"  ⚠ Warning: Could not extract tokens: {e}")
            print(f"  You can run token extraction manually later")

    print("\n" + "=" * 70)

    return output_data


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate old format deck JSON to new format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate from deck folder
  python3 migrate_deck_to_new_format.py /path/to/Decks/MyDeck

  # Migrate with metadata
  python3 migrate_deck_to_new_format.py /path/to/Decks/MyDeck \\
      --format Commander \\
      --description "Zombie tribal deck" \\
      --commander "Wilhelt, the Rotcleaver" \\
      --setname MH2

  # Migrate and extract tokens
  python3 migrate_deck_to_new_format.py /path/to/Decks/MyDeck --extract-tokens
        """
    )

    parser.add_argument("deck_path", help="Path to deck folder or JSON file")
    parser.add_argument("--output", "-o", help="Output JSON path (default: overwrites input)")
    parser.add_argument("--deck-name", help="Deck name for metadata")
    parser.add_argument("--description", "-d", help="Deck description")
    parser.add_argument("--format", "-f", dest="format_name", help="Deck format (e.g., Commander, Modern)")
    parser.add_argument("--author", "-a", help="Deck author")
    parser.add_argument("--tags", "-t", nargs="+", help="Deck tags")
    parser.add_argument("--commander", "-c", help="Commander card name")
    parser.add_argument("--setname", "-s", help="Default set code for cards")
    parser.add_argument("--no-backup", action="store_true", help="Don't create backup of original files")
    parser.add_argument("--extract-tokens", action="store_true", help="Run token extraction after migration")

    args = parser.parse_args()

    # Find deck files
    main_json, tokens_json, deck_name = find_deck_files(args.deck_path)

    if main_json is None:
        print(f"Error: Could not find deck JSON at {args.deck_path}")
        sys.exit(1)

    # Use provided deck name or detected name
    final_deck_name = args.deck_name if args.deck_name else deck_name

    # Run migration
    try:
        migrate_deck(
            main_json_path=main_json,
            tokens_json_path=tokens_json,
            output_path=args.output,
            deck_name=final_deck_name,
            description=args.description,
            format_name=args.format_name,
            author=args.author,
            tags=args.tags,
            commander=args.commander,
            setname=args.setname,
            backup=not args.no_backup,
            extract_tokens=args.extract_tokens
        )
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
