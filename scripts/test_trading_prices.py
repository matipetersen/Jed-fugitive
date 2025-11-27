#!/usr/bin/env python3
"""Test script to verify trading prices vary correctly across items and factions."""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from jedi_fugitive.game.merchants import calculate_sell_price, FACTION_DATA, MerchantFaction
from jedi_fugitive.items.weapons import WEAPONS
from jedi_fugitive.items.armor import ARMORS
from jedi_fugitive.items.consumables import ITEM_DEFS


def test_weapon_pricing():
    """Test that weapons have different prices based on stats and rarity."""
    print("=" * 80)
    print("WEAPON PRICING TEST")
    print("=" * 80)
    
    # Test a few different weapons
    test_weapons = []
    for weapon in WEAPONS[:10]:  # First 10 weapons
        test_weapons.append(weapon)
    
    for faction_key in [MerchantFaction.REPUBLIC_SURVIVORS, MerchantFaction.SCAVENGER_LOOTERS, MerchantFaction.BLACK_MARKET]:
        faction_name = FACTION_DATA[faction_key]['name']
        print(f"\n{faction_name} (Buyback: {FACTION_DATA[faction_key]['buyback'] * 100:.0f}%):")
        print("-" * 80)
        
        for weapon in test_weapons:
            name = getattr(weapon, 'name', 'Unknown')
            rarity = getattr(weapon, 'rarity', 'common')
            base_damage = getattr(weapon, 'base_damage', 0)
            value = getattr(weapon, 'value', 0)
            
            sell_price = calculate_sell_price(weapon, faction_key)
            
            print(f"  {name:30s} | Rarity: {rarity:10s} | Dmg: {base_damage:2d} | Value: {value:3d} | Sells for: {sell_price:3d}g")


def test_armor_pricing():
    """Test that armor has different prices based on stats and rarity."""
    print("\n\n" + "=" * 80)
    print("ARMOR PRICING TEST")
    print("=" * 80)
    
    # Test a few different armors
    test_armors = []
    for armor in ARMORS[:8]:  # First 8 armors
        test_armors.append(armor)
    
    for faction_key in [MerchantFaction.MANDALORIAN_SCOUTS, MerchantFaction.REPUBLIC_SURVIVORS]:
        faction_name = FACTION_DATA[faction_key]['name']
        print(f"\n{faction_name} (Buyback: {FACTION_DATA[faction_key]['buyback'] * 100:.0f}%):")
        print("-" * 80)
        
        for armor in test_armors:
            name = getattr(armor, 'name', 'Unknown')
            rarity = getattr(armor, 'rarity', 'common')
            defense = getattr(armor, 'defense', 0)
            hp_bonus = getattr(armor, 'hp_bonus', 0)
            
            sell_price = calculate_sell_price(armor, faction_key)
            
            print(f"  {name:30s} | Rarity: {rarity:10s} | Def: {defense:2d} | HP: {hp_bonus:3d} | Sells for: {sell_price:3d}g")


def test_consumable_pricing():
    """Test that consumables have different prices based on effects."""
    print("\n\n" + "=" * 80)
    print("CONSUMABLE PRICING TEST")
    print("=" * 80)
    
    faction_key = MerchantFaction.NEUTRAL_TRADERS
    faction_name = FACTION_DATA[faction_key]['name']
    print(f"\n{faction_name} (Buyback: {FACTION_DATA[faction_key]['buyback'] * 100:.0f}%):")
    print("-" * 80)
    
    for item_def in ITEM_DEFS:
        name = item_def.get('name', 'Unknown')
        effect = item_def.get('effect', {})
        
        # Get effect description
        effect_str = ""
        if 'heal' in effect:
            effect_str = f"Heal: {effect['heal']}"
        elif 'stress_reduction' in effect:
            effect_str = f"Stress: -{effect['stress_reduction']}"
        elif 'area_damage' in effect:
            effect_str = f"Area Dmg: {effect['area_damage']}"
        elif 'compass' in effect:
            effect_str = "Compass"
        
        sell_price = calculate_sell_price(item_def, faction_key)
        
        print(f"  {name:30s} | {effect_str:20s} | Sells for: {sell_price:3d}g")


def test_faction_differences():
    """Test that different factions offer different buyback prices."""
    print("\n\n" + "=" * 80)
    print("FACTION BUYBACK COMPARISON")
    print("=" * 80)
    
    # Test with a single weapon
    test_weapon = WEAPONS[0]  # First weapon
    weapon_name = getattr(test_weapon, 'name', 'Test Weapon')
    
    print(f"\nSelling '{weapon_name}' to different factions:")
    print("-" * 80)
    
    for faction_key, faction_data in FACTION_DATA.items():
        faction_name = faction_data['name']
        buyback_rate = faction_data['buyback']
        sell_price = calculate_sell_price(test_weapon, faction_key)
        
        print(f"  {faction_name:25s} | Buyback: {buyback_rate * 100:5.0f}% | Price: {sell_price:3d}g")


def test_rarity_scaling():
    """Test that rarity properly affects sell prices."""
    print("\n\n" + "=" * 80)
    print("RARITY SCALING TEST")
    print("=" * 80)
    
    faction_key = MerchantFaction.NEUTRAL_TRADERS
    
    # Group weapons by rarity
    rarity_groups = {'common': [], 'uncommon': [], 'rare': [], 'epic': [], 'legendary': []}
    for weapon in WEAPONS:
        rarity = getattr(weapon, 'rarity', 'common').lower()
        if rarity in rarity_groups:
            rarity_groups[rarity].append(weapon)
    
    print(f"\nAverage sell prices by rarity:")
    print("-" * 80)
    
    for rarity in ['common', 'uncommon', 'rare', 'epic', 'legendary']:
        weapons = rarity_groups[rarity]
        if weapons:
            avg_price = sum(calculate_sell_price(w, faction_key) for w in weapons) / len(weapons)
            print(f"  {rarity.capitalize():15s} | Average: {avg_price:6.1f}g | Count: {len(weapons)}")


if __name__ == "__main__":
    print("\nTESTING JEDI FUGITIVE TRADING SYSTEM")
    print("=" * 80)
    
    test_weapon_pricing()
    test_armor_pricing()
    test_consumable_pricing()
    test_faction_differences()
    test_rarity_scaling()
    
    print("\n\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
    print("\nIf prices vary by stats, rarity, and faction, the system is working correctly!")
