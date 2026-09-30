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
    
    # Additional Rare Materials
    Material("Quantum Processor", MaterialType.ELECTRONIC, "Rare",
             "Advanced quantum computing core for complex systems."),
    Material("Stabilized Plasma", MaterialType.ENERGY_CELL, "Rare",
             "Contained plasma for high-energy applications."),
    Material("Vibro-Motor", MaterialType.ELECTRONIC, "Uncommon",
             "Ultrasonic vibration generator for weapons."),
    Material("Sensor Array", MaterialType.ELECTRONIC, "Uncommon",
             "Multi-spectrum sensor suite for targeting systems."),
    Material("Reflective Coating", MaterialType.RARE_ALLOY, "Uncommon",
             "Energy-reflective surface treatment."),
    Material("Neural Interface", MaterialType.ELECTRONIC, "Rare",
             "Direct neural connection hardware."),
]

class CraftingRecipe:
    def __init__(self, name: str, recipe_type: str, materials: Dict[str, int], 
                 result: Any, description: str = "", required_level: int = 1):
        self.name = name
        self.recipe_type = recipe_type  # "weapon_upgrade", "item_craft", "repair"
        self.materials = materials  # {"Material Name": quantity}
        self.result = result
        self.description = description
        self.required_level = required_level

# Crafting recipes
CRAFTING_RECIPES = [
    # Weapon Upgrades
    CraftingRecipe(
        "Sharpened Edge",
        "weapon_upgrade",
        {"Scrap Metal": 2, "Durasteel Plate": 1},
        {"stat": "attack", "bonus": 2, "name": "Sharpened"},
        "Sharpen blade edges for +2 Attack",
        required_level=1
    ),
    
    CraftingRecipe(
        "Balanced Grip",
        "weapon_upgrade",
        {"Scrap Metal": 1, "Fused Wire": 2},
        {"stat": "accuracy", "bonus": 5, "name": "Balanced"},
        "Improve weapon balance for +5 Accuracy",
        required_level=2
    ),
    
    CraftingRecipe(
        "Reinforced Frame",
        "weapon_upgrade",
        {"Durasteel Plate": 2, "Plasteel Composite": 1},
        {"stat": "durability", "bonus": 20, "name": "Reinforced"},
        "Strengthen weapon structure, +20 Durability",
        required_level=2
    ),
    
    CraftingRecipe(
        "Ion Capacitor",
        "weapon_upgrade",
        {"Power Cell": 2, "Advanced Circuitry": 1},
        {"stat": "damage", "bonus": 3, "name": "Ion-Charged", "special": "Droid Damage"},
        "Add ion damage, +3 vs Droids",
        required_level=3
    ),
    
    CraftingRecipe(
        "Cortosis Weave",
        "weapon_upgrade",
        {"Cortosis Ore": 1, "Fused Wire": 2},
        {"stat": "defense", "bonus": 3, "name": "Cortosis-Woven", "special": "Lightsaber Resist"},
        "Weave cortosis into weapon/armor, resist lightsabers",
        required_level=4
    ),
    
    CraftingRecipe(
        "Power Cell Overcharge",
        "weapon_upgrade",
        {"Power Cell": 3, "Compact Power Core": 1},
        {"stat": "damage", "bonus": 5, "name": "Overcharged"},
        "Boost weapon power output for +5 Damage",
        required_level=3
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
    
    # Advanced Crafting Recipes
    CraftingRecipe(
        "Force Amplifier",
        "item_craft",
        {"Kyber Crystal": 1, "Advanced Circuitry": 3, "Focusing Lens": 2},
        {"item_id": "force_amplifier", "name": "Force Amplifier", "type": "accessory", "force_power": 5},
        "Amplify Force abilities, +5 Force Power"
    ),
    
    CraftingRecipe(
        "Stealth Field Generator",
        "item_craft", 
        {"Compact Power Core": 2, "Advanced Circuitry": 3, "Plasteel Composite": 2},
        {"item_id": "stealth_field", "name": "Stealth Field Generator", "type": "consumable", "effect": {"stealth": 10, "duration": 5}},
        "Temporary invisibility for 5 turns"
    ),
    
    CraftingRecipe(
        "Enhanced Stimpacks",
        "item_craft",
        {"Power Cell": 1, "Advanced Circuitry": 1, "Scrap Metal": 2},
        {"item_id": "enhanced_medkit", "name": "Enhanced Medkit", "type": "consumable", "effect": {"heal": 50, "cure": True}},
        "Superior healing that also cures status effects"
    ),
    
    CraftingRecipe(
        "Targeting Computer",
        "weapon_upgrade",
        {"Advanced Circuitry": 2, "Focusing Lens": 1, "Power Cell": 1},
        {"stat": "accuracy", "bonus": 12, "name": "Computer-Assisted", "special": "Auto-Target"},
        "Advanced targeting system, +12 Accuracy"
    ),
    
    CraftingRecipe(
        "Vibro-Edge",
        "weapon_upgrade",
        {"Phrik Alloy": 1, "Power Cell": 2, "Advanced Circuitry": 1},
        {"stat": "attack", "bonus": 8, "name": "Vibro-Enhanced", "special": "Armor Pierce"},
        "Ultrasonic vibration edge, +8 Attack, ignores armor"
    ),
    
    CraftingRecipe(
        "Adaptive Armor Plating",
        "armor_upgrade",
        {"Beskar Ingot": 1, "Phrik Alloy": 1, "Advanced Circuitry": 2},
        {"stat": "defense", "bonus": 10, "stat2": "resistance", "bonus2": 3, "name": "Adaptive"},
        "Smart armor that adapts to damage types"
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

class CraftingManager:
    def __init__(self, game):
        self.game = game

    def get_available_recipes(self):
        """Return list of recipes the player can craft based on level."""
        available = []
        for recipe in CRAFTING_RECIPES:
            if getattr(self.game.player, 'level', 1) >= recipe.required_level:
                available.append(recipe)
        return available

    def can_craft(self, recipe):
        return check_materials(self.game.player.inventory, recipe.materials)

    def craft(self, recipe):
        if not self.can_craft(recipe):
            if hasattr(self.game.ui, 'messages'):
                self.game.ui.messages.add(f"Not enough materials for {recipe.name}.")
            return False
        
        # Consume materials
        self.game.player.inventory = consume_materials(self.game.player.inventory, recipe.materials)
        
        # Apply result
        success = False
        if recipe.recipe_type == "weapon_upgrade":
            success = self._upgrade_weapon(recipe)
        elif recipe.recipe_type == "item_craft":
            success = self._craft_item(recipe)
        
        if success:
            if hasattr(self.game.ui, 'messages'):
                self.game.ui.messages.add(f"Successfully crafted {recipe.name}!")
        else:
            if hasattr(self.game.ui, 'messages'):
                self.game.ui.messages.add(f"Failed to craft {recipe.name}.")
        
        return success

    def _upgrade_weapon(self, recipe):
        weapon = getattr(self.game.player, 'equipped_weapon', None)
        if not weapon:
            if hasattr(self.game.ui, 'messages'):
                self.game.ui.messages.add("No weapon equipped to upgrade.")
            return False
            
        # Apply stats
        res = recipe.result
        if 'stat' in res:
            current = getattr(weapon, res['stat'], 0)
            setattr(weapon, res['stat'], current + res['bonus'])
        if 'stat2' in res:
            current = getattr(weapon, res['stat2'], 0)
            setattr(weapon, res['stat2'], current + res['bonus2'])
        if 'name' in res:
            weapon.name = f"{res['name']} {weapon.name}"
            
        return True

    def _craft_item(self, recipe):
        # Create item and add to inventory
        res = recipe.result
        
        # Simple item creation logic - can be expanded
        # For now, we'll create a simple object or dict depending on what inventory expects
        # Assuming inventory can hold objects with 'name' and 'type'
        
        class CraftedItem:
            def __init__(self, data):
                self.name = data.get('name', 'Unknown Item')
                self.type = data.get('type', 'misc')
                self.data = data
                for k, v in data.items():
                    setattr(self, k, v)
                    
        new_item = CraftedItem(res)
        self.game.player.inventory.append(new_item)
        return True

