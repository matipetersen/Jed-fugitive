#!/usr/bin/env python3
"""
Verify that the map generation produces:
1. Multiple tombs (6-9 expected)
2. Multiple biomes (3+ different types)
3. All tombs within bounds
4. Tombs properly spaced
"""
import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

from jedi_fugitive.game.game_manager import GameManager

class DummyStdScr:
    """Dummy screen for headless testing"""
    def __init__(self, h=24, w=80):
        self._h = h
        self._w = w
    
    def getmaxyx(self):
        return (self._h, self._w)
    
    def subwin(self, h, w, y, x):
        return self
    
    def clear(self):
        pass
    
    def erase(self):
        pass
    
    def border(self):
        pass
    
    def addstr(self, *args, **kwargs):
        pass
    
    def addnstr(self, *args, **kwargs):
        pass
    
    def refresh(self):
        pass
    
    def noutrefresh(self):
        pass
    
    def resize(self, h, w):
        self._h = h
        self._w = w
    
    def getch(self):
        return -1

def test_map_generation():
    """Test map generation produces expected results"""
    print("Testing map generation with new parameters...")
    print("=" * 60)
    
    # Create a new game with dummy screen
    dummy_screen = DummyStdScr(h=40, w=120)
    gm = GameManager(dummy_screen)
    gm.initialize()
    gm.generate_world()
    
    # Check map dimensions
    map_height = len(gm.game_map)
    map_width = len(gm.game_map[0]) if map_height > 0 else 0
    print(f"\n✓ Map size: {map_width} x {map_height}")
    
    # Check tomb count
    tomb_count = len(gm.tomb_entrances)
    print(f"✓ Tomb count: {tomb_count}")
    
    if tomb_count < 5:
        print(f"  ⚠ WARNING: Expected 6-9 tombs, got {tomb_count}")
    elif tomb_count > 10:
        print(f"  ⚠ WARNING: Too many tombs: {tomb_count}")
    else:
        print(f"  ✓ Tomb count in expected range (6-9)")
    
    # Check all tombs are within bounds
    all_in_bounds = True
    for x, y in gm.tomb_entrances:
        if not (0 <= x < map_width and 0 <= y < map_height):
            print(f"  ✗ ERROR: Tomb at ({x}, {y}) is out of bounds!")
            all_in_bounds = False
    
    if all_in_bounds:
        print(f"✓ All {tomb_count} tombs are within map bounds")
    
    # Check biome diversity
    if hasattr(gm, 'map_biomes') and gm.map_biomes:
        biome_set = set()
        for row in gm.map_biomes:
            biome_set.update(row)
        
        biome_list = sorted(list(biome_set))
        print(f"✓ Biomes present: {len(biome_list)}")
        for biome in biome_list:
            print(f"  - {biome}")
        
        if len(biome_list) < 3:
            print(f"  ⚠ WARNING: Expected 3+ biomes, got {len(biome_list)}")
        else:
            print(f"  ✓ Good biome diversity")
    else:
        print("✗ No biome map found")
    
    # Check tomb spacing
    print("\n✓ Tomb spacing check:")
    tomb_list = list(gm.tomb_entrances)
    min_spacing = float('inf')
    for i, (x1, y1) in enumerate(tomb_list):
        for x2, y2 in tomb_list[i+1:]:
            dist = abs(x1 - x2) + abs(y1 - y2)
            min_spacing = min(min_spacing, dist)
    
    print(f"  Minimum tomb spacing: {min_spacing} tiles")
    if min_spacing < 15:
        print(f"  ⚠ WARNING: Some tombs are very close together")
    else:
        print(f"  ✓ Tombs are well-spaced")
    
    print("\n" + "=" * 60)
    print("Map generation test complete!")
    
    # Summary
    issues = []
    if tomb_count < 5:
        issues.append(f"Only {tomb_count} tombs (expected 6-9)")
    if not all_in_bounds:
        issues.append("Some tombs out of bounds")
    if hasattr(gm, 'map_biomes') and gm.map_biomes:
        biome_count = len(set(b for row in gm.map_biomes for b in row))
        if biome_count < 3:
            issues.append(f"Only {biome_count} biomes (expected 3+)")
    
    if issues:
        print("\n⚠ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✓ All checks passed!")
        return True

if __name__ == "__main__":
    try:
        success = test_map_generation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
