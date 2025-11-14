from enum import Enum
from typing import List
import random

class ShieldType(Enum):
    ENERGY_SHIELD = "Energy Shield"
    PHYSICAL_SHIELD = "Physical Shield"
    CORTOSIS_SHIELD = "Cortosis Shield"
    FORCE_SHIELD = "Force Shield"

class Shield:
    def __init__(self, name: str, shield_type: ShieldType, defense_bonus: int = 0, 
                 evasion_bonus: int = 0, weight: int = 0, value: int = 0, 
                 special: List[str] = None, rarity: str = "Common", description: str = ""):
        self.name = name
        self.shield_type = shield_type
        self.defense_bonus = defense_bonus
        self.evasion_bonus = evasion_bonus
        self.weight = weight
        self.value = value
        self.special = special if special is not None else []
        self.rarity = rarity
        self.description = description
        self.slot = "offhand"  # Equipment slot
        self.type = "shield"  # For inventory system
        self.is_shield = True  # Flag for equipment logic

# Shield catalog
SHIELDS = [
    # Common Shields
    Shield("Scrap Metal Shield", ShieldType.PHYSICAL_SHIELD, 
           defense_bonus=2, evasion_bonus=-2, weight=4, value=5,
           special=["Heavy", "Makeshift"],
           rarity="Common",
           description="Improvised shield from ship wreckage. Slows you down. +2 Defense, -2 Evasion"),
    
    Shield("Riot Shield", ShieldType.PHYSICAL_SHIELD,
           defense_bonus=3, evasion_bonus=-1, weight=3, value=8,
           special=["Guard Issue", "Sturdy"],
           rarity="Common",
           description="Standard riot control shield. +3 Defense, -1 Evasion"),
    
    Shield("Light Buckler", ShieldType.PHYSICAL_SHIELD,
           defense_bonus=1, evasion_bonus=2, weight=1, value=10,
           special=["Quick", "Parry"],
           rarity="Common",
           description="Small shield for agile fighters. +1 Defense, +2 Evasion"),
    
    # Uncommon Shields
    Shield("Energy Buckler", ShieldType.ENERGY_SHIELD,
           defense_bonus=3, evasion_bonus=1, weight=2, value=15,
           special=["Energy Resistant", "Light"],
           rarity="Uncommon",
           description="Personal energy shield emitter. +3 Defense, +1 Evasion"),
    
    Shield("Durasteel Shield", ShieldType.PHYSICAL_SHIELD,
           defense_bonus=5, evasion_bonus=0, weight=3, value=12,
           special=["Durable", "Blaster Resistant"],
           rarity="Uncommon",
           description="Military-grade durasteel shield. +5 Defense"),
    
    Shield("Cortosis Weave Shield", ShieldType.CORTOSIS_SHIELD,
           defense_bonus=4, evasion_bonus=1, weight=2, value=20,
           special=["Lightsaber Resistant", "Rare Metal"],
           rarity="Uncommon",
           description="Woven with cortosis ore, resists lightsabers. +4 Defense, +1 Evasion"),
    
    # Rare Shields
    Shield("Personal Force Field", ShieldType.ENERGY_SHIELD,
           defense_bonus=6, evasion_bonus=2, weight=1, value=25,
           special=["Energy Absorption", "Recharge"],
           rarity="Rare",
           description="Generates protective force field. +6 Defense, +2 Evasion"),
    
    Shield("Mandalorian Vambrace Shield", ShieldType.ENERGY_SHIELD,
           defense_bonus=5, evasion_bonus=3, weight=1, value=30,
           special=["Wrist-Mounted", "Quick Deploy", "Whistling Birds"],
           rarity="Rare",
           description="Wrist-mounted shield projector. +5 Defense, +3 Evasion"),
    
    # Legendary Shields
    Shield("Sith Battle Shield", ShieldType.FORCE_SHIELD,
           defense_bonus=8, evasion_bonus=0, weight=3, value=40,
           special=["Dark Side Infused", "Fear Aura", "Life Drain"],
           rarity="Legendary",
           description="Ancient Sith war shield radiating dark energy. +8 Defense"),
    
    Shield("Jedi Guardian Shield", ShieldType.FORCE_SHIELD,
           defense_bonus=6, evasion_bonus=4, weight=1, value=45,
           special=["Force Enhanced", "Deflection", "Light Side Blessing"],
           rarity="Legendary",
           description="Force-attuned shield of the Jedi Guardians. +6 Defense, +4 Evasion"),
]
