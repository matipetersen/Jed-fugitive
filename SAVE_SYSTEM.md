# Save System Documentation

## Overview
Jedi Fugitive now includes a comprehensive save/load system that allows you to preserve your progress and return to your game later.

## Features

### Autosave
- **Automatic saves every 20 turns** while you play
- Saves to: `~/.jedi_fugitive/saves/autosave.json` (Mac/Linux) or `%APPDATA%/JediFugitive/saves/autosave.json` (Windows)
- Silent operation - doesn't interrupt gameplay
- Ensures you never lose more than 20 turns of progress

### Manual Save
- Press **Shift+S** (capital S) during gameplay to save manually
- Shows confirmation message: "Game saved successfully!"
- Saves to the autosave location
- Use before quitting or before risky decisions

### Load Game on Startup
When you launch the game, if a save file exists, you'll see:
```
═══ SAVED GAMES FOUND ═══
1. Autosave - Level 3, Turn 150
   Saved: 2024-01-15T14:30:00

[C] Continue from autosave
[N] Start new game
[Q] Quit
```

Choose **C** to continue your previous game, or **N** to start fresh.

## What Gets Saved

### Player Data
- Position (x, y coordinates)
- Health (current HP, max HP)
- Stats (attack, defense, evasion, accuracy)
- Experience (level, XP, light/dark XP)
- Force alignment (corruption, alignment score)
- Force energy (current, maximum, force points)
- Stress level and stress system state
- Player facing direction
- Achievements (kills, tombs explored, artifacts consumed, gold collected)
- Travel log entries (your story!)

### Game State
- Turn count
- Current biome location
- Tomb status (in/out, floor level)
- Quest flags (codex, artifact status)
- Victory/death state

### Items (Limited)
- Basic inventory structure saved
- Equipped weapon and armor names saved
- *Note: Full item restoration requires additional implementation*

## Save File Location

### macOS/Linux
```
~/.jedi_fugitive/saves/
├── autosave.json
├── save_slot_1.json  (future: manual save slots)
├── save_slot_2.json
└── save_slot_3.json
```

### Windows
```
%APPDATA%/JediFugitive/saves/
├── autosave.json
├── save_slot_1.json
├── save_slot_2.json
└── save_slot_3.json
```

## Controls

| Key | Action |
|-----|--------|
| **S** (Shift+S) | Save game manually |
| **C** (at startup) | Continue from autosave |
| **N** (at startup) | Start new game |

## Technical Details

### Save Format
- JSON format for human-readability and debugging
- Includes version number for future compatibility
- Timestamp for tracking when saves were created

### Error Handling
- Corrupted saves automatically fall back to new game
- Save failures don't crash the game
- Missing save files are handled gracefully

### Performance
- Autosave is non-blocking
- Minimal performance impact (< 0.1 seconds)
- Save file size typically < 50 KB

## Planned Features (Future)

- Multiple manual save slots (3 slots planned)
- Save file management (rename, delete)
- Full inventory/item restoration
- Cloud save support
- Auto-backup before major decisions
- Save file compression

## Troubleshooting

### "Failed to load save"
- Save file may be corrupted
- Game will automatically start a new game
- Check save file location for manual recovery

### "Failed to save game"
- Disk space may be full
- Permissions issue with save directory
- Check terminal output for detailed error

### Save file not appearing
- Check the correct save directory for your OS
- Ensure you've played at least 20 turns (for autosave)
- Try manual save with Shift+S

## Development Notes

### Adding to Save State
To save additional game state, modify `serialize_game_state()` in `save_system.py`:
```python
save_data['new_field'] = getattr(game, 'new_field', default_value)
```

### Restoring State
Update `apply_save_data()` to restore new fields:
```python
if 'new_field' in game_data:
    game.new_field = game_data['new_field']
```

### Testing
Run the save system test:
```bash
python3 scripts/test_save_system.py
```

## Credits
Save system implemented to ensure your journey through the Sith wastelands can be continued another day. May the Force be with you, always.
