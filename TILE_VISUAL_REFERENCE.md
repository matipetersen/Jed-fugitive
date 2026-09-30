# Tile Visual Reference - Quick Guide

## Walkable Tiles ✓

### Standard Floors
```
·  Standard dungeon floor (Display.FLOOR)
.  Alternative floor tile
```

### Special Dungeon Floors (All Walkable)
```
◊  Memory Vault - Crystal floor (shimmering psychic energy)
.  Crystal Garden - Rocky ground (crimson crystal sprouts)
▪  Shadowmaze - Shadow floor (darkness made solid)
≈  Bone Cathedral - Bone debris (ancient remains)
≋  Echo Chambers - Resonant floor (sound waves visible)
▫  Twisted Library - Parchment floor (forbidden knowledge)
▓  Pain Forge - Forge floor (superheated from suffering)
∞  Dream Nexus - Dream floor (fluid reality)
```

### Interactive/Surface Tiles (Walkable)
```
D  Sith tomb entrance (Dungeon portal)
K  Sith Keep entrance
🚀 Ship wreckage (can examine)
📡 Comms device (can activate)
✖  Wreckage debris
=  Bridge
▼  Stairs down
▲  Stairs up
```

---

## Non-Walkable Tiles ✗

### Standard Walls
```
█  Primary wall tile (Display.WALL) - Blocks all movement
#  Legacy wall tile - Older maps
^  Mountains - Impassable terrain
```

### Special Dungeon Walls (All Block Movement)
```
▓  Memory Vault - Crystal walls (psychic barriers)
♦  Crystal Garden - Crystal walls (living crystals)
█  Shadowmaze - Dense shadow walls (pure darkness)
╬  Bone Cathedral - Bone construction (skeletal architecture)
║  Echo Chambers - Acoustic walls (sound-reactive)
▤  Twisted Library - Bookshelf walls (infinite knowledge)
▣  Pain Forge - Metal-reinforced stone (torture chambers)
≋  Dream Nexus - Fluid dream walls (impossible geometry)
```

---

## Visual Recognition Guide

### How to Tell Floor from Wall

#### Memory Vault
- Floor: `◊` (small diamond, open)
- Wall:  `▓` (solid block, filled)

#### Crystal Garden
- Floor: `.` (tiny dot, walkable)
- Wall:  `♦` (diamond shape, blocking)

#### Shadowmaze
- Floor: `▪` (small square, hollow)
- Wall:  `█` (full block, solid)

#### Bone Cathedral
- Floor: `≈` (wavy lines, debris)
- Wall:  `╬` (cross pattern, structure)

#### Echo Chambers
- Floor: `≋` (triple wave, resonant)
- Wall:  `║` (vertical lines, acoustic)

#### Twisted Library
- Floor: `▫` (white square, parchment)
- Wall:  `▤` (dense pattern, shelves)

#### Pain Forge
- Floor: `▓` (medium density, hot)
- Wall:  `▣` (square pattern, metal)

#### Dream Nexus
- Floor: `∞` (infinity, fluid)
- Wall:  `≋` (wave pattern, dreamlike)

---

## Common Confusion Points

### Why isn't `~` walkable?
On the **surface**, `~` represents dunes and IS walkable.  
In **dungeons**, it was mistakenly used and has been removed.  
The Echo Chambers now use `≋` instead.

### Why is `▓` both a floor AND a wall?
- Memory Vault WALL: `▓` (solid crystal)
- Pain Forge FLOOR: `▓` (forge tiles)
- Context matters! Check the dungeon type.

### What about stairs?
- `▼` Stairs down - Walkable, triggers floor change
- `▲` Stairs up - Walkable, triggers ascent

### Can enemies walk where I walk?
YES - All tiles follow the same rules.  
If you can walk on it, enemies can too.

---

## Testing Your Own Tiles

If you see a tile and wonder if it's walkable:

1. **Try to move onto it**
   - If blocked: Check if it's in the non_walkable list
   - If allowed: It's a floor tile

2. **Check the tile character**
   - Compare to wall list above
   - If not in wall list → walkable

3. **Look at the context**
   - Floors are typically sparse/light patterns
   - Walls are typically dense/heavy patterns

---

## For Developers

### Adding New Dungeon Tiles

When creating a new dungeon type:

1. **Choose UNIQUE tiles**
   - Floor: Pick something not in non_walkable
   - Wall: Pick something distinct from other walls

2. **Update 5 locations**:
   ```
   src/jedi_fugitive/game/input_handler.py (line ~2173)
   src/jedi_fugitive/game/game_manager.py (line ~2977)
   src/jedi_fugitive/game/game_manager.py (line ~4910)
   src/jedi_fugitive/game/enemy.py (line ~184)
   src/jedi_fugitive/game/map_features.py (line ~53)
   ```

3. **Add wall tile to non_walkable sets**:
   ```python
   non_walkable = {
       '\u2588', '#', '^',  # Standard
       '\u2593', '\u2666', '\u256c', '\u2551',  # Existing
       '\u25a4', '\u25a3', '\u224b',  # Existing
       '\uXXXX',  # YOUR NEW WALL TILE HERE
   }
   ```

4. **Test thoroughly**:
   - Player movement
   - Enemy pathfinding
   - Enemy spawning
   - Reachability

### Unicode Reference
```python
'\u2588'  # █  Full block
'\u2593'  # ▓  Dark shade
'\u2666'  # ♦  Diamond
'\u256c'  # ╬  Cross
'\u2551'  # ║  Double vertical
'\u25a4'  # ▤  Square with pattern
'\u25a3'  # ▣  Square with fill
'\u224b'  # ≋  Triple tilde
'\u25ca'  # ◊  Lozenge
'\u25aa'  # ▪  Small square
'\u2248'  # ≈  Almost equal
'\u25ab'  # ▫  White square
'\u221e'  # ∞  Infinity
```

---

## Quick Lookup Table

| Tile | Name | Type | Walkable? | Dungeon |
|------|------|------|-----------|---------|
| · | Floor | Standard | ✓ | All standard |
| . | Floor | Alt | ✓ | Multiple |
| ◊ | Crystal | Floor | ✓ | Memory Vault |
| ▪ | Shadow | Floor | ✓ | Shadowmaze |
| ≈ | Bone | Floor | ✓ | Bone Cathedral |
| ≋ | Resonant | Floor | ✓ | Echo Chambers |
| ▫ | Parchment | Floor | ✓ | Twisted Library |
| ▓ | Forge | Floor | ✓ | Pain Forge |
| ∞ | Dream | Floor | ✓ | Dream Nexus |
| █ | Wall | Wall | ✗ | Standard/Shadowmaze |
| # | Wall | Wall | ✗ | Legacy |
| ^ | Mountain | Terrain | ✗ | Surface |
| ▓ | Crystal | Wall | ✗ | Memory Vault |
| ♦ | Crystal | Wall | ✗ | Crystal Garden |
| ╬ | Bone | Wall | ✗ | Bone Cathedral |
| ║ | Acoustic | Wall | ✗ | Echo Chambers |
| ▤ | Bookshelf | Wall | ✗ | Twisted Library |
| ▣ | Metal | Wall | ✗ | Pain Forge |
| ≋ | Fluid | Wall | ✗ | Dream Nexus |
| D | Entrance | Interactive | ✓ | Surface |
| ▼ | Stairs | Transition | ✓ | Dungeons |
| ▲ | Stairs | Transition | ✓ | Dungeons |

---

## Emergency Debug Commands

If you're stuck or tiles aren't working:

```python
# Check what tile you're standing on
tile = game.game_map[player.y][player.x]
print(f"Standing on: '{tile}' (unicode: {ord(tile)})")

# Check if tile is walkable
from input_handler import non_walkable
print(f"Walkable: {tile not in non_walkable}")

# Clear pathfinding cache
game._pathfinding_cache = {}

# List all tiles on current map
unique_tiles = set(''.join(''.join(row) for row in game.game_map))
print(f"Map uses: {sorted(unique_tiles)}")
```

---

May the Force guide your path through every dungeon!
