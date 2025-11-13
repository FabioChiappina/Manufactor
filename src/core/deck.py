"""
MTG Deck management and statistics.

This module provides the Deck class which manages collections of Card objects,
calculates deck statistics, and handles JSON import/export.
"""

import os
import json
from typing import List, Dict, Optional, Any, Tuple
from src.core.card import Card
from src.core.card_set import CardSet
from src.core.mana import Mana
from src.utils.paths import DECK_PATH


class Deck:
    """
    Manages a collection of MTG cards with deck statistics and analysis.

    Handles deck loading from JSON, statistics calculation, color distribution,
    mana curve analysis, and token generation.
    """

    @staticmethod
    def from_json(
        deck_json_filepath: str,
        setname: str = "UNK",
        deck_name: Optional[str] = None
    ) -> 'Deck':
        """
        Load a deck from a JSON file.

        Args:
            deck_json_filepath: Path to the JSON file containing deck data
            setname: Set code for cards (default: "UNK")
            deck_name: Name for the deck (default: derived from filepath)

        Returns:
            Deck object loaded from the JSON file

        Raises:
            FileNotFoundError: If deck_json_filepath doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        f = open(deck_json_filepath)
        card_dict = json.load(f)
        basics_dict = {}
        common_tokens = []
        tags = []
        for keyname, card in card_dict.items():
            if keyname.lower() == "_basics":
                basics_dict = card
                continue
            if keyname.lower() == "_common_tokens":
                common_tokens = card
                continue
            if "artist" not in card.keys():
                card["artist"]=None
            if "artwork" not in card.keys():
                card["artwork"]=None
            if "setname" not in card.keys():
                card["setname"]=setname
            if "mana" not in card.keys():
                card["mana"]=None
            if "cardtype" not in card.keys():
                card["cardtype"]=None
            if "subtype" not in card.keys():
                card["subtype"]=None
            if "power" not in card.keys():
                card["power"]=None
            if "toughness" not in card.keys():
                card["toughness"]=None
            if "rarity" not in card.keys():
                card["rarity"]=None
            if "rules" not in card.keys():
                card["rules"]=None
            if "rules1" not in card.keys():
                card["rules1"]=None
            if "rules2" not in card.keys():
                card["rules2"]=None
            if "rules3" not in card.keys():
                card["rules3"]=None
            if "rules4" not in card.keys():
                card["rules4"]=None            
            if "rules5" not in card.keys():
                card["rules5"]=None            
            if "rules6" not in card.keys():
                card["rules6"]=None
            if "flavor" not in card.keys():
                card["flavor"]=None
            if "special" not in card.keys(): 
                card["special"]=None
            if "related_indicator" not in card.keys():
                card["related_indicator"]=None
            if "related" not in card.keys():
                card["related"]=None
            elif (card["special"] is not None) and (("mdfc" in card["special"].lower()) or ("transform" in card["special"].lower())) and (card["related_indicator"] is None):
                related_name, related_mana = "", ""
                # TODO -- this land stuff isn't super accurate, since the back side could have something other than {t}: Add x. Really it should read in the rules text and decide what to show.
                for keyname2, card2 in card_dict.items():
                    if keyname2.lower() == "_basics":
                        continue
                    if card2["name"] == card["related"]:
                        related_name = card2["name"] if "name" in card2.keys() else ""
                        if ("mana" not in card2.keys()) or len(card2["mana"])==0:
                            if "land" in card2["cardtype"].lower():
                                related_colors = Mana.get_colors_produced_by_land(card2["rules"])
                                related_mana = "{t}: Add "
                                for ci, c in enumerate(related_colors):
                                    related_mana += "{"+c+"}"
                                    if (ci==0) and len(related_colors)==2:
                                        related_mana += " or "
                                    elif len(related_colors)==3 and (ci == 0):
                                        related_mana += ", "
                                    elif len(related_colors)==3 and (ci == 1):
                                        related_mana += ", or "
                                related_mana += "."
                            else:
                                related_mana = ""
                        else:
                            related_mana = card2["mana"]
                        break
                card["related_indicator"]=related_name+" "+related_mana
            if "colors" not in card.keys():
                card["colors"]=None
            if "tags" not in card.keys():
                card["tags"]=None
            if "complete" not in card.keys():
                card["complete"]=0
            if "real" not in card.keys():
                card["real"]=0
            if card["tags"] is not None:
                for tag in card["tags"]:
                    if tag not in tags:
                        tags.append(tag)
            if "frame" not in card.keys():
                card["frame"]=None
            # Handle new supertype fields (default to None if not present)
            if "legendary" not in card.keys():
                card["legendary"]=None
            if "basic" not in card.keys():
                card["basic"]=None
            if "snow" not in card.keys():
                card["snow"]=None
            if "token" not in card.keys():
                card["token"]=None
        cards = [Card(name=card["name"],
                      artist=card["artist"],
                      artwork=card["artwork"],
                      setname=card["setname"],
                      mana=card["mana"],
                      cardtype=card["cardtype"],
                      subtype=card["subtype"],
                      power=card["power"],
                      toughness=card["toughness"],
                      rarity=card["rarity"],
                      rules=card["rules"],
                      rules1=card["rules1"],
                      rules2=card["rules2"],
                      rules3=card["rules3"],
                      rules4=card["rules4"],
                      rules5=card["rules5"],
                      rules6=card["rules6"],
                      flavor=card["flavor"],
                      special=card["special"],
                      related=card["related"],
                      related_indicator=card["related_indicator"],
                      colors=card["colors"],
                      tags=card["tags"],
                      complete=card["complete"],
                      real=card["real"],
                      frame=card["frame"],
                      legendary=card["legendary"],
                      basic=card["basic"],
                      snow=card["snow"],
                      token=card["token"])
                  for keyname, card in card_dict.items() if (keyname.lower() != "_basics") and (keyname.lower() != "_common_tokens")]
        deck_name = os.path.basename(deck_json_filepath).replace(".json","") if deck_name is None else deck_name
        return Deck(cards=cards, name=deck_name, tags=tags, basics_dict=basics_dict, common_tokens=common_tokens)

    @staticmethod
    def from_deck_folder(
        deck_folder: str
    ) -> 'Deck':
        """
        Load a deck from a folder containing a deck JSON file.

        Args:
            deck_folder: Path to the deck folder

        Returns:
            Deck object loaded from the folder's JSON file

        Raises:
            ValueError: If deck folder doesn't exist
        """
        setname = (deck_folder.lower().replace("the ",""))[0:3].upper()
        setname = CardSet.adjust_forbidden_custom_setname(setname)
        deck_folder = ' '.join(word[0].upper() + word[1:] for word in deck_folder.split())
        if not os.path.isdir(deck_folder):
            raise ValueError(f"The input deck folder ({deck_folder}) does not exist. Ensure a folder exists of the input name in the path defined by DECK_PATH in paths.py.")
        deck_json_filepath = os.path.join(deck_folder, (os.path.basename(deck_folder).replace(" ", "_") + ".json"))
        return Deck.from_json(deck_json_filepath, setname=setname) # , deck_name=deck_folder

    def __init__(
        self,
        cards: List[Card] = [],
        name: str = "Unknown",
        tags: List[str] = [],
        basics_dict: Dict[str, Any] = {},
        common_tokens: List[str] = []
    ) -> None:
        """
        Initialize a Deck.

        Args:
            cards: List of Card objects in the deck
            name: Name of the deck
            tags: List of tags for categorization
            basics_dict: Dictionary of basic land information
            common_tokens: List of common token names created by cards

        Raises:
            TypeError: If cards contains non-Card objects or name is not a string
        """
        if any([type(c)!=Card for c in cards]):
            raise TypeError("All inputs must be of type Card.")
        if type(name)!=str:
            raise TypeError("Input deck name must be a string (str).")
        self.cards = cards
        self.name = name
        self.tags = tags
        self.basics_dict = basics_dict
        self.common_tokens = common_tokens

    def count_spells(
        self
    ) -> int:
        """
        Count the number of spells (non-land cards) in the deck.

        Returns:
            Number of spell cards
        """
        return sum([card.is_spell() for card in self.cards])

    def count_lands(
        self
    ) -> int:
        """
        Count the number of lands in the deck.

        Returns:
            Number of land cards
        """
        return sum([not card.is_spell() for card in self.cards])

    def get_cardtypes(
        self,
        count_backs: bool = False,
        count_tokens: bool = False
    ) -> Dict[str, int]:
        """
        Get counts of each card type in the deck.

        Args:
            count_backs: Whether to count back faces of double-faced cards
            count_tokens: Whether to count token cards

        Returns:
            Dictionary mapping card types to their counts
        """
        cardtypes_dict = {c.capitalize():0 for c in Card.cardtypes}
        for card in self.cards:
            if not count_tokens and card.is_token():
                continue
            if not count_backs and card.special is not None and "back" in card.special.lower():
                continue
            for thistype in card.cardtype.split():
                cardtypes_dict[thistype.capitalize()] += 1
        return cardtypes_dict

    def print_type_summary(
        self
    ) -> None:
        """
        Print a summary of card types in the deck to console.

        Displays count of each card type (Creature, Instant, Sorcery, etc.).
        """
        print()
        print("TYPE SUMMARY FOR: ", self.name, ".....................")
        type_dict = {typ:0 for typ in ["Creature", "Artifact", "Enchantment", "Instant", "Sorcery", "Land", "Planeswalker", "Battle"]}
        num_spells = self.count_spells()
        type_dict = self.get_cardtypes()
        print(type_dict["Land"], "\tLands")
        print(num_spells, "\tSpells\t")
        for typ in ["Creature", "Artifact", "Enchantment", "Instant", "Sorcery"]:
            if typ=="Sorcery":
                print(type_dict[typ], "\tSorceries\t", round(100*type_dict[typ]/num_spells, 1), "%")
            else:
                print(type_dict[typ], "\t"+typ+"s\t", round(100*type_dict[typ]/num_spells, 1), "%")
        for typ in ["Planeswalker", "Battle"]:
            if type_dict[typ]>0:
                print(type_dict[typ], "\t"+typ+"s\t", round(100*type_dict[typ]/num_spells, 1), "%")
        print()

    def print_tag_summary(
        self
    ) -> None:
        """
        Print a summary of card tags in the deck to console.

        Displays count of cards for each tag category.
        """
        print()
        print("TAG SUMMARY FOR: ", self.name, ".....................")
        tag_dict = {}
        subtag_dict_of_dicts = {}
        for card in self.cards:
            if not card.tags:
                continue
            supertags_this_card = []
            for tag in card.tags:
                supertag, _, subtag = tag.partition('-')
                if subtag:
                    if supertag not in supertags_this_card:
                        supertags_this_card.append(supertag)
                        tag_dict[supertag] = tag_dict.get(supertag, 0) + 1
                    subtag_dict_of_dicts.setdefault(supertag, {})
                    subtag_dict_of_dicts[supertag][subtag] = subtag_dict_of_dicts.get(supertag, {}).get(subtag, 0) + 1
                else:
                    tag_dict[supertag] = tag_dict.get(supertag, 0) + 1
        for tag in sorted(tag_dict.keys()):
            print(tag_dict[tag], "\t", tag)
            if tag in subtag_dict_of_dicts:
                for subtag in sorted(subtag_dict_of_dicts[tag].keys()):
                    print("  ", subtag_dict_of_dicts[tag][subtag], "\t", subtag)
        print()
    
    def print_color_summary(
        self
    ) -> None:
        """
        Print a summary of color distribution in the deck to console.

        Displays counts for colorless, monocolor, and multicolor cards,
        as well as specific color combinations.
        """
        print()
        print("COLOR SUMMARY FOR: ", self.name, ".....................")
        deck_colors = []
        mana_symbol_dict = {}
        for card in self.cards:
            if not card.is_spell():
                continue
            for color in card.colors:
                if color not in deck_colors:
                    deck_colors.append(color)
                if color in mana_symbol_dict.keys():
                    mana_symbol_dict[color] += 1
                else:
                    mana_symbol_dict[color] = 1
        total_mana_symbols = 0
        for color in mana_symbol_dict.keys():
            total_mana_symbols += mana_symbol_dict[color]
        deck_colors = Mana.colors_to_wubrg_order(deck_colors)
        print("All deck colors: ", deck_colors)
        for color in deck_colors:
            print("\t", color, "spells: ", round(mana_symbol_dict[color]*100/total_mana_symbols, 1), "%")
        print()
        # TODO -- scan lands and print mana symbols on lands summary

    def print_mana_summary(
        self
    ) -> None:
        """
        Print a summary of mana curve and distribution in the deck to console.

        Displays average mana value and mana curve distribution.
        """
        print()
        print("MANA SUMMARY FOR: ", self.name, ".....................")
        mana_value_dict = {}
        total_deck_mana_value = 0
        for card in self.cards:
            if card.special is not None and "transform" in card.special and "back" in card.special:
                continue
            if card.is_land():
                continue
            mana_value = card.get_mana_value()
            total_deck_mana_value += mana_value
            if mana_value not in mana_value_dict.keys():
                mana_value_dict[mana_value] = 1
            else:
                mana_value_dict[mana_value] += 1
        max_mana_value = max(mana_value_dict.values())
        for mana_value in range(min(mana_value_dict.keys()), max(mana_value_dict.keys())+1):
            print("Mana Value "+str(mana_value)+":"+(" " if mana_value<10 else ""), "#"*mana_value_dict.get(mana_value, 0), " "*(max_mana_value-mana_value_dict.get(mana_value, 0)), "("+str(mana_value_dict.get(mana_value, 0))+")"+("" if mana_value_dict.get(mana_value, 0)>=10 else " "), round(mana_value_dict.get(mana_value, 0)/len(self.cards)*100, 1), "%")
        print("Average Mana Value (Including Lands):", round(total_deck_mana_value / len(self.cards), 3))
        print("Average Mana Value (Excluding Lands):", round(total_deck_mana_value / self.count_spells(), 3))
        print()

    def get_tokens(
        self,
        save_path: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Extract all tokens created by cards in the deck.

        Parses rules text of all cards to identify tokens and saves them to JSON.

        Args:
            save_path: Optional path to save token JSON file (default: DECK_PATH/deck_name)

        Returns:
            Tuple of (specialized_tokens, common_tokens) where:
            - specialized_tokens: List of dicts with unique token properties
            - common_tokens: List of common token names
        """
        all_tokens, all_common_tokens = [], []
        for card in self.cards:
            this_card_specialized_tokens, this_card_common_tokens = card.get_tokens()
            all_tokens += this_card_specialized_tokens
            all_common_tokens += this_card_common_tokens
        def unique_tokens(
            all_tokens: List[Dict[str, Any]]
        ) -> List[Dict[str, Any]]:
            """
            Deduplicate tokens and aggregate their properties.

            If any card creating a token type is incomplete, the token is marked incomplete.

            Args:
                all_tokens: List of all token dictionaries from all cards

            Returns:
                List of unique token dictionaries with aggregated properties
            """
            unique_tokens = {}
            for token in all_tokens:
                # Create a key without the "complete" field
                key = tuple((k, v) for k, v in token.items() if k not in ['complete', 'related'])
                complete_value = token['complete'] if 'complete' in token.keys() else 0
                related_value = token['related'] if 'related' in token.keys() else []
                related_value = [related_value] if isinstance(related_value, str) else related_value
                if key in unique_tokens:
                    unique_tokens[key] = (unique_tokens[key][0] & complete_value, unique_tokens[key][1] + related_value)
                else:
                    unique_tokens[key] = (complete_value, related_value)
            # Reconstruct the list of dictionaries
            unique_all_tokens = []
            for key, derived_attributes in unique_tokens.items():
                complete, related_list = derived_attributes
                new_dict = dict(key)
                new_dict['complete'] = complete
                new_dict['related'] = related_list
                unique_all_tokens.append(new_dict)
            return unique_all_tokens
        all_tokens = unique_tokens(all_tokens)
        all_tokens = [{k: d[k] for k in ["name","cardtype","subtype","rules","power","toughness","frame","complete","related"] if k in d} for d in all_tokens] 
        all_common_tokens = list(set(all_common_tokens)) 
        print(f"\nFound {len(all_tokens)} token with names:", [token["name"] for token in all_tokens])
        if len(all_common_tokens)>0:
            print(f"Found {len(all_common_tokens)} common tokens: {all_common_tokens}")
        tokens_dict = {"_TOKEN_"+d['name']: d for d in all_tokens}
        if len(all_common_tokens)>0:
            tokens_dict["_COMMON_TOKENS"] = all_common_tokens
        if save_path is None:
            save_path = os.path.join(DECK_PATH, self.name)
        if not os.path.isdir(save_path):
            os.mkdir(save_path)
        if not os.path.isdir(save_path):
            os.mkdir(save_path)
        with open(os.path.join(save_path, self.name+'_Tokens.json'), 'w') as json_file:
            json.dump(tokens_dict, json_file, indent=4)
                 
    # TODO -- For tokens with duplicate names, make json string names (not card names) different according to differences -- can just append _B, _C, etc. (use letters here bc numbers to be reserved for arts (many arts with same name except _number will all map to same dict, just get different arts))


