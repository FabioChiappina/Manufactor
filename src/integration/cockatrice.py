"""
Cockatrice integration for exporting custom MTG cards.

Handles XML generation, deck file creation, and image copying for the
Cockatrice Magic: The Gathering simulator.
"""

import os
import json
import shutil
from random import randint
from src.core.deck import Deck
from src.core.card import Card
from src.core.card_set import CardSet
from src.utils.paths import DECK_PATH, COCKATRICE_PATH, COCKATRICE_MANUFACTOR_PATH, COCKATRICE_IMAGE_PATH, COCKATRICE_CUSTOMSETS_PATH, COCKATRICE_DECKS_PATH


# Updates the custom.xml file that Cockatrice uses to generate card information
# xml_filepath -- path to the custom.xml file used within Cockatrice.
# json_filepath -- path to the custom.json file used only to keep track of each different custom card. Since this is used to build custom.xml, if a card needs to be removed, it should be deleted from custom.json.
# replace_existing_custom_set -- If true and a file is found in Cockatrice/customsets/ named 01.custom.xml, that file is replaced, removing any existing custom cards. Otherwise, increments the last number found and saves a new file.
# replace_deck_files -- If true, replaces deck.cod files in Cockatrice/decks
def update_cockatrice(deck, xml_filepath=None, json_filepath=None, xml_filepath_tokens=None, json_filepath_tokens=None, replace_existing_custom_set=True, replace_deck_files=True):
    if not os.path.isdir(COCKATRICE_MANUFACTOR_PATH):
        os.mkdir(COCKATRICE_MANUFACTOR_PATH)
    if xml_filepath is None:
        xml_filepath = COCKATRICE_MANUFACTOR_PATH
    if not xml_filepath.endswith(".xml"):
        xml_filepath = os.path.join(xml_filepath, "custom.xml")
    xml_temp_filepath = os.path.join(COCKATRICE_MANUFACTOR_PATH, "customtemp.xml")
    if xml_filepath_tokens is None:
        xml_filepath_tokens = COCKATRICE_PATH
    if not xml_filepath_tokens.endswith(".xml"):
        xml_filepath_tokens = os.path.join(xml_filepath_tokens, "tokens.xml")
    xml_orig_filepath_tokens = os.path.join(COCKATRICE_MANUFACTOR_PATH, "tokens_original.xml")
    error_archiving_original_tokens = False
    if not os.path.isfile(xml_orig_filepath_tokens):
        try:
            shutil.copy(xml_filepath_tokens, xml_orig_filepath_tokens)
        except:
            error_archiving_original_tokens = True
            print("\nWARNING: Failed to archive original tokens.xml file in Cockatrice root directory. Cannot update Cockatrice with custom tokens.")
    xml_temp_filepath_tokens = os.path.join(os.path.dirname(xml_filepath_tokens), "tokenstemp.xml")
    if json_filepath is None:
        json_filepath = COCKATRICE_MANUFACTOR_PATH
    if not json_filepath.endswith(".json"):
        json_filepath = os.path.join(json_filepath, "custom.json")
    if json_filepath_tokens is None:
        json_filepath_tokens = COCKATRICE_MANUFACTOR_PATH
    if not json_filepath_tokens.endswith(".json"):
        json_filepath_tokens = os.path.join(json_filepath_tokens, "custom_tokens.json")
    setname = CardSet.adjust_forbidden_custom_setname((deck.name.lower().replace("the ",""))[0:3].upper())
    # Get any tokens that must be updated in Cockatrice
    try:
        tokens_deck = Deck.from_json(os.path.join(DECK_PATH, deck.name, deck.name+'_Tokens.json'), setname, deck.name+"_Tokens")
        tokens_cards = tokens_deck.cards   
    except Exception as e:
        tokens_cards = []
    if error_archiving_original_tokens:
        tokens_cards = []
    cdict = {} # Cards
    tdict = {} # Tokens
    all_token_names_this_deck = []
    for ci, card in enumerate(deck.cards + tokens_cards):
        duplicate_token_names = []
        if card.is_token():
            found_this_token = False
            this_card_name = setname+"_"+card.name
            tokens_with_this_name_paths = [] # Saved tokens paths (a list since some tokens can have duplicates, like MyToken_1.jpg)
            tokens_cockatrice_target_paths = [] # Paths in the cockatrice folder to which to copy the tokens
            base_path_this_token = os.path.join(DECK_PATH, deck.name, "Tokens", card.name+".jpg")
            if os.path.exists(base_path_this_token):
                duplicate_token_names.append(this_card_name.replace('"', '').replace("."," "))
                tokens_with_this_name_paths.append(base_path_this_token)
                tokens_cockatrice_target_paths.append(os.path.join(COCKATRICE_IMAGE_PATH, this_card_name.replace('"', '').replace("."," ")+".full.jpeg"))
                found_this_token = True
            this_token_counter = 1
            while True:
                incremented_token_path = os.path.join(DECK_PATH, deck.name, "Tokens", card.name+"_"+str(this_token_counter)+".jpg")
                if os.path.isfile(incremented_token_path):
                    duplicate_token_names.append(this_card_name.replace('"', '').replace("."," ")+"_"+str(this_token_counter))
                    tokens_with_this_name_paths.append(incremented_token_path)
                    tokens_cockatrice_target_paths.append(os.path.join(COCKATRICE_IMAGE_PATH, this_card_name.replace('"', '').replace("."," ")+"_"+str(this_token_counter)+".full.jpeg"))
                    found_this_token = True
                    this_token_counter += 1
                else:
                    break
            if not found_this_token:
                print(f"\nWARNING: Could not find any tokens with the name {card.name} in the tokens path:", os.path.join(DECK_PATH, deck.name, "Tokens"), "  This token's artwork was not added to Cockatrice.")
            for saved_token_path, target_cockatrice_token_path in zip(tokens_with_this_name_paths, tokens_cockatrice_target_paths):
                try:
                    shutil.copy(saved_token_path, target_cockatrice_token_path)
                except:
                    print("\nWARNING: Could not copy the image from the path " + saved_token_path + " to the Cockatrice path. This token's artwork was not added to Cockatrice. Check to make sure the image exists.")
            if len(duplicate_token_names)>0:
                all_token_names_this_deck += duplicate_token_names
        else:
            this_card_name = card.name
            current_image_path = os.path.join(DECK_PATH, deck.name, "Cards", card.name+".jpg")
            modified_this_card_name = this_card_name.replace('"', '').replace("."," ")
            try:
                shutil.copy(current_image_path, os.path.join(COCKATRICE_IMAGE_PATH, modified_this_card_name+".full.jpeg"))
            except:
                print("\nWARNING: Could not copy the image from the path " + current_image_path + " to the Cockatrice path. This card's artwork was not added to Cockatrice. Check to make sure the image exists.")
        name = (this_card_name).replace('"','&quot;').replace("."," ")
        if card.rules is None:
            text = ""
        else:
            text = (card.rules).replace('"','&quot;')
        coloridentity = "".join(card.colors).upper()
        side = "front"
        if card.special is not None and "back" in card.special:
            side = "back"
        fulltype = card.get_type_line()
        maintype = card.cardtype if type(card.supertype) is not str else card.supertype.title() + " " + card.cardtype.title()
        maintype = maintype.replace("Token ", "")
        if card.is_token():
            maintype = maintype.replace("Legendary ", "")
        cmc = str(card.get_mana_value())
        manacost = "" if card.mana is None else ((card.mana.replace("{","")).replace("}","")).upper()
        if card.is_token():
            frame_filename = os.path.basename(card.frame)
            if frame_filename is not None and len(frame_filename.split("_")[0])<=2:
                colors = frame_filename.split("_")[0].upper()
                if colors.lower() == "m":
                    colors = "WUBRG"
                elif colors.lower() == "c":
                    colors = None
            else:
                colors = None
        else:
            colors = coloridentity
        layout = "normal"
        if card.special == "transform-front" or card.special == "transform-back":
            layout = "transform"
        elif card.special == "mdfc-front" or card.special == "mdfc-back":
            layout = "modal_dfc"
        muid = str(randint(900000, 999999))
        uuid = "d41b07c8-f0c8-4654-" + str(randint(1000, 9999)) + "-" + str(randint(100000000000, 999999999999))
        rarity = "Common" if card.rarity is None else card.rarity
        # Format the .xml file using the appropriate attributes for each card.
        if card.is_token():
            for duplicate_token_name in duplicate_token_names:
                tdict[duplicate_token_name] =  '' 
                tdict[duplicate_token_name] += '        <card>\n'
                tdict[duplicate_token_name] += '            <name>' +duplicate_token_name+ '</name>\n'
                tdict[duplicate_token_name] += '            <text>' +text+ '</text>\n'
                tdict[duplicate_token_name] += '            <prop>\n'
                if (colors is not None) and len(colors)>0:
                    tdict[duplicate_token_name] += '                <colors>' +colors+ '</colors>\n'
                tdict[duplicate_token_name] += '                <type>' +fulltype+ '</type>\n'
                tdict[duplicate_token_name] += '                <maintype>' +maintype+ '</maintype>\n'
                tdict[duplicate_token_name] += '                <cmc>0</cmc>\n'
                tdict[duplicate_token_name] += '            </prop>\n'
                tdict[duplicate_token_name] += '            <set>' +setname+ '</set>\n'
                if (card.related is not None) and isinstance(card.related, list) and (len(card.related) > 0):
                    for this_related in card.related:
                        tdict[duplicate_token_name] += '            <reverse-related>' +this_related+ '</reverse-related>\n'
                tdict[duplicate_token_name] += '            <token>1</token>\n'
                tdict[duplicate_token_name] += '            <tablerow>2</tablerow>\n'
                tdict[duplicate_token_name] += '        </card>\n'
        else:
            cdict[card.name] =  '' 
            cdict[card.name] += '        <card>\n'
            cdict[card.name] += '            <name>' +name+ '</name>\n'
            cdict[card.name] += '            <text>' +text+ '</text>\n'
            cdict[card.name] += '            <prop>\n'
            cdict[card.name] += '                <format-penny>legal</format-penny>\n'
            cdict[card.name] += '                <coloridentity>' +coloridentity+ '</coloridentity>\n'
            cdict[card.name] += '                <format-pioneer>legal</format-pioneer>\n'
            cdict[card.name] += '                <side>' +side+ '</side>\n'
            cdict[card.name] += '                <type>' +fulltype+ '</type>\n'
            cdict[card.name] += '                <format-duel>legal</format-duel>\n'
            cdict[card.name] += '                <maintype>' +maintype+ '</maintype>\n'
            cdict[card.name] += '                <cmc>' +cmc+ '</cmc>\n'
            cdict[card.name] += '                <format-vintage>legal</format-vintage>\n'
            cdict[card.name] += '                <format-modern>legal</format-modern>\n'
            cdict[card.name] += '                <manacost>' +manacost+ '</manacost>\n'
            cdict[card.name] += '                <colors>' +colors+ '</colors>\n'
            cdict[card.name] += '                <format-legacy>legal</format-legacy>\n'
            cdict[card.name] += '                <layout>' +layout+ '</layout>\n'
            cdict[card.name] += '                <format-commander>legal</format-commander>\n'
            cdict[card.name] += '            </prop>\n'
            cdict[card.name] += '            <set muid="' +muid+ '" uuid="' +uuid+ '" num="' +str(ci+1)+ '" rarity="' +rarity+ '">' +setname+ '</set>\n'
            if (card.related is not None) and (card.related != ""):
                cdict[card.name] += '            <related attach="attach">' +card.related+ '</related>\n'
            cdict[card.name] += '            <tablerow>1</tablerow>\n'
            cdict[card.name] += '        </card>\n'
    # Update the custom.json and custom_tokens.json to contain all of the new (if any) card data in this deck:
    try:
        customjson = open(json_filepath)
        customdict_orig = json.load(customjson)
    except:
        customdict_orig = {}
    customdict_new = {}
    customdict_new.update(customdict_orig)
    customdict_new.update(cdict)
    with open(json_filepath, 'w') as f:
        json.dump(customdict_new, f)
    if not error_archiving_original_tokens:
        try:
            customjson_tokens = open(json_filepath_tokens)
            customdict_orig_tokens = json.load(customjson_tokens)
        except:
            customdict_orig_tokens = {}
        customdict_new_tokens = {}
        customdict_new_tokens.update(customdict_orig_tokens)
        customdict_new_tokens.update(tdict)
        with open(json_filepath_tokens, 'w') as f:
            json.dump(customdict_new_tokens, f)
    # Use the custom.json file to update the custom.xml file with the card data from this deck:
    with open(xml_filepath, 'r') as file_orig:
        with open(xml_temp_filepath, 'w') as file_new:
            found_set_name = 0
            for line in file_orig:
                if '<name>' +setname+ '</name>' in line:
                    found_set_name = 1
                if '</sets>' in line:
                    if found_set_name == 0:
                        file_new.write('        <set>\n')
                        file_new.write('            <name>' +setname+ '</name>\n')
                        file_new.write('            <longname>' +deck.name+ '</longname>\n')
                        file_new.write('            <settype>Promo</settype>\n')
                        file_new.write('            <releasedate>2022-09-07</releasedate>\n')
                        file_new.write('        </set>\n')
                file_new.write(line)
                if '<cards>' in line:
                    for cardname in customdict_new.keys():
                        file_new.write(customdict_new[cardname])
                    file_new.write('    </cards>\n')
                    file_new.write('</cockatrice_carddatabase>')
                    break
        file_new.close()
    file_orig.close()
    os.replace(xml_temp_filepath, xml_filepath)
    # Update cockatrice's internal custom.xml files to avoid needing to reload:
    xml_customsets_filename = "01.custom.xml"
    if not replace_existing_custom_set:
        customsets_iteration_number = 1
        while True:
            xml_customsets_filename = str(customsets_iteration_number).zfill(2)+".custom.xml"
            if os.path.isfile(os.path.join(COCKATRICE_CUSTOMSETS_PATH, xml_customsets_filename)):
                customsets_iteration_number += 1
            else:
                break
            if customsets_iteration_number == 100:
                print("\nWARNING: replacing 100.custom.xml!")
                break
    shutil.copy(xml_filepath, os.path.join(COCKATRICE_CUSTOMSETS_PATH, xml_customsets_filename))
    # Repeat for tokens
    if not error_archiving_original_tokens:
        with open(xml_orig_filepath_tokens, 'r') as file_orig:
            with open(xml_temp_filepath_tokens, 'w') as file_new:
                for line in file_orig:
                    # Insert custom tokens at the end of the tokens.xml file
                    if "</cards>" in line:
                        for cardname in customdict_new_tokens.keys():
                            file_new.write(customdict_new_tokens[cardname])
                    file_new.write(line)
            file_new.close()
        file_orig.close()
        os.replace(xml_temp_filepath_tokens, xml_filepath_tokens)
    # Create deck files:
    if replace_deck_files:
        cockatrice_deck_filename = os.path.join(COCKATRICE_DECKS_PATH, deck.name+".cod")
        with open(cockatrice_deck_filename, 'w') as cdeck:
            cdeck.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            cdeck.write('<cockatrice_deck version="1">\n')
            cdeck.write('    <deckname></deckname>\n')
            cdeck.write('    <comments></comments>\n')
            cdeck.write('    <zone name="main">\n')
            for cdeck_cardname in sorted([c.name.replace('"','&quot;').replace("."," ") for c in deck.cards if not ((c.special is not None) and ("back" in c.special.lower()))]):
                cdeck.write('        <card number="1" name="'+cdeck_cardname+'"/>\n')
            for basic_name, basic_count in deck.basics_dict.items():
                if basic_name.lower() not in Card.basic_lands:
                    continue
                cdeck.write('        <card number="'+str(basic_count)+'" name="'+basic_name.title().strip()+'"/>\n')
            cdeck.write('    </zone>\n')
            cdeck.write('    <zone name="tokens">\n')
            for cdeck_tokenname in sorted(all_token_names_this_deck):
                cdeck.write('        <card number="1" name="'+cdeck_tokenname+'"/>\n')
            for cdeck_common_tokenname in sorted(tokens_deck.common_tokens):
                cdeck.write('        <card number="1" name="'+cdeck_common_tokenname+' Token"/>\n')
            cdeck.write('    </zone>\n')
            cdeck.write('</cockatrice_deck>\n')
        cdeck.close()

