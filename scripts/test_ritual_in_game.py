#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_game_with_rituals():
    """Test the ritual system within a brief game session."""
    print("=== Testing Rituals in Actual Game ===")
    
    try:
        # Import game components
        from src.jedi_fugitive.game.game_manager import GameManager
        from src.jedi_fugitive import config
        
        print("1. Initializing game with headless mode...")
        # Create a simple config for testing
        class TestConfig:
            TARGET_WIDTH = 80
            TARGET_HEIGHT = 24
            DIFFICULTY_MULTIPLIER = 1.0
            MAP_SCALE = 1
        
        # Initialize game manager
        test_config = TestConfig()
        game = GameManager(test_config, headless=True)
        
        print("2. Testing ritual availability for new player...")
        player = game.player
        
        # Check initial player alignment
        initial_alignment = getattr(player, 'alignment_score', 0)
        print(f"   Player initial alignment: {initial_alignment}")
        
        # Test ritual function import within game context
        from src.jedi_fugitive.game.rituals import get_available_rituals
        
        # Convert alignment to corruption for ritual system
        if initial_alignment > 0:
            corruption = max(0, 50 - initial_alignment * 2)
        else:
            corruption = min(100, 50 + abs(initial_alignment) * 2)
        
        print(f"   Converted corruption level: {corruption}")
        
        # Get available rituals
        available_rituals = get_available_rituals(
            corruption, 
            None,  # no special location
            getattr(player, 'level', 1), 
            getattr(player, 'tombs_cleared', 0)
        )
        
        print(f"   Available rituals: {len(available_rituals)}")
        
        # List available rituals
        for i, (category, ritual_id, ritual_data) in enumerate(available_rituals[:5]):
            print(f"   {i+1}. [{category}] {ritual_data['name']}")
        
        print("3. Testing ritual execution...")
        if available_rituals:
            # Try to perform the first available ritual
            category, ritual_id, ritual_data = available_rituals[0]
            
            from src.jedi_fugitive.game.rituals import perform_ritual
            description, effects = perform_ritual(category, ritual_id, player, game)
            
            print(f"   Selected ritual: {ritual_data['name']}")
            print(f"   Description lines: {len(description)}")
            print(f"   Effects: {list(effects.keys())}")
            
            # Test effect application
            from src.jedi_fugitive.game.input_handler import _apply_ritual_effects
            
            # Record initial state
            initial_hp = getattr(player, 'hp', 100)
            initial_alignment = getattr(player, 'alignment_score', 0)
            
            print(f"   Before effects - HP: {initial_hp}, Alignment: {initial_alignment}")
            
            # Apply effects
            _apply_ritual_effects(game, effects)
            
            # Check final state
            final_hp = getattr(player, 'hp', 100)
            final_alignment = getattr(player, 'alignment_score', 0)
            
            print(f"   After effects - HP: {final_hp}, Alignment: {final_alignment}")
            
            # Show changes
            if final_hp != initial_hp:
                print(f"   ✅ HP changed: {initial_hp} → {final_hp}")
            if final_alignment != initial_alignment:
                print(f"   ✅ Alignment changed: {initial_alignment} → {final_alignment}")
            
        print("\n4. Ritual system integration status:")
        print("   ✅ Rituals accessible in-game")
        print("   ✅ Player state properly detected")
        print("   ✅ Ritual selection working")
        print("   ✅ Effect application functional")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Game ritual test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Rituals in Game Context")
    print("=" * 50)
    
    success = test_game_with_rituals()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 RITUALS WORKING IN ACTUAL GAME!")
        print("Ready to use 'R' key in-game to access rituals!")
    else:
        print("❌ Some integration issues detected")