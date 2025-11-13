#!/usr/bin/env python3
"""
CLI tool for configuring Manufactor settings.

Usage:
    python -m src.cli.configure --show              # Show current settings
    python -m src.cli.configure --validate          # Validate configured paths
    python -m src.cli.configure --set-deck-path <path>
    python -m src.cli.configure --set-cockatrice-path <path>
    python -m src.cli.configure --reset             # Reset to defaults
"""

import argparse
import sys
from src.services.settings_manager import SettingsManager


def show_settings(settings: SettingsManager):
    """Display current settings."""
    print("Current Configuration:")
    print("=" * 60)
    print(f"Deck Path:       {settings.get_deck_path()}")
    print(f"Cockatrice Path: {settings.get_cockatrice_path()}")
    print()


def validate_settings(settings: SettingsManager):
    """Validate and display path information."""
    print("Path Validation:")
    print("=" * 60)

    validation = settings.validate_paths()
    all_valid = True

    for path_name, info in validation.items():
        display_name = path_name.replace('_', ' ').title()
        print(f"\n{display_name}:")
        print(f"  Location: {info['path']}")
        print(f"  Exists:   {'Yes' if info['exists'] else 'No'}")
        print(f"  Writable: {'Yes' if info['writable'] else 'No'}")

        if not info['exists'] or not info['writable']:
            all_valid = False

    print()
    errors = settings.get_validation_errors()
    if errors:
        print("Issues Found:")
        for error in errors:
            print(f"  - {error}")
        print()
        return False
    else:
        print("All paths are valid!")
        print()
        return True


def set_deck_path(settings: SettingsManager, path: str):
    """Set the deck path."""
    try:
        if settings.set_deck_path(path):
            print(f"Deck path updated to: {path}")
            validate_settings(settings)
        else:
            print("Error: Failed to save deck path configuration", file=sys.stderr)
            sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def set_cockatrice_path(settings: SettingsManager, path: str):
    """Set the Cockatrice path."""
    try:
        if settings.set_cockatrice_path(path):
            print(f"Cockatrice path updated to: {path}")
            validate_settings(settings)
        else:
            print("Error: Failed to save Cockatrice path configuration", file=sys.stderr)
            sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def reset_settings(settings: SettingsManager):
    """Reset settings to defaults."""
    confirm = input("Reset all settings to defaults? (yes/no): ")
    if confirm.lower() in ['yes', 'y']:
        if settings.reset_to_defaults():
            print("Settings reset to defaults")
            show_settings(settings)
        else:
            print("Error: Failed to reset settings", file=sys.stderr)
            sys.exit(1)
    else:
        print("Reset cancelled")


def main():
    """Main entry point for the configuration CLI."""
    parser = argparse.ArgumentParser(
        description="Configure Manufactor settings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Show current settings:
    python -m src.cli.configure --show

  Validate paths:
    python -m src.cli.configure --validate

  Set deck path:
    python -m src.cli.configure --set-deck-path ~/Documents/Magic/Decks

  Set Cockatrice path:
    python -m src.cli.configure --set-cockatrice-path "~/Library/Application Support/Cockatrice/Cockatrice"

  Reset to defaults:
    python -m src.cli.configure --reset
        """
    )

    parser.add_argument(
        '--show',
        action='store_true',
        help='Show current configuration'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate configured paths'
    )

    parser.add_argument(
        '--set-deck-path',
        type=str,
        metavar='PATH',
        help='Set the deck path'
    )

    parser.add_argument(
        '--set-cockatrice-path',
        type=str,
        metavar='PATH',
        help='Set the Cockatrice path'
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset all settings to defaults'
    )

    args = parser.parse_args()

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    settings = SettingsManager()

    # Execute requested actions
    if args.show:
        show_settings(settings)

    if args.validate:
        if not validate_settings(settings):
            sys.exit(1)

    if args.set_deck_path:
        set_deck_path(settings, args.set_deck_path)

    if args.set_cockatrice_path:
        set_cockatrice_path(settings, args.set_cockatrice_path)

    if args.reset:
        reset_settings(settings)


if __name__ == '__main__':
    main()
