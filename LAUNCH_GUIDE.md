# 🎮 GAME LAUNCH GUIDE

## ✅ Quick Start

### Option 1: Launch Script (Recommended)
```bash
cd /Users/matiaspetersen/Documents/Spider/ScholarsOf/jedi-fugitive
./launch_game.py
```

### Option 2: Python with Path
```bash
cd /Users/matiaspetersen/Documents/Spider/ScholarsOf/jedi-fugitive
PYTHONPATH=src python3 -m jedi_fugitive.main
```

### Option 3: Direct Script
```bash
cd /Users/matiaspetersen/Documents/Spider/ScholarsOf/jedi-fugitive
PYTHONPATH=src python3 src/jedi_fugitive/main.py
```

---

## 🎯 Controls Quick Reference

### Movement
- **Arrow Keys / WASD / HJKL** - Move player
- **Shift + Arrow** - Move 5 tiles at once

### Combat & Force
- **Space** - Attack enemy in direction
- **Z** - Force Push
- **X** - Force Lightning
- **C** - Force Drain
- **V** - Force Heal
- **B** - Dash attack
- **N** - Blade Throw

### Stealth & Social (NEW)
- **Z** - Hide/Stealth (when near cover)
- **Shift+D** - Equip Disguise
- **t** - Talk to NPC
- **T** - Trade with merchant

### Inventory & Equipment
- **i** - Open inventory
- **e** - Equipment menu
- **g** - Pick up item
- **d** - Drop item
- **u** - Use consumable
- **c** - Crafting menu

### Information
- **@** - Character sheet
- **?** - Help screen
- **F** - Faction status
- **L** - Journey log
- **m** - World map

### Dungeon
- **>** - Descend stairs
- **<** - Ascend stairs
- **Enter** - Interact with features

### Other
- **ESC** - Cancel/Close menus
- **S** - Save game
- **Q** - Quit game

---

## 🆕 New Features This Session

### 1. Stealth System
- Press **Z** near cover to hide
- Detection radius: 8 tiles (4 while hidden)
- Movement increases noise
- Breaks on attack/Force use

### 2. Faction Battles
- Spawn automatically every 50-100 turns
- 5 factions: Sith, Republic, Hutt, Settlers, Mandalorian
- Intervene by attacking either side
- Loot battlefield after

### 3. Pursuit & Detection
- Detection level: 0-100
- Force use: +20 detection
- Combat: +10 detection
- At 100: Sith Predator spawns (boss)
- Natural decay: -1 per turn

### 4. Unique Enemy Symbols
Each enemy has distinct symbol and color:
- ⚔ Sith Acolyte (cyan)
- ⚡ Sith Warrior (red)
- ☠ Sith Assassin (purple)
- 👹 Terentatek (red)
- 👑 Sith Lord (red)

### 5. Varied Map Shapes
Each game randomly picks one of 4 shapes:
- **Elliptical** - Wide horizontal
- **Diamond** - Angular diagonal
- **Rectangular** - Long corridors
- **Irregular** - Organic boundaries

### 6. Larger Maps
- Old: ~200×200 tiles
- New: ~250-300 tiles (25-50% bigger)

---

## 📊 Diagnostic Status

**All Systems**: ✅ **OPERATIONAL**

- ✅ Python compilation: 100+ files
- ✅ Module imports: 19/19 passed
- ✅ Core systems: Player, Enemy, Combat, Map
- ✅ New systems: Stealth, Factions, Pursuit
- ✅ Items: Weapons, Armor, Consumables, Crafting
- ✅ Launch entry point: Verified

**Full Report**: See `PRE_LAUNCH_DIAGNOSTIC_REPORT.md`

---

## ⚠️ Terminal Requirements

### Minimum Requirements
- **Screen Size**: 80×24 characters (bigger is better)
- **Colors**: 256-color support recommended
- **Unicode**: UTF-8 encoding for symbols

### Recommended Terminals
- **macOS**: Terminal.app, iTerm2
- **Linux**: GNOME Terminal, Konsole, Alacritty
- **Windows**: Windows Terminal, WSL

### Setup (if needed)
```bash
# Set 256 colors
export TERM=xterm-256color

# Set UTF-8 encoding
export LC_ALL=en_US.UTF-8
```

---

## 🐛 Troubleshooting

### Module Not Found Error
```bash
# Make sure to set PYTHONPATH
cd /path/to/jedi-fugitive
PYTHONPATH=src python3 -m jedi_fugitive.main
```

### Unicode Symbols Don't Show
```bash
# Check locale
locale

# Set UTF-8 if needed
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

### Colors Look Wrong
```bash
# Check terminal type
echo $TERM

# Set 256 color mode
export TERM=xterm-256color
```

### Screen Too Small
- Resize terminal to at least 80×24
- Or maximize terminal window
- Check with: `tput cols` and `tput lines`

### Game Crashes
- Check logs: `/tmp/dark_meridian_debug.txt`
- Check crash reports: `logs/` directory
- See: `HOW_TO_REPORT_CRASHES.md`

---

## 💾 Save Files

**Location**: `~/.jedi_fugitive/saves/`

**Commands**:
- Save: Press **S** in game
- Load: Choose from main menu
- Autosave: Every 10 turns

---

## 📚 Additional Documentation

- **KEY_BINDINGS.md** - Complete control reference
- **GAME_SUMMARY.md** - Full game features overview
- **SPECIAL_DUNGEONS.md** - Dungeon types and challenges
- **LIGHTSABER_GUIDE.md** - Customization and forms
- **STEALTH_DISGUISE_FACTION_BATTLES_IMPLEMENTATION.md** - New systems details
- **PURSUIT_AND_MAP_EXPANSION.md** - Detection and maps
- **PRE_LAUNCH_DIAGNOSTIC_REPORT.md** - Full diagnostic results

---

## 🎯 Gameplay Tips

### Early Game (Levels 1-5)
- Avoid using Force powers (raises detection)
- Hide near cover when overwhelmed
- Pick up all items for crafting materials
- Talk to NPCs for quests and lore

### Mid Game (Levels 6-12)
- Equip disguises for safer exploration
- Learn lightsaber forms via meditation
- Trade with merchants for better gear
- Watch for faction battles (loot opportunity)

### Late Game (Levels 13+)
- Use Force powers strategically
- Manage detection level carefully
- Prepare for Sith Predator (at 100 detection)
- Complete special dungeons for endgame gear

---

## 🌟 May the Force Be With You!

**Status**: 🟢 **READY TO LAUNCH**

Launch the game and begin your journey as a Jedi fugitive on a hostile Sith world!

**Recommended First Playthrough**:
1. Learn basic controls with `?` key
2. Explore crash site carefully
3. Talk to first NPC you find
4. Pick up wreckage items for crafting
5. Find your first lightsaber crystal
6. Discover the Ancient Tomb entrance
7. Choose your path: Light or Dark

**Good luck, Jedi!** 🗡️⚡
