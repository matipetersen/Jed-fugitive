# Crash Logger & Play Again Features

## Overview
Added comprehensive crash logging system and play again functionality to help debug issues and improve player experience.

## Features Added

### 1. Crash Logger System

**File**: `src/jedi_fugitive/utils/crash_logger.py`

The crash logger automatically captures:
- **All errors with full stack traces**
- **Game state at time of crash** (player position, HP, level, corruption, etc.)
- **Timestamps** for all events
- **Game events** (world generation, tomb entry, etc.)
- **Session information** (start time, duration, Python version, platform)

**Log Location**: `logs/game_crash_log_YYYYMMDD_HHMMSS.txt`

**Usage**:
```python
from jedi_fugitive.utils.crash_logger import log_error, log_info, log_game_event

# Log an error with full details
try:
    risky_operation()
except Exception as e:
    log_error("OPERATION_FAILED", "Description of what failed", e, game_state_dict)

# Log an info message
log_info("World generation started")

# Log a game event
log_game_event("TOMB_ENTRY", f"Player entered tomb at ({x}, {y})")
```

**Automatic Logging**:
The logger is automatically integrated into:
- Game initialization (`main.py`)
- World generation (`game_manager.py`)
- Tomb entry (`game_manager.py`)
- Main game loop (render, input, tick)
- All major error handling blocks

### 2. Play Again Button

**Modified Files**:
- `src/jedi_fugitive/main.py` - Added play again loop
- `src/jedi_fugitive/game/game_manager.py` - Added play again prompts

**How It Works**:
1. When the game ends (death or victory), the end screen displays
2. Player is shown their full story/journey log
3. Screen presents options:
   ```
   [P] Play Again
   [Q] Quit
   ```
4. Selecting `[P]` restarts the game with a fresh world
5. Selecting `[Q]` exits to terminal

**Victory Screen**:
- Shows final statistics (turns, level, artifacts, corruption)
- Displays 5 different endings based on corruption level
- Shows complete travel log
- Offers play again option

**Death Screen**:
- Shows death statistics (turns survived, cause of death, location)
- Displays Sith Lord taunt based on performance
- Shows last 5 journal entries
- Shows complete travel log
- Offers play again option

## Integration with Existing Systems

### Logging Integration Points:

1. **Main Loop** (`main.py`):
   - Session start/end logging
   - Curses initialization errors
   - Keyboard interrupts
   - Unexpected crashes

2. **Game Manager** (`game_manager.py`):
   - Initialization errors
   - World generation failures
   - Render errors (draw loop)
   - Input handling errors
   - Tomb entry errors

3. **Game State Snapshots**:
   When an error occurs, the following state is captured:
   - Player position (x, y)
   - Player health (hp, max_hp)
   - Player level
   - Stress level
   - Dark corruption percentage
   - Force points
   - In tomb status
   - Turn count
   - Game running/death/victory status
   - Enemy count
   - Map dimensions

## Testing

**Test Script**: `scripts/test_logger_and_play_again.py`

Tests:
1. ✅ Logger initialization
2. ✅ Info logging
3. ✅ Game event logging
4. ✅ Error logging (with and without exceptions)
5. ✅ Game state snapshot capture
6. ✅ Logger close and session summary
7. ✅ Play again method signatures

**Run Tests**:
```bash
python scripts/test_logger_and_play_again.py
```

## Usage for Bug Reports

When you encounter a crash:

1. **Check the logs directory**:
   ```bash
   ls -lh logs/
   ```

2. **View the most recent log**:
   ```bash
   cat logs/game_crash_log_*.txt
   ```

3. **Share the log file** when reporting bugs - it contains:
   - Exact error type and message
   - Full stack trace showing where the crash occurred
   - Game state at time of crash
   - Sequence of events leading to the crash

## Example Log Output

```
================================================================================
JEDI FUGITIVE - CRASH & ERROR LOG
================================================================================
Session started: 2025-11-17 20:41:20
Python version: 3.11.5
Platform: darwin
================================================================================

[2025-11-17 20:41:20] INFO: Game started
[2025-11-17 20:41:20] EVENT [WORLD_GEN]: World generation completed successfully

================================================================================
[2025-11-17 20:42:15] ERROR: TOMB_ENTRY_ERROR
================================================================================

Exception Type: KeyError
Exception Message: 'tomb_level'

Stack Trace:
Traceback (most recent call last):
  File "game_manager.py", line 595, in enter_tomb
    level = self.tomb_data['tomb_level']
KeyError: 'tomb_level'

Game State at Time of Error:
----------------------------------------
  player_x: 145
  player_y: 67
  player_hp: 85
  player_max_hp: 100
  player_level: 3
  player_stress: 45
  player_corruption: 12
  player_force_points: 5
  in_tomb: False
  turn_count: 127
  running: True
  death: False
  victory: False
  enemy_count: 8
  map_height: 100
  map_width: 200

================================================================================
```

## Benefits

1. **Better Bug Reports**: Detailed crash logs with game state make debugging much easier
2. **No Lost Context**: Logger captures everything automatically - no need to remember what happened
3. **Session Tracking**: Each game session has its own log file with timestamps
4. **Quick Restart**: Play again button eliminates need to relaunch the entire game
5. **Player-Friendly**: Clear options at end screen instead of just exiting

## Future Enhancements

Possible improvements:
- Add option to save crash logs with custom descriptions
- Include screenshot/map state in logs
- Email/upload crash reports automatically
- Add performance metrics (FPS, memory usage)
- Log player actions for replay debugging
