# Quick Reference: Reporting Crashes

## When You Encounter a Crash

### 1. Find the Log File
```bash
cd /Users/matiaspetersen/Documents/Spider/ScholarsOf/jedi-fugitive
ls -lht logs/ | head -5
```

The most recent log will be at the top.

### 2. View the Log
```bash
cat logs/game_crash_log_YYYYMMDD_HHMMSS.txt
```

Or just open it in VS Code:
```bash
code logs/game_crash_log_*.txt
```

### 3. What to Share

When reporting a crash to me, share:
- **The full log file** (copy entire contents)
- **What you were doing** when it crashed
- **Whether it's reproducible** (does it happen every time?)

## Log File Location

**Path**: `/Users/matiaspetersen/Documents/Spider/ScholarsOf/jedi-fugitive/logs/`

Each game session creates a new log file with timestamp.

## What's Logged

✅ All errors with full stack traces  
✅ Game state at crash time (player stats, location, etc.)  
✅ Major game events (world gen, tomb entry, etc.)  
✅ Session info (start time, Python version, platform)  

## Play Again Feature

After death or victory:
- View your complete journey log
- Press `[P]` to play again (fresh game)
- Press `[Q]` to quit

No need to restart the entire program!

## Example: Good Bug Report

```
**Crash Report**

What happened: Game crashed when entering a tomb on turn 45

Location: logs/game_crash_log_20251117_204523.txt

Error from log:
[2025-11-17 20:45:23] ERROR: TOMB_ENTRY_ERROR
Exception Type: KeyError
Exception Message: 'tomb_level'
Game State: turn 45, player at (145, 67), HP: 85/100

What I was doing: 
- Walking through desert biome
- Saw tomb entrance marker 'T'
- Pressed Enter to enter tomb
- Game crashed immediately

Reproducible: Yes, happens every time I try to enter THIS specific tomb
```

## Tips

- Logs are **automatically created** - you don't need to do anything special
- Each crash is **fully logged** with game state
- Logs are **timestamped** so you can find the right one
- Old logs are **kept** so you can report multiple issues

## Quick Commands

**View most recent log:**
```bash
tail -100 logs/game_crash_log_*.txt | head -80
```

**Count crashes in session:**
```bash
grep -c "ERROR:" logs/game_crash_log_*.txt
```

**Find all CRASH entries:**
```bash
grep "CRASH" logs/game_crash_log_*.txt
```

**List all game events:**
```bash
grep "EVENT" logs/game_crash_log_*.txt
```
