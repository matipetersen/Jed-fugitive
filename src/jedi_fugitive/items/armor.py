class Armor:
    """Simple Armor data holder with backward-compatible ctor accepting `slot` and extra kwargs."""
    def __init__(
        self,
        name: str,
        defense: int = 0,
        evasion_mod: int = 0,
        hp_bonus: int = 0,
        weight: int = 0,
        rarity: str = "common",
        description: str = "",
        slot: str = "body",
        **kwargs,
    ):
        self.name = name
        self.defense = defense
        self.evasion_mod = evasion_mod
        self.hp_bonus = hp_bonus
        self.weight = weight
        self.rarity = rarity
        self.description = description
        self.slot = slot
        # attach any extra attrs non-destructively
        for k, v in kwargs.items():
            setattr(self, k, v)

# Ensure ARMORS list exists and append new entries non-destructively
try:
    ARMORS
except NameError:
    ARMORS = []

ARMORS.extend([
    Armor("Cloth Robes", slot="body", defense=1, evasion_mod=5, hp_bonus=0, weight=0, rarity="common",
          description="Light robes. +5 evasion."),
    Armor("Scout Vest", slot="body", defense=2, evasion_mod=3, hp_bonus=5, weight=1, rarity="uncommon",
          description="Light vest for scouts."),
    Armor("Stormtrooper Armor", slot="body", defense=5, evasion_mod=-2, hp_bonus=10, weight=3, rarity="rare",
          description="Standard issue armor. Good defence, reduces evasion."),
    Armor("Inquisitor Plate", slot="body", defense=8, evasion_mod=-4, hp_bonus=20, weight=5, rarity="epic",
          description="Heavy plated armor used by elite foes."),
])