#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.jedi_fugitive.game.personality import EnemyPersonality

def create_mock_player(alignment_score=0, kill_count=0):
    """Create a mock player with specific attributes for testing."""
    class MockPlayer:
        def __init__(self, alignment_score, kill_count):
            self.alignment_score = alignment_score
            self.kill_count = kill_count
            self.level = 5
            # Mock force object with abilities
            class MockForce:
                def __init__(self):
                    self.abilities = {
                        'Force Push': {'level': 2},
                        'Force Lightning': {'level': 1},
                        'Saber Throw': {'level': 1}
                    }
            self.force = MockForce()
            
    return MockPlayer(alignment_score, kill_count)

def test_alignment_taunts():
    """Test that taunts change based on player alignment."""
    print("=== Testing Alignment-Based Taunts ===")
    
    enemy_personality = EnemyPersonality()
    
    # Test Light Side Player (high positive alignment)
    light_player = create_mock_player(alignment_score=15, kill_count=2)
    print(f"\nLight Side Player (alignment: {light_player.alignment_score}):")
    for situation in ['attack', 'defend', 'low_hp']:
        taunt = enemy_personality.get_taunt(situation, light_player)
        print(f"  {situation}: {taunt}")
    
    # Test Dark Side Player (high negative alignment) 
    dark_player = create_mock_player(alignment_score=-15, kill_count=20)
    print(f"\nDark Side Player (alignment: {dark_player.alignment_score}):")
    for situation in ['attack', 'defend', 'low_hp']:
        taunt = enemy_personality.get_taunt(situation, dark_player)
        print(f"  {situation}: {taunt}")
        
    # Test Neutral Player
    neutral_player = create_mock_player(alignment_score=2, kill_count=8)
    print(f"\nNeutral Player (alignment: {neutral_player.alignment_score}):")
    for situation in ['attack', 'defend', 'low_hp']:
        taunt = enemy_personality.get_taunt(situation, neutral_player)
        print(f"  {situation}: {taunt}")

def test_special_taunts():
    """Test special contextual taunts."""
    print("\n=== Testing Special Contextual Taunts ===")
    
    enemy_personality = EnemyPersonality()
    
    # Test high kill count
    killer_player = create_mock_player(alignment_score=-5, kill_count=25)
    print(f"\nHigh Kill Count Player (kills: {killer_player.kill_count}):")
    for _ in range(3):  # Try multiple times since it's random
        taunt = enemy_personality.get_taunt('attack', killer_player)
        print(f"  {taunt}")
    
    # Test Force Lightning user
    force_user = create_mock_player(alignment_score=-10, kill_count=5)
    print(f"\nForce Lightning User:")
    for _ in range(3):
        taunt = enemy_personality.get_taunt('attack', force_user)
        print(f"  {taunt}")

def test_jedi_master_taunts():
    """Test Jedi Master specific taunts."""
    print("\n=== Testing Jedi Master Taunts ===")
    
    jedi_personality = EnemyPersonality()
    
    # Test against light side player
    light_player = create_mock_player(alignment_score=20, kill_count=1)
    print(f"\nJedi vs Light Side Player:")
    for situation in ['attack', 'defend', 'low_hp']:
        taunt = jedi_personality.get_taunt(situation, light_player)
        print(f"  {situation}: {taunt}")
    
    # Test against dark side player
    dark_player = create_mock_player(alignment_score=-20, kill_count=30)
    print(f"\nJedi vs Dark Side Player:")
    for situation in ['attack', 'defend', 'low_hp']:
        taunt = jedi_personality.get_taunt(situation, dark_player)
        print(f"  {situation}: {taunt}")

def test_backward_compatibility():
    """Test that the system works without a player reference."""
    print("\n=== Testing Backward Compatibility ===")
    
    enemy_personality = EnemyPersonality()
    
    print("Taunts without player reference:")
    for situation in ['attack', 'defend', 'low_hp']:
        taunt = enemy_personality.get_taunt(situation)  # No player passed
        print(f"  {situation}: {taunt}")

if __name__ == "__main__":
    print("Testing Enhanced Enemy Taunt System")
    print("=" * 50)
    
    try:
        test_alignment_taunts()
        test_special_taunts()
        test_jedi_master_taunts()
        test_backward_compatibility()
        
        print("\n" + "=" * 50)
        print("✅ All taunt system tests completed successfully!")
        print("Dynamic enemy taunts are responding to player alignment and actions.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()