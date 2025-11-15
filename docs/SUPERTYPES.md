# Supertypes

This document explains how supertypes (Legendary, Basic, Snow, Token) work in Manufactor.

## Overview

Supertypes are card properties that can be specified as separate fields in the JSON rather than embedded in the `cardtype` string.

## Supertype Fields

Each supertype has its own optional field:

- **`legendary`**: Set to `1` for legendary permanents
- **`basic`**: Set to `1` for basic lands
- **`snow`**: Set to `1` for snow permanents
- **`token`**: Set to `1` for token creatures/artifacts

## Examples

### Legendary Creature
```json
{
  "front": {
    "name": "Commander",
    "cardtype": "Creature",
    "legendary": 1
  }
}
```

### Basic Land
```json
{
  "front": {
    "name": "Plains",
    "cardtype": "Land",
    "basic": 1
  }
}
```

### Snow Legendary Land
```json
{
  "front": {
    "name": "Snow-Covered Mountain",
    "cardtype": "Land",
    "legendary": 1,
    "snow": 1
  }
}
```

### Token Creature
```json
{
  "name": "Goblin Token",
  "cardtype": "Creature",
  "token": 1
}
```

### Non-Legendary Creature
```json
{
  "front": {
    "name": "Bear",
    "cardtype": "Creature"
  }
}
```

## Backward Compatibility

The system supports **both** formats:

1. **Separate fields** (recommended): `"legendary": 1`
2. **Embedded in cardtype**: `"cardtype": "Legendary Creature"`

### Priority Rules

When both formats are present:
- Explicit supertype fields **take priority** over the `cardtype` string
- If a field is set to `0` or `false`, the card will NOT have that supertype (even if present in `cardtype`)
- If a field is omitted, the system parses the `cardtype` string

### Example of Priority
```json
{
  "name": "Override Example",
  "cardtype": "Legendary Creature",
  "legendary": 0
}
```
**Result**: Not legendary (the explicit `legendary: 0` overrides "Legendary" in cardtype)

## Implementation

Internally, the Card class stores supertypes as a `self.supertype` string (e.g., "Legendary Snow"). The supertype fields are a convenient way to specify them in JSON.

All existing methods like `is_legendary()`, `is_token()`, `is_basic()` work exactly as before.

## Recommendation

For new cards, use the separate supertype fields. They're clearer and more explicit.

See [JSON_FORMAT.md](JSON_FORMAT.md) for complete JSON format documentation.
