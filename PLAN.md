# Manufactor — Implementation Plan for Remaining TODOs

## Context

The Manufactor web UI currently supports browsing decks, viewing card galleries with charts/stats, and basic land management via the mana breakdown ribbon. The goal of this plan is to add a full card-editing workflow with a staging/assembly-line publish system, deck creation, and a suite of card-editor enhancements. Everything below is sequenced by dependency — each phase unblocks the next.

---

## Architecture Overview

### Key new concepts

| Concept | Description |
|---|---|
| **Staging area** | A `Staging/` folder per deck and a `_staging.json` sidecar file. When you Forge a card, its preview image is saved to `Staging/<CardName>.jpg`. The sidecar records which cards have staged changes and their updated card data. |
| **Tab navigation** | `deck.html` maintains the summary section near the top (with the images of the commanders, the bar graphs, the description, and the colors and basic lands breakdown as currently present), but the bottom section (currently just the Cards list with filters, etc.) is refactored into three tabs: **Cards**, **Tokens**, **Assembly Line (N)**. |
| **Split-panel editor** | Clicking a card in Cards tab opens an inline split panel (card image left, editor right) — no separate page. The old `card_edit.html` / `card_editor` route becomes unused. |
| **JSON / Form toggle** | The right-hand editor can switch between a structured form view and a raw JSON editor (CodeMirror, loaded from CDN). |
| **Publish Assembly Line** | Copies staged images from `Staging/` to `Cards/` and `Printing/`, then runs the Cockatrice exporter. |

### Staging JSON (`DeckName_staging.json`)
```json
{
  "CardName": {
    "original": { ...original card dict from deck JSON... },
    "updated": { ...edited card dict... },
    "staged_image_path": "Staging/CardName.jpg",
    "disable_auto_tokens": false
  }
}
```
Stored at `DECK_PATH/<FolderName>/<FolderName>_staging.json`.

---

## Phase 1 — Tab Navigation + Inline Card Editor (Core UI)

**Files changed:** `deck.html`, `style.css`, `main.js`, `app.py`

### 1a. Tab system in deck.html
- Add `<div class="deck-tabs">` with three tab buttons: **Cards**, **Tokens**, **Assembly Line (0)**
- Default active tab: **Cards**
- Tab content panes wrap existing sections:
  - `#tab-cards` — card gallery + controls (existing content)
  - `#tab-tokens` — token gallery (see details below)
  - `#tab-assembly` — empty for now
- Tab switching: pure JS, toggle `active` class
- Assembly Line badge count: `<span class="assembly-badge">0</span>` in the tab button; JS reads from a `data-staged-count` attribute on the page (populated by Flask)
- Highlight badge when count > 0 (CSS class `assembly-badge--active`)
- URL hash support: `#cards`, `#tokens`, `#assembly` to deep-link to a tab

### 1b. Inline split-panel editor
When any card in the Cards tab is clicked (instead of navigating to `card_edit.html`):
- A full-width panel `#card-editor-panel` slides up from the bottom or slides in from the right within `#tab-cards`
- Left half: `<img id="editor-card-preview">` — shows current card image (or placeholder); aspect ratio 5:7
- Right half: The editor (see Phase 2 for JSON/form toggle)
- Header: card name + "Forge" button (greyed initially) + "Close & Forge" button + "Publish Assembly Line" button (greyed initially)
- Back link: "← Back to deck"
- Opening the panel sets `window.location.hash = '#edit/' + encodeURIComponent(cardName)` so refresh works

**New Flask routes needed:**
```
GET  /deck/<deck_name>/card/<card_name>/data      → returns card JSON as JSON response
POST /deck/<deck_name>/card/<card_name>/forge     → renders staged image, returns base64 + staged count
POST /deck/<deck_name>/card/<card_name>/discard   → removes card from staging JSON
```

**Existing route to keep for compatibility:** `GET /deck/<deck_name>/card/<card_name>/edit` (can 301 to deck page with hash)

### 1c. Tokens tab initial content
The Tokens tab is a **unified token library** — tokens appear here from two sources, but are managed identically once present:
- **Auto-generated**: When a card is Forged and `disable_auto_tokens` is not set, tokens detected from its rules text are parsed by `token_parser.parse_tokens_from_rules_text()` and added to `deck["tokens"]` on Publish.
- **Manually created**: A "Create Token" button in the Tokens tab toolbar opens the split-panel editor with a blank token template (`token: 1` pre-set).

Initial tab content:
- Same card gallery grid as the Cards tab, populated from `deck["tokens"]` dict
- If `deck["tokens"]` is empty: a friendly empty-state message ("No tokens yet — tokens will appear here after you Forge cards that create them, or you can create one manually.")
- "Create Token" button in the toolbar (same as "Create Card" but opens with token template)
- Clicking any token → same split-panel editor flow; Forge/Publish pipeline is identical to cards

The auto/manual distinction only affects how tokens arrive in this tab, not how they're edited or published. Tokens staged in the Assembly Line (either auto-detected or manually created/edited) appear in the same before/after comparison view as cards.

**New routes (token-specific):**
```
GET  /deck/<deck_name>/token/<token_name>/data    → returns token JSON
POST /deck/<deck_name>/token/<token_name>/forge   → staged token image
POST /deck/<deck_name>/token/<token_name>/discard → remove from staging
```

---

## Phase 2 — JSON / Form Toggle Editor

**Files changed:** `card_edit.html` (repurposed as partial/macro), `style.css`, `main.js`, templates

### 2a. Form mode
Structured inputs matching the Anakin.json `front` shape:
- **Name** — text input
- **Mana Cost** — plain text input; the user types the cost directly using brace notation. Placeholder text shows examples: `{2}{u}{r}` for standard, `{w/u}` for hybrid, `{g/p}` for Phyrexian, `{2/b}` for generic hybrid. No parsing or widget — just free-form text, same format the renderer already expects.
- **Card Type** — dropdown (Creature, Instant, Sorcery, Enchantment, Artifact, Land, Planeswalker)
- **Subtype** — text input
- **Rules Text** — textarea (mana symbols in rules also use brace notation, same as renderer expects)
- **Power / Toughness** — text inputs
- **Rarity** — dropdown
- **Flavor** — text input
- **Legendary / Basic / Snow** — checkboxes
- For double-faced cards: a "Flip" toggle shows back-face fields
- For subspells: an "Add Subspell" toggle expands subspell section (name, mana, type, subtype, rules) — mana is also a plain text input with same placeholder
- Token toggle: "This is a token" checkbox → sets `token: 1` in JSON

### 2b. JSON mode
- A `<textarea id="json-editor">` containing pretty-printed JSON
- Load [CodeMirror 5 from CDN](https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js) with `mode/javascript/javascript.min.js` and `addon/lint/json-lint.js`
- Toggle switch "Form / JSON" at top of editor panel
- Switching Form→JSON: serialize form fields into JSON and display in CodeMirror
- Switching JSON→Form: parse CodeMirror content and populate form fields
- If JSON is invalid, show inline error and prevent toggle

### 2c. Change detection
- Track `originalJson = JSON.stringify(cardData)` on open
- On any input event in form mode or CodeMirror change event: compare to `originalJson`
- If different: enable Forge button (remove `disabled` / `btn-disabled` class), set `isDirty = true`
- If same: re-disable Forge button

---

## Phase 3 — Forge (Staged Image Generation)

**Files changed:** `app.py`, `src/services/image_generator.py` (minor), `src/ui/helpers.py`

### 3a. New `/deck/<name>/card/<card>/forge` endpoint (POST)
1. Receive updated card JSON from request body
2. Build a `Card` object from the dict (using `CardBuilder` or `Deck.from_json` logic)
3. Call `ImageGenerator.generate_single_card_image(card, save_path=staging_path, include_printing=False)`
4. Write/update `_staging.json` sidecar with original + updated data + staged image path
5. Return JSON: `{ "image_base64": "...", "staged_count": N }`
6. Frontend: update `#editor-card-preview` src with returned base64; update Assembly Line badge

### 3b. Staging folder management
- `helpers.py`: add `get_staging_path(deck_folder)` → `DECK_PATH/<folder>/Staging/`
- `helpers.py`: add `load_staging(deck_folder)` / `save_staging(deck_folder, data)`
- On page load for deck details, load staging sidecar → pass `staged_count` to template

### 3c. Artwork detection
- Before forging: check if `Artwork/<CardName>.jpg` (or `.png`) exists in the deck folder
- If exists: show a green message "✓ Artwork found" in the editor panel
- If missing: show a yellow warning "⚠ No artwork found at Artwork/<CardName>.jpg"

---

## Phase 4 — Assembly Line Tab

**Files changed:** `deck.html`, `style.css`, `main.js`, `app.py`

### 4a. Assembly Line tab content
- Loaded via AJAX when tab is clicked: `GET /deck/<name>/assembly-line-data` → returns HTML partial or JSON
- For each staged card:
  ```
  [Original image]  →  [Staged (forged) image]   [Discard button]
  ```
  - Original image from `Cards/<CardName>.jpg`
  - Staged image from `Staging/<CardName>.jpg`
  - Discard button: calls `POST /deck/<name>/card/<card>/discard`, removes from staging, re-renders
- "Add Entire Deck to Assembly Line" button: calls `POST /deck/<name>/forge-all` → background task that forges every card and adds to staging; shows a progress bar
- Pinned at top/bottom: **"Publish Assembly Line"** button (full-width, green, always visible while scrolling in the tab)
  - Greyed out if staged count = 0
  - Also greyed out while viewing a card with unsaved Forge (isDirty = true) in Cards tab

### 4b. New routes
```
GET  /deck/<name>/assembly-line-data         → JSON list of staged cards with image paths
POST /deck/<name>/card/<card>/discard        → remove from staging, return new staged_count
POST /deck/<name>/forge-all                  → forge every card into staging (long-running, use SSE or polling)
```

---

## Phase 5 — Publish Assembly Line

**Files changed:** `app.py`, new `src/services/publisher.py`

### 5a. Confirmation popup
- Clicking "Publish Assembly Line" shows a `<dialog>` element:
  > Publish **N** staged changes?
  > [Yes] [Review Changes] [Cancel]
- "Review Changes" switches to Assembly Line tab and closes dialog

### 5b. Publish endpoint: `POST /deck/<name>/publish-assembly-line`
1. Load `_staging.json`
2. For each staged card:
   - Copy `Staging/<CardName>.jpg` → `Cards/<CardName>.jpg`
   - Regenerate printing image: `create_printing_image_from_Card(...)` → `Printing/<CardName>.jpg`
   - Update the card's `complete` flag in deck JSON
3. Run `CockatriceExporter.export_deck(deck, ...)`
4. Clear `_staging.json`
5. Return JSON: `{ "cards_updated": N, "total_cards": M, "printing_ok": true, "cockatrice_ok": true }`
6. Frontend: show result toast with those stats, reset Assembly Line badge to 0

---

## Phase 6 — Create Card & Create Deck

**Files changed:** `deck.html`, `app.py`, new `templates/create_deck.html`

### 6a. Create Card
- "Create Card" button in Cards tab toolbar → opens the split-panel editor with blank card data
- JSON template pre-filled:
  ```json
  { "front": { "name": "", "mana": "", "cardtype": "Creature", "subtype": "", "rules": "", "power": "", "toughness": "" }, "quantity": 1, "rarity": "common" }
  ```
- Forge button enabled immediately (it's a new card, always "changed")
- On Forge: card gets added to staging AND a placeholder entry is added to deck JSON with `complete: 0`
- On Publish: card becomes permanent in deck JSON

### 6b. Create Deck
- New page `GET /deck/new` → `create_deck.html`
- Fields: Deck Name, Set Name (auto-computed from deck name, user can override), Description, Format
- Set name auto-computation:
  1. Strip leading "The " / "A " / "An "
  2. Take first 3 letters, uppercase
  3. Check existing `setname` values across all deck JSONs
  4. If collision: try removing vowels, then append incremented digits until unique
- On Create: `POST /deck/new` → creates folder + empty deck JSON + empty staging JSON → redirects to `/deck/<name>#cards`
- New deck starts on the Cards tab (empty gallery, summary section still visible at top showing zeroed-out stats)

---

## Phase 7 — Deck Info Editing & Token Association

**Files changed:** `deck.html`, `app.py`, `style.css`

### 7a. Deck info editing
- In the summary section, add an "Edit" pencil icon near the deck name/description
- Clicking opens an inline edit form: Deck Name, Set Name, Description, Format, Commander
- "Save" button: `POST /deck/<name>/update-metadata`
- Renaming a deck renames the folder and JSON file

### 7b. Token association in card editor
- A collapsible "Tokens" section in the card editor right panel
- Shows detected tokens from rules text (via `token_parser.parse_tokens_from_rules_text()`)
- Each entry: token name, checkbox to disable auto-generation for this card (saved to card JSON as `disable_auto_tokens: true` or per-token `disable_token_<name>: true`)
- When Forge is clicked, if `disable_auto_tokens` is not set, associated tokens are also forged and staged automatically

---

## Phase 8 — Advanced Card Types

**Files changed:** `deck.html`, card editor JS, `app.py`

### 8a. Double-faced cards
- In form mode, if `double_faced_type` is set (or user adds it): show a "Flip" button in editor panel header
- Flip toggles which face is being edited (front/back)
- The preview image changes to show the corresponding face's rendered image
- JSON structure: `{ "front": {...}, "back": {...}, "double_faced_type": "transform|mdfc" }`

### 8b. Subspells (Adventures, Omens)
- In form mode, "Add Subspell" toggle expands section with Subspell Name, Mana, Type, Subtype (Adventure/Omen), Rules
- Maps to `card["subspell"]` in JSON
- Existing `card_renderer.py` already handles rendering these — just needs UI wiring

### 8c. Token creation flag
- "This is a Token" checkbox in card editor → sets `front.token: 1` in JSON
- Token cards show a visual indicator (e.g., "TOKEN" badge) in the gallery grid

---

## Phase 9 — Real Cards Support & Filtering

**Files changed:** `deck.html`, `main.js`, `app.py`

- In card JSON: `real: 1` flag already exists in Anakin.json
- Toggle control in Cards tab toolbar: **All | Custom | Real**
- JS filters gallery by `data-real` attribute on card items
- Card items get `data-real="{{ card_data.real or 0 }}"` attribute in template

---

## Phase 10 — Publish Result Message

Already covered in Phase 5 (`{ "cards_updated": N, "total_cards": M, "printing_ok": ..., "cockatrice_ok": ... }`), display as a persistent toast/banner.

---

## Phase 11 — Unit Tests

**New files:** `tests/test_ui/`, `tests/test_services/`

- Test staging sidecar load/save
- Test forge endpoint with mock card data
- Test publish pipeline (mock filesystem)
- Test setname auto-computation
- Test assembly line discard
- Test token association detection

---

## Not in scope (future work)
- **Planeswalker creation**: Needs new Photoshop card frames + new rendering code in `card_renderer.py`. Track as separate epic.
- **Artwork upload/crop in UI**: Needs file upload endpoint + PIL crop logic. Nice-to-have later.

---

## Critical Files to Modify

| File | Changes |
|---|---|
| `src/ui/templates/deck.html` | Cards/Tokens/Assembly Line tab system, card editor panel, token gallery |
| `src/ui/static/js/main.js` | Tab switching, editor open/close, Forge/Publish logic, change detection, CodeMirror integration |
| `src/ui/static/css/style.css` | Tab styles, split-panel editor styles, staging badge, dialog |
| `src/ui/app.py` | ~15 new routes (forge, discard, publish, assembly data, create card/deck, update metadata, forge-all) |
| `src/ui/helpers.py` | `get_staging_path`, `load_staging`, `save_staging`, `compute_setname` helpers |
| `src/services/image_generator.py` | Minor: expose `generate_single_card_image` cleanly for staging path |
| `src/services/cockatrice_exporter.py` | Called from publish endpoint — verify it works standalone |

## New Files

| File | Purpose |
|---|---|
| `src/ui/templates/create_deck.html` | Create new deck form |
| `src/services/publisher.py` | `PublishService` — orchestrates copy-to-Cards, printing regen, Cockatrice export, staging clear |

---

## Implementation Order (Recommended)

1. **Phase 1** — Tab UI (no backend changes, just HTML/CSS/JS)
2. **Phase 2** — JSON/Form editor panel (frontend only)
3. **Phase 3** — Forge endpoint (first backend work, needs helpers.py staging functions)
4. **Phase 4** — Assembly Line tab
5. **Phase 5** — Publish (completes the core loop)
6. **Phase 6** — Create Card / Create Deck
7. **Phase 7** — Deck metadata editing + Token association in card editor
8. **Phase 8** — DFC / Subspell / Token flag
9. **Phase 9** — Real card filtering
10. **Phase 10/11** — Publish message & tests

---

## Verification

After Phases 1–5 (core loop):
1. Open a deck → see summary section at top, then Cards / Tokens / Assembly Line tabs below
2. Click a card → split panel opens with current image and JSON editor
3. Change a field → Forge button enables
4. Click Forge → preview image updates, Assembly Line badge shows (1)
5. Open Assembly Line tab → see before/after comparison
6. Click Publish → confirmation dialog → confirm → cards saved, Cockatrice updated, badge resets to 0
7. Open deck folder in Finder → verify `Cards/`, `Printing/`, and Cockatrice files updated
