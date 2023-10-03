import os
import json


class Mana:
    mana_symbols_standard = ['w','u','b','r','g','c','s']
    mana_symbols_variable = ['x','y','z']
    mana_symbols_numeric = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20']
    mana_symbols_dual_hybrid = ['w/u', 'u/w', 'w/b', 'b/w', 'w/r', 'r/w', 'w/g', 'g/w', 'u/b', 'b/u', 'u/r', 'r/u', 'u/g', 'g/u', 'b/r', 'r/b', 'b/g', 'g/b', 'r/g', 'g/r']
    mana_symbols_mono_hybrid = ['2/w', '2/u', '2/b', '2/r', '2/g']
    mana_symbols_phyrexian = ['w/p', 'u/p', 'b/p', 'r/p', 'g/p']
    mana_symbols_phyrexian_hybrid = [] # TODO -- unsupported. Need images for: ['w/u/p', 'u/w/p', 'w/b/p', 'b/w/p', 'w/r/p', 'r/w/p', 'w/g/p', 'g/w/p', 'u/b/p', 'b/u/p', 'u/r/p', 'r/u/p', 'u/g/p', 'g/u/p', 'b/r/p', 'r/b/p', 'b/g/p', 'g/b/p', 'r/g/p', 'g/r/p']
    mana_symbols = mana_symbols_standard + mana_symbols_variable + mana_symbols_numeric + mana_symbols_dual_hybrid + mana_symbols_mono_hybrid + mana_symbols_phyrexian + mana_symbols_phyrexian_hybrid
    mana_symbols_bracketed = ["{"+s+"}" for s in mana_symbols] 

    # Returns a dictionary where keys are mana symbols present in the card's mana cost, and values are counts for each of those mana symbols.
    # Note that generic mana symbols are supported only up until {20}.  
    def get_mana_symbols(mana_cost):
        mana_symbols = {}
        mana_cost = mana_cost.lower()
        for symbol in Mana.mana_symbols:
            count = mana_cost.count('{'+symbol+'}')
            if count>0:
                mana_symbols[symbol] = count
        return mana_symbols

    # Returns the integer mana value (converted mana cost) of the input card. 
    def get_mana_value(mana_cost):
        mana_value = 0
        for symbol in Mana.get_mana_symbols(mana_cost).keys():
            if symbol in Mana.mana_symbols_numeric:
                mana_value += int(symbol)
            elif symbol in Mana.mana_symbols_mono_hybrid:
                mana_value += 2
            elif symbol not in Mana.mana_symbols_variable:
                mana_value += 1
        return mana_value

    def get_colors(mana_cost):
        return [] if mana_cost is None else [color for color in ['w','u','b','r','g'] if color in mana_cost.lower()]
    def is_monocolored(mana_cost):
        return len(Mana.get_colors(mana_cost))==1
    def is_colorless(mana_cost):
        return len(Mana.get_colors(mana_cost))==0
    def is_multicolored(mana_cost):
        return len(Mana.get_colors(mana_cost))>1
    def is_bicolored(mana_cost):
        return len(Mana.get_colors(mana_cost))==2
    def is_tricolored(mana_cost):
        return len(Mana.get_colors(mana_cost))==3
    def is_quadcolored(mana_cost):
        return len(Mana.get_colors(mana_cost))==4
    def is_pentacolored(mana_cost):
        return len(Mana.get_colors(mana_cost))==5
    def is_white(mana_cost):
        return 'w' in Mana.get_colors(mana_cost)
    def is_blue(mana_cost):
        return 'u' in Mana.get_colors(mana_cost)
    def is_black(mana_cost):
        return 'b' in Mana.get_colors(mana_cost)
    def is_red(mana_cost):
        return 'r' in Mana.get_colors(mana_cost)
    def is_green(mana_cost):
        return 'g' in Mana.get_colors(mana_cost)
    def is_azorius(mana_cost):
        return Mana.is_white(mana_cost) and Mana.is_blue(mana_cost)
    def is_orzhov(mana_cost):
        return Mana.is_white(mana_cost) and Mana.is_black(mana_cost)
    def is_boros(mana_cost):
        return Mana.is_white(mana_cost) and Mana.is_red(mana_cost)
    def is_selesnya(mana_cost):
        return Mana.is_white(mana_cost) and Mana.is_green(mana_cost)
    def is_dimir(mana_cost):
        return Mana.is_blue(mana_cost) and Mana.is_black(mana_cost)
    def is_izzet(mana_cost):
        return Mana.is_blue(mana_cost) and Mana.is_red(mana_cost)
    def is_simic(mana_cost):
        return Mana.is_blue(mana_cost) and Mana.is_green(mana_cost)
    def is_rakdos(mana_cost):
        return Mana.is_black(mana_cost) and Mana.is_red(mana_cost)
    def is_golgari(mana_cost):
        return Mana.is_black(mana_cost) and Mana.is_green(mana_cost)
    def is_gruul(mana_cost):
        return Mana.is_red(mana_cost) and Mana.is_green(mana_cost)
    # TODO -- add 3 color and 4 color boolean functions

class Set:
    # Whenever a new custom set is created with a default setname conflicting with an existing setname, add that original and replacement setname as a key-value pair to the dictionary below. 
    forbidden_custom_set_names = {"ANA":"ANK"}

    # Adjusts the input setname if the name is reserved for an existing MTG set.    
    def adjust_forbidden_custom_setname(setname):
        if setname.upper() in Set.forbidden_custom_set_names.keys():
            return Set.forbidden_custom_set_names[setname]
        return setname

class Card:
    supertypes = ["token", "legendary", "basic", "snow"]
    cardtypes  = ["land", "creature", "artifact", "enchantment", "planeswalker", "instant", "sorcery", "battle"]

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
    # real: 1 if a real mtg card, 0 if custom
    def __init__(self, name=None, artist=None, artwork=None, setname=None, mana=None, cardtype=None, subtype=None, power=None, toughness=None, rarity=None, rules=None, rules1=None, rules2=None, rules3=None, rules4=None, flavor=None, special=None, related=None, colors=None, tags=None, complete=0, real=0):
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
        if flavor is not None and type(flavor)!=str:
            raise TypeError("flavor input must be of type str.")
        if special is not None and type(special)!=str:
            raise TypeError("special input must be of type str.")
        if related is not None and type(related)!=str:
            raise TypeError("related input must be of type str.")
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
        self.setname= setname if real else Set.adjust_forbidden_custom_setname(setname)
        self.mana=mana
        self.subtype=subtype
        self.power=power
        self.toughness=toughness
        self.rarity=rarity
        self.rules=rules
        self.rules1=rules1
        self.rules2=rules2
        self.rules3=rules3
        self.rules4=rules4
        self.flavor=flavor
        self.special=special
        self.related=related
        self.tags=tags
        self.complete=complete
        self.supertype=Card.get_supertype_from_cardtype(cardtype)
        self.cardtype=Card.filter_supertypes_from_cardtype(cardtype)
        self.colors = self.get_colors() if colors is None else colors

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
    # TODO -- add 3 color and 4 color boolean functions

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

    # Returns the complete line (string) giving a card's supertype(s), card type(s), and subtype(s).
    def get_type_line(self):
        type_line = ""
        if type(self.supertype)==str:
            type_line += self.supertype.title() + " "
        if type(self.cardtype)==str:
            type_line += self.cardtype.title()
        if type(self.subtype)==str:
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
    # TODO -- for lands, the frame filename will have to do with the colors of mana symbols in their text boxes. Not their own colors.
    def get_frame_filename(self, card_borders_folder=None):
        if self.is_tricolored():
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
            available_frames = ["creature", "noncreature"]
            if self.is_colorless():
                available_frames += ["artifact-creature", "artifact-noncreature"]
        elif self.is_mdfc():
            special="mdfc"
            if "front" in self.special.lower():
                special += "-front"
            elif "back" in self.special.lower():
                special += "-back"
            available_frames = ["creature", "noncreature"]
            if self.is_colorless():
                available_frames += ["artifact-creature", "artifact-noncreature"]
        elif self.is_token():
            special="token"
            available_frames = ["creature", "noncreature", "artifact-creature", "artifact-noncreature"]
        else:
            special=None
            available_frames = ["creature", "noncreature", "artifact-creature", "artifact-noncreature", "land", "enchantment-artifact-creature", "enchantment-artifact-noncreature", "enchantment-creature", "enchantment-land"]
        if special is not None:
            filename += special+"_"
        # Manage alternative frames (sagas, planeswalkers, etc.):
        if self.is_saga():
            if self.rules1==self.rules2 and self.rules2==self.rules3:
                numbers="123"
            elif self.rules1==self.rules2:
                numbers="12-3"
            elif self.rules2==self.rules3:
                numbers="1-23"
            else:
                numbers="1-2-3"
            filename += "saga_"+numbers
            # TODO -- add support for four-chapter sagas
        elif self.is_planeswalker(): # TODO -- add support for planeswalkers
            raise ValueError("planeswalkers are not currently supported.")
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


class Deck:
    def from_json(deck_filepath, setname="UNK"):
        f = open(deck_filepath)
        card_dict = json.load(f)
        for card in card_dict.values():
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
            if "flavor" not in card.keys():
                card["flavor"]=None
            if "special" not in card.keys(): 
                card["special"]=None
            if "related" not in card.keys():
                card["related"]=None
            if "colors" not in card.keys():
                card["colors"]=None
            if "tags" not in card.keys():
                card["tags"]=None
            if "complete" not in card.keys():
                card["complete"]=0
            if "real" not in card.keys():
                card["real"]=0
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
                      flavor=card["flavor"],
                      special=card["special"],
                      related=card["related"],
                      colors=card["colors"],
                      tags=card["tags"],
                      complete=card["complete"],
                      real=card["real"])
                  for card in card_dict.values()]
        return Deck(cards)

    def from_deck_folder(deck_folder):
        setname = (deck_folder.lower().replace("the ",""))[0:3].upper()
        setname = Set.adjust_forbidden_custom_setname(setname)
        deck_folder = deck_folder.title()
        deck_filepath = os.path.join(deck_folder, (os.path.basename(deck_folder).replace(" ", "_") + ".json"))
        return Deck.from_json(deck_filepath, setname=setname)

    def __init__(self, cards=[]):
        if any([type(c)!=Card for c in cards]):
            raise TypeError("All inputs must be of type Card.")
        self.cards = cards

    def get_cardtypes(self, count_backs=False, count_tokens=False):
        cardtypes_dict = {c.capitalize():0 for c in Card.cardtypes}
        for card in self.cards:
            if not count_tokens and card.is_token():
                continue
            if not count_backs and card.special is not None and "back" in card.special.lower():
                continue
            for thistype in card.cardtype.split():
                cardtypes_dict[thistype.capitalize()] += 1
        return cardtypes_dict

    def print_type_summary(self):
        pass
        """
        total_cards = 0
        max_cmc_count = 0
        for cmc in sorted(cmc_dict.keys()):
            total_cards += cmc_dict[cmc]
            max_cmc_count = max(cmc_dict[cmc], max_cmc_count)
        print(".................................")
        print(type_dict["Land"], "\tLands")
        print(total_cards, "\tSpells\t")
        print(type_dict["Creature"], "\tCreatures\t", round(100*type_dict["Creature"]/total_cards, 1), "%")
        print(type_dict["Artifact"], "\tArtifacts\t", round(100*type_dict["Artifact"]/total_cards, 1), "%")
        print(type_dict["Enchantment"], "\tEnchantments\t", round(100*type_dict["Enchantment"]/total_cards, 1), "%")
        print(type_dict["Instant"], "\tInstants\t", round(100*type_dict["Instant"]/total_cards, 1), "%")
        print(type_dict["Sorcery"], "\tSorceries\t", round(100*type_dict["Sorcery"]/total_cards, 1), "%")
        """

    def print_tag_summary(self):
        pass
        """
        print(".................................")
        for tag in sorted(tags_dict.keys()):
            print(tags_dict[tag], "\t", string.title(tag))
        """

    def print_mana_summary(self):
        pass
        """
        print(".................................")
        cmc_sum = 0
        for cmc in sorted(cmc_dict.keys()):
            cmc_sum += cmc_dict[cmc] * cmc
            print("CMC", cmc, ": ", "#"*cmc_dict[cmc], " "*(max_cmc_count-cmc_dict[cmc]), round(cmc_dict[cmc]/total_cards*100, 1), "%")
        print("Average CMC:", round(cmc_sum / total_cards, 2))
        print(".................................")
        print("Colors: ", deck_colors)
        total_mana_symbols = 0
        for color in mana_symbol_dict.keys():
            total_mana_symbols += mana_symbol_dict[color]
        for color in mana_symbol_dict.keys():
            print(color, ": ", round(mana_symbol_dict[color]*100/total_mana_symbols, 1), "%")
        print(".................................")
        """
    
all_symbols = Mana.mana_symbols + ["q", "t"]
all_symbols_bracketed = ["{"+s+"}" for s in all_symbols] 