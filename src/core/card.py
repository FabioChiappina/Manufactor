"""
MTG Card representation and management.

This module provides the Card class which represents individual Magic: The Gathering cards
with all their properties, validation, frame selection, and JSON serialization.
"""

import os
from typing import Optional, List, Union, Dict, Any
from src.core.mana import Mana
from src.core.card_set import CardSet
from src.utils.paths import CARD_BORDERS_PATH


class Card:
    supertypes = ["token", "legendary", "basic", "snow"]
    cardtypes  = ["artifact", "enchantment", "land", "creature", "planeswalker", "instant", "sorcery", "battle"]
    basic_lands = ["plains", "island", "swamp", "mountain", "forest", "wastes"]

    rarities = ["common", "uncommon", "rare", "mythic"]

    symbols = Mana.mana_symbols + ['t', 'q']

    @staticmethod
    def from_existing_cardname(
        cardname: str
    ) -> 'Card':
        """
        Return a Card object for the input real MTG card name.

        Args:
            cardname: Name of the existing MTG card

        Returns:
            Card object representing the existing card

        Note:
            TODO - Not yet implemented
        """
        pass

    @staticmethod
    def filter_supertypes_from_cardtype(
        cardtype: str
    ) -> str:
        """
        Remove supertypes from a cardtype string, leaving only card types.

        Args:
            cardtype: The cardtype string potentially containing supertypes

        Returns:
            The cardtype string with supertypes removed
        """
        cardtype = cardtype.title()
        for supertype in Card.supertypes:
            cardtype = cardtype.replace(supertype.capitalize()+" ", "")
        return cardtype

    @staticmethod
    def get_supertype_from_cardtype(
        cardtype: str
    ) -> Optional[str]:
        """
        Extract supertypes from a cardtype string.

        Args:
            cardtype: The cardtype string potentially containing supertypes

        Returns:
            Space-separated string of supertypes, or None if no supertypes found
        """
        supertype_string = ""
        for supertype in Card.supertypes:
            if supertype.lower() in cardtype.lower():
                supertype_string += supertype.capitalize()+" "
        if len(supertype_string)==0:
            return None
        if supertype_string[-1]==" ":
            supertype_string = supertype_string[0:-1]
        return supertype_string

    def __init__(
        self,
        name: Optional[str] = None,
        artist: Optional[str] = None,
        artwork: Optional[str] = None,
        setname: Optional[str] = None,
        mana: Optional[str] = None,
        cardtype: Optional[str] = None,
        subtype: Optional[str] = None,
        power: Optional[Union[str, int]] = None,
        toughness: Optional[Union[str, int]] = None,
        rarity: Optional[Union[str, int]] = None,
        rules: Optional[str] = None,
        rules1: Optional[str] = None,
        rules2: Optional[str] = None,
        rules3: Optional[str] = None,
        rules4: Optional[str] = None,
        rules5: Optional[str] = None,
        rules6: Optional[str] = None,
        flavor: Optional[str] = None,
        special: Optional[str] = None,
        related: Optional[Union[str, List[str]]] = None,
        related_indicator: Optional[str] = None,
        colors: Optional[List[str]] = None,
        tags: Optional[Union[str, List[str]]] = None,
        complete: Union[int, bool, str] = 0,
        real: Union[int, bool, str] = 0,
        frame: Optional[str] = None,
        legendary: Union[int, bool, None] = None,
        basic: Union[int, bool, None] = None,
        snow: Union[int, bool, None] = None,
        token: Union[int, bool, None] = None
    ) -> None:
        """
        Initialize a Magic: The Gathering Card.

        Args:
            name: Card name
            artist: Artist name
            artwork: Path to artwork file
            setname: Set code/name
            mana: Mana cost string (e.g., "{2}{U}{R}")
            cardtype: Card type(s) (e.g., "Creature", "Instant"). Can include supertypes
                     for backward compatibility, or use separate supertype parameters.
            subtype: Card subtype(s) (e.g., "Human Wizard")
            power: Creature power (string or int)
            toughness: Creature toughness (string or int)
            rarity: Card rarity ("common", "uncommon", "rare", "mythic" or 0-3)
            rules: Main rules text
            rules1: First line of rules (for multi-line layouts)
            rules2: Second line of rules
            rules3: Third line of rules
            rules4: Fourth line of rules
            rules5: Fifth line of rules
            rules6: Sixth line of rules
            flavor: Flavor text
            special: Special card type ("front", "back", "transform-front", "transform-back",
                    "mdfc-front", "mdfc-back")
            related: Related card name(s) for double-faced cards
            related_indicator: Text/mana cost for opposite side indicator
            colors: List of color identities (['w', 'u', 'b', 'r', 'g'])
            tags: Tag(s) for categorization
            complete: 1 if card is complete (has image), 0 otherwise
            real: 1 if real MTG card, 0 if custom
            frame: Path to custom frame image
            legendary: True/1 if legendary, False/0 or None if not
            basic: True/1 if basic, False/0 or None if not
            snow: True/1 if snow, False/0 or None if not
            token: True/1 if token, False/0 or None if not

        Raises:
            TypeError: If any argument is not of the expected type
            ValueError: If any argument has an invalid value
        """
        if name is not None and type(name)!=str:
            raise TypeError("name input must be of type str.")
        if artist is not None and type(artist)!=str:
            raise TypeError("artist input must be of type str.")
        if artwork is not None and type(artwork)!=str:
            raise TypeError("artwork input must be of type str.")
        if setname is not None and type(setname)!=str:
            raise TypeError("setname input must be of type str.")
        if mana is not None and type(mana)!=str:
            raise TypeError("mana input must be of type str.")
        if cardtype is not None and type(cardtype)!=str:
            raise TypeError("cardtype input must be of type str.")
        if subtype is not None and type(subtype)!=str:
            raise TypeError("subtype input must be of type str.")
        if power is not None and type(power)!=str and type(power)!=int:
            raise TypeError("power input must be of type str or int.")
        elif type(power)==int:
            power = str(power)
        if toughness is not None and type(toughness)!=str and type(toughness)!=int:
            raise TypeError("toughness input must be of type str or int.")
        elif type(toughness)==int:
            toughness = str(toughness)
        if rarity is not None and type(rarity)!=str and type(rarity)!=int:
            raise TypeError("rarity input must be of type str or int.")
        elif type(rarity)==int:     
            rarity = min(rarity, 3)
            rarity = max(rarity, 0)
            rarity = Card.rarities[rarity]
        if rules is not None and type(rules)!=str:
            raise TypeError("rules input must be of type str.")
        if rules1 is not None and type(rules1)!=str:
            raise TypeError("rules1 input must be of type str.")
        if rules2 is not None and type(rules2)!=str:
            raise TypeError("rules2 input must be of type str.")
        if rules3 is not None and type(rules3)!=str:
            raise TypeError("rules3 input must be of type str.")
        if rules4 is not None and type(rules4)!=str:
            raise TypeError("rules4 input must be of type str.")
        if rules5 is not None and type(rules5)!=str:
            raise TypeError("rules5 input must be of type str.")
        if rules6 is not None and type(rules6)!=str:
            raise TypeError("rules6 input must be of type str.")
        if flavor is not None and type(flavor)!=str:
            raise TypeError("flavor input must be of type str.")
        if special is not None and type(special)!=str:
            raise TypeError("special input must be of type str.")
        if related is not None and type(related)!=str and type(related)!=list:
            raise TypeError("related input must be of type str.")
        if related_indicator is not None and type(related_indicator)!=str:
            raise TypeError("related_indicator input must be of type str.")
        if colors is not None and type(colors)!=list:
            raise TypeError("colors input must be of type list.")
        elif type(colors)==list:
            if not all([c in ['w','u','b','r','g'] for c in colors]):
                raise ValueError("Each element of colors must be in 'wubrg'.")
        if tags is not None and type(tags)!=str and type(tags)!=list:
            raise TypeError("tags input must be of type str or list.")
        elif type(tags)==str:
            tags = [tags]
        if complete is not None and type(complete)!=int and type(complete)!=bool and type(complete)!=str:
            raise TypeError("complete input must be of type int, bool, or str.")
        elif type(complete)==bool:
            complete = int(complete)
        elif type(complete)==str:
            try:
                complete = int(str)
            except:
                raise ValueError("Could not convert complete to an integer.")
        if real is not None and type(real)!=int and type(real)!=bool and type(real)!=str:
            raise TypeError("real input must be of type int, bool, or str.")
        elif type(real)==bool:
            real = int(real)
        elif type(real)==str:
            try:
                real = int(str)
            except:
                raise ValueError("Could not convert real to an integer.")
        self.name=name
        self.artist=artist
        self.artwork=artwork
        self.setname = setname if real else CardSet.adjust_forbidden_custom_setname(setname)
        self.mana = Mana.sort(mana)
        self.subtype=subtype
        self.power=power
        self.toughness=toughness
        self.rarity=rarity
        self.rules = Card.sort_rules_text_mana_symbols(rules)
        self.rules1 = Card.sort_rules_text_mana_symbols(rules1)
        self.rules2 = Card.sort_rules_text_mana_symbols(rules2)
        self.rules3 = Card.sort_rules_text_mana_symbols(rules3)
        self.rules4 = Card.sort_rules_text_mana_symbols(rules4)
        self.rules5 = Card.sort_rules_text_mana_symbols(rules5)
        self.rules6 = Card.sort_rules_text_mana_symbols(rules6)
        self.flavor=flavor
        self.special=special
        self.related=related
        self.related_indicator=related_indicator
        self.tags=tags
        self.complete=complete

        # Handle supertypes: support both old format (in cardtype string) and new format (separate fields)
        # Priority: individual fields > cardtype string parsing
        supertype_from_cardtype = Card.get_supertype_from_cardtype(cardtype)

        # Build supertype string from individual fields or cardtype string
        supertype_parts = []

        # Check individual supertype fields first (new format)
        # Only fall back to cardtype parsing if the field is None (not explicitly set)
        if legendary is not None:
            if legendary == 1 or legendary is True:
                supertype_parts.append("Legendary")
        elif supertype_from_cardtype and "legendary" in supertype_from_cardtype.lower():
            supertype_parts.append("Legendary")

        if basic is not None:
            if basic == 1 or basic is True:
                supertype_parts.append("Basic")
        elif supertype_from_cardtype and "basic" in supertype_from_cardtype.lower():
            supertype_parts.append("Basic")

        if snow is not None:
            if snow == 1 or snow is True:
                supertype_parts.append("Snow")
        elif supertype_from_cardtype and "snow" in supertype_from_cardtype.lower():
            supertype_parts.append("Snow")

        if token is not None:
            if token == 1 or token is True:
                supertype_parts.append("Token")
        elif supertype_from_cardtype and "token" in supertype_from_cardtype.lower():
            supertype_parts.append("Token")

        self.supertype = " ".join(supertype_parts) if supertype_parts else None
        self.cardtype = Card.filter_supertypes_from_cardtype(cardtype)
        self.colors = self.get_colors() if colors is None else colors
        if frame is not None and type(frame)==str and frame.endswith(".jpg"):
            if frame in os.listdir("."):
                self.frame = frame
            elif frame in os.listdir(CARD_BORDERS_PATH):
                self.frame = os.path.join(CARD_BORDERS_PATH, frame)
            else:
                self.frame = self.get_frame_filename(CARD_BORDERS_PATH)
        else:
            self.frame = self.get_frame_filename(CARD_BORDERS_PATH)

    def get_colors(
        self
    ) -> List[str]:
        """
        Get the color identity of this card.

        Returns:
            List of color codes (e.g., ['w', 'u', 'b', 'r', 'g'])
        """
        if self.is_token():
            try:
                return self.colors
            except:
                return []
        else:
            return Mana.get_colors(self.mana)

    def is_monocolored(
        self
    ) -> bool:
        """Check if this card is exactly one color."""
        return Mana.is_monocolored(self.mana)

    def is_colorless(
        self
    ) -> bool:
        """Check if this card is colorless."""
        return Mana.is_colorless(self.mana)

    def is_multicolored(
        self
    ) -> bool:
        """Check if this card is multicolored (2+ colors)."""
        return Mana.is_multicolored(self.mana)

    def is_bicolored(
        self
    ) -> bool:
        """Check if this card is exactly two colors."""
        return Mana.is_bicolored(self.mana)

    def is_tricolored(
        self
    ) -> bool:
        """Check if this card is exactly three colors."""
        return Mana.is_tricolored(self.mana)

    def is_quadcolored(
        self
    ) -> bool:
        """Check if this card is exactly four colors."""
        return Mana.is_quadcolored(self.mana)

    def is_pentacolored(
        self
    ) -> bool:
        """Check if this card is all five colors."""
        return Mana.is_pentacolored(self.mana)
    def is_white(
        self
    ) -> bool:
        """Check if this card contains white."""
        if self.is_token():
            return 'w' in self.colors
        else:
            return Mana.is_white(self.mana)

    def is_blue(
        self
    ) -> bool:
        """Check if this card contains blue."""
        if self.is_token():
            return 'u' in self.colors
        else:
            return Mana.is_blue(self.mana)

    def is_black(
        self
    ) -> bool:
        """Check if this card contains black."""
        if self.is_token():
            return 'b' in self.colors
        else:
            return Mana.is_black(self.mana)

    def is_red(
        self
    ) -> bool:
        """Check if this card contains red."""
        if self.is_token():
            return 'r' in self.colors
        else:
            return Mana.is_red(self.mana)

    def is_green(
        self
    ) -> bool:
        """Check if this card contains green."""
        if self.is_token():
            return 'g' in self.colors
        else:
            return Mana.is_green(self.mana)

    def is_azorius(self) -> bool:
        """Check if this card is Azorius colors (white/blue)."""
        return Mana.is_azorius(self.mana)

    def is_orzhov(self) -> bool:
        """Check if this card is Orzhov colors (white/black)."""
        return Mana.is_orzhov(self.mana)

    def is_boros(self) -> bool:
        """Check if this card is Boros colors (red/white)."""
        return Mana.is_boros(self.mana)

    def is_selesnya(self) -> bool:
        """Check if this card is Selesnya colors (green/white)."""
        return Mana.is_selesnya(self.mana)

    def is_dimir(self) -> bool:
        """Check if this card is Dimir colors (blue/black)."""
        return Mana.is_dimir(self.mana)

    def is_izzet(self) -> bool:
        """Check if this card is Izzet colors (blue/red)."""
        return Mana.is_izzet(self.mana)

    def is_simic(self) -> bool:
        """Check if this card is Simic colors (green/blue)."""
        return Mana.is_simic(self.mana)

    def is_rakdos(self) -> bool:
        """Check if this card is Rakdos colors (black/red)."""
        return Mana.is_rakdos(self.mana)

    def is_golgari(self) -> bool:
        """Check if this card is Golgari colors (black/green)."""
        return Mana.is_golgari(self.mana)

    def is_gruul(self) -> bool:
        """Check if this card is Gruul colors (red/green)."""
        return Mana.is_gruul(self.mana)

    def is_abzan(self) -> bool:
        """Check if this card is Abzan colors (white/black/green)."""
        return Mana.is_abzan(self.mana)

    def is_bant(self) -> bool:
        """Check if this card is Bant colors (green/white/blue)."""
        return Mana.is_bant(self.mana)

    def is_esper(self) -> bool:
        """Check if this card is Esper colors (white/blue/black)."""
        return Mana.is_esper(self.mana)

    def is_grixis(self) -> bool:
        """Check if this card is Grixis colors (blue/black/red)."""
        return Mana.is_grixis(self.mana)

    def is_jeskai(self) -> bool:
        """Check if this card is Jeskai colors (blue/red/white)."""
        return Mana.is_jeskai(self.mana)

    def is_jund(self) -> bool:
        """Check if this card is Jund colors (black/red/green)."""
        return Mana.is_jund(self.mana)

    def is_mardu(self) -> bool:
        """Check if this card is Mardu colors (red/white/black)."""
        return Mana.is_mardu(self.mana)

    def is_naya(self) -> bool:
        """Check if this card is Naya colors (red/green/white)."""
        return Mana.is_naya(self.mana)

    def is_sultai(self) -> bool:
        """Check if this card is Sultai colors (black/green/blue)."""
        return Mana.is_sultai(self.mana)

    def is_temur(self) -> bool:
        """Check if this card is Temur colors (green/blue/red)."""
        return Mana.is_temur(self.mana)

    def is_glint(self) -> bool:
        """Check if this card is Glint colors (blue/black/red/green)."""
        return Mana.is_glint(self.mana)

    def is_dune(self) -> bool:
        """Check if this card is Dune colors (white/black/red/green)."""
        return Mana.is_dune(self.mana)

    def is_ink(self) -> bool:
        """Check if this card is Ink colors (white/blue/red/green)."""
        return Mana.is_ink(self.mana)

    def is_witch(self) -> bool:
        """Check if this card is Witch colors (white/blue/black/green)."""
        return Mana.is_witch(self.mana)

    def is_yore(self) -> bool:
        """Check if this card is Yore colors (white/blue/black/red)."""
        return Mana.is_yore(self.mana)

    def get_colors_produced_by_land(
        self
    ) -> List[str]:
        """
        Get colors of mana produced by this land.

        Only considers colors the land itself produces, not colors in ability costs.

        Returns:
            List of color codes produced by this land
        """
        if not self.is_land():
            return []
        if self.rules is None and self.rules1 is not None:
            rules = self.rules1
            for this_rules in [self.rules2, self.rules3, self.rules4, self.rules5, self.rules6]:
                if this_rules is None:
                    break
                rules += "\n"+this_rules
        elif self.rules is not None:
            rules = self.rules
        else:
            return []
        return Mana.get_colors_produced_by_land(rules)

    def get_colors_in_rules(
        self
    ) -> List[str]:
        """
        Get colors of mana that appear in this card's rules text.

        Returns:
            List of color codes found in the rules text
        """
        if self.rules is None and self.rules1 is not None:
            rules = self.rules1
            for this_rules in [self.rules2, self.rules3, self.rules4, self.rules5, self.rules6]:
                if this_rules is None:
                    break
                rules += "\n"+this_rules
        elif self.rules is not None:
            rules = self.rules
        else:
            return []
        return Mana.get_colors_in_text(rules)

    def is_land(self) -> bool:
        """Check if this card is a land."""
        return "land" in self.cardtype.lower()

    def is_creature(self) -> bool:
        """Check if this card is a creature."""
        return "creature" in self.cardtype.lower()

    def is_artifact(self) -> bool:
        """Check if this card is an artifact."""
        return "artifact" in self.cardtype.lower()

    def is_enchantment(self) -> bool:
        """Check if this card is an enchantment."""
        return "enchantment" in self.cardtype.lower()

    def is_planeswalker(self) -> bool:
        """Check if this card is a planeswalker."""
        return "planeswalker" in self.cardtype.lower()

    def is_instant(self) -> bool:
        """Check if this card is an instant."""
        return "instant" in self.cardtype.lower()

    def is_sorcery(self) -> bool:
        """Check if this card is a sorcery."""
        return "sorcery" in self.cardtype.lower()

    def is_battle(self) -> bool:
        """Check if this card is a battle."""
        return "battle" in self.cardtype.lower()

    def is_saga(self) -> bool:
        """Check if this card is a Saga."""
        return False if self.subtype is None else (self.is_enchantment() and "saga" in self.subtype.lower())

    def is_vehicle(self) -> bool:
        """Check if this card is a Vehicle."""
        return False if self.subtype is None else (self.is_artifact() and "vehicle" in self.subtype.lower())

    def is_token(self) -> bool:
        """Check if this card is a token."""
        return False if self.supertype is None else ("token" in self.supertype.lower())

    def is_legendary(self) -> bool:
        """Check if this card is legendary."""
        return False if self.supertype is None else ("legendary" in self.supertype.lower())

    def is_snow(self) -> bool:
        """Check if this card is a snow permanent."""
        return False if self.supertype is None else ("snow" in self.supertype.lower())

    def is_basic(self) -> bool:
        """Check if this card is a basic land."""
        return False if self.supertype is None else ("basic" in self.supertype.lower())

    def is_transform(self) -> bool:
        """Check if this card is a transform double-faced card."""
        special = self.special.lower() if type(self.special)==str else None
        return special=="front" or special=="back" or special=="transform-front" or special=="transform-back"

    def is_mdfc(self) -> bool:
        """Check if this card is a modal double-faced card."""
        special = self.special.lower() if type(self.special)==str else ""
        return "mdfc" in special

    def is_spell(self) -> bool:
        """Check if this card is a spell (non-land)."""
        return (not self.is_land()) and (self.is_creature() or self.is_artifact() or self.is_enchantment() or self.is_planeswalker() or self.is_instant() or self.is_sorcery() or self.is_battle())

    @staticmethod
    def sort_rules_text_mana_symbols(
        rules: Optional[str]
    ) -> Optional[str]:
        """
        Sort mana symbol groups in rules text by WUBRG order.

        Args:
            rules: Rules text containing mana symbols

        Returns:
            Rules text with sorted mana symbols, or None if input is None
        """
        if rules is None or type(rules)!=str:
            return None
        rebuilt_rules_text = ""
        found_open_bracket = None
        for index, character in enumerate(rules):
            if character=="{" and found_open_bracket is None:
                found_open_bracket = index
            if (index>0) and (rules[index-1]=="}") and (found_open_bracket is not None) and (character!="{"):
                rebuilt_rules_text += Mana.sort(rules[found_open_bracket:index]) # replace the last found mana symbol grouping with sorted
                found_open_bracket = None
            if found_open_bracket is None:
                rebuilt_rules_text += character
        if found_open_bracket is not None: # Push one more series of mana symbols to the rules text
            rebuilt_rules_text += Mana.sort(rules[found_open_bracket:])
        return rebuilt_rules_text

    def get_type_line(
        self
    ) -> str:
        """
        Get the complete type line for this card.

        Combines supertype(s), card type(s), and subtype(s) into a single string.

        Returns:
            Complete type line (e.g., "Legendary Creature — Human Wizard")
        """
        type_line = ""
        if type(self.supertype)==str:
            type_line += self.supertype.title() + " "
        if type(self.cardtype)==str:
            type_line += self.cardtype.title()
        if type(self.subtype)==str and len(self.subtype)>0:
            type_line += " — " + self.subtype.title()
        return type_line

    def get_mana_symbols(
        self
    ) -> Dict[str, int]:
        """
        Get mana symbols in this card's mana cost with their counts.

        Returns:
            Dictionary mapping mana symbols to their counts
            (e.g., {'u': 2, 'r': 1} for {U}{U}{R})

        Note:
            Generic mana symbols supported up to {20}
        """
        return Mana.get_mana_symbols(self.mana)

    def get_mana_value(
        self
    ) -> int:
        """
        Get the mana value (converted mana cost) of this card.

        Returns:
            Integer mana value of the card
        """
        return Mana.get_mana_value(self.mana)

    def get_frame_filename(
        self,
        card_borders_folder: Optional[str] = None
    ) -> str:
        """
        Get the filename of the appropriate card frame for this card.

        Determines the correct frame based on card colors, types, and special properties.

        Args:
            card_borders_folder: Optional path to card borders folder

        Returns:
            Frame filename (or full path if card_borders_folder provided)

        Raises:
            ValueError: If card type is not supported (planeswalkers, battles)
            Exception: If no matching frame is found
        """
        if self.mana is None or len(self.mana)==0:
            if self.is_land():
                colors = self.get_colors_produced_by_land()
            elif not self.is_artifact():
                colors = self.get_colors_in_rules()
            else:
                colors = ""
            if (len(colors)==0) and (self.special is not None) and ("transform" in self.special) and (self.related_indicator is not None) and len(self.related_indicator)>0:
                colors = Mana.get_colors_in_text(self.related_indicator)
            if len(colors)==0:
                filename = "c"
            elif len(colors)==1:
                filename = colors[0]
            elif len(colors)==2:
                filename = Mana.sort("{"+colors[0].lower().strip()+"}" + "{"+colors[1].lower().strip()+"}").replace("{","").replace("}","")
            elif len(colors)>=3:
                filename = "m"
        elif self.is_tricolored() or self.is_quadcolored() or self.is_pentacolored():
            filename = "m"
        elif self.is_bicolored():
            if self.is_azorius():
                filename = "wu"
            elif self.is_orzhov():
                filename = "wb"
            elif self.is_boros():
                filename = "rw"
            elif self.is_selesnya():
                filename = "gw"
            elif self.is_dimir():
                filename = "ub"
            elif self.is_izzet():
                filename = "ur"
            elif self.is_simic():
                filename = "gu"
            elif self.is_rakdos():
                filename = "br"
            elif self.is_golgari():
                filename = "bg"
            elif self.is_gruul():
                filename = "rg"
        elif self.is_monocolored():
            filename = self.colors[0]
        elif self.is_colorless():
            filename = "c"
        filename += "_"
        # Manage special frames: (TODO -- add support for other special frames)
        if self.is_transform():
            special="transform"
            if "front" in self.special.lower():
                special += "-front"
            elif "back" in self.special.lower():
                special += "-back"
            available_frames = ["creature", "noncreature", "artifact-creature", "artifact-noncreature", "land"]
        elif self.is_mdfc():
            special="mdfc"
            if "front" in self.special.lower():
                special += "-front"
            elif "back" in self.special.lower():
                special += "-back"
            available_frames = ["creature", "noncreature", "artifact-creature", "artifact-noncreature", "land"]
        elif self.is_token():
            special="token"
            available_frames = ["creature", "noncreature", "artifact-creature", "artifact-noncreature"]
        else:
            special=None
            available_frames = ["creature", "noncreature", "artifact-creature", "artifact-noncreature", "land", "enchantment-artifact-creature", "enchantment-artifact-noncreature", "enchantment-creature", "enchantment-land"]
        if special is not None:
            filename += special+"_"
        # Manage alternative frames (sagas, planeswalkers, battles, etc.): 
        if self.is_saga():
            filename += "saga"
        elif self.is_vehicle():
            filename += "artifact-vehicle"
        elif self.is_planeswalker(): # TODO -- add support for planeswalkers
            raise ValueError("Planeswalkers are not currently supported.")
        elif self.is_battle(): # TODO -- add support for battles
            raise ValueError("Battles are not currently supported.")
        # TODO -- add support for adventures/omens (subspells)
        else:
            frame = ""
            if self.is_enchantment() and any([f.startswith("enchantment") for f in available_frames]):
                if self.is_artifact() and self.is_creature():
                    frame = "enchantment-artifact-creature"
                elif self.is_artifact():
                    frame = "enchantment-artifact-noncreature"
                elif self.is_land():
                    frame = "enchantment-land"
                elif self.is_creature():
                    frame = "enchantment-creature"
                else:
                    frame = "noncreature"
            elif self.is_artifact() and any([f.startswith("artifact") for f in available_frames]):
                if self.is_creature():
                    frame = "artifact-creature"
                elif self.is_land() and "artifact-land" in available_frames:
                    frame = "artifact-land"
                else:
                    frame = "artifact-noncreature"
            elif self.is_land() and "land" in available_frames:
                frame = "land"
            elif self.is_creature():
                frame = "creature"
            else:
                frame = "noncreature"
            if frame in available_frames:
                filename += frame
            else:
                raise Exception("frame name not found.")
        if self.is_legendary() and not self.is_saga():
            filename += "_legendary"
        filename += ".jpg"
        if card_borders_folder is not None:
            filename = os.path.join(card_borders_folder, filename)
        return filename

    def get_tokens(
        self
    ) -> tuple[List[Dict[str, Any]], List[str]]:
        """
        Extract token definitions from this card's rules text.

        Parses all rules text fields (rules, rules1-6) to identify tokens created
        by this card.

        Returns:
            Tuple of (specialized_tokens, common_tokens) where:
            - specialized_tokens: List of dicts with token properties (name, cardtype,
              subtype, power, toughness, rules, frame, complete, related)
            - common_tokens: List of common token names (Treasure, Clue, Food, etc.)
        """
        from src.token_generation.token_parser import parse_tokens_from_rules_text
        st0, ct0 = parse_tokens_from_rules_text(self.rules, card_name=self.name, complete=self.complete, Card=Card)
        st1, ct1 = parse_tokens_from_rules_text(self.rules1, card_name=self.name, complete=self.complete, Card=Card)
        st2, ct2 = parse_tokens_from_rules_text(self.rules2, card_name=self.name, complete=self.complete, Card=Card)
        st3, ct3 = parse_tokens_from_rules_text(self.rules3, card_name=self.name, complete=self.complete, Card=Card)
        st4, ct4 = parse_tokens_from_rules_text(self.rules4, card_name=self.name, complete=self.complete, Card=Card)
        st5, ct5 = parse_tokens_from_rules_text(self.rules5, card_name=self.name, complete=self.complete, Card=Card)
        st6, ct6 = parse_tokens_from_rules_text(self.rules6, card_name=self.name, complete=self.complete, Card=Card)
        return (st0+st1+st2+st3+st4+st5+st6), (ct0+ct1+ct2+ct3+ct4+ct5+ct6)
