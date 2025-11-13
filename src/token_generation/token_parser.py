"""
Token detection and generation from card rules text.

Automatically parses card rules text to identify and generate token cards
that are created by card abilities.
"""

import re
from num2words import num2words # type: ignore
from src.core.mana import Mana
from src.core.ability import AbilityElements


# This function is extracted from Card.get_tokens_from_rules_text()
# It will be called by Card class as Card.get_tokens_from_rules_text() for compatibility
def parse_tokens_from_rules_text(rules_text, card_name="", common_tokens_list=None, exclude_list=None, complete=0, Card=None):
    """
    Parse rules text to extract token definitions.
    
    Args:
        rules_text: The rules text to parse
        card_name: Name of the card creating the tokens (for related field)
        common_tokens_list: List of common token names to track separately
        exclude_list: List of token names to exclude
        complete: Whether the token is complete (1) or needs image generation (0)
    
    Returns:
        Tuple of (specialized_tokens, common_tokens) where:
        - specialized_tokens: List of dicts with token properties
        - common_tokens: List of common token names found
    """
    # Import Card here to avoid circular dependency
    if Card is None:
        from src.core.card import Card as CardClass
        Card = CardClass

    if common_tokens_list is None:
        common_tokens_list = ["Treasure", "Clue", "Food", "Blood", "Map", "Powerstone"]
    if exclude_list is None:
        exclude_list = ["Creature", "Noncreature", "Artifact", "Nonartifact", "Enchantment",
                       "Nonenchantment", "Land", "Nonland", "Planeswalker", "Nonplaneswalker",
                       "Battle", "Nonbattle"]

    # Main parsing logic
        # Helper function. Returns True if the input word (or pair of words) represents a numeric quantity -- e.g., "a", "an", "x", "one", "two", "three", "that many"
        # The second word is ignored except to compare the combination of word1 and word2 against "that many".
        def is_number_word(word1, word2=""):
            number_words = ["a", "an", "x"] + [num2words(n) for n in range(101)]
            return (word1.lower() in number_words) or ((word1.strip() + " " + word2.strip()).strip() == "that many")
        if rules_text is None or len(rules_text) == 0:
            return [], []
        specialized_tokens, common_tokens = [], []
        lines = rules_text.split("\n")
        colors_dict = {"white": "w", "blue": "u", "black": "b", "red": "r", "green": "g"}
        lines_queue = []
        first_loop_iteration = True
        lines_queue_index = 0
        while len(lines_queue)>0 or first_loop_iteration:
            first_loop_iteration = False
            if len(lines_queue)>0:
                lines_queue.pop(0)  # Remove the previously processed line from the last iteration
            if lines_queue_index < len(lines):
                lines_queue.append(lines[lines_queue_index])  # Append the next line to the queue
                lines_queue_index += 1
            if len(lines_queue)==0:
                break
            line = lines_queue[0]
            name = ""
            cardtype = ""
            subtype = ""
            power = ""
            toughness = ""
            rules = ""
            found_power_toughness = False
            original_words = line.split()
            words = [w.lower() for w in original_words]
            if not (("create" in words) or ("creates" in words)) or not (("token" in [w.replace(',','').replace('.','') for w in words]) or ("tokens" in [w.replace(',','').replace('.','') for w in words])):
                continue
            try:
                create_word_index = words.index("create")
            except:
                create_word_index = words.index("creates")
            words = words[create_word_index:]
            original_words = original_words[create_word_index:]
            create_word_index = 0
            try:
                token_word_index = [w.replace(',','').replace('.','') for w in words].index("token")
            except:
                token_word_index = [w.replace(',','').replace('.','') for w in words].index("tokens")
            try:
                with_word_index = words[token_word_index:].index("with") + token_word_index
                # If the word "with" is found after "token", we can expect to see rules text after "with".
                if any(["." in wti for wti in words[token_word_index:]]): # If there is a period after "token" and before "with", then the "with" is not specifying rules text.
                    period_index_after_token = next((ind for ind, val in enumerate(["." in wti for wti in words[token_word_index:]]) if val), None)
                    if period_index_after_token is not None and period_index_after_token < words[token_word_index:].index("with"):
                        with_word_index = None
            except:
                with_word_index = None
            if token_word_index < create_word_index:
                continue
            # If there's a period after the word "token", and the word "create" appears AFTER that period, separate those two parts of the line and process them as separate tokens.
            if any(['.' in wt for wt in words[token_word_index:]]):
                period_index_after_token = next((ind for ind, val in enumerate(["." in wti for wti in words[token_word_index:]]) if val), None)
                if (period_index_after_token is not None) and ("create" in words[token_word_index:]) and (period_index_after_token < words[token_word_index:].index("create")):
                    rest_of_line = original_words[token_word_index+period_index_after_token+1:]
                    rest_of_line = " ".join(rest_of_line)
                    lines_queue.append(rest_of_line)
                    words = words[0:token_word_index+period_index_after_token]
                    original_words = original_words[0:token_word_index+period_index_after_token]
            # If the word after "token"/"tokens" is "or", "and", "a", or "then", the rest of the line of text has nothing to do with this token. Ignore it and add to the lines queue.
            if (token_word_index+1 < len(words)) and ("." not in words[token_word_index]) and (words[token_word_index+1].lower() in ["and","or","a","then"]):
                if token_word_index+2 < len(words):
                    period_index_after_token = next((ind for ind, val in enumerate(["." in wti for wti in words[token_word_index+1:]]) if val), len(words[token_word_index+1:])) + token_word_index+1
                    # If the word "token"/"tokens" appears AGAIN before the next period, then the word "create" is appended to the rest of the line (after or/and/a/then), as another token is presumed to be created.
                    if (("token" in [wat.replace(',','').replace('.','') for wat in words[token_word_index+1:period_index_after_token+1]]) or ("tokens" in [wat.replace(',','').replace('.','') for wat in words[token_word_index+1:period_index_after_token+1]])):
                        if words[token_word_index+1].lower() in ["and","or","then"]:
                            rest_of_line = [original_words[token_word_index+1]] + ["create"] + original_words[token_word_index+2:]
                        else:
                            rest_of_line = ["create"] + original_words[token_word_index+1:]
                    else:
                        rest_of_line = original_words[token_word_index+1:]
                    rest_of_line = " ".join(rest_of_line)
                    lines_queue.append(rest_of_line)
                words = words[0:token_word_index+1]
                original_words = original_words[0:token_word_index+1]
            # Filter out token copies -- don't need their own files
            if ("token copy" in " ".join(original_words)) or ("token that's a copy" in " ".join(original_words)) or ("tokens that are copies" in " ".join(original_words)):
                continue
            # Extract name
            words_to_exclude_from_names_and_subtypes = ["Goaded", "Attach", "To", "That", "Many"]
            name_default_to_subtype = False
            if ("named" in words[create_word_index:]): # Check if "named" appears -- if so, the phrase that follows is the name.
                words_until_next_punctuation = []
                for index in range(words.index("named")+1, len(words)):
                    words_until_next_punctuation.append(words[index].replace(',','').replace('.','').replace("\"",""))
                    if (',' in words[index]) or ('.' in words[index]) or (words[index]=="with"):
                        if words[index]=="with":
                            del words_until_next_punctuation[-1]
                        break
                name = " ".join(words_until_next_punctuation).title()
            else:
                # Check if the word immediately following "create" is not a number word or "a", "an", or "and" -- if so, the phrase after "create" is the name
                if (create_word_index < len(words)-2) and not is_number_word(words[create_word_index + 1], words[create_word_index + 2]):
                    # The words between "create" and the next comma are the name of the token
                    words_until_next_comma = []
                    for index in range(create_word_index+1, len(words)):
                        words_until_next_comma.append(words[index].replace(',',''))
                        if ',' in words[index]:
                            break
                    name = " ".join(words_until_next_comma).title()
                else:
                    # If neither 1 nor 2 are true, no name is provided -- the name is equal to the subtypes
                    name = ""
                    name_default_to_subtype = True
            # Find a "number word" index -- the index of a word after create indicating a number of tokens to be made ("a", "an", "that many", "one", "two", ...)
            number_word_index = None
            for nwi in range(create_word_index + 1, token_word_index):
                if ((nwi<token_word_index-1) and is_number_word(words[nwi], words[nwi+1])) or ((nwi==token_word_index-1) and is_number_word(words[nwi])):
                    number_word_index = nwi
                    break
            number_word_index = create_word_index if (number_word_index is None) else number_word_index
            # Extract cardtype & subtype
            cardtype = " ".join([cardtype for cardtype in Card.cardtypes if (cardtype in [w.lower() for w in words[number_word_index:token_word_index]])]).title()
            if "token" not in cardtype.lower():
                cardtype = "Token "+cardtype
            if "legendary" in [w.lower() for w in words[number_word_index:token_word_index]]:
                cardtype = "Legendary "+cardtype
            cardtype = cardtype.strip()
            subtype = " ".join([word.lower().replace(",","").replace(".","") for word in words[number_word_index+1:token_word_index] if (("/" not in word) and 
                                                                                            (word.lower().replace(',','').replace('.','') != name.lower()) and
                                                                                            (word.lower().replace(',','').replace('.','') not in [we.lower() for we in words_to_exclude_from_names_and_subtypes]) and
                                                                                            (word.lower().replace(',','').replace('.','') not in Card.cardtypes) and
                                                                                            (word.lower().replace(',','').replace('.','') not in [num2words(n) for n in range(101)]) and
                                                                                            (word.lower().replace(',','').replace('.','') not in ["legendary", "colorless", "tapped", "x", "a", "an", "and"]) and
                                                                                            (word.lower().replace(',','').replace('.','') not in colors_dict.keys()))]).title()
            subtype = subtype.lower().replace("that many","").strip().title()
            subtype = subtype.replace("'S", "'s")
            name = name.replace("'S ", "'s ")
            if name_default_to_subtype:
                name = subtype
            elif subtype == name:
                subtype = ""
            name = name.strip()
            # Extract power and toughness
            for i, word in enumerate(words):
                if "/" in word:
                    power, toughness = word.split("/")
                    try:
                        int(power)
                        int(toughness)
                        if "+" not in power and "+" not in toughness and "-" not in power and "-" not in toughness:
                            found_power_toughness = True
                            break
                    except:
                        pass
            # Extract rules if the word "with" is present after the word "token" -- keep parsing rules until "." is found (outside of quotation marks)
            rules = ""
            if with_word_index is not None:
                words_until_next_period = []
                current_open_quote = False
                for index in range(with_word_index+1, len(original_words)):
                    defer_quote_flip = False
                    word_to_append = original_words[index]
                    if "\"" in word_to_append:
                        if "." in word_to_append and word_to_append.rfind(".")<word_to_append.index("\""):
                            defer_quote_flip = True
                        else:
                            current_open_quote = not current_open_quote
                    if (index == with_word_index+1) and len(word_to_append)>1:
                        word_to_append = word_to_append[0].upper() + word_to_append[1:]
                    if word_to_append.lower() == "named":
                        break
                    words_until_next_period.append(word_to_append)
                    if '.' in original_words[index] and not current_open_quote:
                        if defer_quote_flip:
                            current_open_quote = not current_open_quote
                        break
                # Postprocess the text after the word with in search of any of these phrases: "and a", "or a", ", a" -- these signal a new token and should be added to the lines queue
                before, after = None, None
                split_up_words_until_next_period = []
                last_split_index = 0
                for wri in range(len(words_until_next_period) - 1):
                    # Check for "and a" and "or a"
                    if (words_until_next_period[wri] == 'and' or words_until_next_period[wri] == 'or') and words_until_next_period[wri+1] == 'a':
                        before_end_index = wri
                    # Check for ", a"
                    elif words_until_next_period[wri].endswith(',') and words_until_next_period[wri+1] == 'a':
                        before_end_index = wri+1
                    else:
                        continue
                    before, after = words_until_next_period[last_split_index:before_end_index], words_until_next_period[wri+1:]
                    last_split_index = wri+1
                    split_up_words_until_next_period.append(before)
                if after is not None:
                    split_up_words_until_next_period.append(after)
                if len(split_up_words_until_next_period)>1:
                    split_up_words_until_next_period = [split_up_words_until_next_period[0]] + [["create"]+spl for spl in split_up_words_until_next_period[1:]]
                    words_until_next_period = split_up_words_until_next_period[0]
                    for splt in split_up_words_until_next_period[1:]:
                        lines_queue.append(" ".join(splt))
                rules = " ".join(words_until_next_period)            
            # Postprocess rules in search for abilities that can be broken up into new lines
            rules_split = rules.split("and \"")
            if len(rules_split)>1:
                rules = rules_split[0].strip()+"\n"+rules_split[1].strip().replace("\"","",1)
            rules = rules.replace(",\n","\n")
            # Postprocess rules again in search of keyword lists that can be better formatted
            rules_lines = rules.split("\n")
            postprocessed_rules = ""
            for ri, rules_line in enumerate(rules_lines):
                phrases = [phrase.strip() for phrase in rules_line.split(',')]
                found_phrase_too_long = False
                for phrase in phrases:
                    if len(phrase.split()) > 2:
                        found_phrase_too_long = True
                        break
                if found_phrase_too_long:
                    if ri > 0:
                        postprocessed_rules += "\n"
                    postprocessed_rules += rules_line
                    continue
                if len(phrases) > 1 and phrases[-1].startswith('and '):
                    phrases[-2] += ', ' + phrases[-1][4:]
                    del phrases[-1] 
                last_phrase = phrases[-1]
                if last_phrase.endswith('.'):
                    phrases[-1] = last_phrase[:-1]
                fixed_line = ', '.join(phrases)
                if ri > 0:
                    postprocessed_rules += "\n"
                postprocessed_rules += fixed_line
            rules = postprocessed_rules
            # One more postprocessing to catch KEYWORD1 and KEYWORD2 lines:
            rules_lines = rules.split("\n")
            postprocessed_rules = ""
            for ri, rules_line in enumerate(rules_lines):
                phrases = [phrase.strip() for phrase in rules_line.split(' and ')]
                found_phrase_too_long = False
                for phrase in phrases:
                    if len(phrase.split()) > 2 and not (phrase.split()[0].lower()=="protection" and phrase.split()[1].lower()=="from"):
                        found_phrase_too_long = True
                        break
                if found_phrase_too_long:
                    if ri > 0:
                        postprocessed_rules += "\n"
                    postprocessed_rules += rules_line
                    continue
                if len(phrases) > 1 and phrases[-1].startswith('and '):
                    phrases[-2] += ', ' + phrases[-1][4:]
                    del phrases[-1] 
                last_phrase = phrases[-1]
                if last_phrase.endswith('.'):
                    phrases[-1] = last_phrase[:-1]
                fixed_line = ', '.join(phrases)
                if ri > 0:
                    postprocessed_rules += "\n"
                postprocessed_rules += fixed_line
            rules = postprocessed_rules
            # One final postprocessing to remove starting/ending quotes:
            rules_lines = rules.split("\n")
            postprocessed_rules = ""
            for ri, rules_line in enumerate(rules_lines):
                if rules_line.startswith("\""):
                    if rules_line.endswith("\""):
                        rules_line = rules_line[1:-1]
                    elif  rules_line.endswith("\"."):
                        rules_line = rules_line[1:-2]
                if ri > 0:
                    postprocessed_rules += "\n"
                postprocessed_rules += rules_line
            rules = postprocessed_rules.replace("..",".")
            # If there's only a few words, and the final word in the line of text is an ability that needs elaborating, automatically provide the description
            if len(rules.split()) <= 6:
                if any([ability.name.lower().replace(" ","").replace(".","") == rules.split(",")[-1].lower().replace(" ","").replace(".","") for ability in AbilityElements.all_abilities]):
                    rules += " (" + AbilityElements.all_abilities_dict[rules.split(",")[-1].lower().replace(" ","").replace(".","")].selfDescription + ")"
            # Handle the special case of Roles
            if "Role" in subtype.split():
                subtype = "Aura Role"
                cardtype = "Token Enchantment"
                name = name.replace("Role", "").strip()
                rules = ""
                parentheses_re_match = re.search(r'\((.*?)\)', " ".join(original_words))
                if parentheses_re_match:
                    rules = parentheses_re_match.group(1)  # Extract the text within parentheses
                    rules = re.sub(re.escape("If you control another Role on it, put that one into the graveyard."), "", rules, flags=re.IGNORECASE).strip() # Remove Role rules text.
                    rules = re.sub(re.escape("that Role"), "this Role", rules, flags=re.IGNORECASE).strip() # Replace text referencing that Role with this Role.
                    rules = "Enchant creature\n" + rules
            # Extract colors:
            colors = [colors_dict[color] for color in colors_dict.keys() if (color in [w.lower().replace(',','').replace('.','') for w in words[number_word_index:token_word_index]])]
            colors = Mana.colors_to_wubrg_order(colors)
            dummy_card = Card(name=name,
                              mana="".join(["{"+c+"}" for c in colors]),
                              cardtype=cardtype,
                              subtype=subtype,
                              power=power if found_power_toughness else None,
                              toughness=toughness if found_power_toughness else None,
                              rules=rules,
                              colors=colors)
            frame_filename = dummy_card.get_frame_filename()
            # Create and return the dictionary
            this_token = {
                "name": name,
                "cardtype": cardtype,
                "subtype": subtype,
                "rules": rules,
                "complete": complete
            }
            if (card_name is not None) and len(card_name)>0:
                this_token["related"] = card_name
            if found_power_toughness:
                this_token["power"] = power
                this_token["toughness"] = toughness
            if frame_filename is not None and len(frame_filename)>0:
                this_token["frame"] = frame_filename
            if this_token["name"].lower() in [e.lower() for e in exclude_list]: # Explicitly excluded token
                continue
            if this_token["name"].lower() in [e.lower() for e in common_tokens_list]:
                common_tokens.append(name)
                continue
            if (this_token["cardtype"] == "Token"): # Invalid token -- no cardtype specified
                continue
            specialized_tokens.append(this_token)
        return specialized_tokens, common_tokens
