"""
MTG Card representation and management.

This module provides the Card class which represents individual Magic: The Gathering cards
with all their properties, validation, frame selection, and JSON serialization.
"""

import os
import json
from src.core.mana import Mana
from src.core.card_set import CardSet
from src.utils.paths import CARD_BORDERS_PATH


class Card:
    supertypes = ["token", "legendary", "basic", "snow"]
    cardtypes  = ["artifact", "enchantment", "land", "creature", "planeswalker", "instant", "sorcery", "battle"]
    basic_lands = ["plains", "island", "swamp", "mountain", "forest", "wastes"]

    rarities = ["common", "uncommon", "rare", "mythic"]

    symbols = Mana.mana_symbols + ['t', 'q']

    # TODO -- return a Card object for the input real MTG card name
    def from_existing_cardname(cardname):
        pass

    # From the input cardtype string, removes any types that are super types, not card types.
    def filter_supertypes_from_cardtype(cardtype):
        cardtype = cardtype.title()
        for supertype in Card.supertypes:
            cardtype = cardtype.replace(supertype.capitalize()+" ", "")
        return cardtype
    # From the input cardtype string, returns any types that are super types, not card types.
    def get_supertype_from_cardtype(cardtype):
        supertype_string = ""
        for supertype in Card.supertypes:
            if supertype.lower() in cardtype.lower():
                supertype_string += supertype.capitalize()+" "
        if len(supertype_string)==0:
            return None
        if supertype_string[-1]==" ":
            supertype_string = supertype_string[0:-1]
        return supertype_string

    # special: front or transform-front, back or transform-back, mdfc-front, mdfc-back (later add adventure, ...)
    # related_indicator: Text/mana cost to be written on an indicator of the opposite side of the card. If omitted, default text/mana value is computed from the card's "related" field if present and if special is mdfc/transform. Otherwise, indicator is omitted.
    # real: 1 if a real mtg card, 0 if custom
    def __init__(self, name=None, artist=None, artwork=None, setname=None, mana=None, cardtype=None, subtype=None, power=None, toughness=None, rarity=None, rules=None, rules1=None, rules2=None, rules3=None, rules4=None, rules5=None, rules6=None, flavor=None, special=None, related=None, related_indicator=None, colors=None, tags=None, complete=0, real=0, frame=None):
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
        self.supertype=Card.get_supertype_from_cardtype(cardtype)
        self.cardtype=Card.filter_supertypes_from_cardtype(cardtype)
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

    def get_colors(self):
        if self.is_token():
            try:
                return self.colors
            except:
                return []
        else:
            return Mana.get_colors(self.mana)
    def is_monocolored(self):
        return Mana.is_monocolored(self.mana)
    def is_colorless(self):
        return Mana.is_colorless(self.mana)
    def is_multicolored(self):
        return Mana.is_multicolored(self.mana)
    def is_bicolored(self):
        return Mana.is_bicolored(self.mana)
    def is_tricolored(self):
        return Mana.is_tricolored(self.mana)
    def is_quadcolored(self):
        return Mana.is_quadcolored(self.mana)
    def is_pentacolored(self):
        return Mana.is_pentacolored(self.mana)
    def is_white(self):
        if self.is_token():
            return 'w' in self.colors
        else:
            return Mana.is_white(self.mana)
    def is_blue(self):
        if self.is_token():
            return 'u' in self.colors
        else:
            return Mana.is_blue(self.mana)
    def is_black(self):
        if self.is_token():
            return 'b' in self.colors
        else:
            return Mana.is_black(self.mana)
    def is_red(self):
        if self.is_token():
            return 'r' in self.colors
        else:
            return Mana.is_red(self.mana)
    def is_green(self):
        if self.is_token():
            return 'g' in self.colors
        else:
            return Mana.is_green(self.mana)
    def is_azorius(self):
        return Mana.is_azorius(self.mana)
    def is_orzhov(self):
        return Mana.is_orzhov(self.mana)
    def is_boros(self):
        return Mana.is_boros(self.mana)
    def is_selesnya(self):
        return Mana.is_selesnya(self.mana)
    def is_dimir(self):
        return Mana.is_dimir(self.mana)
    def is_izzet(self):
        return Mana.is_izzet(self.mana)
    def is_simic(self):
        return Mana.is_simic(self.mana)
    def is_rakdos(self):
        return Mana.is_rakdos(self.mana)
    def is_golgari(self):
        return Mana.is_golgari(self.mana)
    def is_gruul(self):
        return Mana.is_gruul(self.mana)
    def is_abzan(self):
        return Mana.is_abzan(self.mana)
    def is_bant(self):
        return Mana.is_bant(self.mana)
    def is_esper(self):
        return Mana.is_esper(self.mana)
    def is_grixis(self):
        return Mana.is_grixis(self.mana)
    def is_jeskai(self):
        return Mana.is_jeskai(self.mana)
    def is_jund(self):
        return Mana.is_jund(self.mana)
    def is_mardu(self):
        return Mana.is_mardu(self.mana)
    def is_naya(self):
        return Mana.is_naya(self.mana)
    def is_sultai(self):
        return Mana.is_sultai(self.mana)
    def is_temur(self):
        return Mana.is_temur(self.mana)
    def is_glint(self):
        return Mana.is_glint(self.mana)
    def is_dune(self):
        return Mana.is_dune(self.mana)
    def is_ink(self):
        return Mana.is_ink(self.mana)
    def is_witch(self):
        return Mana.is_witch(self.mana)
    def is_yore(self):
        return Mana.is_yore(self.mana)
    
    # Returns a list with each color of mana (among WUBRG) that the card produces, if this card is a land.
    # Colors of mana in the costs of abilities are not considered -- only colors that the land itself produces.
    def get_colors_produced_by_land(self):
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
    
    # Returns a list with each color of mana (among WUBRG) in the rules text of the card.
    def get_colors_in_rules(self):
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
    
    def is_land(self):
        return "land" in self.cardtype.lower()
    def is_creature(self):
        return "creature" in self.cardtype.lower()
    def is_artifact(self):
        return "artifact" in self.cardtype.lower()
    def is_enchantment(self):
        return "enchantment" in self.cardtype.lower()
    def is_planeswalker(self):
        return "planeswalker" in self.cardtype.lower()
    def is_instant(self):
        return "instant" in self.cardtype.lower()
    def is_sorcery(self):
        return "sorcery" in self.cardtype.lower()
    def is_battle(self):
        return "battle" in self.cardtype.lower()

    def is_saga(self):
        return False if self.subtype is None else (self.is_enchantment() and "saga" in self.subtype.lower())
    def is_vehicle(self):
        return False if self.subtype is None else (self.is_artifact() and "vehicle" in self.subtype.lower())

    def is_token(self):
        return False if self.supertype is None else ("token" in self.supertype.lower())
    def is_legendary(self):
        return False if self.supertype is None else ("legendary" in self.supertype.lower())
    def is_snow(self):
        return False if self.supertype is None else ("snow" in self.supertype.lower())
    def is_basic(self):
        return False if self.supertype is None else ("basic" in self.supertype.lower())

    def is_transform(self):
        special = self.special.lower() if type(self.special)==str else None
        return special=="front" or special=="back" or special=="transform-front" or special=="transform-back"
    def is_mdfc(self):
        special = self.special.lower() if type(self.special)==str else ""
        return "mdfc" in special
    
    def is_spell(self):
        return (not self.is_land()) and (self.is_creature() or self.is_artifact() or self.is_enchantment() or self.is_planeswalker() or self.is_instant() or self.is_sorcery() or self.is_battle())

    # Sorts any groups of mana symbols by wrap-around WUBRG order.
    def sort_rules_text_mana_symbols(rules):
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

    # Returns the complete line (string) giving a card's supertype(s), card type(s), and subtype(s).
    def get_type_line(self):
        type_line = ""
        if type(self.supertype)==str:
            type_line += self.supertype.title() + " "
        if type(self.cardtype)==str:
            type_line += self.cardtype.title()
        if type(self.subtype)==str and len(self.subtype)>0:
            type_line += " — " + self.subtype.title()
        return type_line

    # Returns a dictionary where keys are mana symbols present in the card's mana cost, and values are counts for each of those mana symbols.
    # Note that generic mana symbols are supported only up until {20}. 
    def get_mana_symbols(self):
        return Mana.get_mana_symbols(self.mana)

    # Returns the integer mana value (converted mana cost) of the input card.
    def get_mana_value(self):
        return Mana.get_mana_value(self.mana)

    # Returns the name of the file containing the appropriate frame for this card
    def get_frame_filename(self, card_borders_folder=None):
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
        # TODO -- add support for adventures
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
    
    def get_tokens(self):
        st0, ct0 = Card.get_tokens_from_rules_text(self.rules,  card_name=self.name, complete=self.complete)
        st1, ct1 = Card.get_tokens_from_rules_text(self.rules1, card_name=self.name, complete=self.complete)
        st2, ct2 = Card.get_tokens_from_rules_text(self.rules2, card_name=self.name, complete=self.complete)
        st3, ct3 = Card.get_tokens_from_rules_text(self.rules3, card_name=self.name, complete=self.complete)
        st4, ct4 = Card.get_tokens_from_rules_text(self.rules4, card_name=self.name, complete=self.complete)
        st5, ct5 = Card.get_tokens_from_rules_text(self.rules5, card_name=self.name, complete=self.complete)
        st6, ct6 = Card.get_tokens_from_rules_text(self.rules6, card_name=self.name, complete=self.complete)
        return (st0+st1+st2+st3+st4+st5+st6), (ct0+ct1+ct2+ct3+ct4+ct5+ct6)

    # complete - 1 if the token is already complete and shouldn't have its image recreated, 0 otherwise
    # card_name - If not None and not empty, will be set as related to all tokens found
    # Outputs:
    #           specialized_tokens -- A list of tokens in the rules text, excluding a small set of commonly made tokens with shorthand names. This is a list of dictionaries, where each dictionary gives the properties of a single token.
    #           common_tokens      -- A list of common tokens with shorthand names listed in the rules text. This is a list of strings, where each string is a name of a common token.
