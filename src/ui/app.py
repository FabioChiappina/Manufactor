"""
Main UI application for Magic Card Manufactor.

This module provides the Flask-based web interface for the card creation tool.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
import base64
import json
import os
import shutil
import urllib.request as _url_req
from urllib.parse import unquote, quote, urlencode
from src.services.settings_manager import SettingsManager
from src.services.image_generator import ImageGenerator
from src.utils.paths import SYMBOL_PATH, CARD_FRAMES_PATH
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
    get_card_artwork_path,
    card_from_editor_dict,
    compute_setname,
)

app = Flask(__name__)
app.secret_key = 'manufactor-secret-key-change-in-production'


def _touch_last_modified(raw_deck):
    """Update last_modified timestamp in deck metadata dict (in-place)."""
    from datetime import datetime
    raw_deck.setdefault('metadata', {})['last_modified'] = datetime.utcnow().isoformat() + 'Z'


@app.route('/symbols/<filename>')
def serve_symbol(filename):
    """Serve mana symbol images from Assets/Symbols/."""
    return send_from_directory(SYMBOL_PATH, filename)


@app.route('/')
def index():
    """Home page with deck grid."""
    filter_status = request.args.get('filter', 'all')
    sort_order = request.args.get('sort', 'recent')
    if sort_order not in ('recent', 'alpha'):
        sort_order = 'recent'

    settings = SettingsManager()
    deck_path = settings.get_deck_path()

    # Check if deck path is configured
    if not deck_path or not deck_path.strip():
        flash('Deck path is not configured. Please configure it in Settings.', 'warning')
        return render_template('index.html', decks=[], filter_status=filter_status, sort_order=sort_order)

    if not os.path.isdir(deck_path):
        flash(f'Deck path does not exist: {deck_path}', 'error')
        return render_template('index.html', decks=[], filter_status=filter_status, sort_order=sort_order)

    decks = get_decks_with_metadata(filter_status, sort_order)
    return render_template('index.html', decks=decks, filter_status=filter_status, sort_order=sort_order)


@app.route('/deck/new', methods=['GET', 'POST'])
def new_deck():
    """Create a new deck."""
    import re
    from datetime import datetime

    if request.method == 'GET':
        return render_template('create_deck.html')

    deck_name = request.form.get('deck_name', '').strip()
    setname_raw = request.form.get('setname', '').strip().upper()
    description = request.form.get('description', '').strip()
    format_ = request.form.get('format', 'Commander').strip()

    if not deck_name:
        flash('Deck name is required.', 'error')
        return render_template('create_deck.html',
                               deck_name=deck_name, setname=setname_raw,
                               description=description, format=format_)

    setname_val = setname_raw if setname_raw else compute_setname(deck_name)

    # Build folder name: keep letters, digits, spaces, hyphens → replace spaces with underscores
    folder_name = re.sub(r'[^\w\s-]', '', deck_name).strip().replace(' ', '_') or 'NewDeck'

    settings = SettingsManager()
    deck_path = settings.get_deck_path()
    if not deck_path or not os.path.isdir(deck_path):
        flash('Deck path is not configured or does not exist.', 'error')
        return redirect(url_for('settings'))

    # Resolve folder name collision
    base_folder = folder_name
    counter = 2
    folder_path = os.path.join(deck_path, folder_name)
    while os.path.exists(folder_path):
        folder_name = f"{base_folder}_{counter}"
        folder_path = os.path.join(deck_path, folder_name)
        counter += 1

    os.makedirs(folder_path)
    for subdir in ('Cards', 'Tokens', 'Artwork', 'Printing', 'Staging'):
        os.makedirs(os.path.join(folder_path, subdir), exist_ok=True)

    now = datetime.utcnow().isoformat() + 'Z'
    deck_json = {
        'metadata': {
            'folder_name': folder_name,
            'deck_name': deck_name,
            'description': description,
            'format': format_,
            'setname': setname_val,
            'created': now,
            'last_modified': now,
            'complete': 0,
            'tags': [],
        },
        'cards': {},
        'tokens': {},
    }

    json_path = os.path.join(folder_path, f"{folder_name}.json")
    with open(json_path, 'w') as f:
        json.dump(deck_json, f, indent=2)

    save_staging(folder_path, {})

    flash(f'Deck "{deck_name}" created!', 'success')
    return redirect(url_for('deck_details', deck_name=deck_name) + '#cards')


@app.route('/api/compute-setname')
def api_compute_setname():
    """Auto-compute a set code from a deck name."""
    name = request.args.get('name', '').strip()
    exclude = request.args.get('exclude', None)
    if not name:
        return jsonify({'setname': ''})
    return jsonify({'setname': compute_setname(name, exclude_setname=exclude)})


@app.route('/deck/<deck_name>/update-metadata', methods=['POST'])
def update_deck_metadata(deck_name):
    """Update top-level deck metadata (name, description, format, setname)."""
    from datetime import datetime
    deck_name = unquote(deck_name)

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    data = request.get_json() or {}

    json_path = deck_data['json_path']
    with open(json_path, 'r') as f:
        raw_deck = json.load(f)

    metadata = raw_deck.setdefault('metadata', {})

    if 'deck_name' in data and data['deck_name'].strip():
        metadata['deck_name'] = data['deck_name'].strip()
    if 'description' in data:
        metadata['description'] = data['description'].strip()
    if 'format' in data and data['format'].strip():
        metadata['format'] = data['format'].strip()
    if 'setname' in data and data['setname'].strip():
        metadata['setname'] = data['setname'].strip().upper()

    metadata['last_modified'] = datetime.utcnow().isoformat() + 'Z'

    with open(json_path, 'w') as f:
        json.dump(raw_deck, f, indent=2)

    return jsonify({'success': True, 'metadata': metadata})


@app.route('/deck/<deck_name>/toggle-commander', methods=['POST'])
def toggle_commander(deck_name):
    """Add or remove a card from the deck's commander list."""
    from datetime import datetime
    deck_name = unquote(deck_name)

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    data = request.get_json() or {}
    card_name = data.get('card_name', '').strip()
    if not card_name:
        return jsonify({'error': 'card_name required'}), 400

    json_path = deck_data['json_path']
    with open(json_path, 'r') as f:
        raw_deck = json.load(f)

    metadata = raw_deck.setdefault('metadata', {})
    commander = metadata.get('commander', [])

    # Normalize to list
    if isinstance(commander, str):
        commander = [commander] if commander else []
    elif not isinstance(commander, list):
        commander = []

    if card_name in commander:
        commander.remove(card_name)
        is_commander = False
    else:
        commander.append(card_name)
        is_commander = True

    if not commander:
        metadata.pop('commander', None)
    else:
        metadata['commander'] = commander

    metadata['last_modified'] = datetime.utcnow().isoformat() + 'Z'

    with open(json_path, 'w') as f:
        json.dump(raw_deck, f, indent=2)

    return jsonify({'success': True, 'is_commander': is_commander, 'commanders': commander})


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
    staged_cards = set(staging.keys())

    return render_template('deck.html', deck=deck_data, staged_count=staged_count, staged_cards=staged_cards)


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
    _touch_last_modified(full_deck_data)

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

    _touch_last_modified(full_deck_data)
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

    _touch_last_modified(full_deck_data)
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

    folder_path = deck_data['folder_path']

    # Prefer staged data — if this card has been forged, show the pending version
    staging = load_staging(folder_path)
    staged_entry = staging.get(card_name)
    staging_dir = get_staging_path(folder_path)

    def _img_base64(path):
        if os.path.isfile(path):
            with open(path, 'rb') as _f:
                return 'data:image/jpeg;base64,' + base64.b64encode(_f.read()).decode('utf-8')
        return None

    if staged_entry:
        card_json = dict(staged_entry['updated'])
        # Prefer staged image; fall back to Cards/
        # Use front_name from entry (DFC deck keys differ from the image filename)
        staged_front = staged_entry.get('front_name') or card_name
        staged_img = os.path.join(staging_dir, f"{staged_front}.jpg")
        card_json['image_base64'] = _img_base64(staged_img) or get_card_image_base64(folder_path, card_name)
    else:
        card = deck_data['cards'].get(card_name)
        if card is None:
            # Commander cards are excluded from deck_data['cards'] — check raw JSON
            with open(deck_data['json_path'], 'r') as f:
                raw_deck = json.load(f)
            raw_card = raw_deck.get('cards', {}).get(card_name)
            if raw_card is None:
                return jsonify({'error': 'Card not found'}), 404
            card_json = dict(raw_card) if isinstance(raw_card, dict) else {}
            card_json['image_base64'] = get_card_image_base64(folder_path, card_name)
        else:
            # card already includes image_base64 from load_deck_by_name
            card_json = dict(card)

    # Check whether artwork exists for this card
    artwork_path = get_card_artwork_path(folder_path, card_name)
    artwork_found = artwork_path is not None
    artwork_hint = f"Artwork/{os.path.basename(artwork_path)}" if artwork_path else None

    card_json['_artwork_found'] = artwork_found
    card_json['_artwork_hint'] = artwork_hint

    # Include back face image — prefer staged version
    back_name = card_json.get('back', {}).get('name') if isinstance(card_json.get('back'), dict) else None
    if back_name:
        staged_back = os.path.join(staging_dir, f"{back_name}.jpg")
        card_json['back_image_base64'] = _img_base64(staged_back) or get_card_image_base64(folder_path, back_name)

    # Include deck-level tag list for the tag picker
    card_json['_deck_tags'] = sorted(deck_data['metadata'].get('tags', []))

    return jsonify(card_json)


@app.route('/deck/<deck_name>/add-card-tag', methods=['POST'])
def add_card_tag(deck_name):
    """Add a tag to a card and ensure it exists in deck metadata."""
    deck_name = unquote(deck_name)
    card_name = request.args.get('name', '')
    data = request.get_json() or {}
    tag = (data.get('tag') or '').strip()
    if not card_name or not tag:
        return jsonify({'error': 'Card name and tag required'}), 400

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    folder_path = deck_data['folder_path']

    with open(deck_data['json_path'], 'r') as f:
        raw_deck = json.load(f)

    card = raw_deck.get('cards', {}).get(card_name)
    if not isinstance(card, dict):
        return jsonify({'error': 'Card not found'}), 404

    card_tags = list(card.get('tags') or [])
    if tag not in card_tags:
        card_tags.append(tag)
    raw_deck['cards'][card_name]['tags'] = card_tags

    meta_tags = list(raw_deck.get('metadata', {}).get('tags') or [])
    if tag not in meta_tags:
        meta_tags.append(tag)
        meta_tags.sort()
    raw_deck.setdefault('metadata', {})['tags'] = meta_tags
    _touch_last_modified(raw_deck)

    with open(deck_data['json_path'], 'w') as f:
        json.dump(raw_deck, f, indent=2)

    # Keep staging entry in sync so staged cards also see the updated tags
    staging = load_staging(folder_path)
    if card_name in staging and isinstance(staging[card_name].get('updated'), dict):
        staging[card_name]['updated']['tags'] = card_tags
        save_staging(folder_path, staging)

    return jsonify({'card_tags': card_tags, 'deck_tags': meta_tags})


@app.route('/deck/<deck_name>/remove-card-tag', methods=['POST'])
def remove_card_tag(deck_name):
    """Remove a tag from a card; remove from deck metadata if no longer used."""
    deck_name = unquote(deck_name)
    card_name = request.args.get('name', '')
    data = request.get_json() or {}
    tag = (data.get('tag') or '').strip()
    if not card_name or not tag:
        return jsonify({'error': 'Card name and tag required'}), 400

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    folder_path = deck_data['folder_path']

    with open(deck_data['json_path'], 'r') as f:
        raw_deck = json.load(f)

    card = raw_deck.get('cards', {}).get(card_name)
    if not isinstance(card, dict):
        return jsonify({'error': 'Card not found'}), 404

    card_tags = [t for t in (card.get('tags') or []) if t != tag]
    raw_deck['cards'][card_name]['tags'] = card_tags

    # Remove from deck metadata if no other card uses this tag
    tag_still_used = any(
        tag in (c.get('tags') or [])
        for n, c in raw_deck.get('cards', {}).items()
        if isinstance(c, dict) and n != card_name
    )
    meta_tags = list(raw_deck.get('metadata', {}).get('tags') or [])
    if not tag_still_used and tag in meta_tags:
        meta_tags.remove(tag)
    raw_deck.setdefault('metadata', {})['tags'] = meta_tags
    _touch_last_modified(raw_deck)

    with open(deck_data['json_path'], 'w') as f:
        json.dump(raw_deck, f, indent=2)

    # Keep staging entry in sync so staged cards also see the updated tags
    staging = load_staging(folder_path)
    if card_name in staging and isinstance(staging[card_name].get('updated'), dict):
        staging[card_name]['updated']['tags'] = card_tags
        save_staging(folder_path, staging)

    return jsonify({'card_tags': card_tags, 'deck_tags': meta_tags})


@app.route('/deck/<deck_name>/bulk-add-tag', methods=['POST'])
def bulk_add_tag(deck_name):
    """Add a tag to multiple cards at once."""
    deck_name = unquote(deck_name)
    data = request.get_json() or {}
    tag = (data.get('tag') or '').strip()
    card_names = data.get('card_names') or []
    if not tag or not card_names:
        return jsonify({'error': 'Tag and card names required'}), 400

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    folder_path = deck_data['folder_path']

    with open(deck_data['json_path'], 'r') as f:
        raw_deck = json.load(f)

    meta_tags = list(raw_deck.get('metadata', {}).get('tags') or [])
    if tag not in meta_tags:
        meta_tags.append(tag)
        meta_tags.sort()
    raw_deck.setdefault('metadata', {})['tags'] = meta_tags

    updated_cards = {}
    for card_name in card_names:
        card = raw_deck.get('cards', {}).get(card_name)
        if not isinstance(card, dict):
            continue
        card_tags = list(card.get('tags') or [])
        if tag not in card_tags:
            card_tags.append(tag)
        raw_deck['cards'][card_name]['tags'] = card_tags
        updated_cards[card_name] = card_tags

    _touch_last_modified(raw_deck)
    with open(deck_data['json_path'], 'w') as f:
        json.dump(raw_deck, f, indent=2)

    staging = load_staging(folder_path)
    changed_staging = False
    for card_name, card_tags in updated_cards.items():
        if card_name in staging and isinstance(staging[card_name].get('updated'), dict):
            staging[card_name]['updated']['tags'] = card_tags
            changed_staging = True
    if changed_staging:
        save_staging(folder_path, staging)

    return jsonify({'deck_tags': meta_tags, 'updated_cards': updated_cards})


@app.route('/deck/<deck_name>/tags-data', methods=['GET'])
def get_tags_data(deck_name):
    """Return all deck tags with per-tag card counts."""
    deck_name = unquote(deck_name)
    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    with open(deck_data['json_path'], 'r') as f:
        raw_deck = json.load(f)

    meta_tags = sorted(raw_deck.get('metadata', {}).get('tags') or [])
    cards = raw_deck.get('cards', {})

    tag_card_counts = {tag: 0 for tag in meta_tags}
    for card in cards.values():
        if not isinstance(card, dict):
            continue
        for tag in (card.get('tags') or []):
            if tag in tag_card_counts:
                tag_card_counts[tag] += 1

    tags = [{'name': t, 'card_count': tag_card_counts[t]} for t in meta_tags]
    return jsonify({'tags': tags})


@app.route('/deck/<deck_name>/rename-tag', methods=['POST'])
def rename_tag(deck_name):
    """Rename a tag across all cards and deck metadata."""
    deck_name = unquote(deck_name)
    data = request.get_json() or {}
    old_tag = (data.get('old_tag') or '').strip()
    new_tag = (data.get('new_tag') or '').strip()

    if not old_tag or not new_tag:
        return jsonify({'error': 'old_tag and new_tag required'}), 400
    if old_tag == new_tag:
        return jsonify({'error': 'Tags are identical'}), 400

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    folder_path = deck_data['folder_path']
    with open(deck_data['json_path'], 'r') as f:
        raw_deck = json.load(f)

    affected = 0
    for card_name, card in raw_deck.get('cards', {}).items():
        if not isinstance(card, dict):
            continue
        card_tags = list(card.get('tags') or [])
        if old_tag in card_tags:
            idx = card_tags.index(old_tag)
            card_tags[idx] = new_tag
            raw_deck['cards'][card_name]['tags'] = card_tags
            affected += 1

    meta_tags = list(raw_deck.get('metadata', {}).get('tags') or [])
    if old_tag in meta_tags:
        meta_tags.remove(old_tag)
    if new_tag not in meta_tags:
        meta_tags.append(new_tag)
    meta_tags.sort()
    raw_deck.setdefault('metadata', {})['tags'] = meta_tags
    _touch_last_modified(raw_deck)

    with open(deck_data['json_path'], 'w') as f:
        json.dump(raw_deck, f, indent=2)

    staging = load_staging(folder_path)
    changed_staging = False
    for entry in staging.values():
        if isinstance(entry.get('updated'), dict):
            card_tags = list(entry['updated'].get('tags') or [])
            if old_tag in card_tags:
                idx = card_tags.index(old_tag)
                card_tags[idx] = new_tag
                entry['updated']['tags'] = card_tags
                changed_staging = True
    if changed_staging:
        save_staging(folder_path, staging)

    return jsonify({'deck_tags': meta_tags, 'affected_cards': affected})


@app.route('/deck/<deck_name>/delete-tag', methods=['POST'])
def delete_tag(deck_name):
    """Remove a tag from all cards and deck metadata."""
    deck_name = unquote(deck_name)
    data = request.get_json() or {}
    tag = (data.get('tag') or '').strip()

    if not tag:
        return jsonify({'error': 'tag required'}), 400

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    folder_path = deck_data['folder_path']
    with open(deck_data['json_path'], 'r') as f:
        raw_deck = json.load(f)

    affected = 0
    for card_name, card in raw_deck.get('cards', {}).items():
        if not isinstance(card, dict):
            continue
        card_tags = list(card.get('tags') or [])
        if tag in card_tags:
            raw_deck['cards'][card_name]['tags'] = [t for t in card_tags if t != tag]
            affected += 1

    meta_tags = list(raw_deck.get('metadata', {}).get('tags') or [])
    if tag in meta_tags:
        meta_tags.remove(tag)
    raw_deck.setdefault('metadata', {})['tags'] = meta_tags
    _touch_last_modified(raw_deck)

    with open(deck_data['json_path'], 'w') as f:
        json.dump(raw_deck, f, indent=2)

    staging = load_staging(folder_path)
    changed_staging = False
    for entry in staging.values():
        if isinstance(entry.get('updated'), dict):
            card_tags = list(entry['updated'].get('tags') or [])
            if tag in card_tags:
                entry['updated']['tags'] = [t for t in card_tags if t != tag]
                changed_staging = True
    if changed_staging:
        save_staging(folder_path, staging)

    return jsonify({'deck_tags': meta_tags, 'affected_cards': affected})


@app.route('/deck/<deck_name>/add-cards-by-text', methods=['POST'])
def add_cards_by_text(deck_name):
    """Add all cards whose rules/flavor text contains a keyword to a given tag."""
    deck_name = unquote(deck_name)
    data = request.get_json() or {}
    tag = (data.get('tag') or '').strip()
    text = (data.get('text') or '').strip()

    if not tag or not text:
        return jsonify({'error': 'tag and text required'}), 400

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    folder_path = deck_data['folder_path']
    with open(deck_data['json_path'], 'r') as f:
        raw_deck = json.load(f)

    text_lower = text.lower()

    def _face_texts(face):
        if not isinstance(face, dict):
            return []
        result = []
        for key in ('rules', 'rules1', 'rules2', 'rules3', 'rules4', 'flavor'):
            v = face.get(key)
            if isinstance(v, str):
                result.append(v)
        return result

    added_cards = []
    already_had_tag = []

    for card_name, card in raw_deck.get('cards', {}).items():
        if not isinstance(card, dict):
            continue
        texts = _face_texts(card.get('front') or card)
        texts += _face_texts(card.get('back'))
        sub = card.get('subspell')
        if isinstance(sub, dict):
            texts += _face_texts(sub)
        if text_lower not in ' '.join(texts).lower():
            continue

        card_tags = list(card.get('tags') or [])
        if tag in card_tags:
            already_had_tag.append(card_name)
            continue

        card_tags.append(tag)
        raw_deck['cards'][card_name]['tags'] = card_tags
        added_cards.append(card_name)

    meta_tags = list(raw_deck.get('metadata', {}).get('tags') or [])
    if added_cards and tag not in meta_tags:
        meta_tags.append(tag)
        meta_tags.sort()
    raw_deck.setdefault('metadata', {})['tags'] = meta_tags

    if added_cards:
        _touch_last_modified(raw_deck)
        with open(deck_data['json_path'], 'w') as f:
            json.dump(raw_deck, f, indent=2)

        staging = load_staging(folder_path)
        changed_staging = False
        for card_name in added_cards:
            if card_name in staging and isinstance(staging[card_name].get('updated'), dict):
                stag_tags = list(staging[card_name]['updated'].get('tags') or [])
                if tag not in stag_tags:
                    stag_tags.append(tag)
                    staging[card_name]['updated']['tags'] = stag_tags
                    changed_staging = True
        if changed_staging:
            save_staging(folder_path, staging)

    return jsonify({
        'deck_tags': meta_tags,
        'tag': tag,
        'added_cards': added_cards,
        'already_had_tag': already_had_tag,
    })


@app.route('/card-frames')
def card_frames():
    """Return sorted list of card frame filenames from Assets/CardFrames/."""
    try:
        files = sorted(f for f in os.listdir(CARD_FRAMES_PATH) if f.endswith('.jpg'))
    except OSError:
        files = []
    return jsonify(files)


@app.route('/deck/<deck_name>/forge-card', methods=['POST'])
def forge_card(deck_name):
    """Generate a staged card image from the editor JSON and update the staging sidecar."""
    deck_name = unquote(deck_name)
    card_name = request.args.get('name', '_new')
    is_new = (card_name == '_new')

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No card data provided'}), 400

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    try:
        return _do_forge(deck_data, card_name, is_new, data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Forge failed unexpectedly: {e}'}), 500


def _do_forge(deck_data, card_name, is_new, data):
    """Inner forge logic — always returns a Flask response."""
    folder_path = deck_data['folder_path']
    setname = deck_data['metadata'].get('setname', 'UNK')

    # Ensure Staging/ and Artwork/ directories exist
    staging_dir = get_staging_path(folder_path)
    os.makedirs(staging_dir, exist_ok=True)
    os.makedirs(os.path.join(folder_path, 'Artwork'), exist_ok=True)

    # Build Card object(s) from the editor dict
    try:
        cards = card_from_editor_dict(data, setname=setname)
    except Exception as e:
        return jsonify({'error': f'Invalid card data: {e}'}), 400

    if not cards:
        return jsonify({'error': 'No card produced from data'}), 400

    # Validate front name
    front_name = cards[0].name
    if not front_name:
        return jsonify({'error': 'Card must have a name'}), 400

    # Full deck-JSON key: "FrontName / SubspellName" for subspell cards only.
    # DFC cards always use just the front name as the deck key (per deck.py convention).
    front_card = cards[0]
    full_deck_key = (f"{front_name} / {front_card.subspell.name}"
                     if front_card.is_subspell() else front_name)

    # Extract the quantity from the editor data (always saved immediately to deck JSON).
    new_quantity = max(1, int(data.get('quantity') or 1))

    # Load deck JSON now (needed for quantity-only check and later for staging sidecar).
    with open(deck_data['json_path'], 'r') as f:
        raw_deck = json.load(f)

    original = raw_deck.get('cards', {}).get(card_name if not is_new else full_deck_key)

    # Generate images into Staging/
    gen = ImageGenerator()
    images = {}  # card_name -> base64 string
    for card in cards:
        # Read the generated image back as base64.
        # The renderer names the output after the artwork file, which may differ
        # in apostrophe variant (e.g. U+2019 vs U+0027).  Normalize both sides,
        # then rename the file to the canonical card.name so all downstream
        # lookups (staging sidecar, assembly line, publish) use a consistent path.
        def _anorm(s):
            return s.replace('\u2019', "'").replace('\u2018', "'").replace('\u02bc', "'").lower()
        img_path = os.path.join(staging_dir, f"{card.name}.jpg")
        # Remove any stale canonical image before re-generating.  Without this,
        # a second forge on a card whose artwork filename uses a different apostrophe
        # variant than card.name would leave the old img_path in place and the
        # rename-normalisation block below would be skipped, returning the stale
        # forge-1 image instead of the freshly rendered forge-2 image.
        if os.path.isfile(img_path):
            os.remove(img_path)
        success = gen.generate_single_card_image(card, save_path=staging_dir, include_printing=False)
        if not success:
            return jsonify({'error': f'Image generation failed for "{card.name}"'}), 500
        if not os.path.isfile(img_path):
            canon = _anorm(card.name)
            for fname in sorted(os.listdir(staging_dir)):
                if not fname.endswith('.jpg'):
                    continue
                if _anorm(fname[:-4]) == canon:
                    actual = os.path.join(staging_dir, fname)
                    os.rename(actual, img_path)
                    break
        if os.path.isfile(img_path):
            with open(img_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
                images[card.name] = f"data:image/jpeg;base64,{b64}"

    # For brand-new cards: add a placeholder entry to the deck JSON
    if is_new or original is None:
        placeholder = dict(data)
        placeholder['complete'] = 0
        placeholder['quantity'] = new_quantity
        raw_deck.setdefault('cards', {})[full_deck_key] = placeholder
        _touch_last_modified(raw_deck)
        with open(deck_data['json_path'], 'w') as f:
            json.dump(raw_deck, f, indent=2)
        original = {}
        is_new = True
    elif full_deck_key != card_name:
        # Subspell was added/changed — rename the deck JSON entry
        existing = raw_deck.get('cards', {}).pop(card_name, {})
        existing.update(data)
        existing['complete'] = 0
        existing['quantity'] = new_quantity
        raw_deck.setdefault('cards', {})[full_deck_key] = existing
        _touch_last_modified(raw_deck)
        with open(deck_data['json_path'], 'w') as f:
            json.dump(raw_deck, f, indent=2)
    else:
        # Existing card being re-forged — save quantity directly to deck JSON now.
        raw_deck['cards'][card_name]['quantity'] = new_quantity
        _touch_last_modified(raw_deck)
        with open(deck_data['json_path'], 'w') as f:
            json.dump(raw_deck, f, indent=2)

    # Update _staging.json sidecar — always key by the full deck key
    staging_key = full_deck_key
    staging = load_staging(folder_path)
    # Remove any old staging entry under the previous name to avoid duplicates
    if card_name != full_deck_key and card_name in staging:
        del staging[card_name]

    # serializeForm() on the client never includes 'tags' (managed out-of-band).
    # Preserve them from the deck JSON so the staged version doesn't lose them.
    existing_tags = raw_deck.get('cards', {}).get(full_deck_key, {}).get('tags')
    if existing_tags and not data.get('tags'):
        data['tags'] = existing_tags

    staging_entry = {
        'original': original,
        'updated': data,
        'staged_image_path': f"Staging/{front_name}.jpg",
        'front_name': front_name,
        'disable_auto_tokens': data.get('disable_auto_tokens', False),
        'is_new': is_new,
    }
    # Record the old deck-JSON key if the card was renamed (subspell added/changed/removed)
    if not is_new and full_deck_key != card_name:
        staging_entry['original_key'] = card_name
    staging[staging_key] = staging_entry
    save_staging(folder_path, staging)

    result = {
        'image_base64': images.get(front_name),
        'staged_count': len(staging),
    }
    if len(cards) > 1:
        result['back_image_base64'] = images.get(cards[1].name)
    # If the card was renamed (subspell added/changed), tell the client
    if full_deck_key != card_name:
        result['new_card_name'] = full_deck_key

    return jsonify(result)


@app.route('/deck/<deck_name>/assembly-line-data')
def assembly_line_data(deck_name):
    """Return JSON list of staged cards with original + staged images."""
    deck_name = unquote(deck_name)
    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    folder_path = deck_data['folder_path']
    staging = load_staging(folder_path)
    staging_dir = get_staging_path(folder_path)

    def _b64(path):
        if path and os.path.isfile(path):
            with open(path, 'rb') as f:
                return 'data:image/jpeg;base64,' + base64.b64encode(f.read()).decode()
        return None

    _NON_TEXT_KEYS = {'complete', 'quantity', 'real', 'tags', 'token'}

    def _strip_meta(d):
        if not isinstance(d, dict):
            return d
        return {k: _strip_meta(v) for k, v in d.items() if k not in _NON_TEXT_KEYS}

    items = []
    for card_name, entry in staging.items():
        front_name = entry.get('front_name') or card_name
        staged_img_rel = entry.get('staged_image_path', '')
        staged_img_filename = os.path.basename(staged_img_rel) if staged_img_rel else f"{front_name}.jpg"
        staged_b64 = _b64(os.path.join(staging_dir, staged_img_filename))
        original_b64 = get_card_image_base64(folder_path, card_name)

        # Back face images for double-faced cards
        orig_card = entry.get('original') or {}
        updated_card = entry.get('updated') or {}
        orig_back_name = (orig_card.get('back') or {}).get('name') if orig_card.get('double_faced_type') else None
        staged_back_name = (updated_card.get('back') or {}).get('name') if updated_card.get('double_faced_type') else None

        orig_back_b64 = None
        if orig_back_name:
            orig_back_b64 = get_card_image_base64(folder_path, orig_back_name)

        staged_back_b64 = None
        if staged_back_name:
            staged_back_path = os.path.join(staging_dir, f"{staged_back_name}.jpg")
            staged_back_b64 = _b64(staged_back_path) or get_card_image_base64(folder_path, staged_back_name)

        # Determine what changed
        is_new = entry.get('is_new', False)
        pending_delete = entry.get('pending_delete', False)
        if is_new or pending_delete:
            change_type = None
        elif _strip_meta(orig_card) != _strip_meta(updated_card):
            change_type = 'text_changed'
        else:
            change_type = 'artwork_only'

        items.append({
            'card_name': card_name,
            'is_new': is_new,
            'is_real': entry.get('is_real', False),
            'pending_delete': pending_delete,
            'original_image_base64': original_b64,
            'staged_image_base64': staged_b64,
            'original_back_image_base64': orig_back_b64,
            'staged_back_image_base64': staged_back_b64,
            'change_type': change_type,
        })

    return jsonify(items)


@app.route('/deck/<deck_name>/discard-card', methods=['POST'])
def discard_card(deck_name):
    """Remove a card from the staging area."""
    deck_name = unquote(deck_name)
    card_name = request.args.get('name', '')

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    folder_path = deck_data['folder_path']
    staging = load_staging(folder_path)
    entry = staging.pop(card_name, None)
    is_new_card = entry.get('is_new', False) if entry else False

    # If card was brand-new (placeholder only), remove it from the deck JSON too.
    # If card was renamed (subspell added/changed), revert the rename.
    original_key = entry.get('original_key') if entry else None
    if entry and (entry.get('is_new') or original_key):
        with open(deck_data['json_path'], 'r') as f:
            raw_deck = json.load(f)
        cards_dict = raw_deck.get('cards', {})
        if entry.get('is_new'):
            cards_dict.pop(card_name, None)
        if original_key:
            # Remove the renamed entry and restore the original
            cards_dict.pop(card_name, None)
            orig_data = entry.get('original')
            if orig_data is not None:
                cards_dict[original_key] = orig_data
        _touch_last_modified(raw_deck)
        with open(deck_data['json_path'], 'w') as f:
            json.dump(raw_deck, f, indent=2)

    # Remove staged image file(s) — front and back face for DFCs
    staging_dir = get_staging_path(folder_path)
    front_name = (entry.get('front_name') or card_name) if entry else card_name
    staged_img = os.path.join(staging_dir, f"{front_name}.jpg")
    if os.path.isfile(staged_img):
        os.remove(staged_img)
    if entry:
        back_face_name = ((entry.get('updated') or {}).get('back') or {}).get('name')
        if back_face_name:
            staged_back = os.path.join(staging_dir, f"{back_face_name}.jpg")
            if os.path.isfile(staged_back):
                os.remove(staged_back)

    save_staging(folder_path, staging)
    return jsonify({'staged_count': len(staging), 'is_new': is_new_card})


@app.route('/deck/<deck_name>/stage-delete', methods=['POST'])
def stage_delete(deck_name):
    """Stage a card for deletion; the removal is applied when the assembly line is published."""
    deck_name = unquote(deck_name)
    card_name = request.args.get('name', '').strip()
    if not card_name:
        return jsonify({'error': 'name required'}), 400

    try:
        deck_data = load_deck_by_name(deck_name)
        if not deck_data:
            return jsonify({'error': 'Deck not found'}), 404

        folder_path = deck_data['folder_path']
        staging = load_staging(folder_path)

        with open(deck_data['json_path'], 'r') as f:
            raw_deck = json.load(f)
        original = raw_deck.get('cards', {}).get(card_name, {})

        # Discard any existing staged image for this card first
        staging_dir = get_staging_path(folder_path)
        old_entry = staging.get(card_name, {})
        old_front = old_entry.get('front_name') or card_name
        old_updated = old_entry.get('updated') or {}
        old_back_name = (old_updated.get('back') or {}).get('name', '')

        for fname in [f"{old_front}.jpg"] + ([f"{old_back_name}.jpg"] if old_back_name else []):
            p = os.path.join(staging_dir, fname)
            if os.path.isfile(p):
                os.remove(p)

        # Preserve is_new from the old entry so the assembly line shows the correct
        # placeholder ("New Card" vs "No Image") for cards that were never published.
        was_new = old_entry.get('is_new', False)

        staging[card_name] = {
            'original': original,
            'updated': None,
            'front_name': card_name,
            'pending_delete': True,
            'is_new': was_new,
        }
        save_staging(folder_path, staging)
        return jsonify({'success': True, 'staged_count': len(staging)})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to stage deletion: {e}'}), 500


@app.route('/deck/<deck_name>/forge-all-list')
def forge_all_list(deck_name):
    """Return the list of non-real card names to forge and the total deck card count."""
    deck_name = unquote(deck_name)
    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    with open(deck_data['json_path'], 'r') as f:
        raw_deck = json.load(f)

    cards_to_forge = [
        card_name
        for card_name, card_dict in raw_deck.get('cards', {}).items()
        if isinstance(card_dict, dict) and not card_dict.get('real')
    ]

    return jsonify({
        'cards': cards_to_forge,
        'total_deck_cards': deck_data['total_cards'],
    })


@app.route('/deck/<deck_name>/forge-one', methods=['POST'])
def forge_one(deck_name):
    """Forge a single named card from the deck JSON into the staging area."""
    deck_name = unquote(deck_name)
    card_name = request.args.get('card', '').strip()
    if not card_name:
        return jsonify({'error': 'card name required'}), 400

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    folder_path = deck_data['folder_path']
    setname = deck_data['metadata'].get('setname', 'UNK')

    with open(deck_data['json_path'], 'r') as f:
        raw_deck = json.load(f)

    card_dict = raw_deck.get('cards', {}).get(card_name)
    if card_dict is None:
        return jsonify({'error': 'Card not found'}), 404
    if not isinstance(card_dict, dict):
        return jsonify({'error': 'Invalid card data'}), 400
    if card_dict.get('real'):
        staging = load_staging(folder_path)
        return jsonify({'skipped': True, 'missing_artwork': False, 'staged_count': len(staging)})

    # Check if artwork exists for this card
    artwork_path = get_card_artwork_path(folder_path, card_name)
    missing_artwork = artwork_path is None

    staging_dir = get_staging_path(folder_path)
    os.makedirs(staging_dir, exist_ok=True)

    def _anorm(s):
        return s.replace('\u2019', "'").replace('\u2018', "'").replace('\u02bc', "'").lower()

    gen = ImageGenerator()
    try:
        cards = card_from_editor_dict(card_dict, setname=setname)
    except Exception as e:
        return jsonify({'error': str(e), 'missing_artwork': missing_artwork}), 400

    for card in cards:
        if not gen.generate_single_card_image(card, save_path=staging_dir, include_printing=False):
            return jsonify({'error': 'Image generation failed', 'missing_artwork': missing_artwork}), 500
        # Normalize apostrophe variants in the filename so downstream lookups
        # (assembly-line-data, publish) can find the staged image reliably.
        img_path = os.path.join(staging_dir, f"{card.name}.jpg")
        if not os.path.isfile(img_path):
            canon = _anorm(card.name)
            for fname in sorted(os.listdir(staging_dir)):
                if not fname.endswith('.jpg'):
                    continue
                if _anorm(fname[:-4]) == canon:
                    os.rename(os.path.join(staging_dir, fname), img_path)
                    break

    front_name = cards[0].name
    staging = load_staging(folder_path)
    staging[card_name] = {
        'original': card_dict,
        'updated': card_dict,
        'staged_image_path': f"Staging/{front_name}.jpg",
        'front_name': front_name,
        'disable_auto_tokens': card_dict.get('disable_auto_tokens', False),
        'is_new': False,
    }
    save_staging(folder_path, staging)

    return jsonify({
        'success': True,
        'missing_artwork': missing_artwork,
        'staged_count': len(staging),
    })


@app.route('/deck/<deck_name>/forge-all', methods=['POST'])
def forge_all(deck_name):
    """Forge every non-real card in the deck into the staging area."""
    deck_name = unquote(deck_name)
    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    folder_path = deck_data['folder_path']
    setname = deck_data['metadata'].get('setname', 'UNK')
    staging_dir = get_staging_path(folder_path)
    os.makedirs(staging_dir, exist_ok=True)

    with open(deck_data['json_path'], 'r') as f:
        raw_deck = json.load(f)

    def _anorm_fa(s):
        return s.replace('\u2019', "'").replace('\u2018', "'").replace('\u02bc', "'").lower()

    staging = load_staging(folder_path)
    gen = ImageGenerator()
    forged = 0
    errors = []

    for card_name, card_dict in raw_deck.get('cards', {}).items():
        if not isinstance(card_dict, dict):
            continue
        if card_dict.get('real'):
            continue  # Skip real (non-custom) cards

        try:
            cards = card_from_editor_dict(card_dict, setname=setname)
        except Exception as e:
            errors.append(f"{card_name}: {e}")
            continue

        success = True
        for card in cards:
            if not gen.generate_single_card_image(card, save_path=staging_dir, include_printing=False):
                errors.append(f"{card_name}: image generation failed")
                success = False
                break
            # Normalize apostrophe variants so staging lookups find the file.
            img_path = os.path.join(staging_dir, f"{card.name}.jpg")
            if not os.path.isfile(img_path):
                canon = _anorm_fa(card.name)
                for fname in sorted(os.listdir(staging_dir)):
                    if not fname.endswith('.jpg'):
                        continue
                    if _anorm_fa(fname[:-4]) == canon:
                        os.rename(os.path.join(staging_dir, fname), img_path)
                        break

        if success:
            front_name = cards[0].name
            staging[card_name] = {
                'original': raw_deck['cards'].get(card_name, {}),
                'updated': card_dict,
                'staged_image_path': f"Staging/{front_name}.jpg",
                'front_name': front_name,
                'disable_auto_tokens': card_dict.get('disable_auto_tokens', False),
                'is_new': False,
            }
            forged += 1

    save_staging(folder_path, staging)
    return jsonify({'forged': forged, 'staged_count': len(staging), 'errors': errors})


@app.route('/deck/<deck_name>/publish-assembly-line', methods=['POST'])
def publish_assembly_line(deck_name):
    """Copy staged images to Cards/, regenerate Printing/, update deck JSON, run Cockatrice export."""
    deck_name = unquote(deck_name)
    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    folder_path = deck_data['folder_path']
    staging = load_staging(folder_path)
    staging_dir = get_staging_path(folder_path)

    if not staging:
        return jsonify({'error': 'Nothing to publish'}), 400

    cards_dir = os.path.join(folder_path, 'Cards')
    printing_dir = os.path.join(folder_path, 'Printing')
    os.makedirs(cards_dir, exist_ok=True)
    os.makedirs(printing_dir, exist_ok=True)

    with open(deck_data['json_path'], 'r') as f:
        raw_deck = json.load(f)

    setname = deck_data['metadata'].get('setname', 'UNK')
    gen = ImageGenerator()
    cards_updated = 0
    printing_ok = True
    printing_errors = []

    for card_name, entry in staging.items():
        # Pending-delete: remove from deck JSON and Cards/ image
        if entry.get('pending_delete'):
            raw_deck.get('cards', {}).pop(card_name, None)
            card_img = os.path.join(cards_dir, f"{card_name}.jpg")
            if os.path.isfile(card_img):
                os.remove(card_img)
            cards_updated += 1
            continue

        front_name = entry.get('front_name') or card_name
        # Use staged_image_path if present (handles sanitized filenames for DFC real cards)
        staged_img_rel = entry.get('staged_image_path', '')
        staged_img_filename = os.path.basename(staged_img_rel) if staged_img_rel else f"{front_name}.jpg"
        staged_img = os.path.join(staging_dir, staged_img_filename)
        # Copy staged image → Cards/
        if os.path.isfile(staged_img):
            shutil.copy2(staged_img, os.path.join(cards_dir, staged_img_filename))

        # Also copy back face staged image for DFCs
        updated_data_entry = entry.get('updated', {})
        back_face_data = updated_data_entry.get('back') or {}
        back_face_name = back_face_data.get('name')
        if back_face_name:
            staged_back = os.path.join(staging_dir, f"{back_face_name}.jpg")
            if os.path.isfile(staged_back):
                shutil.copy2(staged_back, os.path.join(cards_dir, f"{back_face_name}.jpg"))

        # Replace the deck JSON entry with the updated data (not merge — merge would
        # leave removed fields like subspell/back/double_faced_type in place).
        # Preserve fields the editor doesn't manage: quantity, tags, real, colors.
        updated_data = entry.get('updated', {})
        old_entry = raw_deck.get('cards', {}).get(card_name, {})
        new_entry = dict(updated_data)
        for key in ('quantity', 'tags', 'real', 'colors'):
            if key in old_entry:
                new_entry[key] = old_entry[key]
        new_entry['complete'] = 1
        raw_deck.setdefault('cards', {})[card_name] = new_entry

        # Regenerate printing image from the staged image (skip for real cards)
        if not updated_data.get('real'):
            try:
                card_list = card_from_editor_dict(updated_data, setname=setname)
                if card_list:
                    from src.rendering.card_renderer import create_printing_image_from_Card
                    create_printing_image_from_Card(
                        card_list[0],
                        saved_image_path=cards_dir,
                        save_path=printing_dir,
                    )
            except Exception as e:
                print(f"Printing regen failed for {card_name}: {e}")
                printing_ok = False
                printing_errors.append(f"{card_name}: {str(e)[:120]}")

        cards_updated += 1

    # Persist updated deck JSON
    _touch_last_modified(raw_deck)
    with open(deck_data['json_path'], 'w') as f:
        json.dump(raw_deck, f, indent=2)

    # Clear staging sidecar and staged images (including back faces for DFCs)
    for card_name, entry in staging.items():
        staged_img_rel = entry.get('staged_image_path', '')
        staged_img_filename = os.path.basename(staged_img_rel) if staged_img_rel else f"{(entry.get('front_name') or card_name)}.jpg"
        staged_img = os.path.join(staging_dir, staged_img_filename)
        if os.path.isfile(staged_img):
            os.remove(staged_img)
        updated_entry = entry.get('updated') or {}
        back_face_name = (updated_entry.get('back') or {}).get('name')
        if back_face_name:
            staged_back = os.path.join(staging_dir, f"{back_face_name}.jpg")
            if os.path.isfile(staged_back):
                os.remove(staged_back)
    save_staging(folder_path, {})

    # Cockatrice export
    cockatrice_ok = None  # None = not configured
    cockatrice_error = None
    try:
        from src.services.cockatrice_exporter import CockatriceExporter
        from src.core.deck import Deck
        exporter = CockatriceExporter()
        if exporter.is_cockatrice_available():
            deck_obj = Deck.from_json(deck_data['json_path'], setname, deck_data['folder_name'])
            exporter.export_deck(deck_obj)
            cockatrice_ok = True
    except Exception as e:
        print(f"Cockatrice export failed: {e}")
        cockatrice_ok = False
        cockatrice_error = str(e)

    total_cards = sum(
        c.get('quantity', 1) if isinstance(c, dict) else 1
        for c in raw_deck.get('cards', {}).values()
    )

    return jsonify({
        'cards_updated': cards_updated,
        'total_cards': total_cards,
        'printing_ok': printing_ok,
        'printing_errors': printing_errors,
        'cockatrice_ok': cockatrice_ok,
        'cockatrice_error': cockatrice_error,
        'staged_count': 0,
        'published_cards': list(staging.keys()),
    })


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
    _touch_last_modified(full_deck_data)

    # Save back to JSON
    with open(json_path, 'w') as f:
        json.dump(full_deck_data, f, indent=2)

    flash(f'Card "{card_name}" saved successfully!', 'success')
    return redirect(url_for('card_editor', deck_name=deck_name, card_name=card_name))


# ── Scryfall API proxy endpoints ──────────────────────────────────────────────

@app.route('/api/scryfall/search')
def scryfall_search():
    """Proxy Scryfall card search by name with optional color filter."""
    q = request.args.get('q', '').strip()
    colors = request.args.get('colors', 'wubrg').strip().lower()
    if not q or len(q) < 2:
        return jsonify({'cards': []})

    included = set(colors) & set('wubrg')
    excluded = set('wubrg') - included

    # Build Scryfall search query using partial name match
    params = urlencode({'q': q, 'unique': 'cards', 'order': 'name'})
    url = f'https://api.scryfall.com/cards/search?{params}'

    _scryfall_headers = {'User-Agent': 'MagicManufactor/1.0', 'Accept': 'application/json'}
    try:
        req = _url_req.Request(url, headers=_scryfall_headers)
        with _url_req.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        cards = []
        for card in data.get('data', []):
            ci = set(c.lower() for c in card.get('color_identity', []))
            # Exclude if card has any excluded color
            if excluded and ci & excluded:
                continue
            cards.append({
                'name': card.get('name', ''),
                'oracle_id': card.get('oracle_id', ''),
                'mana_cost': card.get('mana_cost', ''),
                'type_line': card.get('type_line', ''),
                'color_identity': card.get('color_identity', []),
            })
        return jsonify({'cards': cards[:20]})

    except Exception as e:
        # 404 from Scryfall means no results
        return jsonify({'cards': [], 'error': str(e)})


@app.route('/api/scryfall/printings')
def scryfall_printings():
    """Get all printings of a card by exact name."""
    name = request.args.get('name', '').strip()
    if not name:
        return jsonify({'printings': []})

    params = urlencode({'q': f'!"{name}"', 'unique': 'prints', 'order': 'released', 'dir': 'asc'})
    url = f'https://api.scryfall.com/cards/search?{params}'

    _scryfall_headers = {'User-Agent': 'MagicManufactor/1.0', 'Accept': 'application/json'}
    try:
        req = _url_req.Request(url, headers=_scryfall_headers)
        with _url_req.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        printings = []
        for card in data.get('data', []):
            images = card.get('image_uris', {})
            # Double-faced cards store images per face
            if not images and card.get('card_faces'):
                images = (card['card_faces'][0] or {}).get('image_uris', {})
            mana_cost = card.get('mana_cost', '')
            oracle_text = card.get('oracle_text', '')
            if not mana_cost and card.get('card_faces'):
                mana_cost = (card['card_faces'][0] or {}).get('mana_cost', '')
            if not oracle_text and card.get('card_faces'):
                oracle_text = (card['card_faces'][0] or {}).get('oracle_text', '')
            printings.append({
                'id': card.get('id', ''),
                'oracle_id': card.get('oracle_id', ''),
                'name': card.get('name', ''),
                'set': card.get('set', '').upper(),
                'set_name': card.get('set_name', ''),
                'collector_number': card.get('collector_number', ''),
                'released_at': card.get('released_at', ''),
                'image_uri': images.get('normal') or images.get('large', ''),
                'image_uri_small': images.get('small') or images.get('normal', ''),
                'mana_cost': mana_cost,
                'type_line': card.get('type_line', ''),
                'oracle_text': oracle_text,
                'power': card.get('power', ''),
                'toughness': card.get('toughness', ''),
                'colors': card.get('colors', []),
                'color_identity': card.get('color_identity', []),
                'rarity': card.get('rarity', 'common'),
                'artist': card.get('artist', ''),
                'layout': card.get('layout', ''),
            })
        return jsonify({'printings': printings})

    except Exception as e:
        return jsonify({'printings': [], 'error': str(e)})


@app.route('/deck/<deck_name>/add-real-card', methods=['POST'])
def add_real_card(deck_name):
    """Add or update a real MTG card in the deck via the staging pipeline."""
    deck_name = unquote(deck_name)
    data = request.get_json() or {}

    card_name   = data.get('name', '').strip()
    image_uri   = data.get('image_uri', '').strip()
    quantity    = max(1, int(data.get('quantity', 1) or 1))
    scryfall_id = data.get('scryfall_id', '').strip()
    oracle_id   = data.get('oracle_id', '').strip()
    mana_cost   = data.get('mana_cost', '') or ''
    type_line   = data.get('type_line', '') or ''
    oracle_text = data.get('oracle_text', '') or ''
    power       = data.get('power', '') or ''
    toughness   = data.get('toughness', '') or ''
    colors      = data.get('colors', [])
    color_id    = data.get('color_identity', [])
    rarity      = (data.get('rarity', 'common') or 'common').lower()
    set_code    = data.get('set', '') or ''
    set_name_v  = data.get('set_name', '') or ''
    artist      = data.get('artist', '') or ''

    if not card_name or not image_uri:
        return jsonify({'error': 'card name and image_uri required'}), 400

    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    folder_path = deck_data['folder_path']
    staging_dir = get_staging_path(folder_path)
    os.makedirs(staging_dir, exist_ok=True)

    # Parse type_line → cardtype + subtype + supertypes
    cardtype = type_line
    subtype  = ''
    if '\u2014' in type_line:
        parts    = type_line.split('\u2014', 1)
        cardtype = parts[0].strip()
        subtype  = parts[1].strip()

    legendary = basic = snow = 0
    ct_words = cardtype.split()
    if 'Legendary' in ct_words: legendary = 1; ct_words.remove('Legendary')
    if 'Basic'     in ct_words: basic     = 1; ct_words.remove('Basic')
    if 'Snow'      in ct_words: snow      = 1; ct_words.remove('Snow')
    cardtype_clean = ' '.join(ct_words)

    # Sanitize card name for use as a filename (e.g. "Foo // Bar" → "Foo -- Bar")
    safe_card_filename = card_name.replace(' // ', ' -- ').replace('/', '-')

    # Download Scryfall image → Staging/<safe_name>.jpg
    staged_img_path = os.path.join(staging_dir, f"{safe_card_filename}.jpg")
    try:
        req = _url_req.Request(image_uri, headers={'User-Agent': 'MagicManufactor/1.0', 'Accept': 'image/*,*/*'})
        with _url_req.urlopen(req, timeout=20) as resp:
            img_bytes = resp.read()
        with open(staged_img_path, 'wb') as f:
            f.write(img_bytes)
    except Exception as e:
        return jsonify({'error': f'Failed to download card image: {e}'}), 500

    card_entry = {
        'front': {
            'name': card_name,
            'mana': mana_cost,
            'cardtype': cardtype_clean,
            'subtype': subtype,
            'rules': oracle_text,
            'power': power,
            'toughness': toughness,
            'legendary': legendary,
            'basic': basic,
            'snow': snow,
        },
        'quantity': quantity,
        'real': 1,
        'complete': 0,
        'rarity': rarity,
        'colors': colors,
        'color_identity': color_id,
        'scryfall_id': scryfall_id,
        'oracle_id': oracle_id,
        'set': set_code,
        'set_name': set_name_v,
        'artist': artist,
        'image_uri': image_uri,
    }

    with open(deck_data['json_path'], 'r') as f:
        raw_deck = json.load(f)

    is_new   = card_name not in raw_deck.get('cards', {})
    original = raw_deck.get('cards', {}).get(card_name, {})

    raw_deck.setdefault('cards', {})[card_name] = card_entry
    _touch_last_modified(raw_deck)
    with open(deck_data['json_path'], 'w') as f:
        json.dump(raw_deck, f, indent=2)

    staging = load_staging(folder_path)
    staging[card_name] = {
        'original': original,
        'updated':  card_entry,
        'staged_image_path': f"Staging/{safe_card_filename}.jpg",
        'front_name': card_name,
        'is_new':  is_new,
        'is_real': True,
    }
    save_staging(folder_path, staging)

    image_b64 = None
    if os.path.isfile(staged_img_path):
        with open(staged_img_path, 'rb') as f:
            image_b64 = 'data:image/jpeg;base64,' + base64.b64encode(f.read()).decode()

    return jsonify({
        'success': True,
        'is_new':  is_new,
        'staged_count': len(staging),
        'image_base64': image_b64,
    })


@app.route('/api/print-run/cards')
def print_run_cards():
    """Return cards from Printing/ folders sorted by most recently modified, up to 6 months back."""
    from datetime import datetime
    scope = request.args.get('scope', 'all').strip()

    settings_mgr = SettingsManager()
    deck_path = settings_mgr.get_deck_path()
    if not deck_path or not os.path.isdir(deck_path):
        return jsonify({'error': 'Deck path not configured'}), 400

    cutoff = datetime.now().timestamp() - (180 * 24 * 3600)  # 6 months ago

    # Identify deck folders (must have a matching <FolderName>.json)
    if scope == 'all':
        try:
            deck_names = [
                d for d in os.listdir(deck_path)
                if os.path.isdir(os.path.join(deck_path, d))
                and os.path.isfile(os.path.join(deck_path, d, f"{d}.json"))
            ]
        except OSError:
            deck_names = []
    else:
        deck_names = [scope] if (
            os.path.isdir(os.path.join(deck_path, scope))
            and os.path.isfile(os.path.join(deck_path, scope, f"{scope}.json"))
        ) else []

    cards = []
    for deck_name in deck_names:
        printing_dir = os.path.join(deck_path, deck_name, 'Printing')
        if not os.path.isdir(printing_dir):
            continue
        json_path = os.path.join(deck_path, deck_name, f"{deck_name}.json")
        try:
            with open(json_path, 'r') as f:
                raw_deck = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        for card_key in raw_deck.get('cards', {}):
            # For DFC/subspell cards the key is "FrontName / BackName"; use the
            # front name to find the Printing/ image and get its mtime.
            front_name = card_key.partition(' / ')[0].strip() if ' / ' in card_key else card_key
            fpath = os.path.join(printing_dir, f"{front_name}.jpg")
            try:
                mtime = os.path.getmtime(fpath)
            except OSError:
                continue
            if mtime < cutoff:
                continue
            cards.append({
                'deck_name': deck_name,
                'card_name': card_key,
                'modified_timestamp': mtime,
            })

    cards.sort(key=lambda x: x['modified_timestamp'], reverse=True)

    now = datetime.now().timestamp()
    for card in cards:
        age = now - card['modified_timestamp']
        if age < 3600:
            rel = f"{int(age / 60)}m ago"
        elif age < 86400:
            rel = f"{int(age / 3600)}h ago"
        elif age < 7 * 86400:
            rel = f"{int(age / 86400)}d ago"
        elif age < 30 * 86400:
            rel = f"{int(age / 86400 / 7)}w ago"
        else:
            rel = f"{int(age / 86400 / 30)}mo ago"
        card['modified_relative'] = rel

    return jsonify({'cards': cards})


@app.route('/api/print-run/prepare', methods=['POST'])
def print_run_prepare():
    """Create a PrintRun-<date> folder, save print_run.json, and copy Printing/ images into it."""
    from datetime import date as _date

    data = request.get_json() or {}
    cards_by_deck = data.get('cards', {})  # {deck_name: [card_name, ...]}

    if not cards_by_deck or not any(cards_by_deck.values()):
        return jsonify({'error': 'No cards selected'}), 400

    settings_mgr = SettingsManager()
    deck_path = settings_mgr.get_deck_path()
    if not deck_path or not os.path.isdir(deck_path):
        return jsonify({'error': 'Deck path not configured'}), 400

    today = _date.today().isoformat()
    base_dir_name = f"PrintRun-{today}"
    output_dir_name = base_dir_name
    output_dir = os.path.join(deck_path, output_dir_name)
    counter = 2
    while os.path.exists(output_dir):
        output_dir_name = f"{base_dir_name}-{counter}"
        output_dir = os.path.join(deck_path, output_dir_name)
        counter += 1

    os.makedirs(output_dir)

    with open(os.path.join(output_dir, 'print_run.json'), 'w') as f:
        json.dump(cards_by_deck, f, indent=2)

    total_cards = sum(len(v) for v in cards_by_deck.values())
    pad = len(str(total_cards))
    card_counter = 0
    copied = 0
    errors = []

    for deck_name, card_names in cards_by_deck.items():
        printing_path = os.path.join(deck_path, deck_name, 'Printing')
        for card_name in card_names:
            card_counter += 1
            front, _, back = card_name.partition(' / ')
            if back:
                for prefix, name in [('Front', front), ('Back', back)]:
                    src = os.path.join(printing_path, f'{name}.jpg')
                    if not os.path.isfile(src):
                        # Subspell back faces share the front image — skip silently
                        continue
                    dst_name = f"{prefix}_{card_counter:0{pad}}_{name}.jpg"
                    dst = os.path.join(output_dir, dst_name)
                    try:
                        shutil.copyfile(src, dst)
                        copied += 1
                    except Exception as e:
                        errors.append(f"{deck_name}/{name}: {e}")
            else:
                src = os.path.join(printing_path, f'{card_name}.jpg')
                dst_name = f"Front_{card_counter:0{pad}}_{card_name}.jpg"
                dst = os.path.join(output_dir, dst_name)
                try:
                    shutil.copyfile(src, dst)
                    copied += 1
                except Exception as e:
                    errors.append(f"{deck_name}/{card_name}: {e}")

    return jsonify({
        'success': True,
        'output_dir': output_dir_name,
        'copied': copied,
        'total_selected': total_cards,
        'errors': errors,
    })


# ── Cockatrice Cleanup helpers ────────────────────────────────────────────────

def _normalize_name_for_match(name):
    """Normalize a raw card name to match against decoded XML <name> element text."""
    return (name
            .replace('\u2019', "'").replace('\u2018', "'")
            .replace('.', ' ')
            .replace("'", '')
            .replace(' // ', ' -- '))


def _normalize_name_for_image(name):
    """Normalize a raw card name to get the Cockatrice CUSTOM/ image filename base (no .full.jpeg)."""
    return (name
            .replace('\u2019', "'").replace('\u2018', "'")
            .replace('"', '')
            .replace('.', ' ')
            .replace("'", '')
            .replace(' // ', ' -- ')
            .replace('/', ''))


def _get_all_deck_card_info(deck_path):
    """
    Scan all decks and return name sets for Cockatrice cleanup matching.

    Returns:
        dict of {deck_folder: {
            'setname': str,
            'xml_names': set of normalized names that should appear in <name> tags,
            'image_names': set of normalized image base names (no .full.jpeg),
            'token_image_prefixes': set of "SETNAME_tokenname" prefixes
        }}
    """
    result = {}
    try:
        folders = [
            d for d in os.listdir(deck_path)
            if os.path.isdir(os.path.join(deck_path, d))
            and os.path.isfile(os.path.join(deck_path, d, f'{d}.json'))
        ]
    except OSError:
        return result

    for folder in folders:
        json_path = os.path.join(deck_path, folder, f'{folder}.json')
        try:
            with open(json_path) as f:
                raw = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        setname = (raw.get('metadata') or {}).get('setname', '')
        if not setname:
            continue

        xml_names = set()
        image_names = set()
        token_image_prefixes = set()

        for card_data in (raw.get('cards') or {}).values():
            front = card_data.get('front') or {}
            back = card_data.get('back') or {}
            front_name = front.get('name', '')
            back_name = back.get('name', '')

            if card_data.get('real'):
                # Real cards are not in the custom XML, but their images may exist in
                # CUSTOM/ from previous exports — track them so they aren't flagged.
                if front_name:
                    image_names.add(_normalize_name_for_image(front_name))
                if back_name:
                    image_names.add(_normalize_name_for_image(back_name))
                continue

            if front.get('token'):
                # Token in cards section — use consistent normalization for prefix
                if front_name:
                    token_image_prefixes.add(_normalize_name_for_image(setname + '_' + front_name))
                continue  # Tokens go in tokens.xml, not customsets XML

            if front_name:
                xml_names.add(_normalize_name_for_match(front_name))
                image_names.add(_normalize_name_for_image(front_name))
            if back_name:
                xml_names.add(_normalize_name_for_match(back_name))
                image_names.add(_normalize_name_for_image(back_name))

        # Process the dedicated "tokens" section (e.g. "_TOKEN_Foo" entries)
        for token_data in (raw.get('tokens') or {}).values():
            token_name = token_data.get('name', '')
            if token_name:
                token_image_prefixes.add(_normalize_name_for_image(setname + '_' + token_name))

        result[folder] = {
            'setname': setname,
            'xml_names': xml_names,
            'image_names': image_names,
            'token_image_prefixes': token_image_prefixes,
        }

    return result


@app.route('/api/cockatrice-cleanup/scan')
def cockatrice_cleanup_scan():
    """Scan Cockatrice customsets XML files and CUSTOM image folder for orphaned/straggler entries."""
    import xml.etree.ElementTree as ET
    import re

    scope = request.args.get('scope', 'all').strip()

    settings_mgr = SettingsManager()
    deck_path = settings_mgr.get_deck_path()
    cockatrice_path = settings_mgr.get_cockatrice_path()

    if not deck_path or not os.path.isdir(deck_path):
        return jsonify({'error': 'Deck path not configured'}), 400
    if not cockatrice_path or not os.path.isdir(cockatrice_path):
        return jsonify({'error': 'Cockatrice path not configured'}), 400

    all_decks = _get_all_deck_card_info(deck_path)

    # Build reverse map: setname → merged deck info (xml_names / image_names)
    setname_to_info = {}
    for folder, info in all_decks.items():
        sn = info['setname']
        if sn not in setname_to_info:
            setname_to_info[sn] = {
                'xml_names': set(info['xml_names']),
                'image_names': set(info['image_names']),
            }
        else:
            setname_to_info[sn]['xml_names'] |= info['xml_names']
            setname_to_info[sn]['image_names'] |= info['image_names']

    all_setnames = set(setname_to_info.keys())

    # Determine which setnames are "in scope" for orphan checking
    if scope == 'all':
        scoped_setnames = all_setnames
    else:
        scoped_setnames = {
            info['setname']
            for folder, info in all_decks.items()
            if folder == scope
        }

    # ── Scan customsets/XX.custom.xml files ──────────────────────────────────
    customsets_path = os.path.join(cockatrice_path, 'customsets')
    if not os.path.isdir(customsets_path):
        return jsonify({'error': f'Cockatrice customsets folder not found: {customsets_path}'}), 400

    junk_xml_cards = []
    seen = set()  # (xml_name, set_code) already reported

    for filename in sorted(os.listdir(customsets_path)):
        if not re.match(r'^\d{2}\.custom\.xml$', filename):
            continue
        xml_path = os.path.join(customsets_path, filename)
        try:
            tree = ET.parse(xml_path)
        except ET.ParseError:
            continue

        root = tree.getroot()
        # Find cards under the <cards> element to avoid matching <set> entries
        cards_elem = root.find('cards')
        if cards_elem is None:
            continue

        for card_elem in cards_elem.findall('card'):
            name_elem = card_elem.find('name')
            set_elem = card_elem.find('set')
            if name_elem is None or set_elem is None:
                continue
            xml_name = (name_elem.text or '').strip()
            set_code = (set_elem.text or '').strip()

            key = (xml_name, set_code)
            if key in seen:
                continue
            seen.add(key)

            # Normalize the XML name for deck-membership matching (old XML entries may
            # still contain apostrophes or other characters that cockatrice.py strips).
            xml_name_norm = _normalize_name_for_match(xml_name)

            if set_code in scoped_setnames:
                # Belongs to a scoped deck's set — check if the card is actually in that deck
                deck_info = setname_to_info.get(set_code)
                if deck_info and xml_name_norm not in deck_info['xml_names']:
                    junk_xml_cards.append({
                        'xml_name': xml_name,
                        'set_code': set_code,
                        'category': 'orphan',
                        'reason': f'Set {set_code} is a known deck but card not found in deck JSON',
                    })
            elif set_code not in all_setnames:
                # Straggler: always shown regardless of scope
                junk_xml_cards.append({
                    'xml_name': xml_name,
                    'set_code': set_code,
                    'category': 'straggler',
                    'reason': f'Set code {set_code} does not belong to any known deck',
                })

    # ── Scan CUSTOM image folder ──────────────────────────────────────────────
    custom_image_path = os.path.join(cockatrice_path, 'pics', 'CUSTOM')
    junk_images = []

    if os.path.isdir(custom_image_path):
        all_valid_image_names = set()
        all_token_prefixes = set()
        for info in all_decks.values():
            all_valid_image_names |= info['image_names']
            all_token_prefixes |= info.get('token_image_prefixes', set())

        for fname in sorted(os.listdir(custom_image_path)):
            if not fname.endswith('.full.jpeg'):
                continue
            base = fname[:-len('.full.jpeg')]
            # Normalize for matching — old files may have apostrophes or other
            # characters that cockatrice.py now strips from filenames.
            base_norm = _normalize_name_for_image(base)
            if base_norm in all_valid_image_names:
                continue
            # Check token image prefixes (normalized, with optional _N suffix)
            is_token = any(
                base_norm == prefix or re.match(r'^' + re.escape(prefix) + r'_\d+$', base_norm)
                for prefix in all_token_prefixes
            )
            if is_token:
                continue
            junk_images.append({
                'filename': fname,
                'reason': 'No matching card found in any deck',
            })

    return jsonify({
        'junk_xml_cards': junk_xml_cards,
        'junk_images': junk_images,
    })


@app.route('/api/cockatrice-cleanup/purge', methods=['POST'])
def cockatrice_cleanup_purge():
    """Remove selected junk XML card entries and image files from Cockatrice folders."""
    import xml.etree.ElementTree as ET
    import re

    data = request.get_json() or {}
    xml_cards_to_purge = data.get('xml_cards', [])  # [{xml_name, set_code}]
    images_to_delete = data.get('images', [])        # [filename]

    if not xml_cards_to_purge and not images_to_delete:
        return jsonify({'error': 'Nothing selected to purge'}), 400

    settings_mgr = SettingsManager()
    cockatrice_path = settings_mgr.get_cockatrice_path()
    if not cockatrice_path or not os.path.isdir(cockatrice_path):
        return jsonify({'error': 'Cockatrice path not configured'}), 400

    purge_set = {
        (c['xml_name'], c['set_code'])
        for c in xml_cards_to_purge
        if 'xml_name' in c and 'set_code' in c
    }

    errors = []
    removed_names = set()

    # ── Update all customsets/XX.custom.xml and manufactor/custom.xml ────────
    if purge_set:
        xml_files = []
        customsets_path = os.path.join(cockatrice_path, 'customsets')
        if os.path.isdir(customsets_path):
            for fn in sorted(os.listdir(customsets_path)):
                if re.match(r'^\d{2}\.custom\.xml$', fn):
                    xml_files.append(os.path.join(customsets_path, fn))

        manufactor_xml = os.path.join(cockatrice_path, 'manufactor', 'custom.xml')
        if os.path.isfile(manufactor_xml):
            xml_files.append(manufactor_xml)

        for xml_path in xml_files:
            try:
                tree = ET.parse(xml_path)
            except ET.ParseError as e:
                errors.append(f'Parse error in {os.path.basename(xml_path)}: {e}')
                continue

            root = tree.getroot()
            cards_elem = root.find('cards')
            if cards_elem is None:
                continue

            to_remove = []
            for card_elem in cards_elem.findall('card'):
                name_elem = card_elem.find('name')
                set_elem = card_elem.find('set')
                if name_elem is None or set_elem is None:
                    continue
                xml_name = (name_elem.text or '').strip()
                set_code = (set_elem.text or '').strip()
                if (xml_name, set_code) in purge_set:
                    to_remove.append(card_elem)
                    removed_names.add((xml_name, set_code))

            for card_elem in to_remove:
                cards_elem.remove(card_elem)

            if to_remove:
                try:
                    tree.write(xml_path, encoding='unicode')
                except Exception as e:
                    errors.append(f'Write error for {os.path.basename(xml_path)}: {e}')

        # Also clean up manufactor/custom.json
        custom_json_path = os.path.join(cockatrice_path, 'manufactor', 'custom.json')
        if os.path.isfile(custom_json_path):
            try:
                with open(custom_json_path) as f:
                    custom_json = json.load(f)
                purge_xml_names = {xml_name for (xml_name, _) in purge_set}
                keys_to_remove = [
                    k for k in custom_json
                    if _normalize_name_for_match(k) in purge_xml_names
                ]
                for k in keys_to_remove:
                    del custom_json[k]
                with open(custom_json_path, 'w') as f:
                    json.dump(custom_json, f)
            except Exception as e:
                errors.append(f'Failed to update custom.json: {e}')

    # ── Delete image files ────────────────────────────────────────────────────
    images_deleted = 0
    custom_image_path = os.path.join(cockatrice_path, 'pics', 'CUSTOM')
    if os.path.isdir(custom_image_path):
        for fname in images_to_delete:
            if not fname.endswith('.full.jpeg'):
                errors.append(f'Skipped (not .full.jpeg): {fname}')
                continue
            if os.sep in fname or '/' in fname or '..' in fname:
                errors.append(f'Skipped (unsafe filename): {fname}')
                continue
            fpath = os.path.join(custom_image_path, fname)
            if os.path.isfile(fpath):
                try:
                    os.remove(fpath)
                    images_deleted += 1
                except Exception as e:
                    errors.append(f'Failed to delete {fname}: {e}')
            else:
                errors.append(f'Already gone: {fname}')

    return jsonify({
        'success': True,
        'xml_cards_removed': len(removed_names),
        'images_deleted': images_deleted,
        'errors': errors,
    })


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


# ── Interactions ──────────────────────────────────────────────────────────────

@app.route('/deck/<deck_name>/interactions/add', methods=['POST'])
def add_interaction(deck_name):
    """Add a new interaction to the deck."""
    import uuid
    deck_name = unquote(deck_name)
    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    data = request.get_json() or {}
    interaction = {
        'id': str(uuid.uuid4()),
        'title': data.get('title', '').strip(),
        'description': data.get('description', '').strip(),
        'groups': data.get('groups', []),
    }

    json_path = deck_data['json_path']
    with open(json_path, 'r') as f:
        raw_deck = json.load(f)

    raw_deck.setdefault('interactions', []).append(interaction)
    _touch_last_modified(raw_deck)

    with open(json_path, 'w') as f:
        json.dump(raw_deck, f, indent=2)

    return jsonify({'success': True, 'interaction': interaction, 'interactions': raw_deck['interactions']})


@app.route('/deck/<deck_name>/interactions/<interaction_id>/update', methods=['POST'])
def update_interaction(deck_name, interaction_id):
    """Update an existing interaction."""
    deck_name = unquote(deck_name)
    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    data = request.get_json() or {}
    json_path = deck_data['json_path']
    with open(json_path, 'r') as f:
        raw_deck = json.load(f)

    interactions = raw_deck.get('interactions', [])
    for i, item in enumerate(interactions):
        if item.get('id') == interaction_id:
            interactions[i] = {
                'id': interaction_id,
                'title': data.get('title', '').strip(),
                'description': data.get('description', '').strip(),
                'groups': data.get('groups', []),
            }
            break

    raw_deck['interactions'] = interactions
    _touch_last_modified(raw_deck)

    with open(json_path, 'w') as f:
        json.dump(raw_deck, f, indent=2)

    return jsonify({'success': True, 'interactions': interactions})


@app.route('/deck/<deck_name>/interactions/<interaction_id>/delete', methods=['POST'])
def delete_interaction(deck_name, interaction_id):
    """Delete an interaction."""
    deck_name = unquote(deck_name)
    deck_data = load_deck_by_name(deck_name)
    if not deck_data:
        return jsonify({'error': 'Deck not found'}), 404

    json_path = deck_data['json_path']
    with open(json_path, 'r') as f:
        raw_deck = json.load(f)

    raw_deck['interactions'] = [
        item for item in raw_deck.get('interactions', [])
        if item.get('id') != interaction_id
    ]
    _touch_last_modified(raw_deck)

    with open(json_path, 'w') as f:
        json.dump(raw_deck, f, indent=2)

    return jsonify({'success': True, 'interactions': raw_deck['interactions']})


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
