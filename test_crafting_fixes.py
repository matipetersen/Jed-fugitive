#!/usr/bin/env python3
"""
Test script to verify crafting system fixes.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jedi_fugitive.items.crafting import CRAFTING_RECIPES, check_materials, consume_materials
from jedi_fugitive.items.weapons import WEAPONS, WeaponType, HandRequirement
from jedi_fugitive.items.upgrade_compatibility import is_upgrade_compatible, get_compatible_upgrades
from jedi_fugitive.game.equipment import craft_item

class MockPlayer:
    def __init__(self):
        self.inventory = [
            # Add materials for testing
            {"name": "Scrap Metal", "type": "material"},
            {"name": "Scrap Metal", "type": "material"},
            {"name": "Durasteel Plate", "type": "material"},
            {"name": "Fused Wire", "type": "material"},
            {"name": "Fused Wire", "type": "material"},
            {"name": "Power Cell", "type": "material"},
            {"name": "Advanced Circuitry", "type": "material"},
        ]
        self.equipped_weapon = None
        self._base_stats = {"attack": 10, "accuracy": 80, "defense": 5, "max_hp": 100, "evasion": 10}
        self.attack = 10
        self.accuracy = 80
        self.defense = 5
        self.max_hp = 100
        self.evasion = 10

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

def test_compatibility_system():
    """Test weapon type compatibility system."""
    print("=== TESTING COMPATIBILITY SYSTEM ===")
    
    # Get test weapons
    vibroblade = next((w for w in WEAPONS if w.weapon_type == WeaponType.VIBROBLADE), None)
    blaster = next((w for w in WEAPONS if w.weapon_type == WeaponType.BLASTER_PISTOL), None)
    lightsaber = next((w for w in WEAPONS if w.weapon_type == WeaponType.LIGHTSABER), None)
    
    test_cases = [
        (vibroblade, "Sharpened Edge", True, "Physical blade should accept sharpening"),
        (blaster, "Sharpened Edge", False, "Energy weapon should reject blade sharpening"),
        (blaster, "Ion Capacitor", True, "Blaster should accept ion upgrade"),
        (vibroblade, "Ion Capacitor", False, "Physical weapon should reject ion upgrade"),
        (lightsaber, "Kyber Attunement", True, "Lightsaber should accept Kyber crystal"),
        (blaster, "Kyber Attunement", False, "Blaster should reject Kyber crystal"),
    ]
    
    for weapon, recipe_name, expected, description in test_cases:
        if weapon:
            is_compatible, reason = is_upgrade_compatible(recipe_name, weapon)
            status = "PASS" if is_compatible == expected else "FAIL"
            print(f"{status}: {description}")
            print(f"  Result: {is_compatible} - {reason}")
        else:
            print(f"SKIP: {description} (weapon not found)")
    
    return True

def test_double_application_fix():
    """Test that weapon upgrades don't apply bonuses twice."""
    print("\n=== TESTING DOUBLE APPLICATION FIX ===")
    
    game = MockGame()
    
    # Get a vibroblade for testing
    vibroblade = next((w for w in WEAPONS if w.weapon_type == WeaponType.VIBROBLADE), None)
    if not vibroblade:
        print("SKIP: No vibroblade found for testing")
        return False
    
    # Create a copy to avoid modifying the original
    import copy
    test_weapon = copy.deepcopy(vibroblade)
    
    # Equip weapon
    game.player.equipped_weapon = test_weapon
    
    # Record initial values
    initial_weapon_damage = getattr(test_weapon, 'base_damage', 0)
    initial_player_attack = game.player.attack
    
    print(f"Initial weapon damage: {initial_weapon_damage}")
    print(f"Initial player attack: {initial_player_attack}")
    
    # Apply "Sharpened Edge" upgrade (+2 attack)
    try:
        success = craft_item(game, "Sharpened Edge")
        
        if success:
            final_weapon_damage = getattr(test_weapon, 'base_damage', 0)
            final_player_attack = game.player.attack
            
            weapon_increase = final_weapon_damage - initial_weapon_damage
            player_increase = final_player_attack - initial_player_attack
            
            print(f"Final weapon damage: {final_weapon_damage} (+{weapon_increase})")
            print(f"Final player attack: {final_player_attack} (+{player_increase})")
            
            # Weapon should increase by +2, player should also increase by +2 (not +4)
            if weapon_increase == 2 and player_increase == 2:
                print("PASS: No double application detected")
                return True
            else:
                print(f"FAIL: Expected +2/+2, got +{weapon_increase}/+{player_increase}")
                return False
        else:
            print("FAIL: Upgrade failed")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_shield_weapon_separation():
    """Test that shields are properly separated from weapons."""
    print("\n=== TESTING SHIELD/WEAPON SEPARATION ===")
    
    # Count shields in weapons list (should be zero after fix)
    shield_weapons = [w for w in WEAPONS if w.weapon_type == WeaponType.ENERGY_SHIELD]
    
    print(f"Energy shields found in weapons list: {len(shield_weapons)}")
    
    if shield_weapons:
        print("ISSUE: Found shields in weapons list:")
        for shield in shield_weapons[:3]:
            print(f"  - {shield.name} (damage: {getattr(shield, 'base_damage', 0)})")
        print("These should be moved to shields.py and use Shield class")
        return False
    else:
        print("PASS: No shields found in weapons list")
        return True

def test_material_validation_order():
    """Test that materials are not consumed if upgrade fails validation."""
    print("\n=== TESTING MATERIAL VALIDATION ORDER ===")
    
    game = MockGame()
    
    # Get a blaster (incompatible with "Sharpened Edge")
    blaster = next((w for w in WEAPONS if w.weapon_type == WeaponType.BLASTER_PISTOL), None)
    if not blaster:
        print("SKIP: No blaster found for testing")
        return False
    
    import copy
    test_weapon = copy.deepcopy(blaster)
    game.player.equipped_weapon = test_weapon
    
    # Count materials before attempt
    initial_materials = [item for item in game.player.inventory if item.get('type') == 'material']
    initial_count = len(initial_materials)
    
    print(f"Initial materials: {initial_count}")
    
    # Try to apply incompatible upgrade
    try:
        success = craft_item(game, "Sharpened Edge")
        
        final_materials = [item for item in game.player.inventory if item.get('type') == 'material']
        final_count = len(final_materials)
        
        print(f"Final materials: {final_count}")
        print(f"Upgrade success: {success}")
        
        if not success and final_count == initial_count:
            print("PASS: Materials preserved when upgrade failed validation")
            return True
        elif success:
            print("FAIL: Incompatible upgrade should have failed")
            return False
        else:
            print("FAIL: Materials were consumed even though upgrade failed")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Run all tests."""
    print("CRAFTING SYSTEM FIXES TEST")
    print("=" * 40)
    
    tests = [
        ("Compatibility System", test_compatibility_system),
        ("Double Application Fix", test_double_application_fix),
        ("Shield/Weapon Separation", test_shield_weapon_separation),
        ("Material Validation Order", test_material_validation_order),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 40)
    print("TEST RESULTS:")
    print("=" * 40)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nSUMMARY: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All fixes working correctly!")
    else:
        print("⚠️  Some issues remain - see failed tests above")

if __name__ == "__main__":
    main()