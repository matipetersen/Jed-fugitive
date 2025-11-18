# Stress GUI Fix - Implementation Summary

## Issue Reported
User reported that the stress GUI was showing on the surface before entering the first tomb, with stress rising above the limit.

## Root Cause
The stress GUI visibility was only checking if `_stress_system_active` was True, without verifying whether the player was actually in a tomb. This meant:
- If a player loaded a saved game where they had previously entered a tomb, the stress GUI would show on the surface
- The stress GUI would appear even when stress wasn't actually increasing

## Solution Implemented

### Changes to `ui_renderer.py`

1. **Main Stress Bar Display (Line ~412)**
   - Added check for `tomb_floor` to determine if player is in tomb
   - Modified condition from:
     ```python
     if getattr(game.player, '_stress_system_active', False):
     ```
   - To:
     ```python
     in_tomb = getattr(game, 'tomb_floor', None) is not None
     if getattr(game.player, '_stress_system_active', False) and in_tomb:
     ```

2. **Fallback Stress Display (Exception Handler ~458)**
   - Added same tomb check to fallback rendering
   - Ensures stress is never shown on surface, even if main rendering fails

3. **Fixed Syntax Error**
   - Removed duplicate/malformed except blocks
   - Cleaned up exception handling structure

## How It Works

### Tomb Detection Logic
- **On Surface**: `tomb_floor` is `None`
- **In Tomb**: `tomb_floor` is >= 0 (floor number)

### Visibility Rules
Stress GUI now shows only when BOTH conditions are met:
1. `_stress_system_active` is True (player has entered a tomb at least once)
2. `tomb_floor is not None` (player is currently in a tomb)

### Test Results
Created `test_stress_gui.py` which validates:
- ✓ Hidden on surface when system inactive
- ✓ Hidden on surface when system active (saved game case)
- ✓ Hidden in tomb when system inactive
- ✓ Visible in tomb when system active (normal case)

## User Impact

### Before Fix
- Stress GUI visible on surface after loading saved games
- Confusing UI state (showing stress when it's not increasing)
- Breaks immersion (stress is tomb-specific mechanic)

### After Fix
- Stress GUI only appears when player is in tomb
- Clean surface UI without stress distractions
- Stress system activates seamlessly upon tomb entry
- Loading saved games no longer shows stress on surface

## Testing Recommendations

1. **New Game Flow**
   - Start new game → No stress GUI on surface
   - Enter first tomb → Stress GUI appears
   - Exit tomb → Stress GUI disappears
   - Re-enter tomb → Stress GUI reappears

2. **Saved Game Flow**
   - Load save where tomb was entered → No stress GUI on surface
   - Enter tomb → Stress GUI appears
   - Verify stress value persists correctly

3. **Edge Cases**
   - Load autosave from inside tomb → Stress GUI visible
   - Die in tomb → New game has no stress GUI on surface
   - Multiple tomb entries → Stress GUI behavior consistent

## Related Files Modified

1. **src/jedi_fugitive/game/ui_renderer.py**
   - Lines 410-414: Added tomb check to main stress display
   - Lines 456-462: Added tomb check to fallback display
   - Removed syntax errors (duplicate except blocks)

2. **scripts/test_stress_gui.py** (NEW)
   - Test suite for stress GUI visibility logic
   - Validates all 4 visibility scenarios
   - Can be run independently for regression testing

## Notes

- Stress gain is already gated by `_stress_system_active` in `game_manager.py`
- This fix only affects UI visibility, not stress mechanics
- No changes needed to stress calculation or save system
- Fix is backward compatible with existing save files
