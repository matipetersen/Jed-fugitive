#!/usr/bin/env python3
"""
Test script for enhanced persistent game statistics.
Tests K/D ratio, win streaks, and total kills tracking.
"""

import sys
import os
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.utils.game_stats import GameStats


def test_enhanced_stats():
    """Test all enhanced statistics features."""
    print("\n" + "="*60)
    print("Testing Enhanced Game Statistics")
    print("="*60)
    
    # Use a temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_file = f.name
    
    try:
        stats = GameStats(test_file)
        
        # Test 1: Initial state
        print("\n[Test 1] Initial State")
        assert stats.get_total_runs() == 0
        assert stats.get_total_victories() == 0
        assert stats.get_total_deaths() == 0
        assert stats.get_total_kills() == 0
        assert stats.get_kill_death_ratio() == 0.0
        assert stats.get_current_win_streak() == 0
        assert stats.get_best_win_streak() == 0
        print("  ✓ All counters start at 0")
        
        # Test 2: Record first run - increment
        print("\n[Test 2] Increment Runs")
        run1 = stats.increment_runs()
        assert run1 == 1
        assert stats.get_total_runs() == 1
        print(f"  ✓ Run counter: {stats.get_total_runs()}")
        
        # Test 3: Record a victory
        print("\n[Test 3] Record Victory")
        stats.record_victory(player_level=5, enemies_killed=15, turns_taken=100)
        assert stats.get_total_victories() == 1
        assert stats.get_total_kills() == 15
        assert stats.get_current_win_streak() == 1
        assert stats.get_best_win_streak() == 1
        print(f"  ✓ Victories: {stats.get_total_victories()}")
        print(f"  ✓ Total Kills: {stats.get_total_kills()}")
        print(f"  ✓ Win Streak: {stats.get_current_win_streak()}")
        
        # Test 4: K/D ratio with no deaths
        print("\n[Test 4] K/D Ratio (No Deaths)")
        kd = stats.get_kill_death_ratio()
        assert kd == 15.0  # 15 kills / 0 deaths = 15.0
        print(f"  ✓ K/D Ratio: {kd:.2f}")
        
        # Test 5: Another victory (win streak)
        print("\n[Test 5] Win Streak Build")
        stats.increment_runs()
        stats.record_victory(player_level=6, enemies_killed=20, turns_taken=120)
        assert stats.get_total_victories() == 2
        assert stats.get_total_kills() == 35  # 15 + 20
        assert stats.get_current_win_streak() == 2
        assert stats.get_best_win_streak() == 2
        print(f"  ✓ Win Streak: {stats.get_current_win_streak()}")
        print(f"  ✓ Total Kills: {stats.get_total_kills()}")
        
        # Test 6: Record a death (resets streak)
        print("\n[Test 6] Death Resets Streak")
        stats.increment_runs()
        stats.record_death(player_level=3, enemies_killed=8, turns_taken=50)
        assert stats.get_total_deaths() == 1
        assert stats.get_total_kills() == 43  # 35 + 8
        assert stats.get_current_win_streak() == 0  # Reset
        assert stats.get_best_win_streak() == 2  # Preserved
        print(f"  ✓ Deaths: {stats.get_total_deaths()}")
        print(f"  ✓ Current Streak: {stats.get_current_win_streak()}")
        print(f"  ✓ Best Streak: {stats.get_best_win_streak()}")
        
        # Test 7: K/D ratio calculation
        print("\n[Test 7] K/D Ratio Calculation")
        kd = stats.get_kill_death_ratio()
        expected_kd = 43.0 / 1.0  # 43 kills / 1 death
        assert abs(kd - expected_kd) < 0.01
        print(f"  ✓ K/D Ratio: {kd:.2f}")
        
        # Test 8: Win rate
        print("\n[Test 8] Win Rate")
        win_rate = stats.get_win_rate()
        expected_rate = (2.0 / 3.0) * 100  # 2 victories out of 3 runs
        assert abs(win_rate - expected_rate) < 0.01
        print(f"  ✓ Win Rate: {win_rate:.1f}%")
        
        # Test 9: Persistence
        print("\n[Test 9] Stats Persistence")
        stats2 = GameStats(test_file)
        assert stats2.get_total_runs() == 3
        assert stats2.get_total_victories() == 2
        assert stats2.get_total_deaths() == 1
        assert stats2.get_total_kills() == 43
        assert stats2.get_current_win_streak() == 0
        assert stats2.get_best_win_streak() == 2
        print("  ✓ Stats loaded correctly from file")
        
        # Test 10: Stats summary
        print("\n[Test 10] Stats Summary")
        summary = stats.get_stats_summary()
        print("\nFormatted Summary:")
        print("-" * 40)
        print(summary)
        print("-" * 40)
        assert "Total Runs: 3" in summary
        assert "K/D Ratio:" in summary
        assert "Win Streak:" in summary
        print("  ✓ Summary generated correctly")
        
        # Test 11: Fastest victory tracking
        print("\n[Test 11] Fastest Victory")
        stats.increment_runs()
        stats.record_victory(player_level=7, enemies_killed=25, turns_taken=80)
        fastest = stats.stats.get("fastest_victory_turns", 0)
        assert fastest == 80  # Should be the fastest so far
        print(f"  ✓ Fastest Victory: {fastest} turns")
        
        # Test 12: Multiple deaths K/D calculation
        print("\n[Test 12] K/D with Multiple Deaths")
        stats.increment_runs()
        stats.record_death(player_level=2, enemies_killed=5, turns_taken=30)
        stats.increment_runs()
        stats.record_death(player_level=1, enemies_killed=2, turns_taken=20)
        kd = stats.get_kill_death_ratio()
        # (43 + 25 + 5 + 2) / 3 = 75 / 3 = 25.0
        expected_kd = 75.0 / 3.0
        assert abs(kd - expected_kd) < 0.01
        print(f"  ✓ K/D Ratio: {kd:.2f} (75 kills / 3 deaths)")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        
        # Show final stats
        print("\n📊 Final Statistics:")
        print(stats.get_stats_summary())
        
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.unlink(test_file)


if __name__ == "__main__":
    test_enhanced_stats()
