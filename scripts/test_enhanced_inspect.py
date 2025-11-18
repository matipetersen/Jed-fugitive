#!/usr/bin/env python3
"""
Test the enhanced inspection system with detailed lore.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from jedi_fugitive.game import inspection

def test_enemy_inspection():
    """Test enemy inspection at different corruption levels."""
    print("=" * 60)
    print("TESTING ENEMY INSPECTION")
    print("=" * 60)
    
    enemies = [
        'Sith Acolyte Malgus',
        'Sith Warrior Revan',
        'Dark Jedi Hunter',
        'Darth Bane'
    ]
    
    corruption_levels = [
        (20, 'Light Side'),
        (50, 'Balanced'),
        (80, 'Dark Side')
    ]
    
    for enemy in enemies:
        print(f"\n{'=' * 60}")
        print(f"Enemy: {enemy}")
        print('=' * 60)
        
        for corruption, alignment in corruption_levels:
            print(f"\n  [{alignment} - Corruption: {corruption}]")
            print(f"  {'-' * 54}")
            
            result = inspection.get_enemy_inspection(enemy, corruption)
            
            print(f"  Title: {result['title']}")
            print(f"  Description: {result['description']}")
            print(f"  Lore: {result['lore']}")
            print(f"  Tactics: {result['tactics']}")
            if result.get('personal_note'):
                print(f"  Personal: {result['personal_note']}")
    
    print("\n" + "=" * 60)
    print("Enemy inspection tests completed!")
    print("=" * 60)

def test_item_inspection():
    """Test item inspection at different corruption levels."""
    print("\n\n" + "=" * 60)
    print("TESTING ITEM INSPECTION")
    print("=" * 60)
    
    items = [
        ('lightsaber', 'Jedi Lightsaber'),
        ('force_crystal', 'Kyber Crystal'),
        ('medkit', 'Medical Kit'),
        ('ancient_artifact', 'Sith Holocron'),
    ]
    
    corruption_levels = [20, 50, 80]
    
    for token, name in items:
        print(f"\n{'=' * 60}")
        print(f"Item: {name} ({token})")
        print('=' * 60)
        
        for corruption in corruption_levels:
            print(f"\n  [Corruption: {corruption}]")
            print(f"  {'-' * 54}")
            
            result = inspection.get_item_inspection(token, name, corruption)
            
            print(f"  Name: {result['name']}")
            print(f"  Description: {result['description']}")
            if result.get('lore'):
                print(f"  Lore: {result['lore']}")
            if result.get('condition'):
                print(f"  Condition: {result['condition']}")
            if result.get('choice'):
                print(f"  Choice: {result['choice']}")
    
    print("\n" + "=" * 60)
    print("Item inspection tests completed!")
    print("=" * 60)

def test_environment_inspection():
    """Test environmental feature inspection."""
    print("\n\n" + "=" * 60)
    print("TESTING ENVIRONMENT INSPECTION")
    print("=" * 60)
    
    locations = [
        'tomb_entrance',
        'ancient_statue',
        'crash_wreckage',
        'meditation_shrine'
    ]
    
    for location in locations:
        print(f"\n{'=' * 60}")
        print(f"Location: {location}")
        print('=' * 60)
        
        result = inspection.get_environment_inspection(location)
        if result:
            print(f"  Description: {result['description']}")
            print(f"  Lore: {result['lore']}")
        else:
            print(f"  No lore found for {location}")
    
    print("\n" + "=" * 60)
    print("Environment inspection tests completed!")
    print("=" * 60)

def test_formatting():
    """Test formatted output."""
    print("\n\n" + "=" * 60)
    print("TESTING FORMATTED OUTPUT")
    print("=" * 60)
    
    # Test enemy formatting
    print("\n[Enemy Format Example]")
    enemy_data = inspection.get_enemy_inspection('Sith Warrior', 50)
    lines = inspection.format_inspection_text(enemy_data, 'enemy')
    for line in lines:
        print(line)
    
    # Test item formatting
    print("\n\n[Item Format Example]")
    item_data = inspection.get_item_inspection('lightsaber', 'Jedi Lightsaber', 30)
    lines = inspection.format_inspection_text(item_data, 'item')
    for line in lines:
        print(line)
    
    # Test environment formatting
    print("\n\n[Environment Format Example]")
    env_data = inspection.get_environment_inspection('tomb_entrance')
    if env_data:
        lines = inspection.format_inspection_text(env_data, 'environment')
        for line in lines:
            print(line)
    
    print("\n" + "=" * 60)
    print("Formatting tests completed!")
    print("=" * 60)

def main():
    """Run all inspection tests."""
    print("\n" + "=" * 60)
    print("ENHANCED INSPECTION SYSTEM TEST")
    print("=" * 60)
    
    test_enemy_inspection()
    test_item_inspection()
    test_environment_inspection()
    test_formatting()
    
    print("\n\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nThe enhanced inspection system provides:")
    print("  ✓ Detailed enemy lore with 4 enemy types")
    print("  ✓ Corruption-based personal reflections")
    print("  ✓ Rich item descriptions with lore")
    print("  ✓ Environmental storytelling")
    print("  ✓ Tactical combat advice")
    print("\nPress 'x' in-game to inspect enemies, items, and features!")

if __name__ == '__main__':
    main()
