"""
Main UI application for Magic Card Manufactor.

This module provides the Flask-based web interface for the card creation tool.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
import json
import os
from urllib.parse import unquote, quote
from src.services.settings_manager import SettingsManager
from src.utils.paths import SYMBOL_PATH
from src.ui.helpers import (
    get_available_decks,
    get_decks_with_metadata,
    load_deck_by_name,
    load_common_tokens,
    save_common_tokens,
    load_staging,
    save_staging,
    get_staging_path,
    get_card_image_base64,
)

app = Flask(__name__)
app.secret_key = 'manufactor-secret-key-change-in-production'


@app.route('/symbols/<filename>')
def serve_symbol(filename):
    """Serve mana symbol images from Assets/Symbols/."""
    return send_from_directory(SYMBOL_PATH, filename)


@app.route('/')
def index():
    """Home page with deck grid."""
    filter_status = request.args.get('filter', 'all')

    settings = SettingsManager()
    deck_path = settings.get_deck_path()

    # Check if deck path is configured
    if not deck_path or not deck_path.strip():
        flash('Deck path is not configured. Please configure it in Settings.', 'warning')
        return render_template('index.html', decks=[], filter_status=filter_status)

    if not os.path.isdir(deck_path):
        flash(f'Deck path does not exist: {deck_path}', 'error')
        return render_template('index.html', decks=[], filter_status=filter_status)

    decks = get_decks_with_metadata(filter_status)
    return render_template('index.html', decks=decks, filter_status=filter_status)


@app.route('/deck/<deck_name>')
def deck_details(deck_name):
    """Deck details page."""
    deck_name = unquote(deck_name)

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        flash(f'Deck "{deck_name}" not found', 'error')
        return redirect(url_for('index'))

    staging = load_staging(deck_data['folder_path'])
    staged_count = len(staging)

    return render_template('deck.html', deck=deck_data, staged_count=staged_count)


@app.route('/deck/<deck_name>/toggle-complete', methods=['POST'])
def toggle_complete(deck_name):
    """Toggle deck completion status."""
    # Decode URL-encoded deck name
    deck_name = unquote(deck_name)

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        flash(f'Deck "{deck_name}" not found', 'error')
        return redirect(url_for('index'))

    # Load the deck JSON
    json_path = deck_data['json_path']
    with open(json_path, 'r') as f:
        full_deck_data = json.load(f)

    # Toggle the complete status
    current_status = full_deck_data.get('metadata', {}).get('complete', 0)
    new_status = 0 if current_status else 1

    if 'metadata' not in full_deck_data:
        full_deck_data['metadata'] = {}

    full_deck_data['metadata']['complete'] = new_status

    # Save back to JSON
    with open(json_path, 'w') as f:
        json.dump(full_deck_data, f, indent=2)

    status_text = "complete" if new_status else "incomplete"
    flash(f'Deck "{deck_name}" marked as {status_text}!', 'success')
    return redirect(url_for('deck_details', deck_name=deck_name))


@app.route('/deck/<deck_name>/add-basic/<color>', methods=['POST'])
def add_basic(deck_name, color):
    """Add one basic land of the given color to the deck."""
    deck_name = unquote(deck_name)

    BASIC_MAP = {
        'w': {'name': 'Plains',   'cardtype': 'Basic Land', 'subtype': 'Plains'},
        'u': {'name': 'Island',   'cardtype': 'Basic Land', 'subtype': 'Island'},
        'b': {'name': 'Swamp',    'cardtype': 'Basic Land', 'subtype': 'Swamp'},
        'r': {'name': 'Mountain', 'cardtype': 'Basic Land', 'subtype': 'Mountain'},
        'g': {'name': 'Forest',   'cardtype': 'Basic Land', 'subtype': 'Forest'},
        'c': {'name': 'Wastes',   'cardtype': 'Basic Land', 'subtype': 'Wastes'},
    }

    if color not in BASIC_MAP:
        return jsonify({'error': 'Invalid color'}), 400

    basic_info = BASIC_MAP[color]

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    json_path = deck_data['json_path']
    with open(json_path, 'r') as f:
        full_deck_data = json.load(f)

    cards = full_deck_data.setdefault('cards', {})

    # Find existing basic land of this subtype.
    # Real basics use front.basic=1 and front.subtype; custom basics may use top-level cardtype.
    target_subtype = basic_info['subtype'].lower()
    found_name = None
    for card_name, card_data in cards.items():
        if not isinstance(card_data, dict):
            continue
        front = card_data.get('front', {})
        # Real basic: front.basic flag set and front.subtype matches
        if front.get('basic') and target_subtype in front.get('subtype', '').lower():
            found_name = card_name
            break
        # Custom basic: top-level cardtype contains "basic land" and subtype matches
        ct = card_data.get('cardtype', '').lower()
        st = card_data.get('subtype', '').lower()
        if 'basic' in ct and 'land' in ct and target_subtype in st:
            found_name = card_name
            break

    if found_name:
        cards[found_name]['quantity'] = cards[found_name].get('quantity', 1) + 1
        new_qty = cards[found_name]['quantity']
    else:
        # Create a new basic land in the real-card format
        cards[basic_info['name']] = {
            'front': {
                'name': basic_info['name'],
                'cardtype': 'Land',
                'subtype': basic_info['subtype'],
                'basic': 1,
            },
            'quantity': 1,
            'real': 1,
        }
        new_qty = 1

    with open(json_path, 'w') as f:
        json.dump(full_deck_data, f, indent=2)

    total_cards = sum(
        c.get('quantity', 1) if isinstance(c, dict) else 1
        for c in cards.values()
    )
    return jsonify({'quantity': new_qty, 'total_cards': total_cards})


@app.route('/deck/<deck_name>/remove-basic/<color>', methods=['POST'])
def remove_basic(deck_name, color):
    """Remove one basic land of the given color from the deck."""
    deck_name = unquote(deck_name)

    SUBTYPE_MAP = {
        'w': 'plains', 'u': 'island', 'b': 'swamp',
        'r': 'mountain', 'g': 'forest', 'c': 'wastes',
    }

    if color not in SUBTYPE_MAP:
        return jsonify({'error': 'Invalid color'}), 400

    target_subtype = SUBTYPE_MAP[color]

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    json_path = deck_data['json_path']
    with open(json_path, 'r') as f:
        full_deck_data = json.load(f)

    cards = full_deck_data.setdefault('cards', {})

    found_name = None
    for card_name, card_data in cards.items():
        if not isinstance(card_data, dict):
            continue
        front = card_data.get('front', {})
        if front.get('basic') and target_subtype in front.get('subtype', '').lower():
            found_name = card_name
            break
        ct = card_data.get('cardtype', '').lower()
        st = card_data.get('subtype', '').lower()
        if 'basic' in ct and 'land' in ct and target_subtype in st:
            found_name = card_name
            break

    if not found_name:
        total_cards = sum(
            c.get('quantity', 1) if isinstance(c, dict) else 1 for c in cards.values()
        )
        return jsonify({'quantity': 0, 'total_cards': total_cards})

    current_qty = cards[found_name].get('quantity', 1)
    if current_qty <= 1:
        del cards[found_name]
        new_qty = 0
    else:
        cards[found_name]['quantity'] = current_qty - 1
        new_qty = current_qty - 1

    with open(json_path, 'w') as f:
        json.dump(full_deck_data, f, indent=2)

    total_cards = sum(
        c.get('quantity', 1) if isinstance(c, dict) else 1 for c in cards.values()
    )
    return jsonify({'quantity': new_qty, 'total_cards': total_cards})


@app.route('/deck/<deck_name>/card/<card_name>/edit')
def card_editor(deck_name, card_name):
    """Redirect to inline deck editor (old standalone page is superseded)."""
    deck_name = unquote(deck_name)
    card_name = unquote(card_name)
    return redirect(
        url_for('deck_details', deck_name=deck_name) + '#edit/' + quote(card_name, safe='')
    )


@app.route('/deck/<deck_name>/card-data')
def card_data(deck_name):
    """Return card JSON for the inline editor."""
    deck_name = unquote(deck_name)
    card_name = request.args.get('name', '')
    if not card_name:
        return jsonify({'error': 'Card name required'}), 400

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    card = deck_data['cards'].get(card_name)
    if card is None:
        # Commander cards are excluded from deck_data['cards'] — check raw JSON
        with open(deck_data['json_path'], 'r') as f:
            raw_deck = json.load(f)
        raw_card = raw_deck.get('cards', {}).get(card_name)
        if raw_card is None:
            return jsonify({'error': 'Card not found'}), 404
        card_json = dict(raw_card) if isinstance(raw_card, dict) else {}
        card_json['image_base64'] = get_card_image_base64(deck_data['folder_path'], card_name)
    else:
        # card already includes image_base64 from load_deck_by_name
        card_json = dict(card)

    # Check whether artwork exists for this card
    artwork_folder = os.path.join(deck_data['folder_path'], 'Artwork')
    artwork_found = False
    artwork_hint = None
    names_to_check = [card_name]
    if ' / ' in card_name:
        names_to_check.append(card_name.split(' / ')[0])
    for name in names_to_check:
        for ext in ['.jpg', '.jpeg', '.png']:
            candidate = os.path.join(artwork_folder, f"{name}{ext}")
            if os.path.isfile(candidate):
                artwork_found = True
                artwork_hint = f"Artwork/{name}{ext}"
                break
        if artwork_found:
            break

    card_json['_artwork_found'] = artwork_found
    card_json['_artwork_hint'] = artwork_hint

    return jsonify(card_json)


@app.route('/deck/<deck_name>/card/<card_name>/save', methods=['POST'])
def save_card(deck_name, card_name):
    """Save card changes."""
    # Decode URL-encoded names
    deck_name = unquote(deck_name)
    card_name = unquote(card_name)

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        flash(f'Deck "{deck_name}" not found', 'error')
        return redirect(url_for('index'))

    # Get form data
    updated_card = {
        'name': request.form.get('name', '').strip(),
        'cardtype': request.form.get('cardtype', '').strip(),
        'subtype': request.form.get('subtype', '').strip(),
        'cost': request.form.get('cost', '').strip(),
        'rules': request.form.get('rules', '').strip(),
        'power': request.form.get('power', '').strip(),
        'toughness': request.form.get('toughness', '').strip(),
        'rarity': request.form.get('rarity', '').strip(),
        'flavor': request.form.get('flavor', '').strip(),
    }

    # Remove empty fields
    updated_card = {k: v for k, v in updated_card.items() if v}

    # Load the deck JSON
    json_path = deck_data['json_path']
    with open(json_path, 'r') as f:
        full_deck_data = json.load(f)

    # Update the card
    full_deck_data['cards'][card_name] = updated_card

    # Save back to JSON
    with open(json_path, 'w') as f:
        json.dump(full_deck_data, f, indent=2)

    flash(f'Card "{card_name}" saved successfully!', 'success')
    return redirect(url_for('card_editor', deck_name=deck_name, card_name=card_name))


@app.route('/settings')
def settings():
    """Settings page."""
    settings_mgr = SettingsManager()
    tokens = load_common_tokens()

    return render_template('settings.html',
                         deck_path=settings_mgr.get_deck_path(),
                         cockatrice_path=settings_mgr.get_cockatrice_path(),
                         tokens=tokens)


@app.route('/settings/save', methods=['POST'])
def save_settings():
    """Save path settings."""
    settings_mgr = SettingsManager()

    deck_path = request.form.get('deck_path', '').strip()
    cockatrice_path = request.form.get('cockatrice_path', '').strip()

    try:
        # Set the paths
        settings_mgr.set_deck_path(deck_path)
        settings_mgr.set_cockatrice_path(cockatrice_path)

        # Validate
        errors = settings_mgr.get_validation_errors()

        if errors:
            for error in errors:
                flash(error, 'warning')
            flash('Settings saved with warnings', 'warning')
        else:
            flash('Settings saved successfully!', 'success')

    except Exception as e:
        flash(f'Error saving settings: {str(e)}', 'error')

    return redirect(url_for('settings'))


@app.route('/settings/tokens/add', methods=['POST'])
def add_token():
    """Add a new token."""
    name = request.form.get('token_name', '').strip()
    cardtype = request.form.get('token_cardtype', '').strip()
    subtype = request.form.get('token_subtype', '').strip()
    rules = request.form.get('token_rules', '').strip()
    colors = request.form.get('token_colors', '').strip()
    frame = request.form.get('token_frame', '').strip()

    if not name:
        flash('Token name is required', 'error')
        return redirect(url_for('settings'))

    tokens = load_common_tokens()

    if name in tokens:
        flash(f'Token "{name}" already exists. Delete it first to replace it.', 'error')
        return redirect(url_for('settings'))

    # Parse colors from comma-separated string
    colors_list = []
    if colors:
        colors_list = [c.strip() for c in colors.split(',') if c.strip()]

    # Build token dict
    token_data = {
        "name": name,
        "cardtype": cardtype or "Artifact",
        "subtype": subtype or name,
        "rules": rules or "",
        "token": 1,
        "colors": colors_list,
        "rarity": "common"
    }

    # Only add frame field if it's specified
    if frame:
        token_data["frame"] = frame

    tokens[name] = token_data
    save_common_tokens(tokens)

    flash(f'Token "{name}" added successfully!', 'success')
    return redirect(url_for('settings'))


@app.route('/settings/tokens/delete', methods=['POST'])
def delete_token():
    """Delete a token."""
    name = request.form.get('delete_token_name', '').strip()

    if not name:
        flash('Please enter a token name to delete', 'error')
        return redirect(url_for('settings'))

    tokens = load_common_tokens()

    if name not in tokens:
        flash(f'Token "{name}" not found', 'error')
        return redirect(url_for('settings'))

    del tokens[name]
    save_common_tokens(tokens)

    flash(f'Token "{name}" deleted successfully!', 'success')
    return redirect(url_for('settings'))


@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')


def launch_ui(debug=True, port=7860):
    """
    Launch the Flask UI.

    Args:
        debug (bool): Whether to run in debug mode
        port (int): Port to run the server on
    """
    app.run(debug=debug, port=port, host='0.0.0.0')


if __name__ == "__main__":
    # Launch the UI when run directly
    launch_ui()
