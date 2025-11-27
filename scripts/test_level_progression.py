#!/usr/bin/env python3
"""Test level progression consistency between paths and GUI display."""
import sys
sys.path.insert(0, '/Users/matiaspetersen/Documents/Spider/ScholarsOf/jedi-fugitive/src')

from jedi_fugitive.game.player import Player

def test_level_sync():
    """Test that player.level stays synchronized with the dual path system."""
    print("Testing level synchronization...")
    
    # Create a player
    player = Player(x=0, y=0)
    
    # Initial state
    if player.level != 1:
        print(f"❌ Initial level should be 1, got {player.level}")
        return False
    
    # Simulate light path level up
    player.light_level = 2
    player.light_xp = 0
    player.xp_to_next_light = 125
    player.level_up()
    
    if player.level < 2:
        print(f"❌ After light level up, player.level should be at least 2, got {player.level}")
        return False
    
    # Simulate dark path level up
    player.dark_level = 3
    player.dark_xp = 0
    player.xp_to_next_dark = 156
    player.level_up()
    
    expected_level = max(player.light_level, player.dark_level)
    if player.level < expected_level:
        print(f"❌ player.level ({player.level}) should be at least {expected_level}")
        return False
    
    print(f"✅ Level synchronization works: player.level={player.level}, light={player.light_level}, dark={player.dark_level}")
    return True

def test_stats_display_level():
    """Test that stats display shows the correct level."""
    print("\nTesting stats display level...")
    
    player = Player(x=0, y=0)
    
    # Set up dual path
    player.level = 5
    player.light_level = 3
    player.dark_level = 5
    player.light_xp = 50
    player.dark_xp = 75
    player.xp_to_next_light = 156
    player.xp_to_next_dark = 195
    player.corruption = 60
    
    # Get stats display
    stats = player.get_stats_display()
    
    if not stats:
        print("❌ Stats display returned empty")
        return False
    
    # Check that level line exists and shows correct value
    level_line = stats[0] if stats else ""
    if "Level:" not in level_line:
        print(f"❌ First line should show Level, got: {level_line}")
        return False
    
    # Extract level number from display
    try:
        # Format: "Level: 5 (75/195 XP)"
        level_part = level_line.split("(")[0].strip()  # "Level: 5"
        displayed_level = int(level_part.split(": ")[1])
        
        if displayed_level != player.level:
            print(f"❌ Displayed level ({displayed_level}) != player.level ({player.level})")
            return False
        
        # Should show dark path XP since dark_level >= light_level
        if "75/195" not in level_line:
            print(f"❌ Should show dark path XP (75/195), got: {level_line}")
            return False
        
    except Exception as e:
        print(f"❌ Failed to parse level line: {e}")
        print(f"   Line: {level_line}")
        return False
    
    # Check corruption display
    corruption_line = stats[1] if len(stats) > 1 else ""
    if "Corruption: 60%" not in corruption_line:
        print(f"❌ Corruption line should show 60%, got: {corruption_line}")
        return False
    
    print(f"✅ Stats display shows correct level: {level_line}")
    print(f"✅ Stats display shows correct corruption: {corruption_line}")
    return True

def test_light_vs_dark_progression():
    """Test that light and dark path progress independently."""
    print("\nTesting independent path progression...")
    
    player = Player(x=0, y=0)
    
    # Progress light path
    player.light_level = 4
    player.light_xp = 100
    player.xp_to_next_light = 195
    
    # Progress dark path
    player.dark_level = 2
    player.dark_xp = 50
    player.xp_to_next_dark = 125
    
    # Sync level
    player.level = max(player.light_level, player.dark_level)
    
    if player.level != 4:
        print(f"❌ player.level should be 4 (max of light=4, dark=2), got {player.level}")
        return False
    
    # Get stats - should show light path since light_level > dark_level
    stats = player.get_stats_display()
    level_line = stats[0]
    
    if "100/195" not in level_line:
        print(f"❌ Should show light path XP (100/195), got: {level_line}")
        return False
    
    print(f"✅ Independent path progression works correctly")
    print(f"   Light: Lvl {player.light_level}, {player.light_xp}/{player.xp_to_next_light} XP")
    print(f"   Dark: Lvl {player.dark_level}, {player.dark_xp}/{player.xp_to_next_dark} XP")
    print(f"   Player: Lvl {player.level} (synced to highest)")
    return True

def test_corruption_attribute():
    """Test that corruption attribute is correctly named."""
    print("\nTesting corruption attribute...")
    
    player = Player(x=0, y=0)
    
    # Set corruption
    player.corruption = 45
    
    # Verify it's accessible
    if not hasattr(player, 'corruption'):
        print("❌ Player missing 'corruption' attribute")
        return False
    
    if player.corruption != 45:
        print(f"❌ Corruption should be 45, got {player.corruption}")
        return False
    
    # Check stats display uses it correctly
    stats = player.get_stats_display()
    corruption_line = stats[1] if len(stats) > 1 else ""
    
    if "Corruption: 45%" not in corruption_line:
        print(f"❌ Corruption display should show 45%, got: {corruption_line}")
        return False
    
    print(f"✅ Corruption attribute works correctly: {corruption_line}")
    return True

def main():
    print("="*60)
    print("LEVEL PROGRESSION TEST SUITE".center(60))
    print("="*60)
    
    tests = [
        test_level_sync,
        test_stats_display_level,
        test_light_vs_dark_progression,
        test_corruption_attribute,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
