"""
Image generation service for MTG cards.

Provides high-level API for generating card and token images with progress tracking.
Acts as a bridge between UI and rendering layer.
"""

import os
from typing import Callable, Optional, Tuple
from src.core.deck import Deck
from src.core.card import Card
from src.core.card_set import CardSet
from src.rendering.card_renderer import create_card_image_from_Card, create_printing_image_from_Card
from src.utils.paths import DECK_PATH


class ImageGenerator:
    """
    Service for generating card images from decks.

    Handles:
    - Card image generation with progress callbacks
    - Token image generation
    - Printing image generation
    - Directory management
    """

    def __init__(self):
        """Initialize the ImageGenerator service."""
        pass

    def generate_deck_images(
        self,
        deck: Deck,
        save_path: Optional[str] = None,
        skip_complete: bool = True,
        automatic_tokens: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[int, int]:
        """
        Generate all card images for a deck.

        Args:
            deck: The deck to generate images for
            save_path: Optional custom save path (defaults to DECK_PATH/deck.name)
            skip_complete: Skip cards with complete flag set
            automatic_tokens: Regenerate token JSON before creating token images
            progress_callback: Optional callback function(current, total, card_name)

        Returns:
            Tuple of (cards_generated, tokens_generated)

        Raises:
            TypeError: If deck is not a Deck instance
        """
        if not isinstance(deck, Deck):
            raise TypeError("Input deck must be of type Deck.")

        # Setup paths
        if save_path is None:
            save_path = os.path.join(DECK_PATH, deck.name)

        # Ensure directory structure
        self._ensure_directories(save_path, deck.name)

        # Generate card images
        cards_generated = self._generate_card_images(
            deck,
            save_path,
            skip_complete,
            progress_callback
        )

        # Generate token images
        tokens_generated = 0
        if automatic_tokens:
            tokens_generated = self._generate_token_images(
                deck,
                skip_complete,
                progress_callback
            )

        return cards_generated, tokens_generated

    def generate_single_card_image(
        self,
        card: Card,
        save_path: str,
        include_printing: bool = True
    ) -> bool:
        """
        Generate image for a single card.

        Args:
            card: The card to generate an image for
            save_path: Path to save the card image
            include_printing: Also generate printing image

        Returns:
            True if successful
        """
        if not isinstance(card, Card):
            raise TypeError("Input card must be of type Card.")

        try:
            create_card_image_from_Card(card, save_path=save_path)

            if include_printing:
                printing_path = os.path.join(
                    os.path.dirname(os.path.dirname(save_path)),
                    "Printing"
                )
                create_printing_image_from_Card(
                    card,
                    saved_image_path=save_path,
                    save_path=printing_path
                )

            return True
        except Exception as e:
            print(f"Error generating image for {card.name}: {e}")
            return False

    def _ensure_directories(self, save_path: str, deck_name: str):
        """Ensure all required directories exist."""
        directories = [
            save_path,
            os.path.join(save_path, "Cards"),
            os.path.join(save_path, "Artwork"),
            os.path.join(save_path, "Printing"),
            os.path.join(save_path, "Tokens")
        ]

        for directory in directories:
            if not os.path.isdir(directory):
                os.makedirs(directory, exist_ok=True)

    def _generate_card_images(
        self,
        deck: Deck,
        save_path: str,
        skip_complete: bool,
        progress_callback: Optional[Callable]
    ) -> int:
        """Generate images for all cards in deck."""
        cards_path = os.path.join(save_path, "Cards")
        printing_path = os.path.join(save_path, "Printing")

        cards_to_create = [c for c in deck.cards if not (c.complete and skip_complete)]
        total = len(cards_to_create)

        for index, card in enumerate(cards_to_create, 1):
            if progress_callback:
                progress_callback(index, total, card.name)

            create_card_image_from_Card(card, save_path=cards_path)
            create_printing_image_from_Card(
                card,
                saved_image_path=cards_path,
                save_path=printing_path
            )

        return total

    def _generate_token_images(
        self,
        deck: Deck,
        skip_complete: bool,
        progress_callback: Optional[Callable]
    ) -> int:
        """Generate images for all tokens in deck."""
        # Generate token JSON
        deck.get_tokens()

        try:
            # Load tokens deck
            setname = (deck.name.lower().replace("the ", ""))[0:3].upper()
            setname = CardSet.adjust_forbidden_custom_setname(setname)

            tokens_deck = Deck.from_json(
                os.path.join(DECK_PATH, deck.name, deck.name + '_Tokens.json'),
                setname,
                deck.name + "_Tokens"
            )

            tokens_path = os.path.join(DECK_PATH, deck.name, "Tokens")
            printing_path = os.path.join(DECK_PATH, deck.name, "Printing")

            tokens_to_create = [c for c in tokens_deck.cards if not (c.complete and skip_complete)]
            total = len(tokens_to_create)

            for index, card in enumerate(tokens_to_create, 1):
                if progress_callback:
                    progress_callback(index, total, f"Token: {card.name}")

                create_card_image_from_Card(card, save_path=tokens_path)
                create_printing_image_from_Card(
                    card,
                    saved_image_path=tokens_path,
                    save_path=printing_path
                )

            return total
        except Exception as e:
            # No tokens or error loading tokens
            return 0
