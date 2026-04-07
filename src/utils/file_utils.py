"""
File system utilities for finding and managing card image files.
"""

import os
import re
import unicodedata
from typing import List


_APOSTROPHE_TABLE = str.maketrans({'\u2019': "'", '\u2018': "'", '\u02bc': "'"})


def _norm(s: str) -> str:
    """NFC-normalize and collapse apostrophe variants to plain ASCII apostrophe."""
    return unicodedata.normalize('NFC', s).translate(_APOSTROPHE_TABLE)


def find_cards_with_card_name(
    cardname: str,
    search_path: str
) -> List[str]:
    """
    Find all card image files matching the given card name.

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
    norm_name = _norm(cardname)
    pattern1 = re.compile(rf"^{re.escape(norm_name)}\.jpg$")
    pattern2 = re.compile(rf"^{re.escape(norm_name)}_\d+\.jpg$")
    for file in os.listdir(search_path):
        if pattern1.match(_norm(file)) or pattern2.match(_norm(file)):
            matching_files.append(file)
    return matching_files
