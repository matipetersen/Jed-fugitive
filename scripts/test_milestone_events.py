#!/usr/bin/env python3
"""Test milestone events system."""
import sys
sys.path.insert(0, '/Users/matiaspetersen/Documents/Spider/ScholarsOf/jedi-fugitive/src')

from jedi_fugitive.game.milestone_events import (
    FIRST_SITH_DEFEATED,
    FIRST_TOMB_DISCOVERED,
    CORRUPTION_MILESTONE_25,
    CORRUPTION_MILESTONE_50,
    CORRUPTION_MILESTONE_75,
    LEVEL_MILESTONES,
    KILL_MILESTONES,
    TOMB_DEPTH_MILESTONES,
    ARTIFACT_MILESTONES,
    get_alignment_category,
    format_milestone_display,
    get_journal_entry_for_milestone,
    check_milestone_trigger,
    get_all_pending_milestones,
)

# Mock player class for testing
class MockPlayer:
    def __init__(self):
        self.level = 1
        self.corruption = 0
        self.total_kills = 0
        self.artifacts_collected = []
        self.max_tomb_depth = 0
        self.tombs_discovered = 0
        self.max_hp = 100
        self.hp = 100
        self.max_force = 100
        self.force = 100

def test_alignment_categories():
    """Test alignment category determination."""
    print("Testing alignment categories...")
    
    if get_alignment_category(0) != 'light':
        print("❌ 0 corruption should be 'light'")
        return False
    
    if get_alignment_category(35) != 'light':
        print("❌ 35 corruption should be 'light'")
        return False
    
    if get_alignment_category(50) != 'balanced':
        print("❌ 50 corruption should be 'balanced'")
        return False
    
    if get_alignment_category(70) != 'dark':
        print("❌ 70 corruption should be 'dark'")
        return False
    
    print("✅ Alignment categories work correctly")
    return True

def test_first_kill_milestone():
    """Test first Sith defeated milestone."""
    print("\nTesting first Sith defeated milestone...")
    
    player = MockPlayer()
    
    # Should not trigger with 0 kills
    if check_milestone_trigger(player, 'first_sith', 1):
        print("❌ First kill triggered with 0 kills")
        return False
    
    # Should trigger with 1 kill
    player.total_kills = 1
    if not check_milestone_trigger(player, 'first_sith', 1):
        print("❌ First kill didn't trigger with 1 kill")
        return False
    
    # Should not trigger twice
    if check_milestone_trigger(player, 'first_sith', 1):
        print("❌ First kill triggered twice")
        return False
    
    # Check milestone data
    if 'title' not in FIRST_SITH_DEFEATED:
        print("❌ First Sith milestone missing title")
        return False
    
    if FIRST_SITH_DEFEATED['title'] != 'First Blood':
        print(f"❌ Expected title 'First Blood', got {FIRST_SITH_DEFEATED['title']}")
        return False
    
    # Check all alignment messages exist
    for alignment in ['light', 'balanced', 'dark']:
        if alignment not in FIRST_SITH_DEFEATED['messages']:
            print(f"❌ Missing {alignment} messages")
            return False
        if len(FIRST_SITH_DEFEATED['messages'][alignment]) < 3:
            print(f"❌ {alignment} messages too short")
            return False
    
    print("✅ First Sith defeated milestone works correctly")
    return True

def test_corruption_milestones():
    """Test corruption threshold milestones."""
    print("\nTesting corruption milestones...")
    
    player = MockPlayer()
    
    # Test 25% threshold
    player.corruption = 24
    if check_milestone_trigger(player, 'corruption', 25):
        print("❌ 25% milestone triggered at 24 corruption")
        return False
    
    player.corruption = 25
    if not check_milestone_trigger(player, 'corruption', 25):
        print("❌ 25% milestone didn't trigger at 25 corruption")
        return False
    
    # Test 50% threshold
    player.corruption = 50
    if not check_milestone_trigger(player, 'corruption', 50):
        print("❌ 50% milestone didn't trigger at 50 corruption")
        return False
    
    # Test 75% threshold
    player.corruption = 75
    if not check_milestone_trigger(player, 'corruption', 75):
        print("❌ 75% milestone didn't trigger at 75 corruption")
        return False
    
    # Verify milestone data
    for threshold, milestone in [(25, CORRUPTION_MILESTONE_25), 
                                   (50, CORRUPTION_MILESTONE_50),
                                   (75, CORRUPTION_MILESTONE_75)]:
        if 'title' not in milestone:
            print(f"❌ Corruption {threshold}% milestone missing title")
            return False
        if 'threshold' not in milestone or milestone['threshold'] != threshold:
            print(f"❌ Corruption {threshold}% milestone has wrong threshold")
            return False
        if len(milestone['messages']) < 4:
            print(f"❌ Corruption {threshold}% milestone has too few messages")
            return False
    
    print("✅ Corruption milestones work correctly")
    return True

def test_level_milestones():
    """Test level-up milestones."""
    print("\nTesting level milestones...")
    
    player = MockPlayer()
    
    # Test each level milestone
    for level in [5, 10, 15, 20]:
        player.level = level
        if not check_milestone_trigger(player, 'level', level):
            print(f"❌ Level {level} milestone didn't trigger")
            return False
        
        # Verify milestone data
        if level not in LEVEL_MILESTONES:
            print(f"❌ Level {level} milestone not defined")
            return False
        
        milestone = LEVEL_MILESTONES[level]
        if 'title' not in milestone:
            print(f"❌ Level {level} milestone missing title")
            return False
        
        # Check all alignment messages
        for alignment in ['light', 'balanced', 'dark']:
            if alignment not in milestone['messages']:
                print(f"❌ Level {level} missing {alignment} messages")
                return False
    
    print("✅ Level milestones work correctly")
    return True

def test_kill_count_milestones():
    """Test kill count milestones."""
    print("\nTesting kill count milestones...")
    
    player = MockPlayer()
    
    for count in [10, 25, 50, 100]:
        player.total_kills = count
        if not check_milestone_trigger(player, 'kills', count):
            print(f"❌ Kill count {count} milestone didn't trigger")
            return False
        
        if count not in KILL_MILESTONES:
            print(f"❌ Kill count {count} milestone not defined")
            return False
        
        milestone = KILL_MILESTONES[count]
        if 'title' not in milestone:
            print(f"❌ Kill count {count} milestone missing title")
            return False
    
    print("✅ Kill count milestones work correctly")
    return True

def test_formatting():
    """Test milestone display formatting."""
    print("\nTesting milestone formatting...")
    
    # Test with different corruption levels
    for corruption in [20, 50, 80]:
        formatted = format_milestone_display(FIRST_SITH_DEFEATED, corruption)
        
        if not formatted:
            print(f"❌ Formatting returned empty at {corruption} corruption")
            return False
        
        if not any('FIRST BLOOD' in line.upper() for line in formatted):
            print(f"❌ Formatted text missing title at {corruption} corruption")
            return False
    
    # Test journal entry retrieval
    for corruption in [20, 50, 80]:
        journal = get_journal_entry_for_milestone(FIRST_SITH_DEFEATED, corruption)
        if not journal:
            print(f"❌ No journal entry at {corruption} corruption")
            return False
        if len(journal) < 50:
            print(f"❌ Journal entry too short at {corruption} corruption")
            return False
    
    print("✅ Milestone formatting works correctly")
    return True

def test_pending_milestones():
    """Test getting all pending milestones."""
    print("\nTesting pending milestone detection...")
    
    player = MockPlayer()
    
    # No milestones should trigger initially
    pending = get_all_pending_milestones(player)
    if pending:
        print(f"❌ Found {len(pending)} milestones with new player (expected 0)")
        return False
    
    # Trigger first kill
    player.total_kills = 1
    pending = get_all_pending_milestones(player)
    if len(pending) != 1:
        print(f"❌ Expected 1 milestone after first kill, got {len(pending)}")
        return False
    
    # Trigger multiple milestones
    player.level = 5
    player.corruption = 25
    player.total_kills = 10
    pending = get_all_pending_milestones(player)
    
    # Should have: level 5, corruption 25, kills 10 (first_sith already triggered)
    expected_min = 3
    if len(pending) < expected_min:
        print(f"❌ Expected at least {expected_min} milestones, got {len(pending)}")
        return False
    
    print("✅ Pending milestone detection works correctly")
    return True

def test_statistics():
    """Test milestone statistics."""
    print("\nTesting milestone statistics...")
    
    # Count total milestones
    total = 0
    
    # Special milestones
    total += 2  # First Sith, First Tomb
    
    # Corruption milestones
    total += 3  # 25%, 50%, 75%
    
    # Level milestones
    total += len(LEVEL_MILESTONES)  # 4 levels
    
    # Kill milestones
    total += len(KILL_MILESTONES)  # 4 thresholds
    
    # Tomb depth milestones
    total += len(TOMB_DEPTH_MILESTONES)  # 3 depths
    
    # Artifact milestones
    total += len(ARTIFACT_MILESTONES)  # 3 counts
    
    print(f"✅ Statistics: {total} total milestone events")
    print(f"   - 2 special events (first kill, first tomb)")
    print(f"   - 3 corruption thresholds")
    print(f"   - {len(LEVEL_MILESTONES)} level milestones")
    print(f"   - {len(KILL_MILESTONES)} kill count milestones")
    print(f"   - {len(TOMB_DEPTH_MILESTONES)} tomb depth milestones")
    print(f"   - {len(ARTIFACT_MILESTONES)} artifact collection milestones")
    
    if total < 19:
        print(f"❌ Expected at least 19 milestones, found {total}")
        return False
    
    return True

def main():
    print("="*60)
    print("MILESTONE EVENTS TEST SUITE".center(60))
    print("="*60)
    
    tests = [
        test_alignment_categories,
        test_first_kill_milestone,
        test_corruption_milestones,
        test_level_milestones,
        test_kill_count_milestones,
        test_formatting,
        test_pending_milestones,
        test_statistics,
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
