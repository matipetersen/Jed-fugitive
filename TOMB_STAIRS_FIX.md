# Tomb Stairs Fix

## Problem
Tomb stairs were not working correctly on all levels. Players could descend but had difficulty ascending back up through multi-level tombs.

## Root Cause
In `src/jedi_fugitive/map/generation.py`, the `generate_dungeon_level()` function had a bug where STAIRS_UP were only placed on depth 1:

```python
# BUGGY CODE:
if depth == 1:
    ux,uy = rooms[0][0]+1, rooms[0][1]+1
    game_map[uy][ux] = Display.STAIRS_UP
dx,dy = rooms[-1][0]+rooms[-1][2]-2, rooms[-1][1]+rooms[-1][3]-2
game_map[dy][dx] = Display.STAIRS_DOWN
```

This meant:
- **Level 1**: Had STAIRS_UP and STAIRS_DOWN ✓
- **Level 2+**: Only had STAIRS_DOWN, no STAIRS_UP ✗

Players could descend through tombs but couldn't ascend back up from deeper levels.

## Solution
Removed the conditional check that restricted STAIRS_UP to only depth 1. Now all levels get both stair types:

```python
# FIXED CODE:
# Place stairs up in first room (for returning to previous level)
# All levels get stairs up so player can always ascend
ux,uy = rooms[0][0]+1, rooms[0][1]+1
game_map[uy][ux] = Display.STAIRS_UP

# Place stairs down in last room (for descending to next level)
# This should be placed on all levels - the game logic will handle
# whether there's actually a deeper level to go to
dx,dy = rooms[-1][0]+rooms[-1][2]-2, rooms[-1][1]+rooms[-1][3]-2
game_map[dy][dx] = Display.STAIRS_DOWN
```

## Changes Made

### Modified Files
1. **`src/jedi_fugitive/map/generation.py`** (lines 84-94)
   - Removed `if depth == 1:` conditional
   - Added explanatory comments
   - Now places STAIRS_UP on every level

### Stair Placement Logic
- **STAIRS_UP** ('< ')`: Placed in first room (for ascending to previous level)
- **STAIRS_DOWN** (`>`): Placed in last room (for descending to next level)
- Both stairs guaranteed on every level
- Stairs placed in different rooms to avoid overlap
- Game logic in `game_manager.py` handles level boundaries

## Testing

### Test Coverage
Created comprehensive test suite (`test_tomb_stairs_fix.py`):

**Test 1: Stair Placement on Multiple Levels**
- Verified levels 1-5 all have exactly 1 STAIRS_UP and 1 STAIRS_DOWN
- Confirmed stairs are at different positions
- Validated stairs are in correct rooms (first and last)

**Test 2: Stair Accessibility**
- Checked that stairs have adjacent floor tiles
- Verified players can reach stairs from room interior
- Tested on levels 1, 3, and 5

**Test 3: Stairs Don't Overlap with Items**
- Ensured no items spawn on stair positions
- Verified for all item types (gold, food, potions, artifacts)
- Tested across all depth levels

**Test 4: Consistency Across Multiple Generations**
- Ran 10 generation cycles for levels 1-3
- Confirmed consistent stair placement
- Verified randomness doesn't break stair logic

**Test 5: Visual Verification**
- Generated sample map with stairs highlighted
- Manual inspection of stair positioning
- Confirmed visual correctness

### Test Results
```
Testing Tomb Stair Placement
==============================
✅ All levels (1-5+) now have STAIRS_UP placed
✅ All levels have exactly 1 STAIRS_UP and 1 STAIRS_DOWN
✅ Stairs are in separate rooms (first and last)
✅ Stairs are accessible (have adjacent floor tiles)
✅ No overlap between stairs and items
✅ Consistent placement across multiple generations

ALL TESTS PASSED
```

## Impact

### Gameplay
1. **Fixed Tomb Navigation**: Players can now ascend and descend freely through multi-level tombs
2. **Exploration**: All tomb levels are now fully explorable without getting stuck
3. **Risk/Reward**: Players can retreat to shallower levels if overwhelmed
4. **Quest Completion**: Can return to retrieve quest items from deeper levels

### User Experience
1. **No More Soft Locks**: Players won't get trapped on deeper tomb levels
2. **Strategic Retreat**: Can leave tombs and return later
3. **Natural Flow**: Dungeon traversal works as expected
4. **Reduced Frustration**: Eliminates the "can't go back up" problem

## Visual Example

Before fix - Level 2 map:
```
###########
#.........#  <- No stairs up!
#...$.....#
#.........#
#.......>.#  <- Only stairs down
###########
```

After fix - Level 2 map:
```
###########
#<........#  <- Stairs up added!
#...$.....#
#.........#
#.......>.#  <- Stairs down present
###########
```

## Completion Status

✅ **Item #12: Fix tomb stairs on all levels**

**Implementation:**
- Identified root cause in generation.py
- Removed depth-conditional stair placement
- Added STAIRS_UP to all levels
- Created comprehensive test suite
- All tests passing
- No regression issues

**Progress: 14/15 tasks (93%)**

## Remaining Tasks
- #4: Enhance NPC dialogue with quests and inter-NPC dynamics
- #13: Enable inspect to reveal Sith ambushers
