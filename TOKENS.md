# TOKENS.md — Token System Reference

## Overview

This document covers the complete token system rework across six implementation sessions (T1–T6). All major features are implemented. Use this as a reference for current behaviour, implementation history, and the small list of remaining work.

---

## Current State (as of T7)

### Storage Format

Deck JSON stores tokens under a top-level `"tokens"` key. Token images live in `<DeckPath>/<FolderName>/Tokens/`. Alternate artworks use the `_N` suffix.

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

### Token Naming Convention

| Location | Format | Example |
|---|---|---|
| Deck JSON key | `_TOKEN_<Name>` | `_TOKEN_Clue` |
| Token image (primary) | `Tokens/<Name>.jpg` | `Tokens/Clue.jpg` |
| Token image (alt art) | `Tokens/<Name>_N.jpg` | `Tokens/Clue_1.jpg` |
| Artwork input (primary) | `Artwork/<Name>.jpg` | `Artwork/Clue.jpg` |
| Artwork input (alt art) | `Artwork/<Name>_N.jpg` | `Artwork/Clue_1.jpg` |
| Staging (primary) | `Staging/<Name>.jpg` | `Staging/Clue.jpg` |
| Staging (alt art) | `Staging/<Name>_N.jpg` | `Staging/Clue_1.jpg` |
| Cockatrice XML name | `<SETCODE>_<Name>` | `BAT_Clue` |
| Cockatrice image | `<SETCODE>_<Name>.full.jpeg` | `BAT_Clue.full.jpeg` |
| Cockatrice alt art | `<SETCODE>_<Name>_N.full.jpeg` | `BAT_Clue_1.full.jpeg` |
| Deck `.cod` token zone | `<SETCODE>_<Name>` | `BAT_Clue` |

### What the `Deck` Object Carries

- `deck.cards` — list of `Card` objects (no token `Card` objects in the new format)
- `deck.tokens` — raw dict `{ "_TOKEN_Foo": { "name": "Foo", ... }, ... }`

### How Cockatrice Predefined Tokens Work

A deck `.cod` file has a `<zone name="tokens">` section listing token names. Those names must exactly match `<name>` entries in `tokens.xml`. The `<reverse-related>` tag in the token XML entry must match the normalized name of the source card in `custom.xml` (same normalization: strip apostrophes, dots, Unicode curly quotes; `//` → `--`). The Cockatrice exporter now reads `deck.tokens` directly; the old `_Tokens.json` sidecar file is no longer used.

---

## What's Remaining

| Item | Priority | Description |
|---|---|---|
| **Manual testing — F2b (ability words)** | Verify | Forge a card that creates a token with "anarky" → confirm reminder text appears on the forged token image |
| **Live debounced token panel** | Low | Token discovery panel only updates after Forge, not live as the user types (intentional gap from T4) |
| **F2 — DFC tokens** | Deferred | Tokens that transform are rare and complex; token editor only supports single-faced tokens |

| **Manual testing — F3 (alt artworks)** | UPDATE: Completed ✅  | Place `<TokenName>_1.jpg` in `Artwork/`, forge the token → `Staging/<TokenName>_1.jpg` appears; publish → `Tokens/<TokenName>_1.jpg` copied; reopen token editor → alt art strip shows the thumbnail |
| **Manual testing — T1 (Cockatrice)** | UPDATE: Completed ✅ | Publish a deck with tokens → open Cockatrice → confirm "T" zone and right-click "Create token" per card |

### T2 Test Coverage Gaps

The test suite currently has 66 cases covering all previously-failing bugs. These categories have no dedicated test cases yet:

- **DFC back face tokens** — a card whose back face (not front) creates tokens
- **Conditional tokens** — `"If X is 3 or more, create a 3/3 Beast creature token."`
- **Ability word NOT in config** — should produce no reminder text injection (regression guard)

---

## ✅ T2 Parser Bugs — All Fixed

All 22 originally-failing test cases now pass (66/66 total). Below is the record of each bug and its fix for future reference.

### Bug 1 — X/X power/toughness not parsed ✅
`int(power)` threw for `"X"`. Fixed: `_valid_pt()` helper accepts `power.upper() == "X"` as valid, and uppercases the stored value to `"X"`.

### Bug 2 — Legendary tokens put "Legendary" in cardtype instead of `legendary: 1` field ✅
Fixed: track `is_legendary` flag, remove "Legendary" from `cardtype` string, pass `legendary=1` to the `Card()` constructor for frame generation, add `"legendary": 1` to the token dict.

### Bug 3 — Multi-keyword comma-separated lines don't get reminder text injected ✅
`_inject_ability_reminder_text` only matched lines whose **entire content** was an ability word key. Fixed: also split each line on commas and check each part individually. Only fires when the token rules contain no complex (multi-word) ability lines, to avoid redundant injection.

### Bug 4 — Tokens defined entirely in reminder text parentheticals are not discovered ✅
When the rules say `Create a Charger token.` with no type/color info, the parser produced `cardtype = "Token"` (invalid) and filtered it out. Fixed: added a pre-processing pass `_expand_reminder_definitions(rules_text)` that:
1. Scans all `(...)` blocks for sentences matching:
   - `It's a [P/T] [colors] [Types] creature/artifact [with rules]`
   - `They're [P/T] [colors] [Types] creatures/artifacts [with rules]`
   - `A <Name> is a [P/T] [colors] [Types] creature/artifact [with rules]`
   - `<Name>s are [P/T] [colors] [Types] creatures/artifacts [with rules]`
2. Synthesizes a create line (e.g. `create a 4/2 black green Zombie creature token named Charger with trample, haste.`) and appends it to rules_text before the main parse.
3. Skips names that are already in `common_tokens_list` (avoids duplicate detection for common tokens like Food whose type is defined in their own reminder text).

### Bug 5 — Empty-name token not filtered ✅
`"Whenever you create an artifact token, draw a card."` produced `{name: "", cardtype: "Token Artifact"}`. The `cardtype == "Token"` guard didn't catch it. Fixed: added `if not this_token["name"]: continue` plus a `_bad_names` set (`{"or more", "one", "many", "those", ...}`) for names that are artifacts of parsing replacement-effect wording.

### Bug 6 — Common token inside quoted token rules not detected ✅
`"The Golden Snitch"` had rules `"... creates a Treasure token."` embedded inside its own quoted ability. Fixed: after the main parse loop, each specialized token's `rules` field is recursively parsed via `parse_tokens_from_rules_text` to detect common tokens; results are merged into the outer `common_tokens` list.

### Bug 7 — Custom keyword reminder text from earlier line not picked up ✅
`Nulllink (Damage dealt by a source with nulllink...)` defined earlier in the rules → token with `nulllink` keyword got no reminder text. Fixed: added `_extract_inline_reminders(rules_text)` that pre-scans every line for `keyword (reminder text)` patterns and builds a per-parse dict; this is merged into the ability words lookup used by `_inject_ability_reminder_text`.

### Bug 8 — Role token inside parenthetical with preceding non-token sentence ✅
`Unforgivable (As an additional cost to cast this spell, create an Imprisoned Role token...)` — the opening `(` came before `create`, so slicing `original_words` at `create` lost the parenthetical context. Fixed: role handler now searches the full unsliced `line` for the parenthetical first; also strips the "As an additional cost to cast this spell, create ... Role token ... you control." sentence from role rules.

---

## Files Inventory

| File | Status |
|---|---|
| `src/integration/cockatrice.py` | ✅ Fixed (T1) — reads `deck.tokens` dict; `<reverse-related>` normalization fixed; `_Tokens.json` load removed |
| `src/token_generation/token_parser.py` | ✅ All parser bugs fixed (T2, T7) — `_expand_reminder_definitions`, `_extract_inline_reminders`, `_inject_ability_reminder_text`, X/X P/T, legendary flag, empty-name guard, recursive common-token scan |
| `src/core/card.py` | ✅ `get_tokens()` extended (T4) — scans front, back (DFC), subspell faces; all `rules1`–`rules6` slots |
| `src/core/deck.py` | `get_tokens()` runs discovery on whole deck; `_from_json_new_format` loads `tokens` dict |
| `src/core/ability.py` | `AbilityElements` class kept as fallback; ability words now managed via `config/ability_words.json` |
| `src/ui/app.py` | ✅ Token CRUD routes (T3); `_apply_token_discovery` (T4); ability-words routes (T5); `token_data` returns `alt_images_base64` (T6); publish copies `_N` alt art variants (T6) |
| `src/ui/helpers.py` | ✅ `card_from_editor_dict` extended (T3); `load_ability_words` / `save_ability_words` (T5); `alt_art_count` in token dict (T6) |
| `src/ui/templates/deck.html` | ✅ Token editor (T3); disable-auto-tokens checkbox + discovered-tokens panel (T4); alt art count badge in gallery + alt art strip in editor (T6) |
| `src/ui/templates/settings.html` | ✅ Ability Words management section (T5): table + add/delete forms |
| `src/ui/static/js/main.js` | ✅ Full token editor wiring (T3); `_updateDiscoveredTokensPanel`, `disable_auto_tokens` (T4); orphan warning row with Delete button in Assembly Line (T5); `_updateTokenAltArtStrip` (T6) |
| `src/ui/static/css/style.css` | ✅ Token editor styles (T3); discovered tokens panel (T4); assembly orphan warning (T5); alt art badge + strip (T6) |
| `src/services/cockatrice_exporter.py` | No changes needed — calls `update_cockatrice` |
| `config/common_tokens.json` | Common token definitions used by parser and `_apply_token_discovery` |
| `config/ability_words.json` | ✅ Created (T5) — configurable ability word definitions; managed via Settings page |
| `config/ability_words.example.json` | ✅ Template |
| `tests/conftest.py` | ✅ `mock_common_tokens` fixture |
| `tests/test_token_discovery/test_token_parser.py` | ✅ Parametrized test runner |
| `tests/test_token_discovery/fixtures/token_test_cases.json` | ✅ 66 test cases; all passing |

---

## Additional Features

### ✅ F1: Orphaned Tokens

Tokens whose `source_cards` list is empty are shown with:
- A yellow outline in the token gallery (`token-gallery-item--orphan`)
- A warning message below the image in the token editor
- An amber warning bar with a "Delete Token" button in the Assembly Line tab when a staged token entry has `source_cards: []`

### F2: DFC Tokens (Tokens That Transform)

Not supported. DFC tokens are rare and complex. The token editor only supports single-faced tokens.

### ✅ F2b: Custom Ability Word Reminder Text

`config/ability_words.json` stores configurable ability words (preset: Decayed, Shadow, Protection from everything, Anarky). The token parser's `_inject_ability_reminder_text()` function scans every keyword-only line in the token rules text (≤ 4 words, no `{`, no existing parenthetical) and appends the configured `selfDescription` in parentheses. Also handles comma-separated keyword lists (e.g. `"Haste, lifelink, decayed"` → injects reminder for `decayed`). Falls back to hardcoded `AbilityElements` if the config file is missing. Users manage ability words via Settings → "Ability Word Reminder Text."

### ✅ F3: Multiple Artworks Per Token — Workflow

**To forge and publish a token with numbered-only artworks** (e.g. `Artwork/Zombie_1.jpg`, `Artwork/Zombie_2.jpg` but no `Artwork/Zombie.jpg`):
1. Tokens tab → click the token → opens token editor
2. Click Forge → renderer finds all `Artwork/<name>_N.jpg` variants via `find_cards_with_card_name` and generates `Staging/<name>_N.jpg` for each
3. Token appears in Assembly Line with the first variant as its thumbnail
4. Click Publish → copies each `Staging/<name>_N.jpg` → `Tokens/<name>_N.jpg`

**Note**: Auto-discovery (triggered when forging a card like Tank Dempsey) only stages a token if something changed — new token or a `source_cards` update. If the token already exists and is already attributed to that card, nothing gets staged and nothing appears in the Assembly Line for the token. To force a token re-forge, open it directly in the token editor.

### ✅ F3: Multiple Artworks Per Token

`create_card_image_from_Card` (via `find_cards_with_card_name`) already discovers and renders all `Artwork/<name>_N.jpg` variants into the Staging dir. Added in T6:
- **Publish**: copies `Staging/<name>_N.jpg` → `Tokens/<name>_N.jpg` for all N
- **Gallery badge**: `alt_art_count > 0` shows a "N arts" badge on the token thumbnail
- **Token editor strip**: "Alternate Artworks" section below the source-cards panel shows thumbnails of all `Tokens/<name>_N.jpg` variants; refreshes after each forge
- **`token_data` endpoint**: returns `alt_images_base64` list (checks Staging first, falls back to Tokens)
- **`helpers.py`**: `alt_art_count` field added to each token dict at page load
- Cockatrice exporter needed no changes — it already iterated `_N` variants

### ✅ F4: Token Discovery for DFC Back Faces and Subspells

`card.get_tokens()` scans front face (`rules`, `rules1`–`rules6`), DFC back face (`.back`), and subspell face (`.subspell`) via a shared `_parse_face()` helper. Sagas are covered because their chapter rules use `rules1`–`rules6` slots.

### ✅ F5: Common Tokens in Cockatrice Predefined Zone

Common tokens (Clue, Treasure, Food, etc.) always appear in the `.cod` predefined zone even when no local image exists. Cockatrice prints a warning for missing images and uses its built-in image or a blank.

---

## Implementation History

### ✅ Phase T1: Fix Cockatrice Predefined Tokens

**Files changed**: `src/integration/cockatrice.py`

1. Replaced `Deck.from_json(... _Tokens.json ...)` with code that reads `deck.tokens` and constructs `Card` objects directly
2. Common tokens without local images still appear in `tokens.xml` and the `.cod` predefined zone
3. Fixed `<reverse-related>` normalization: source card names run through the same normalization as card names in `custom.xml`
4. Fixed `.cod` predefined tokens zone: uses `set()` to deduplicate
5. Removed now-unused `Deck` import from `cockatrice.py`

### ✅ Phase T2: Unit Tests — Token Discovery

**Files created**: `tests/conftest.py`, `tests/test_token_discovery/__init__.py`, `tests/test_token_discovery/test_token_parser.py`, `tests/test_token_discovery/fixtures/token_test_cases.json`  
**Files changed**: `src/token_generation/token_parser.py`

Infrastructure: `mock_common_tokens` pytest fixture; parametrized test runner over `token_test_cases.json`.

Parser bugs fixed in original T2 session:
- **`(create` in reminder text**: strips leading `(` before "create" detection
- **`"a number of X tokens"` phrasing**: added "Number" and "Of" to exclusion list
- **`keyword, "quoted ability"` formatting**: splits `Reach, "{t}: Add {G}."` into `Reach\n{t}: Add {G}.`

All remaining bugs (Bugs 1–8 above) fixed in T7 session. **66/66 tests pass.**

### ✅ Phase T3: Manual Token Creation in Tokens Tab

**Files changed**: `deck.html`, `main.js`, `app.py`, `style.css`, `helpers.py`

1. `+ Create Token` button in Tokens tab toolbar
2. Token editor reuses `#card-editor-panel` in token mode (hides mana/rarity/qty/DFC/subspell/tags; shows color picker and source cards panel)
3. Flask routes: `GET /deck/<name>/token-data`, `POST /deck/<name>/forge-token`, `POST /deck/<name>/stage-delete-token`
4. Publish and discard endpoints handle `_TOKEN_<name>` staging keys; token images go to `Tokens/`
5. Assembly Line shows token rows with a `(token)` label
6. Token gallery items with no `source_cards` show yellow orphan outline
7. Token delete: confirmation dialog → staged deletion → applied on publish

Token staging key: `_TOKEN_<name>` in `_staging.json` with `is_token: True`. Token JSON is flat (no `front`/`back` nesting).

### ✅ Phase T4: Forge-Time Auto-Discovery + Card Editor Token Panel

**Files changed**: `src/core/card.py`, `app.py`, `deck.html`, `main.js`, `style.css`

1. `card.get_tokens()` extended to scan back face and subspell face via `_parse_face()` helper
2. `_apply_token_discovery(folder_path, raw_deck, deck_key, prev_deck_key, card_obj, staging)` helper in `app.py`:
   - Deduplicates discovered tokens by name (case-insensitive)
   - Adds `deck_key` to `source_cards` on existing matching tokens
   - Creates placeholders and stages new tokens
   - Handles renames (`prev_deck_key` → `deck_key` when a subspell rename occurs)
   - Orphan detection: removes card from `source_cards` of tokens no longer discovered; stages the update
   - Called from `_do_forge`, `forge_one`, and `forge_all`
3. Card editor right pane gains:
   - `#ef-disable-auto-tokens-row` — checkbox to skip token discovery for this card (persisted in deck JSON via publish)
   - `#ef-discovered-tokens-panel` — shows discovered tokens after forge with New/Updated/Orphaned badges
4. Forge response includes `discovered_tokens: [{ name, cardtype, power, toughness, is_new, is_orphaned }]`

Known intentional gap: the discovered-tokens panel only updates after clicking Forge, not live as the user types.

### ✅ Phase T5: Orphaned Token Flow + Ability Words

**Files changed**: `app.py`, `helpers.py`, `main.js`, `style.css`, `settings.html`  
**Files created**: `config/ability_words.json`, `config/ability_words.example.json`

1. **F1 (orphaned tokens)**: `assembly-line-data` includes `source_cards` for token entries; Assembly Line row shows amber warning bar with "Delete Token" button when `source_cards` is empty
2. **F2b (ability words)**: `_inject_ability_reminder_text()` in `token_parser.py` loads from `config/ability_words.json`; Settings page has full Ability Words management (table + add/delete). Routes: `POST /settings/ability-words/add`, `POST /settings/ability-words/delete`

### ✅ Phase T6: Multiple Artworks Per Token (F3)

**Files changed**: `app.py`, `helpers.py`, `deck.html`, `main.js`, `style.css`

1. `helpers.py`: `alt_art_count` added to each token dict — counts `<name>_N.jpg` files in `Tokens/`
2. `token_data` endpoint: returns `alt_images_base64` list — collects staged variants from `Staging/`, falls back to `Tokens/`
3. `publish_assembly_line`: after copying primary token image, copies all `Staging/<name>_N.jpg` → `Tokens/<name>_N.jpg`
4. `deck.html` gallery: "N arts" badge (`token-alt-art-badge`) in bottom-right corner when `alt_art_count > 0`
5. `deck.html` editor: `#editor-token-alt-art-section` div added to preview pane
6. `main.js`: `_updateTokenAltArtStrip(altImages)` — renders thumbnails; called on token load, after forge (with a re-fetch), and cleared on close/new-token
7. `style.css`: `.token-alt-art-badge`, `.editor-token-alt-art-section`, `.editor-token-alt-art-strip`, `.token-alt-art-thumb`

### ✅ Phase T7: Parser Bug Fixes

**Files changed**: `src/token_generation/token_parser.py`, `tests/test_token_discovery/fixtures/token_test_cases.json`

Fixed all 8 parser bugs (Bugs 1–8 above). Added:
- `_split_sentences_respecting_quotes()` — sentence splitter that respects quoted content
- `_expand_reminder_definitions()` — pre-processing pass for reminder-text token definitions
- `_extract_inline_reminders()` — pre-scans rules for inline `keyword (reminder text)` definitions
- Updated `_inject_ability_reminder_text()` — comma-split multi-keyword handling + inline reminder support
- Updated test cases: reminder-text-defined tokens use `"Token Creature"` / `"Token Artifact"` cardtype (consistent with all other specialized tokens); Witch toughness corrected from 5 to 4.

**Test suite: 66/66 passing.**

---

## Appendix: Cockatrice Token XML Structure

```xml
<!-- tokens.xml entry -->
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

`<reverse-related>` must match the normalized card name in `custom.xml`. Current normalization:
```python
name = raw.replace('\u2019',"'").replace('\u2018',"'")
         .replace('"','&quot;').replace("."," ").replace("'","")
         .replace(" // ", " -- ")
```
