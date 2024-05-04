import os
import json
import shutil

from paths import DECK_PATH

output_dir = os.path.join(DECK_PATH, "Reprints")

if not os.path.isdir(output_dir):
    os.mkdir(output_dir)

# TODO -- allow a name for the reprints folder, defined as command line arg

# Load reprints.json
with open(os.path.join(DECK_PATH, 'reprints.json'), 'r') as f:
    reprints_data = json.load(f)

# Iterate through each deck
card_counter = 0
for deck_name, cards in reprints_data.items():
    printing_path = os.path.join(DECK_PATH, deck_name, 'Printing')
    # Iterate through each card
    for card_name in cards:
        card_counter += 1
        # Construct source and target paths
        source_path = os.path.join(printing_path, f'{card_name}.jpg')
        target_path = os.path.join(output_dir, f'{card_name}.jpg')
        # Copy the file
        try:
            shutil.copyfile(source_path, target_path)
        except:
            print(f"Failed to copy '{source_path}' to '{target_path}'")