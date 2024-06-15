import os
import argparse
import string
import json
import shutil
from random import randint

import paths
import game_elements
import build_card

# Creates the card images (including tokens) and the printing images.
#   skip_complete -- If true, skips over creating the images for any cards with the complete flag set.
#   automatic_tokens -- If true, re-generates the _Tokens.json before generating images for the tokens. Otherwise, searches for an existing tokens JSON only.
def create_images_from_Deck(deck, save_path=None, skip_complete=True, automatic_tokens=True):
    if type(deck)!=game_elements.Deck:
        raise TypeError("Input deck must be of type Deck.")
    if save_path is None:
        save_path = os.path.join(paths.DECK_PATH, deck.name)
    if not os.path.isdir(save_path):
        os.mkdir(save_path)
    if not save_path.endswith("Cards"):
        save_path = os.path.join(save_path, "Cards")
    if not os.path.isdir(save_path):
        os.mkdir(save_path)
    printing_path = os.path.join(paths.DECK_PATH, deck.name, "Printing")
    if not os.path.isdir(printing_path):
        os.mkdir(printing_path)
    num_to_create = len([c for c in deck.cards if (not c.complete)]) if skip_complete else len(deck.cards)
    num_created_so_far = 0
    for card in deck.cards:
        if card.complete and skip_complete:
            continue
        num_created_so_far += 1
        print("Building image for card", num_created_so_far, "of", num_to_create, ":", card.name)
        build_card.create_card_image_from_Card(card, save_path=save_path)
        build_card.create_printing_image_from_Card(card, saved_image_path=save_path, save_path=printing_path)
    if automatic_tokens:
        deck.get_tokens()
    try:
        setname = (deck.name.lower().replace("the ",""))[0:3].upper()
        setname = game_elements.Set.adjust_forbidden_custom_setname(setname)
        tokens_deck = game_elements.Deck.from_json(os.path.join(paths.DECK_PATH, deck.name, deck.name+'_Tokens.json'), setname, deck.name+"_Tokens")
        tokens_path = os.path.join(paths.DECK_PATH, deck.name, "Tokens")
        if not os.path.isdir(tokens_path):
            os.mkdir(tokens_path)
        num_to_create = len([c for c in tokens_deck.cards if (not c.complete)]) if skip_complete else len(tokens_deck.cards)
        num_created_so_far = 0
        for card in tokens_deck.cards:
            if card.complete and skip_complete:
                continue
            num_created_so_far += 1
            print("Building image for token", num_created_so_far, "of", num_to_create, ":", card.name)
            build_card.create_card_image_from_Card(card, save_path=tokens_path)
            build_card.create_printing_image_from_Card(card, saved_image_path=tokens_path, save_path=printing_path)
    except:
        pass

# TODO -- should have the custom.json and custom_tokens.json files in their own cockatrice folder in the repo. Temp files can go there
# TODO -- custom.xml and TK.xml files should both just save directly to the cockatrice path. Already done with TK.xml
# Updates the custom.xml file that Cockatrice uses to generate card information
# xml_filepath -- path to the custom.xml file used within Cockatrice.
# json_filepath -- path to the custom.json file used only to keep track of each different custom card. Since this is used to build custom.xml, if a card needs to be removed, it should be deleted from custom.json.
def update_cockatrice(deck, xml_filepath=None, json_filepath=None, xml_filepath_tokens=None, json_filepath_tokens=None):
    if xml_filepath is None:
        xml_filepath = os.path.dirname(paths.DECK_PATH)
    if not xml_filepath.endswith(".xml"):
        xml_filepath = os.path.join(xml_filepath, "custom.xml")
    xml_temp_filepath = os.path.join(os.path.dirname(xml_filepath), "customtemp.xml")
    if xml_filepath_tokens is None:
        xml_filepath_tokens = paths.COCKATRICE_PATH
    if not xml_filepath_tokens.endswith(".xml"):
        xml_filepath_tokens = os.path.join(xml_filepath_tokens, "tokens.xml")
    xml_temp_filepath_tokens = os.path.join(os.path.dirname(xml_filepath_tokens), "tokenstemp.xml")
    if json_filepath is None:
        json_filepath = os.path.dirname(paths.DECK_PATH)
    if not json_filepath.endswith(".json"):
        json_filepath = os.path.join(json_filepath, "custom.json")
    if json_filepath_tokens is None:
        json_filepath_tokens = os.path.dirname(paths.DECK_PATH)
    if not json_filepath_tokens.endswith(".json"):
        json_filepath_tokens = os.path.join(json_filepath_tokens, "custom_tokens.json")
    setname = game_elements.Set.adjust_forbidden_custom_setname((deck.name.lower().replace("the ",""))[0:3].upper())
    # Get any tokens that must be updated in Cockatrice
    try:
        tokens_deck = game_elements.Deck.from_json(os.path.join(paths.DECK_PATH, deck.name, deck.name+'_Tokens.json'), setname, deck.name+"_Tokens")
        tokens_cards = tokens_deck.cards        
    except Exception as e:
        tokens_cards = []
    cdict = {} # Cards
    tdict = {} # Tokens
    for ci, card in enumerate(deck.cards + tokens_cards):
        if card.is_token():
            this_card_name = setname+"_"+card.name
            current_image_path = os.path.join(paths.DECK_PATH, deck.name, "Tokens", card.name+".jpg")
        else:
            this_card_name = card.name
            current_image_path = os.path.join(paths.DECK_PATH, deck.name, "Cards", card.name+".jpg")
        modified_this_card_name = this_card_name.replace('"', '').replace("."," ")
        try:
            shutil.copy(current_image_path, os.path.join(paths.COCKATRICE_IMAGE_PATH, modified_this_card_name+".full.jpeg"))
        except:
            print("\nWARNING -- could not copy the image from the path " + current_image_path + " to the Cockatrice path -- check to make sure the image exists.")
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
            tdict[card.name] =  '' 
            tdict[card.name] += '        <card>\n'
            tdict[card.name] += '            <name>' +name+ '</name>\n'
            tdict[card.name] += '            <text>' +text+ '</text>\n'
            tdict[card.name] += '            <prop>\n'
            if (colors is not None) and len(colors)>0:
                tdict[card.name] += '                <colors>' +colors+ '</colors>\n'
            tdict[card.name] += '                <type>' +fulltype+ '</type>\n'
            tdict[card.name] += '                <maintype>' +maintype+ '</maintype>\n'
            tdict[card.name] += '                <cmc>0</cmc>\n'
            tdict[card.name] += '            </prop>\n'
            tdict[card.name] += '            <set muid="' +muid+ '" uuid="' +uuid+ '" num="' +str(ci+1)+ '" rarity="' +rarity+ '">' +setname+ '</set>\n'
            if (card.related is not None) and isinstance(card.related, list) and (len(card.related) > 0):
                for this_related in card.related:
                    tdict[card.name] += '            <reverse-related>' +this_related+ '</reverse-related>\n'
            tdict[card.name] += '            <token>1</token>\n'
            tdict[card.name] += '            <tablerow>2</tablerow>\n'
            tdict[card.name] += '        </card>\n'
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
            # TODO just need to copy the TK.xml cards into tokens.xml, not too bad
    # Update the custom.json and custom_tokens.json to contain all of the new (if any) card data in this deck:
    try:
        customjson = open(json_filepath)
        customdict_orig = json.load(customjson)
    except:
        customdict_orig = {}
    customdict_new = {}
    customdict_new.update(customdict_orig)
    customdict_new.update(cdict)
    try:
        customjson_tokens = open(json_filepath_tokens)
        customdict_orig_tokens = json.load(customjson_tokens)
    except:
        customdict_orig_tokens = {}
    customdict_new_tokens = {}
    customdict_new_tokens.update(customdict_orig_tokens)
    customdict_new_tokens.update(tdict)
    with open(json_filepath, 'w') as f:
        json.dump(customdict_new, f)
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
    # Repeat for tokens

    with open(xml_filepath_tokens, 'w') as file_new:
        setup_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>\n',
            '<cockatrice_carddatabase version="4" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="https://raw.githubusercontent.com/Cockatrice/Cockatrice/master/doc/carddatabase_v4/cards.xsd">\n'
            '    <info>\n',
            '        <author>Cockatrice 2.8.0 (2021-01-26)</author>\n',
            '        <createdAt>2024-06-02T17:07:59Z</createdAt>\n',
            '        <sourceUrl>unknown</sourceUrl>\n',
            '        <sourceVersion>unknown</sourceVersion>\n',
            '    </info>\n',
            '    <sets>\n',
            '        <set>\n',
            '            <name>TK</name>\n',
            '            <longname>Dummy set containing tokens</longname>\n',
            '            <settype>Tokens</settype>\n',
            '            <releasedate></releasedate>\n',
            '        </set>\n',
            '    </sets>\n',
            '</cockatrice_carddatabase>\n'
        ]
        for li, line in enumerate(setup_lines):
            file_new.write(line)
            if "</sets>" in line:
                break
        file_new.write('    <cards>\n')
        for cardname in customdict_new_tokens.keys():
            file_new.write(customdict_new_tokens[cardname])
        file_new.write('    </cards>\n')
        file_new.write(setup_lines[-1])
    file_new.close()

def main():
    parser = argparse.ArgumentParser(description='MTG Custom Card Builder')
    parser.add_argument('-d', '--deck', help='Name of Commander / Deck', type=str, default='Test', dest='deck')
    parser.add_argument('-t', '--automatic-tokens', help='1 if _Tokens.json should be generated automatically', type=int, default=True, dest='automatic_tokens')
    args = parser.parse_args()
    deck_folder = os.path.join(paths.DECK_PATH, ' '.join(word[0].upper() + word[1:] for word in args.deck.split()))
    print("BUILDING DECK: ", deck_folder, "\n")
    for directory in ["Cards", "Artwork", "Printing"]:
        if not os.path.isdir(os.path.join(deck_folder, directory)):
            os.mkdir(os.path.join(deck_folder, directory))
    deck = game_elements.Deck.from_deck_folder(deck_folder)
    deck.print_color_summary()
    deck.print_mana_summary()
    deck.print_type_summary()
    deck.print_tag_summary()
    create_images_from_Deck(deck, automatic_tokens=args.automatic_tokens)
    if deck.name != "Test":
        update_cockatrice(deck)

if __name__ == '__main__':
    main()