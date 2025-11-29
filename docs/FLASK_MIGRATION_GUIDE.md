# Flask Migration Guide

This document provides a comprehensive plan for migrating the Manufactor UI from Gradio to Flask, enabling true multi-page navigation and clickable deck cards.

## Table of Contents
- [Why Migrate to Flask?](#why-migrate-to-flask)
- [What Will Change](#what-will-change)
- [What Will Stay the Same](#what-will-stay-the-same)
- [Architecture Overview](#architecture-overview)
- [Migration Plan](#migration-plan)
- [Implementation Details](#implementation-details)
- [Code Examples](#code-examples)
- [Testing Strategy](#testing-strategy)
- [Deployment](#deployment)

---

## Why Migrate to Flask?

### Gradio's Limitations (Discovered)

Based on our experience documented in [GRADIO_NAVIGATION_GUIDE.md](GRADIO_NAVIGATION_GUIDE.md), Gradio has fundamental limitations:

1. **No Multi-Page Support** - Single-page application only, limited to tabs
2. **No Clickable HTML** - HTML components are display-only, can't trigger Python functions
3. **Limited Navigation** - Column visibility toggling is unreliable
4. **Tab-Only Routing** - URL changes are limited to fragment identifiers (`#Details`)
5. **Not Designed for This** - Gradio is built for ML demos, not content management

### Flask's Advantages

1. **True Multi-Page Navigation** - Each page gets its own URL (`/`, `/deck/MyDeck`, `/card/edit`)
2. **Clickable Everything** - Links, buttons, cards can all navigate to new pages
3. **Full HTML/CSS Control** - Keep your purple gradient aesthetic exactly as-is
4. **Form Handling** - Built-in support for card editor forms
5. **Python Integration** - Trigger any Python function from any route
6. **Mature Ecosystem** - Thousands of tutorials, extensions, and examples

---

## What Will Change

### UI Framework
- **Before**: Gradio Blocks with Tabs, HTML, and Dropdowns
- **After**: Flask routes with Jinja2 HTML templates

### Navigation
- **Before**: Tab switching via `gr.update(selected="Details")`
- **After**: Regular HTML links (`<a href="/deck/MyDeck">`)

### File Structure
```
# Before (Gradio)
src/ui/app.py          # Everything in one file

# After (Flask)
src/ui/
  ├── app.py           # Flask app and routes
  ├── templates/       # HTML templates
  │   ├── base.html    # Base layout with navigation
  │   ├── index.html   # Home page (deck grid)
  │   ├── deck.html    # Deck details page
  │   ├── card.html    # Card editor page
  │   └── settings.html
  └── static/          # CSS, JavaScript, images
      ├── css/
      │   └── style.css  # Your purple gradients
      └── js/
          └── main.js    # Optional interactivity
```

### Launch Command
- **Before**: `python3 -m src.ui.app`
- **After**: `flask --app src.ui.app run` or `python3 -m src.ui.app`

---

## What Will Stay the Same

### Business Logic (No Changes Needed!)
All your existing Python code stays exactly the same:

- ✅ `SettingsManager` - No changes
- ✅ `DeckManager` - No changes
- ✅ `get_available_decks()` - No changes
- ✅ `get_card_artwork_path()` - No changes
- ✅ `create_diagonal_split_image()` - No changes
- ✅ All card rendering code - No changes

### Data Format
- ✅ Deck JSON files - No changes
- ✅ `config/config.json` - No changes
- ✅ `config/common_tokens.json` - No changes
- ✅ Artwork folder structure - No changes

### Visual Design
Your purple gradient deck cards, styles, and layouts can be preserved exactly:
- Same CSS (gradient backgrounds, hover effects, card grid)
- Same deck card design
- Same fonts, colors, spacing

---

## Architecture Overview

### Flask Routing Structure

```
Route                         → Page                  → Purpose
─────────────────────────────────────────────────────────────────
GET  /                        → index.html            → Deck grid homepage
GET  /deck/<deck_name>        → deck.html             → Deck details + card list
GET  /deck/<deck_name>/card/<card_name>/edit
                              → card_edit.html        → Card JSON editor
POST /deck/<deck_name>/card/<card_name>/render
                              → (redirect back)       → Render card image
GET  /settings                → settings.html         → Settings page
POST /settings/save           → (redirect back)       → Save settings
GET  /settings/tokens/add     → (redirect back)       → Add token
POST /settings/tokens/delete  → (redirect back)       → Delete token
```

### Request Flow Example

**User clicks deck card "Eldrazi Tribal":**

1. Browser sends: `GET /deck/Eldrazi%20Tribal`
2. Flask route handler:
   - Calls `get_available_decks()`
   - Finds deck JSON
   - Loads deck data
   - Renders `deck.html` template with data
3. Browser receives HTML page showing:
   - Deck info (format, card count, commander)
   - Grid of cards in the deck
   - Each card is clickable → `/deck/Eldrazi Tribal/card/Ulamog/edit`

---

## Migration Plan

### Phase 1: Setup (30 minutes)
1. Install Flask: `pip install flask`
2. Update `requirements.txt`
3. Create folder structure: `templates/`, `static/css/`, `static/js/`
4. Create base template with navigation

### Phase 2: Home Page (1-2 hours)
1. Convert deck grid HTML to Jinja2 template
2. Create route: `@app.route('/')`
3. Migrate `create_deck_cards_html()` logic
4. Add filter buttons (All/Complete/Incomplete)
5. Make deck cards clickable with `<a href="/deck/{{ deck_name }}">`

### Phase 3: Deck Details Page (1-2 hours)
1. Create `deck.html` template
2. Create route: `@app.route('/deck/<deck_name>')`
3. Display deck metadata (format, commander, description)
4. Show card list as clickable grid
5. Add "Back to My Decks" button

### Phase 4: Card Editor Page (2-3 hours)
1. Create `card_edit.html` template with form
2. Create route: `@app.route('/deck/<deck_name>/card/<card_name>/edit')`
3. Load card JSON into form fields (dropdowns/inputs)
4. Add "Render" button that POSTs to `/render`
5. Implement POST route to trigger card rendering Python code

### Phase 5: Settings Page (1 hour)
1. Convert Settings tab to `settings.html`
2. Create routes for GET/POST settings
3. Migrate token management (add/delete)
4. Keep same validation logic

### Phase 6: Polish (1-2 hours)
1. Add CSS styling (purple gradients, hover effects)
2. Add loading indicators
3. Error handling and validation messages
4. Test all navigation flows

### Total Estimated Time: 6-11 hours

---

## Implementation Details

### 1. Flask App Structure

**File: `src/ui/app.py`**

```python
from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from src.services.settings_manager import SettingsManager
from src.services.deck_manager import DeckManager
from src.utils.paths import PROJECT_ROOT

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # For flash messages

# Import your existing helper functions
from src.ui.helpers import (
    get_available_decks,
    get_card_artwork_path,
    create_diagonal_split_image
)

@app.route('/')
def index():
    """Home page with deck grid."""
    filter_status = request.args.get('filter', 'all')
    decks = get_decks_with_metadata(filter_status)
    return render_template('index.html', decks=decks, filter_status=filter_status)

@app.route('/deck/<deck_name>')
def deck_details(deck_name):
    """Deck details page."""
    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        flash(f'Deck "{deck_name}" not found', 'error')
        return redirect(url_for('index'))

    return render_template('deck.html', deck=deck_data)

@app.route('/deck/<deck_name>/card/<card_name>/edit')
def card_editor(deck_name, card_name):
    """Card editor page."""
    deck_data = load_deck_by_name(deck_name)
    card_data = deck_data['cards'].get(card_name)

    if not card_data:
        flash(f'Card "{card_name}" not found', 'error')
        return redirect(url_for('deck_details', deck_name=deck_name))

    return render_template('card_edit.html',
                         deck_name=deck_name,
                         card_name=card_name,
                         card=card_data)

@app.route('/deck/<deck_name>/card/<card_name>/render', methods=['POST'])
def render_card(deck_name, card_name):
    """Render card image."""
    # Get form data
    card_data = {
        'name': request.form.get('name'),
        'cardtype': request.form.get('cardtype'),
        'subtype': request.form.get('subtype'),
        'cost': request.form.get('cost'),
        'rules': request.form.get('rules'),
        # ... other fields
    }

    # Call your existing card rendering code
    from src.services.card_renderer import render_card_image
    try:
        render_card_image(deck_name, card_name, card_data)
        flash(f'Card "{card_name}" rendered successfully!', 'success')
    except Exception as e:
        flash(f'Error rendering card: {str(e)}', 'error')

    return redirect(url_for('card_editor', deck_name=deck_name, card_name=card_name))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Settings page."""
    if request.method == 'POST':
        # Save settings
        settings_mgr = SettingsManager()
        settings_mgr.set_deck_path(request.form.get('deck_path'))
        settings_mgr.set_cockatrice_path(request.form.get('cockatrice_path'))

        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings'))

    # GET request - show form
    settings_mgr = SettingsManager()
    return render_template('settings.html',
                         deck_path=settings_mgr.get_deck_path(),
                         cockatrice_path=settings_mgr.get_cockatrice_path())

if __name__ == '__main__':
    app.run(debug=True, port=7860)
```

### 2. Helper Functions (Extract from Current Code)

**File: `src/ui/helpers.py`**

Move existing functions here:
- `get_available_decks()`
- `get_card_artwork_path()`
- `create_diagonal_split_image()`
- `get_card_artwork_base64()`

Add new helper:

```python
def get_decks_with_metadata(filter_status='all'):
    """
    Get decks with full metadata for display.

    Args:
        filter_status: "all", "complete", or "incomplete"

    Returns:
        List of dicts with deck info
    """
    decks = get_available_decks()
    result = []

    for folder_name, deck_folder_path, json_path in decks:
        with open(json_path, 'r') as f:
            deck_data = json.load(f)

        metadata = deck_data.get('metadata', {})
        deck_complete = metadata.get('complete', 0)

        # Apply filter
        if filter_status == "complete" and not deck_complete:
            continue
        elif filter_status == "incomplete" and deck_complete:
            continue

        # Get artwork path for background
        artwork_path = get_deck_artwork(deck_folder_path, deck_data)

        result.append({
            'name': metadata.get('deck_name', folder_name),
            'folder_name': folder_name,
            'card_count': len(deck_data.get('cards', {})),
            'format': metadata.get('format', ''),
            'description': metadata.get('description', ''),
            'commander': metadata.get('commander', ''),
            'complete': deck_complete,
            'artwork_path': artwork_path,
            'json_path': json_path
        })

    return result

def load_deck_by_name(deck_name):
    """Load deck data by display name."""
    decks = get_available_decks()

    for folder_name, deck_folder_path, json_path in decks:
        with open(json_path, 'r') as f:
            deck_data = json.load(f)

        metadata = deck_data.get('metadata', {})
        display_name = metadata.get('deck_name', folder_name)

        if display_name == deck_name:
            return {
                'name': display_name,
                'folder_name': folder_name,
                'folder_path': deck_folder_path,
                'json_path': json_path,
                'metadata': metadata,
                'cards': deck_data.get('cards', {})
            }

    return None
```

### 3. Base Template (Navigation & Layout)

**File: `src/ui/templates/base.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Manufactor{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <header>
        <div class="container">
            <h1><a href="/">Manufactor</a></h1>
            <nav>
                <a href="/" {% if request.path == '/' %}class="active"{% endif %}>My Decks</a>
                <a href="/settings" {% if request.path == '/settings' %}class="active"{% endif %}>Settings</a>
                <a href="/about" {% if request.path == '/about' %}class="active"{% endif %}>About</a>
            </nav>
        </div>
    </header>

    <main class="container">
        <!-- Flash messages -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        <!-- Page content -->
        {% block content %}{% endblock %}
    </main>

    <footer>
        <div class="container">
            <p>Manufactor - Magic: The Gathering Custom Card Creator</p>
        </div>
    </footer>

    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>
```

### 4. Home Page Template (Deck Grid)

**File: `src/ui/templates/index.html`**

```html
{% extends "base.html" %}

{% block title %}My Decks - Manufactor{% endblock %}

{% block content %}
<div class="page-header">
    <h2>My Decks</h2>
    <p>Click on a deck to view details and manage cards</p>
</div>

<!-- Filter buttons -->
<div class="filter-controls">
    <a href="/?filter=all" class="btn btn-sm {% if filter_status == 'all' %}btn-primary{% endif %}">
        📚 All Decks
    </a>
    <a href="/?filter=complete" class="btn btn-sm {% if filter_status == 'complete' %}btn-primary{% endif %}">
        ✅ Complete
    </a>
    <a href="/?filter=incomplete" class="btn btn-sm {% if filter_status == 'incomplete' %}btn-primary{% endif %}">
        ⏳ Incomplete
    </a>
</div>

<!-- Deck grid (same design as current Gradio) -->
<div class="deck-grid">
    {% for deck in decks %}
    <a href="/deck/{{ deck.name | urlencode }}" class="deck-card"
       style="--bg-image: url('{{ deck.artwork_path }}');">
        <h3>{{ deck.name }}</h3>
        <div class="deck-card-info">
            📦 {{ deck.card_count }} cards
            {% if deck.format %}
                • 🎮 {{ deck.format }}
            {% endif %}
            • {{ '✅ Complete' if deck.complete else '⏳ Incomplete' }}
        </div>
        {% if deck.description %}
        <div class="deck-card-info">{{ deck.description[:100] }}...</div>
        {% endif %}
        <div class="deck-card-path">{{ deck.json_path }}</div>
    </a>
    {% endfor %}
</div>

{% if not decks %}
<div class="empty-state">
    <h3>No Decks Found</h3>
    <p>No valid deck folders found in your deck path.</p>
    <p>A valid deck folder must contain a JSON file with the same name as the folder.</p>
    <p>For example: <code>/Decks/MyDeck/MyDeck.json</code></p>
    <a href="/settings" class="btn btn-primary">Configure Deck Path</a>
</div>
{% endif %}
{% endblock %}
```

### 5. Deck Details Template

**File: `src/ui/templates/deck.html`**

```html
{% extends "base.html" %}

{% block title %}{{ deck.name }} - Manufactor{% endblock %}

{% block content %}
<div class="breadcrumb">
    <a href="/">← Back to My Decks</a>
</div>

<div class="deck-details">
    <h1>{{ deck.name }}</h1>

    <div class="deck-info-card">
        <h3>Deck Information</h3>
        <p><strong>Format:</strong> {{ deck.metadata.format or 'Unknown' }}</p>
        <p><strong>Total Cards:</strong> {{ deck.cards|length }}</p>

        {% if deck.metadata.commander %}
            {% if deck.metadata.commander is string %}
                <p><strong>Commander:</strong> {{ deck.metadata.commander }}</p>
            {% else %}
                <p><strong>Commanders:</strong> {{ deck.metadata.commander|join(', ') }}</p>
            {% endif %}
        {% endif %}

        <p><strong>Status:</strong>
            {{ '✅ Complete' if deck.metadata.complete else '⏳ Incomplete' }}
        </p>
    </div>

    <div class="deck-description">
        <h3>Description</h3>
        <p>{{ deck.metadata.description or 'No description available.' }}</p>
    </div>

    <div class="card-list">
        <h3>Cards ({{ deck.cards|length }})</h3>
        <div class="card-grid">
            {% for card_name, card_data in deck.cards.items() %}
            <a href="/deck/{{ deck.name | urlencode }}/card/{{ card_name | urlencode }}/edit"
               class="card-item">
                <div class="card-name">{{ card_name }}</div>
                <div class="card-type">{{ card_data.cardtype }}</div>
            </a>
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}
```

### 6. Card Editor Template

**File: `src/ui/templates/card_edit.html`**

```html
{% extends "base.html" %}

{% block title %}Edit {{ card_name }} - Manufactor{% endblock %}

{% block content %}
<div class="breadcrumb">
    <a href="/">My Decks</a> /
    <a href="/deck/{{ deck_name | urlencode }}">{{ deck_name }}</a> /
    {{ card_name }}
</div>

<div class="card-editor">
    <h1>Edit Card: {{ card_name }}</h1>

    <form method="POST" action="/deck/{{ deck_name | urlencode }}/card/{{ card_name | urlencode }}/render">
        <div class="form-row">
            <div class="form-group">
                <label for="name">Card Name</label>
                <input type="text" id="name" name="name" value="{{ card.name }}" required>
            </div>

            <div class="form-group">
                <label for="cost">Mana Cost</label>
                <input type="text" id="cost" name="cost" value="{{ card.cost or '' }}">
            </div>
        </div>

        <div class="form-row">
            <div class="form-group">
                <label for="cardtype">Card Type</label>
                <select id="cardtype" name="cardtype">
                    <option value="Creature" {% if card.cardtype == 'Creature' %}selected{% endif %}>Creature</option>
                    <option value="Instant" {% if card.cardtype == 'Instant' %}selected{% endif %}>Instant</option>
                    <option value="Sorcery" {% if card.cardtype == 'Sorcery' %}selected{% endif %}>Sorcery</option>
                    <option value="Enchantment" {% if card.cardtype == 'Enchantment' %}selected{% endif %}>Enchantment</option>
                    <option value="Artifact" {% if card.cardtype == 'Artifact' %}selected{% endif %}>Artifact</option>
                    <option value="Land" {% if card.cardtype == 'Land' %}selected{% endif %}>Land</option>
                    <option value="Planeswalker" {% if card.cardtype == 'Planeswalker' %}selected{% endif %}>Planeswalker</option>
                </select>
            </div>

            <div class="form-group">
                <label for="subtype">Subtype</label>
                <input type="text" id="subtype" name="subtype" value="{{ card.subtype or '' }}">
            </div>
        </div>

        <div class="form-group">
            <label for="rules">Rules Text</label>
            <textarea id="rules" name="rules" rows="5">{{ card.rules or '' }}</textarea>
        </div>

        <div class="form-row">
            <div class="form-group">
                <label for="power">Power</label>
                <input type="text" id="power" name="power" value="{{ card.power or '' }}">
            </div>

            <div class="form-group">
                <label for="toughness">Toughness</label>
                <input type="text" id="toughness" name="toughness" value="{{ card.toughness or '' }}">
            </div>
        </div>

        <div class="form-actions">
            <button type="submit" class="btn btn-primary">🎨 Render Card</button>
            <a href="/deck/{{ deck_name | urlencode }}" class="btn btn-secondary">Cancel</a>
        </div>
    </form>

    <!-- Preview area (if card image exists) -->
    <div class="card-preview">
        <h3>Card Preview</h3>
        <img src="/static/rendered/{{ deck_name }}/{{ card_name }}.png"
             alt="{{ card_name }}"
             onerror="this.style.display='none'">
    </div>
</div>
{% endblock %}
```

### 7. CSS Styling (Purple Gradients Preserved)

**File: `src/ui/static/css/style.css`**

```css
/* Same purple gradient deck cards from Gradio */
.deck-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
    padding: 20px;
}

.deck-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
    cursor: pointer;
    color: white;
    position: relative;
    overflow: hidden;
    text-decoration: none;
    display: block;
}

.deck-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: var(--bg-image, none);
    background-size: cover;
    background-position: center;
    opacity: 0.6;
    filter: brightness(0.5);
    z-index: 0;
}

.deck-card > * {
    position: relative;
    z-index: 1;
}

.deck-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
}

.deck-card h3 {
    margin: 0 0 12px 0;
    font-size: 28px;
    font-weight: 600;
}

.deck-card-info {
    font-size: 14px;
    opacity: 0.9;
    margin: 6px 0;
}

.deck-card-path {
    font-size: 10px;
    opacity: 0.6;
    margin-top: 12px;
    font-family: monospace;
    word-break: break-all;
}

/* Deck info card (details page) */
.deck-info-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 12px;
    margin: 20px 0;
}

.deck-info-card h3 {
    margin-top: 0;
}

/* Form styling */
.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: 600;
}

.form-group input,
.form-group select,
.form-group textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
    transition: background 0.2s;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-primary:hover {
    filter: brightness(1.1);
}

/* Flash messages */
.alert {
    padding: 15px;
    margin-bottom: 20px;
    border-radius: 6px;
}

.alert-success {
    background: #d4edda;
    color: #155724;
}

.alert-error {
    background: #f8d7da;
    color: #721c24;
}
```

---

## Code Examples

### Example: Rendering a Card

When user clicks "Render Card" button in card editor:

```python
@app.route('/deck/<deck_name>/card/<card_name>/render', methods=['POST'])
def render_card(deck_name, card_name):
    """Render card image from form data."""
    # Get form data
    card_data = {
        'name': request.form.get('name'),
        'cardtype': request.form.get('cardtype'),
        'subtype': request.form.get('subtype'),
        'cost': request.form.get('cost'),
        'rules': request.form.get('rules'),
        'power': request.form.get('power'),
        'toughness': request.form.get('toughness'),
        # ... other fields
    }

    # Update deck JSON
    deck = load_deck_by_name(deck_name)
    deck_json_path = deck['json_path']

    with open(deck_json_path, 'r') as f:
        deck_data = json.load(f)

    deck_data['cards'][card_name] = card_data

    with open(deck_json_path, 'w') as f:
        json.dump(deck_data, f, indent=2)

    # Call your existing rendering code
    from src.services.card_renderer import CardRenderer
    renderer = CardRenderer()

    try:
        output_path = renderer.render_card(
            deck_name=deck_name,
            card_name=card_name,
            card_data=card_data
        )
        flash(f'✅ Card "{card_name}" rendered successfully! Saved to {output_path}', 'success')
    except Exception as e:
        flash(f'❌ Error rendering card: {str(e)}', 'error')

    # Redirect back to editor
    return redirect(url_for('card_editor', deck_name=deck_name, card_name=card_name))
```

---

## Testing Strategy

### 1. Manual Testing Checklist

- [ ] Home page loads and displays all decks
- [ ] Filter buttons (All/Complete/Incomplete) work
- [ ] Clicking a deck card navigates to deck details page
- [ ] Deck details page shows correct metadata
- [ ] Card list displays all cards
- [ ] Clicking a card navigates to editor
- [ ] Card editor loads existing card data
- [ ] Form fields are pre-filled correctly
- [ ] "Render Card" button triggers Python rendering code
- [ ] Flash messages appear after actions
- [ ] Settings page saves configuration
- [ ] Token management (add/delete) works

### 2. Automated Tests (Optional)

```python
# tests/test_routes.py
import pytest
from src.ui.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Test home page loads."""
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'My Decks' in rv.data

def test_deck_details(client):
    """Test deck details page."""
    rv = client.get('/deck/Test%20Deck')
    assert rv.status_code == 200 or rv.status_code == 302  # May redirect if not found

def test_card_editor(client):
    """Test card editor page."""
    rv = client.get('/deck/Test%20Deck/card/Test%20Card/edit')
    assert rv.status_code in [200, 302]
```

---

## Deployment

### Development Server

```bash
# Option 1: Using flask command
export FLASK_APP=src.ui.app
export FLASK_ENV=development
flask run --port 7860

# Option 2: Using Python
python3 -m src.ui.app
```

### Production Server (Optional)

For production deployment, use Gunicorn or Waitress:

```bash
# Install
pip install gunicorn

# Run
gunicorn -w 4 -b 0.0.0.0:7860 src.ui.app:app
```

---

## Migration Checklist

### Pre-Migration
- [ ] Read this guide thoroughly
- [ ] Backup current `src/ui/app.py`
- [ ] Ensure all Gradio features are documented

### Setup
- [ ] Install Flask: `pip install flask`
- [ ] Create folder structure: `templates/`, `static/css/`, `static/js/`
- [ ] Move helper functions to `src/ui/helpers.py`

### Templates
- [ ] Create `base.html` with navigation
- [ ] Create `index.html` for deck grid
- [ ] Create `deck.html` for deck details
- [ ] Create `card_edit.html` for card editor
- [ ] Create `settings.html` for settings page

### Routes
- [ ] Implement `@app.route('/')` - home page
- [ ] Implement `@app.route('/deck/<deck_name>')` - deck details
- [ ] Implement `@app.route('/deck/<deck_name>/card/<card_name>/edit')` - editor
- [ ] Implement `@app.route('/deck/<deck_name>/card/<card_name>/render')` - render
- [ ] Implement `@app.route('/settings')` - settings

### Styling
- [ ] Copy purple gradient CSS from Gradio
- [ ] Style deck grid
- [ ] Style forms
- [ ] Add flash message styling
- [ ] Test responsive design

### Testing
- [ ] Test all navigation flows
- [ ] Test filter buttons
- [ ] Test card rendering
- [ ] Test settings save
- [ ] Test error handling

### Deployment
- [ ] Update documentation
- [ ] Update README with new launch command
- [ ] Update `requirements.txt`

---

## Troubleshooting

### Issue: Templates not found
**Solution**: Ensure `templates/` folder is at `src/ui/templates/`

### Issue: Static files 404
**Solution**: Ensure `static/` folder is at `src/ui/static/`

### Issue: URL encoding errors with deck names
**Solution**: Use `| urlencode` filter in templates and `urllib.parse.unquote()` in routes

### Issue: Flash messages not appearing
**Solution**: Ensure `app.secret_key` is set and `{% with messages = get_flashed_messages() %}` is in base template

---

## Next Steps After Migration

Once Flask is working:

1. **Add More Features**:
   - Batch render all cards in deck
   - Export to Cockatrice from web UI
   - Card search/filter
   - Deck statistics

2. **Improve Card Editor**:
   - Live preview of card while editing
   - Autocomplete for card types
   - Validation before rendering

3. **Enhance UX**:
   - Loading spinners during render
   - Progress bar for batch operations
   - Keyboard shortcuts

4. **Deploy to Production**:
   - Set up proper web server (Nginx + Gunicorn)
   - Add user authentication (if needed)
   - Enable HTTPS

---

## Conclusion

Migrating from Gradio to Flask will give you:
- ✅ True multi-page navigation
- ✅ Clickable deck cards that work
- ✅ Full control over HTML/CSS/JS
- ✅ Easy integration with card rendering code
- ✅ Professional web application structure

All your existing Python business logic stays the same - you're just replacing the UI framework with one designed for multi-page web applications.

**Estimated migration time**: 6-11 hours for a complete, polished migration.

**Recommended approach**: Start with Phase 1 (setup) and Phase 2 (home page), test thoroughly, then proceed to subsequent phases.

Good luck with the migration! 🚀
