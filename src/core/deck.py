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

        Supports both old format (flat card dict) and new format (metadata/cards/tokens).

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
        data = json.load(f)
        f.close()

        # Detect format: new format has "metadata" key, old format does not
        if "metadata" in data:
            # New format
            return Deck._from_json_new_format(data, setname, deck_name)
        else:
            # Old format (backward compatibility)
            return Deck._from_json_old_format(data, deck_json_filepath, setname, deck_name)

    @staticmethod
    def _from_json_old_format(
        card_dict: Dict[str, Any],
        deck_json_filepath: str,
        setname: str = "UNK",
        deck_name: Optional[str] = None
    ) -> 'Deck':
        """Load deck from old JSON format (flat card dictionary)."""
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
    def _from_json_new_format(
        data: Dict[str, Any],
        setname: str = "UNK",
        deck_name: Optional[str] = None
    ) -> 'Deck':
        """Load deck from new JSON format (metadata/cards/tokens structure)."""
        from datetime import datetime

        # Extract metadata
        metadata = data.get("metadata", {})
        folder_name = metadata.get("folder_name", "Unknown")
        deck_display_name = metadata.get("deck_name", deck_name or folder_name)
        description = metadata.get("description")
        format_type = metadata.get("format")
        created = metadata.get("created")
        last_modified = metadata.get("last_modified")
        author = metadata.get("author")
        deck_tags = metadata.get("tags", [])
        commander = metadata.get("commander")

        # Get default setname from metadata, fallback to parameter, then "UNK"
        default_setname = metadata.get("setname", setname)

        # Extract cards
        card_dict = data.get("cards", {})
        tags = []

        # Process each card
        for keyname, card in card_dict.items():
            # Check if this is a card with new front/back structure
            if "front" in card:
                # New structure (either single-faced with front, or double-faced with front+back)
                # Skip defaults, handle separately
                continue

            # Set defaults for missing fields (old format only)
            if "artist" not in card.keys():
                card["artist"]=None
            if "artwork" not in card.keys():
                card["artwork"]=None
            if "setname" not in card.keys():
                card["setname"]=default_setname
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
            for i in range(1, 7):
                if f"rules{i}" not in card.keys():
                    card[f"rules{i}"]=None
            if "flavor" not in card.keys():
                card["flavor"]=None
            if "special" not in card.keys():
                card["special"]=None
            if "related_indicator" not in card.keys():
                card["related_indicator"]=None
            if "related" not in card.keys():
                card["related"]=None
            elif (card["special"] is not None) and (("mdfc" in card["special"].lower()) or ("transform" in card["special"].lower())) and (card["related_indicator"] is None):
                # Auto-generate related_indicator for double-faced cards
                related_name, related_mana = "", ""
                for keyname2, card2 in card_dict.items():
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
            if "quantity" not in card.keys():
                card["quantity"]=None
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
            # Handle supertype fields
            if "legendary" not in card.keys():
                card["legendary"]=None
            if "basic" not in card.keys():
                card["basic"]=None
            if "snow" not in card.keys():
                card["snow"]=None
            if "token" not in card.keys():
                card["token"]=None

        # Create Card objects
        from src.core.card import CardFace
        cards = []

        for keyname, card in card_dict.items():
            # Check for new double-faced structure
            if "front" in card and "back" in card:
                # Double-faced card with new structure
                # Extract shared card-level fields
                quantity = card.get("quantity", 1)
                complete = card.get("complete", 0)
                real = card.get("real", 0)
                rarity = card.get("rarity")
                colors = card.get("colors")
                card_tags = card.get("tags")
                setname = card.get("setname", default_setname)
                artwork = card.get("artwork")
                artist = card.get("artist")
                double_faced_type = card.get("double_faced_type")  # "transform" or "mdfc"

                # Create CardFace objects for front and back
                front_data = card["front"]
                back_data = card["back"]

                front_face = CardFace(
                    name=front_data["name"],
                    mana=front_data.get("mana"),
                    cardtype=front_data.get("cardtype"),
                    subtype=front_data.get("subtype"),
                    power=front_data.get("power"),
                    toughness=front_data.get("toughness"),
                    rules=front_data.get("rules"),
                    rules1=front_data.get("rules1"),
                    rules2=front_data.get("rules2"),
                    rules3=front_data.get("rules3"),
                    rules4=front_data.get("rules4"),
                    rules5=front_data.get("rules5"),
                    rules6=front_data.get("rules6"),
                    flavor=front_data.get("flavor"),
                    related_indicator=front_data.get("related_indicator"),
                    legendary=front_data.get("legendary"),
                    basic=front_data.get("basic"),
                    snow=front_data.get("snow")
                )

                back_face = CardFace(
                    name=back_data["name"],
                    mana=back_data.get("mana"),
                    cardtype=back_data.get("cardtype"),
                    subtype=back_data.get("subtype"),
                    power=back_data.get("power"),
                    toughness=back_data.get("toughness"),
                    rules=back_data.get("rules"),
                    rules1=back_data.get("rules1"),
                    rules2=back_data.get("rules2"),
                    rules3=back_data.get("rules3"),
                    rules4=back_data.get("rules4"),
                    rules5=back_data.get("rules5"),
                    rules6=back_data.get("rules6"),
                    flavor=back_data.get("flavor"),
                    related_indicator=back_data.get("related_indicator"),
                    legendary=back_data.get("legendary"),
                    basic=back_data.get("basic"),
                    snow=back_data.get("snow")
                )

                # Create Card using front face data for the old fields (for backward compatibility)
                # but also populate the new front/back CardFace fields
                new_card = Card(
                    name=front_face.name,
                    artist=artist,
                    artwork=artwork,
                    setname=setname,
                    mana=front_face.mana,
                    cardtype=front_face.cardtype,
                    subtype=front_face.subtype,
                    power=front_face.power,
                    toughness=front_face.toughness,
                    rarity=rarity,
                    rules=front_face.rules,
                    rules1=front_face.rules1,
                    rules2=front_face.rules2,
                    rules3=front_face.rules3,
                    rules4=front_face.rules4,
                    rules5=front_face.rules5,
                    rules6=front_face.rules6,
                    flavor=front_face.flavor,
                    special=f"{double_faced_type}-front" if double_faced_type else None,
                    related=back_face.name,
                    related_indicator=front_face.related_indicator,
                    colors=colors,
                    tags=card_tags,
                    quantity=quantity,
                    complete=complete,
                    real=real,
                    legendary=front_face.supertype and "legendary" in front_face.supertype.lower(),
                    basic=front_face.supertype and "basic" in front_face.supertype.lower(),
                    snow=front_face.supertype and "snow" in front_face.supertype.lower()
                )

                # Populate the new CardFace fields
                new_card.front = front_face
                new_card.back = back_face
                new_card.double_faced_type = double_faced_type

                cards.append(new_card)

                # Collect tags
                if card_tags:
                    for tag in card_tags:
                        if tag not in tags:
                            tags.append(tag)
            elif "front" in card:
                # Single-faced card with new structure (has front but no back)
                # Extract shared card-level fields
                quantity = card.get("quantity", 1)
                complete = card.get("complete", 0)
                real = card.get("real", 0)
                rarity = card.get("rarity")
                colors = card.get("colors")
                card_tags = card.get("tags")
                setname = card.get("setname", default_setname)
                artwork = card.get("artwork")
                artist = card.get("artist")
                token = card.get("token")

                # Create CardFace object for front
                front_data = card["front"]

                front_face = CardFace(
                    name=front_data["name"],
                    mana=front_data.get("mana"),
                    cardtype=front_data.get("cardtype"),
                    subtype=front_data.get("subtype"),
                    power=front_data.get("power"),
                    toughness=front_data.get("toughness"),
                    rules=front_data.get("rules"),
                    rules1=front_data.get("rules1"),
                    rules2=front_data.get("rules2"),
                    rules3=front_data.get("rules3"),
                    rules4=front_data.get("rules4"),
                    rules5=front_data.get("rules5"),
                    rules6=front_data.get("rules6"),
                    flavor=front_data.get("flavor"),
                    related_indicator=front_data.get("related_indicator"),
                    legendary=front_data.get("legendary"),
                    basic=front_data.get("basic"),
                    snow=front_data.get("snow")
                )

                # Create Card using front face data
                new_card = Card(
                    name=front_face.name,
                    artist=artist,
                    artwork=artwork,
                    setname=setname,
                    mana=front_face.mana,
                    cardtype=front_face.cardtype,
                    subtype=front_face.subtype,
                    power=front_face.power,
                    toughness=front_face.toughness,
                    rarity=rarity,
                    rules=front_face.rules,
                    rules1=front_face.rules1,
                    rules2=front_face.rules2,
                    rules3=front_face.rules3,
                    rules4=front_face.rules4,
                    rules5=front_face.rules5,
                    rules6=front_face.rules6,
                    flavor=front_face.flavor,
                    colors=colors,
                    tags=card_tags,
                    quantity=quantity,
                    complete=complete,
                    real=real,
                    token=token,
                    legendary=front_face.supertype and "legendary" in front_face.supertype.lower(),
                    basic=front_face.supertype and "basic" in front_face.supertype.lower(),
                    snow=front_face.supertype and "snow" in front_face.supertype.lower()
                )

                # Populate the new CardFace field (no back face for single-faced cards)
                new_card.front = front_face

                cards.append(new_card)

                # Collect tags
                if card_tags:
                    for tag in card_tags:
                        if tag not in tags:
                            tags.append(tag)
            else:
                # Single-faced card (old structure)
                cards.append(Card(
                    name=card["name"],
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
                    quantity=card["quantity"],
                    complete=card["complete"],
                    real=card["real"],
                    frame=card["frame"],
                    legendary=card["legendary"],
                    basic=card["basic"],
                    snow=card["snow"],
                    token=card["token"]
                ))

        # Extract tokens (stored in deck, not as separate Cards)
        tokens_dict = data.get("tokens", {})

        # Merge deck_tags with card tags
        all_tags = list(set(tags + deck_tags))

        return Deck(
            cards=cards,
            name=deck_display_name,
            tags=all_tags,
            folder_name=folder_name,
            description=description,
            format=format_type,
            created=created,
            last_modified=last_modified,
            author=author,
            commander=commander,
            tokens=tokens_dict,
            setname=default_setname
        )

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
        common_tokens: List[str] = [],
        folder_name: Optional[str] = None,
        description: Optional[str] = None,
        format: Optional[str] = None,
        created: Optional[str] = None,
        last_modified: Optional[str] = None,
        author: Optional[str] = None,
        commander: Optional[Any] = None,
        tokens: Optional[Dict[str, Any]] = None,
        setname: Optional[str] = None
    ) -> None:
        """
        Initialize a Deck.

        Args:
            cards: List of Card objects in the deck
            name: Display name of the deck
            tags: List of tags for categorization
            basics_dict: Dictionary of basic land information (old format)
            common_tokens: List of common token names created by cards (old format)
            folder_name: Name of deck folder on filesystem
            description: User-provided deck description
            format: Format (Commander, Modern, Standard, etc.)
            created: Deck creation timestamp (ISO 8601)
            last_modified: Last modification timestamp (ISO 8601)
            author: Deck creator name
            commander: Commander card name(s). Can be a string (single commander) or list of strings (partner commanders, etc.)
            tokens: Dictionary of token definitions (new format)
            setname: Default set code for cards without specific setname (default: "UNK")

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

        # New metadata fields
        self.folder_name = folder_name or name
        self.description = description
        self.format = format
        self.created = created
        self.last_modified = last_modified
        self.author = author

        # Commander can be a string (single) or list (partners/multiple)
        # Normalize to list internally for consistency
        if commander is None:
            self.commander = None
        elif isinstance(commander, str):
            self.commander = [commander] if commander else None
        elif isinstance(commander, list):
            self.commander = commander if commander else None
        else:
            self.commander = [str(commander)]

        self.tokens = tokens or {}
        self.setname = setname or "UNK"

    def to_json(
        self,
        filepath: Optional[str] = None,
        use_new_format: bool = True
    ) -> Dict[str, Any]:
        """
        Export deck to JSON format.

        Args:
            filepath: Optional path to save JSON file. If None, returns dict without saving.
            use_new_format: If True, use new metadata/cards/tokens format. If False, use old flat format.

        Returns:
            Dictionary representation of the deck
        """
        from datetime import datetime

        if use_new_format:
            # Export commander: if single commander, export as string for simplicity
            # If multiple commanders (partners, etc.), export as list
            commander_export = None
            if self.commander is not None:
                if len(self.commander) == 1:
                    commander_export = self.commander[0]
                else:
                    commander_export = self.commander

            # New format with metadata/cards/tokens structure
            deck_dict = {
                "metadata": {
                    "folder_name": self.folder_name,
                    "deck_name": self.name,
                    "description": self.description,
                    "format": self.format,
                    "created": self.created or datetime.now().isoformat(),
                    "last_modified": datetime.now().isoformat(),
                    "author": self.author,
                    "tags": self.tags,
                    "commander": commander_export,
                    "setname": self.setname
                },
                "cards": {},
                "tokens": self.tokens
            }

            # Add cards
            for card in self.cards:
                # Check if this is a double-faced card with CardFace objects
                if hasattr(card, 'front') and card.front is not None and hasattr(card, 'back') and card.back is not None:
                    # Double-faced card - use new front/back structure
                    key = f"{card.front.name} / {card.back.name}"

                    card_data = {
                        "front": card.front.to_dict(),
                        "back": card.back.to_dict(),
                    }

                    # Add shared card-level fields
                    if card.double_faced_type: card_data["double_faced_type"] = card.double_faced_type
                    if card.quantity and card.quantity != 1: card_data["quantity"] = card.quantity
                    if card.complete: card_data["complete"] = card.complete
                    if card.real: card_data["real"] = card.real
                    if card.rarity: card_data["rarity"] = card.rarity
                    if card.colors: card_data["colors"] = card.colors
                    if card.tags: card_data["tags"] = card.tags
                    if card.artwork: card_data["artwork"] = card.artwork
                    if card.artist: card_data["artist"] = card.artist

                    # Add setname only if it differs from deck's default
                    if hasattr(card, 'setname') and card.setname and card.setname != self.setname:
                        card_data["setname"] = card.setname

                    deck_dict["cards"][key] = card_data
                else:
                    # Single-faced card - use new front structure for consistency
                    # Check if card has CardFace object
                    if hasattr(card, 'front') and card.front is not None:
                        # Card has CardFace - use it
                        card_data = {
                            "front": card.front.to_dict()
                        }
                    else:
                        # Card doesn't have CardFace - create front dict from card fields
                        front_dict = {
                            "name": card.name,
                        }

                        # Add face-specific fields
                        if card.mana: front_dict["mana"] = card.mana
                        if card.cardtype: front_dict["cardtype"] = card.cardtype
                        if card.subtype: front_dict["subtype"] = card.subtype
                        if card.power: front_dict["power"] = card.power
                        if card.toughness: front_dict["toughness"] = card.toughness
                        if card.rules: front_dict["rules"] = card.rules
                        if card.rules1: front_dict["rules1"] = card.rules1
                        if card.rules2: front_dict["rules2"] = card.rules2
                        if card.rules3: front_dict["rules3"] = card.rules3
                        if card.rules4: front_dict["rules4"] = card.rules4
                        if card.rules5: front_dict["rules5"] = card.rules5
                        if card.rules6: front_dict["rules6"] = card.rules6
                        if card.flavor: front_dict["flavor"] = card.flavor
                        if card.related_indicator: front_dict["related_indicator"] = card.related_indicator

                        # Add supertype fields to front
                        if hasattr(card, 'supertype') and card.supertype:
                            if 'Legendary' in card.supertype: front_dict["legendary"] = 1
                            if 'Basic' in card.supertype: front_dict["basic"] = 1
                            if 'Snow' in card.supertype: front_dict["snow"] = 1

                        card_data = {"front": front_dict}

                    # Add shared card-level fields
                    if card.quantity and card.quantity != 1: card_data["quantity"] = card.quantity
                    if card.complete: card_data["complete"] = card.complete
                    if card.real: card_data["real"] = card.real
                    if card.rarity: card_data["rarity"] = card.rarity
                    if card.colors: card_data["colors"] = card.colors
                    if card.tags: card_data["tags"] = card.tags
                    if card.artwork: card_data["artwork"] = card.artwork
                    if card.artist: card_data["artist"] = card.artist

                    # Add setname only if it differs from deck's default
                    if hasattr(card, 'setname') and card.setname and card.setname != self.setname:
                        card_data["setname"] = card.setname

                    # Add token field if present
                    if hasattr(card, 'token') and card.token:
                        card_data["token"] = card.token

                    deck_dict["cards"][card.name] = card_data

        else:
            # Old format (flat card dictionary) for backward compatibility
            deck_dict = {}

            # Add cards
            for card in self.cards:
                card_data = {
                    "name": card.name,
                    "cardtype": card.cardtype,
                }

                # Add all fields (old format includes everything)
                if card.mana: card_data["mana"] = card.mana
                if card.subtype: card_data["subtype"] = card.subtype
                if card.power: card_data["power"] = card.power
                if card.toughness: card_data["toughness"] = card.toughness
                if card.rarity: card_data["rarity"] = card.rarity
                if card.rules: card_data["rules"] = card.rules
                if card.rules1: card_data["rules1"] = card.rules1
                if card.rules2: card_data["rules2"] = card.rules2
                if card.rules3: card_data["rules3"] = card.rules3
                if card.rules4: card_data["rules4"] = card.rules4
                if card.rules5: card_data["rules5"] = card.rules5
                if card.rules6: card_data["rules6"] = card.rules6
                if card.flavor: card_data["flavor"] = card.flavor
                if card.special: card_data["special"] = card.special
                if card.related: card_data["related"] = card.related
                if card.related_indicator: card_data["related_indicator"] = card.related_indicator
                if card.colors: card_data["colors"] = card.colors
                if card.tags: card_data["tags"] = card.tags
                if card.complete: card_data["complete"] = card.complete
                if card.real: card_data["real"] = card.real
                if card.frame: card_data["frame"] = card.frame
                if card.artwork: card_data["artwork"] = card.artwork
                if card.artist: card_data["artist"] = card.artist

                # Add supertype fields
                if hasattr(card, 'supertype') and card.supertype:
                    if 'Legendary' in card.supertype: card_data["legendary"] = 1
                    if 'Basic' in card.supertype: card_data["basic"] = 1
                    if 'Snow' in card.supertype: card_data["snow"] = 1
                    if 'Token' in card.supertype: card_data["token"] = 1

                deck_dict[card.name] = card_data

            # Add old format special keys
            if self.basics_dict:
                deck_dict["_basics"] = self.basics_dict
            if self.common_tokens:
                deck_dict["_common_tokens"] = self.common_tokens

        # Save to file if filepath provided
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(deck_dict, f, indent=4)

        return deck_dict

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
        save_path: Optional[str] = None,
        save_to_deck: bool = True,
        save_legacy_file: bool = False
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Extract all tokens created by cards in the deck.

        Parses rules text of all cards to identify tokens. Populates self.tokens with
        new format including source_cards tracking.

        Args:
            save_path: Optional path to save token JSON file (default: DECK_PATH/deck_name)
            save_to_deck: If True, populate self.tokens dict (new format)
            save_legacy_file: If True, save separate _Tokens.json file (old format)

        Returns:
            Tuple of (specialized_tokens, common_tokens) where:
            - specialized_tokens: List of dicts with unique token properties
            - common_tokens: List of common token names
        """
        from src.token_generation.token_parser import load_common_token_definitions

        # Track which cards create which tokens
        token_to_sources = {}  # {token_name: [source_card_names]}
        all_tokens, all_common_tokens = [], []

        for card in self.cards:
            this_card_specialized_tokens, this_card_common_tokens = card.get_tokens()

            # Track source cards for specialized tokens
            for token in this_card_specialized_tokens:
                token_name = token.get('name', '')
                if token_name not in token_to_sources:
                    token_to_sources[token_name] = []
                token_to_sources[token_name].append(card.name)

            # Track source cards for common tokens
            for token_name in this_card_common_tokens:
                if token_name not in token_to_sources:
                    token_to_sources[token_name] = []
                token_to_sources[token_name].append(card.name)

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

        print(f"\nFound {len(all_tokens)} specialized tokens:", [token["name"] for token in all_tokens])
        if len(all_common_tokens)>0:
            print(f"Found {len(all_common_tokens)} common tokens: {all_common_tokens}")

        # Populate self.tokens with new format (includes source_cards)
        if save_to_deck:
            self.tokens = {}
            common_token_defs = load_common_token_definitions()

            # Add specialized tokens
            for token in all_tokens:
                token_name = token['name']
                token_key = f"_TOKEN_{token_name}"
                token_dict = token.copy()
                token_dict['token'] = 1
                token_dict['quantity'] = 1
                token_dict['source_cards'] = token_to_sources.get(token_name, [])
                # Rename 'related' to 'source_cards' if it exists
                if 'related' in token_dict:
                    del token_dict['related']
                self.tokens[token_key] = token_dict

            # Add common tokens with definitions from common_tokens.json
            for common_token_name in all_common_tokens:
                token_key = f"_TOKEN_{common_token_name}"
                if common_token_name in common_token_defs:
                    # Use definition from common_tokens.json
                    token_dict = common_token_defs[common_token_name].copy()
                    token_dict['source_cards'] = token_to_sources.get(common_token_name, [])
                    token_dict['quantity'] = 1
                    token_dict['complete'] = 1  # Common tokens are pre-defined
                    self.tokens[token_key] = token_dict
                else:
                    # Fallback: minimal token definition
                    self.tokens[token_key] = {
                        'name': common_token_name,
                        'token': 1,
                        'complete': 0,
                        'quantity': 1,
                        'source_cards': token_to_sources.get(common_token_name, [])
                    }

        # Legacy: Save separate _Tokens.json file (old format)
        if save_legacy_file:
            tokens_dict = {"_TOKEN_"+d['name']: d for d in all_tokens}
            if len(all_common_tokens)>0:
                tokens_dict["_COMMON_TOKENS"] = all_common_tokens

            if save_path is None:
                save_path = os.path.join(DECK_PATH, self.name)
            if not os.path.isdir(save_path):
                os.mkdir(save_path)

            with open(os.path.join(save_path, self.name+'_Tokens.json'), 'w') as json_file:
                json.dump(tokens_dict, json_file, indent=4)

        return (all_tokens, all_common_tokens)

    # TODO -- For tokens with duplicate names, make json string names (not card names) different according to differences -- can just append _B, _C, etc. (use letters here bc numbers to be reserved for arts (many arts with same name except _number will all map to same dict, just get different arts))


