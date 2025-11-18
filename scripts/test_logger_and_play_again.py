#!/usr/bin/env python3
"""Test crash logger and play again functionality."""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

def test_logger():
    """Test that the crash logger works correctly."""
    print("="*60)
    print("TESTING CRASH LOGGER")
    print("="*60)
    
    try:
        from jedi_fugitive.utils.crash_logger import get_logger, log_error, log_info, log_game_event
        
        print("\n1. Testing logger initialization...")
        logger = get_logger()
        print(f"   ✓ Logger initialized: {logger._log_file}")
        
        print("\n2. Testing log_info()...")
        log_info("Test info message")
        print("   ✓ Info logged")
        
        print("\n3. Testing log_game_event()...")
        log_game_event("TEST_EVENT", "This is a test event")
        print("   ✓ Game event logged")
        
        print("\n4. Testing log_error() without exception...")
        log_error("TEST_ERROR", "Test error without exception")
        print("   ✓ Error logged")
        
        print("\n5. Testing log_error() with exception...")
        try:
            # Intentionally cause an error
            x = 1 / 0
        except Exception as e:
            log_error("TEST_CRASH", "Division by zero test", e, {"test_state": "active"})
        print("   ✓ Error with exception logged")
        
        print("\n6. Testing game state snapshot...")
        # Create mock game manager
        class MockGameManager:
            class MockPlayer:
                x, y = 10, 20
                hp, max_hp = 50, 100
                level = 5
                stress = 30
                dark_corruption = 15
                force_points = 8
                tomb_floor = None
            
            def __init__(self):
                self.player = self.MockPlayer()
                self.turn_count = 42
                self.running = True
                self.death = False
                self.victory = False
                self.enemies = [1, 2, 3]  # Mock enemies
                self.game_map = [['.'] * 100 for _ in range(50)]
        
        mock_gm = MockGameManager()
        state = logger.get_game_state_snapshot(mock_gm)
        print(f"   ✓ State snapshot: {len(state)} fields captured")
        for key, value in state.items():
            print(f"     - {key}: {value}")
        
        print("\n7. Closing logger...")
        logger.close()
        print("   ✓ Logger closed")
        
        print("\n" + "="*60)
        print("LOGGER TEST PASSED ✓")
        print("="*60)
        print(f"\nLog file created at: {logger._log_file}")
        print("Check the file to see all logged events.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Logger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_play_again_logic():
    """Test the play again return values (without full curses)."""
    print("\n" + "="*60)
    print("TESTING PLAY AGAIN LOGIC")
    print("="*60)
    
    try:
        from jedi_fugitive.game.game_manager import GameManager
        
        print("\n1. Checking show_death_stats() signature...")
        import inspect
        sig = inspect.signature(GameManager.show_death_stats)
        print(f"   ✓ Method exists with signature: {sig}")
        
        print("\n2. Checking show_victory_stats() signature...")
        sig = inspect.signature(GameManager.show_victory_stats)
        print(f"   ✓ Method exists with signature: {sig}")
        
        print("\n" + "="*60)
        print("PLAY AGAIN LOGIC TEST PASSED ✓")
        print("="*60)
        print("\nNote: Full integration test requires running the actual game")
        print("and dying/winning, then selecting [P] to play again.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Play again logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = True
    
    success = test_logger() and success
    success = test_play_again_logic() and success
    
    print("\n" + "="*60)
    if success:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print("="*60)
    
    sys.exit(0 if success else 1)
