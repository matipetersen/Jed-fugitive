#!/usr/bin/env python3
"""
Debug script to identify and fix two issues:
1. Invisible Sith Inquisitor attacking player
2. Mountain pass biome trapping player with no tomb access
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def check_sith_inquisitor_issue():
    """Check if Sith Inquisitor is spawning unexpectedly"""
    print("=" * 70)
    print("Issue 1: Invisible Sith Inquisitor")
    print("=" * 70)
    print()
    
    print("Problem: Player receives 'Sith Inquisitor siphons your energy' message")
    print("         but cannot see the enemy.")
    print()
    
    print("Root Cause:")
    print("  • Sith Inquisitor has AI that runs every 4 turns (turn_count % 4 == 0)")
    print("  • Siphons 2 Force points from player automatically")
    print("  • Located in enemies_sith.py:346")
    print()
    
    print("This enemy should ONLY spawn in:")
    print("  • Sith Keep (end-game dungeon)")
    print("  • NOT on the surface world")
    print()
    
    print("Possible causes of invisible enemy:")
    print("  1. Enemy spawned off-map or at invalid coordinates")
    print("  2. Enemy spawned outside player's vision range")
    print("  3. Enemy spawned in a wall/impassable tile")
    print("  4. Display symbol not rendering correctly")
    print()
    
    print("✓ Solution: Check enemy spawning logic to ensure proper placement")
    print()

def check_mountain_pass_issue():
    """Check mountain pass biome enclosure problem"""
    print("=" * 70)
    print("Issue 2: Mountain Pass Biome Enclosure")
    print("=" * 70)
    print()
    
    print("Problem: Player spawned in mountain_pass biome and cannot leave.")
    print("         Tomb was not discoverable.")
    print()
    
    print("Root Cause:")
    print("  • Mountain tiles have 80% chance to be walls (#)")
    print("  • Only 20% chance to be passable floor (.)")
    print("  • map_features.py:377")
    print()
    
    print("  • Tombs placed one per biome type (map_features.py:760-860)")
    print("  • If mountain_pass completely surrounded by walls:")
    print("    - Player trapped inside")
    print("    - Tomb spawns inside mountain_pass but unreachable")
    print("    - Other biomes' tombs blocked by mountain walls")
    print()
    
    print("✓ Solutions:")
    print("  1. Ensure mountain passes always have corridors to other biomes")
    print("  2. Never spawn player in mountain_pass biome")
    print("  3. Tombs should not spawn in mountain_pass biome")
    print("  4. Create guaranteed pathways through mountain ranges")
    print()

def recommend_fixes():
    """Recommend specific code fixes"""
    print("=" * 70)
    print("Recommended Fixes")
    print("=" * 70)
    print()
    
    print("Fix 1: Prevent Sith Inquisitor from spawning on surface")
    print("-" * 70)
    print("Location: src/jedi_fugitive/game/game_manager.py")
    print("          (enemy spawning code around line 2810)")
    print()
    print("Change:")
    print("  • Remove create_sith_inquisitor from random surface spawns")
    print("  • Verify it ONLY spawns in Sith Keep via sith_keep.py:218")
    print()
    
    print("Fix 2: Exclude mountain_pass from player spawn biomes")
    print("-" * 70)
    print("Location: src/jedi_fugitive/game/level.py")
    print("          (player placement logic)")
    print()
    print("Change:")
    print("  biome_types = ['forest', 'desert', 'rocky', 'plains', 'river']")
    print("  # Remove 'mountain_pass' from player spawn options")
    print()
    
    print("Fix 3: Exclude mountain_pass from tomb placement")
    print("-" * 70)
    print("Location: src/jedi_fugitive/game/map_features.py:777")
    print()
    print("Change:")
    print("  biome_types = ['forest', 'desert', 'rocky', 'plains', 'river']")
    print("  # Remove 'mountain_pass' - tombs should not spawn in mountains")
    print()
    
    print("Fix 4: Ensure mountain passes create corridors")
    print("-" * 70)
    print("Location: src/jedi_fugitive/game/map_features.py:377")
    print()
    print("Change mountain generation to create guaranteed passes:")
    print("  • Group mountain tiles into ranges")
    print("  • Create 2-3 wide corridors through each range")
    print("  • Ensure no biome can be completely enclosed")
    print()
    
    print("Fix 5: Add visibility check for enemy actions")
    print("-" * 70)
    print("Location: src/jedi_fugitive/game/enemies_sith.py:346")
    print()
    print("Add distance check before showing siphon message:")
    print("  if dist <= player_vision_range:")
    print("      game.ui.messages.add(f'{self.name} siphons your Force essence!')")
    print("  # Don't show message if enemy is invisible/too far")
    print()

def main():
    print()
    check_sith_inquisitor_issue()
    check_mountain_pass_issue()
    recommend_fixes()
    
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    print("Both issues stem from procedural generation problems:")
    print()
    print("1. INVISIBLE SITH INQUISITOR:")
    print("   • Enemy spawned off-map or outside vision")
    print("   • AI still runs and siphons Force every 4 turns")
    print("   • Fix: Check spawning logic, add distance check for messages")
    print()
    print("2. MOUNTAIN PASS ENCLOSURE:")
    print("   • Player spawned in mountain_pass surrounded by walls")
    print("   • Tomb spawned but unreachable")
    print("   • Fix: Exclude mountain_pass from spawn/tomb placement")
    print("          Ensure corridors through mountain ranges")
    print()
    print("Apply the 5 recommended fixes above to resolve both issues.")
    print()

if __name__ == "__main__":
    main()
