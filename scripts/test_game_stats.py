#!/usr/bin/env python3
"""
Test script for persistent game statistics system.
"""

import sys
from pathlib import Path
import tempfile
import os

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_stats_initialization():
    """Test that stats initialize correctly"""
    from jedi_fugitive.utils.game_stats import GameStats
    
    print("Test 1: Stats initialization...")
    
    # Use temp file for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        stats = GameStats(stats_file=temp_file)
        
        assert stats.get_total_runs() == 0, "Initial runs should be 0"
        assert stats.get_total_victories() == 0, "Initial victories should be 0"
        assert stats.get_total_deaths() == 0, "Initial deaths should be 0"
        assert stats.get_win_rate() == 0.0, "Initial win rate should be 0.0"
        
        print("  ✓ Stats initialized with correct defaults")
        print(f"  ✓ Stats file: {temp_file}")
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
    print()

def test_increment_runs():
    """Test that run counter increments correctly"""
    from jedi_fugitive.utils.game_stats import GameStats
    
    print("Test 2: Run counter increments...")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        stats = GameStats(stats_file=temp_file)
        
        run1 = stats.increment_runs()
        assert run1 == 1, f"First run should be 1, got {run1}"
        
        run2 = stats.increment_runs()
        assert run2 == 2, f"Second run should be 2, got {run2}"
        
        run3 = stats.increment_runs()
        assert run3 == 3, f"Third run should be 3, got {run3}"
        
        assert stats.get_total_runs() == 3, "Total runs should be 3"
        
        print("  ✓ Run counter increments correctly")
        print(f"  ✓ Total runs: {stats.get_total_runs()}")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    print()

def test_persistence():
    """Test that stats persist across instances"""
    from jedi_fugitive.utils.game_stats import GameStats
    
    print("Test 3: Stats persistence...")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        # First instance
        stats1 = GameStats(stats_file=temp_file)
        stats1.increment_runs()
        stats1.increment_runs()
        stats1.record_victory(player_level=5, enemies_killed=20)
        
        # Second instance (should load from file)
        stats2 = GameStats(stats_file=temp_file)
        
        assert stats2.get_total_runs() == 2, f"Persisted runs should be 2, got {stats2.get_total_runs()}"
        assert stats2.get_total_victories() == 1, f"Persisted victories should be 1, got {stats2.get_total_victories()}"
        
        print("  ✓ Stats persist across instances")
        print(f"  ✓ Loaded runs: {stats2.get_total_runs()}")
        print(f"  ✓ Loaded victories: {stats2.get_total_victories()}")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    print()

def test_victory_tracking():
    """Test that victories are tracked correctly"""
    from jedi_fugitive.utils.game_stats import GameStats
    
    print("Test 4: Victory tracking...")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        stats = GameStats(stats_file=temp_file)
        stats.increment_runs()
        stats.increment_runs()
        stats.increment_runs()
        
        stats.record_victory(player_level=5, enemies_killed=20)
        stats.record_victory(player_level=8, enemies_killed=35)
        
        assert stats.get_total_victories() == 2, "Should have 2 victories"
        assert stats.stats['highest_level'] == 8, "Highest level should be 8"
        assert stats.stats['most_enemies_killed'] == 35, "Most enemies killed should be 35"
        
        print("  ✓ Victories tracked correctly")
        print(f"  ✓ Total victories: {stats.get_total_victories()}")
        print(f"  ✓ Highest level: {stats.stats['highest_level']}")
        print(f"  ✓ Most enemies killed: {stats.stats['most_enemies_killed']}")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    print()

def test_death_tracking():
    """Test that deaths are tracked correctly"""
    from jedi_fugitive.utils.game_stats import GameStats
    
    print("Test 5: Death tracking...")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        stats = GameStats(stats_file=temp_file)
        stats.increment_runs()
        stats.increment_runs()
        stats.increment_runs()
        
        stats.record_death(player_level=3, enemies_killed=10)
        stats.record_death(player_level=4, enemies_killed=15)
        
        assert stats.get_total_deaths() == 2, "Should have 2 deaths"
        assert stats.stats['highest_level'] == 4, "Highest level should be 4"
        
        print("  ✓ Deaths tracked correctly")
        print(f"  ✓ Total deaths: {stats.get_total_deaths()}")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    print()

def test_win_rate():
    """Test win rate calculation"""
    from jedi_fugitive.utils.game_stats import GameStats
    
    print("Test 6: Win rate calculation...")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        stats = GameStats(stats_file=temp_file)
        
        # 10 runs: 7 victories, 3 deaths
        for _ in range(10):
            stats.increment_runs()
        
        for _ in range(7):
            stats.record_victory()
        
        for _ in range(3):
            stats.record_death()
        
        win_rate = stats.get_win_rate()
        expected = 70.0  # 7/10 * 100
        
        assert abs(win_rate - expected) < 0.1, f"Win rate should be ~{expected}%, got {win_rate}%"
        
        print("  ✓ Win rate calculated correctly")
        print(f"  ✓ Runs: {stats.get_total_runs()}")
        print(f"  ✓ Victories: {stats.get_total_victories()}")
        print(f"  ✓ Deaths: {stats.get_total_deaths()}")
        print(f"  ✓ Win Rate: {win_rate:.1f}%")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    print()

def test_stats_summary():
    """Test formatted stats summary"""
    from jedi_fugitive.utils.game_stats import GameStats
    
    print("Test 7: Stats summary formatting...")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        stats = GameStats(stats_file=temp_file)
        
        for _ in range(5):
            stats.increment_runs()
        
        stats.record_victory(player_level=10, enemies_killed=50)
        stats.record_victory(player_level=8, enemies_killed=40)
        stats.record_death(player_level=5, enemies_killed=20)
        
        summary = stats.get_stats_summary()
        
        assert "Total Runs: 5" in summary, "Summary should include total runs"
        assert "Victories: 2" in summary, "Summary should include victories"
        assert "Deaths: 1" in summary, "Summary should include deaths"
        assert "Win Rate:" in summary, "Summary should include win rate"
        assert "Highest Level: 10" in summary, "Summary should include highest level"
        assert "Most Enemies Killed: 50" in summary, "Summary should include most enemies killed"
        
        print("  ✓ Stats summary formatted correctly")
        print("\n--- Stats Summary ---")
        print(summary)
        print("---------------------")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    print()

def main():
    print("=" * 60)
    print("Testing Persistent Game Statistics System")
    print("=" * 60)
    print()
    
    try:
        test_stats_initialization()
        test_increment_runs()
        test_persistence()
        test_victory_tracking()
        test_death_tracking()
        test_win_rate()
        test_stats_summary()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print()
        print("Summary:")
        print("  • Stats initialize with correct defaults")
        print("  • Run counter increments properly")
        print("  • Stats persist across instances (file-based)")
        print("  • Victory/death tracking works")
        print("  • Win rate calculated correctly")
        print("  • Stats summary formats nicely")
        print()
        print("The game will now track your runs persistently!")
        print(f"Stats will be stored in: ~/.jedi_fugitive/game_stats.json")
        return 0
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
