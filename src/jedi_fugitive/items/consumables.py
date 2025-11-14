"""Consumable items placed in the world.

Each entry is a dict with keys: id, name, token (map glyph), type, effect (description or small dict).
Game systems may extend these definitions into proper item objects; this file serves as a simple
catalog so the world generator can place useful consumables.
"""

ITEM_DEFS = [
    {
        "id": "medkit_small",
        "name": "Small Medkit",
        "token": "+",
        "type": "consumable",
        "effect": {"heal": 10},
        "description": "Heals 10 HP when used.",
    },
    {
        "id": "stimpack",
        "name": "Stimpack",
        "token": "!",
        "type": "consumable",
        "effect": {"heal": 5, "temp_speed": 1, "duration": 6},
        "description": "Heals 5 HP and grants a short burst of energy.",
    },
    {
        "id": "grenade",
        "name": "Thermal Grenade",
        "token": "*",
        "type": "consumable",
        # expanded radius: round (circular) area of effect, 3 tiles
        "effect": {"area_damage": 24, "radius": 3},
        "description": "Deals area damage when thrown.",
    },
    {
        "id": "energy_cell",
        "name": "Energy Cell",
        "token": "c",
        "type": "ammo",
        "effect": {"ammo": 8},
        "description": "A small energy cell used to reload energy weapons.",
    },
    {
        "id": "jedi_meditation_focus",
        "name": "Jedi Meditation Focus",
        "token": "M",
        "type": "consumable",
        "effect": {"stress_reduction": 40},
        "description": "A focus used to clear the mind. Reduces stress by 40.",
    },
    {
        "id": "calming_tea",
        "name": "Calming Tea",
        "token": "T",
        "type": "consumable",
        "effect": {"stress_reduction": 25},
        "description": "A soothing brew that calms the nerves (-25 stress).",
    },
    {
        "id": "compass",
        "name": "Compass (Tombfinder)",
        "token": "C",
        "type": "consumable",
        # special effect: when used, triggers a scan/compass action that points toward nearest tomb
        "effect": {"compass": True},
        "description": "A mechanical compass enhanced with a simple tombfinding rune. Use to locate the nearest tomb.",
    },
    {
        "id": "ration",
        "name": "Emergency Ration",
        "token": ":",
        "type": "consumable",
        "effect": {"heal": 8, "stress_reduction": 10},
        "description": "A compact meal pack. Restores 8 HP and reduces stress by 10.",
    },
    {
        "id": "water_canteen",
        "name": "Water Canteen",
        "token": ":",
        "type": "consumable",
        "effect": {"heal": 5, "stress_reduction": 15},
        "description": "Fresh water from your ship's reserves. Restores 5 HP and calms the mind (-15 stress).",
    },
    {
        "id": "nutrient_paste",
        "name": "Nutrient Paste",
        "token": ":",
        "type": "consumable",
        "effect": {"heal": 12},
        "description": "Unappetizing but effective. Restores 12 HP.",
    },
]
