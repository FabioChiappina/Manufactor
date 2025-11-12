"""
MTG keyword abilities and mechanics.

Defines standard keyword abilities with their rules text descriptions.
"""


class Ability:
    """Represents a keyword ability with its description."""

    def __init__(self, name, isTriggered=None, isActivated=None, selfDescription=None, generalDescription=None):
        self.name = name
        self.isTriggered = isTriggered
        self.isActivated = isActivated
        self.selfDescription = selfDescription
        self.generalDescription = generalDescription


class AbilityElements:
    """Collection of standard MTG keyword abilities."""

    decayed = Ability("Decayed", selfDescription="This creature can't block. When it attacks, sacrifice it at end of combat.", generalDescription="A creature with decayed can't block. When it attacks, sacrifice it at end of combat.")
    protectionFromEverything = Ability("Protection from everything", selfDescription="This creature can't be blocked, targeted, dealt damage, enchanted, or equipped by anything.", generalDescription="A creature with protection from everything can't be blocked, targeted, dealt damage, enchanted, or equipped by anything.")
    shadow = Ability("Shadow", selfDescription="This creature can block or be blocked by only creatures with shadow.", generalDescription="A creature with shadow can block or be blocked by only creatures with shadow.")
    anarky = Ability("Anarky", selfDescription="This creature attacks a randomly selected opponent each combat if able.", generalDescription="A creature with anarky attacks a randomly selected opponent each combat if able.")
    all_abilities = [decayed, protectionFromEverything, shadow, anarky]
    all_abilities_dict = {ab.name.lower().replace(" ",""):ab for ab in all_abilities}
