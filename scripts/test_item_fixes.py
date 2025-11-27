#!/usr/bin/env python3
"""Test the item classification and spawn fixes."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game import fauna_system

class DummyStdscr:
    def getmaxyx(self): return (40, 140)
    def getch(self): return -1
    def clear(self): pass
    def refresh(self): pass

def test_riot_shield_classification():
    """Test that riot shields are properly classified as shields, not weapons."""
    print("=== Testing Riot Shield Classification ===")
    
    try:
        from jedi_fugitive.items.weapons import WEAPONS
        from jedi_fugitive.items.weapons import WeaponType
        
        # Find riot shields
        riot_shields = [w for w in WEAPONS if 'riot shield' in w.name.lower()]
        
        if riot_shields:
            shield = riot_shields[0]
            print(f"Found: {shield.name}")
            print(f"  Type: {shield.weapon_type}")
            print(f"  Should be: {WeaponType.ENERGY_SHIELD}")
            print(f"  Is Energy Shield: {shield.weapon_type == WeaponType.ENERGY_SHIELD}")
            
            # Test equipment system detection
            stdscr = DummyStdscr()
            game = GameManager(stdscr)
            game.initialize()
            
            # Add shield to inventory
            game.player.inventory = [shield]
            
            print(f"  Equipment system should detect as shield: Testing...")
            # This will be detected by the new logic we added
            
        else:
            print("No riot shields found!")
            
    except Exception as e:
        print(f"Error testing shield classification: {e}")

def test_fauna_loot_system():
    """Test that fauna encounters properly add items to inventory."""
    print("\n=== Testing Fauna Loot System ===")
    
    try:
        stdscr = DummyStdscr()
        game = GameManager(stdscr)
        game.initialize()
        
        # Create fauna encounter
        fauna_data = {
            'name': 'Test Nexu',
            'description': 'A test creature',
            'loot_items': ['nexu_fur_scraps', 'small_bones'],
            'loot_chance': 1.0  # 100% chance for testing
        }
        
        encounter = fauna_system.FaunaEncounter(fauna_data, 'forest')
        
        # Test loot creation
        item = encounter._create_fauna_item('nexu_fur_scraps')
        print(f"Created fauna item: {item['name']}")
        print(f"  Type: {item['type']}")
        print(f"  Description: {item['description']}")
        print(f"  Value: {item['value']}")
        
        # Test loot granting
        initial_inventory = len(game.player.inventory)
        encounter._grant_loot(game)
        final_inventory = len(game.player.inventory)
        
        print(f"Inventory before: {initial_inventory}")
        print(f"Inventory after: {final_inventory}")
        print(f"Items added: {final_inventory - initial_inventory}")
        
        if final_inventory > initial_inventory:
            new_item = game.player.inventory[-1]
            print(f"Added item: {new_item}")
            
    except Exception as e:
        print(f"Error testing fauna loot: {e}")

def test_symbol_conflicts():
    """Test that 'L' symbols are properly differentiated."""
    print("\n=== Testing Symbol Conflicts (L = Lightsaber vs Sith Lord) ===")
    
    try:
        stdscr = DummyStdscr()
        game = GameManager(stdscr)
        game.initialize()
        
        # Check token map
        from jedi_fugitive.items.tokens import TOKEN_MAP
        if 'L' in TOKEN_MAP:
            item = TOKEN_MAP['L']
            print(f"'L' token represents: {item['name']}")
            print(f"  Type: {item['type']}")
            print(f"  Description: {item['description']}")
        else:
            print("No 'L' token found in TOKEN_MAP")
            
        # Check if Sith Lords use 'L'
        from jedi_fugitive.game import enemies_sith as sith
        sith_lord = sith.create_sith_lord(level=5, x=0, y=0)
        inquisitor = sith.create_sith_inquisitor(level=7, x=0, y=0)
        
        print(f"Sith Lord symbol: '{sith_lord.symbol}'")
        print(f"Sith Inquisitor symbol: '{inquisitor.symbol}'")
        
        # Check if 'G' is used for guarded caches now
        print(f"\nChecking if guarded caches use 'G' instead of 'L'...")
        # This would require running generate_world to check
        
    except Exception as e:
        print(f"Error testing symbol conflicts: {e}")

def test_encounter_popups():
    """Test that encounters have popup interfaces."""
    print("\n=== Testing Encounter Popup Systems ===")
    
    try:
        stdscr = DummyStdscr()
        game = GameManager(stdscr)
        game.initialize()
        
        # Check if fauna manager has popup functionality
        if hasattr(game, 'fauna_manager'):
            fm = game.fauna_manager
            if hasattr(fm, '_show_fauna_encounter_popup'):
                print("Fauna encounter popup system: ✓ Available")
            else:
                print("Fauna encounter popup system: ✗ Missing")
        else:
            # Create fauna manager
            game.fauna_manager = fauna_system.FaunaManager(game)
            print("Fauna manager created")
            
        # Check if UI has popup capabilities
        if hasattr(game.ui, 'centered_dialog'):
            print("UI popup system: ✓ Available")
        else:
            print("UI popup system: ✗ Missing")
            
    except Exception as e:
        print(f"Error testing encounter popups: {e}")

def main():
    """Run all tests."""
    print("Testing Item System Fixes")
    print("=" * 50)
    
    test_riot_shield_classification()
    test_fauna_loot_system()
    test_symbol_conflicts()
    test_encounter_popups()
    
    print("\n" + "=" * 50)
    print("Tests completed!")

if __name__ == '__main__':
    main()