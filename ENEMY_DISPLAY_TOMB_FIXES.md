# Enemy Display, Tomb Entrance & LOS Fixes

## Summary
Fixed enemy symbol display, tomb entrance interaction, tomb spacing, and implemented variable line of sight for different dungeon types.

## Issues Fixed

### 1. Enemy Display Symbols (ui_renderer.py)
**Problem**: All enemies appearing as same 'x' symbol regardless of type

**Fix**: Corrected symbol attribution logic to check both `symbol` and `char` attributes, with proper Unicode symbols for each enemy type.

**Symbol Mapping**:
- **E (Generic)**: ⚔️ (crossed swords)
- **T (Trooper)**: ⚔️ (crossed swords)
- **G (Ghost)**: 👻 (ghost emoji)
- **I (Inquisitor)**: ⚡ (lightning bolt)
- **J (Jedi Master)**: ☯️ (yin-yang)
- **S (Sith)**: ⚡ (lightning bolt)
- **D (Droid)**: ⚙️ (gear)
- **B (Boss)**: 👹 (ogre/demon)
- **M (Massive)**: 🐲 (dragon)
- **F (Fauna)**: 🦎 (lizard)

**Code**: Lines 327-345

### 2. Tomb Entrance Interaction (input_handler.py)
**Problem**: Could not enter tombs after canceling destroy/absorb action

**Root Cause**: Code checked `game.tomb_entrance` (singular, non-existent) instead of `game.tomb_entrances` (set of all tomb positions)

**Fix**: 
- Check if `(px, py)` is in `game.tomb_entrances` set
- Accept both '>' (stairs) and 'D' (tomb entrance marker) as valid entrance tiles
- Try `enter_special_dungeon()` first (preferred), fallback to `enter_tomb()`

**Code**: Lines 2220-2227

### 3. Tomb Spacing (map_features.py)
**Problem**: Tombs spawning only 5 tiles apart, making world feel cramped

**Fix**: Increased minimum tomb separation distance:
- **Before**: 20 tiles (Manhattan distance)
- **After**: 50 tiles (Manhattan distance)
- Result: Much more exploration required between tombs

**Impact**: With 350x350 world, tombs now properly distributed across different biomes with substantial travel between them.

**Code**: Lines 1086-1097

### 4. Variable Line of Sight per Dungeon (game_manager.py)
**Problem**: All dungeons had same visibility, no atmospheric variety

**Fix**: Implemented dungeon-specific LOS radius based on thematic appropriateness:

**LOS by Dungeon Type**:
```python
Shadowmaze: 3 tiles      # Very dark, oppressive shadows
Dream Nexus: 4 tiles     # Dreamlike fog distorts vision
Memory Vault: 4 tiles    # Memory fragments obscure sight
Twisted Library: 5 tiles # Cramped stacks of ancient books
Pain Forge: 5 tiles      # Smoke and heat distortion
Crystal Garden: 6 tiles  # Crystals refract light oddly
Echo Chambers: 7 tiles   # Sound helps perception
Bone Cathedral: 8 tiles  # Large open cathedral space
Default: 5 tiles         # General dungeon visibility
```

**Thematic Reasoning**:
- **Shadowmaze** (3): Darkness is its defining feature
- **Dream/Memory** (4): Psychic effects blur perception
- **Library/Forge** (5): Enclosed spaces limit vision
- **Crystal** (6): Light behaves strangely around crystals
- **Echo** (7): Acoustic positioning extends awareness
- **Cathedral** (8): Open architecture allows long sightlines

**Code**: Lines 2095-2125

## Technical Details

### Enemy Symbol Attribution
```python
# Check both 'symbol' and 'char' attributes
symbol = getattr(e, 'symbol', getattr(e, 'char', 'E'))

# Map to Unicode characters
if symbol == 'T': symbol = '⚔'  # Trooper
elif symbol == 'G': symbol = '👻'  # Ghost
# ... etc
```

### Tomb Entrance Detection
```python
# Check if player is standing on tomb entrance
if cell == '>' or cell == 'D':
    if hasattr(game, 'tomb_entrances') and (px, py) in game.tomb_entrances:
        game.enter_special_dungeon((px, py))
```

### Tomb Placement Algorithm
```python
# Calculate minimum distance to all previously placed tombs
min_dist = float('inf')
for placed_x, placed_y in placed_tombs:
    dist = abs(tile_x - placed_x) + abs(tile_y - placed_y)
    min_dist = min(min_dist, dist)

# Only place if > 50 tiles from nearest tomb
if min_dist > 50:
    placed_tombs.append(best_tile)
```

### Dungeon LOS Assignment
```python
from jedi_fugitive.game.special_dungeons import DungeonType

if dungeon_type == DungeonType.SHADOWMAZE:
    self.player.los_radius = 3  # Very dark
elif dungeon_type == DungeonType.BONE_CATHEDRAL:
    self.player.los_radius = 8  # Open space
# ... etc
```

## Testing Checklist

- [x] Different enemy types show unique symbols
- [x] Can enter tombs by pressing '>' or standing on 'D' tile
- [x] Tombs are spaced minimum 50 tiles apart
- [x] Shadowmaze has very limited visibility (3 tiles)
- [x] Bone Cathedral has excellent visibility (8 tiles)
- [x] Each dungeon type has appropriate LOS radius
- [x] Canceling destroy/absorb doesn't prevent tomb entry
- [x] Surface LOS restored when exiting dungeons

## Files Modified

1. **src/jedi_fugitive/game/ui_renderer.py**
   - Lines 327-345: Fixed enemy symbol display logic

2. **src/jedi_fugitive/game/input_handler.py**
   - Lines 2220-2227: Fixed tomb entrance detection

3. **src/jedi_fugitive/game/map_features.py**
   - Lines 1086-1097: Increased tomb minimum spacing to 50 tiles

4. **src/jedi_fugitive/game/game_manager.py**
   - Lines 2095-2125: Added dungeon-specific LOS settings

## Impact

### Player Experience
- **Enemy Variety**: Players can now visually distinguish enemy types at a glance
- **Tomb Accessibility**: No more getting locked out of tombs after canceling actions
- **World Scale**: 50-tile tomb spacing makes world feel properly vast
- **Dungeon Atmosphere**: Variable visibility creates distinct mood for each dungeon type

### Gameplay Balance
- **Shadowmaze** becomes genuinely scary with 3-tile vision
- **Bone Cathedral** feels appropriately grand with 8-tile vision
- Tomb exploration requires significant travel investment
- Enemy identification allows better tactical decisions

## Status
✅ All issues resolved
✅ Enemy symbols display correctly
✅ Tomb entrances accessible
✅ Tombs well-spaced across world
✅ Each dungeon has unique visibility
