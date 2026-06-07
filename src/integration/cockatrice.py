"""
Cockatrice integration for exporting custom MTG cards.

Handles XML generation, deck file creation, and image copying for the
Cockatrice Magic: The Gathering simulator.
"""

import os
import json
import shutil
from random import randint
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
    # Prefer stored setname from deck metadata; fall back to auto-computing from name
    if deck.setname and deck.setname not in ('UNK', ''):
        setname = deck.setname
    else:
        setname = CardSet.adjust_forbidden_custom_setname((deck.name.lower().replace("the ",""))[0:3].upper())
    # Build token Card objects from deck.tokens dict (new format).
    # The legacy _Tokens.json sidecar no longer exists for web-UI-managed decks.
    tokens_cards = []
    for token_key, token_data in (deck.tokens or {}).items():
        if not isinstance(token_data, dict):
            continue
        token_card = Card(
            name=token_data.get('name', ''),
            cardtype=token_data.get('cardtype', 'Token Creature'),
            subtype=token_data.get('subtype') or None,
            rules=token_data.get('rules') or None,
            power=token_data.get('power') or None,
            toughness=token_data.get('toughness') or None,
            frame=token_data.get('frame') or None,
            colors=token_data.get('colors') or None,
            related=token_data.get('source_cards') or None,
            token=1,
            complete=token_data.get('complete', 0),
        )
        tokens_cards.append(token_card)
    cdict = {} # Cards
    tdict = {} # Tokens
    all_token_names_this_deck = []
    custom_prefixed_basics = set()  # basic land card names being registered under a setname prefix
    for ci, card in enumerate(deck.cards + tokens_cards):
        _is_custom_basic = False
        if getattr(card, 'real', 0):
            # Basic lands with a locally downloaded image: register as a prefixed custom card
            # (e.g. ANK_Plains) so each deck can have its own artwork in pics/CUSTOM/.
            if card.name.lower() in Card.basic_lands:
                _src = os.path.join(DECK_PATH, deck.folder_name, "Cards", card.name + ".jpg")
                if os.path.isfile(_src):
                    _is_custom_basic = True  # fall through to custom-card processing below
                else:
                    continue  # no chosen art — let Cockatrice use its default
            else:
                # Non-basic real card: copy locally downloaded image to CUSTOM so
                # Cockatrice displays the chosen printing art.
                safe_src_name = card.name.replace(' // ', ' -- ').replace('/', '-')
                _src = os.path.join(DECK_PATH, deck.folder_name, "Cards", safe_src_name + ".jpg")
                if os.path.isfile(_src):
                    _dst_name = card.name.replace('\u2019', "'").replace('\u2018', "'").replace('"', '').replace('.', ' ').replace("'", '').replace('?', '').replace(' // ', ' -- ').replace('/', '')
                    try:
                        shutil.copy(_src, os.path.join(COCKATRICE_IMAGE_PATH, _dst_name + ".full.jpeg"))
                    except Exception:
                        print(f"\nWARNING: Could not copy image for real card {card.name} to Cockatrice.")

                # For real MDFC/transform cards, also copy the back face image (if
                # downloaded) and fall through to add a custom XML entry with the
                # <related attach="attach"> element — without it Cockatrice can't
                # offer the flip option even though the card is in its built-in DB.
                if getattr(card, 'special', None) in ('mdfc-front', 'transform-front'):
                    _back_name = getattr(card, 'related', None)
                    if _back_name:
                        _back_safe = _back_name.replace('/', '-')
                        _back_src = os.path.join(DECK_PATH, deck.folder_name, "Cards", _back_safe + ".jpg")
                        if os.path.isfile(_back_src):
                            _back_dst = _back_name.replace('\u2019', "'").replace('\u2018', "'").replace('"', '').replace('.', ' ').replace("'", '').replace('?', '').replace(' // ', ' -- ').replace('/', '')
                            try:
                                shutil.copy(_back_src, os.path.join(COCKATRICE_IMAGE_PATH, _back_dst + ".full.jpeg"))
                            except Exception:
                                print(f"\nWARNING: Could not copy back face image for {_back_name} to Cockatrice.")
                    # Fall through to XML generation below (do NOT continue).
                else:
                    continue
        duplicate_token_names = []
        if card.is_token():
            found_this_token = False
            this_card_name = setname+"_"+card.name
            tokens_with_this_name_paths = [] # Saved tokens paths (a list since some tokens can have duplicates, like MyToken_1.jpg)
            tokens_cockatrice_target_paths = [] # Paths in the cockatrice folder to which to copy the tokens
            # Use folder_name for filesystem paths
            base_path_this_token = os.path.join(DECK_PATH, deck.folder_name, "Tokens", card.name+".jpg")
            if os.path.exists(base_path_this_token):
                duplicate_token_names.append(this_card_name.replace('"', '').replace("."," ").replace("?",""))
                tokens_with_this_name_paths.append(base_path_this_token)
                tokens_cockatrice_target_paths.append(os.path.join(COCKATRICE_IMAGE_PATH, this_card_name.replace('"', '').replace("."," ").replace("?","")+".full.jpeg"))
                found_this_token = True
            this_token_counter = 1
            while True:
                incremented_token_path = os.path.join(DECK_PATH, deck.folder_name, "Tokens", card.name+"_"+str(this_token_counter)+".jpg")
                if os.path.isfile(incremented_token_path):
                    duplicate_token_names.append(this_card_name.replace('"', '').replace("."," ").replace("?","")+"_"+str(this_token_counter))
                    tokens_with_this_name_paths.append(incremented_token_path)
                    tokens_cockatrice_target_paths.append(os.path.join(COCKATRICE_IMAGE_PATH, this_card_name.replace('"', '').replace("."," ").replace("?","")+"_"+str(this_token_counter)+".full.jpeg"))
                    found_this_token = True
                    this_token_counter += 1
                else:
                    break
            if not found_this_token:
                print(f"\nWARNING: Could not find any tokens with the name {card.name} in the tokens path:", os.path.join(DECK_PATH, deck.folder_name, "Tokens"), "  This token's artwork was not added to Cockatrice.")
                # Register without the setname prefix so Cockatrice can resolve
                # common tokens (Clue, Treasure, Food, etc.) from its built-in database.
                duplicate_token_names.append(card.name.replace('"', '').replace(".", " ").replace("?", ""))
            for saved_token_path, target_cockatrice_token_path in zip(tokens_with_this_name_paths, tokens_cockatrice_target_paths):
                try:
                    shutil.copy(saved_token_path, target_cockatrice_token_path)
                except:
                    print("\nWARNING: Could not copy the image from the path " + saved_token_path + " to the Cockatrice path. This token's artwork was not added to Cockatrice. Check to make sure the image exists.")
            if len(duplicate_token_names)>0:
                all_token_names_this_deck += duplicate_token_names
        else:
            if _is_custom_basic:
                this_card_name = setname + "_" + card.name
                custom_prefixed_basics.add(card.name)
            else:
                this_card_name = card.name
            # Use folder_name for filesystem paths
            # Match app.py's safe_card_filename: replace ' // ' with ' -- ' and '/' with '-'
            safe_cards_filename = card.name.replace(' // ', ' -- ').replace('/', '-')
            current_image_path = os.path.join(DECK_PATH, deck.folder_name, "Cards", safe_cards_filename+".jpg")
            # Cockatrice image filename: normalize Unicode apostrophes → straight, then strip all apostrophes
            modified_this_card_name = this_card_name.replace('\u2019',"'").replace('\u2018',"'").replace('"', '').replace("."," ").replace("?","").replace("'","").replace(" // ", " -- ").replace("/","")
            try:
                shutil.copy(current_image_path, os.path.join(COCKATRICE_IMAGE_PATH, modified_this_card_name+".full.jpeg"))
            except:
                print("\nWARNING: Could not copy the image from the path " + current_image_path + " to the Cockatrice path. This card's artwork was not added to Cockatrice. Check to make sure the image exists.")
        name = (this_card_name).replace('\u2019',"'").replace('\u2018',"'").replace('"','&quot;').replace("."," ").replace("'","").replace("?","").replace(" // ", " -- ")
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
                        normalized_related = this_related.replace('\u2019',"'").replace('\u2018',"'").replace('"','&quot;').replace("."," ").replace("'","").replace("?","").replace(" // ", " -- ")
                        tdict[duplicate_token_name] += '            <reverse-related>' + normalized_related + '</reverse-related>\n'
                elif (card.related is not None) and isinstance(card.related, str) and len(card.related) > 0:
                    normalized_related = card.related.replace('\u2019',"'").replace('\u2018',"'").replace('"','&quot;').replace("."," ").replace("'","").replace("?","").replace(" // ", " -- ")
                    tdict[duplicate_token_name] += '            <reverse-related>' + normalized_related + '</reverse-related>\n'
                tdict[duplicate_token_name] += '            <token>1</token>\n'
                tdict[duplicate_token_name] += '            <tablerow>2</tablerow>\n'
                tdict[duplicate_token_name] += '        </card>\n'
        else:
            cdict[this_card_name] =  '' 
            cdict[this_card_name] += '        <card>\n'
            cdict[this_card_name] += '            <name>' +name+ '</name>\n'
            cdict[this_card_name] += '            <text>' +text+ '</text>\n'
            cdict[this_card_name] += '            <prop>\n'
            cdict[this_card_name] += '                <format-penny>legal</format-penny>\n'
            cdict[this_card_name] += '                <coloridentity>' +coloridentity+ '</coloridentity>\n'
            cdict[this_card_name] += '                <format-pioneer>legal</format-pioneer>\n'
            cdict[this_card_name] += '                <side>' +side+ '</side>\n'
            cdict[this_card_name] += '                <type>' +fulltype+ '</type>\n'
            cdict[this_card_name] += '                <format-duel>legal</format-duel>\n'
            cdict[this_card_name] += '                <maintype>' +maintype+ '</maintype>\n'
            cdict[this_card_name] += '                <cmc>' +cmc+ '</cmc>\n'
            cdict[this_card_name] += '                <format-vintage>legal</format-vintage>\n'
            cdict[this_card_name] += '                <format-modern>legal</format-modern>\n'
            cdict[this_card_name] += '                <manacost>' +manacost+ '</manacost>\n'
            cdict[this_card_name] += '                <colors>' +colors+ '</colors>\n'
            cdict[this_card_name] += '                <format-legacy>legal</format-legacy>\n'
            cdict[this_card_name] += '                <layout>' +layout+ '</layout>\n'
            cdict[this_card_name] += '                <format-commander>legal</format-commander>\n'
            cdict[this_card_name] += '            </prop>\n'
            cdict[this_card_name] += '            <set muid="' +muid+ '" uuid="' +uuid+ '" num="' +str(ci+1)+ '" rarity="' +rarity+ '">' +setname+ '</set>\n'
            if (card.related is not None) and (card.related != ""):
                # For real DFC cards the back face will be a custom XML stub entry
                # (see below), so normalize the name to match that stub's <name>.
                # For all other cards use the raw related name as before.
                _is_real_dfc_front = (getattr(card, 'real', 0) and
                                      getattr(card, 'special', None) in ('mdfc-front', 'transform-front'))
                if _is_real_dfc_front:
                    _norm_back = (card.related
                                  .replace('\u2019', "'").replace('\u2018', "'")
                                  .replace('"', '').replace('.', ' ')
                                  .replace("'", '').replace('?', '').replace(' // ', ' -- ').replace('/', ''))
                    cdict[this_card_name] += '            <related attach="attach">' + _norm_back + '</related>\n'
                else:
                    cdict[this_card_name] += '            <related attach="attach">' +card.related+ '</related>\n'
            cdict[this_card_name] += '            <tablerow>1</tablerow>\n'
            cdict[this_card_name] += '        </card>\n'

            # For real MDFC/transform cards add a minimal back-face stub so that
            # Cockatrice resolves it through the custom XML (and thus looks for its
            # image in pics/CUSTOM/) rather than falling back to the built-in DB and
            # its internet-based image fetcher.
            _is_real_dfc_front = (getattr(card, 'real', 0) and
                                   getattr(card, 'special', None) in ('mdfc-front', 'transform-front')
                                   and card.related)
            if _is_real_dfc_front:
                _norm_back = (card.related
                              .replace('\u2019', "'").replace('\u2018', "'")
                              .replace('"', '').replace('.', ' ')
                              .replace("'", '').replace('?', '').replace(' // ', ' -- ').replace('/', ''))
                _back_layout = 'modal_dfc' if 'mdfc' in (card.special or '') else 'transform'
                # Derive back-face card type from the combined type string (part after ' // ')
                _combined_type = card.cardtype or ''
                _back_type_raw = _combined_type.split(' // ')[1].strip() if ' // ' in _combined_type else ''
                # Identify the primary (non-supertype) card type for <maintype>
                _back_maintype = next(
                    (ct.capitalize() for ct in Card.cardtypes if ct.lower() in _back_type_raw.lower()),
                    _back_type_raw.split()[0] if _back_type_raw else ''
                )
                _back_muid = str(randint(900000, 999999))
                _back_uuid = ("d41b07c8-f0c8-4654-" + str(randint(1000, 9999)) +
                              "-" + str(randint(100000000000, 999999999999)))
                cdict[_norm_back] = ''
                cdict[_norm_back] += '        <card>\n'
                cdict[_norm_back] += '            <name>' + _norm_back + '</name>\n'
                cdict[_norm_back] += '            <text></text>\n'
                cdict[_norm_back] += '            <prop>\n'
                cdict[_norm_back] += '                <format-penny>legal</format-penny>\n'
                cdict[_norm_back] += '                <coloridentity>' + coloridentity + '</coloridentity>\n'
                cdict[_norm_back] += '                <format-pioneer>legal</format-pioneer>\n'
                cdict[_norm_back] += '                <side>back</side>\n'
                if _back_type_raw:
                    cdict[_norm_back] += '                <type>' + _back_type_raw + '</type>\n'
                    cdict[_norm_back] += '                <format-duel>legal</format-duel>\n'
                    cdict[_norm_back] += '                <maintype>' + _back_maintype + '</maintype>\n'
                cdict[_norm_back] += '                <cmc>0</cmc>\n'
                cdict[_norm_back] += '                <format-vintage>legal</format-vintage>\n'
                cdict[_norm_back] += '                <format-modern>legal</format-modern>\n'
                cdict[_norm_back] += '                <manacost></manacost>\n'
                cdict[_norm_back] += '                <colors></colors>\n'
                cdict[_norm_back] += '                <format-legacy>legal</format-legacy>\n'
                cdict[_norm_back] += '                <layout>' + _back_layout + '</layout>\n'
                cdict[_norm_back] += '                <format-commander>legal</format-commander>\n'
                cdict[_norm_back] += '            </prop>\n'
                cdict[_norm_back] += ('            <set muid="' + _back_muid + '" uuid="' + _back_uuid +
                                      '" num="0" rarity="' + rarity + '">' + setname + '</set>\n')
                cdict[_norm_back] += '            <related>' + name + '</related>\n'
                cdict[_norm_back] += '            <tablerow>1</tablerow>\n'
                cdict[_norm_back] += '        </card>\n'
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
        commander_names = set(deck.commander) if deck.commander else set()
        non_back_cards = sorted([c for c in deck.cards if not ((c.special is not None) and ("back" in c.special.lower()))], key=lambda c: c.name)
        with open(cockatrice_deck_filename, 'w') as cdeck:
            cdeck.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            cdeck.write('<cockatrice_deck version="1">\n')
            cdeck.write('    <deckname></deckname>\n')
            cdeck.write('    <comments></comments>\n')
            cdeck.write('    <zone name="main">\n')
            for card in non_back_cards:
                if card.name in commander_names:
                    continue
                if card.name in custom_prefixed_basics:
                    cdeck_cardname = setname + "_" + card.name
                else:
                    cdeck_cardname = card.name.replace('\u2019',"'").replace('\u2018',"'").replace('"','&quot;').replace("."," ").replace("'","").replace("?","").replace(" // ", " -- ")
                qty = int(card.quantity) if (card.quantity and int(card.quantity) > 0) else 1
                cdeck.write('        <card number="'+str(qty)+'" name="'+cdeck_cardname+'"/>\n')
            for basic_name, basic_count in deck.basics_dict.items():
                if basic_name.lower() not in Card.basic_lands:
                    continue
                cdeck.write('        <card number="'+str(basic_count)+'" name="'+basic_name.title().strip()+'"/>\n')
            cdeck.write('    </zone>\n')
            cdeck.write('    <zone name="tokens">\n')
            for cdeck_tokenname in sorted(set(all_token_names_this_deck)):
                cdeck.write('        <card number="1" name="'+cdeck_tokenname+'"/>\n')
            cdeck.write('    </zone>\n')
            if commander_names:
                cdeck.write('    <zone name="side">\n')
                for card in [c for c in non_back_cards if c.name in commander_names]:
                    if card.name in custom_prefixed_basics:
                        cdeck_cardname = setname + "_" + card.name
                    else:
                        cdeck_cardname = card.name.replace('\u2019',"'").replace('\u2018',"'").replace('"','&quot;').replace("."," ").replace("'","").replace("?","").replace(" // ", " -- ")
                    qty = int(card.quantity) if (card.quantity and int(card.quantity) > 0) else 1
                    cdeck.write('        <card number="'+str(qty)+'" name="'+cdeck_cardname+'"/>\n')
                cdeck.write('    </zone>\n')
            cdeck.write('</cockatrice_deck>\n')
        cdeck.close()

