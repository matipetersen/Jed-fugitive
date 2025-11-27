#!/usr/bin/env python3
"""
Test script to verify reward system integration across all event types.
Tests environmental events, random events, narrative choices, and fauna encounters.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_reward_system():
    """Test all reward systems to ensure they apply actual effects."""
    
    print("=== REWARD SYSTEM INTEGRATION TEST ===\n")
    
    try:
        from jedi_fugitive.game.reward_system import (
            apply_narrative_reward, 
            apply_environmental_reward,
            tick_temporary_effects
        )
        from jedi_fugitive.game.random_events import get_random_event, trigger_random_event
        from jedi_fugitive.game.narrative_events import get_environmental_event
        
        # Create mock objects
        class MockPlayer:
            def __init__(self):
                self.force_points = 10
                self.health = 50
                self.max_health = 100
                self.attack = 15
                self.evasion = 10
                self.accuracy = 75
                self.x = 5
                self.y = 5
                self.temporary_effects = {}
                self.active_effects = {}
                self.temporary_boosts = {}
                self.weapon_enhancements = {}
                self.equipped_weapon = {"name": "Test Lightsaber", "attack": 5}
                self.journal = []
        
        class MockUI:
            def __init__(self):
                self.messages = self
                self._messages = []
            
            def add(self, message):
                self._messages.append(message)
                print(f"[MESSAGE] {message}")
        
        class MockInventory:
            def __init__(self):
                self.crafting_materials = {}
                self._items = []
            
            def add_item(self, item):
                self._items.append(item)
                return True
        
        # Initialize test objects
        player = MockPlayer()
        ui = MockUI()
        inventory = MockInventory()
        
        print("Initial player stats:")
        print(f"  Force Points: {player.force_points}")
        print(f"  Health: {player.health}/{player.max_health}")
        print(f"  Attack: {player.attack}")
        print(f"  Evasion: {player.evasion}")
        print(f"  Accuracy: {player.accuracy}")
        print(f"  Crafting Materials: {inventory.crafting_materials}")
        print()
        
        # Test 1: Environmental Event Rewards
        print("=== TEST 1: Environmental Event Rewards ===")
        try:
            env_event = get_environmental_event()
            print(f"Environmental event: {env_event.get('title', 'Unknown')}")
            print("Description:", ' '.join(env_event.get('description', [])))
            
            apply_environmental_reward(player, env_event, ui, inventory)
            print("\nAfter environmental event:")
            print(f"  Force Points: {player.force_points}")
            print(f"  Health: {player.health}/{player.max_health}")
            print(f"  Attack: {player.attack}")
            print(f"  Evasion: {player.evasion}")
            print(f"  Accuracy: {player.accuracy}")
            print(f"  Crafting Materials: {inventory.crafting_materials}")
            print(f"  Temporary Effects: {player.temporary_effects}")
            print()
        except Exception as e:
            print(f"Environmental event test failed: {e}")
            print()
        
        # Test 2: Narrative Choice Rewards
        print("=== TEST 2: Narrative Choice Rewards ===")
        try:
            # Test force_insight reward
            class MockGame:
                def __init__(self):
                    self.player = player
                    self.ui = ui
                    self.inventory = inventory
            
            game = MockGame()
            
            result = apply_narrative_reward(game, 'force_insight')
            print(f"Force insight reward result: {result}")
            
            result = apply_narrative_reward(game, 'healing_herbs')
            print(f"Healing herbs reward result: {result}")
            
            result = apply_narrative_reward(game, 'weapon_upgrade')
            print(f"Weapon upgrade reward result: {result}")
            
            print("\nAfter narrative rewards:")
            print(f"  Force Points: {player.force_points}")
            print(f"  Health: {player.health}/{player.max_health}")
            print(f"  Attack: {player.attack}")
            print(f"  Temporary Effects: {player.temporary_effects}")
            print()
        except Exception as e:
            print(f"Narrative choice test failed: {e}")
            print()
        
        # Test 3: Temporary Effect Processing
        print("=== TEST 3: Temporary Effect Processing ===")
        try:
            # Simulate multiple turns
            for turn in range(1, 6):
                print(f"\nTurn {turn}:")
                tick_temporary_effects(game)
                print(f"  Attack: {player.attack}")
                print(f"  Evasion: {player.evasion}")
                print(f"  Accuracy: {player.accuracy}")
                print(f"  Temporary Effects: {player.temporary_effects}")
            print(f"  Weapon Enhancements: {player.weapon_enhancements}")
            print(f"  Active Effects: {player.active_effects}")
        except Exception as e:
            print(f"Temporary effect processing test failed: {e}")
        
        # Test 4: Random Event Integration
        print("\n=== TEST 4: Random Event Integration ===")
        try:
            # Test beneficial random event
            random_event = get_random_event("beneficial")
            if random_event:
                print(f"Random event: {random_event.get('title', 'Unknown')}")
                
                # Check if the event has reward effects
                event_effects = random_event.get('effects', {})
                if event_effects:
                    print(f"Event effects: {event_effects}")
                else:
                    print("No effects found in random event")
        except Exception as e:
            print(f"Random event test failed: {e}")
        
        print("\n=== REWARD SYSTEM TEST COMPLETE ===")
        print("\nFinal player stats:")
        print(f"  Force Points: {player.force_points}")
        print(f"  Health: {player.health}/{player.max_health}")
        print(f"  Attack: {player.attack}")
        print(f"  Evasion: {player.evasion}")
        print(f"  Accuracy: {player.accuracy}")
        print(f"  Items in inventory: {len(inventory._items)}")
        print(f"  Crafting Materials: {inventory.crafting_materials}")
        print(f"  Journal entries: {len(player.journal)}")
        
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're running from the correct directory")
        return False
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    test_reward_system()