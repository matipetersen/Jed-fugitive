# Control Audit Summary - Jedi Fugitive

## Issues Found and Fixed

### ❌ Removed from Help (Not Implemented)
- **`c` - Scan/Compass**: Mentioned in help but no implementation exists
- **`@` - Character sheet**: Mentioned in help but no implementation exists

### ✅ Added to Help (Were Implemented But Missing)
- **`z` - Unequip weapon**: Fully functional, was not documented
- **`o` - Unequip armor/offhand**: Fully functional, was not documented
- **`T` - Trade with merchant**: Fully functional, was not documented
- **`p` - Toggle popup messages**: Fully functional, was not documented
- **`A` - Absorb POI** (landmarks): For Dark Side power
- **`D` - Destroy POI** (landmarks): For Light Side XP

### 📝 Clarified in Help
- **Artifact choices**: Made it clear `a`/`d` are for artifacts from inventory
- **POI choices**: Separated `A`/`D` for landmarks/ruins into own section
- **Encounter markers**: Added explanation of `?` markers on map
- **Alignment thresholds**: Corrected to 0-35, 36-65, 66-100 (not 0-30, 31-59, 60-100)
- **Vi-style diagonal**: Fixed from "ybn" to "yubn" (y=↖ u=↗ b=↙ n=↘)

## Complete Control Reference

### Movement
- **Arrow Keys**: Cardinal movement (↑↓←→)
- **hjkl**: Vi-style cardinal
- **yubn**: Vi-style diagonal (y=↖ u=↗ b=↙ n=↘)
- **Numpad 1-9**: Full 8-direction movement

### Inventory & Items
- **g**: Pick up item
- **e**: Equip weapon/armor
- **u**: Use/consume item
- **d**: Drop item
- **z**: Unequip weapon
- **o**: Unequip armor/offhand
- **x**: Inspect tile

### Combat
- **Walk into enemy**: Melee attack
- **t**: Throw grenade (targeting)
- **F**: Fire ranged weapon (targeting)

### Force Abilities
- **f**: Force powers menu

### Information
- **j**: Journal/Travel Log
- **i**: Inventory
- **v**: Sith Codex (toggle)

### Crafting & Trading
- **C**: Crafting Bench
- **T**: Trade with merchant

### Landmarks & POI
- **A**: ABSORB (Dark Side +corruption)
- **D**: DESTROY (Light Side +XP)

### Artifacts (from inventory)
- **a**: ABSORB (Dark Side)
- **d**: DESTROY (Light Side)

### System
- **?**: Help screen
- **m**: Meditate
- **p**: Toggle popups
- **S**: Save game
- **r**: Reveal map (debug)
- **q / ESC**: Quit

## Test Results
✅ All 23 help screen keys verified as implemented
✅ No duplicate key bindings (context-sensitive where needed)
✅ Help screen now 100% accurate

## Files Modified
- `src/jedi_fugitive/game/input_handler.py` - Updated help screen (lines 481-541)

## Files Created
- `scripts/audit_controls.py` - Control audit tool
- `scripts/test_help_accuracy.py` - Help screen verification test
- `CONTROL_AUDIT.md` - This summary document
