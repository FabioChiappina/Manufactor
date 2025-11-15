# Double-Faced Cards

## Overview

This document describes how double-faced cards (DFCs) work in Manufactor, including transform cards and modal double-faced cards (MDFCs).

Double-faced cards are represented as a single JSON entry with nested `front` and `back` objects.

## JSON Format

### Double-Faced Card

```json
{
  "Front Name / Back Name": {
    "front": {
      "name": "Front Name",
      "mana": "{3}{B}",
      "cardtype": "Creature",
      "subtype": "Human",
      "power": "2",
      "toughness": "3",
      "rules": "Front face rules text",
      "legendary": 1
    },
    "back": {
      "name": "Back Name",
      "mana": "",
      "cardtype": "Enchantment",
      "rules": "Back face rules text",
      "legendary": 1
    },
    "double_faced_type": "transform",
    "quantity": 1,
    "complete": 1,
    "rarity": "rare",
    "colors": ["b"],
    "tags": ["Tribal"],
    "setname": "SET"
  }
}
```

### Single-Faced Card

For comparison, single-faced cards also use the `front` structure:

```json
{
  "Card Name": {
    "front": {
      "name": "Card Name",
      "mana": "{2}{U}",
      "cardtype": "Instant",
      "rules": "Draw two cards"
    },
    "quantity": 4,
    "complete": 1,
    "rarity": "common"
  }
}
```

### Key Features

1. **Top-level JSON key**: Uses format `"Front Name / Back Name"` for double-faced cards
2. **Shared fields at top level**:
   - `double_faced_type`: `"transform"` or `"mdfc"`
   - `quantity`, `complete`, `real`, `rarity`, `colors`, `tags`
   - `artwork`, `artist`, `setname`

3. **Face-specific fields in `front` and `back` objects**:
   - `name` (required for both faces)
   - `mana`, `cardtype`, `subtype`
   - `power`, `toughness`
   - `rules`, `rules1`-`rules6`, `flavor`
   - `related_indicator`
   - `legendary`, `basic`, `snow`

### Code Architecture

#### CardFace Class

New class in [`src/core/card.py`](../src/core/card.py) representing a single face:

```python
class CardFace:
    def __init__(
        self,
        name: str,
        mana: Optional[str] = None,
        cardtype: Optional[str] = None,
        # ... other face-specific fields
    )
```

#### Card Class Updates

Added new fields to [`src/core/card.py`](../src/core/card.py):

```python
class Card:
    # ... existing fields ...

    # New structure for double-faced cards
    front: Optional[CardFace] = None
    back: Optional[CardFace] = None
    double_faced_type: Optional[str] = None  # "transform" | "mdfc" | None
```

For double-faced cards:
- `card.front` contains the front face CardFace object
- `card.back` contains the back face CardFace object
- `card.double_faced_type` is `"transform"` or `"mdfc"`
- Traditional fields (`card.name`, `card.mana`, etc.) are populated from the front face for backward compatibility

For single-faced cards:
- `card.front` and `card.back` are `None`
- Traditional fields work as before

#### Deck Class Updates

Updated [`src/core/deck.py`](../src/core/deck.py):

**`_from_json_new_format()`**: Detects and loads double-faced cards with front/back structure
- Creates CardFace objects for front and back
- Populates both new CardFace fields and legacy Card fields

**`to_json()`**: Exports double-faced cards using `"Front Name / Back Name"` keys
- Uses `card.front.to_dict()` and `card.back.to_dict()` for face data
- Includes shared fields at top level

### Backward Compatibility

The implementation maintains full backward compatibility:

1. **Loading old format**: Existing decks with separate front/back entries still load correctly
2. **Single-faced cards**: Continue to work exactly as before
3. **Rendering**: Existing rendering code continues to work (uses legacy Card fields)
4. **Statistics**: Existing deck statistics work (no back faces to filter out)

### Creating New Double-Faced Cards

When creating double-faced cards, use the "Front Name / Back Name" key format with nested `front` and `back` objects:

```json
{
  "metadata": { ... },
  "cards": {
    "Transform Front / Transform Back": {
      "front": { "name": "Transform Front", ... },
      "back": { "name": "Transform Back", ... },
      "double_faced_type": "transform",
      ...
    }
  },
  "tokens": {}
}
```

## Commander Field

The `commander` field in metadata supports both single and multiple commanders:

**Single Commander:**
```json
{
  "metadata": {
    "commander": "Anakin Skywalker, Chosen One / Darth Vader, Fallen Hero",
    ...
  }
}
```

**Multiple Commanders (Partners, etc.):**
```json
{
  "metadata": {
    "commander": [
      "Tymna the Weaver",
      "Thrasios, Triton Hero"
    ],
    ...
  }
}
```

**Notes:**
- For double-faced commanders, use the full "Front Name / Back Name" format
- The commander name(s) must match card key(s) in the `cards` section
- Internally, commanders are stored as a list; single commanders are exported as strings for simplicity

## Benefits for Web UI

The new structure is ideal for the planned web UI:

1. **Single card entity**: One JSON entry = one physical card
2. **Easy face switching**: Toggle between `card.front` and `card.back` for editing
3. **Natural workflow**: Click button to make card double-faced, flip to edit either face
4. **Deck view**: Show `card.front` by default, add flip button for double-faced cards
5. **Type safety**: CardFace class provides clear structure for form inputs
6. **Multiple commanders**: Support for partner commanders and other multi-commander formats

## Technical Details

### CardFace Methods

- `CardFace.to_dict()`: Serializes face to JSON dictionary
- CardFace handles its own supertype parsing (legendary, basic, snow)
- CardFace uses Card static methods for validation

### Card Properties

For double-faced cards where `card.front` exists:
- Legacy fields (`card.name`, `card.mana`, etc.) reference front face values
- This ensures existing code continues to work unchanged
- New code should use `card.front` and `card.back` for explicit face access

### Deck Loading Logic

```python
if "front" in card_data and "back" in card_data:
    # New double-faced structure
    front_face = CardFace(**card_data["front"])
    back_face = CardFace(**card_data["back"])

    card = Card(...)  # Populate from front for compatibility
    card.front = front_face
    card.back = back_face
    card.double_faced_type = card_data.get("double_faced_type")
else:
    # Single-faced card
    card = Card(...)
```
