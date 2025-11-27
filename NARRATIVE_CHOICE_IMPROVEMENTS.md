# Narrative Choice System Improvements

## Summary
Enhanced the narrative event system to make player choices interactive, fair, and more engaging.

## Changes Made

### 1. Removed Alignment Labels (narrative_events.py)
**Problem**: Choices showed "(Light)", "(Dark)", "(Neutral)" labels, making the moral choice obvious.

**Solution**: Removed all alignment labels from choice text. Players now make decisions based on the action itself, not pre-labeled morality.

**Before**:
```
1. Defend the survivor and drive off the scavengers (Light)
2. Kill the scavengers and take everything (Dark)
3. Leave - this isn't your problem (Neutral)
```

**After**:
```
1. Defend the survivor and drive off the scavengers
2. Kill the scavengers and take everything
3. Leave - this isn't your problem
```

### 2. Randomized Choice Order (narrative_events.py)
**Problem**: Choices always appeared in same order (light/dark/neutral), making patterns predictable.

**Solution**: 
- Modified `format_distress_signal()` to shuffle choice order
- Modified `format_environmental_event()` to shuffle choice order
- Return a choice_mapping dict that maps display numbers (1,2,3) to actual choice keys
- Each time event displays, choices appear in different random order

**Example**: Same event, different displays:
```
Attempt 1:               Attempt 2:               Attempt 3:
1. Leave (neutral)       1. Kill all (dark)       1. Kill all (dark)
2. Defend (light)        2. Leave (neutral)       2. Leave (neutral)
3. Kill all (dark)       3. Defend (light)        3. Defend (light)
```

### 3. Interactive Choice System (input_handler.py + game_manager.py)
**Problem**: Events displayed "Press 1, 2, 3" but no input handling existed - choices were non-functional.

**Solution**:
- Added `pending_narrative_choice` attribute to GameManager
- When distress signal/environmental event triggers, store: (event_data, choice_mapping, event_type)
- Added input handling in `handle_input()` to detect 1/2/3 keypresses
- When choice pressed:
  - Look up actual choice_key from choice_mapping
  - Process choice using new `process_narrative_choice()` function
  - Display outcome message
  - Apply corruption change
  - Apply reward
  - Clear pending choice
- Added ESC to cancel/skip choices

### 4. Choice Processing Function (narrative_events.py)
**Added**: `process_narrative_choice(event_data, choice_key, player)`

**Purpose**: Extract outcome, corruption change, and reward from event data structure.

**Handles**: Both distress signals (nested under 'scenario') and environmental events (flat 'choices' dict).

**Returns**: (outcome_message, corruption_change, reward_type)

### 5. Environmental Event Formatter (narrative_events.py)
**Added**: `format_environmental_event(event)`

**Purpose**: Format environmental events with randomized choices, similar to distress signals.

**Returns**: (formatted_lines, choice_mapping) or (formatted_lines, None) if event has no choices.

## Files Modified

### src/jedi_fugitive/game/narrative_events.py
- Removed "(Light)", "(Dark)", "(Neutral)" from 4 distress signals
- Removed "(Light)", "(Dark)" from environmental event
- Modified `format_distress_signal()` to return (lines, choice_mapping)
- Added `format_environmental_event()` function
- Added `process_narrative_choice()` function

### src/jedi_fugitive/game/game_manager.py
- Added `self.pending_narrative_choice = None` in __init__
- Updated distress signal handling to store pending choice
- Updated environmental event handling to store pending choice

### src/jedi_fugitive/game/input_handler.py
- Added narrative choice input handling (1/2/3 keys)
- Processes choice, displays outcome, applies effects
- Added ESC to cancel pending choices

## Testing

### scripts/test_narrative_choices.py
Comprehensive unit tests:
- ✅ Alignment labels removed
- ✅ Choice randomization working (6 different orders in 10 attempts)
- ✅ Choice mapping correct (1,2,3 -> choice keys)
- ✅ Choice processing returns valid data
- ✅ Environmental events work correctly

### scripts/demo_narrative_choices.py
Integration demo showing:
- Complete distress signal flow
- Complete environmental event flow
- Same event displaying in 3 different random orders
- Choice processing with outcomes and corruption changes

## Player Experience Improvements

1. **Meaningful Choices**: Players must read and consider each option's description rather than relying on alignment labels

2. **Fair Selection**: Random order prevents bias toward "first option" or "last option"

3. **Actually Interactive**: Choices now work - pressing 1/2/3 actually does something!

4. **Immediate Feedback**: Clear outcome messages, corruption changes, and rewards

5. **Can Skip**: ESC key allows ignoring events if player isn't interested

## Gameplay Impact

- **More Immersive**: Choices feel like real dilemmas, not "pick your alignment"
- **Better Balance**: No optimal position (e.g., "middle option is always safe")
- **Replay Value**: Same events feel different each playthrough
- **Player Agency**: Choices are functional and have real consequences
