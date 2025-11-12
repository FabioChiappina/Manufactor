"""
MTG Set information and management.

Handles set name validation and conflicts with existing Magic: The Gathering sets.
"""


class CardSet:
    """Manages MTG set names and prevents conflicts with official set codes."""

    # Whenever a new custom set is created with a default setname conflicting with an existing setname, add that original and replacement setname as a key-value pair to the dictionary below.
    forbidden_custom_set_names = {"ANA":"ANK"}

    # Adjusts the input setname if the name is reserved for an existing MTG set.
    def adjust_forbidden_custom_setname(setname):
        if setname is not None and setname.upper() in CardSet.forbidden_custom_set_names.keys():
            return CardSet.forbidden_custom_set_names[setname]
        return setname
