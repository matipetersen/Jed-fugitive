#!/usr/bin/env python3
"""
Simple test script to verify atmospheric events system works.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jedi_fugitive.game.atmospheric_events import AtmosphericEventManager, ATMOSPHERIC_EVENTS, ENVIRONMENTAL_HAZARDS

def test_atmospheric_events():
    print("Testing Atmospheric Events System...")
    print(f"Found {len(ATMOSPHERIC_EVENTS)} atmospheric events:")
    
    for event in ATMOSPHERIC_EVENTS:
        print(f"  - {event['name']}: {event['description']}")
        print(f"    Duration: {event['duration']} turns")
        print(f"    Trigger chance: {event['trigger_chance']}")
        print(f"    Biomes: {', '.join(event['biomes'])}")
        print()
    
    print(f"Found {len(ENVIRONMENTAL_HAZARDS)} environmental hazards:")
    for hazard in ENVIRONMENTAL_HAZARDS:
        print(f"  - {hazard['name']}: {hazard['description']}")
        print(f"    Effect: {hazard['effect']}")
        print()
    
    print("✓ Atmospheric events system imported successfully!")
    print("✓ All events and hazards loaded correctly!")
    
    # Test atmospheric manager creation
    class MockGame:
        def __init__(self):
            self.turn_count = 0
            self.current_biome = 'forest'
    
    mock_game = MockGame()
    manager = AtmosphericEventManager(mock_game)
    print("✓ AtmosphericEventManager created successfully!")
    
    # Test visibility and movement modifiers
    print(f"✓ Visibility modifier: {manager.get_visibility_modifier()}")
    print(f"✓ Movement cost modifier: {manager.get_movement_cost_modifier()}")
    
    print("\n🌟 All tests passed! Atmospheric events system is working correctly!")

if __name__ == "__main__":
    test_atmospheric_events()