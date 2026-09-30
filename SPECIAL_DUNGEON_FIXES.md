# Special Dungeon Navigation Fixes

## Issues Fixed (December 12, 2025)

### Issue 1: Fire Projectile Import Error
**Error**: `cannot import name 'fire_projectile' from 'jedi_fugitive.game.projectiles'`

**Root Cause**: The input_handler.py was trying to import `fire_projectile` which doesn't exist. The actual function is `spawn_blaster`.

**Fix Applied**: Changed line 2109-2110 in input_handler.py:
```python
# OLD (broken):
from jedi_fugitive.game.projectiles import fire_projectile
fire_projectile(game, px, py, nearest_enemy.x, nearest_enemy.y, active_weapon)

# NEW (fixed):
from jedi_fugitive.game.projectiles import spawn_blaster
weapon_damage = getattr(active_weapon, 'base_damage', 6) if hasattr(active_weapon, 'base_damage') else 6
spawn_blaster(game, px, py, nearest_enemy.x, nearest_enemy.y, damage=weapon_damage)
```

### Issue 2: Special Dungeons Unwalkable
**Error**: "Vault of Lost Memories is unwalkable" and "Forge of Eternal Torment is unwalkable"

**Root Cause**: Special dungeon floor tiles weren't recognized as walkable by the movement system.

**Multiple Problems**:

1. **Tile Conflict**: Pain Forge used `'▓'` as floor_tile, but Memory Vault uses `'▓'` as wall_tile. This created a conflict where `'▓'` was in the non_walkable set, making Pain Forge completely unwalkable!

2. **Missing Floor Tiles**: Special dungeon floor tiles weren't in any walkable list, so movement was blocked even though the tiles were generated correctly.

**Fixes Applied**:

#### Fix 1: Resolved Tile Conflict (special_dungeons.py line 434)
```python
# OLD (broken):
'floor_tile': '▓',   # Forge floor - CONFLICT with Memory Vault walls!

# NEW (fixed):
'floor_tile': '░',   # Forge floor (light shade) - unique tile
```

#### Fix 2: Added Special Floor Tiles to Walkable Set (input_handler.py lines 2293-2303)
```python
# WALKABLE special dungeon floor tiles
# These must be explicitly allowed for special dungeons to work
special_floors = {
    '◊',  # Memory Vault crystal floor
    '.',  # Crystal Garden rocky ground / normal floor
    '▪',  # Shadowmaze shadow floor
    '≈',  # Bone Cathedral bone debris
    '≋',  # Echo Chambers resonant floor
    '▫',  # Twisted Library parchment floor
    '░',  # Pain Forge forge floor (changed from ▓)
    '∞',  # Dream Nexus dream floor
    '·',  # Standard floor tile
}
```

#### Fix 3: Corrected Walkability Logic (input_handler.py line 2306)
```python
# Block ONLY if it's in non_walkable AND NOT in special_floors
# Special floors override non_walkable (allows special dungeon navigation)
if cell_str in non_walkable and cell_str not in special_floors:
    try: game.ui.messages.add("Blocked.")
    except Exception: pass
    return
```

---

## Special Dungeon Floor Tiles Reference

| Dungeon | Floor Tile | Wall Tile | Notes |
|---------|------------|-----------|-------|
| Memory Vault | `◊` | `▓` | Crystal floor / Crystal walls |
| Crystal Garden | `.` | `♦` | Rocky ground / Crystal walls |
| Shadowmaze | `▪` | `█` | Shadow floor / Solid walls |
| Bone Cathedral | `≈` | `╬` | Bone debris / Cross walls |
| Echo Chambers | `≋` | `║` | Resonant floor / Acoustic walls |
| Twisted Library | `▫` | `▤` | Parchment floor / Bookshelf walls |
| Pain Forge | `░` | `▣` | Forge floor / Metal walls |
| Dream Nexus | `∞` | `≋` | Dream floor / Fluid walls |

---

## Testing Recommendations

1. **New Game Test**: Start fresh game and enter each special dungeon to verify walkability
2. **Old Saves**: If a save file has player inside Pain Forge with old `▓` floors, movement may still be blocked until player exits and re-enters
3. **Combat Test**: Fire ranged weapon with 'f' key to verify projectile fix works
4. **Floor Variety**: Walk on all floor types to ensure no tile is blocking movement

---

## Additional Notes

- All special dungeon floor tiles are now properly recognized as walkable
- The non_walkable set contains only wall tiles and impassable terrain
- Special floors explicitly override non_walkable checks
- Stairs (`>` and `<`) and artifacts (`◆`) are always walkable regardless of tile type
