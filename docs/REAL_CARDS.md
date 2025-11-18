# Real MTG Cards Integration

## Overview

Manufactor supports mixing real Magic: The Gathering cards with custom cards in the same deck. This document explains how to mark cards as "real" and how to handle their images in both the build process and future UI implementations.

## Purpose

You may want to create decks that include:
- **Custom cards** - Your own designs with custom artwork
- **Real cards** - Official MTG cards from existing sets

The goal is to support viewing both types together in a UI, with the ability to filter and distinguish between them.

---

## Marking Cards as Real

### In Deck JSON

Add `"real": 1` to any card object to mark it as a real MTG card:

```json
{
  "cards": {
    "Lightning Bolt": {
      "name": "Lightning Bolt",
      "mana": "{r}",
      "cardtype": "Instant",
      "rules": "Lightning Bolt deals 3 damage to any target.",
      "rarity": "common",
      "real": 1,
      "complete": 1,
      "quantity": 4
    },
    "My Custom Card": {
      "name": "My Custom Card",
      "mana": "{2}{u}",
      "cardtype": "Creature",
      "subtype": "Wizard",
      "power": "2",
      "toughness": "2",
      "real": 0,
      "complete": 0,
      "quantity": 1
    }
  }
}
```

### Field Details

- `"real": 1` - This is a real MTG card
- `"real": 0` - This is a custom card (default if field is omitted)

The `real` field is already implemented in:
- [src/core/card.py:445](../src/core/card.py#L445)
- [src/core/deck.py:151-152](../src/core/deck.py#L151-L152)

---

## Current Folder Structure

The existing folder structure works perfectly for mixed decks:

```
Decks/
└── MyDeck/
    ├── MyDeck.json              # Contains both real and custom cards
    ├── Cards/                   # Generated images for custom cards only
    │   └── My Custom Card.jpg
    ├── Artwork/                 # Source artwork for custom cards
    │   └── My Custom Card.jpg
    ├── Printing/                # Print-ready versions (custom cards)
    │   └── My Custom Card.jpg
    └── Tokens/                  # Generated token images
        └── Treasure.jpg
```

**Important**: Do NOT create separate `RealCards/` or `CustomCards/` folders. The `real` field provides all the metadata needed to distinguish card types.

---

## Build Process Behavior

### Current Implementation

When running `python3 -m src.cli.build_deck --deck "DeckName"`:

1. **All cards** (real and custom) are processed
2. Image generation occurs for cards where `complete != 1`
3. Real cards with `complete == 1` are skipped (no image generated)

### Recommended: Skip Image Generation for Real Cards

Real MTG cards don't need custom images generated. To handle them properly:

1. Set `"complete": 1` for all real cards (prevents image generation attempts)
2. Don't add artwork files for real cards to `Artwork/` folder
3. Real card images will be fetched from external sources in the UI

**Example workflow:**
```bash
# Build a mixed deck
python3 -m src.cli.build_deck --deck "MyMixedDeck"

# Only custom cards (real: 0) will have images generated
# Real cards (real: 1) are skipped
```

---

## UI Implementation Strategy

### Recommended Approach: Scryfall API Integration

When you build the UI, fetch real card images on-demand from Scryfall API rather than storing them locally.

#### Why Scryfall?

- **Free API** - No authentication required for basic image fetching
- **High-quality images** - Multiple sizes and formats available
- **Always up-to-date** - Latest card art and errata
- **No storage needed** - Saves disk space
- **API Documentation**: https://scryfall.com/docs/api

#### Scryfall Image Endpoints

```
# Get card by exact name
https://api.scryfall.com/cards/named?exact={card_name}

# Get card image directly
https://api.scryfall.com/cards/named?exact={card_name}&format=image

# Different image sizes
&version=small      # 146 x 204
&version=normal     # 488 x 680 (default)
&version=large      # 672 x 936
&version=png        # Full resolution PNG
&version=art_crop   # Just the artwork
```

#### Example Implementation (Pseudocode)

```python
from src.core.deck import Deck
import requests
from pathlib import Path

class CardImageProvider:
    """Provides card images for both real and custom cards."""

    def __init__(self, deck_name: str):
        self.deck = Deck.from_deck_folder(deck_name)
        self.deck_path = Path(f"Decks/{deck_name}")
        self.cache_path = Path("cache/real_cards")  # Optional: local cache
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def get_card_image_path(self, card) -> str:
        """Returns path to card image (local or URL)."""
        if card.real:
            return self._get_real_card_image(card.name)
        else:
            return self._get_custom_card_image(card.name)

    def _get_custom_card_image(self, card_name: str) -> str:
        """Returns path to locally generated custom card image."""
        return str(self.deck_path / "Cards" / f"{card_name}.jpg")

    def _get_real_card_image(self, card_name: str) -> str:
        """Returns URL or cached path for real MTG card."""
        # Option A: Return Scryfall URL directly (recommended)
        return f"https://api.scryfall.com/cards/named?exact={card_name}&format=image&version=normal"

        # Option B: Download and cache locally
        cache_file = self.cache_path / f"{card_name}.jpg"
        if not cache_file.exists():
            url = f"https://api.scryfall.com/cards/named?exact={card_name}&format=image"
            response = requests.get(url)
            cache_file.write_bytes(response.content)
        return str(cache_file)

    def get_all_cards_with_images(self):
        """Returns list of (card, image_path) tuples."""
        return [
            (card, self.get_card_image_path(card))
            for card in self.deck.cards
        ]

    def get_filtered_cards(self, show_real=True, show_custom=True):
        """Returns filtered list based on card type."""
        cards = []
        for card in self.deck.cards:
            if card.real and show_real:
                cards.append((card, self.get_card_image_path(card)))
            elif not card.real and show_custom:
                cards.append((card, self.get_card_image_path(card)))
        return cards


# Usage in UI
provider = CardImageProvider("MyMixedDeck")

# Show all cards
all_cards = provider.get_all_cards_with_images()

# Show only custom cards
custom_only = provider.get_filtered_cards(show_real=False, show_custom=True)

# Show only real cards
real_only = provider.get_filtered_cards(show_real=True, show_custom=False)
```

---

## UI Filtering

Your UI should provide toggle buttons to filter the deck view:

### Filter Options

1. **Show All** - Display both real and custom cards (default)
2. **Custom Only** - Filter where `card.real == 0` or `card.real is None`
3. **Real Only** - Filter where `card.real == 1`

### Example UI Controls (Pseudocode)

```python
class DeckViewer:
    def __init__(self, deck_name):
        self.provider = CardImageProvider(deck_name)
        self.show_real = True
        self.show_custom = True

    def on_show_all_clicked(self):
        self.show_real = True
        self.show_custom = True
        self.refresh_display()

    def on_show_custom_only_clicked(self):
        self.show_real = False
        self.show_custom = True
        self.refresh_display()

    def on_show_real_only_clicked(self):
        self.show_real = True
        self.show_custom = False
        self.refresh_display()

    def refresh_display(self):
        cards = self.provider.get_filtered_cards(
            show_real=self.show_real,
            show_custom=self.show_custom
        )
        # Update UI with filtered card list
        self.display_cards(cards)
```

---

## Alternative: Local Storage for Real Cards

If you need offline support or want to avoid API rate limits, you can store real card images locally.

### Shared Cache Approach

Create a **shared** cache folder at the project level (not per-deck):

```
Magic/
├── Manufactor/           # This repo
├── Decks/                # All your decks
└── RealCardsCache/       # Shared cache for all real cards
    ├── Lightning Bolt.jpg
    ├── Sol Ring.jpg
    └── Counterspell.jpg
```

### Benefits of Shared Cache

- **No duplication** - Lightning Bolt stored once, used across all decks
- **Disk space efficient** - Real cards reused across multiple decks
- **Offline support** - Works without internet after initial download
- **Fast loading** - No API calls needed

### Cache Implementation

```python
class RealCardCache:
    """Manages a shared cache of real MTG card images."""

    def __init__(self, cache_dir: str = "../RealCardsCache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_card_image(self, card_name: str) -> str:
        """Returns path to cached card image, downloading if needed."""
        cache_file = self.cache_dir / f"{card_name}.jpg"

        if not cache_file.exists():
            print(f"Downloading {card_name} from Scryfall...")
            self._download_from_scryfall(card_name, cache_file)

        return str(cache_file)

    def _download_from_scryfall(self, card_name: str, save_path: Path):
        """Downloads card image from Scryfall API."""
        import requests
        url = f"https://api.scryfall.com/cards/named"
        params = {
            "exact": card_name,
            "format": "image",
            "version": "normal"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        save_path.write_bytes(response.content)

    def clear_cache(self):
        """Removes all cached images."""
        for file in self.cache_dir.glob("*.jpg"):
            file.unlink()

    def cache_size(self) -> int:
        """Returns number of cached cards."""
        return len(list(self.cache_dir.glob("*.jpg")))
```

---

## Implementation Checklist

When building your UI, use this checklist:

### Phase 1: Basic Support
- [ ] Read `real` field from deck JSON
- [ ] Display custom card images from `Cards/` folder
- [ ] Fetch real card images from Scryfall API (or cache)
- [ ] Show both types in a unified list

### Phase 2: Filtering
- [ ] Add "Show All" button (default)
- [ ] Add "Custom Only" toggle
- [ ] Add "Real Only" toggle
- [ ] Update card display based on filter state

### Phase 3: Enhanced Features (Optional)
- [ ] Implement local cache for real cards
- [ ] Add cache management (clear cache, view cache size)
- [ ] Show visual indicator for real vs custom cards
- [ ] Add statistics (e.g., "42 custom, 58 real")
- [ ] Support exporting deck with only custom/real cards

---

## API Rate Limiting

### Scryfall API Limits

- **Rate limit**: ~10 requests per second
- **Best practice**: Add 50-100ms delay between requests
- **Bulk downloads**: Use Scryfall's bulk data if downloading many cards

### Example Rate-Limited Fetcher

```python
import time
import requests

class ScryfalFetcher:
    def __init__(self, delay_ms: int = 100):
        self.delay = delay_ms / 1000  # Convert to seconds
        self.last_request_time = 0

    def fetch_card_image(self, card_name: str) -> bytes:
        """Fetch card image with rate limiting."""
        # Enforce delay between requests
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

        url = f"https://api.scryfall.com/cards/named"
        params = {"exact": card_name, "format": "image"}
        response = requests.get(url, params=params)
        response.raise_for_status()

        self.last_request_time = time.time()
        return response.content
```

---

## Summary

### Key Points

1. **Use the `real` field** - Already implemented, no schema changes needed
2. **Keep current folder structure** - `Cards/`, `Artwork/`, `Printing/` work for mixed decks
3. **Don't generate images for real cards** - Fetch from Scryfall instead
4. **Fetch on-demand** - Recommended approach for UI
5. **Optional local cache** - Use shared folder if offline support needed
6. **UI filtering** - Simple boolean checks on `card.real` field

### Related Files

- Card class: [src/core/card.py](../src/core/card.py)
- Deck class: [src/core/deck.py](../src/core/deck.py)
- JSON format docs: [JSON_FORMAT.md](JSON_FORMAT.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Future Enhancements

Consider these features for future versions:

1. **CLI flag**: `--fetch-real-cards` to download real card images during build
2. **Scryfall integration service**: `src/services/scryfall_fetcher.py`
3. **Cache management CLI**: `python3 -m src.cli.manage_cache --clear`
4. **Deck export options**: Export only custom cards, only real cards, or both
5. **Cockatrice integration**: Mark real cards differently in exported XML
