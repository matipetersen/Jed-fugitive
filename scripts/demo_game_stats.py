#!/usr/bin/env python3
"""
Quick demo of the persistent game statistics system.
Shows how stats accumulate across multiple "game runs".
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from jedi_fugitive.utils.game_stats import get_game_stats

def main():
    print("=" * 60)
    print("Game Statistics Demo")
    print("=" * 60)
    print()
    
    stats = get_game_stats()
    
    print("Current Statistics:")
    print("-" * 40)
    print(stats.get_stats_summary())
    print("-" * 40)
    print()
    
    print("Simulating a new game run...")
    run_num = stats.increment_runs()
    print(f"  ✓ This is game run #{run_num}")
    print()
    
    # Show what happens after a victory
    print("Simulating a victory...")
    stats.record_victory(player_level=7, enemies_killed=25)
    print("  ✓ Victory recorded!")
    print()
    
    print("Updated Statistics:")
    print("-" * 40)
    print(stats.get_stats_summary())
    print("-" * 40)
    print()
    
    print(f"Stats file location: ~/.jedi_fugitive/game_stats.json")
    print()
    print("These stats persist across game sessions!")

if __name__ == "__main__":
    main()
