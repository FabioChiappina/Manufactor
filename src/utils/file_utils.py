"""
File system utilities for finding and managing card image files.
"""

import os
import re
import unicodedata


def find_cards_with_card_name(cardname, search_path):
    """
    Returns a list of all card image files matching the given card name.

    Finds files with names like:
    - <cardname>.jpg
    - <cardname>_<number>.jpg (for multiple artworks)

    Args:
        cardname: Name of the card to search for
        search_path: Directory to search in

    Returns:
        List of matching filenames
    """
    matching_files = []
    pattern1 = re.compile(rf"^{re.escape(unicodedata.normalize('NFC', cardname))}\.jpg$")
    pattern2 = re.compile(rf"^{re.escape(unicodedata.normalize('NFC', cardname))}_\d+\.jpg$")
    for file in os.listdir(search_path):
        if pattern1.match(unicodedata.normalize('NFC', file)) or pattern2.match(unicodedata.normalize('NFC', file)):
            matching_files.append(unicodedata.normalize('NFC', file))
    return matching_files
