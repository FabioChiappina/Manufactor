import os
import argparse

from src.core.deck import Deck
from src.core.card_set import CardSet
from src.rendering.card_renderer import create_card_image_from_Card, create_printing_image_from_Card
from src.integration.cockatrice import update_cockatrice
from src.utils.paths import DECK_PATH

# Creates the card images (including tokens) and the printing images.
#   skip_complete -- If true, skips over creating the images for any cards with the complete flag set.
#   automatic_tokens -- If true, re-generates the _Tokens.json before generating images for the tokens. Otherwise, searches for an existing tokens JSON only.
def create_images_from_Deck(deck, save_path=None, skip_complete=True, automatic_tokens=True):
    if type(deck)!=Deck:
        raise TypeError("Input deck must be of type Deck.")
    if save_path is None:
        save_path = os.path.join(DECK_PATH, deck.name)
    if not os.path.isdir(save_path):
        os.mkdir(save_path)
    if not save_path.endswith("Cards"):
        save_path = os.path.join(save_path, "Cards")
    if not os.path.isdir(save_path):
        os.mkdir(save_path)
    printing_path = os.path.join(DECK_PATH, deck.name, "Printing")
    if not os.path.isdir(printing_path):
        os.mkdir(printing_path)
    num_to_create = len([c for c in deck.cards if (not c.complete)]) if skip_complete else len(deck.cards)
    num_created_so_far = 0
    for card in deck.cards:
        if card.complete and skip_complete:
            continue
        num_created_so_far += 1
        print("Building image for card", num_created_so_far, "of", num_to_create, ":", card.name)
        create_card_image_from_Card(card, save_path=save_path)
        create_printing_image_from_Card(card, saved_image_path=save_path, save_path=printing_path)
    if automatic_tokens:
        deck.get_tokens()
    try:
        setname = (deck.name.lower().replace("the ",""))[0:3].upper()
        setname = CardSet.adjust_forbidden_custom_setname(setname)
        tokens_deck = Deck.from_json(os.path.join(DECK_PATH, deck.name, deck.name+'_Tokens.json'), setname, deck.name+"_Tokens")
        tokens_path = os.path.join(DECK_PATH, deck.name, "Tokens")
        if not os.path.isdir(tokens_path):
            os.mkdir(tokens_path)
        num_to_create = len([c for c in tokens_deck.cards if (not c.complete)]) if skip_complete else len(tokens_deck.cards)
        num_created_so_far = 0
        for card in tokens_deck.cards:
            if card.complete and skip_complete:
                continue
            num_created_so_far += 1
            print("Building image for token", num_created_so_far, "of", num_to_create, ":", card.name)
            create_card_image_from_Card(card, save_path=tokens_path)
            create_printing_image_from_Card(card, saved_image_path=tokens_path, save_path=printing_path)
    except:
        pass

def main():
    parser = argparse.ArgumentParser(description='MTG Custom Card Builder')
    parser.add_argument('-d', '--deck', help='Name of Commander / Deck', type=str, default='Test', dest='deck')
    parser.add_argument('-t', '--automatic-tokens', help='1 if _Tokens.json should be generated automatically', type=int, default=True, dest='automatic_tokens')
    args = parser.parse_args()
    deck_folder = os.path.join(DECK_PATH, ' '.join(word[0].upper() + word[1:] for word in args.deck.split()))
    print("BUILDING DECK: ", deck_folder, "\n")
    for directory in ["Cards", "Artwork", "Printing"]:
        if not os.path.isdir(os.path.join(deck_folder, directory)):
            os.mkdir(os.path.join(deck_folder, directory))
    deck = Deck.from_deck_folder(deck_folder)
    deck.print_color_summary()
    deck.print_mana_summary()
    deck.print_type_summary()
    deck.print_tag_summary()
    create_images_from_Deck(deck, automatic_tokens=args.automatic_tokens)
    if deck.name != "Test":
        update_cockatrice(deck)

if __name__ == '__main__':
    main()