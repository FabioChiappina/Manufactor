"""
Main UI application for Magic Card Manufactor.

This module provides the Gradio-based web interface for the card creation tool.
"""

import gradio as gr
import json
import os
import base64
import io
from pathlib import Path
from PIL import Image, ImageDraw
from src.services.settings_manager import SettingsManager
from src.services.deck_manager import DeckManager
from src.utils.paths import PROJECT_ROOT


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


def check_deck_path_configured():
    """
    Check if deck path is configured.

    Returns:
        Tuple of (is_configured: bool, message: str)
    """
    settings = SettingsManager()
    deck_path = settings.get_deck_path()

    if not deck_path or not deck_path.strip():
        return False, """## ⚠️ Configuration Required

**Error**: Deck path is not configured.

Please go to the **Settings** tab and configure your Deck Path before using Manufactor."""
    else:
        return True, """## Your Decks

Browse and manage your custom card decks.

*Deck management features coming soon...*"""


def save_settings(deck_path: str, cockatrice_path: str):
    """
    Save settings to config.json.

    Args:
        deck_path: Path to deck folder
        cockatrice_path: Path to Cockatrice installation

    Returns:
        Tuple of (success message, updated deck path, updated cockatrice path, updated deck cards HTML)
    """
    settings = SettingsManager()

    try:
        # Set the paths
        settings.set_deck_path(deck_path)
        settings.set_cockatrice_path(cockatrice_path)

        # Validate
        errors = settings.get_validation_errors()

        # Refresh deck view HTML
        deck_html = create_deck_cards_html()

        if errors:
            warning_msg = "Settings saved with warnings:\n" + "\n".join(f"- {e}" for e in errors)
            return warning_msg, deck_path, cockatrice_path, deck_html
        else:
            return "Settings saved successfully!", deck_path, cockatrice_path, deck_html

    except Exception as e:
        deck_html = create_deck_cards_html()
        return f"Error saving settings: {str(e)}", deck_path, cockatrice_path, deck_html


def load_current_settings():
    """
    Load current settings from config.

    Returns:
        Tuple of (deck_path, cockatrice_path)
    """
    settings = SettingsManager()
    return settings.get_deck_path(), settings.get_cockatrice_path()


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


def get_tokens_dataframe():
    """
    Get tokens as a list of lists for Gradio DataFrame.

    Returns:
        List of [name, type, subtype, rules, colors, frame] rows
    """
    tokens = load_common_tokens()
    rows = []
    for name, data in tokens.items():
        # Format colors as comma-separated string
        colors = ', '.join(data.get('colors', []))
        frame = data.get('frame', '')

        rows.append([
            name,
            data.get('cardtype', ''),
            data.get('subtype', ''),
            data.get('rules', ''),
            colors,
            frame
        ])
    return rows


def add_token(name: str, cardtype: str, subtype: str, rules: str, colors: str, frame: str):
    """
    Add a new token to common_tokens.json.

    Args:
        name: Token name
        cardtype: Card type
        subtype: Subtype
        rules: Rules text
        colors: Colors (comma-separated, e.g., "W, U" or empty for colorless)
        frame: Frame name (empty for default)

    Returns:
        Tuple of (status message, updated dataframe)
    """
    if not name or not name.strip():
        return "Error: Token name is required", get_tokens_dataframe()

    tokens = load_common_tokens()

    if name in tokens:
        return f"Error: Token '{name}' already exists. Delete it first if you want to replace it.", get_tokens_dataframe()

    # Parse colors from comma-separated string
    colors_list = []
    if colors and colors.strip():
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
    if frame and frame.strip():
        token_data["frame"] = frame.strip()

    tokens[name] = token_data

    save_common_tokens(tokens)
    return f"Token '{name}' added successfully!", get_tokens_dataframe()


def delete_token(name: str):
    """
    Delete a token from common_tokens.json.

    Args:
        name: Token name to delete

    Returns:
        Tuple of (status message, updated dataframe)
    """
    if not name or not name.strip():
        return "Error: Please enter a token name to delete", get_tokens_dataframe()

    tokens = load_common_tokens()

    if name not in tokens:
        return f"Error: Token '{name}' not found", get_tokens_dataframe()

    del tokens[name]
    save_common_tokens(tokens)
    return f"Token '{name}' deleted successfully!", get_tokens_dataframe()


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

    # Look for the artwork file in the Artwork subfolder
    artwork_folder = os.path.join(deck_folder_path, "Artwork")
    if not os.path.isdir(artwork_folder):
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
            artwork_path = os.path.join(artwork_folder, f"{name}{ext}")
            if os.path.isfile(artwork_path):
                return artwork_path

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
        max_width = max(img1.width, img2.width)
        max_height = max(img1.height, img2.height)

        # Use a standard size for consistency
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


def create_deck_cards_html():
    """
    Create HTML for displaying decks as cards.

    Returns:
        HTML string with deck cards
    """
    settings = SettingsManager()
    deck_path = settings.get_deck_path()

    # Check if deck path is configured
    if not deck_path or not deck_path.strip():
        return """
        <div style="padding: 20px; text-align: center;">
            <h2>⚠️ Configuration Required</h2>
            <p>Deck path is not configured. Please go to the <strong>Settings</strong> tab and configure your Deck Path.</p>
        </div>
        """

    if not os.path.isdir(deck_path):
        return f"""
        <div style="padding: 20px; text-align: center;">
            <h2>⚠️ Deck Path Not Found</h2>
            <p>The configured deck path does not exist: <code>{deck_path}</code></p>
            <p>Please update the path in the <strong>Settings</strong> tab.</p>
        </div>
        """

    # Get available decks
    decks = get_available_decks()

    if not decks:
        return """
        <div style="padding: 20px; text-align: center;">
            <h2>No Decks Found</h2>
            <p>No valid deck folders found in your deck path.</p>
            <p>A valid deck folder must contain a JSON file with the same name as the folder.</p>
            <p>For example: <code>/Decks/MyDeck/MyDeck.json</code></p>
        </div>
        """

    # Create card grid HTML
    html = """
    <style>
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
    </style>
    <div class="deck-grid">
    """

    for folder_name, deck_folder_path, json_path in decks:
        # Try to get some info from the JSON file
        card_count = "?"
        deck_description = ""
        deck_format = ""
        display_name = folder_name  # Default to folder name
        card_image_name = None
        background_style = ""

        try:
            with open(json_path, 'r') as f:
                deck_data = json.load(f)
                # Handle both old (list) and new (dict with metadata) formats
                if isinstance(deck_data, list):
                    card_count = len(deck_data)
                    # For old format, use first card if available
                    if deck_data:
                        card_image_name = deck_data[0].get('name') if isinstance(deck_data[0], dict) else None
                elif isinstance(deck_data, dict):
                    cards_dict = deck_data.get('cards', {})
                    if cards_dict:
                        card_count = len(cards_dict)

                    if 'metadata' in deck_data:
                        metadata = deck_data['metadata']
                        # Use deck_name from metadata if available
                        display_name = metadata.get('deck_name', folder_name)
                        deck_description = metadata.get('description', '')[:100]  # First 100 chars
                        deck_format = metadata.get('format', '')

                        # Get deck_image from metadata, or auto-select
                        deck_image_raw = metadata.get('deck_image', '')
                        card_image_name = deck_image_raw.strip() if deck_image_raw else ''

                        # Auto-select if deck_image is not specified
                        if not card_image_name:
                            # If Commander format, use the commander
                            if deck_format and deck_format.lower() == 'commander':
                                commander = metadata.get('commander', '')
                                # Handle both string and list (for partner commanders)
                                if isinstance(commander, list):
                                    card_image_name = commander[0].strip() if commander else ''
                                elif commander:
                                    card_image_name = commander.strip()

                            # If still no image, use first card
                            if not card_image_name and cards_dict:
                                card_image_name = list(cards_dict.keys())[0]
        except Exception as e:
            print(f"Error processing deck {folder_name}: {e}")
            pass

        # Get the background image
        bg_image_data = None
        is_partner_commanders = False

        # Check if this is a partner commander deck (exactly 2 commanders)
        try:
            with open(json_path, 'r') as f:
                deck_data_check = json.load(f)
                if isinstance(deck_data_check, dict) and 'metadata' in deck_data_check:
                    meta_check = deck_data_check['metadata']
                    commander_check = meta_check.get('commander', '')
                    if isinstance(commander_check, list) and len(commander_check) == 2:
                        is_partner_commanders = True
                        # Create diagonal split image for partner commanders
                        composite_img = create_diagonal_split_image(deck_folder_path, commander_check[0], commander_check[1])
                        if composite_img:
                            bg_image_data = pil_image_to_base64(composite_img)
        except:
            pass

        # Fall back to single card image if not partner commanders
        if not bg_image_data and card_image_name:
            bg_image_data = get_card_artwork_base64(deck_folder_path, card_image_name)

        # Apply background style if we have image data
        if bg_image_data:
            background_style = f' style="--bg-image: url(\'{bg_image_data}\')"'

        # Create deck info line
        info_parts = [f"📦 {card_count} cards"]
        if deck_format:
            info_parts.append(f"🎮 {deck_format}")

        html += f"""
        <div class="deck-card"{background_style} onclick="alert('Deck details for {display_name} coming soon!')">
            <h3>{display_name}</h3>
            <div class="deck-card-info">{' • '.join(info_parts)}</div>
            {f'<div class="deck-card-info">{deck_description}...</div>' if deck_description else ''}
            <div class="deck-card-path">{json_path}</div>
        </div>
        """

    html += """
    </div>
    """

    return html


def refresh_deck_view():
    """
    Refresh the deck view by regenerating the HTML.

    Returns:
        Updated HTML for deck cards
    """
    return create_deck_cards_html()


def create_ui():
    """
    Create and configure the main Gradio UI.

    Returns:
        gr.Blocks: Configured Gradio interface
    """
    # Create the main interface using Gradio Blocks
    with gr.Blocks(title="Manufactor") as app:
        gr.Markdown("# Manufactor")
        gr.Markdown("Welcome to the Magic: The Gathering custom card creator!")

        # My Decks tab
        with gr.Tab("My Decks"):
            gr.Markdown("## My Decks")
            gr.Markdown("Click on a deck card to view details (coming soon)")

            # Refresh button
            refresh_btn = gr.Button("🔄 Refresh Decks", size="sm")

            # Deck cards display
            deck_cards_display = gr.HTML(create_deck_cards_html)

            # Wire up refresh button
            refresh_btn.click(
                fn=refresh_deck_view,
                outputs=[deck_cards_display]
            )

        # Settings tab
        with gr.Tab("Settings", elem_id="settings-tab"):
            gr.Markdown("## Configuration")
            gr.Markdown("Configure paths for deck storage and Cockatrice integration.")

            save_button = gr.Button("Save Settings", variant="primary")
            status_message = gr.Textbox(label="Status", interactive=False, lines=3)

            with gr.Group():
                gr.Markdown("### Deck Path")
                gr.Markdown("Location where your deck folders and card files are stored.")
                deck_path_input = gr.Textbox(
                    label="Deck Path",
                    placeholder="/path/to/your/Decks",
                    value=lambda: load_current_settings()[0]
                )

            with gr.Group():
                gr.Markdown("### Cockatrice Path")
                gr.Markdown("Root folder of your Cockatrice installation.")
                cockatrice_path_input = gr.Textbox(
                    label="Cockatrice Path",
                    placeholder="~/Library/Application Support/Cockatrice/Cockatrice",
                    value=lambda: load_current_settings()[1]
                )

            # Wire up the save button
            save_button.click(
                fn=save_settings,
                inputs=[deck_path_input, cockatrice_path_input],
                outputs=[status_message, deck_path_input, cockatrice_path_input, deck_cards_display]
            )

            gr.Markdown("---")

            # Common Tokens section
            gr.Markdown("## Common Token Definitions")
            gr.Markdown("Manage predefined tokens (Treasure, Clue, Food, etc.) that can be automatically generated.")

            # Display current tokens
            with gr.Group():
                gr.Markdown("### Current Tokens")
                tokens_display = gr.Dataframe(
                    headers=["Name", "Card Type", "Subtype", "Rules Text", "Colors", "Frame"],
                    value=get_tokens_dataframe,
                    interactive=False,
                    wrap=True,
                    column_widths=["12%", "12%", "12%", "42%", "10%", "12%"]
                )

            # Add new token
            with gr.Group():
                gr.Markdown("### Add New Token")
                with gr.Row():
                    token_name = gr.Textbox(label="Token Name", placeholder="e.g., Treasure")
                    token_cardtype = gr.Textbox(label="Card Type", placeholder="e.g., Artifact")
                    token_subtype = gr.Textbox(label="Subtype", placeholder="e.g., Treasure")
                with gr.Row():
                    token_rules = gr.Textbox(label="Rules Text", placeholder="e.g., {T}, Sacrifice...", lines=2)
                with gr.Row():
                    token_colors = gr.Textbox(label="Colors (comma-separated)", placeholder="e.g., W, U or leave empty for colorless")
                    token_frame = gr.Textbox(label="Frame (optional)", placeholder="Leave empty for default")

                add_token_button = gr.Button("Add Token", variant="secondary")
                add_token_status = gr.Textbox(label="Add Status", interactive=False)

                add_token_button.click(
                    fn=add_token,
                    inputs=[token_name, token_cardtype, token_subtype, token_rules, token_colors, token_frame],
                    outputs=[add_token_status, tokens_display]
                )

            # Delete token
            with gr.Group():
                gr.Markdown("### Delete Token")
                delete_token_name = gr.Textbox(label="Token Name to Delete", placeholder="e.g., Treasure")
                delete_token_button = gr.Button("Delete Token", variant="stop")
                delete_token_status = gr.Textbox(label="Delete Status", interactive=False)

                delete_token_button.click(
                    fn=delete_token,
                    inputs=[delete_token_name],
                    outputs=[delete_token_status, tokens_display]
                )

        with gr.Tab("About"):
            gr.Markdown("""
            ## About Manufactor

            A Python-based tool for creating custom Magic: The Gathering cards with
            automated image generation and Cockatrice integration.

            ### Features (Coming Soon)
            - Card creation and editing
            - Deck management
            - Image generation
            - Cockatrice export

            ### Built With
            - Python 3.7+
            - Pillow for image processing
            - Gradio for UI

            ### Current Status
            Phase 7 Basic UI - Homepage initialized
            """)

    return app


def launch_ui(share=False, server_port=None):
    """
    Launch the Gradio UI.

    Args:
        share (bool): Whether to create a public share link
        server_port (int): Port to run the server on (None = auto-find available port)
    """
    app = create_ui()
    app.launch(share=share, server_port=server_port)


if __name__ == "__main__":
    # Launch the UI when run directly
    launch_ui()
