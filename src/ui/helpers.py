"""
Helper functions for the Manufactor Flask UI.

This module contains utility functions extracted from the original Gradio app
for working with decks, cards, artwork, and tokens.
"""

import json
import os
import base64
import io
import unicodedata
from pathlib import Path
from PIL import Image, ImageDraw
from src.services.settings_manager import SettingsManager
from src.utils.paths import PROJECT_ROOT
from src.core.mana import Mana

# CSS background colors for each MTG color (used in deck color banner)
_COLOR_BANNER_CSS = {
    'w': '#f5f0d8',
    'u': '#1565a8',
    'b': '#1a1a1a',
    'r': '#cc2b28',
    'g': '#1a7835',
}
_GOLD_BANNER_CSS = '#e0b832'
_COLORLESS_BANNER_CSS = '#8a8a8a'


def _get_deck_colors(cards_dict, metadata):
    """Return deck colors in WUBRG order, derived from metadata or card costs."""
    meta_colors = metadata.get('colors', [])
    if meta_colors:
        return Mana.colors_to_wubrg_order([c.lower() for c in meta_colors])
    all_colors = set()
    for card_data in cards_dict.values():
        if isinstance(card_data, dict):
            # mana is nested under 'front' for standard cards
            cost = card_data.get('front', {}).get('mana', '') or card_data.get('mana', '')
            if cost:
                all_colors.update(Mana.get_colors(cost))
    return Mana.colors_to_wubrg_order(list(all_colors))


def _get_banner_style(colors):
    """Return CSS background style string for the deck color banner."""
    if len(colors) == 0:
        return f'background: {_COLORLESS_BANNER_CSS};'
    elif len(colors) == 1:
        return f'background: {_COLOR_BANNER_CSS.get(colors[0], _COLORLESS_BANNER_CSS)};'
    elif len(colors) == 2:
        c1 = _COLOR_BANNER_CSS.get(colors[0], _COLORLESS_BANNER_CSS)
        c2 = _COLOR_BANNER_CSS.get(colors[1], _COLORLESS_BANNER_CSS)
        return f'background: linear-gradient(to bottom, {c1} 50%, {c2} 50%);'
    else:
        return f'background: {_GOLD_BANNER_CSS};'


def get_available_decks():
    """
    Get list of available decks from the configured deck path.

    Returns:
        List of tuples (deck_name, deck_path, deck_json_path) or empty list if path not configured
    """
    settings = SettingsManager()
    deck_path = settings.get_deck_path()

    if not deck_path or not deck_path.strip() or not os.path.isdir(deck_path):
        return []

    decks = []
    try:
        for item in os.listdir(deck_path):
            item_path = os.path.join(deck_path, item)
            if os.path.isdir(item_path):
                # Check if there's a JSON file with the same name
                json_file = os.path.join(item_path, f"{item}.json")
                if os.path.isfile(json_file):
                    decks.append((item, item_path, json_file))
    except (OSError, PermissionError):
        return []

    return sorted(decks, key=lambda x: x[0])


_ARTWORK_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']
_APOSTROPHE_TABLE = str.maketrans({'\u2019': "'", '\u2018': "'", '\u02bc': "'"})


def _normalize_artwork_name(s):
    """Normalize a name for fuzzy file matching: NFC + lowercase + apostrophe variants → plain apostrophe."""
    return unicodedata.normalize('NFC', s).lower().translate(_APOSTROPHE_TABLE)


def get_card_artwork_path(deck_folder_path, card_name):
    """
    Get the file path for a card's artwork.

    Args:
        deck_folder_path: Path to the deck folder
        card_name: Name of the card to find artwork for

    Returns:
        Path to the artwork file or None if not found
    """
    if not card_name:
        return None

    artwork_folder = os.path.join(deck_folder_path, "Artwork")
    if not os.path.isdir(artwork_folder):
        return None

    names_to_try = [card_name]
    if " / " in card_name:
        names_to_try.append(card_name.split(" / ")[0])

    # Fast path: exact filename match
    for name in names_to_try:
        for ext in _ARTWORK_EXTENSIONS:
            path = os.path.join(artwork_folder, f"{name}{ext}")
            if os.path.isfile(path):
                return path

    # Fallback: scan directory with normalized comparison
    # Handles apostrophe variants (U+0027 vs U+2019) and case differences
    try:
        files = os.listdir(artwork_folder)
    except OSError:
        return None

    for name in names_to_try:
        target = _normalize_artwork_name(name)
        for f in files:
            base, ext = os.path.splitext(f)
            if ext.lower() not in _ARTWORK_EXTENSIONS:
                continue
            if _normalize_artwork_name(base) == target:
                return os.path.join(artwork_folder, f)

    return None


def create_diagonal_split_image(deck_folder_path, card_name_1, card_name_2):
    """
    Create a composite image with two cards split diagonally.

    Args:
        deck_folder_path: Path to the deck folder
        card_name_1: Name of first card (top-left)
        card_name_2: Name of second card (bottom-right)

    Returns:
        PIL Image object or None if either image not found
    """
    # Get paths to both artwork files
    path1 = get_card_artwork_path(deck_folder_path, card_name_1)
    path2 = get_card_artwork_path(deck_folder_path, card_name_2)

    if not path1 or not path2:
        return None

    try:
        # Load both images
        img1 = Image.open(path1).convert('RGB')
        img2 = Image.open(path2).convert('RGB')

        # Resize both images to the same size (use the larger dimensions)
        target_width = 800
        target_height = 600

        img1 = img1.resize((target_width, target_height), Image.Resampling.LANCZOS)
        img2 = img2.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # Create a new image for the composite
        composite = Image.new('RGB', (target_width, target_height))

        # Create a mask for the diagonal split (top-left to bottom-right)
        mask = Image.new('L', (target_width, target_height), 0)
        draw = ImageDraw.Draw(mask)

        # Draw a diagonal triangle for the top-left portion
        # Polygon points: top-left corner, top-right corner, bottom-right corner
        draw.polygon([(0, 0), (target_width, 0), (target_width, target_height), (0, target_height)], fill=255)
        draw.polygon([(0, 0), (target_width, target_height), (0, target_height)], fill=0)

        # Composite the images using the mask
        composite.paste(img1, (0, 0))
        composite.paste(img2, (0, 0), mask)

        return composite

    except Exception as e:
        print(f"Error creating diagonal split image: {e}")
        return None


def pil_image_to_base64(img):
    """
    Convert a PIL Image to base64 data URI.

    Args:
        img: PIL Image object

    Returns:
        Base64 encoded data URI string
    """
    try:
        # Save image to bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)

        # Encode to base64
        img_data = buffer.read()
        b64_data = base64.b64encode(img_data).decode('utf-8')
        return f"data:image/jpeg;base64,{b64_data}"
    except Exception as e:
        print(f"Error converting PIL image to base64: {e}")
        return None


def get_card_artwork_base64(deck_folder_path, card_name):
    """
    Get the base64 encoded artwork image for a card.

    Args:
        deck_folder_path: Path to the deck folder
        card_name: Name of the card to find artwork for

    Returns:
        Base64 encoded image string or None if not found
    """
    if not card_name:
        return None

    # Get the artwork path
    artwork_path = get_card_artwork_path(deck_folder_path, card_name)
    if not artwork_path:
        return None

    try:
        with open(artwork_path, 'rb') as img_file:
            img_data = img_file.read()
            # Encode to base64
            b64_data = base64.b64encode(img_data).decode('utf-8')
            # Determine MIME type from extension
            ext = os.path.splitext(artwork_path)[1].lower()
            mime_type = f"image/{ext[1:]}"
            if ext in ['.jpg', '.jpeg']:
                mime_type = "image/jpeg"
            return f"data:{mime_type};base64,{b64_data}"
    except Exception as e:
        print(f"Error loading artwork from {artwork_path}: {e}")
        return None


def get_decks_with_metadata(filter_status='all', sort_order='recent'):
    """
    Get decks with full metadata for display.

    Args:
        filter_status: "all", "complete", or "incomplete"
        sort_order: "recent" (default, newest last_modified first) or "alpha" (A-Z by name)

    Returns:
        List of dicts with deck info
    """
    decks = get_available_decks()
    result = []

    for folder_name, deck_folder_path, json_path in decks:
        with open(json_path, 'r') as f:
            deck_data = json.load(f)

        metadata = deck_data.get('metadata', {})
        cards_dict = deck_data.get('cards', {})
        deck_complete = metadata.get('complete', 0)

        # Apply filter
        if filter_status == "complete" and not deck_complete:
            continue
        elif filter_status == "incomplete" and deck_complete:
            continue

        # Get deck display name
        display_name = metadata.get('deck_name', folder_name)

        # Get card image name for background
        card_image_name = None
        is_partner_commanders = False

        # Get deck_image from metadata, or auto-select
        deck_image_raw = metadata.get('deck_image', '')
        card_image_name = deck_image_raw.strip() if deck_image_raw else ''

        # Auto-select if deck_image is not specified
        if not card_image_name:
            deck_format = metadata.get('format', '')
            # If Commander format, use the commander
            if deck_format and deck_format.lower() == 'commander':
                commander = metadata.get('commander', '')
                # Handle both string and list (for partner commanders)
                if isinstance(commander, list):
                    if len(commander) == 2:
                        is_partner_commanders = True
                    card_image_name = commander[0].strip() if commander else ''
                elif commander:
                    card_image_name = commander.strip()

            # If still no image, use first card
            if not card_image_name and cards_dict:
                card_image_name = list(cards_dict.keys())[0]

        # Get the background image
        bg_image_data = None

        # Check if this is a partner commander deck (exactly 2 commanders)
        if is_partner_commanders:
            commander = metadata.get('commander', [])
            # Create diagonal split image for partner commanders
            composite_img = create_diagonal_split_image(deck_folder_path, commander[0], commander[1])
            if composite_img:
                bg_image_data = pil_image_to_base64(composite_img)

        # Fall back to single card image if not partner commanders
        if not bg_image_data and card_image_name:
            bg_image_data = get_card_artwork_base64(deck_folder_path, card_image_name)

        # Calculate total card count including quantities
        total_card_count = 0
        for card_name, card_data in cards_dict.items():
            if isinstance(card_data, dict):
                total_card_count += card_data.get('quantity', 1)
            else:
                total_card_count += 1

        colors_wubrg = _get_deck_colors(cards_dict, metadata)
        banner_style = _get_banner_style(colors_wubrg)

        result.append({
            'name': display_name,
            'folder_name': folder_name,
            'card_count': total_card_count,
            'format': metadata.get('format', ''),
            'description': metadata.get('description', ''),
            'commander': metadata.get('commander', ''),
            'complete': deck_complete,
            'artwork_base64': bg_image_data,
            'json_path': json_path,
            'folder_path': deck_folder_path,
            'colors_wubrg': colors_wubrg,
            'banner_style': banner_style,
            'last_modified': metadata.get('last_modified', ''),
        })

    if sort_order == 'alpha':
        result.sort(key=lambda d: d['name'].lower())
    else:
        # Default: most recently modified first; decks without a timestamp go last
        result.sort(key=lambda d: d['last_modified'] or '', reverse=True)

    return result


def get_card_image_path(deck_folder_path, card_name):
    """
    Get the file path for a card image from the Cards folder.

    Args:
        deck_folder_path: Path to the deck folder
        card_name: Name of the card to find image for

    Returns:
        Path to the card image file or None if not found
    """
    if not card_name:
        return None

    # Look for the card image in the Cards subfolder
    cards_folder = os.path.join(deck_folder_path, "Cards")
    if not os.path.isdir(cards_folder):
        return None

    # List of card names to try (for double-faced cards)
    names_to_try = [card_name]

    # If it's a double-faced card (contains " / "), try the front face
    if " / " in card_name:
        front_face = card_name.split(" / ")[0]
        names_to_try.append(front_face)

    # Try to find the image file (support common image extensions)
    for name in names_to_try:
        for ext in ['.jpg', '.jpeg', '.png', '.gif']:
            image_path = os.path.join(cards_folder, f"{name}{ext}")
            if os.path.isfile(image_path):
                return image_path

    return None


def get_card_image_base64(deck_folder_path, card_name):
    """
    Get the base64 encoded card image from the Cards folder.

    Args:
        deck_folder_path: Path to the deck folder
        card_name: Name of the card to find image for

    Returns:
        Base64 encoded image string or None if not found
    """
    if not card_name:
        return None

    # Get the card image path
    image_path = get_card_image_path(deck_folder_path, card_name)
    if not image_path:
        return None

    try:
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
            # Encode to base64
            b64_data = base64.b64encode(img_data).decode('utf-8')
            # Determine MIME type from extension
            ext = os.path.splitext(image_path)[1].lower()
            mime_type = f"image/{ext[1:]}"
            if ext in ['.jpg', '.jpeg']:
                mime_type = "image/jpeg"
            return f"data:{mime_type};base64,{b64_data}"
    except Exception as e:
        print(f"Error loading card image from {image_path}: {e}")
        return None


def load_deck_by_name(deck_name):
    """
    Load deck data by display name.

    Args:
        deck_name: Display name of the deck to load

    Returns:
        Dict with deck data or None if not found
    """
    decks = get_available_decks()

    for folder_name, deck_folder_path, json_path in decks:
        with open(json_path, 'r') as f:
            deck_data = json.load(f)

        metadata = deck_data.get('metadata', {})
        display_name = metadata.get('deck_name', folder_name)

        if display_name == deck_name:
            # Get commander card images if present
            commander_images = []
            commander_names = []
            commander = metadata.get('commander')
            if commander:
                if isinstance(commander, str):
                    commander_names = [commander]
                    # Single commander
                    commander_img = get_card_image_base64(deck_folder_path, commander)
                    if commander_img:
                        commander_images.append(commander_img)
                elif isinstance(commander, list):
                    commander_names = commander
                    # Multiple commanders
                    for commander_name in commander:
                        commander_img = get_card_image_base64(deck_folder_path, commander_name)
                        if commander_img:
                            commander_images.append(commander_img)

            # Get card images from Cards folder, excluding commanders
            commander_cards = {}
            cards_with_images = {}
            for card_name, card_data in deck_data.get('cards', {}).items():
                # Skip commander cards to avoid duplication
                if card_name in commander_names:
                    commander_cards[card_name] = card_data if isinstance(card_data, dict) else {}
                    continue
                # Get the card image (from Cards folder, not Artwork folder)
                card_image = get_card_image_base64(deck_folder_path, card_name)

                # Get quantity (default to 1 if not specified)
                quantity = 1
                if isinstance(card_data, dict):
                    quantity = card_data.get('quantity', 1)

                # Load back face image for double-faced cards
                back_image = None
                if isinstance(card_data, dict) and card_data.get('double_faced_type'):
                    back_name = (card_data.get('back') or {}).get('name')
                    if back_name:
                        back_image = get_card_image_base64(deck_folder_path, back_name)

                cards_with_images[card_name] = {
                    **(card_data if isinstance(card_data, dict) else {}),
                    'image_base64': card_image,
                    'back_image_base64': back_image,
                    'quantity': quantity
                }

            # Calculate total card count including commanders and quantities
            total_cards = 0
            unique_cards = 0
            custom_cards = 0
            for card_name, card_data in deck_data.get('cards', {}).items():
                unique_cards += 1
                if isinstance(card_data, dict):
                    total_cards += card_data.get('quantity', 1)
                    if not card_data.get('real', 0):
                        custom_cards += 1
                else:
                    total_cards += 1
                    custom_cards += 1

            commander_count = len(commander_names)

            # Load tokens from deck JSON (new format stores them under "tokens" key)
            tokens_dict = deck_data.get('tokens', {})
            tokens_with_images = {}
            tokens_folder = os.path.join(deck_folder_path, 'Tokens')
            for token_key, token_data in tokens_dict.items():
                if not isinstance(token_data, dict):
                    continue
                display_token_name = token_data.get('name', token_key.replace('_TOKEN_', ''))
                token_image = None
                if os.path.isdir(tokens_folder):
                    for name_to_try in [display_token_name, token_key]:
                        for ext in ['.jpg', '.jpeg', '.png']:
                            img_path = os.path.join(tokens_folder, f"{name_to_try}{ext}")
                            if os.path.isfile(img_path):
                                try:
                                    with open(img_path, 'rb') as f:
                                        b64 = base64.b64encode(f.read()).decode('utf-8')
                                        token_image = f"data:image/jpeg;base64,{b64}"
                                except Exception:
                                    pass
                                break
                        if token_image:
                            break
                # Load back face image for double-faced tokens
                token_back_image = None
                if token_data.get('double_faced_type'):
                    token_back_name = (token_data.get('back') or {}).get('name')
                    if token_back_name and os.path.isdir(tokens_folder):
                        for ext in ['.jpg', '.jpeg', '.png']:
                            back_img_path = os.path.join(tokens_folder, f"{token_back_name}{ext}")
                            if os.path.isfile(back_img_path):
                                try:
                                    with open(back_img_path, 'rb') as f:
                                        b64 = base64.b64encode(f.read()).decode('utf-8')
                                        token_back_image = f"data:image/jpeg;base64,{b64}"
                                except Exception:
                                    pass
                                break

                tokens_with_images[token_key] = {
                    **token_data,
                    'image_base64': token_image,
                    'back_image_base64': token_back_image,
                    'quantity': token_data.get('quantity', 1),
                }

            return {
                'name': display_name,
                'folder_name': folder_name,
                'folder_path': deck_folder_path,
                'json_path': json_path,
                'metadata': metadata,
                'cards': cards_with_images,
                'tokens': tokens_with_images,
                'commander_cards': commander_cards,
                'commander_images': commander_images if commander_images else None,
                'total_cards': total_cards,
                'unique_cards': unique_cards,
                'custom_cards': custom_cards,
                'commander_count': commander_count
            }

    return None


def load_common_tokens():
    """
    Load common token definitions.

    Returns:
        Dictionary of token definitions
    """
    tokens_path = Path(PROJECT_ROOT) / "config" / "common_tokens.json"
    if tokens_path.exists():
        with open(tokens_path, 'r') as f:
            return json.load(f)
    return {}


def save_common_tokens(tokens_dict):
    """
    Save common token definitions.

    Args:
        tokens_dict: Dictionary of token definitions
    """
    tokens_path = Path(PROJECT_ROOT) / "config" / "common_tokens.json"
    with open(tokens_path, 'w') as f:
        json.dump(tokens_dict, f, indent=2)


# ─── Staging helpers ────────────────────────────────────────────────────────

def get_staging_path(deck_folder_path):
    """Return path to the Staging/ folder for a deck."""
    return os.path.join(deck_folder_path, 'Staging')


def load_staging(deck_folder_path):
    """
    Load the staging sidecar JSON for a deck.

    Returns a dict mapping card_name → staged entry, or {} if none exists.
    """
    folder_name = os.path.basename(deck_folder_path)
    staging_json = os.path.join(deck_folder_path, f'{folder_name}_staging.json')
    if os.path.isfile(staging_json):
        try:
            with open(staging_json, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_staging(deck_folder_path, data):
    """
    Persist the staging sidecar JSON for a deck.

    Args:
        deck_folder_path: Path to the deck folder
        data: Dict mapping card_name → staged entry
    """
    folder_name = os.path.basename(deck_folder_path)
    staging_json = os.path.join(deck_folder_path, f'{folder_name}_staging.json')
    with open(staging_json, 'w') as f:
        json.dump(data, f, indent=2)


def compute_setname(deck_name: str, exclude_setname: str = None) -> str:
    """
    Auto-compute a 3-letter set code from a deck name.

    - Strips leading "The ", "A ", "An " (case-insensitive)
    - Takes first 3 alpha characters, uppercase
    - Checks uniqueness against existing decks' setnames
    - Appends digits or substitutes last letter if collision

    Args:
        deck_name: The proposed deck name
        exclude_setname: Current setname to exclude from collision check (for editing)

    Returns:
        A unique 3-letter set code
    """
    import string as _string
    from src.core.card_set import CardSet

    # Collect existing set names
    existing_setnames = set()
    try:
        for _, __, _jpath in get_available_decks():
            with open(_jpath, 'r') as _f:
                _data = json.load(_f)
            _sn = _data.get('metadata', {}).get('setname', '')
            if _sn and (exclude_setname is None or _sn.upper() != exclude_setname.upper()):
                existing_setnames.add(_sn.upper())
    except Exception:
        pass

    # Strip leading articles
    name = deck_name.strip()
    for prefix in ('the ', 'a ', 'an '):
        if name.lower().startswith(prefix):
            name = name[len(prefix):]
            break

    # Get first 3 alpha characters
    letters = ''.join(c for c in name if c.isalpha())
    if len(letters) >= 3:
        base = letters[:3].upper()
    elif letters:
        base = letters.upper().ljust(3, 'X')
    else:
        base = 'NEW'

    # Try base, then digits, then letter substitutions
    candidate = CardSet.adjust_forbidden_custom_setname(base)
    if candidate not in existing_setnames:
        return candidate

    for digit in '23456789':
        candidate = CardSet.adjust_forbidden_custom_setname(base[:2] + digit)
        if candidate not in existing_setnames:
            return candidate

    for char in _string.ascii_uppercase:
        candidate = CardSet.adjust_forbidden_custom_setname(base[:2] + char)
        if candidate not in existing_setnames:
            return candidate

    return base  # Fallback


def card_from_editor_dict(card_dict, setname='UNK'):
    """
    Build Card object(s) from the card editor JSON dict.

    Handles single-faced and double-faced cards.

    Args:
        card_dict: Card dict as sent by the editor (front/back/rarity/etc.)
        setname:   Set code to assign to the card(s)

    Returns:
        List of Card objects: [front_card] for single-faced cards,
        [front_card, back_card] for double-faced cards.
    """
    from src.core.card import Card, CardFace

    front_data  = card_dict.get('front') or {}
    back_data   = card_dict.get('back')  or {}
    dfc_type    = card_dict.get('double_faced_type') or None
    rarity      = card_dict.get('rarity')
    quantity    = card_dict.get('quantity', 1)
    complete    = card_dict.get('complete', 0)
    real        = card_dict.get('real', 0)
    tags        = card_dict.get('tags') or None
    # frame is face-specific; fall back to top-level for backward compat with old JSONs
    front_frame = front_data.get('frame') or card_dict.get('frame') or None
    back_frame  = back_data.get('frame') or None
    front_name  = front_data.get('name', '')
    back_name   = back_data.get('name', '')

    if dfc_type and back_name:
        # Double-faced card — build front and back Card objects
        front_card = Card(
            name=front_name, setname=setname,
            mana=front_data.get('mana'), cardtype=front_data.get('cardtype'),
            subtype=front_data.get('subtype'), power=front_data.get('power'),
            toughness=front_data.get('toughness'), rarity=rarity,
            rules=front_data.get('rules'),
            rules1=front_data.get('rules1'), rules2=front_data.get('rules2'),
            rules3=front_data.get('rules3'), rules4=front_data.get('rules4'),
            rules5=front_data.get('rules5'), rules6=front_data.get('rules6'),
            flavor=front_data.get('flavor'),
            special=f"{dfc_type}-front", related=back_name,
            tags=tags, quantity=quantity, complete=complete, real=real, frame=front_frame,
            legendary=front_data.get('legendary'),
            basic=front_data.get('basic'),
            snow=front_data.get('snow'),
        )
        front_card.front = CardFace(
            name=front_name,
            mana=front_data.get('mana'), cardtype=front_data.get('cardtype'),
            subtype=front_data.get('subtype'), power=front_data.get('power'),
            toughness=front_data.get('toughness'),
            rules=front_data.get('rules'),
            rules1=front_data.get('rules1'), rules2=front_data.get('rules2'),
            rules3=front_data.get('rules3'), rules4=front_data.get('rules4'),
            rules5=front_data.get('rules5'), rules6=front_data.get('rules6'),
            flavor=front_data.get('flavor'),
            legendary=front_data.get('legendary'),
            basic=front_data.get('basic'),
            snow=front_data.get('snow'),
        )
        back_face = CardFace(
            name=back_name,
            mana=back_data.get('mana'), cardtype=back_data.get('cardtype'),
            subtype=back_data.get('subtype'), power=back_data.get('power'),
            toughness=back_data.get('toughness'),
            rules=back_data.get('rules'),
            rules1=back_data.get('rules1'), rules2=back_data.get('rules2'),
            rules3=back_data.get('rules3'), rules4=back_data.get('rules4'),
            rules5=back_data.get('rules5'), rules6=back_data.get('rules6'),
            flavor=back_data.get('flavor'),
            legendary=back_data.get('legendary'),
            basic=back_data.get('basic'),
            snow=back_data.get('snow'),
        )
        front_card.back = back_face
        front_card.double_faced_type = dfc_type

        back_card = Card(
            name=back_name, setname=setname,
            mana=back_data.get('mana'), cardtype=back_data.get('cardtype'),
            subtype=back_data.get('subtype'), power=back_data.get('power'),
            toughness=back_data.get('toughness'), rarity=rarity,
            rules=back_data.get('rules'),
            rules1=back_data.get('rules1'), rules2=back_data.get('rules2'),
            rules3=back_data.get('rules3'), rules4=back_data.get('rules4'),
            rules5=back_data.get('rules5'), rules6=back_data.get('rules6'),
            flavor=back_data.get('flavor'),
            special=f"{dfc_type}-back", related=front_name,
            complete=complete, real=real, frame=back_frame,
            legendary=back_data.get('legendary'),
            basic=back_data.get('basic'),
            snow=back_data.get('snow'),
        )
        back_card.double_faced_type = dfc_type

        # Set related_indicator for MDFC cards so the renderer draws the opposite-face box.
        # Format expected by card_renderer: "OtherFaceName {mana}" (split on first '{').
        if dfc_type == 'mdfc':
            back_mana = back_data.get('mana') or ''
            front_mana = front_data.get('mana') or ''
            front_card.related_indicator = (back_name + (' ' + back_mana if back_mana else '')).strip()
            back_card.related_indicator = (front_name + (' ' + front_mana if front_mana else '')).strip()

        return [front_card, back_card]
    else:
        # Single-faced card
        card = Card(
            name=front_name, setname=setname,
            mana=front_data.get('mana'), cardtype=front_data.get('cardtype'),
            subtype=front_data.get('subtype'), power=front_data.get('power'),
            toughness=front_data.get('toughness'), rarity=rarity,
            rules=front_data.get('rules'),
            rules1=front_data.get('rules1'), rules2=front_data.get('rules2'),
            rules3=front_data.get('rules3'), rules4=front_data.get('rules4'),
            rules5=front_data.get('rules5'), rules6=front_data.get('rules6'),
            flavor=front_data.get('flavor'),
            tags=tags, quantity=quantity, complete=complete, real=real, frame=front_frame,
            legendary=front_data.get('legendary'),
            basic=front_data.get('basic'),
            snow=front_data.get('snow'),
            token=front_data.get('token'),
        )
        # Attach subspell if present (Adventure/Omen)
        subspell_data = card_dict.get('subspell') or {}
        if subspell_data.get('name') and subspell_data.get('cardtype'):
            subspell_face = CardFace(
                name=subspell_data['name'],
                mana=subspell_data.get('mana'),
                cardtype=subspell_data.get('cardtype'),
                subtype=subspell_data.get('subtype'),
                rules=subspell_data.get('rules'),
                flavor=subspell_data.get('flavor'),
            )
            card.subspell = subspell_face
        return [card]
