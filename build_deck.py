import os
import argparse
import string
import json
import shutil
from random import randint

import paths
import game_elements
import build_card

# Both creates the card images and the printing images.
def create_images_from_Deck(deck, save_path=None, skip_complete=True):
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
    for ci, card in enumerate(deck.cards):
        if card.complete and skip_complete:
            continue
        print("Building image for card", ci+1, "of", len(deck.cards), ":", card.name)
        build_card.create_card_image_from_Card(card, save_path=save_path)
        build_card.create_printing_image_from_Card(card, saved_image_path=save_path, save_path=printing_path)

# Updates the custom.xml file that Cockatrice uses to generate card information
# xml_filepath -- path to the custom.xml file used within Cockatrice.
# json_filepath -- path to the custom.json file used only to keep track of each different custom card. Since this is used to build custom.xml, if a card needs to be removed, it should be deleted from custom.json (possibly also from custom.json).
def update_cockatrice(deck, xml_filepath=None, json_filepath=None, image_path=paths.COCKATRICE_IMAGE_PATH):
    if xml_filepath is None:
        xml_filepath = os.path.dirname(paths.DECK_PATH)
    if not xml_filepath.endswith(".xml"):
        xml_filepath = os.path.join(xml_filepath, "custom.xml")
    xml_temp_filepath = os.path.join(os.path.dirname(xml_filepath), "customtemp.xml")
    if json_filepath is None:
        json_filepath = os.path.dirname(paths.DECK_PATH)
    if not json_filepath.endswith(".json"):
        json_filepath = os.path.join(json_filepath, "custom.json")
    setname = game_elements.Set.adjust_forbidden_custom_setname((deck.name.lower().replace("the ",""))[0:3].upper())
    cdict = {}
    for ci, card in enumerate(deck.cards):
        current_image_path = os.path.join(paths.DECK_PATH, deck.name, "Cards", card.name+".jpg")
        try:
            shutil.copy(current_image_path, os.path.join(paths.COCKATRICE_IMAGE_PATH, (card.name.replace('"', '').replace("."," "))+".full.jpeg"))
        except:
            print("\nWARNING -- could not copy the image from the path " + os.path.join(paths.DECK_PATH, deck.name, "Cards", card.name+".jpg") + " to the Cockatrice path -- check to make sure the image exists.")
        name = (card.name).replace('"','&quot;').replace("."," ")
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
        cmc = str(card.get_mana_value())
        if card.mana is None:
            manacost = ""
        else:
            manacost = ((card.mana.replace("{","")).replace("}","")).upper()
        colors = coloridentity
        layout = "normal"
        if card.special == "transform-front" or card.special == "transform-back":
            layout = "transform"
        elif card.special == "mdfc-front" or card.special == "mdfc-back":
            layout = "modal_dfc"
        muid = str(randint(900000, 999999))
        uuid = "d41b07c8-f0c8-4654-" + str(randint(1000, 9999)) + "-" + str(randint(100000000000, 999999999999))
        rarity = card.rarity
        # Format the .xml file using the appropriate attributes for each card.
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
    # Update the custom.json to contain all of the new (if any) card data in this deck:
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

def main():
    parser = argparse.ArgumentParser(description='MTG Custom Card Builder')
    parser.add_argument('-d', '--deck', help='Name of Commander / Deck', type=str, default='Test', dest='deck')
    args = parser.parse_args()
    deck_folder = os.path.join(paths.DECK_PATH, string.capwords(args.deck))
    print("BUILDING DECK: ", deck_folder, "\n")
    for directory in ["Cards", "Images", "Printing"]:
        if not os.path.isdir(os.path.join(deck_folder, directory)):
            os.mkdir(os.path.join(deck_folder, directory))
    deck = game_elements.Deck.from_deck_folder(deck_folder)
    deck.print_color_summary()
    deck.print_mana_summary()
    deck.print_type_summary()
    deck.print_tag_summary()
    create_images_from_Deck(deck)
    if deck.name != "Test":
        update_cockatrice(deck)

if __name__ == '__main__':
    main()