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
    # === LIGHT ARMOR (High Evasion) ===
    Armor("Cloth Robes", slot="body", defense=1, evasion_mod=5, hp_bonus=0, weight=0, rarity="common",
          description="Light robes. +5 evasion.", capacity_bonus=2),
    Armor("Padded Undersuit", slot="body", defense=1, evasion_mod=4, hp_bonus=5, weight=0, rarity="common",
          description="Comfortable padding. +1 defense, +4 evasion, +5 HP.", capacity_bonus=3),
    Armor("Scout Vest", slot="body", defense=2, evasion_mod=3, hp_bonus=5, weight=1, rarity="uncommon",
          description="Light vest for scouts. +5 carry capacity.", capacity_bonus=5),
    Armor("Jedi Robes", slot="body", defense=2, evasion_mod=6, hp_bonus=10, weight=0, rarity="uncommon",
          description="Traditional Jedi robes. +2 defense, +6 evasion, +10 HP.", capacity_bonus=3),
    Armor("Smuggler's Jacket", slot="body", defense=3, evasion_mod=5, hp_bonus=10, weight=1, rarity="uncommon",
          description="Stylish and protective. +3 defense, +5 evasion, +10 HP. +7 carry capacity.", capacity_bonus=7),
    Armor("Assassin's Garb", slot="body", defense=2, evasion_mod=8, hp_bonus=5, weight=0, rarity="rare",
          description="Silent and agile. +2 defense, +8 evasion, +5 HP. +4 carry capacity.", capacity_bonus=4),
    Armor("Light Combat Suit", slot="body", defense=3, evasion_mod=4, hp_bonus=15, weight=1, rarity="rare",
          description="Flexible tactical armor. +3 defense, +4 evasion, +15 HP. +6 carry capacity.", capacity_bonus=6),
    
    # === MEDIUM ARMOR (Balanced) ===
    Armor("Mercenary Armor", slot="body", defense=4, evasion_mod=1, hp_bonus=15, weight=2, rarity="uncommon",
          description="Practical protection for hired guns. +4 defense, +1 evasion, +15 HP. +3 carry capacity.", capacity_bonus=3),
    Armor("Mandalorian Armor", slot="body", defense=6, evasion_mod=0, hp_bonus=20, weight=3, rarity="rare",
          description="Legendary Mandalorian beskar'gam. +6 defense, +20 HP. +5 carry capacity.", capacity_bonus=5),
    Armor("Bounty Hunter Gear", slot="body", defense=5, evasion_mod=1, hp_bonus=18, weight=2, rarity="rare",
          description="Rugged armor for tracking prey. +5 defense, +1 evasion, +18 HP. +8 carry capacity.", capacity_bonus=8),
    Armor("Republic Trooper Armor", slot="body", defense=5, evasion_mod=-1, hp_bonus=20, weight=3, rarity="uncommon",
          description="Republic military standard. +5 defense, -1 evasion, +20 HP. +2 carry capacity.", capacity_bonus=2),
    
    # === HEAVY ARMOR (High Defense) ===
    Armor("Stormtrooper Armor", slot="body", defense=5, evasion_mod=-2, hp_bonus=10, weight=3, rarity="rare",
          description="Standard issue armor. Good defence, reduces evasion. +1 carry capacity.", capacity_bonus=1),
    Armor("Heavy Combat Armor", slot="body", defense=7, evasion_mod=-3, hp_bonus=25, weight=4, rarity="rare",
          description="Thick plating. +7 defense, -3 evasion, +25 HP.", capacity_bonus=0),
    Armor("Sith War Plate", slot="body", defense=8, evasion_mod=-3, hp_bonus=30, weight=5, rarity="epic",
          description="Ancient Sith battle armor. +8 defense, -3 evasion, +30 HP.", capacity_bonus=0),
    Armor("Inquisitor Plate", slot="body", defense=8, evasion_mod=-4, hp_bonus=20, weight=5, rarity="epic",
          description="Heavy plated armor used by elite foes.", capacity_bonus=0),
    Armor("Juggernaut Plating", slot="body", defense=10, evasion_mod=-5, hp_bonus=40, weight=6, rarity="legendary",
          description="Impenetrable armor. +10 defense, -5 evasion, +40 HP. Bulky.", capacity_bonus=-2),
    
    # === SPECIAL ARMOR ===
    Armor("Cortosis Weave Vest", slot="body", defense=4, evasion_mod=2, hp_bonus=15, weight=2, rarity="rare",
          description="Lightsaber-resistant weave. +4 defense, +2 evasion, +15 HP. +4 carry capacity.", capacity_bonus=4),
    Armor("Stealth Field Generator", slot="body", defense=1, evasion_mod=10, hp_bonus=5, weight=1, rarity="legendary",
          description="Personal cloaking device. +1 defense, +10 evasion, +5 HP. +6 carry capacity.", capacity_bonus=6),
    Armor("Force Channeling Robes", slot="body", defense=3, evasion_mod=4, hp_bonus=20, weight=0, rarity="legendary",
          description="Enhances Force abilities. +3 defense, +4 evasion, +20 HP. +10 carry capacity.", capacity_bonus=10),
])