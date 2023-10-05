import os
import argparse
import string
import paths
import game_elements
import build_card

# Both creates the card images and the printing images.
def create_images_from_Deck(deck, save_path=None, skip_complete=True):
    if type(deck)!=game_elements.Deck:
        raise TypeError("Input deck must be of type Deck.")
    if save_path is None:
        save_path = os.path.join(paths.DECK_PATH, deck.name)
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
    # TODO 
    # cockatrice(card_dict, deck_folder)

if __name__ == '__main__':
    main()