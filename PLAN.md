# Manufactor — Implementation Plan for Remaining TODOs

## Context

The Manufactor web UI supports browsing decks, viewing card galleries with charts/stats, basic land management, and a full tab-based card-editing workflow. The goal is to complete the Forge → Assembly Line → Publish pipeline.

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

**Files changed:** `deck.html`, `style.css`, `main.js`, `app.py`

### Completed
- Form mode fields:
  - **Row 1:** Name (wide), Mana Cost (medium), Rarity dropdown (narrow auto-width)
  - **Row 2:** Supertypes (Legendary / Basic / Snow checkboxes), Card Type, Subtype
  - **Row 3:** Power (90px), Toughness (90px), Frame Filename (fill, with `<datalist>` autocomplete from `Assets/CardFrames/`), Double Faced Type dropdown (None / Transform / MDFC)
  - **Row 4:** Rules Text (6-row textarea)
  - **Row 5:** Flavor Text (2-row textarea)
- JSON mode: CodeMirror 5 loaded from CDN, lazy-initialized on first switch
- Form↔JSON sync in both directions (JSON→Form validates before switching)
- Change detection: `_originalJson` snapshot on editor open; dirty flag enables Forge button (amber→red gradient)
- Forge is a **stub** for now (marks not-dirty, optionally closes editor) — real implementation in Phase 3
- Publish button disabled until `staged_count > 0`
- `/card-frames` endpoint returns sorted list of `.jpg` filenames from `Assets/CardFrames/` for autocomplete
- `frame` and `double_faced_type` top-level fields serialized/deserialized in both form and JSON modes

---

## ✅ Phase 9 — Card Legitimacy Filter *(implemented early, folded into Phase 1+2)*

**Files changed:** `deck.html`, `main.js`

### Completed
- "Card Legitimacy" dropdown in Cards tab toolbar: **Any / Only Real / Only Custom**
- Filters by `data-real` attribute (already present on card gallery items)
- Wired into `applyCardControls` alongside existing MV and type filters

---

## ✅ Phase 12 — Inline Tag Editing *(implemented early)*

**Files changed:** `deck.html`, `style.css`, `main.js`, `app.py`

### Completed
- Tag chips with `×` remove button displayed in editor left pane (below artwork status)
- "+ Add Tag" opens an inline picker: filter input + scrollable list of existing deck tags not on this card
- Typing filters the list; unmatched non-empty input shows a *"Create new tag: …"* option
- `POST /deck/<name>/add-card-tag?name=<card>` — adds tag to card and to `metadata.tags` if new
- `POST /deck/<name>/remove-card-tag?name=<card>` — removes tag from card; removes from `metadata.tags` if no other card uses it
- Both endpoints persist changes immediately to the deck JSON file
- Gallery item `data-tags` attribute updated in-place so group-by-tag still works without a page reload
- `card-data` endpoint now also returns `_deck_tags` (sorted list of all deck-level tags)

---

## ✅ Phase 3 — Forge (Staged Image Generation)

**Files changed:** `app.py`, `src/ui/helpers.py`, `src/ui/static/js/main.js`

### Completed
- `helpers.py`: `card_from_editor_dict(card_dict, setname)` — builds `Card` object(s) from editor JSON; handles single-faced and DFC (returns `[front_card, back_card]`)
- `app.py`: `POST /deck/<name>/card/<card>/forge` — builds Card, generates image to `Staging/`, updates `_staging.json` sidecar (`original`, `updated`, `staged_image_path`, `is_new`), returns `{ image_base64, staged_count }` (+ `back_image_base64` for DFC). New cards get a placeholder entry in deck JSON with `complete: 0`
- `main.js`: `getEditorJson()` helper (reads form or CodeMirror JSON mode); `onForgeClick()` — POSTs to forge endpoint, updates preview + assembly badge, promotes new cards to `_currentCardName`
- `app.py` `card_data` endpoint: now checks `_staging.json` first and returns staged `updated` data + staged image when available, so reopening a staged card shows the pending state
- `deck.html` / `main.js`: `close-forge-btn` starts `disabled`; `updateButtonStates()` now also manages `close-forge-btn` (enabled iff dirty/new, same as Forge button)

---

## ✅ Phase 4 — Assembly Line Tab

**Files changed:** `deck.html`, `style.css`, `main.js`, `app.py`

### Completed
- **AJAX-loaded tab content**: Assembly Line tab body is fetched fresh on every tab switch via `GET /deck/<name>/assembly-line-data`
- **3-column responsive grid**: Cards displayed 3-per-row at full width, 2-per-row ≤1100px, 1-per-row ≤768px; column dividers via CSS `nth-child`
- **Card row layout**: `.assembly-card-header` flex row with card name (left) + Discard button (top-right); below it `.assembly-card-images` showing Original → arrow → Staged at 240px wide
- **Discard**: `POST /deck/<name>/card/<card>/discard` removes from `_staging.json`, row animates out, `_updatePublishBar()` refreshes count
- **Forge Entire Deck**: `POST /deck/<name>/forge-all` forges every non-real card in the deck into staging; on success calls `_updatePublishBar()` + `loadAssemblyLineData()`
- **Publish Assembly Line button**: full-width green, always visible; disabled when `staged_count = 0`; shows live count `Publish Assembly Line (N)`
- **Empty state**: "No staged changes…" message spans all 3 columns via `grid-column: 1 / -1`
- **`_updatePublishBar(count)`**: single source of truth — updates tab badge, publish-count span, and button disabled state

### New routes
```
GET  /deck/<name>/assembly-line-data         → JSON list of staged cards with image data
POST /deck/<name>/card/<card>/discard        → remove from staging, return new staged_count
POST /deck/<name>/forge-all                  → forge every card into staging
```

---

## ✅ Phase 5 — Publish Assembly Line

**Files changed:** `app.py`, `deck.html`, `style.css`, `main.js`

### Completed
- **Confirmation dialog** (`<dialog>`): "Publish N staged change(s)?" → [Publish] [Review Changes]; centered in viewport via `position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%)`
- **Publish endpoint**: `POST /deck/<name>/publish-assembly-line`
  1. Load `_staging.json`
  2. For each staged card: copy `Staging/<CardName>.jpg` → `Cards/<CardName>.jpg` via `shutil.copy2`
  3. Regenerate printing image via `create_printing_image_from_Card`
  4. Update `complete: 1` flag in deck JSON
  5. Run `CockatriceExporter.export_deck()`
  6. Clear `_staging.json`
  7. Return `{ published_cards, cards_updated, printing_ok, cockatrice_ok }`
- **Publish log**: inline log panel below the publish button shows per-step status (cards updated, printing regen, Cockatrice export) with green/red/gray entries
- **Gallery image refresh**: after publish, `_refreshGalleryImages(cardNames)` fetches `/card-data?name=...` for each published card and swaps the `<img src>` in the Cards tab gallery — no page reload needed
- **Changed filter**: "Changed" dropdown (Any / Yes / No) in Cards tab toolbar; filters by `data-staged` attribute on gallery items
- **Publish count always current**: `onForgeClick` now calls `_updatePublishBar(data.staged_count)` instead of manually patching the badge, so count stays in sync after every Forge

---

## ✅ Phase 10 — Publish Result Message

Covered by Phase 5 publish log (inline log panel below the publish button). Shows per-card and per-step status with color-coded entries (`publish-log-ok`, `publish-log-err`, `publish-log-skip`).

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

**Files to change:** `deck.html`, `main.js`, `app.py`, `style.css`

### 🔲 8a. Double-faced cards (partially done)

**What's implemented:**
- Front/Back face tabs visible in the editor left pane (always present)
- Switching face tabs updates both the form fields AND the preview image
- Preview shows the back card's `Cards/<BackName>.jpg` when on the Back tab; placeholder if no image exists
- `double_faced_type` dropdown in the form (None / Transform / MDFC) — maps to top-level JSON field
- Back face data serialized/deserialized in both form and JSON modes
- `card-data` endpoint returns `back_image_base64` by looking up the back face's `name` in `Cards/`

**What remains:**
- When editing the back face of a card that has no back face yet (single-faced), the double faced type dropdown should automatically choose transform as the double faced type.
- The double-faced type dropdown should always have the same value for both sides of a card, since it's a card-level attribute in the JSON (e.g., "double_faced_type" is at the same level as fields like "complete", "tags", "front", "back", ...). So editing the value of the dropdown on one face should cause the other face's value to update too, and forging that card should then cause BOTH the front and back face to be re-rendered.
- Creating a brand-new back face from scratch (typing a back name for the first time) is untested — confirm the round-trip works correctly through Forge.
- The `double_faced_type` value set in the UI should be passed through to the `Card` object during Forge so the renderer picks the correct MDFC/Transform frame automatically (Phase 3 dependency).

---

### ⬜ 8b. Multi-section rules text (Sagas, Planeswalkers, and similar)

Some card types use multiple named rules-text keys instead of a single `"rules"` field:

| Card type | JSON keys used | Description |
|---|---|---|
| **Saga** | `rules1`, `rules2`, `rules3` (+ more) | Each chapter (I, II, III…) has its own rules text; the renderer maps chapter number → rules key |
| **Planeswalker** | `rules1`, `rules2`, `rules3` (+ loyalty costs) | Each loyalty ability is a separate field; loyalty cost (e.g. `+1`, `-2`, `-8`) is stored alongside each rules section |
| **Class** | `rules1`, `rules2`, `rules3` | Each level-up tier has its own text block |

**What needs to happen in the UI:**
- When the card type is Saga, Planeswalker, or Class, the single Rules Text textarea should be replaced by a **dynamic multi-section editor**: one text area per chapter/ability, with `+` / `−` buttons to add or remove sections.
- For Sagas specifically, the chapter label (I, II, III, …) should be shown automatically.
- For Planeswalkers, each section needs an additional loyalty-cost input field (e.g. `"+1"`, `"−3"`, `"−8"`).
- The form serializer/deserializer must map between `rules1`/`rules2`/etc. and the multi-section UI.
- The renderer (`card_renderer.py`) already handles `rules1`/`rules2` for Sagas; check whether Planeswalker rendering is stubbed or fully absent before planning that sub-task.

**Note:** Full Planeswalker support also requires new Photoshop frame assets and updated rendering code — treat this as a separate sub-epic within Phase 8. Sagas and Classes are lower-hanging fruit since frame assets exist.

---

### ⬜ 8c. Subspells (Adventures, Omens)
- "Add Subspell" toggle expands: Subspell Name, Mana (plain text), Type, Subtype, Rules
- Maps to `card["subspell"]` — renderer already handles this

### ⬜ 8d. Token flag
- "This is a Token" checkbox already in form → sets `front.token: 1`
- Token cards already show "TOKEN" badge in gallery grid (implemented)

---

## ⬜ Phase 11 — Unit Tests

**New files:** `tests/test_ui/`, `tests/test_services/`

- Staging sidecar load/save
- Forge endpoint with mock card data
- Publish pipeline (mock filesystem)
- Set name auto-computation
- Assembly line discard
- Token association detection
- Tag add/remove endpoints (card and deck-level cleanup)

---

## Not in scope (future work)
- **Artwork upload/crop in UI**: File upload endpoint + PIL crop. Nice-to-have later.
- **Planeswalker frame assets**: New Photoshop frames needed before full PW rendering is possible. Blocked on art assets, not code.

---

## Critical Files

| File | Role |
|---|---|
| `src/ui/templates/deck.html` | Tab system, editor panel, tag section, token gallery, assembly line, confirm dialog ✅ |
| `src/ui/static/js/main.js` | Tab switching, editor, filters, tag editing, Forge, Assembly Line, Publish ✅ |
| `src/ui/static/css/style.css` | All new styles ✅ |
| `src/ui/app.py` | Routes: card_data ✅, card-frames ✅, add/remove-card-tag ✅, forge ✅, discard ✅, publish ✅, assembly-line-data ✅, forge-all ✅ |
| `src/ui/helpers.py` | Staging helpers ✅, card_from_editor_dict ✅, compute_setname ⬜ |
| `src/services/image_generator.py` | Single-card render used by Forge ✅ |
| `src/services/cockatrice_exporter.py` | Called from Publish endpoint ✅ |

## New Files Needed

| File | Purpose |
|---|---|
| `src/ui/templates/create_deck.html` | Create new deck form ⬜ |

---

## Next Steps

**Recommended order:**
1. **Phase 8a remaining** — DFC dropdown sync, auto-select Transform on back face, `double_faced_type` passed to renderer
2. **Phase 6** — Create Deck page (Create Card already works via Forge)
3. **Phase 7** — Deck metadata editing + token association in editor
4. **Phase 8b–d** — Multi-section rules text, subspells, token flag
5. **Phase 11** — Unit tests
