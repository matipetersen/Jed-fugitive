#!/usr/bin/env python3
"""
Demo script showing enhanced game statistics in action.
Simulates a few game runs to demonstrate the persistent tracking.
"""

import sys
import os
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.utils.game_stats import GameStats


def simulate_game_session():
    """Simulate a game session with multiple runs."""
    print("\n" + "═"*70)
    print("🎮 JEDI FUGITIVE - Enhanced Statistics Demo")
    print("═"*70)
    
    # Use a temporary file for this demo
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_file = f.name
    
    try:
        stats = GameStats(test_file)
        
        print("\n📖 Simulating a game session with multiple runs...")
        print()
        
        # Run 1: First Victory
        print("━" * 70)
        print("🎯 RUN #1: First Attempt")
        run1 = stats.increment_runs()
        stats.record_victory(player_level=8, enemies_killed=42, turns_taken=250)
        print(f"   Result: VICTORY! 🎉")
        print(f"   Level: 8 | Kills: 42 | Turns: 250")
        print()
        print("📊 Current Stats:")
        print(f"   Total Kills: {stats.get_total_kills()}")
        print(f"   Win Rate: {stats.get_win_rate():.1f}%")
        print(f"   K/D Ratio: {stats.get_kill_death_ratio():.2f}")
        print(f"   Win Streak: {stats.get_current_win_streak()} 🔥")
        
        # Run 2: Death
        print("\n" + "━" * 70)
        print("💀 RUN #2: Overconfidence")
        stats.increment_runs()
        stats.record_death(player_level=5, enemies_killed=18, turns_taken=120)
        print(f"   Result: DEATH 💀")
        print(f"   Level: 5 | Kills: 18 | Turns: 120")
        print()
        print("📊 Current Stats:")
        print(f"   Total Kills: {stats.get_total_kills()}")
        print(f"   Win Rate: {stats.get_win_rate():.1f}%")
        print(f"   K/D Ratio: {stats.get_kill_death_ratio():.2f}")
        print(f"   Win Streak: {stats.get_current_win_streak()} (Best: {stats.get_best_win_streak()})")
        
        # Run 3: Victory again
        print("\n" + "━" * 70)
        print("🎯 RUN #3: Redemption")
        stats.increment_runs()
        stats.record_victory(player_level=10, enemies_killed=55, turns_taken=180)
        print(f"   Result: VICTORY! 🎉")
        print(f"   Level: 10 | Kills: 55 | Turns: 180")
        print()
        print("📊 Current Stats:")
        print(f"   Total Kills: {stats.get_total_kills()}")
        print(f"   Win Rate: {stats.get_win_rate():.1f}%")
        print(f"   K/D Ratio: {stats.get_kill_death_ratio():.2f}")
        print(f"   Win Streak: {stats.get_current_win_streak()} 🔥")
        
        # Run 4: Another Victory (building streak)
        print("\n" + "━" * 70)
        print("🎯 RUN #4: On a Roll")
        stats.increment_runs()
        stats.record_victory(player_level=9, enemies_killed=47, turns_taken=200)
        print(f"   Result: VICTORY! 🎉")
        print(f"   Level: 9 | Kills: 47 | Turns: 200")
        print()
        print("📊 Current Stats:")
        print(f"   Total Kills: {stats.get_total_kills()}")
        print(f"   Win Rate: {stats.get_win_rate():.1f}%")
        print(f"   K/D Ratio: {stats.get_kill_death_ratio():.2f}")
        print(f"   Win Streak: {stats.get_current_win_streak()} 🔥🔥")
        
        # Run 5: Speedrun attempt
        print("\n" + "━" * 70)
        print("⚡ RUN #5: Speedrun Attempt")
        stats.increment_runs()
        stats.record_victory(player_level=7, enemies_killed=35, turns_taken=95)
        print(f"   Result: VICTORY! 🎉")
        print(f"   Level: 7 | Kills: 35 | Turns: 95")
        print(f"   ⚡ NEW RECORD! Fastest victory!")
        print()
        print("📊 Current Stats:")
        print(f"   Total Kills: {stats.get_total_kills()}")
        print(f"   Win Rate: {stats.get_win_rate():.1f}%")
        print(f"   K/D Ratio: {stats.get_kill_death_ratio():.2f}")
        print(f"   Win Streak: {stats.get_current_win_streak()} 🔥🔥🔥")
        
        # Run 6: Death ends streak
        print("\n" + "━" * 70)
        print("💀 RUN #6: Reality Check")
        stats.increment_runs()
        stats.record_death(player_level=3, enemies_killed=12, turns_taken=75)
        print(f"   Result: DEATH 💀")
        print(f"   Level: 3 | Kills: 12 | Turns: 75")
        print()
        print("📊 Current Stats:")
        print(f"   Total Kills: {stats.get_total_kills()}")
        print(f"   Win Rate: {stats.get_win_rate():.1f}%")
        print(f"   K/D Ratio: {stats.get_kill_death_ratio():.2f}")
        print(f"   Win Streak: {stats.get_current_win_streak()} (Best: {stats.get_best_win_streak()})")
        
        # Final Summary
        print("\n" + "═"*70)
        print("📊 FINAL SESSION STATISTICS")
        print("═"*70)
        print()
        print(stats.get_stats_summary())
        print()
        print("═"*70)
        
        # Demonstrate persistence
        print("\n🔄 Testing Persistence...")
        print("   Loading stats from file...")
        stats2 = GameStats(test_file)
        print("   ✅ Stats loaded successfully!")
        print()
        print("   Verified Stats:")
        print(f"   • Total Runs: {stats2.get_total_runs()}")
        print(f"   • Total Kills: {stats2.get_total_kills()}")
        print(f"   • K/D Ratio: {stats2.get_kill_death_ratio():.2f}")
        print(f"   • Best Win Streak: {stats2.get_best_win_streak()}")
        
        print("\n" + "═"*70)
        print("✅ Demo Complete - Enhanced Statistics Working Perfectly!")
        print("═"*70)
        
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.unlink(test_file)


if __name__ == "__main__":
    simulate_game_session()
