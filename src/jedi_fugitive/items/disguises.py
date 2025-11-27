"""
Disguise items for disguise & suspicion system.
"""

class Disguise:
    def __init__(self, name, description, detection_bonus, allowed_factions):
        self.name = name
        self.description = description
        self.detection_bonus = detection_bonus  # How much detection is reduced
        self.allowed_factions = allowed_factions  # Factions this disguise grants access to

# Example disguises
DISGUISE_TYPES = {
    'civilian': Disguise('Civilian Clothes', 'Simple local attire.', 20, ['Settlers']),
    'stormtrooper': Disguise('Stormtrooper Armor', 'Imperial trooper armor.', 40, ['Imperial']),
    'merchant': Disguise('Merchant Garb', 'Trader outfit with Hutt insignia.', 30, ['Hutt']),
}

# Usage: Add Disguise items to player inventory, set player.disguise to one of these
