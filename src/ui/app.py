"""
Main UI application for Magic Card Manufactor.

This module provides the Gradio-based web interface for the card creation tool.
"""

import gradio as gr
import json
from pathlib import Path
from src.services.settings_manager import SettingsManager
from src.utils.paths import PROJECT_ROOT


def save_settings(deck_path: str, cockatrice_path: str):
    """
    Save settings to config.json.

    Args:
        deck_path: Path to deck folder
        cockatrice_path: Path to Cockatrice installation

    Returns:
        Tuple of (success message, updated deck path, updated cockatrice path)
    """
    settings = SettingsManager()

    try:
        # Set the paths
        settings.set_deck_path(deck_path)
        settings.set_cockatrice_path(cockatrice_path)

        # Validate
        errors = settings.get_validation_errors()
        if errors:
            warning_msg = "Settings saved with warnings:\n" + "\n".join(f"- {e}" for e in errors)
            return warning_msg, deck_path, cockatrice_path
        else:
            return "Settings saved successfully!", deck_path, cockatrice_path

    except Exception as e:
        return f"Error saving settings: {str(e)}", deck_path, cockatrice_path


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
            gr.Markdown("""
            ## Your Decks

            Browse and manage your custom card decks.

            *Deck management features coming soon...*
            """)

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
                outputs=[status_message, deck_path_input, cockatrice_path_input]
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
