from enum import Enum
from typing import List, Dict, Any
import random

class MaterialType(Enum):
    COMMON_METAL = "Common Metal"
    RARE_ALLOY = "Rare Alloy"
    CRYSTAL = "Crystal"
    ELECTRONIC = "Electronic Component"
    ENERGY_CELL = "Energy Cell"
    CORTOSIS = "Cortosis Ore"
    PHRIK = "Phrik Alloy"
    BESKAR = "Beskar Steel"
    KYBER = "Kyber Crystal"

class Material:
    def __init__(self, name: str, material_type: MaterialType, rarity: str = "Common", 
                 description: str = "", stackable: bool = True):
        self.name = name
        self.material_type = material_type
        self.rarity = rarity
        self.description = description
        self.stackable = stackable
        self.type = "material"  # For inventory system

# Crafting materials catalog
MATERIALS = [
    # Common Materials
    Material("Scrap Metal", MaterialType.COMMON_METAL, "Common",
             "Salvaged metal scraps. Basic crafting material."),
    Material("Durasteel Plate", MaterialType.COMMON_METAL, "Common",
             "Standard durasteel armor plating."),
    Material("Fused Wire", MaterialType.ELECTRONIC, "Common",
             "Electrical wiring for basic repairs."),
    Material("Power Cell", MaterialType.ENERGY_CELL, "Common",
             "Standard energy cell for weapons and devices."),
    
    # Uncommon Materials
    Material("Plasteel Composite", MaterialType.RARE_ALLOY, "Uncommon",
             "Lightweight but strong polymer-metal blend."),
    Material("Focusing Lens", MaterialType.CRYSTAL, "Uncommon",
             "Crystal lens for energy weapons and lightsabers."),
    Material("Advanced Circuitry", MaterialType.ELECTRONIC, "Uncommon",
             "High-grade electronic components."),
    Material("Ionization Chamber", MaterialType.ELECTRONIC, "Uncommon",
             "Weapon modification for ion damage."),
    
    # Rare Materials
    Material("Cortosis Ore", MaterialType.CORTOSIS, "Rare",
             "Rare ore that can short-circuit lightsabers."),
    Material("Phrik Alloy", MaterialType.PHRIK, "Rare",
             "Extremely durable metal resistant to lightsabers."),
    Material("Synthetic Crystal", MaterialType.CRYSTAL, "Rare",
             "Lab-grown focusing crystal for weapons."),
    Material("Compact Power Core", MaterialType.ENERGY_CELL, "Rare",
             "High-output miniaturized power source."),
    
    # Legendary Materials
    Material("Beskar Ingot", MaterialType.BESKAR, "Legendary",
             "Mandalorian iron, virtually indestructible."),
    Material("Kyber Crystal", MaterialType.KYBER, "Legendary",
             "Force-attuned crystal, heart of a lightsaber."),
]

class CraftingRecipe:
    def __init__(self, name: str, recipe_type: str, materials: Dict[str, int], 
                 result: Any, description: str = "", skill_required: int = 0):
        self.name = name
        self.recipe_type = recipe_type  # "weapon_upgrade", "item_craft", "repair"
        self.materials = materials  # {"Material Name": quantity}
        self.result = result
        self.description = description
        self.skill_required = skill_required

# Crafting recipes
CRAFTING_RECIPES = [
    # Weapon Upgrades
    CraftingRecipe(
        "Sharpened Edge",
        "weapon_upgrade",
        {"Scrap Metal": 2, "Durasteel Plate": 1},
        {"stat": "attack", "bonus": 2, "name": "Sharpened"},
        "Sharpen blade edges for +2 Attack"
    ),
    
    CraftingRecipe(
        "Balanced Grip",
        "weapon_upgrade",
        {"Scrap Metal": 1, "Fused Wire": 2},
        {"stat": "accuracy", "bonus": 5, "name": "Balanced"},
        "Improve weapon balance for +5 Accuracy"
    ),
    
    CraftingRecipe(
        "Reinforced Frame",
        "weapon_upgrade",
        {"Durasteel Plate": 2, "Plasteel Composite": 1},
        {"stat": "durability", "bonus": 20, "name": "Reinforced"},
        "Strengthen weapon structure, +20 Durability"
    ),
    
    CraftingRecipe(
        "Ion Capacitor",
        "weapon_upgrade",
        {"Power Cell": 2, "Advanced Circuitry": 1},
        {"stat": "damage", "bonus": 3, "name": "Ion-Charged", "special": "Droid Damage"},
        "Add ion damage, +3 vs Droids"
    ),
    
    CraftingRecipe(
        "Cortosis Weave",
        "weapon_upgrade",
        {"Cortosis Ore": 1, "Fused Wire": 2},
        {"stat": "defense", "bonus": 3, "name": "Cortosis-Woven", "special": "Lightsaber Resist"},
        "Weave cortosis into weapon/armor, resist lightsabers"
    ),
    
    CraftingRecipe(
        "Power Cell Overcharge",
        "weapon_upgrade",
        {"Power Cell": 3, "Compact Power Core": 1},
        {"stat": "damage", "bonus": 5, "name": "Overcharged"},
        "Boost weapon power output for +5 Damage"
    ),
    
    CraftingRecipe(
        "Crystal Focus",
        "weapon_upgrade",
        {"Focusing Lens": 1, "Synthetic Crystal": 1},
        {"stat": "accuracy", "bonus": 8, "stat2": "attack", "bonus2": 3, "name": "Crystal-Focused"},
        "Add focusing crystal, +8 Accuracy, +3 Attack"
    ),
    
    CraftingRecipe(
        "Beskar Reinforcement",
        "weapon_upgrade",
        {"Beskar Ingot": 1, "Durasteel Plate": 2},
        {"stat": "defense", "bonus": 8, "stat2": "durability", "bonus2": 50, "name": "Beskar-Forged"},
        "Forge with Beskar, +8 Defense, +50 Durability"
    ),
    
    CraftingRecipe(
        "Kyber Attunement",
        "weapon_upgrade",
        {"Kyber Crystal": 1, "Focusing Lens": 2},
        {"stat": "attack", "bonus": 10, "stat2": "accuracy", "bonus2": 10, "name": "Kyber-Attuned", "special": "Force Resonance"},
        "Attune weapon with Kyber crystal, +10 Attack, +10 Accuracy, Force bonus"
    ),
    
    # Item Crafting
    CraftingRecipe(
        "Medkit",
        "item_craft",
        {"Scrap Metal": 1, "Fused Wire": 1},
        {"item_id": "medkit", "name": "Medkit", "type": "consumable", "effect": {"heal": 30}},
        "Craft healing medkit, restores 30 HP"
    ),
    
    CraftingRecipe(
        "Energy Shield Generator",
        "item_craft",
        {"Power Cell": 3, "Advanced Circuitry": 2, "Plasteel Composite": 1},
        {"item_id": "energy_buckler", "name": "Energy Buckler", "type": "shield", "defense": 3, "evasion": 1},
        "Build personal energy shield, +3 Defense, +1 Evasion"
    ),
    
    CraftingRecipe(
        "Thermal Detonator",
        "item_craft",
        {"Power Cell": 2, "Advanced Circuitry": 1, "Ionization Chamber": 1},
        {"item_id": "thermal_grenade", "name": "Thermal Detonator", "type": "consumable", "effect": {"area_damage": 24, "radius": 3}},
        "Craft explosive thermal detonator"
    ),
]

def get_material_by_name(name: str):
    """Get material object by name."""
    for mat in MATERIALS:
        if mat.name.lower() == name.lower():
            return mat
    return None

def get_recipe_by_name(name: str):
    """Get recipe object by name."""
    for recipe in CRAFTING_RECIPES:
        if recipe.name.lower() == name.lower():
            return recipe
    return None

def check_materials(inventory: List[Any], materials_needed: Dict[str, int]) -> bool:
    """Check if player has required materials in inventory."""
    material_counts = {}
    
    # Count materials in inventory
    for item in inventory:
        if isinstance(item, dict):
            item_name = item.get('name', '')
            item_type = item.get('type', '')
        elif hasattr(item, 'name'):
            item_name = item.name
            item_type = getattr(item, 'type', '')
        else:
            continue
        
        if item_type == 'material':
            material_counts[item_name] = material_counts.get(item_name, 0) + 1
    
    # Check if we have enough of each material
    for material_name, needed_count in materials_needed.items():
        if material_counts.get(material_name, 0) < needed_count:
            return False
    
    return True

def consume_materials(inventory: List[Any], materials_needed: Dict[str, int]) -> List[Any]:
    """Remove materials from inventory and return updated inventory."""
    materials_to_remove = dict(materials_needed)
    new_inventory = []
    
    for item in inventory:
        if isinstance(item, dict):
            item_name = item.get('name', '')
            item_type = item.get('type', '')
        elif hasattr(item, 'name'):
            item_name = item.name
            item_type = getattr(item, 'type', '')
        else:
            new_inventory.append(item)
            continue
        
        # If this is a material we need to consume
        if item_type == 'material' and item_name in materials_to_remove:
            if materials_to_remove[item_name] > 0:
                materials_to_remove[item_name] -= 1
                continue  # Don't add to new inventory (consumed)
        
        new_inventory.append(item)
    
    return new_inventory
