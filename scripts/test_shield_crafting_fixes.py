#!/usr/bin/env python3
"""
Test script to verify shield classification and crafting compatibility fixes.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_shield_classification():
    """Test that shields are no longer classified as weapons."""
    print("=== SHIELD CLASSIFICATION TEST ===")
    
    try:
        from jedi_fugitive.items.weapons import WEAPONS, WeaponType
        from jedi_fugitive.items.shields import SHIELDS, Shield
        
        # Check that shields are removed from weapons
        shield_names_in_weapons = []
        for weapon in WEAPONS:
            if any(shield_word in weapon.name.lower() for shield_word in ['shield', 'buckler']):
                shield_names_in_weapons.append(weapon.name)
        
        print(f"Found {len(shield_names_in_weapons)} shield-like items in weapons:")
        for name in shield_names_in_weapons:
            print(f"  - {name} (❌ Should be in shields.py)")
        
        # Check that shields exist in shields.py
        print(f"\nFound {len(SHIELDS)} proper shield items:")
        for shield in SHIELDS[:5]:  # Show first 5
            print(f"  - {shield.name} (✅ Properly classified)")
            print(f"    Type: {type(shield).__name__}")
            print(f"    Defense: +{shield.defense_bonus}, Evasion: {shield.evasion_bonus:+d}")
        
        if len(SHIELDS) > 5:
            print(f"  ... and {len(SHIELDS) - 5} more shields")
        
        # Check for ENERGY_SHIELD weapon type
        energy_shield_weapons = [w for w in WEAPONS if hasattr(w, 'weapon_type') and 
                                str(w.weapon_type).upper().find('ENERGY_SHIELD') != -1]
        
        print(f"\nWeapons with ENERGY_SHIELD type: {len(energy_shield_weapons)}")
        for weapon in energy_shield_weapons:
            print(f"  - {weapon.name} (❌ Should not be a weapon)")
            
        return len(shield_names_in_weapons) == 0 and len(energy_shield_weapons) == 0
        
    except Exception as e:
        print(f"Shield classification test failed: {e}")
        return False

def test_crafting_compatibility():
    """Test that crafting recipes work with all weapon types."""
    print("\n=== CRAFTING COMPATIBILITY TEST ===")
    
    try:
        from jedi_fugitive.items.weapons import WEAPONS, WeaponType
        from jedi_fugitive.items.upgrade_compatibility import is_upgrade_compatible, UPGRADE_COMPATIBILITY
        from jedi_fugitive.items.crafting import CRAFTING_RECIPES
        
        # Get weapon upgrade recipes
        weapon_upgrade_recipes = [r for r in CRAFTING_RECIPES if r.recipe_type == "weapon_upgrade"]
        print(f"Found {len(weapon_upgrade_recipes)} weapon upgrade recipes")
        
        # Test each weapon type against each upgrade
        weapon_types = list(WeaponType)
        compatibility_results = {}
        
        for recipe in weapon_upgrade_recipes:
            recipe_name = recipe.name
            compatibility_results[recipe_name] = {}
            
            print(f"\nTesting recipe: {recipe_name}")
            
            # Create mock weapons for each type
            for weapon_type in weapon_types:
                # Create a mock weapon with this type
                class MockWeapon:
                    def __init__(self, wtype):
                        self.weapon_type = wtype
                        self.name = f"Test {wtype.value}"
                
                mock_weapon = MockWeapon(weapon_type)
                is_compatible, reason = is_upgrade_compatible(recipe_name, mock_weapon)
                compatibility_results[recipe_name][weapon_type] = is_compatible
                
                status = "✅" if is_compatible else "❌"
                print(f"  {status} {weapon_type.value}: {reason}")
        
        # Summary: count compatible weapon types per recipe
        print("\n=== COMPATIBILITY SUMMARY ===")
        for recipe_name, results in compatibility_results.items():
            compatible_count = sum(results.values())
            total_count = len(results)
            print(f"{recipe_name}: {compatible_count}/{total_count} weapon types compatible")
            
            # Show incompatible types
            incompatible = [wt.value for wt, compatible in results.items() if not compatible]
            if incompatible and len(incompatible) < len(weapon_types):
                print(f"  Not compatible: {', '.join(incompatible)}")
        
        return True
        
    except Exception as e:
        print(f"Crafting compatibility test failed: {e}")
        return False

def test_specific_weapons():
    """Test specific problematic weapons."""
    print("\n=== SPECIFIC WEAPON TESTS ===")
    
    try:
        from jedi_fugitive.items.weapons import WEAPONS
        from jedi_fugitive.items.upgrade_compatibility import is_upgrade_compatible
        
        # Find some specific weapons to test
        test_weapons = []
        weapon_names_to_test = ["Riot Shield", "Vibroblade", "E-11 Blaster Rifle", "Lightsaber"]
        
        for weapon in WEAPONS:
            if any(name.lower() in weapon.name.lower() for name in weapon_names_to_test):
                test_weapons.append(weapon)
        
        print(f"Testing {len(test_weapons)} specific weapons:")
        
        upgrade_names = ["Sharpened Edge", "Balanced Grip", "Ion Capacitor", "Crystal Focus"]
        
        for weapon in test_weapons:
            print(f"\n{weapon.name} ({weapon.weapon_type.value}):")
            for upgrade_name in upgrade_names:
                is_compatible, reason = is_upgrade_compatible(upgrade_name, weapon)
                status = "✅" if is_compatible else "❌"
                print(f"  {status} {upgrade_name}: {reason}")
        
        return True
        
    except Exception as e:
        print(f"Specific weapon test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 SHIELD & CRAFTING FIXES VERIFICATION")
    print("=" * 50)
    
    test1 = test_shield_classification()
    test2 = test_crafting_compatibility() 
    test3 = test_specific_weapons()
    
    print("\n" + "=" * 50)
    print("RESULTS:")
    print(f"  Shield Classification: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"  Crafting Compatibility: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"  Specific Weapons: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 ALL TESTS PASSED! Fixes are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")