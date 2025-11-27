#!/usr/bin/env python3
"""
Comprehensive Game Balance Validation
Tests all systems: map generation, tomb placement, reachability, win conditions, equipment, and progression paths.
"""
import sys
import os
import random
import time

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game.level import Display
from jedi_fugitive.game.map_features import get_reachable_tiles

class DummyStdScr:
    """Dummy screen for headless testing"""
    def __init__(self, h=24, w=80):
        self._h = h
        self._w = w
    def getmaxyx(self):
        return (self._h, self._w)
    def subwin(self, h, w, y, x):
        return self
    def clear(self): pass
    def erase(self): pass
    def border(self): pass
    def addstr(self, *a, **k): pass
    def addnstr(self, *a, **k): pass
    def refresh(self): pass
    def noutrefresh(self): pass
    def resize(self, h, w): 
        self._h, self._w = h, w
    def mvwin(self, y, x): pass
    def move(self, y, x): pass
    def clrtoeol(self): pass
    def getch(self): 
        return -1

def print_header(msg):
    print(f"\n{'='*60}")
    print(f" {msg}")
    print(f"{'='*60}")

def print_step(msg):
    print(f"\n[STEP] {msg}")

def run_comprehensive_simulation():
    print_header("COMPREHENSIVE GAME BALANCE VALIDATION")
    
    print_step("Initializing Game Manager...")
    dummy_screen = DummyStdScr()
    game = GameManager(dummy_screen)
    
    print_step("Setting Up Game World...")
    game.initialize()
    game.generate_world()
    
    # === MAP ANALYSIS ===
    print_header("MAP ANALYSIS")
    
    mh = len(game.game_map)
    mw = len(game.game_map[0])
    area = mw * mh
    print(f"✓ Map Dimensions: {mw} x {mh}")
    print(f"✓ Total Area: {area:,} tiles")
    
    if area < 10000:
        print("  ⚠ WARNING: Map seems small for exploration")
    elif area > 100000:
        print("  ⚠ WARNING: Map might be too large")
    else:
        print("  ✓ Map size appears balanced")
    
    # === REACHABILITY ANALYSIS ===
    print_header("REACHABILITY ANALYSIS")
    
    px, py = game.player.x, game.player.y
    print(f"✓ Player Start Position: ({px}, {py})")
    
    reachable = get_reachable_tiles(game.game_map, px, py)
    reachable_count = len(reachable)
    reachable_percent = (reachable_count / area) * 100
    
    print(f"✓ Reachable Tiles: {reachable_count:,} ({reachable_percent:.1f}%)")
    
    if reachable_percent < 15:
        print("  ⚠ WARNING: Low reachability - map might be too fragmented")
    elif reachable_percent > 80:
        print("  ⚠ WARNING: Very high reachability - might lack barriers/challenges")
    else:
        print("  ✓ Reachability seems balanced")
    
    # === BIOME ANALYSIS ===
    print_header("BIOME DIVERSITY ANALYSIS")
    
    biome_counts = {}
    if hasattr(game, 'map_biomes') and game.map_biomes:
        for y in range(mh):
            for x in range(mw):
                if (x, y) in reachable:
                    b = game.map_biomes[y][x]
                    biome_counts[b] = biome_counts.get(b, 0) + 1
        
        print(f"✓ Biomes Found: {len(biome_counts)}")
        for b, count in sorted(biome_counts.items(), key=lambda x: x[1], reverse=True):
            percent = (count / reachable_count) * 100
            print(f"  - {b.capitalize()}: {count:,} tiles ({percent:.1f}%)")
            
        if len(biome_counts) < 3:
            print("  ⚠ WARNING: Insufficient biome diversity")
        elif len(biome_counts) >= 4:
            print("  ✓ Good biome diversity for varied exploration")
    else:
        print("  ✗ ERROR: No biome map found!")

    # === TOMB ANALYSIS ===
    print_header("TOMB & WIN CONDITION ANALYSIS")
    
    tombs = getattr(game, 'tomb_entrances', set())
    print(f"✓ Tombs Placed: {len(tombs)}")
    
    reachable_tombs = sum(1 for tx, ty in tombs if (tx, ty) in reachable)
    print(f"✓ Reachable Tombs: {reachable_tombs}/{len(tombs)}")
    
    # Analyze tomb distribution across biomes
    tomb_biomes = {}
    for tx, ty in tombs:
        if (tx, ty) in reachable and hasattr(game, 'map_biomes'):
            biome = game.map_biomes[ty][tx] 
            tomb_biomes[biome] = tomb_biomes.get(biome, 0) + 1
    
    if tomb_biomes:
        print("✓ Tomb Distribution by Biome:")
        for biome, count in tomb_biomes.items():
            print(f"  - {biome.capitalize()}: {count} tombs")
    
    # Win condition check
    if reachable_tombs < 3:
        print("  ❌ CRITICAL: Game is UNWINNABLE (need 3+ reachable tombs)")
    elif reachable_tombs >= 3:
        print(f"  ✅ Game is WINNABLE ({reachable_tombs} reachable tombs)")
    
    # Check key locations
    ship_pos = getattr(game, 'ship_pos', None)
    comms_pos = getattr(game, 'comms_pos', None)
    
    if ship_pos and ship_pos in reachable:
        print("✓ Ship wreckage is reachable")
    elif ship_pos:
        print("  ⚠ Ship wreckage is unreachable")
    else:
        print("  ⚠ Ship wreckage not found")
        
    if comms_pos and comms_pos in reachable:
        print("✓ Comms terminal is reachable")
    elif comms_pos:
        print("  ❌ CRITICAL: Comms terminal is unreachable")
    else:
        print("  ❌ CRITICAL: Comms terminal not found")

    # === CONTENT ANALYSIS ===
    print_header("CONTENT & CHALLENGE ANALYSIS")
    
    enemies = getattr(game, 'enemies', [])
    landmarks = getattr(game, 'map_landmarks', {})
    merchants = getattr(game, 'merchants', {})
    loot_caches = getattr(game, 'loot_caches', {})
    
    print(f"✓ Enemies Spawned: {len(enemies)}")
    print(f"✓ Landmarks/POIs: {len(landmarks)}")
    print(f"✓ Merchant Camps: {len(merchants)}")
    print(f"✓ Loot Caches: {len(loot_caches)}")
    
    # Enemy analysis
    enemy_levels = [getattr(e, 'level', 1) for e in enemies]
    if enemy_levels:
        avg_level = sum(enemy_levels) / len(enemy_levels)
        print(f"✓ Enemy Level Range: {min(enemy_levels)}-{max(enemy_levels)} (avg: {avg_level:.1f})")
    
    patrols = sum(1 for e in enemies if hasattr(e, 'patrol_points') and e.patrol_points)
    patrol_percent = (patrols / len(enemies)) * 100 if enemies else 0
    print(f"✓ Enemies with Patrols: {patrols}/{len(enemies)} ({patrol_percent:.1f}%)")
    
    if len(enemies) < 10:
        print("  ⚠ WARNING: Few enemies - game might be too easy")
    elif len(enemies) > 100:
        print("  ⚠ WARNING: Many enemies - might be overwhelming")
    else:
        print("  ✓ Enemy count seems balanced")

    # === EQUIPMENT & PROGRESSION ANALYSIS ===
    print_header("EQUIPMENT & PROGRESSION ANALYSIS")
    
    # Check starting equipment
    player_inv = getattr(game.player, 'inventory', [])
    print(f"✓ Starting Inventory: {len(player_inv)} items")
    
    for item in player_inv:
        if hasattr(item, 'name'):
            item_type = getattr(item, 'weapon_type', getattr(item, 'type', 'unknown'))
            print(f"  - {item.name} ({item_type})")
        elif isinstance(item, dict):
            print(f"  - {item.get('name', 'Unknown')} ({item.get('type', 'unknown')})")
    
    # Check available loot
    items_on_map = getattr(game, 'items_on_map', [])
    print(f"✓ Items on Map: {len(items_on_map)}")
    
    # Count items by type
    item_types = {}
    for item in items_on_map:
        item_type = item.get('type', 'unknown') if isinstance(item, dict) else 'unknown'
        item_types[item_type] = item_types.get(item_type, 0) + 1
    
    if item_types:
        print("✓ Loot Distribution:")
        for item_type, count in sorted(item_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {item_type.capitalize()}: {count}")

    # === SITH KEEP ANALYSIS ===
    print_header("SITH KEEP ANALYSIS")
    
    try:
        # Look for Sith Keep in landmarks or check if it was placed
        sith_keep_found = False
        for (lx, ly), landmark in landmarks.items():
            if 'keep' in landmark.get('name', '').lower() or 'sith keep' in landmark.get('name', '').lower():
                if (lx, ly) in reachable:
                    print(f"✓ Sith Keep found at ({lx}, {ly}) - REACHABLE")
                    sith_keep_found = True
                else:
                    print(f"⚠ Sith Keep found at ({lx}, {ly}) - UNREACHABLE")
                    sith_keep_found = True
                break
        
        if not sith_keep_found:
            print("⚠ Sith Keep not found in landmarks")
    except Exception as e:
        print(f"⚠ Error checking Sith Keep: {e}")

    # === FINAL ASSESSMENT ===
    print_header("FINAL ASSESSMENT")
    
    issues = []
    successes = []
    
    # Critical checks
    if reachable_tombs < 3:
        issues.append("CRITICAL: Insufficient reachable tombs")
    else:
        successes.append(f"Victory possible ({reachable_tombs} tombs)")
        
    if not (comms_pos and comms_pos in reachable):
        issues.append("CRITICAL: Comms terminal unreachable")
    else:
        successes.append("Comms terminal accessible")
    
    # Balance checks
    if len(biome_counts) < 3:
        issues.append("Insufficient biome diversity")
    else:
        successes.append(f"Good biome diversity ({len(biome_counts)} biomes)")
        
    if reachable_percent < 15:
        issues.append("Map too fragmented (low reachability)")
    elif reachable_percent > 80:
        issues.append("Map lacks barriers (too reachable)")
    else:
        successes.append(f"Balanced reachability ({reachable_percent:.1f}%)")
        
    if len(enemies) < 10:
        issues.append("Too few enemies")
    elif len(enemies) > 100:
        issues.append("Too many enemies")
    else:
        successes.append(f"Balanced enemy count ({len(enemies)})")
    
    # Print results
    if successes:
        print("✅ SUCCESSES:")
        for success in successes:
            print(f"  ✓ {success}")
    
    if issues:
        print("\n❌ ISSUES FOUND:")
        for issue in issues:
            print(f"  ✗ {issue}")
    
    # Overall verdict
    critical_issues = [i for i in issues if i.startswith("CRITICAL")]
    
    if critical_issues:
        print(f"\n🔴 OVERALL: GAME IS BROKEN ({len(critical_issues)} critical issues)")
        return False
    elif issues:
        print(f"\n🟡 OVERALL: GAME IS PLAYABLE BUT HAS ISSUES ({len(issues)} issues)")
        return True
    else:
        print(f"\n🟢 OVERALL: GAME IS WELL BALANCED ({len(successes)} systems working)")
        return True

if __name__ == "__main__":
    try:
        success = run_comprehensive_simulation()
        exit_code = 0 if success else 1
        print(f"\nValidation completed with exit code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)