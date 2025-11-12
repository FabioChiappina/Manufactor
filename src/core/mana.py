"""
Mana cost parsing and color management for Magic: The Gathering cards.

This module provides the Mana class which handles:
- Mana symbol parsing and validation
- Color identity calculation
- Mana value (CMC) computation
- Color-based card type checking (monocolored, multicolored, specific guild colors)
- Mana cost sorting and normalization
"""

from functools import cmp_to_key


class Mana:
    """Handles all mana-related operations for MTG cards."""

    mana_symbols_standard = ['w','u','b','r','g','c','s']
    mana_symbols_variable = ['x','y','z']
    mana_symbols_numeric = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20']
    mana_symbols_dual_hybrid = ['w/u', 'w/b', 'r/w', 'g/w', 'u/b', 'u/r', 'g/u', 'b/r', 'b/g', 'r/g', 'c/w', 'c/u', 'c/b', 'c/r', 'c/g']
    mana_symbols_mono_hybrid = ['2/w', '2/u', '2/b', '2/r', '2/g']
    mana_symbols_phyrexian = ['w/p', 'u/p', 'b/p', 'r/p', 'g/p']
    mana_symbols_phyrexian_hybrid = ['w/u/p', 'w/b/p', 'r/w/p', 'g/w/p', 'u/b/p', 'u/r/p', 'g/u/p', 'b/r/p', 'b/g/p', 'r/g/p']
    mana_symbols_custom = ['e']
    mana_symbols = mana_symbols_standard + mana_symbols_variable + mana_symbols_numeric + mana_symbols_dual_hybrid + mana_symbols_mono_hybrid + mana_symbols_phyrexian + mana_symbols_phyrexian_hybrid + mana_symbols_custom
    mana_symbols_bracketed = ["{"+s+"}" for s in mana_symbols]

    # Returns a dictionary where keys are mana symbols present in the card's mana cost, and values are counts for each of those mana symbols.
    # Note that generic mana symbols are supported only up until {20}.
    def get_mana_symbols(mana_cost):
        mana_symbols = {}
        try:
            mana_cost = mana_cost.lower()
        except:
            return {}
        mana_cost = Mana.correct_hybrid_symbols(mana_cost)
        for symbol in Mana.mana_symbols:
            count = mana_cost.count('{'+symbol+'}')
            if count>0:
                mana_symbols[symbol] = count
        return mana_symbols

    # Returns the integer mana value (converted mana cost) of the input card.
    def get_mana_value(mana_cost):
        mana_value = 0
        mana_value_dict = Mana.get_mana_symbols(mana_cost)
        for symbol in mana_value_dict.keys():
            if symbol in Mana.mana_symbols_numeric:
                mana_value += int(symbol) * mana_value_dict[symbol]
            elif symbol in Mana.mana_symbols_mono_hybrid:
                mana_value += 2 * mana_value_dict[symbol]
            elif symbol not in Mana.mana_symbols_variable:
                mana_value += 1 * mana_value_dict[symbol]
        return mana_value

    def get_colors(mana_cost):
        return [] if mana_cost is None else [color for color in ['w','u','b','r','g'] if color in mana_cost.lower()]

    def get_colors_in_text(text):
        text = text.lower()
        colors = []
        for c in ["w","u","b","r","g"]:
            if "{"+c in text or c+"}" in text:
                if c not in colors:
                    colors.append(c)
        return colors

    def get_colors_produced_by_land(text):
        rules = text.lower()
        colors = []
        rules_lines = rules.split("\n")
        for line in rules_lines:
            split_by_colon = line.split(":")
            if len(split_by_colon)==2:
                line = split_by_colon[1]
            for c in ["w","u","b","r","g"]:
                if "{"+c in line or c+"}" in line:
                    if c not in colors:
                        colors.append(c)
        if ("mana of any" in rules and "color" in rules) or ("mana in any combination of colors" in rules):
            for c in ["w","u","b","r","g"]:
                if c not in colors:
                    colors.append(c)
        return colors

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

    def is_abzan(mana_cost):
        return Mana.is_white(mana_cost) and Mana.is_black(mana_cost) and Mana.is_green(mana_cost)

    def is_bant(mana_cost):
        return Mana.is_white(mana_cost) and Mana.is_blue(mana_cost) and Mana.is_green(mana_cost)

    def is_esper(mana_cost):
        return Mana.is_white(mana_cost) and Mana.is_blue(mana_cost) and Mana.is_black(mana_cost)

    def is_grixis(mana_cost):
        return Mana.is_blue(mana_cost) and Mana.is_black(mana_cost) and Mana.is_red(mana_cost)

    def is_jeskai(mana_cost):
        return Mana.is_white(mana_cost) and Mana.is_blue(mana_cost) and Mana.is_red(mana_cost)

    def is_jund(mana_cost):
        return Mana.is_black(mana_cost) and Mana.is_red(mana_cost) and Mana.is_green(mana_cost)

    def is_mardu(mana_cost):
        return Mana.is_white(mana_cost) and Mana.is_black(mana_cost) and Mana.is_red(mana_cost)

    def is_naya(mana_cost):
        return Mana.is_white(mana_cost) and Mana.is_red(mana_cost) and Mana.is_green(mana_cost)

    def is_sultai(mana_cost):
        return Mana.is_blue(mana_cost) and Mana.is_black(mana_cost) and Mana.is_green(mana_cost)

    def is_temur(mana_cost):
        return Mana.is_blue(mana_cost) and Mana.is_red(mana_cost) and Mana.is_green(mana_cost)

    def is_glint(mana_cost):
        return Mana.is_blue(mana_cost) and Mana.is_black(mana_cost) and Mana.is_red(mana_cost) and Mana.is_green(mana_cost)

    def is_dune(mana_cost):
        return Mana.is_white(mana_cost) and Mana.is_black(mana_cost) and Mana.is_red(mana_cost) and Mana.is_green(mana_cost)

    def is_ink(mana_cost):
        return Mana.is_white(mana_cost) and Mana.is_blue(mana_cost) and Mana.is_red(mana_cost) and Mana.is_green(mana_cost)

    def is_witch(mana_cost):
        return Mana.is_white(mana_cost) and Mana.is_blue(mana_cost) and Mana.is_black(mana_cost) and Mana.is_green(mana_cost)

    def is_yore(mana_cost):
        return Mana.is_white(mana_cost) and Mana.is_blue(mana_cost) and Mana.is_black(mana_cost) and Mana.is_red(mana_cost)

    # Sorts the input colors list to WUBRG order.
    # Colors are not wrapped around -- the order is always WUBRG. (e.g., W is always before G)
    def colors_to_wubrg_order(colors):
        sorted_colors = []
        for color in "wubrgcs":
            if color in colors:
                sorted_colors.append(color)
        return sorted_colors

    # Corrects any hybrid mana symbols with incorrect orderings (e.g., {u/w} --> {w/u})
    def correct_hybrid_symbols(mana_cost):
        if mana_cost is None:
            return None
        mana_cost = mana_cost.replace("u/w", "w/u")
        mana_cost = mana_cost.replace("b/w", "w/b")
        mana_cost = mana_cost.replace("w/r", "r/w")
        mana_cost = mana_cost.replace("w/g", "g/w")
        mana_cost = mana_cost.replace("b/u", "u/b")
        mana_cost = mana_cost.replace("r/u", "u/r")
        mana_cost = mana_cost.replace("u/g", "g/u")
        mana_cost = mana_cost.replace("r/b", "b/r")
        mana_cost = mana_cost.replace("g/b", "b/g")
        mana_cost = mana_cost.replace("g/r", "r/g")
        mana_cost = mana_cost.replace("p/w", "w/p")
        mana_cost = mana_cost.replace("p/u", "u/p")
        mana_cost = mana_cost.replace("p/b", "b/p")
        mana_cost = mana_cost.replace("p/r", "r/p")
        mana_cost = mana_cost.replace("p/g", "g/p")
        mana_cost = mana_cost.replace("w/c", "c/w")
        mana_cost = mana_cost.replace("u/c", "c/u")
        mana_cost = mana_cost.replace("b/c", "c/b")
        mana_cost = mana_cost.replace("r/c", "c/r")
        mana_cost = mana_cost.replace("g/c", "c/g")
        mana_cost = mana_cost.replace("w/2", "2/w")
        mana_cost = mana_cost.replace("u/2", "2/u")
        mana_cost = mana_cost.replace("b/2", "2/b")
        mana_cost = mana_cost.replace("r/2", "2/r")
        mana_cost = mana_cost.replace("g/2", "2/g")
        return mana_cost

    # Sorts the input mana cost so that wrap-around WUBRG order is reinforced. (e.g, WG --> GW)
    def sort(mana_cost):
        if mana_cost is None or type(mana_cost)!=str:
            return None
        if mana_cost == "{t}" or mana_cost == "{q}":
            return mana_cost
        mana_cost = Mana.correct_hybrid_symbols(mana_cost.lower())
        mana_symbols = Mana.get_mana_symbols(mana_cost)
        mana_symbols_list = []
        for mana_symbol in mana_symbols.keys():
            mana_symbols_list += [mana_symbol for i in range(mana_symbols[mana_symbol])]
        mana_symbols_list = sorted(mana_symbols_list, key=cmp_to_key(Mana.compare_two_mana_symbols))
        mana_symbols_list = ["{"+m+"}" for m in mana_symbols_list]
        return "".join(mana_symbols_list)

    # Comparator used to decide which of two input mana symbols comes first in wrap-around WUBRG order.
    # Returns a negative number if mana_symbol_1 comes before mana_symbol_2.
    def compare_two_mana_symbols(mana_symbol_1, mana_symbol_2):
        mana_symbol_1 = mana_symbol_1.replace("{","").replace("}","")
        mana_symbol_2 = mana_symbol_2.replace("{","").replace("}","")
        if mana_symbol_1 == mana_symbol_2:
            return 0
        # NOTE: when adding new mana symbols to sorted_order, make sure to add them twice for proper wrap-around ordering
        sorted_order = ["x","y","z","20","19","18","17","16","15","14","13","12","11","10","9","8","7","6","5","4","3","2","1","0","s","c","e","w","2/w","c/w","w/p","w/u","w/u/p","w/b","w/b/p","u","2/u","c/u","u/p","u/b","u/b/p","u/r","u/r/p","b","2/b","c/b","b/p","b/r","b/r/p","b/g","b/g/p","r","2/r","c/r","r/p","r/g","r/g/p","r/w","r/w/p","g","2/g","c/g","g/p","g/w","g/w/p","g/u","g/u/p","w","2/w","c/w","w/p","w/u","w/u/p","w/b","w/b/p","u","2/u","c/u","u/p","u/b","u/b/p","u/r","u/r/p","b","2/b","c/b","b/p","b/r","b/r/p","b/g","b/g/p","r","2/r","c/r","r/p","r/g","r/g/p","r/w","r/w/p","g","2/g","c/g","g/p"]
        distance_1_to_2, distance_2_to_1 = len(sorted_order), len(sorted_order)
        found_first_index = None
        for mi, mana_symbol in enumerate(sorted_order):
            if mana_symbol == mana_symbol_1:
                found_first_index = mi
            if mana_symbol == mana_symbol_2 and found_first_index is not None:
                distance_1_to_2 = mi - found_first_index
                break
        found_second_index = None
        for mi, mana_symbol in enumerate(sorted_order):
            if mana_symbol == mana_symbol_2:
                found_second_index = mi
            if mana_symbol == mana_symbol_1 and found_second_index is not None:
                distance_2_to_1 = mi - found_second_index
                break
        if found_first_index is None and found_second_index is None: # Two unrecognized symbols:
            return 0
        if found_first_index is None: # Unrecognized symbol always at the beginning
            return -1
        if found_second_index is None: # Unrecognized symbol always at the beginning
            return 1
        if distance_1_to_2 <= distance_2_to_1: # 1 comes before 2
            return -1 * distance_1_to_2
        else: # 2 comes before 1
            return distance_2_to_1
