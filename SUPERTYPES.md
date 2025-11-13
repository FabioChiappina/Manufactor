# Supertype Format Changes

## Overview

The JSON card format now supports separate fields for each supertype instead of including them in the `cardtype` field. This makes the data structure clearer and easier to work with.

## New Format

### Before (Old Format)
```json
{
  "Harry Potter": {
    "name": "Harry Potter",
    "cardtype": "Legendary Creature",
    "subtype": "Human Wizard",
    ...
  }
}
```

### After (New Format)
```json
{
  "Harry Potter": {
    "name": "Harry Potter",
    "cardtype": "Creature",
    "subtype": "Human Wizard",
    "legendary": 1,
    ...
  }
}
```

## Supertype Fields

Each supertype now has its own optional field:

- **`legendary`**: Set to `1`, `true`, or omit (defaults to false)
- **`basic`**: Set to `1`, `true`, or omit (defaults to false)
- **`snow`**: Set to `1`, `true`, or omit (defaults to false)
- **`token`**: Set to `1`, `true`, or omit (defaults to false)

## Examples

### Legendary Creature
```json
{
  "name": "Commander",
  "cardtype": "Creature",
  "legendary": 1
}
```

### Basic Land
```json
{
  "name": "Plains",
  "cardtype": "Land",
  "basic": true
}
```

### Snow Legendary Land
```json
{
  "name": "Snow-Covered Mountain",
  "cardtype": "Land",
  "legendary": 1,
  "snow": 1
}
```

### Token Creature
```json
{
  "name": "Goblin Token",
  "cardtype": "Creature",
  "token": true
}
```

### Non-Legendary Creature (No Supertype Fields Needed)
```json
{
  "name": "Bear",
  "cardtype": "Creature"
}
```

## Backward Compatibility

The system fully supports **both** formats:

1. **Old format** (supertypes in `cardtype` string): Still works perfectly
2. **New format** (separate fields): Recommended for new cards
3. **Mixed**: You can use both in the same deck JSON

### Priority Rules

When both formats are present:
- **Explicit supertype fields take priority** over the `cardtype` string
- If a field is set to `0` or `false`, the card will NOT have that supertype (even if present in `cardtype`)
- If a field is omitted (`null`/not present), the system falls back to parsing the `cardtype` string

### Example of Priority
```json
{
  "name": "Override Example",
  "cardtype": "Legendary Creature",
  "legendary": 0
}
```
Result: **Not legendary** (the explicit `legendary: 0` overrides "Legendary" in cardtype)

## Migration Guide

You can migrate your JSON files gradually:

### Option 1: Keep Old Format
No action needed! Old format still works.

### Option 2: Migrate to New Format
For each card with supertypes:

1. Find "Legendary", "Basic", "Snow", or "Token" in the `cardtype` field
2. Remove that supertype from `cardtype`
3. Add the corresponding field: `"legendary": 1`, `"basic": 1`, etc.

#### Example Migration
```json
// Before
{
  "cardtype": "Legendary Creature"
}

// After
{
  "cardtype": "Creature",
  "legendary": 1
}
```

### Option 3: Use Find & Replace
For large files, you can use find/replace:

- Find: `"cardtype": "Legendary Creature"`
- Replace: `"cardtype": "Creature",\n    "legendary": 1`

(Repeat for "Basic Land", "Snow", and "Token")

## Benefits of New Format

1. **Clearer structure**: Supertypes are explicit, not embedded in strings
2. **Easier parsing**: No string manipulation needed
3. **Type safety**: Boolean/integer fields instead of string parsing
4. **Explicit control**: Can explicitly set `legendary: 0` to override
5. **Future-proof**: Easy to add new supertypes as separate fields

## Implementation Details

### Code Changes

The changes maintain full backward compatibility:

- [src/core/card.py](src/core/card.py): Card class now accepts `legendary`, `basic`, `snow`, `token` parameters
- [src/core/deck.py](src/core/deck.py): Deck.from_json() parses the new fields
- All existing code (rendering, Cockatrice export, token generation) continues to work unchanged

### Internal Behavior

Internally, the Card class still stores supertypes as a `self.supertype` string (e.g., "Legendary Snow"). All existing methods like `is_legendary()`, `is_token()`, etc. work exactly as before.

The new supertype fields are just a more convenient way to specify supertypes in JSON, which get converted to the internal string format.

## Testing

All tests pass for:
- Old format (supertypes in cardtype string)
- New format (separate supertype fields)
- Mixed format (some cards use old, some use new)
- Priority/override scenarios
- Deck loading from JSON
- Card rendering
- Cockatrice export

## Recommendation

For **new cards**, use the new format with separate fields. It's cleaner and more explicit.

For **existing cards**, no rush to migrate - both formats will continue to work indefinitely.
