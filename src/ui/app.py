"""
Main UI application for Magic Card Manufactor.

This module provides the Flask-based web interface for the card creation tool.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from urllib.parse import unquote
from src.services.settings_manager import SettingsManager
from src.ui.helpers import (
    get_available_decks,
    get_decks_with_metadata,
    load_deck_by_name,
    load_common_tokens,
    save_common_tokens
)

app = Flask(__name__)
app.secret_key = 'manufactor-secret-key-change-in-production'


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
    # Decode URL-encoded deck name
    deck_name = unquote(deck_name)

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        flash(f'Deck "{deck_name}" not found', 'error')
        return redirect(url_for('index'))

    return render_template('deck.html', deck=deck_data)


@app.route('/deck/<deck_name>/card/<card_name>/edit')
def card_editor(deck_name, card_name):
    """Card editor page."""
    # Decode URL-encoded names
    deck_name = unquote(deck_name)
    card_name = unquote(card_name)

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        flash(f'Deck "{deck_name}" not found', 'error')
        return redirect(url_for('index'))

    card_data = deck_data['cards'].get(card_name)
    if not card_data:
        flash(f'Card "{card_name}" not found in deck "{deck_name}"', 'error')
        return redirect(url_for('deck_details', deck_name=deck_name))

    return render_template('card_edit.html',
                         deck_name=deck_name,
                         card_name=card_name,
                         card=card_data)


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
