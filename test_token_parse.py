import game_elements
"""
c = game_elements.Card(cardtype="Instant", rules="This spell costs {2} less to cast no matter what.\nWhen this creature enters the battlefield, create three 1/4 red, white, and black Spider Goblin creature tokens with reach and haste.")
t = c.get_tokens()
print(t)
print()

c = game_elements.Card(cardtype="Legendary Creature", rules="Create a Treasure token.\nWhen you cast this spell, create Boknok, a legendary artifact land token with \"{t}: Add {r}.\".\nWhen this enters the battlefield, create seven 6/5 green and red Zombie enchantment creature tokens with menace named The Storm of Utter Garniceholes.")
t = c.get_tokens()
print(t)
print()

c = game_elements.Card(cardtype="Legendary Enchantment", rules="When you cast this spell, create a 1/1 blue Wurm Saga enchantment creature token with hexproof, flying, and \"Whenever you cast a spell, draw a card.\"")
t = c.get_tokens()
print(t)
print()

c = game_elements.Card(cardtype="Artifact", rules="Create two 1/1 red goblin creature tokens.\nThis spell costs {1} less to cast for each attacking creature.\nTrample\nWhen Ancient Stone Idol dies, create a 6/12 colorless Construct artifact creature token with trample.")
t = c.get_tokens()
print(t)
print()
"""
c = game_elements.Card(cardtype="Legendary Sorcery", rules="Cascade\nCreate a 2/2 green Bear creature token and a 6/6 white Angel creature token.")
t = c.get_tokens()
print(t)
print()

c = game_elements.Card(cardtype="Legendary Sorcery", rules="When you cast this spell, create a 1/1 red Goblin creature token and tokens you control gain indestructible.")
t = c.get_tokens()
print(t)
print()

c = game_elements.Card(cardtype="Instant", rules="When you cast this spell, create a 1/1 blue Bird creature token with flying, a 1/1 green Elf creature token, and a 2/4 red and white Ox Construct artifact creature token with defender.")
t = c.get_tokens()
print(t)
print()

c = game_elements.Card(cardtype="Artifact", rules="When you cast this spell, create a 0/1 red Kobold creature token with menace or a 1/2 black Spider creature token with reach.")
t = c.get_tokens()
print(t)
print()