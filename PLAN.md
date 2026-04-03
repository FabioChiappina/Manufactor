# Manufactor — Implementation Plan for Remaining TODOs

## Context

The Manufactor web UI supports browsing decks, viewing card galleries with charts/stats, basic land management, and now a full tab-based card-editing workflow. The goal is to complete the Forge → Assembly Line → Publish pipeline.

---

## Status Legend
- ✅ **Done** — fully implemented and working
- 🔲 **Next** — immediate next step
- ⬜ **Pending** — not yet started

---

## Architecture Overview

### Key concepts

| Concept | Description |
|---|---|
| **Staging area** | A `Staging/` folder per deck and a `_staging.json` sidecar file. When you Forge a card, its preview image is saved to `Staging/<CardName>.jpg`. The sidecar records original + updated card data and the staged image path. |
| **Tab navigation** | Summary section stays at the top (commanders, charts, mana breakdown). Below it: three tabs — **Cards**, **Tokens**, **Assembly Line (N)**. |
| **Split-panel editor** | Clicking a card opens an inline split panel within the Cards tab (image left, form/JSON editor right). No separate page. |
| **JSON / Form toggle** | Editor switches between a structured form and a raw CodeMirror JSON editor. |
| **Publish Assembly Line** | Copies staged images to `Cards/` and `Printing/`, then runs the Cockatrice exporter. |

### Staging JSON (`<FolderName>_staging.json`)
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

## ✅ Phase 1 — Tab Navigation + Inline Card Editor (Core UI)

**Files changed:** `deck.html`, `style.css`, `main.js`, `app.py`, `helpers.py`, `base.html`

### Completed
- `deck.html` full rewrite: Cards / Tokens / Assembly Line tabs below fixed summary section
- Tab switching (pure JS), URL hash routing (`#cards`, `#tokens`, `#assembly`, `#edit/CardName`, `#new-card`)
- Assembly Line badge (`data-staged-count` from Flask, highlighted when > 0)
- Inline split-panel editor (`#card-editor-panel`) with header, preview pane, form/JSON pane
- `← Cards` back button closes editor and returns to gallery
- `+ Create Card` button opens blank editor (always dirty)
- `base.html`: added `{% block extra_head %}` and `{% block extra_scripts %}` for CodeMirror CDN
- `helpers.py`: `get_staging_path`, `load_staging`, `save_staging` added
- `app.py`: `staged_count` passed to `deck_details`; `card_data` JSON endpoint added; old `card_editor` route redirected to deck page with hash
- Bug fix: `getCanonicalItems()` scoped to `#cards-tab-main` so token gallery items never bleed into the cards list
- Cards tab count badge (`Cards 99`) added to tab button
- Token images load from `Tokens/` subfolder per deck

---

## ✅ Phase 2 — JSON / Form Toggle Editor

**Files changed:** `deck.html`, `style.css`, `main.js`

### Completed
- Form mode: Name, Mana Cost (plain text with brace-notation placeholder), Card Type dropdown, Subtype, Rules textarea, Power, Toughness, Rarity dropdown, Flavor, Legendary/Basic/Snow/Token checkboxes
- JSON mode: CodeMirror 5 loaded from CDN, lazy-initialized on first switch
- Form↔JSON sync in both directions (JSON→Form validates before switching)
- Change detection: `_originalJson` snapshot on editor open; dirty flag enables Forge button (amber→red gradient)
- Forge is a **stub** for now (marks not-dirty, optionally closes editor) — real implementation in Phase 3
- Publish button disabled until `staged_count > 0`

---

## ✅ Phase 9 — Card Legitimacy Filter *(implemented early, folded into Phase 1+2)*

**Files changed:** `deck.html`, `main.js`

### Completed
- "Card Legitimacy" dropdown in Cards tab toolbar: **Any / Only Real / Only Custom**
- Filters by `data-real` attribute (already present on card gallery items)
- Wired into `applyCardControls` alongside existing MV and type filters

---

## 🔲 Phase 3 — Forge (Staged Image Generation)

**Files to change:** `app.py`, `src/services/image_generator.py` (minor), `src/ui/helpers.py`

### 3a. New `/deck/<name>/card/<card>/forge` endpoint (POST)
1. Receive updated card JSON from request body (`Content-Type: application/json`)
2. Build a `Card` object from the dict (using `CardBuilder` or `Deck.from_json` logic — investigate which is simpler)
3. Call `ImageGenerator.generate_single_card_image(card, save_path=staging_path, include_printing=False)`
4. Write/update `_staging.json` sidecar: `{ original, updated, staged_image_path, disable_auto_tokens }`
5. Return JSON: `{ "image_base64": "data:image/jpeg;base64,...", "staged_count": N }`

### 3b. Frontend wiring (in `main.js` `onForgeClick`)
- Replace the stub with a real `fetch` POST to the forge endpoint
- On success: call `updatePreview(data.image_base64)`, update `_stagedCount`, refresh `#assembly-badge` text and `assembly-badge--active` class, call `updateButtonStates()`
- Mark `_editorIsDirty = false` after successful forge

### 3c. Artwork detection (already partially done)
- `card_data` endpoint already returns `_artwork_found` / `_artwork_hint`
- These are already shown in the editor header as green/amber status
- No additional work needed here

### Notes
- Investigate `image_generator.py` to find the right entry point for single-card rendering
- Staging folder (`Staging/`) should be created if it doesn't exist
- The forge endpoint should work for both existing cards (update) and new cards (create placeholder in deck JSON with `complete: 0`)

---

## ⬜ Phase 4 — Assembly Line Tab

**Files to change:** `deck.html`, `style.css`, `main.js`, `app.py`

### 4a. Assembly Line tab content (loaded via AJAX on tab click)
- `GET /deck/<name>/assembly-line-data` → JSON list: `[{ card_name, original_image_base64, staged_image_base64 }, ...]`
- For each staged card render:
  ```
  [Original image]  →  [Staged image]   [Discard button]
  ```
- Discard button: `POST /deck/<name>/card/<card>/discard` → removes from `_staging.json`, returns new `staged_count`
- "Add Entire Deck to Assembly Line" button: `POST /deck/<name>/forge-all` (long-running; use SSE or polling for progress)
- Pinned "Publish Assembly Line" button (full-width green, always visible while scrolling)
  - Disabled if `staged_count = 0`

### 4b. New routes
```
GET  /deck/<name>/assembly-line-data         → JSON list of staged cards with image paths
POST /deck/<name>/card/<card>/discard        → remove from staging, return new staged_count
POST /deck/<name>/forge-all                  → forge every card into staging
```

---

## ⬜ Phase 5 — Publish Assembly Line

**Files to change:** `app.py`, new `src/services/publisher.py`

### 5a. Confirmation dialog
- `<dialog>` element: "Publish **N** staged changes?" → [Yes] [Review Changes] [Cancel]
- "Review Changes" switches to Assembly Line tab

### 5b. Publish endpoint: `POST /deck/<name>/publish-assembly-line`
1. Load `_staging.json`
2. For each staged card:
   - Copy `Staging/<CardName>.jpg` → `Cards/<CardName>.jpg`
   - Regenerate printing image → `Printing/<CardName>.jpg`
   - Update `complete` flag in deck JSON
3. Run `CockatriceExporter.export_deck(...)`
4. Clear `_staging.json`
5. Return: `{ "cards_updated": N, "total_cards": M, "printing_ok": true, "cockatrice_ok": true }`
6. Frontend: toast with stats, reset badge to 0

---

## ⬜ Phase 6 — Create Card & Create Deck

**Files to change:** `deck.html`, `app.py`, new `templates/create_deck.html`

### 6a. Create Card
- Already wired: `+ Create Card` button opens blank editor, always dirty
- **Remaining**: On Forge of a new card, add placeholder entry to deck JSON (`complete: 0`) and add to staging
- On Publish: card becomes permanent in deck JSON

### 6b. Create Deck
- `GET /deck/new` → `create_deck.html`
- Fields: Deck Name, Set Name (auto-computed, user-overridable), Description, Format
- Set name auto-computation: strip "The/A/An", take first 3 letters uppercase, check uniqueness against existing decks, append digits on collision
- `POST /deck/new` → creates folder + empty deck JSON + empty staging JSON → redirect to `/deck/<name>#cards`

---

## ⬜ Phase 7 — Deck Info Editing & Token Association

**Files to change:** `deck.html`, `app.py`, `style.css`

### 7a. Deck info editing
- Pencil icon in summary section → inline edit form (Deck Name, Set Name, Description, Format, Commander)
- `POST /deck/<name>/update-metadata` → save; renaming also renames the folder and JSON file

### 7b. Token association in card editor
- Collapsible "Tokens" section in editor right panel
- Shows tokens detected from rules text via `token_parser.parse_tokens_from_rules_text()`
- Per-token checkbox: "Disable auto-generation" → saves `disable_auto_tokens: true` in card JSON
- On Forge: auto-forge + stage associated tokens (unless disabled)

---

## ⬜ Phase 8 — Advanced Card Types

**Files to change:** `deck.html`, `main.js`, `app.py`

### 8a. Double-faced cards
- "Flip" button in editor header when `double_faced_type` is set
- Toggles between front/back face fields; preview updates accordingly
- JSON: `{ "front": {...}, "back": {...}, "double_faced_type": "transform|mdfc" }`

### 8b. Subspells (Adventures, Omens)
- "Add Subspell" toggle expands: Subspell Name, Mana (plain text), Type, Subtype, Rules
- Maps to `card["subspell"]` — renderer already handles this

### 8c. Token flag
- "This is a Token" checkbox already in form → sets `front.token: 1`
- Token cards already show "TOKEN" badge in gallery grid (implemented)

---

## ⬜ Phase 10 — Publish Result Message

Covered by Phase 5 return payload. Display as a persistent toast/banner with `cards_updated`, `total_cards`, `printing_ok`, `cockatrice_ok`.

---

## ⬜ Phase 11 — Unit Tests

**New files:** `tests/test_ui/`, `tests/test_services/`

- Staging sidecar load/save
- Forge endpoint with mock card data
- Publish pipeline (mock filesystem)
- Set name auto-computation
- Assembly line discard
- Token association detection

---

## Not in scope (future work)
- **Planeswalker creation**: New Photoshop frames + new rendering code needed. Separate epic.
- **Artwork upload/crop in UI**: File upload endpoint + PIL crop. Nice-to-have later.

---

## Critical Files

| File | Role |
|---|---|
| `src/ui/templates/deck.html` | Tab system, editor panel, token gallery ✅ |
| `src/ui/static/js/main.js` | Tab switching, editor, filters, Forge/Publish ✅ (Forge stub) |
| `src/ui/static/css/style.css` | All new styles ✅ |
| `src/ui/app.py` | Routes: card_data ✅, forge 🔲, discard 🔲, publish 🔲, assembly-line-data 🔲, forge-all 🔲 |
| `src/ui/helpers.py` | Staging helpers ✅, compute_setname ⬜ |
| `src/services/image_generator.py` | Single-card render for Forge 🔲 |
| `src/services/cockatrice_exporter.py` | Called from Publish — verify standalone 🔲 |

## New Files Needed

| File | Purpose |
|---|---|
| `src/ui/templates/create_deck.html` | Create new deck form ⬜ |
| `src/services/publisher.py` | Orchestrates copy-to-Cards, printing regen, Cockatrice export, staging clear ⬜ |

---

## Next Session: Start with Phase 3

**Goal**: Make the Forge button actually generate and stage a card image.

**Entry point investigation needed first**:
- Look at `src/services/image_generator.py` to find the right method for single-card rendering
- Check how `CardBuilder` or `Deck.from_json` builds a `Card` object from a raw dict
- Confirm `ImageGenerator` can accept a custom save path

**Then implement**:
1. `POST /deck/<name>/card/<card>/forge` in `app.py`
2. Update `onForgeClick` in `main.js` to call the real endpoint and handle the response
