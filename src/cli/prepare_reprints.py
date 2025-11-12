import os
import sys
import json
import shutil

from src.utils.paths import DECK_PATH

# NOTE: To make reprints recognize which card fronts pair with which card backs, separate the name of the card front and the card back using ' / '.

# Check if command-line argument for output directory name is provided
if len(sys.argv) < 2:
    print("No output directory provided. Using 'Reprints'.")
    output_directory_name = "Reprints"
else:
    output_directory_name = sys.argv[1]
output_dir = os.path.join(DECK_PATH, output_directory_name)

if not os.path.isdir(output_dir):
    os.mkdir(output_dir)

# Load reprints.json
with open(os.path.join(DECK_PATH, 'reprints.json'), 'r') as f:
    reprints_data = json.load(f)

# Get the total number of cards
total_cards = sum(len(cards) for cards in reprints_data.values())

# Iterate through each deck
card_counter = 0
for deck_name, cards in reprints_data.items():
    printing_path = os.path.join(DECK_PATH, deck_name, 'Printing')
    # Iterate through each card
    for card_name in cards:
        card_counter += 1
        front, _, back = card_name.partition(' / ')
        if back:  # If card has both front and back parts
            front_target_name = f"Front_{card_counter:0{len(str(total_cards))}}_{front}.jpg"
            back_target_name = f"Back_{card_counter:0{len(str(total_cards))}}_{back}.jpg"
            front_source_path = os.path.join(printing_path, f'{front}.jpg')
            back_source_path = os.path.join(printing_path, f'{back}.jpg')
            front_target_path = os.path.join(output_dir, front_target_name)
            back_target_path = os.path.join(output_dir, back_target_name)
            try:
                shutil.copyfile(front_source_path, front_target_path)
                shutil.copyfile(back_source_path, back_target_path)
            except Exception as e:
                print(f"Failed to copy '{front_source_path}' to '{front_target_path}'")
                print(f"Failed to copy '{back_source_path}' to '{back_target_path}'")
        else:  # If card has only front part
            target_name = f"Front_{card_counter:0{len(str(total_cards))}}_{card_name}.jpg"
            source_path = os.path.join(printing_path, f'{card_name}.jpg')
            target_path = os.path.join(output_dir, target_name)
            try:
                shutil.copyfile(source_path, target_path)
            except Exception as e:
                print(f"Failed to copy '{source_path}' to '{target_path}'")
