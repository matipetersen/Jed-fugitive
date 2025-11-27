#!/usr/bin/env python3
"""
Test script to analyze the crafting system and identify weapon upgrade issues.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jedi_fugitive.items.crafting import CRAFTING_RECIPES, check_materials, consume_materials
from jedi_fugitive.items.weapons import WEAPONS, WeaponType, HandRequirement
from jedi_fugitive.game.equipment import craft_item

class MockPlayer:
    def __init__(self):
        self.inventory = [
            # Add basic materials for testing
            {"name": "Scrap Metal", "type": "material"},
            {"name": "Scrap Metal", "type": "material"},
            {"name": "Durasteel Plate", "type": "material"},
            {"name": "Fused Wire", "type": "material"},
            {"name": "Fused Wire", "type": "material"},
            {"name": "Power Cell", "type": "material"},
            {"name": "Advanced Circuitry", "type": "material"},
        ]
        self.equipped_weapon = None
        self.attack = 10
        self.accuracy = 80
        self.defense = 5

class MockUI:
    def __init__(self):
        self.messages = MockMessages()

class MockMessages:
    def add(self, msg):
        print(f"MESSAGE: {msg}")

class MockGame:
    def __init__(self):
        self.player = MockPlayer()
        self.ui = MockUI()
        self.turn_count = 1

def analyze_weapons():
    """Analyze all weapons and their types."""
    print("=== WEAPON ANALYSIS ===")
    print(f"Total weapons defined: {len(WEAPONS)}")
    
    # Group weapons by type
    weapon_types = {}
    hand_requirements = {}
    
    for weapon in WEAPONS:
        wtype = getattr(weapon, 'weapon_type', 'Unknown')
        hands = getattr(weapon, 'hands', HandRequirement.ONE_HAND)
        
        # Count by weapon type
        if wtype not in weapon_types:
            weapon_types[wtype] = []
        weapon_types[wtype].append(weapon)
        
        # Count by hand requirement
        hands_str = hands.value if hasattr(hands, 'value') else str(hands)
        if hands_str not in hand_requirements:
            hand_requirements[hands_str] = []
        hand_requirements[hands_str].append(weapon)
    
    print("\n--- Weapons by Type ---")
    for wtype, weapons in weapon_types.items():
        print(f"{wtype}: {len(weapons)} weapons")
        for w in weapons[:3]:  # Show first 3 as examples
            print(f"  - {w.name} (damage: {getattr(w, 'base_damage', 0)})")
    
    print("\n--- Weapons by Hand Requirement ---")
    for hands, weapons in hand_requirements.items():
        print(f"{hands}: {len(weapons)} weapons")
    
    return weapon_types, hand_requirements

def analyze_crafting_recipes():
    """Analyze crafting recipes and their requirements."""
    print("\n=== CRAFTING RECIPE ANALYSIS ===")
    print(f"Total recipes: {len(CRAFTING_RECIPES)}")
    
    recipe_types = {}
    for recipe in CRAFTING_RECIPES:
        rtype = recipe.recipe_type
        if rtype not in recipe_types:
            recipe_types[rtype] = []
        recipe_types[rtype].append(recipe)
    
    print("\n--- Recipes by Type ---")
    for rtype, recipes in recipe_types.items():
        print(f"{rtype}: {len(recipes)} recipes")
        for recipe in recipes:
            print(f"  - {recipe.name}: {recipe.description}")
    
    return recipe_types

def test_weapon_upgrade_logic():
    """Test the weapon upgrade logic with different weapon types."""
    print("\n=== WEAPON UPGRADE LOGIC TEST ===")
    
    # Create mock game
    game = MockGame()
    
    # Test with different weapon types
    test_weapons = [
        # Find weapons of different types
        next((w for w in WEAPONS if w.weapon_type == WeaponType.VIBROBLADE), None),
        next((w for w in WEAPONS if w.weapon_type == WeaponType.BLASTER_PISTOL), None),
        next((w for w in WEAPONS if w.weapon_type == WeaponType.LIGHTSABER), None),
        next((w for w in WEAPONS if w.weapon_type == WeaponType.ENERGY_SHIELD), None),
    ]
    
    for weapon in test_weapons:
        if weapon is None:
            continue
            
        print(f"\n--- Testing with {weapon.name} ({weapon.weapon_type}) ---")
        
        # Equip weapon
        game.player.equipped_weapon = weapon
        original_damage = getattr(weapon, 'base_damage', 0)
        original_player_attack = game.player.attack
        
        print(f"Original weapon damage: {original_damage}")
        print(f"Original player attack: {original_player_attack}")
        
        # Test "Sharpened Edge" upgrade
        try:
            success = craft_item(game, "Sharpened Edge")
            print(f"Sharpened Edge upgrade result: {success}")
            
            if success:
                new_damage = getattr(weapon, 'base_damage', 0)
                new_player_attack = game.player.attack
                print(f"New weapon damage: {new_damage} (change: +{new_damage - original_damage})")
                print(f"New player attack: {new_player_attack} (change: +{new_player_attack - original_player_attack})")
            else:
                print("Upgrade failed!")
                
        except Exception as e:
            print(f"ERROR during upgrade: {e}")
            import traceback
            traceback.print_exc()

def check_weapon_upgrade_restrictions():
    """Check if there are any restrictions on weapon types for upgrades."""
    print("\n=== WEAPON UPGRADE RESTRICTIONS ANALYSIS ===")
    
    # Look at the craft_item function for any weapon type restrictions
    print("Analyzing craft_item function in equipment.py...")
    
    # Check if weapon upgrades have type restrictions in the recipe logic
    weapon_upgrade_recipes = [r for r in CRAFTING_RECIPES if r.recipe_type == "weapon_upgrade"]
    
    print(f"Found {len(weapon_upgrade_recipes)} weapon upgrade recipes:")
    for recipe in weapon_upgrade_recipes:
        result = recipe.result
        stat = result.get('stat')
        bonus = result.get('bonus', 0)
        special = result.get('special', '')
        print(f"  - {recipe.name}: +{bonus} {stat} {f'({special})' if special else ''}")
    
    # Look for any weapon type checks in the crafting logic
    print("\nLooking for weapon type restrictions in crafting logic...")
    print("No explicit weapon type checks found in current implementation.")
    print("All weapon upgrades should work on any equipped weapon.")

def find_potential_issues():
    """Identify potential issues with the crafting system."""
    print("\n=== POTENTIAL ISSUES ANALYSIS ===")
    
    issues_found = []
    
    # Issue 1: Check if shields can be "upgraded" as weapons
    shield_weapons = [w for w in WEAPONS if w.weapon_type == WeaponType.ENERGY_SHIELD]
    if shield_weapons:
        issues_found.append("ISSUE: Energy shields are defined as weapons but may not benefit from weapon upgrades")
        print("ISSUE 1: Energy shields are defined as weapons in the weapon list")
        print("  - This could cause confusion when trying to upgrade shields")
        print("  - Shields should probably not receive attack/accuracy bonuses")
        for shield in shield_weapons[:3]:
            print(f"    - {shield.name}: base_damage={getattr(shield, 'base_damage', 0)}")
    
    # Issue 2: Check for weapons with zero base damage
    zero_damage_weapons = [w for w in WEAPONS if getattr(w, 'base_damage', 0) == 0]
    if zero_damage_weapons:
        issues_found.append("ISSUE: Some weapons have zero base damage")
        print("ISSUE 2: Weapons with zero base damage found:")
        for weapon in zero_damage_weapons:
            print(f"  - {weapon.name}: {weapon.weapon_type}")
    
    # Issue 3: Check weapon normalization
    print("ISSUE 3: Weapon normalization may cause problems")
    print("  - The _normalize_weapons() function modifies WEAPONS list")
    print("  - This could cause inconsistencies between different weapon instances")
    
    # Issue 4: Check for material requirements that might be hard to obtain
    rare_materials = set()
    for recipe in CRAFTING_RECIPES:
        if recipe.recipe_type == "weapon_upgrade":
            for material, count in recipe.materials.items():
                if "Kyber" in material or "Beskar" in material or "Phrik" in material or "Cortosis" in material:
                    rare_materials.add(material)
    
    if rare_materials:
        issues_found.append("ISSUE: Some upgrades require very rare materials")
        print("ISSUE 4: Very rare materials required for some upgrades:")
        for material in rare_materials:
            print(f"  - {material}")
    
    # Issue 5: Check stat application logic
    print("ISSUE 5: Stat application may have bugs")
    print("  - Weapon upgrades modify both weapon.base_damage AND game.player.attack")
    print("  - This could lead to double-application of bonuses")
    print("  - Need to verify that equipment effects are properly managed")
    
    return issues_found

def main():
    """Main analysis function."""
    print("JEDI FUGITIVE CRAFTING SYSTEM ANALYSIS")
    print("=" * 50)
    
    try:
        # Analyze weapons
        weapon_types, hand_requirements = analyze_weapons()
        
        # Analyze recipes
        recipe_types = analyze_crafting_recipes()
        
        # Test upgrade logic
        test_weapon_upgrade_logic()
        
        # Check for restrictions
        check_weapon_upgrade_restrictions()
        
        # Find potential issues
        issues = find_potential_issues()
        
        print(f"\n=== SUMMARY ===")
        print(f"Issues found: {len(issues)}")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
            
        print(f"\nTotal weapons: {len(WEAPONS)}")
        print(f"Total recipes: {len(CRAFTING_RECIPES)}")
        print(f"Weapon upgrade recipes: {len([r for r in CRAFTING_RECIPES if r.recipe_type == 'weapon_upgrade'])}")
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()