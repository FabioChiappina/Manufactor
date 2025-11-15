# Subspells (Adventure/Omen Cards)

## Overview

Subspells are mini-spells embedded within a card's front face, similar to Adventures and Omens in Magic: The Gathering. A card can have a subspell that functions as a separate castable spell while still being part of the same physical card.

**Examples from MTG:**
- Beanstalk Giant / Fertile Footsteps (Adventure)
- Bonecrusher Giant / Stomp (Adventure)
- Virtue of Courage / Embereth (Omen - Wilds of Eldraine)

## JSON Format

Subspells use a structure parallel to `front` and `back` fields. The card's JSON key includes both the main card name and the subspell name, separated by a slash.

### Basic Example

```json
{
  "cards": {
    "Beanstalk Giant / Fertile Footsteps": {
      "front": {
        "name": "Beanstalk Giant",
        "mana": "{6}{g}",
        "cardtype": "Creature",
        "subtype": "Giant",
        "power": "5",
        "toughness": "5",
        "rules": "Beanstalk Giant's power and toughness are each equal to the number of lands you control."
      },
      "subspell": {
        "name": "Fertile Footsteps",
        "mana": "{2}{g}",
        "cardtype": "Sorcery",
        "subtype": "Adventure",
        "rules": "Search your library for a basic land card, put it onto the battlefield, then shuffle."
      },
      "quantity": 1,
      "complete": 1,
      "rarity": "uncommon"
    }
  }
}
```

### Multicolor Example

Subspell colors contribute to the card's color identity:

```json
{
  "cards": {
    "White Knight / Blue Trick": {
      "front": {
        "name": "White Knight",
        "mana": "{1}{w}",
        "cardtype": "Creature",
        "subtype": "Human Knight",
        "power": "2",
        "toughness": "2",
        "rules": "First strike"
      },
      "subspell": {
        "name": "Blue Trick",
        "mana": "{u}",
        "cardtype": "Instant",
        "subtype": "Adventure",
        "rules": "Draw a card."
      },
      "quantity": 1,
      "complete": 1,
      "rarity": "rare"
    }
  }
}
```

This card has a **white and blue** color identity (Azorius).

## Subspell Fields

The `subspell` object supports the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Subspell name |
| mana | string | No | Mana cost (e.g., "{2}{g}") |
| cardtype | string | Yes | Must be "Instant" or "Sorcery" |
| subtype | string | No | Usually "Adventure" or "Omen" |
| rules | string | No | Subspell rules text |
| rules1-6 | string | No | Additional rules lines (for complex subspells) |
| flavor | string | No | Flavor text |
| related_indicator | string | No | Related text/mana (rarely used) |

### Restrictions

1. **Card Type**: Subspells **must** be Instant or Sorcery
2. **No Power/Toughness**: Subspells cannot have power or toughness
3. **Subtype**: Typically "Adventure" or "Omen", but others are allowed for future expansion
4. **No Supertypes**: Subspells cannot be Legendary, Basic, Snow, or Token

## Card-Level Fields

Fields that apply to the entire physical card go at the top level (outside `front` and `subspell`):

| Field | Description |
|-------|-------------|
| quantity | Number of copies in deck |
| complete | Whether card image is generated |
| real | Whether card is a real MTG card |
| rarity | common, uncommon, rare, mythic |
| colors | Color identity (auto-calculated from mana costs) |
| tags | Categorization tags |
| artwork | Path to artwork file |
| artist | Artist name |
| setname | Set code (can override deck default) |

## Color Identity

Cards with subspells have their color identity calculated from **both** the main card's mana cost and the subspell's mana cost.

**Example:**
- Main card: `{1}{w}` (White)
- Subspell: `{u}` (Blue)
- **Color Identity**: White and Blue (Azorius)

This matches official MTG rules where Adventures contribute to color identity.

## Card Names

### Full Card Name

Use the helper method `card.get_full_card_name()` to get the complete name:

```python
card.get_full_card_name()
# Returns: "Beanstalk Giant / Fertile Footsteps"
```

### JSON Keys

The JSON key for a card with a subspell **must** use the full name format:

```json
"Beanstalk Giant / Fertile Footsteps": { ... }
```

### File Names

Generated card images should use the full name as the filename:

```
Beanstalk Giant / Fertile Footsteps.jpg
```

## Python API

### Creating a Card with a Subspell

```python
from src.core.card import Card, CardFace

# Create main card
card = Card(
    name="Beanstalk Giant",
    mana="{6}{g}",
    cardtype="Creature",
    subtype="Giant",
    power="5",
    toughness="5",
    rules="Beanstalk Giant's power and toughness are each equal to the number of lands you control.",
    rarity="uncommon"
)

# Create subspell
subspell = CardFace(
    name="Fertile Footsteps",
    mana="{2}{g}",
    cardtype="Sorcery",
    subtype="Adventure",
    rules="Search your library for a basic land card, put it onto the battlefield, then shuffle."
)

# Validate and attach
Card.validate_subspell_cardface(subspell)
card.subspell = subspell
```

### Checking for Subspells

```python
if card.is_subspell():
    print(f"This card has a subspell: {card.subspell.name}")
```

### Accessing Subspell Data

```python
if card.subspell:
    print(f"Subspell Name: {card.subspell.name}")
    print(f"Subspell Mana: {card.subspell.mana}")
    print(f"Subspell Type: {card.subspell.cardtype}")
    print(f"Subspell Subtype: {card.subspell.subtype}")
    print(f"Subspell Rules: {card.subspell.rules}")
```

### Validation

Subspells are automatically validated when loading from JSON. You can also manually validate:

```python
try:
    Card.validate_subspell_cardface(subspell)
    print("Valid subspell!")
except ValueError as e:
    print(f"Invalid subspell: {e}")
```

**Validation checks:**
- Cardtype must be Instant or Sorcery
- Cannot have power or toughness
- Must have a cardtype field

## Loading and Saving Decks

### Loading

Decks with subspell cards load automatically:

```python
from src.core.deck import Deck

deck = Deck.from_json("MyDeck.json", "SET", "MyDeck")

for card in deck.cards:
    if card.is_subspell():
        print(f"Found Adventure card: {card.get_full_card_name()}")
```

### Saving

Export decks with subspells using the new format:

```python
deck.to_json("MyDeck.json", use_new_format=True)
```

The exported JSON will:
- Use full name as key: `"Beanstalk Giant / Fertile Footsteps"`
- Include `subspell` field with all subspell data
- Calculate color identity from both main and subspell mana costs

## Rendering (Future)

**Note:** Card rendering for subspells is not yet implemented. You'll need to:

1. Create frame templates for Adventure/Omen cards with space for the subspell box
2. Update `src/rendering/card_renderer.py` to:
   - Detect cards with subspells
   - Adjust main rules text area to make room
   - Render subspell box on the left side with:
     - Subspell name
     - Subspell mana cost
     - Subspell type line
     - Subspell rules text

The data model is fully ready for rendering - you just need to add the visual layout logic.

## Examples

### Adventure Card (Monocolored)

```json
{
  "Bonecrusher Giant / Stomp": {
    "front": {
      "name": "Bonecrusher Giant",
      "mana": "{2}{r}",
      "cardtype": "Creature",
      "subtype": "Giant",
      "power": "4",
      "toughness": "3",
      "rules": "Whenever Bonecrusher Giant becomes the target of a spell, Bonecrusher Giant deals 2 damage to that spell's controller."
    },
    "subspell": {
      "name": "Stomp",
      "mana": "{1}{r}",
      "cardtype": "Instant",
      "subtype": "Adventure",
      "rules": "Damage can't be prevented this turn. Stomp deals 2 damage to any target."
    },
    "quantity": 4,
    "complete": 1,
    "rarity": "rare"
  }
}
```

### Omen Card (Wilds of Eldraine)

```json
{
  "Virtue of Courage / Embereth": {
    "front": {
      "name": "Virtue of Courage",
      "mana": "{3}{r}{r}",
      "cardtype": "Enchantment",
      "rules": "Creatures you control get +1/+0.\nWhenever a creature you control enters the battlefield, you may pay {r}{r}. If you do, that creature deals damage equal to its power to any target."
    },
    "subspell": {
      "name": "Embereth",
      "mana": "{1}{r}",
      "cardtype": "Sorcery",
      "subtype": "Omen",
      "rules": "Embereth deals 2 damage to any target."
    },
    "quantity": 1,
    "complete": 0,
    "rarity": "mythic"
  }
}
```

### Multicolor Adventure

```json
{
  "Azorius Adventurer / Spell Pierce": {
    "front": {
      "name": "Azorius Adventurer",
      "mana": "{2}{w}",
      "cardtype": "Creature",
      "subtype": "Human Wizard",
      "power": "2",
      "toughness": "2",
      "rules": "Flying"
    },
    "subspell": {
      "name": "Spell Pierce",
      "mana": "{u}",
      "cardtype": "Instant",
      "subtype": "Adventure",
      "rules": "Counter target noncreature spell unless its controller pays {2}."
    },
    "quantity": 1,
    "complete": 0,
    "rarity": "uncommon"
  }
}
```

Color identity: **White and Blue** (from {2}{w} + {u})

## Migration from Old Format

If you have old-style Adventure cards stored as separate front/back cards, you'll need to manually convert them to the new subspell format.

**Old format (incorrect):**
```json
{
  "Bonecrusher Giant": { ... },
  "Stomp": { ... }
}
```

**New format (correct):**
```json
{
  "Bonecrusher Giant / Stomp": {
    "front": { ... },
    "subspell": { ... }
  }
}
```

## See Also

- [JSON Format Reference](JSON_FORMAT.md) - Complete JSON format documentation
- [Double-Faced Cards](DOUBLE_FACED_CARDS.md) - Transform and MDFC cards
- [Card Architecture](ARCHITECTURE.md) - Overall system architecture
