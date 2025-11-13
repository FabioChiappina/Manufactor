"""
MTG Set information and management.

Handles set name validation and conflicts with existing Magic: The Gathering sets.
"""

from typing import Optional, Dict


class CardSet:
    """Manages MTG set names and prevents conflicts with official set codes."""

    forbidden_custom_set_names: Dict[str, str] = {"ANA":"ANK"}

    @staticmethod
    def adjust_forbidden_custom_setname(
        setname: Optional[str]
    ) -> Optional[str]:
        """
        Adjust set name if it conflicts with an existing MTG set.

        Args:
            setname: The proposed set name

        Returns:
            Adjusted set name if conflict exists, otherwise original name
        """
        if setname is not None and setname.upper() in CardSet.forbidden_custom_set_names.keys():
            return CardSet.forbidden_custom_set_names[setname]
        return setname
