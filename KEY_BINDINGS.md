# Jedi Fugitive - Complete Key Bindings Reference

## MOVEMENT KEYS

### Cardinal Movement (4 directions)
- **Arrow Keys**: ↑↓←→ (Up, Down, Left, Right)
- **Vi-style Keys**: h j k l
  - `h` = Left (West)
  - `j` = Down (South)
  - `k` = Up (North)
  - `l` = Right (East)

### Diagonal Movement (4 directions)
- **Vi-style Keys**: y b n
  - `y` = Up-Left (Northwest) ↖
  - `b` = Down-Left (Southwest) ↙
  - `n` = Down-Right (Southeast) ↘
  - **NOTE**: `u` (Up-Right) removed to avoid conflict with "use item"

- **Numpad Keys**: 7 1 3 9
  - `7` = Up-Left (Northwest) ↖
  - `9` = Up-Right (Northeast) ↗
  - `1` = Down-Left (Southwest) ↙
  - `3` = Down-Right (Southeast) ↘

## ACTION KEYS

### Inventory Management
- `g` = **Pick up** item at current location
- `e` = **Equip** weapon/armor/shield from inventory
  - For shields: Auto-equips to offhand
  - For 1H weapons with main weapon equipped: Prompts for main (`m`) or offhand (`o`)
- `u` = **Use** consumable item (stimpack, artifact, etc.)
- `d` = **Drop** item from inventory
- `i` = Open **inventory** screen

### Interaction
- `x` = **Inspect** tile (examine objects/enemies)
- `Space` = **Confirm** action / Continue dialogue
- `Enter` = **Confirm** action / Continue dialogue

### Combat
- **Walk into enemy** = Melee attack
- `t` = **Throw grenade** (targeting mode, 3-tile range)
- `F` = **Fire** ranged weapon (targeting mode, weapon-dependent range)

### Force Powers
- `f` = Open **Force abilities** menu
- `m` = **Meditate** (restore Force energy, HP, reduce stress - may attract enemies!)
- `c` = Show Force **compass** (locate objectives)

### Information & Meta
- `j` = Open **journal** / travel log
- `v` = Open **Sith Codex** (lore entries)
- `@` = View **character** sheet
- `C` = Open **crafting** bench (upgrade weapons, craft items)
- `?` = Show **help** screen
- `q` = **Quit** game
- `ESC` = **Cancel** current action

### Debug/Admin (optional)
- `r` = **Reveal** map (debug mode)
- `p` = Toggle **popups** on/off

## TARGETING MODE KEYS

When in targeting mode (after pressing `t` for grenade or `F` for gun):
- **Movement Keys** (all listed above) = Move targeting reticle
- `Space` or `Enter` = **Confirm** target and fire/throw
- `ESC` or `c` = **Cancel** targeting

## SPECIAL PROMPTS

### Artifact Choice (when picking up artifacts)
- `a` = **ABSORB** artifact (Dark Side path) - gain power, increase corruption
- `d` = **DESTROY** artifact (Light Side path) - resist temptation, stay pure

### Dual Wield Prompt (when equipping 1H weapon with main weapon already equipped)
- `m` = Equip to **Main hand** (replace current main weapon)
- `o` = Equip to **Offhand** (dual wield)
- `ESC` = Cancel equip

### Inventory/Menu Navigation
- **Arrow Keys** or **hjkl** = Navigate menu options
- `Number keys` (1-9) = Select item by index (if numbered)
- `Space` or `Enter` = Confirm selection
- `ESC` = Cancel/Close menu

## RECENT CHANGES (Fixed)

### v1.2 - Key Binding Fixes
- **FIXED**: Removed `u` from diagonal movement to resolve conflict with "use item" command
  - Previously: `u` key was mapped to both diagonal up-right movement AND use item
  - Now: `u` key exclusively triggers "use item" command
  - Alternative: Use numpad `9` for diagonal up-right movement

- **IMPROVED**: Enhanced dual wield prompt for offhand weapons
  - Added clear multi-line prompt when equipping 1H weapons
  - Shows current main weapon name
  - Lists all options (`m`, `o`, ESC) with descriptions

- **ADDED**: Shield drop system
  - Enemies now drop shields (15% of equipment drops)
  - Shield rarity scales with enemy tier
  - Shields auto-equip to offhand slot

## NOTES

1. **Movement Priority**: All movement keys are processed BEFORE action keys, so movement takes precedence
2. **Offhand Equipment**: 
   - Shields always go to offhand
   - One-handed weapons can go to offhand for dual-wielding
   - Two-handed weapons cannot dual-wield
3. **Combat**: Walking into enemies triggers melee attack automatically
4. **Force Meditation**: Has a risk/reward mechanic - heals HP but may spawn enemies nearby
5. **Artifact Choices**: Your decisions (absorb vs destroy) permanently affect your Force alignment and abilities

## TROUBLESHOOTING

**Q: Why can't I use items with 'u' key?**
A: This was fixed in v1.2. If you're still seeing issues, ensure you're on the latest version.

**Q: How do I equip shields?**
A: Pick up shield with `g`, then press `e` to equip. Shields auto-equip to offhand slot.

**Q: How do I dual-wield weapons?**
A: 
1. Equip a one-handed weapon to main hand
2. Pick up another one-handed weapon
3. Press `e` to equip
4. Choose `o` for offhand when prompted

**Q: Why can't I dual-wield?**
A: Your main weapon might be two-handed or already using both hands. Only one-handed weapons can dual-wield.
