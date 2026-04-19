# TOKENS.md — Comprehensive Token Rework Plan

## Overview

This document outlines a complete rework of the token system in Manufactor. It covers four major problem areas:

1. **Bug: Tokens no longer show up as predefined in Cockatrice** — root cause identified
2. **Unit test suite for token discovery** — iterative, data-driven approach
3. **Manual token creation in the Tokens tab** — UI + backend
4. **Forge-time automatic token discovery** — integration with card editor and assembly line

---

## Current State Analysis

### How Tokens Are Stored (New Format)

Deck JSON stores tokens under a top-level `"tokens"` key:

```json
{
  "metadata": { ... },
  "cards": { ... },
  "tokens": {
    "_TOKEN_Clue": {
      "name": "Clue",
      "cardtype": "Artifact",
      "subtype": "Clue",
      "rules": "{2}, Sacrifice this artifact: Draw a card.",
      "token": 1,
      "complete": 1,
      "source_cards": ["Batman, The Dark Knight"]
    }
  }
}
```

Token images live at `<DeckPath>/<FolderName>/Tokens/<TokenName>.jpg`.
Alternate artworks are `<TokenName>_1.jpg`, `<TokenName>_2.jpg`, etc.

### How the Cockatrice Exporter Uses Tokens

`src/integration/cockatrice.py → update_cockatrice()` does:

```python
tokens_deck = Deck.from_json(
    os.path.join(DECK_PATH, deck.folder_name, deck.folder_name + '_Tokens.json'),
    ...
)
tokens_cards = tokens_deck.cards
```

It then iterates `deck.cards + tokens_cards`. For each `Card` where `card.is_token()` is true, it:
- Copies `Tokens/<card.name>.jpg` to `COCKATRICE_IMAGE_PATH/<SETCODE>_<card.name>.full.jpeg`
- Writes an XML entry into `tokens.xml` with `<name>SETCODE_card.name</name>`
- Writes the deck `.cod` file with a `<zone name="tokens">` listing `<card name="SETCODE_card.name"/>`

**Root Cause of Bug #1**: `deck.tokens` (populated from the new JSON format) is a raw dict stored on the `Deck` object. The Cockatrice exporter completely ignores it — it only reads the legacy `_Tokens.json` sidecar file, which no longer exists for decks managed by the web UI. Since `_Tokens.json` fails to load, `tokens_cards = []`, and no tokens appear in the Cockatrice export.

### Token Naming Convention Summary

| Location | Format | Example |
|---|---|---|
| Deck JSON key | `_TOKEN_<Name>` | `_TOKEN_Clue` |
| Token image file | `Tokens/<Name>.jpg` | `Tokens/Clue.jpg` |
| Alternate art | `Tokens/<Name>_1.jpg` | `Tokens/Clue_1.jpg` |
| Cockatrice XML name | `<SETCODE>_<Name>` | `BAT_Clue` |
| Cockatrice image | `<SETCODE>_<Name>.full.jpeg` | `BAT_Clue.full.jpeg` |
| Deck `.cod` token zone | `<SETCODE>_<Name>` | `BAT_Clue` |

### What the `Deck` Object Carries

- `deck.cards` — list of `Card` objects (no token Card objects in the new format)
- `deck.tokens` — raw dict `{ "_TOKEN_Foo": { "name": "Foo", ... }, ... }`
- `deck.common_tokens` — list of common token names (old format only, populated from `_COMMON_TOKENS` key; not used in new format)

---

## Problem #1: Fix Cockatrice Predefined Tokens (Highest Priority)

### Root Cause

`update_cockatrice()` tries to load a `_Tokens.json` file that no longer exists. It never reads `deck.tokens`.

### Fix Strategy

Convert `deck.tokens` to a list of `Card` objects inside `update_cockatrice()`, replacing the `_Tokens.json` load. No separate file is needed.

**Where to change**: `src/integration/cockatrice.py` — the beginning of `update_cockatrice()`, specifically the block that currently does `Deck.from_json(... '_Tokens.json' ...)`.

**New logic (pseudocode)**:

```python
tokens_cards = []
for token_key, token_data in (deck.tokens or {}).items():
    if not isinstance(token_data, dict):
        continue
    token_card = Card(
        name=token_data.get('name', ''),
        cardtype=token_data.get('cardtype', 'Token Creature'),
        subtype=token_data.get('subtype', ''),
        rules=token_data.get('rules', ''),
        power=token_data.get('power'),
        toughness=token_data.get('toughness'),
        frame=token_data.get('frame'),
        colors=token_data.get('colors'),
        related=token_data.get('source_cards'),   # used for <reverse-related> tags
        token=1,
        complete=token_data.get('complete', 0),
    )
    tokens_cards.append(token_card)
```

**Also fix the `.cod` predefined token zone**: Currently the deck `.cod` file lists token names from `all_token_names_this_deck` (built from cards that `is_token()`) and from `tokens_deck.common_tokens`. After the fix, it should list token names from the newly-constructed `tokens_cards` list.

**Also fix the `related` field**: `Card.related` is currently expected to be a string (a single card name). For tokens, `source_cards` is a list. The Cockatrice XML writes `<reverse-related>` for each entry. Make sure the cockatrice loop handles both string and list for `card.related`.

### Secondary Bug: `<reverse-related>` Name Normalization

Even after the main fix, Cockatrice's right-click "Create token" menu (which shows predefined tokens for a specific card) may still not work. This menu works by matching the `<name>` of a card in `custom.xml` against the `<reverse-related>` content in `tokens.xml`. If these don't match exactly, the association is broken.

The current `update_cockatrice()` normalizes card names for `custom.xml` like this:

```python
name = this_card_name.replace('\u2019',"'").replace('\u2018',"'")
         .replace('"','&quot;').replace("."," ").replace("'","")
         .replace(" // ", " -- ")
```

But when writing `<reverse-related>` tags for tokens, the source card names come raw from `source_cards` (e.g. `"Batman, The Dark Knight"`) without applying the same normalization. If a source card name has apostrophes, dots, or Unicode quotes, the `<reverse-related>` value will not match the card's `<name>` in `custom.xml`.

**Fix**: Apply the same normalization function to each source card name before writing it into `<reverse-related>`.

Both bugs must be fixed together for predefined tokens to work end-to-end.

### Files to Change (Bug Fix Only)

- `src/integration/cockatrice.py` — replace `_Tokens.json` load with `deck.tokens` dict conversion; apply name normalization to `<reverse-related>` values
- `src/services/cockatrice_exporter.py` — no changes needed (it calls `update_cockatrice`)

### Testing the Fix

After implementing, Publish a deck that has tokens in its JSON. Open Cockatrice and load the deck. Confirm tokens appear in the predefined tokens zone (the "T" button in the deck list). Then right-click a card that creates a token mid-game and confirm "Create token" offers the correct predefined token.

---

## Problem #2: Unit Test Suite for Token Discovery

### Test Project Structure

Update the existing dedicated (and mostly empty) `tests/` directory that can grow beyond token tests:

```
tests/
    __init__.py
    conftest.py                          # shared fixtures (common_tokens mock, Card mock)
    test_token_discovery/
        __init__.py
        test_token_parser.py             # parametrized tests, one per rules-text example
        fixtures/
            token_test_cases.json        # the test data repository
    # Future directories:
    # services/
    # integration/
    # ui/
```

### Test Data Format (`token_test_cases.json`)

A draft initial version of this file (`tests/test_token_discovery/fixtures/token_test_cases.json`) has already been created. This will eventually be populated with many more test cases, but it is a good starting point.
Each entry maps a rules text string to the expected token(s):

```json
[
  {
    "id": "basic_creature_token",
    "description": "Simple creature token with P/T",
    "card_name": "Example Card",
    "rules": "Create a 1/1 white Soldier creature token.",
    "expected_specialized": [
      {
        "name": "Soldier",
        "cardtype": "Token Creature",
        "subtype": "Soldier",
        "power": "1",
        "toughness": "1",
        "rules": ""
      }
    ],
    "expected_common": []
  },
  {
    "id": "clue_token",
    "description": "Clue token (common token)",
    "card_name": "Example Investigator",
    "rules": "Investigate. (Create a colorless Clue artifact token with \"{2}, Sacrifice this artifact: Draw a card.\")",
    "expected_specialized": [],
    "expected_common": ["Clue"]
  }
]
```

### Test Parametrization

`test_token_parser.py` loads `token_test_cases.json` and parametrizes over it:

```python
import json, pytest
from src.token_generation.token_parser import parse_tokens_from_rules_text

with open("tests/token_discovery/fixtures/token_test_cases.json") as f:
    TEST_CASES = json.load(f)

@pytest.mark.parametrize("case", TEST_CASES, ids=[c["id"] for c in TEST_CASES])
def test_token_discovery(case, mock_common_tokens):
    specialized, common = parse_tokens_from_rules_text(
        case["rules_text"],
        card_name=case.get("card_name", ""),
        common_tokens_list=mock_common_tokens,
    )
    # Check specialized tokens
    for expected in case["expected_specialized"]:
        match = next((t for t in specialized if t["name"] == expected["name"]), None)
        assert match is not None, f"Expected token '{expected['name']}' not found"
        for field, value in expected.items():
            assert match.get(field) == value, f"Field '{field}' mismatch for token '{expected['name']}'"
    assert len(specialized) == len(case["expected_specialized"]), "Wrong number of specialized tokens"
    # Check common tokens
    assert sorted(common) == sorted(case["expected_common"]), "Common tokens mismatch"
```

### Iterative Workflow (Requires User Input)

1. You provide a rules text example + what tokens it should produce
2. That example gets added to `token_test_cases.json`
3. Run `pytest tests/token_discovery/` to see if it passes
4. If it fails, analyze what `parse_tokens_from_rules_text` actually returns vs. expected
5. Fix the parser in `token_parser.py` to handle the new case
6. Confirm all prior tests still pass (no regressions)

**Categories of rules text I need examples for**:
- Simple creature tokens: `"Create a 1/1 white Soldier creature token."`
- Named tokens: `"Create a 2/2 black Zombie creature token named Joker's Goon."`
- Tokens with rules: `"Create a 1/1 green Elf Druid creature token with 'Tap: Add {G}.'"` 
- Tokens with multiple abilities (and/or)
- Legendary tokens: `"Create a legendary 4/4 Dragon token with flying."`
- Non-creature tokens (Treasures, Clues, Food — common tokens)
- Role tokens (Aura Role) — special handling already exists
- Token copies — should be skipped
- Multi-token lines: `"Create a 1/1 Soldier and a 1/1 Warrior creature token."`
- Conditional tokens: `"If X is 3 or more, create a 3/3 Beast creature token."`
- Cards that create tokens in rules text of BACK face (DFC)
- Cards with subspells that create tokens
- Custom ability reminder text on tokens — need to confirm this already works

### Custom Ability Reminder Text

`token_parser.py` line 336 checks `AbilityElements.all_abilities` for the last word in rules to append a description. This only fires for the very last word if the rules text is ≤6 words total. Need to test cases like:

- Token with a single keyword that has custom reminder text defined in settings
- Token where the keyword is in the middle of other text
- Potential enhancement: scan all keywords in token rules text (not just the last word) and inject reminder text for any that appear in the custom abilities config

**Action needed from user**: Provide the structure of where custom ability reminder texts are defined (likely in settings/config), and examples of tokens that should display that reminder text.

---

## Problem #3: Manual Token Creation in the Tokens Tab

### Current Tokens Tab State

The Tokens tab exists in the UI and displays existing tokens from `deck.tokens`. Token images load from `Tokens/<name>.jpg`. Clicking a token currently opens it for editing in the same split-panel editor used for cards (but only if the editing code is wired up — needs verification).

### Desired Behavior

1. Click "+ Create Token" in the Tokens tab toolbar → opens the card editor in the right panel, pre-configured for token creation
2. The editor form auto-sets "Token" checkbox = true and locks it
3. The user fills in name, cardtype, subtype, P/T, rules, etc.
4. Click Forge → generates the token image to `Staging/<TokenName>.jpg`; adds a staged entry
5. On Publish → copies image to `Tokens/<TokenName>.jpg`; adds the token to the `"tokens"` dict in deck JSON with key `_TOKEN_<name>`

### JSON Storage Decision

Tokens are stored in the `"tokens"` section of the deck JSON (not in `"cards"`). This is already the correct structure. The key difference:

- Cards are keyed by display name: `"Batman, The Dark Knight": { "front": {...}, ... }`
- Tokens are keyed with prefix: `"_TOKEN_Clue": { "name": "Clue", "token": 1, ... }`

Tokens do NOT use the `front`/`back` structure — they use flat fields directly. This is simpler and consistent with the existing format.

### Staging Token Changes

The current `_staging.json` format maps card name → staged entry. We need to also stage token changes. Options:

**Option A**: Use the same `_staging.json` but namespace token keys with `_TOKEN_` prefix:
```json
{
  "Batman, The Dark Knight": { ... },
  "_TOKEN_Clue": {
    "original": { ... },
    "updated": { ... },
    "staged_image_path": "Staging/_TOKEN_Clue.jpg",
    "is_new": true
  }
}
```

**Option B**: Use a separate `_staging_tokens.json` file.

**Recommendation: Option A** — simpler, keeps a single source of truth for all staged changes. The `_TOKEN_` prefix unambiguously identifies token entries vs. card entries.

The Assembly Line tab must be updated to show staged tokens alongside staged cards (different visual treatment — e.g., a "TOKEN" badge on the card thumbnail).

### Token Editor Form Differences vs. Card Editor

| Field | Card Editor | Token Editor |
|---|---|---|
| "This is a Token" checkbox | Optional | Always checked, locked |
| Mana cost | Yes | No (tokens are colorless or use frame for color) |
| Color identity | Implicit from mana | Explicit color picker (selects frame) |
| Rarity | Yes | No |
| Quantity | Yes | No (always 1 in the token zone) |
| Double-faced type | Yes | Probably no (skip for now) |
| Source cards | No | Read-only display — list of cards that create this token |
| Frame | Auto-computed | Auto-computed from colors/cardtype |

### New Flask Routes Needed

```
POST /deck/<name>/token/forge                → Forge a token (new or existing)
POST /deck/<name>/token/discard              → Discard a staged token
GET  /deck/<name>/token-data?key=_TOKEN_Foo  → Return token JSON + staged image
```

### Forge Endpoint for Tokens (`/deck/<name>/token/forge`)

- Accepts the same JSON shape as the card forge endpoint
- Sets `token=1`, `is_token=True` before rendering
- Saves image to `Staging/<TokenName>.jpg`
- Updates `_staging.json` under key `_TOKEN_<TokenName>`
- Returns `{ image_base64, staged_count }`

### Publish Changes for Tokens

`/deck/<name>/publish-assembly-line` already handles all staged entries. Need to extend it:

1. For entries where the key starts with `_TOKEN_`:
   - Copy `Staging/<name>.jpg` → `Tokens/<name>.jpg`
   - Update or add the entry in `deck_json["tokens"]`
   - Do NOT regenerate the printing image (tokens don't appear in printing sheets)
2. Re-run Cockatrice export as before

---

## Problem #4: Forge-Time Automatic Token Discovery

### Goals

- When a card is Forged, automatically discover what tokens it creates
- Compare discovered tokens against tokens already in the deck JSON
- Stage any new/changed tokens alongside the card change in the assembly line
- Provide a way to skip auto-discovery per card (for cards with complex/custom token logic)
- "Forge All Cards" should also re-run token discovery for all cards

### The `disable_auto_tokens` Flag

Already exists! The staging JSON already carries `disable_auto_tokens` per staged card entry (see `PLAN.md` and `app.py`). This needs to also be persisted in the deck JSON per card, so that even before a card is staged, the UI knows whether to run auto-discovery for it.

Proposed location in deck JSON (per card, at card level, not inside `front`):
```json
"Some Card Name": {
  "front": { ... },
  "disable_auto_tokens": true,
  "quantity": 1,
  "complete": 1
}
```

The card editor should show a checkbox: "Skip automatic token discovery for this card". This is a card-level field (not face-specific).

### Auto-Discovery Flow on Forge

When `POST /deck/<name>/card/<card>/forge` is called:

1. Parse `disable_auto_tokens` from the submitted card dict
2. If `disable_auto_tokens` is true → skip all token processing
3. Otherwise:
   a. Run `parse_tokens_from_rules_text(front_rules_text, card_name=card_name)`
   b. Also run on back face rules text for DFCs
   c. Also run on subspell rules text if present
   d. For each discovered token, check if an equivalent token exists in `deck_json["tokens"]`:
      - **Match found**: add this card name to the token's `source_cards` if not already there → stage the token update if `source_cards` changed
      - **No match**: create a new token entry → stage it as a new token (`is_new=True`)
   e. For any tokens currently attributed to this card in the existing deck JSON that are NOT found in the new discovery → remove this card from their `source_cards`; if `source_cards` becomes empty, optionally delete the token (or mark it for deletion with a flag)

**Token Matching Logic**: Two tokens are "equivalent" if they have the same `name` (case-insensitive). This is intentionally simple — more complex matching (same P/T, same rules) would cause too many false positives with homebrewed cards.

### Displaying Discovered Tokens in the Card Editor

**Proposed UX**: A collapsible "Tokens" panel in the card editor right pane (below the form fields), similar to what Phase 7b describes. It shows:

- A list of tokens discovered from this card's rules text (read-only preview)
- Each entry shows: token name, type, P/T (if applicable)
- If a discovered token already exists in the deck → shows "Already in deck" badge
- If a discovered token is new → shows "Will be added" badge
- Checkbox: "Skip automatic token discovery for this card"

This panel updates live as the user edits rules text (debounced), before forging.

### "Forge All Cards" and Tokens

`POST /deck/<name>/forge-all` currently forges all non-real cards. It should:

1. After forging all cards, also run full token discovery on the whole deck
2. Diff discovered tokens vs. existing `deck.tokens`
3. Stage any additions, modifications, or deletions as token changes

This is equivalent to calling "token discovery on the whole deck" — which is the same as calling `Deck.get_tokens()` and then comparing the result with the current `deck.tokens`.

### Handling Discarded Token Changes

Token staged entries work the same as card staged entries in the assembly line:
- User can discard a staged token change via the Assembly Line tab
- Discarding removes the `_TOKEN_<name>` entry from `_staging.json`
- The original token (if it existed) is restored

---

## Additional Features & Design Decisions

### F1: Orphaned Tokens

What happens to tokens that are no longer created by any card? If a card is edited to remove a token-creating ability, and that was the only card creating that token, should the token be automatically removed from the deck?

**Answer**: No automatic removal. Stage the change as "token source_cards became empty" and let the user decide whether to delete it in the Assembly Line. The Tokens tab should visually flag tokens with no `source_cards` with a yellow outline (no text on the token image from the gallery view). Then when the user opens up that orphaned token, a warning message appears on the left hand side of the token, beneath the token's image, indicating: "Warning: Token not generated by any cards." This can double to indicate to the user either (1) this token was orphaned, and used to be associated with a card but is not anymore, or (2) this was a manually created token that doesn't appear to be attached to any existing card. That way the user has a visual indicator to do a manual cleanup if they so desire.

### F2: DFC tokens (tokens that transform)

For now, these types of tokens will not be supported. DFC tokens are rare and complex. The token editor will only support single-faced tokens. Add a note to revisit eventually.

### F3: Multiple artworks for a token

The Cockatrice exporter already handles `<TokenName>_1.jpg`, `<TokenName>_2.jpg`, etc. (the `while True` loop in `update_cockatrice()`). Each alternate artwork gets its own Cockatrice XML entry with a `_1`, `_2` suffix.

In the UI, the Tokens tab should show all artwork variants for a token (stacked thumbnails or a carousel). Forging a token or any card with that token should automatically discover all available artworks for the token in the Artwork folder (they either have the filename `Artwork/<TokenName>.jpg` or they `Artwork/<TokenName>_N.jpg`, all of which should be picked up) and all artwork variants should be added as images to `Staging/<TokenName>_N.jpg`.

Handling multiple artworks should come only after the main problems above have been dealt with.

### F4: Token discovery for back faces of DFCs and subspells

The current `parse_tokens_from_rules_text` only takes a single rules text string. The calling code in `Deck.get_tokens()` calls `card.get_tokens()` which internally calls the parser on the card's main rules. Need to also check:
- `card.back.rules` (DFC back face)
- `card.subspell.rules` (Adventure/Omen subspell)

This should be handled in `card.get_tokens()` in `src/core/card.py` (or wherever `card.get_tokens` is implemented — confirm this exists). If it only checks `card.rules`, it needs updating. For other types of cards that have multiple rules text boxes (e.g., Sagas which can have several rules boxes, or Planeswalkers), tokens should be discovered from ALL of those rules text boxes.

### F5: Common tokens vs. specialized tokens in the new format

The existing system distinguishes:
- **Common tokens** (Treasure, Clue, Food, etc.) — defined in `config/common_tokens.json`, reused across decks
- **Specialized tokens** — unique to a deck, stored in `deck.tokens`

The current code adds both to `deck.tokens` (common tokens get their definition pulled from `common_tokens.json`). This is fine.

For the Cockatrice fix, we need to handle common tokens properly. Currently in the deck JSON they appear with `complete: 1` but may have no image in `Tokens/`. For common tokens with no image, the Cockatrice exporter prints a warning. This is acceptable behavior — common tokens use Cockatrice's built-in token database. The critical thing is just ensuring that the tokens do end up in the Cockatrice deck definition so they can be conveniently created within a Cockatrice game along with the other predefined tokens of the deck. Note that even though common tokens may not have a local image file, they should definitely still be included in the Cockatrice `.cod` predefined tokens zone. They'll appear in the token list but have no artwork (so Cockatrice will use its built-in image or a blank), but this is still useful (quick access to the token in-game, even without custom art).

---

## Implementation Phases (Recommended Order)

### ✅ Phase T1: Fix Cockatrice Predefined Tokens (Bug Fix)

**Status**: Complete  
**Files changed**: `src/integration/cockatrice.py`

What was done:
1. Replaced `Deck.from_json(... _Tokens.json ...)` block with code that reads `deck.tokens` and constructs `Card` objects directly — the sidecar file no longer exists for web-UI decks
2. Tokens without local images (e.g. common tokens like Clue, Treasure) now still appear in `tokens.xml` and the `.cod` predefined zone — previously they were silently dropped
3. Fixed `<reverse-related>` normalization: source card names are now run through the same normalization as card names in `custom.xml` (strip apostrophes, dots, Unicode curly quotes, `//` → `--`). Without this, Cockatrice's right-click "Create token" menu couldn't match the source card
4. Fixed `.cod` predefined tokens zone: uses `set()` to deduplicate; removed the stale `tokens_deck.common_tokens` reference
5. Removed the now-unused `Deck` import from `cockatrice.py`

Manual testing still needed: Publish a deck with tokens → open Cockatrice → confirm predefined tokens appear in the "T" zone and right-click "Create token" works per-card.

---

### ✅ Phase T2: Unit Tests — Token Discovery (Infrastructure + First Pass)

**Status**: Infrastructure complete; 26/26 tests passing; iterative expansion ongoing  
**Files changed/created**:
- `tests/conftest.py` — `mock_common_tokens` fixture
- `tests/test_token_discovery/__init__.py`
- `tests/test_token_discovery/test_token_parser.py` — parametrized test runner
- `tests/test_token_discovery/fixtures/token_test_cases.json` — 26 test cases (all passing)
- `src/token_generation/token_parser.py` — three parser bug fixes (see below)

Parser bugs fixed during this phase:
- **`(create` in reminder text**: `Investigate. (Create a Clue token...)` now correctly detects the token — strips leading `(` before the "create" detection and index lookup
- **`"a number of X tokens"` phrasing**: added "Number" and "Of" to `words_to_exclude_from_names_and_subtypes`, so "Treasure" is now correctly extracted from "a number of Treasure tokens"
- **`keyword, "quoted ability"` formatting**: added a postprocessing step that splits `Reach, "{t}: Add {G}."` into `Reach\n{t}: Add {G}.` (only when the keyword before `, "` contains no `{`)

Test data corrections made:
- `role_token_3`: expected token name corrected "Detective" → "Hypnotized" (copy-paste error)
- `treasure_token`: added `Black Mask` Equipment token to `expected_specialized` (parser was correct, test data was incomplete)
- `custom_token_common_types`: added `"Treasure"` to `expected_common` (the card's second ability also creates a Treasure token)

**Next steps for Phase T2** (iterative — needs user input):
- Add more test cases to `token_test_cases.json` covering the categories listed in the "Categories of rules text" section above
- Run `pytest tests/test_token_discovery/ -v` after each addition; fix parser if tests fail

### ✅ Phase T3: Manual Token Creation in Tokens Tab

**Status**: Complete  
**Files changed**: `deck.html`, `main.js`, `app.py`, `style.css`, `helpers.py`

What was done:
1. Added `+ Create Token` button to the Tokens tab toolbar
2. Token editor reuses `#card-editor-panel` — on open the editor switches to the Cards tab, hides `#cards-tab-main`, enters token mode (hides mana/rarity/qty/DFC/subspell/tags; shows color picker and source cards panel)
3. Back button is patched via clone/replace: routes to `closeTokenEditor()` in token mode, `closeCardEditor()` otherwise
4. Added Flask routes: `GET /deck/<name>/token-data`, `POST /deck/<name>/forge-token`, `POST /deck/<name>/stage-delete-token`
5. Publish and discard endpoints extended to handle `_TOKEN_<name>` staging keys; token images publish to `Tokens/` folder
6. Assembly line shows token rows with a `(token)` label; discard path is `onDiscardToken()`
7. Token gallery items with no `source_cards` show yellow orphan outline; orphan warning shown below image in editor
8. Token delete confirmation dialog: staged deletion, applied on publish

Key implementation details:
- Token staging key: `_TOKEN_<name>` in `_staging.json` with `is_token: True` flag
- Token JSON is flat (no `front`/`back` nesting); `card_from_editor_dict` extended to accept `token` and `colors` at top level
- `helpers.py`: `card_from_editor_dict` passes explicit `colors` and `token` fallback for tokens
- `_exitTokenMode()` skips restoring `ef-subspell-section` (managed by `_setSubspellActive`) and `ef-discovered-tokens-panel`

---

### ✅ Phase T4: Forge-Time Auto-Discovery + Card Editor Token Panel

**Status**: Complete  
**Files changed**: `src/core/card.py`, `app.py`, `deck.html`, `main.js`, `style.css`

What was done:
1. **`src/core/card.py`** — `get_tokens()` extended to scan all rules fields on the back face (DFC `.back`) and subspell face (Adventure/Omen `.subspell`) in addition to the front face, via a shared `_parse_face()` inner helper.

2. **`app.py`** — New `_apply_token_discovery(folder_path, raw_deck, deck_key, prev_deck_key, card_obj, staging)` helper:
   - Deduplicates discovered tokens by name (case-insensitive)
   - For each discovered token: adds `deck_key` to `source_cards` on existing tokens (handles renames from `prev_deck_key` → `deck_key`); creates placeholder in `raw_deck["tokens"]` and stages new tokens
   - Handles common tokens (Clue, Treasure, etc.) the same way, pulling definition from `common_tokens.json`
   - Orphan detection: tokens currently attributed to this card that are no longer discovered → removes card from their `source_cards`, stages the update
   - Called from `_do_forge` (per interactive forge), `forge_one` (per-card in Forge All List), and `forge_all` (bulk forge)
   - `_do_forge` response now includes `discovered_tokens` list: `[{ name, cardtype, power, toughness, is_new, is_orphaned }]`

3. **`deck.html`** — Two additions in the card editor right pane (inside `#editor-form-mode`):
   - `#ef-disable-auto-tokens-row` — "Skip automatic token discovery for this card" checkbox; hidden in token mode via `_TOKEN_FIELDS_TO_HIDE`
   - `#ef-discovered-tokens-panel` — panel below the form, shows tokens found after forge with New/Updated/Orphaned badges; hidden in token mode and on editor close

4. **`main.js`**:
   - `populateForm()` reads `disable_auto_tokens` into the checkbox
   - `serializeForm()` writes `disable_auto_tokens: true` when checked
   - `onForgeClick()` calls `_updateDiscoveredTokensPanel(data.discovered_tokens)` after a successful forge
   - `_updateDiscoveredTokensPanel(tokens)` — builds the panel rows, shows/hides the panel
   - `closeCardEditor()` hides `#ef-discovered-tokens-panel`
   - `ef-discovered-tokens-panel` added to `_TOKEN_FIELDS_TO_HIDE` (so it hides on entering token mode) and skipped in `_exitTokenMode` restore loop (visibility managed by forge response)

5. **`style.css`** — Styles for `.ef-disable-auto-tokens-row`, `.ef-checkbox-label--subtle`, `.ef-discovered-tokens-panel`, `.ef-discovered-tokens-header`, `.ef-discovered-tokens-title`, `.ef-discovered-tokens-list`, `.ef-discovered-token-row`, `.ef-discovered-token-name`, `.ef-discovered-token-badge` and its `--new`, `--existing`, `--orphaned` variants.

Known gap (intentional): the token discovery panel does **not** update live as the user types (debounced preview). It only updates after clicking Forge. This can be added later if desired.

---

### Phase T5: Ensure Finer Points From "Additional Features & Design Decisions" Section Are Implemented

**Effort**: Medium — 1–2 sessions  
**Prerequisite**: T4 complete ✅

Steps (not fully fleshed out yet):
1. **F1 — Orphaned token cleanup flow**: The yellow gallery outline and editor warning are already in place (T3). What's missing is a first-class "Delete this orphaned token" prompt in the Assembly Line when a token's `source_cards` becomes empty after a forge. Currently the user must open the token editor and manually delete it.
2. **F3 — Multiple artworks per token**: Tokens tab should show all artwork variants (`<TokenName>_1.jpg`, `<TokenName>_2.jpg`, etc.) as stacked thumbnails or a carousel. Forging should discover all `Artwork/<TokenName>_N.jpg` variants and stage them all. Cockatrice exporter already handles the `_N` suffix naming.
3. **F4 — Token discovery for DFC back faces / subspells / multi-rules boxes**: Already done in T4 (`card.get_tokens()` now scans `.back` and `.subspell`). Verify that Sagas (`rules1`–`rules6` on the front face) also work — they should, since `_parse_face()` iterates all six slots.
4. **F5 — Common tokens in Cockatrice predefined zone**: Already handled in T1 (common tokens appear in `.cod` even without a local image). Confirm this holds end-to-end after T3/T4 changes.

---

## Files Inventory

| File | Relevance |
|---|---|
| `src/integration/cockatrice.py` | ✅ Fixed — now reads `deck.tokens` dict; `_Tokens.json` load removed; `<reverse-related>` normalization fixed |
| `src/token_generation/token_parser.py` | ✅ Three parser bugs fixed (see Phase T2); target for further improvements |
| `src/core/deck.py` | `get_tokens()` — runs discovery on whole deck; `_from_json_new_format` — loads `tokens` dict |
| `src/core/card.py` | ✅ `get_tokens()` extended — now scans front, back (DFC), and subspell faces; all rules1–6 slots |
| `src/ui/app.py` | ✅ Token routes added (T3); `_apply_token_discovery` helper (T4); forge/forge-all/publish all handle tokens |
| `src/ui/helpers.py` | ✅ `card_from_editor_dict` extended for token `colors` and `token` flag; staging helpers |
| `src/ui/templates/deck.html` | ✅ Token editor (T3): color picker, source cards, orphan warning, delete dialog; T4: disable-auto-tokens checkbox, discovered-tokens panel |
| `src/ui/static/js/main.js` | ✅ Full token editor wiring (T3); `_updateDiscoveredTokensPanel`, `disable_auto_tokens` serialize/populate (T4) |
| `src/ui/static/css/style.css` | ✅ Token editor styles (T3); discovered tokens panel styles (T4) |
| `src/services/cockatrice_exporter.py` | Calls `update_cockatrice`; no changes needed |
| `config/common_tokens.json` | Common token definitions used by parser and `_apply_token_discovery` |
| `tests/conftest.py` | ✅ Created — `mock_common_tokens` pytest fixture |
| `tests/test_token_discovery/__init__.py` | ✅ Created |
| `tests/test_token_discovery/test_token_parser.py` | ✅ Created — 26 parametrized test cases, all passing |
| `tests/test_token_discovery/fixtures/token_test_cases.json` | ✅ 26 test cases; needs iterative expansion |

---

## Information Requested From User (Including Answers)

These items must be resolved before certain phases can be implemented. Phase T1 (Cockatrice bug fix) can proceed without any of them.

### Needed for Phase T2 (Unit Tests)

**Item 1 — Custom ability reminder text**  
**Question**: Where is custom ability reminder text defined in settings/config? Which part of the settings UI controls it? Does the token parser already pick up custom reminder text for token abilities, or is that missing entirely? Provide at least one example of a token that should display custom reminder text (give the rules text of the card that creates it, the token's expected output text including the reminder, and what the custom ability definition looks like in config).
**Answer**: It looks like there is currently no support for custom ability reminder text through the settings, but I'd like to change that. Check out the file src/core/ability.py, where there is a class called "AbilityElements" that contains a few hard-coded definitions for some ability words that I've put on tokens before (I hard-coded them as a temporary solution to allow the tokens I generated to have the reminder text I wanted). Most of the ability words there are real MTG ability words, but one of them (anarky) is an example of a custom ability word. I want to rework the way we do this so it looks just like the custom tokens that a user can configure. We can have some preset ability words and their reminder text (e.g., the ones I already have in that AbilityElements class, like decayed, shadow, and protection from everything), plus the custom anarky ability word and its reminder text, and then allow users to delete or add new ability words. This way they can configure their settings so that tokens DO or DON'T automatically include the reminder text for ability words those tokens have.
An example of rules text with a custom ability word: "Create a 1/1 red Human creature token with anarky."
That rules text should lead to a token of card type Creature, subtype Human, power and toughness 1/1, color red (which affects the card frame filename), and the text box on that token should read: "Anarky (This creature attacks a randomly selected opponent each combat if able.)" That is -- ONLY assuming that the ability word "anarky" is one of the configured ability words with that saved reminder text.

**Item 2 — Token discovery test cases (ongoing, iterative)**  
Once the test infrastructure is in place, provide rules text examples + expected token outputs so the test data repository can be built up. This will happen across multiple sessions. Format: the full rules text of the card, and for each token it creates: name, cardtype, subtype, P/T (if any), rules text. Flag cases where the current parser is known to fail.
**Answer**: A draft initial version of `tests/test_token_discovery/fixtures/token_test_cases.json` is provided. This contains 10-15 initial token test cases from one known set of already discovered tokens. Many further additions to this JSON file will be necessary, but this is a good starting point.

### Resolved for Phase T3 (Manual Token Creation) ✅

**Item 3 — Token editor UX**: Reuses `#card-editor-panel` with token mode active (no tags, subspells, commander button, quantity, DFC, face toggle). Form and JSON modes both supported. Deletion is staged via confirmation dialog, applied on publish. *(Implemented in T3)*

**Item 4 — Common tokens in Cockatrice predefined zone**: Always listed in `.cod` regardless of whether a local image exists. *(Implemented in T1)*

### Resolved for Phase T4 (Forge-Time Auto-Discovery) ✅

**Item 5 — Token discovery scope**: `card.get_tokens()` now scans front face (`rules`, `rules1`–`rules6`), back face (DFC), and subspell face. Multi-rules-box cards (Sagas, Planeswalkers) are covered because their rules use `rules1`–`rules6` slots on the front face. *(Implemented in T4)*

**Item 6 — Renaming cards + source_cards**: `_apply_token_discovery` receives both `prev_deck_key` and `deck_key`; when they differ (subspell added/changed causes a rename), any token whose `source_cards` contains `prev_deck_key` gets it replaced with `deck_key`. *(Implemented in T4)*

---

## Appendix: How Cockatrice Predefined Tokens Work

A Cockatrice deck `.cod` file has a `<zone name="tokens">` section:

```xml
<zone name="tokens">
    <card number="1" name="BAT_Clue"/>
    <card number="1" name="BAT_Treasure"/>
</zone>
```

The names here must exactly match the `<name>` field in the `tokens.xml` database:

```xml
<card>
    <name>BAT_Clue</name>
    <text>{2}, Sacrifice this artifact: Draw a card.</text>
    <prop>
        <type>Token Artifact — Clue</type>
        <maintype>Artifact</maintype>
        <cmc>0</cmc>
    </prop>
    <set>BAT</set>
    <reverse-related>Batman, The Dark Knight</reverse-related>
    <token>1</token>
    <tablerow>2</tablerow>
</card>
```

The token artwork file must be at:
`COCKATRICE_IMAGE_PATH/BAT_Clue.full.jpeg`

When a user right-clicks a card in Cockatrice during a game and selects "Create token", Cockatrice shows only the predefined tokens associated with that card. The `<reverse-related>` tag is what creates that association — it contains the name of the card that creates the token. So **the Cockatrice name of the card must exactly match what's in `<reverse-related>`**. For custom cards exported by Manufactor, the card name in `custom.xml` is the normalized name (no apostrophes, no dots). We need to make sure the `<reverse-related>` value in the token XML uses the same normalization.

Current normalization in `update_cockatrice()`:
```python
name = this_card_name.replace('\u2019',"'").replace('\u2018',"'")
         .replace('"','&quot;').replace("."," ").replace("'","")
         .replace(" // ", " -- ")
```

The `<reverse-related>` content should be the normalized version of the source card name, not the raw name from `source_cards`. This is a subtle bug that might cause "create token" not to work even after the main fix — worth double-checking.
