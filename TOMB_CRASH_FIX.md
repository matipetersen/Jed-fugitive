# Sith Tomb Crash Fix - Summary

## Issue Reported
Game crashes at level 2 in Sith tombs when player dies.

## Root Causes Identified

### 1. Missing Stairs on Deeper Levels (PRIMARY ISSUE)
**Location:** `src/jedi_fugitive/game/level.py` line 73-75

**Problem:**
```python
if rooms:
    if depth == 1:  # ← Only level 1 got stairs up!
        ux,uy = rooms[0][0]+1, rooms[0][1]+1
        game_map[uy][ux] = Display.STAIRS_UP
```

- STAIRS_UP was only placed on depth == 1
- Levels 2, 3, 4, 5 had no way to return upward
- When player descended to level 2, `change_floor()` tried to place them at a non-existent stairs_up position
- This caused fallback logic to trigger, but could lead to crashes in certain scenarios

**Fix:**
```python
if rooms:
    # Always place stairs up in first room (for returning from deeper levels)
    ux,uy = rooms[0][0]+1, rooms[0][1]+1
    game_map[uy][ux] = Display.STAIRS_UP
    # Always place stairs down in last room (for descending deeper)
    dx,dy = rooms[-1][0]+rooms[-1][2]-2, rooms[-1][1]+rooms[-1][3]-2
    game_map[dy][dx] = Display.STAIRS_DOWN
```

### 2. No Death Check in Floor Changes
**Location:** `src/jedi_fugitive/game/game_manager.py` line 1576

**Problem:**
- `change_floor()` didn't check if player was dead before attempting floor transition
- Dead players could trigger floor changes, leading to invalid state

**Fix:**
```python
def change_floor(self, delta: int) -> bool:
    """Change current dungeon floor by delta (+1 down, -1 up). Returns True on success."""
    try:
        # Safety check: don't allow floor changes if player is dead
        if getattr(self.player, 'hp', 1) <= 0:
            return False
        # ... rest of function
```

### 3. Fragile Enemy/Item Loading
**Location:** `src/jedi_fugitive/game/game_manager.py` line 1683-1690

**Problem:**
```python
try:
    self.enemies = [e for e in (getattr(self, 'tomb_enemies', [])[new] or [])]
except Exception:
    self.enemies = getattr(self, 'enemies', []) or []
```
- List comprehension could fail if `tomb_enemies[new]` was None or missing
- Generic exception handling masked the real error

**Fix:**
```python
try:
    tomb_enemies_list = getattr(self, 'tomb_enemies', [])
    if tomb_enemies_list and new < len(tomb_enemies_list):
        floor_enemies = tomb_enemies_list[new]
        if floor_enemies is not None:
            self.enemies = [e for e in floor_enemies if e is not None]
        else:
            self.enemies = []
    else:
        self.enemies = []
except Exception as e:
    print(f"ERROR loading tomb enemies for floor {new}: {e}")
    self.enemies = []
```
- Explicit bounds checking
- None-safety for floor_enemies
- Filters out None enemies
- Better error logging

## Files Modified

1. **`src/jedi_fugitive/game/level.py`**
   - Lines 73-78: Fixed stairs generation to place stairs on ALL levels

2. **`src/jedi_fugitive/game/game_manager.py`**
   - Lines 1576-1585: Added death check in `change_floor()`
   - Lines 1683-1707: Improved enemy/item loading with bounds checking and error handling

## Testing Results

### Before Fix:
- ✗ Level 2+ had no stairs up
- ✗ Dead players could trigger floor changes
- ✗ Enemy loading could crash on None values

### After Fix:
- ✅ All levels 1-5 have both stairs up and stairs down
- ✅ Dead players cannot change floors (returns False)
- ✅ Enemy loading handles None, empty lists, and out-of-bounds gracefully
- ✅ Proper error messages in console for debugging

## Test Coverage

Created test scripts:
1. `scripts/debug_tomb_crash.py` - Tests tomb generation and structure
2. `scripts/test_tomb_death.py` - Tests death scenarios and error handling

Both pass successfully:
```
✓ Stairs are now placed on all levels
✓ Player death prevents floor changes
✓ Error handling prevents crashes
✓ Bounds checking works correctly
```

## Edge Cases Handled

1. **Missing stairs:** All levels now guaranteed to have both up/down stairs
2. **Dead player:** Cannot change floors when HP <= 0
3. **Null enemy lists:** Handles None and empty lists gracefully
4. **Out of bounds:** Proper bounds checking prevents array index errors
5. **Invalid floor transitions:** Checks for valid tomb_levels before attempting changes

## Impact

- Game should no longer crash at level 2
- Tomb exploration is now fully functional
- Players can descend and ascend through all tomb levels safely
- Death is handled cleanly without crashes
- Better error logging for future debugging
