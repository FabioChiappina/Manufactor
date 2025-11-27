"""
CLI tool for building MTG decks.

Uses the services layer to load decks, generate images, and export to Cockatrice.
"""

import argparse

from src.services.deck_manager import DeckManager
from src.services.image_generator import ImageGenerator
from src.services.cockatrice_exporter import CockatriceExporter


def progress_callback(current: int, total: int, card_name: str):
    """
    Callback function for image generation progress.

    Args:
        current: Current card number being processed
        total: Total number of cards to process
        card_name: Name of the card being processed
    """
    print(f"Building image for card {current} of {total}: {card_name}")


def main():
    """Main entry point for the deck building CLI."""
    parser = argparse.ArgumentParser(description='MTG Custom Card Builder')
    parser.add_argument(
        '-d', '--deck',
        help='Name of Commander / Deck',
        type=str,
        default='Test',
        dest='deck'
    )
    parser.add_argument(
        '-t', '--automatic-tokens',
        help='1 if _Tokens.json should be generated automatically',
        type=int,
        default=True,
        dest='automatic_tokens'
    )
    args = parser.parse_args()

    # Initialize services
    deck_manager = DeckManager()
    image_generator = ImageGenerator()
    cockatrice_exporter = CockatriceExporter()

    # Normalize deck name (capitalize each word)
    deck_name = ' '.join(word[0].upper() + word[1:] for word in args.deck.split())
    print(f"BUILDING DECK: {deck_name}\n")

    # Create deck folder structure if needed
    deck_manager.create_deck_folder(deck_name)

    # Load deck from folder
    try:
        deck = deck_manager.load_deck_from_folder(deck_name)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    # Print deck statistics
    print("Deck Statistics:")
    print("-" * 50)
    deck_manager.print_deck_summaries(deck)
    print("-" * 50)
    print()

    # Generate images with progress callback
    print("Generating card images...")
    cards_generated, tokens_generated = image_generator.generate_deck_images(
        deck,
        automatic_tokens=bool(args.automatic_tokens),
        progress_callback=progress_callback
    )

    print(f"\nSuccessfully generated {cards_generated} card(s) and {tokens_generated} token(s)")

    # Export to Cockatrice (skip for Test deck)
    if deck.name != "Test":
        print("\nExporting to Cockatrice...")
        if cockatrice_exporter.is_cockatrice_available():
            try:
                success = cockatrice_exporter.export_deck(deck)
                if success:
                    print("Successfully exported to Cockatrice")
                else:
                    print("Warning: Failed to export to Cockatrice")
            except Exception as e:
                print(f"Error during Cockatrice export: {e}")
        else:
            print("Warning: Cockatrice not properly configured. Skipping export.")
            errors = cockatrice_exporter.validate_export_paths()
            for error in errors:
                print(f"  - {error}")

    print("\nDeck building complete!")
    return 0


if __name__ == '__main__':
    exit(main())