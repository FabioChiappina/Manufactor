# Deck JSON Format Reference

This document describes the complete JSON format for Manufactor deck files.

## Table of Contents
- [Deck Structure](#deck-structure)
- [Metadata Section](#metadata-section)
- [Cards Section](#cards-section)
  - [Single-Faced Cards](#single-faced-cards)
  - [Double-Faced Cards](#double-faced-cards)
  - [Basic Lands](#basic-lands)
- [Tokens Section](#tokens-section)
- [Complete Example](#complete-example)

---

## Deck Structure

All decks use a structured JSON format with three top-level sections:

```json
{
  "metadata": { ... },
  "cards": { ... },
  "tokens": { ... }
}
```

---

## Metadata Section

Contains deck-level information:

```json
{
  "metadata": {
    "folder_name": "DeckFolder",
    "deck_name": "Display Name",
    "description": "Deck description",
    "format": "Commander",
    "created": "2025-01-15T12:00:00Z",
    "last_modified": "2025-01-15T12:00:00Z",
    "author": "Your Name",
    "tags": ["Tribal", "Aggro"],
    "commander": "Commander Name",
    "setname": "SET"
  }
}
```

### Metadata Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| folder_name | string | Yes | Name of deck folder on filesystem |
| deck_name | string | Yes | Display name for the deck |
| description | string | No | Deck description or strategy notes |
| format | string | No | Format (Commander, Modern, Standard, etc.) |
| created | string (ISO 8601) | No | Deck creation timestamp |
| last_modified | string (ISO 8601) | No | Last modification timestamp |
| author | string | No | Deck creator name |
| tags | array of strings | No | Tags for categorization |
| commander | string or array | No | Commander name(s) - see [Commander Field](#commander-field) |
| setname | string | No | Default set code for cards (e.g., "RCH", "ANK") |

### Commander Field

The `commander` field supports both single and multiple commanders:

**Single Commander:**
```json
"commander": "Anakin Skywalker, Chosen One / Darth Vader, Fallen Hero"
```

**Multiple Commanders (Partners):**
```json
"commander": [
  "Tymna the Weaver",
  "Thrasios, Triton Hero"
]
```

**Notes:**
- For double-faced commanders, use the full "Front Name / Back Name" format
- Commander name(s) must match card key(s) in the `cards` section

---

## Cards Section

Contains all card definitions. The card name is used as the JSON key.

### Single-Faced Cards

All cards, including single-faced cards, use a consistent `front` field structure:

```json
{
  "cards": {
    "Lightning Bolt": {
      "front": {
        "name": "Lightning Bolt",
        "mana": "{r}",
        "cardtype": "Instant",
        "rules": "Lightning Bolt deals 3 damage to any target."
      },
      "quantity": 4,
      "complete": 1,
      "real": 1,
      "rarity": "common"
    }
  }
}
```

### Double-Faced Cards

Double-faced cards use the "Front Name / Back Name" format as the key:

```json
{
  "cards": {
    "Ludvig Maxis, Nightfather / The Sinister Voice In The Aether": {
      "front": {
        "name": "Ludvig Maxis, Nightfather",
        "mana": "{2}{b}",
        "cardtype": "Creature",
        "subtype": "Human Scientist",
        "power": "2",
        "toughness": "3",
        "rules": "At the beginning of your end step, if a creature died this turn, transform Ludvig Maxis.",
        "legendary": 1
      },
      "back": {
        "name": "The Sinister Voice In The Aether",
        "cardtype": "Enchantment",
        "rules": "Creatures you control get +1/+1 and have menace.",
        "legendary": 1
      },
      "double_faced_type": "transform",
      "quantity": 1,
      "complete": 1,
      "rarity": "rare"
    }
  }
}
```

### Basic Lands

Basic lands are regular cards with the `basic` field:

```json
{
  "cards": {
    "Swamp": {
      "front": {
        "name": "Swamp",
        "cardtype": "Land",
        "subtype": "Swamp",
        "basic": 1
      },
      "quantity": 13,
      "complete": 1,
      "real": 1
    }
  }
}
```

### Face Fields (front/back)

Fields that go inside `front` or `back` objects:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Card face name |
| mana | string | No | Mana cost (e.g., "{2}{u}{r}") |
| cardtype | string | Yes | Card type (Creature, Instant, Land, etc.) |
| subtype | string | No | Card subtype (e.g., "Human Wizard") |
| power | string/int | No | Power value (creatures only) |
| toughness | string/int | No | Toughness value (creatures only) |
| rules | string | No | Main rules text |
| rules1-6 | string | No | Additional rules lines (for complex cards) |
| flavor | string | No | Flavor text |
| related_indicator | string | No | Text/mana for opposite face indicator |
| legendary | int | No | 1 if legendary, 0 or omit if not |
| basic | int | No | 1 if basic, 0 or omit if not |
| snow | int | No | 1 if snow permanent, 0 or omit if not |

### Card-Level Fields

Fields that go at the card level (outside front/back):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| double_faced_type | string | For DFCs | "transform" or "mdfc" |
| quantity | int | No | Number of copies (default: 1) |
| complete | int | No | 1 if card image generated |
| real | int | No | 1 if real MTG card, 0 if custom |
| rarity | string | No | common, uncommon, rare, mythic |
| colors | array | No | Color identity (["w", "u", "b", "r", "g"]) |
| tags | array | No | Tags for categorization |
| artwork | string | No | Path to artwork file |
| artist | string | No | Artist name |
| setname | string | No | Set code override (if different from deck default) |

---

## Tokens Section

Contains token definitions:

```json
{
  "tokens": {
    "_TOKEN_Zombie": {
      "name": "Zombie",
      "cardtype": "Creature",
      "subtype": "Zombie",
      "power": "2",
      "toughness": "2",
      "rules": "Decayed (This creature can't block. When it attacks, sacrifice it at end of combat.)",
      "token": 1,
      "complete": 1,
      "source_cards": ["Ghoulish Procession", "Crawl from the Cellar"]
    },
    "_TOKEN_Treasure": {
      "name": "Treasure",
      "cardtype": "Artifact",
      "subtype": "Treasure",
      "rules": "{t}, Sacrifice this artifact: Add one mana of any color.",
      "token": 1,
      "complete": 1,
      "source_cards": ["Dockside Extortionist"]
    }
  }
}
```

### Token Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Token name |
| cardtype | string | Yes | Card type (usually Creature or Artifact) |
| subtype | string | No | Token subtype |
| power | string/int | No | Power (creature tokens) |
| toughness | string/int | No | Toughness (creature tokens) |
| rules | string | No | Token rules text |
| token | int | Yes | Always 1 for tokens |
| complete | int | No | 1 if token image generated |
| source_cards | array | No | List of cards that create this token |
| colors | array | No | Color identity |

**Note:** Token keys should start with `_TOKEN_` prefix for consistency.

---

## Complete Example

```json
{
  "metadata": {
    "folder_name": "ExampleDeck",
    "deck_name": "Example Commander Deck",
    "description": "A sample deck showing the JSON format",
    "format": "Commander",
    "created": "2025-01-15T12:00:00Z",
    "last_modified": "2025-01-15T12:00:00Z",
    "author": "Example Author",
    "tags": ["Example", "Tutorial"],
    "commander": "Example Commander",
    "setname": "EXM"
  },
  "cards": {
    "Example Commander": {
      "front": {
        "name": "Example Commander",
        "mana": "{2}{u}{r}",
        "cardtype": "Creature",
        "subtype": "Human Wizard",
        "power": "3",
        "toughness": "3",
        "rules": "Whenever you cast an instant or sorcery spell, create a Treasure token.",
        "legendary": 1
      },
      "quantity": 1,
      "complete": 1,
      "rarity": "rare"
    },
    "Lightning Bolt": {
      "front": {
        "name": "Lightning Bolt",
        "mana": "{r}",
        "cardtype": "Instant",
        "rules": "Lightning Bolt deals 3 damage to any target."
      },
      "quantity": 1,
      "complete": 1,
      "real": 1,
      "rarity": "common"
    },
    "Island": {
      "front": {
        "name": "Island",
        "cardtype": "Land",
        "subtype": "Island",
        "basic": 1
      },
      "quantity": 10,
      "complete": 1,
      "real": 1
    }
  },
  "tokens": {
    "_TOKEN_Treasure": {
      "name": "Treasure",
      "cardtype": "Artifact",
      "subtype": "Treasure",
      "rules": "{t}, Sacrifice this artifact: Add one mana of any color.",
      "token": 1,
      "complete": 1,
      "source_cards": ["Example Commander"]
    }
  }
}
```

---

## Additional Notes

### Mana Cost Format
Mana costs use curly braces for each symbol:
- `{w}` - White
- `{u}` - Blue
- `{b}` - Black
- `{r}` - Red
- `{g}` - Green
- `{c}` - Colorless
- `{x}` - Variable
- `{2}` - Generic mana (number)
- `{2/w}` - Hybrid (2 or white)
- `{w/u}` - Hybrid (white or blue)
- `{w/p}` - Phyrexian (white or 2 life)

### Color Codes
When specifying colors arrays:
- `"w"` - White
- `"u"` - Blue
- `"b"` - Black
- `"r"` - Red
- `"g"` - Green

### Auto-Parsing
The following are automatically parsed and don't require explicit specification:
- **Colors**: Derived from mana cost if not specified
- **Supertype**: Can be included in cardtype string or as separate fields (separate fields recommended)

### Migration
For migrating decks from old formats, use the migration script:
```bash
python3 scripts/migrate_deck_to_new_format.py <deck_folder> --extract-tokens
```

See [scripts/README.md](../scripts/README.md) for details.
