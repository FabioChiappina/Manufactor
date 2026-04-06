"""
Main UI application for Magic Card Manufactor.

This module provides the Flask-based web interface for the card creation tool.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
import base64
import json
import os
import shutil
from urllib.parse import unquote, quote
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
    card_from_editor_dict,
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
        staged_img = os.path.join(staging_dir, f"{card_name}.jpg")
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
    artwork_folder = os.path.join(folder_path, 'Artwork')
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

    with open(deck_data['json_path'], 'w') as f:
        json.dump(raw_deck, f, indent=2)

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

    with open(deck_data['json_path'], 'w') as f:
        json.dump(raw_deck, f, indent=2)

    return jsonify({'card_tags': card_tags, 'deck_tags': meta_tags})


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

    # Generate images into Staging/
    gen = ImageGenerator()
    images = {}  # card_name -> base64 string
    for card in cards:
        success = gen.generate_single_card_image(card, save_path=staging_dir, include_printing=False)
        if not success:
            return jsonify({'error': f'Image generation failed for "{card.name}"'}), 500
        # Read the generated image back as base64
        img_path = os.path.join(staging_dir, f"{card.name}.jpg")
        if not os.path.isfile(img_path):
            # Renderer may have used the artwork filename — find it
            for fname in sorted(os.listdir(staging_dir)):
                if fname.startswith(card.name) and fname.endswith('.jpg'):
                    img_path = os.path.join(staging_dir, fname)
                    break
        if os.path.isfile(img_path):
            with open(img_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
                images[card.name] = f"data:image/jpeg;base64,{b64}"

    # Load original card data from deck JSON (for the staging sidecar)
    with open(deck_data['json_path'], 'r') as f:
        raw_deck = json.load(f)

    original = raw_deck.get('cards', {}).get(card_name if not is_new else front_name)

    # For brand-new cards: add a placeholder entry to the deck JSON
    if is_new or original is None:
        placeholder = dict(data)
        placeholder['complete'] = 0
        raw_deck.setdefault('cards', {})[front_name] = placeholder
        with open(deck_data['json_path'], 'w') as f:
            json.dump(raw_deck, f, indent=2)
        original = {}
        is_new = True

    # Update _staging.json sidecar
    staging = load_staging(folder_path)
    staging[front_name] = {
        'original': original,
        'updated': data,
        'staged_image_path': f"Staging/{front_name}.jpg",
        'disable_auto_tokens': data.get('disable_auto_tokens', False),
        'is_new': is_new,
    }
    save_staging(folder_path, staging)

    result = {
        'image_base64': images.get(front_name),
        'staged_count': len(staging),
    }
    if len(cards) > 1:
        result['back_image_base64'] = images.get(cards[1].name)

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

    items = []
    for card_name, entry in staging.items():
        staged_b64 = _b64(os.path.join(staging_dir, f"{card_name}.jpg"))
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

        items.append({
            'card_name': card_name,
            'is_new': entry.get('is_new', False),
            'original_image_base64': original_b64,
            'staged_image_base64': staged_b64,
            'original_back_image_base64': orig_back_b64,
            'staged_back_image_base64': staged_back_b64,
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

    # If card was brand-new (placeholder only), remove it from the deck JSON too
    if entry and entry.get('is_new'):
        with open(deck_data['json_path'], 'r') as f:
            raw_deck = json.load(f)
        if card_name in raw_deck.get('cards', {}):
            del raw_deck['cards'][card_name]
            with open(deck_data['json_path'], 'w') as f:
                json.dump(raw_deck, f, indent=2)

    # Remove staged image file(s) — front and back face for DFCs
    staging_dir = get_staging_path(folder_path)
    staged_img = os.path.join(staging_dir, f"{card_name}.jpg")
    if os.path.isfile(staged_img):
        os.remove(staged_img)
    if entry:
        back_face_name = (entry.get('updated', {}).get('back') or {}).get('name')
        if back_face_name:
            staged_back = os.path.join(staging_dir, f"{back_face_name}.jpg")
            if os.path.isfile(staged_back):
                os.remove(staged_back)

    save_staging(folder_path, staging)
    return jsonify({'staged_count': len(staging)})


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

        if success:
            front_name = cards[0].name
            staging[front_name] = {
                'original': raw_deck['cards'].get(card_name, {}),
                'updated': card_dict,
                'staged_image_path': f"Staging/{front_name}.jpg",
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

    for card_name, entry in staging.items():
        # Copy staged image → Cards/
        staged_img = os.path.join(staging_dir, f"{card_name}.jpg")
        if os.path.isfile(staged_img):
            shutil.copy2(staged_img, os.path.join(cards_dir, f"{card_name}.jpg"))

        # Also copy back face staged image for DFCs
        updated_data_entry = entry.get('updated', {})
        back_face_data = updated_data_entry.get('back') or {}
        back_face_name = back_face_data.get('name')
        if back_face_name:
            staged_back = os.path.join(staging_dir, f"{back_face_name}.jpg")
            if os.path.isfile(staged_back):
                shutil.copy2(staged_back, os.path.join(cards_dir, f"{back_face_name}.jpg"))

        # Merge updated data into deck JSON and mark complete
        updated_data = entry.get('updated', {})
        if card_name in raw_deck.get('cards', {}):
            raw_deck['cards'][card_name].update(updated_data)
            raw_deck['cards'][card_name]['complete'] = 1
        else:
            # New card — add it
            new_entry = dict(updated_data)
            new_entry['complete'] = 1
            raw_deck.setdefault('cards', {})[card_name] = new_entry

        # Regenerate printing image from the staged image
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

        cards_updated += 1

    # Persist updated deck JSON
    with open(deck_data['json_path'], 'w') as f:
        json.dump(raw_deck, f, indent=2)

    # Clear staging sidecar and staged images (including back faces for DFCs)
    for card_name, entry in staging.items():
        staged_img = os.path.join(staging_dir, f"{card_name}.jpg")
        if os.path.isfile(staged_img):
            os.remove(staged_img)
        back_face_name = (entry.get('updated', {}).get('back') or {}).get('name')
        if back_face_name:
            staged_back = os.path.join(staging_dir, f"{back_face_name}.jpg")
            if os.path.isfile(staged_back):
                os.remove(staged_back)
    save_staging(folder_path, {})

    # Cockatrice export
    cockatrice_ok = None  # None = not configured
    try:
        from src.services.cockatrice_exporter import CockatriceExporter
        from src.core.deck import Deck
        exporter = CockatriceExporter()
        if exporter.is_cockatrice_available():
            deck_obj = Deck.from_json(deck_data['json_path'], setname, deck_data['folder_name'])
            cockatrice_ok = exporter.export_deck(deck_obj)
    except Exception as e:
        print(f"Cockatrice export failed: {e}")
        cockatrice_ok = False

    total_cards = sum(
        c.get('quantity', 1) if isinstance(c, dict) else 1
        for c in raw_deck.get('cards', {}).values()
    )

    return jsonify({
        'cards_updated': cards_updated,
        'total_cards': total_cards,
        'printing_ok': printing_ok,
        'cockatrice_ok': cockatrice_ok,
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
