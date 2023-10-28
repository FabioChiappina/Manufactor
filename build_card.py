import os
from PIL import Image, ImageDraw, ImageFont
import game_elements
from paths import ASSETS_PATH, SYMBOL_PATH, SET_SYMBOL_PATH, SAGA_SYMBOL_PATH, FONT_PATHS

POSITION_CARD_NAME  = (66,80)
POSITION_CARD_TYPE  = (66,611)
POSITION_TOKEN_CARD_TYPE = (66,POSITION_CARD_TYPE[1]+115)
POSITION_SAGA_CARD_TYPE = (66,POSITION_CARD_TYPE[1]+295)
POSITION_RULES_TEXT = (70,650)
POSITION_TOKEN_RULES_TEXT = (70,POSITION_RULES_TEXT[1]+110)
POSITION_SAGA_RULES_TEXT = (97,306)
POSITION_SET_SYMBOL = (634,593)
POSITION_TOKEN_SET_SYMBOL = (634,POSITION_SET_SYMBOL[1]+115)
POSITION_SAGA_SET_SYMBOL = (634,POSITION_SET_SYMBOL[1]+295)
POSITION_POWER      = (610,947)
POSITION_TOUGHNESS  = (651,947)
POSITION_MANA_SYMBOL = (648,61)
POSITION_FLAVOR_LINE = (82,None)
POSITION_SAGA_LINE = (84,None)
POSITION_SAGA_NUM_CHAPTERS = (250,232)
POSITION_SAGA_CHAPTER_SYMBOLS = (31,None)

MAX_HEIGHT_CARD_NAME  = 44.5
MAX_HEIGHT_CARD_TYPE  = 37.5
MAX_FONT_SIZE_RULES_TEXT_LETTERS = 37
MAX_HEIGHT_RULES_TEXT_BOX = 277 
MAX_HEIGHT_TOKEN_RULES_TEXT_BOX = 178
MAX_HEIGHT_SAGA_RULES_TEXT_BOX = 537
MAX_WIDTH_RULES_TEXT_BOX = 605
MAX_WIDTH_SAGA_RULES_TEXT_BOX = 255
MAX_WIDTH_CARD_NAME = 575
MAX_WIDTH_CARD_TYPE = 567
MAX_HEIGHT_POWER_TOUGHNESS = 39

CARD_WIDTH = 744
CARD_HEIGHT = 1039

SET_SYMBOL_SIZE = 40
MANA_SYMBOL_SIZE = 37
SPECIAL_SYMBOL_SIZE = 60

BLACK = (0, 0, 0)
WHITE = (255,255,255)

################################################################################
################################################################################

def create_card_image_from_Card(card, save_path=None):
    if type(card)!=game_elements.Card:
        raise TypeError("Input card must be of type Card.")
    card_draw = CardDraw(card, save_path=save_path)
    card_draw.write_name()
    card_draw.write_type_line()
    card_draw.write_rules_text()
    card_draw.paste_mana_symbols()
    card_draw.paste_set_symbol()
    card_draw.paste_artwork(artwork_path=os.path.join(os.path.dirname(save_path), "Images"))
    card_draw.write_power_toughness()
    card_draw.save()

def create_printing_image_from_Card(card, saved_image_path=None, save_path=None):
    if type(card)!=game_elements.Card:
        raise TypeError("Input card must be of type Card.")
    if saved_image_path is None:
        saved_image_path = card.name+".jpg"
    if not saved_image_path.endswith(card.name+".jpg"):
        saved_image_path = os.path.join(saved_image_path, card.name+".jpg")
    if save_path is None:
        save_path = card.name+"_printing.jpg"
    if not save_path.endswith(card.name+".jpg"):
        save_path = os.path.join(save_path, card.name+".jpg")
    image_bkg = Image.open(os.path.join(ASSETS_PATH, 'black_card.jpg'))
    image_card = Image.open(saved_image_path)
    shrink_ratio = 0.85
    image_card = image_card.resize((round(744*shrink_ratio),round(1039*shrink_ratio)))
    new_image = image_bkg.copy()
    new_image.paste(image_card, (round((1-shrink_ratio)/2 * 744), round((1-shrink_ratio)/2 * 1039)))
    xy = [(55,78),(55,106),(82,78)]
    draw = ImageDraw.Draw(new_image)
    draw.polygon(xy, fill ="black", outline ="black")
    xy = [(660,78),(690,106),(690,78)]
    draw = ImageDraw.Draw(new_image)
    draw.polygon(xy, fill ="black", outline ="black")
    xy = [(55,934),(55,962),(82,962)]
    draw = ImageDraw.Draw(new_image)
    draw.polygon(xy, fill ="black", outline ="black")
    xy = [(660,962),(690,934),(690,962)]
    draw = ImageDraw.Draw(new_image)
    draw.polygon(xy, fill ="black", outline ="black")
    if card.is_creature():
        xy = [(428,913),(428,947),(650,947),(650,913)]
        draw = ImageDraw.Draw(new_image)
        draw.polygon(xy, fill ="black", outline ="black")
    else:
        xy = [(428,900),(428,947),(650,947),(650,900)]
        draw = ImageDraw.Draw(new_image)
        draw.polygon(xy, fill ="black", outline ="black")
    new_image.save(save_path)

################################################################################
################################################################################
# Modified from the ImageText object created by Alvaro Justen:
# Copyright 2011 Álvaro Justen [alvarojusten at gmail dot com]
# License: GPL <http://www.gnu.org/copyleft/gpl.html>
# # https://gist.github.com/turicas/1455973

class CardDraw(object):
    def __init__(self, card, filename=None, save_path=None):
        if type(card)!=game_elements.Card:
            raise TypeError("Could not create a new CardDraw object. Input card must be of type Card.")
        self.card = card
        if filename is None:
            filename = card.name+".jpg"
        self.filename = filename
        if save_path is None:
            save_path = filename
        elif not save_path.endswith(".jpg"):
            save_path = os.path.join(save_path, self.filename)
        self.save_path = save_path
        self.image = Image.open(self.card.frame)
        self.size = self.image.size
        self.draw = ImageDraw.Draw(self.image)

    def save(self, save_path=None):
        self.image.save(save_path or self.save_path)

    def get_text_size(self, font_filename, font_size, text):
        font = ImageFont.truetype(font_filename, font_size)
        _, _, x, y = font.getbbox(text)
        return (x,y)

    def get_font_size(self, text, font, max_width=None, max_height=None, min_font_size=1):
        if max_width is None and max_height is None:
            raise ValueError('You need to pass max_width or max_height')
        font_size = min_font_size
        text_size = self.get_text_size(font, font_size, text)
        if (max_width is not None and text_size[0] > max_width) or \
           (max_height is not None and text_size[1] > max_height):
            raise ValueError("Text can't be filled in only (%dpx, %dpx)" % \
                    text_size)
        while True:
            if (max_width is not None and text_size[0] >= max_width) or \
               (max_height is not None and text_size[1] >= max_height):
                return min(int(max_height), font_size - 1)
            font_size += 1
            text_size = self.get_text_size(font, font_size, text)

    # Writes a single line of text:
    def write_text(self, position, text, font_filename, font_size="fill", color=BLACK, max_width=None, max_height=None, adjust_for_below_letters=False, x_centered=False, y_centered=True, return_symbol_positions=False):
        if font_size == 'fill' and (max_width is not None or max_height is not None):
            font_size = self.get_font_size(text, font_filename, max_width, max_height)
        text_size = self.get_text_size(font_filename, font_size, text)
        font = ImageFont.truetype(font_filename, font_size)
        if position == 'center':
            x = (self.size[0] - text_size[0]) / 2
            y = (self.size[1] - text_size[1]) / 2
        elif type(position)==tuple or type(position)==list:
            x,y = position
        else:
            raise ValueError("Position must be a tuple/list or 'center'.")
        if x_centered:
            x -= text_size[0]/2
        if y_centered:
            y -= text_size[1]/2
        if adjust_for_below_letters:
            letters_slightly_below = ['I', 'P']
            letters_mid_below = ['G', 'H', 'J', 'j', 'y']
            letters_very_below = ['F', 'K', 'Q', 'R', 'g', 'p', 'q']
            adjustment_weight_slight, adjustment_weight_mid, adjustment_weight_very = 0.025, 0.065, 0.11
            # If any of the very below letters are present, don't raise the y-value at all:
            if any([l in text for l in letters_very_below]):
                pass
            # If none of the very below lettesr are present, but some of the mid below letters are present, raise the y-value slightly:
            elif any([l in text for l in letters_mid_below]):
                y -= text_size[1]*adjustment_weight_slight
            # If none of the very or mid below letters are present, but some of the slightly below letters are present, raise the y-value a medium amount:
            elif any([l in text for l in letters_slightly_below]):
                y -= text_size[1]*adjustment_weight_mid
            # If none of the slightly/mid/very below letters are present, raise the y-value significantly:  
            else:
                y -= text_size[1]*adjustment_weight_very
        self.draw.text((x, y), text, font=font, fill=color)
        if return_symbol_positions:
            symbol_positions = []
            for i, char in enumerate(text):
                if char=="○":
                    size_so_far = self.get_text_size(font_filename, font_size, text[0:i-1])
                    symbol_positions.append((int(x+size_so_far[0]), int(y)))
            return text_size, symbol_positions
        else:
            return text_size

    # TODO -- within flavor text, support non-italicized words
    # TODO -- support manual italics and parenthesis italics. Would need to just find what line it starts on and call write_text twice with diff fonts. Then do the same for lines it ends on. Lines in the middle can all be italics.
    def write_rules_text(self, font_size='fill', color=BLACK, place='left'):
        font_filename, font_filename_flavor = FONT_PATHS["rules"], FONT_PATHS["flavor"]
        text, text_flavor = self.card.rules, self.card.flavor
        if self.card.is_saga():
            max_width = MAX_WIDTH_SAGA_RULES_TEXT_BOX
        else:
            max_width = MAX_WIDTH_RULES_TEXT_BOX
        if (text is None or len(text)==0) and text_flavor is not None:
            text = text_flavor
            font_filename = font_filename_flavor
            text_flavor = None
        elif self.card.is_saga():
            all_chapter_texts = [self.card.rules1, self.card.rules2, self.card.rules3, self.card.rules4, self.card.rules5, self.card.rules6]
            unique_chapter_groups = [] # Each element contains unique text. If all chapters are unique, this has the same length as the number of chapters.
            unique_chapter_group_numbers = [] # Element i contains the chapter numbers (1-6) that have the text of the ith element of unique_chapter_groups.
            num_chapters = sum([ctext is not None for ctext in all_chapter_texts])
            num_chapters_image = Image.open(os.path.join(SAGA_SYMBOL_PATH, str(num_chapters)+".jpg"))
            self.image.paste(num_chapters_image, POSITION_SAGA_NUM_CHAPTERS)
            for ci, chapter_text in enumerate(all_chapter_texts):
                if chapter_text is None:
                    break
                if chapter_text not in unique_chapter_groups:
                    unique_chapter_groups.append(chapter_text)
                    unique_chapter_group_numbers.append([ci+1])
                else:
                    unique_chapter_group_numbers[unique_chapter_groups.index(chapter_text)].append(ci+1)
            text = ""
            for ci, chapter_text in enumerate(unique_chapter_groups):
                if chapter_text is not None:
                    text += chapter_text
                    if ci!=len(unique_chapter_groups)-1:
                        text += "\n\n"
            text_flavor = None
        elif text is None and text_flavor is None:
            return
        if self.card.is_token():
            max_height = MAX_HEIGHT_TOKEN_RULES_TEXT_BOX
            x,y = POSITION_TOKEN_RULES_TEXT
        elif self.card.is_saga():
            max_height = MAX_HEIGHT_SAGA_RULES_TEXT_BOX
            x,y = POSITION_SAGA_RULES_TEXT
        else:
            max_height = MAX_HEIGHT_RULES_TEXT_BOX
            x,y = POSITION_RULES_TEXT
        if font_size == 'fill':
            fill = True
            font_size = self.get_font_size(text, font_filename, max_height=MAX_FONT_SIZE_RULES_TEXT_LETTERS, max_width=MAX_WIDTH_RULES_TEXT_BOX)
        else:
            fill = False
        text_blocks = text.split('\n')
        if text_flavor is None:
            flavor_block_index = None
        else:
            flavor_block_index = len(text_blocks)
            text_blocks_flavor = text_flavor.split('\n')
            text_blocks += text_blocks_flavor
        if self.card.is_saga():
            saga_separator_indices = list(range(len(text_blocks)))[1::2]
        # Need to replace all of the possible symbols with  ○ , and need to record which character number in the string that is.
        list_of_symbols = []
        for ti, text_block in enumerate(text_blocks):
            tokenized_text_block = text_block.split()
            retokenized_text_block = []
            for token in tokenized_text_block:
                if "{" not in token:
                    retokenized_text_block.append(token)
                    continue
                prev_bracket = None
                token_replaced = ""
                for index, c in enumerate(token):
                    if c=='{':
                        prev_bracket = index
                    if prev_bracket is None:
                        token_replaced += c # Handles non-symbol characters (e.g., periods, commas, colons...)
                    if prev_bracket is not None and index > 0 and index < len(token) and c=="}":
                        found_symbol = token[prev_bracket:index+1]
                        if found_symbol in game_elements.all_symbols_bracketed:
                            list_of_symbols.append(found_symbol.replace("{", "").replace("}", ""))
                            token_replaced += " ○ "
                            prev_bracket = None
                        else:
                            token_replaced += found_symbol
                token_replaced = token_replaced.replace("  ", " ")
                retokenized_text_block.append(token_replaced)
            text_blocks[ti] = " ".join(retokenized_text_block)
        # Now have replaced all symbols with ○ , and have a list for each text block of the original symbols. We can use those lists to paste images as we call write_text.
        total_height = 1e11
        first_box_fill_attempt = True
        text_lines = []
        flavor_block_line_index = None
        while total_height > max_height:
            if not first_box_fill_attempt:
                font_size -= 1
            text_height = self.get_text_size(font_filename, font_size, "j")[1]
            text_height_flavor = self.get_text_size(font_filename_flavor, font_size, "j")[1]
            saga_separator_line_indices = []
            text_lines = []
            cumulative_text_height = text_height
            for ti, this_text_block in enumerate(text_blocks):
                while True:
                    lines = []
                    line = []
                    words = this_text_block.split()
                    # Preprocess the split words to combine all of the symbols into a single word:
                    words_adjusted_for_symbols = []
                    last_symbol_seen = None
                    for wi, word in enumerate(words):
                        if word != "○":
                            if last_symbol_seen is not None:
                                words_adjusted_for_symbols.append(" " + "  ".join(words[last_symbol_seen:wi])+(" " if ((wi<len(words)-1) and (words[wi] not in [".",",",":"]))else "")) # Need an extra space after?
                                last_symbol_seen = None
                            words_adjusted_for_symbols.append(word)
                            continue
                        if last_symbol_seen is None:
                            last_symbol_seen = wi
                        if wi==len(words)-1:
                            words_adjusted_for_symbols.append(" " + "  ".join(words[last_symbol_seen:]))
                    # One more pass through the adjusted words, combining any symbols with following punctuation:
                    words_readjusted = []
                    previous_word_is_symbol = False
                    for word in words_adjusted_for_symbols:
                        if previous_word_is_symbol and word in [".",",",":"]:
                            words_readjusted[-1] = words_readjusted[-1] + " " + word
                        else:
                            words_readjusted.append(word)
                        previous_word_is_symbol = "○" in word
                    words = words_readjusted.copy()
                    for word in words:
                        reached_creature_pt_box = self.card.is_creature() and (cumulative_text_height > (MAX_HEIGHT_RULES_TEXT_BOX-50))
                        new_line = ' '.join(line + [word])
                        size = self.get_text_size(font_filename, font_size, new_line)
                        this_max_width = max_width-80 if reached_creature_pt_box else max_width # Ensures the rules text doesn't run into the power/toughness box
                        if size[0] <= this_max_width:
                            line.append(word)
                        else:
                            cumulative_text_height += text_height
                            lines.append(line)
                            line = [word]
                    if line:
                        cumulative_text_height += text_height
                        reached_creature_pt_box = self.card.is_creature() and (cumulative_text_height > (MAX_HEIGHT_RULES_TEXT_BOX-50))
                        lines.append(line)
                    if font_size >= MAX_FONT_SIZE_RULES_TEXT_LETTERS:
                        break
                    elif fill and ti==0 and first_box_fill_attempt:
                        font_size += 1
                        cumulative_text_height = text_height
                    else:
                        break
                if ti == flavor_block_index:
                    cumulative_text_height += text_height
                    text_height = text_height_flavor
                    flavor_block_line_index = len(text_lines)
                    text_lines += [" "]
                elif self.card.is_saga() and ti in saga_separator_indices:
                    saga_separator_line_indices.append(len(text_lines))
                    text_lines += [" "]
                text_lines += [' '.join(line) for line in lines if line]
                if ti != len(text_blocks)-1 and (True if flavor_block_index is None else ti < flavor_block_index):
                    cumulative_text_height += text_height/2
                    text_lines += [""]
            text_height = self.get_text_size(font_filename, font_size, "j")[1]
            total_height = len(text_lines)*text_height - (0.5*text_height)*len([t for t in text_lines if t==""])
            if not fill:
                break
            first_box_fill_attempt = False
        if max_height > total_height:
            if self.card.is_saga():
                y += (max_height - total_height) / 3
                y -= 3
            else:
                y += (max_height - total_height) / 2
                y -= 3
        height = y
        list_of_symbol_positions = []
        symbol_size = self.get_text_size(font_filename, font_size, "I")[1]
        flavor_line_position = None
        saga_line_positions = []
        for index, line in enumerate(text_lines):
            total_size = self.get_text_size(font_filename, font_size, line)
            if line=="":
                height += text_height/2
            elif line==" ":
                height += text_height
            else:
                height += text_height
            if index == flavor_block_line_index:
                font_filename = font_filename_flavor
                flavor_line_position = (POSITION_FLAVOR_LINE[0], int(height-text_height/4))
            elif self.card.is_saga() and index in saga_separator_line_indices:
                saga_line_positions.append((POSITION_SAGA_LINE[0], int(height)))
            if place == 'left':
                _, symbol_positions = self.write_text((x, height), line, font_filename, font_size, color, return_symbol_positions=True)
            elif place == 'right':
                x_left = x + max_width - total_size[0]
                _, symbol_positions = self.write_text((x_left, height), line, font_filename, font_size, color, return_symbol_positions=True)
            elif place == 'center':
                x_left = int(x + ((max_width - total_size[0]) / 2))
                _, symbol_positions = self.write_text((x_left, height), line, font_filename, font_size, color, return_symbol_positions=True)
            list_of_symbol_positions += [(s[0], s[1]+int(0.1*symbol_size)) for s in symbol_positions]
        self.paste_in_text_symbols(list_of_symbols, list_of_symbol_positions, symbol_size)
        # Paste the line between text and flavor text:
        if flavor_line_position is not None:
            flavor_line_image = Image.open(os.path.join(ASSETS_PATH, "flavor_line.png"))
            self.image.paste(flavor_line_image, flavor_line_position, flavor_line_image)
        # Paste the lines between Saga chapters:
        if len(saga_line_positions)>0:
            saga_line_image = Image.open(os.path.join(ASSETS_PATH, "saga_line.png"))
            for saga_line_position in saga_line_positions:
                self.image.paste(saga_line_image, saga_line_position, saga_line_image)
        # Paste Saga chapter symbols:
        if self.card.is_saga():
            single_saga_symbol_height = 65
            y_bounds = [POSITION_SAGA_RULES_TEXT[1]-3] + [slp[1] for slp in saga_line_positions] + [POSITION_SAGA_RULES_TEXT[1]+MAX_HEIGHT_SAGA_RULES_TEXT_BOX-20-46*(len(unique_chapter_group_numbers)==1)]
            y_bounds_by_group = []
            for gi, group_numbers in enumerate(unique_chapter_group_numbers):
                y_bounds_by_group.append((y_bounds[gi],y_bounds[gi+1]))
                group_center_ypos = (y_bounds_by_group[gi][0]+y_bounds_by_group[gi][1])/2
                this_group_ypos = int(group_center_ypos - (single_saga_symbol_height * len(group_numbers))/2)
                for gnum in group_numbers:
                    saga_chapter_symbol_image = Image.open(os.path.join(SAGA_SYMBOL_PATH, "ch"+str(gnum)+".png"))
                    self.image.paste(saga_chapter_symbol_image, (POSITION_SAGA_CHAPTER_SYMBOLS[0], this_group_ypos), saga_chapter_symbol_image)
                    this_group_ypos += single_saga_symbol_height + 4 + 4*(len(unique_chapter_group_numbers)==1)
        return (max_width, height - y)

    def write_name(self):
        mdfc_or_transform = self.card.special is not None and (("mdfc" in self.card.special) or ("transform" in self.card.special))
        position = (POSITION_CARD_NAME[0]+ SPECIAL_SYMBOL_SIZE, POSITION_CARD_NAME[1]) if mdfc_or_transform else POSITION_CARD_NAME
        position = (position[0]+(int(CARD_WIDTH/2)-POSITION_CARD_NAME[0] if self.card.is_token() else 0), position[1])
        max_width = MAX_WIDTH_CARD_NAME - (0 if self.card.mana is None else self.card.mana.count("{")*MANA_SYMBOL_SIZE) - (SPECIAL_SYMBOL_SIZE if mdfc_or_transform else 0)
        if self.card.is_token():
            color = WHITE
        elif self.card.special is not None and "back" in self.card.special:
            color = WHITE
        else:
            color = BLACK
        font_filename = FONT_PATHS["token"] if self.card.is_token() else FONT_PATHS["name"]
        x_centered = self.card.is_token()
        self.write_text(position, self.card.name, font_filename=font_filename, font_size='fill', max_height=MAX_HEIGHT_CARD_NAME, max_width=max_width, adjust_for_below_letters=1, x_centered=x_centered, color=color)

    def write_type_line(self):
        if self.card.special is not None and "back" in self.card.special:
            color = WHITE
        else:
            color = BLACK
        if self.card.is_token():
            position = POSITION_TOKEN_CARD_TYPE
        elif self.card.is_saga():
            position = POSITION_SAGA_CARD_TYPE
        else:
            position = POSITION_CARD_TYPE
        self.write_text(position, self.card.get_type_line(), font_filename=FONT_PATHS["name"], font_size='fill', max_height=MAX_HEIGHT_CARD_TYPE, max_width=MAX_WIDTH_CARD_TYPE, adjust_for_below_letters=1, color=color)

    def write_power_toughness(self):
        if self.card.is_vehicle():
            color = WHITE
        elif self.card.special is not None and "back" in self.card.special:
            color = WHITE
        else:
            color = BLACK
        maxpt = max(0 if self.card.power is None else int(self.card.power), 0 if self.card.toughness is None else int(self.card.toughness))
        minpt = min(0 if self.card.power is None else int(self.card.power), 0 if self.card.toughness is None else int(self.card.toughness))
        max_height = MAX_HEIGHT_POWER_TOUGHNESS-3 if (maxpt >= 10 and minpt < 10) else MAX_HEIGHT_POWER_TOUGHNESS
        if self.card.power is not None:
            self.write_text(POSITION_POWER if int(self.card.power)<10 else (POSITION_POWER[0]-15, POSITION_POWER[1]), self.card.power, font_filename=FONT_PATHS["name"], font_size='fill', max_height=max_height, max_width=MAX_HEIGHT_POWER_TOUGHNESS, adjust_for_below_letters=0, color=color)
        if self.card.toughness is not None:
            self.write_text(POSITION_TOUGHNESS, self.card.toughness, font_filename=FONT_PATHS["name"], font_size='fill', max_height=max_height, max_width=MAX_HEIGHT_POWER_TOUGHNESS, adjust_for_below_letters=0, color=color)

    def paste_in_text_symbols(self, symbols, symbol_positions, symbol_size, shadow=False):
        symbols = [os.path.join(SYMBOL_PATH, symbol.replace('/','')+".png") for symbol in symbols]
        for symbol, symbol_position in zip(symbols, symbol_positions):
            if shadow:
                shadow_image = Image.open(os.path.join(SYMBOL_PATH, "black.png"))
                shadow_image = shadow_image.resize((symbol_size, symbol_size))
                self.image.paste(shadow_image, (symbol_position[0]-1, symbol_position[1]+3), shadow_image)
            mana_image = Image.open(symbol)
            mana_image = mana_image.resize((symbol_size, symbol_size))
            self.image.paste(mana_image, symbol_position, mana_image)

    def paste_mana_symbols(self):
        if self.card.mana is None or len(self.card.mana)==0:
            return
        mana_symbols = [m.replace('}','').replace('/','') for m in self.card.mana.split('{')]
        mana_symbol_paths = [os.path.join(SYMBOL_PATH, symbol+".png") for symbol in mana_symbols if (len(symbol)!=0 and os.path.isfile(os.path.join(SYMBOL_PATH, symbol+".png")))]
        mana_symbol_paths.reverse()
        position = POSITION_MANA_SYMBOL
        for mana_symbol in mana_symbol_paths:
            shadow_image = Image.open(os.path.join(SYMBOL_PATH, "black.png"))
            shadow_image = shadow_image.resize((MANA_SYMBOL_SIZE, MANA_SYMBOL_SIZE))
            self.image.paste(shadow_image, (position[0]-1, position[1]+3), shadow_image)
            mana_image = Image.open(mana_symbol)
            mana_image = mana_image.resize((MANA_SYMBOL_SIZE, MANA_SYMBOL_SIZE))
            self.image.paste(mana_image, position, mana_image)
            position = (position[0]-(3+MANA_SYMBOL_SIZE), position[1])

    def paste_set_symbol(self):
        if self.card.rarity is None or len(self.card.rarity)==0:
            rarity = "common"
        else:
            rarity = self.card.rarity.lower()
        if rarity=="common":
            set_symbol_path = os.path.join(SET_SYMBOL_PATH, "Common.png")
        elif rarity=="uncommon":
            set_symbol_path = os.path.join(SET_SYMBOL_PATH, "Uncommon.png")
        elif rarity=="rare":
            set_symbol_path = os.path.join(SET_SYMBOL_PATH, "Rare.png")
        elif rarity=="mythic":
            set_symbol_path = os.path.join(SET_SYMBOL_PATH, "Mythic.png")
        rarity_image = Image.open(set_symbol_path)
        rarity_image = rarity_image.resize((int((1200/981)*SET_SYMBOL_SIZE), SET_SYMBOL_SIZE))
        if self.card.is_token():
            position = POSITION_TOKEN_SET_SYMBOL
        elif self.card.is_saga():
            position = POSITION_SAGA_SET_SYMBOL
        else:  
            position = POSITION_SET_SYMBOL
        self.image.paste(rarity_image, position, rarity_image)

    def paste_artwork(self, artwork_path=None):
        if artwork_path is None:
            artwork_path = os.path.join(".", "Images")
        if not artwork_path.endswith(self.card.name+".jpg"):
            artwork_path = os.path.join(artwork_path, self.card.name+".jpg")
        try:
            artwork_image = Image.open(artwork_path)
        except:
            print("  Failed to open artwork image for card " + self.card.name + ".jpeg")
            return
        if self.card.is_saga():
            self.image.paste(artwork_image, (373, 118))
        elif self.card.is_token():
            self.image.paste(artwork_image, (58, 170))
        else:
            self.image.paste(artwork_image, (58, 118))