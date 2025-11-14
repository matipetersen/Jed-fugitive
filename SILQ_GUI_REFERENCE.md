# SILQ GUI SYSTEM REFERENCE
## Jedi Fugitive: Echoes of the Fallen - Complete UI Documentation

**Last Updated:** November 14, 2025  
**Version:** 2.1 - Crafting System Integration & Targeting Fix

---

## 📐 SILQ Layout Philosophy

**SILQ** = **S**tats **I**nfo **L**og **Q**uest (SILQ panel on right side)

The UI uses a clean, information-dense terminal interface optimized for roguelike gameplay. The screen is divided into distinct functional zones with minimal visual clutter but maximum tactical information.

### Core Principles:
1. **Map Dominance**: Largest area = game map (left 70%)
2. **Info at Glance**: Stats/inventory always visible (right 30%)
3. **Message Clarity**: Scrolling message log for combat feedback
4. **Context Awareness**: UI adapts to game state (targeting, inventory, dialogue)
5. **Color Coding**: Visual hierarchy through consistent color palette

---

## 🖥️ Screen Layout

```
┌─────────────────────────────────────────┬──────────────────────────┐
│                                         │     STATS & INFO         │
│                                         │  ┌──────────────────┐   │
│                                         │  │ HP: 87/100       │   │
│                                         │  │ Force: 65/100    │   │
│           GAME MAP                      │  │ Level: 12 (Bal)  │   │
│         (Main View)                     │  │ Corruption: 45%  │   │
│                                         │  │                  │   │
│    Shows: Player (@), Enemies (E),      │  │ Attack: 15       │   │
│    Items (w,a,s,!,?), Terrain           │  │ Defense: 12      │   │
│                                         │  │ Accuracy: 78%    │   │
│    Compass arrow (↗) points to          │  │ Evasion: 15%     │   │
│    nearest tomb when active             │  │ Stress: 35       │   │
│                                         │  └──────────────────┘   │
│    Reticle (X) shows targeting          │                         │
│    when using Force/weapons             │  EQUIPMENT:             │
│                                         │  Main: Lightsaber       │
│                                         │  Off: Blaster Pistol    │
│                                         │  Armor: Jedi Robes      │
├─────────────────────────────────────────┤                         │
│        MESSAGE LOG                      │  INVENTORY: (7/9)       │
│  > You strike Sith Trooper for 18 dmg  │  [1] Medkit            │
│  > Sith Trooper attacks! Miss!          │  [2] Grenade           │
│  > You gained 15 XP                     │  [3] Scrap Metal (3x)  │
│  > Level up! You are now level 12       │  [4] Cortosis Ore      │
│                                         │  [5] Kyber Crystal     │
└─────────────────────────────────────────┴──────────────────────────┘
          Turn: 234  |  Biome: Sith Tomb Level 3
              Press ? for help  |  Q to quit
```

---

## 🎨 Visual Elements

### Map Symbols

#### Player & NPCs
| Symbol | Meaning | Color | Notes |
|--------|---------|-------|-------|
| `@` | Player | White/Bold | Facing direction affects inspect |
| `E` | Enemy | Red | Sith troopers, acolytes, warriors |
| `G` | Ghost | Cyan | Ethereal Sith spirits in tombs |
| `B` | Boss | Magenta/Bold | Final confrontation enemy |

#### Terrain & Features
| Symbol | Meaning | Color | Notes |
|--------|---------|-------|-------|
| `.` | Floor | Gray | Walkable empty space |
| `#` | Wall | White | Impassable terrain |
| `+` | Door | Yellow | Opens when approached |
| `D` | Tomb | Magenta | Dungeon entrance on surface |
| `>` | Stairs Down | White | Descend deeper into tomb |
| `<` | Stairs Up | White | Ascend toward exit |
| `~` | Water | Blue | May slow movement |
| `^` | Mountain | White | Impassable high ground |
| `T` | Tree | Green | Scenery, may block vision |

#### Interactive Objects
| Symbol | Meaning | Color | Notes |
|--------|---------|-------|-------|
| `S` | Starship | Cyan/Bold | Your crashed ship, extraction point |
| `C` | Comms Terminal | Yellow/Bold | Needs 3 artifacts to activate |
| `!` | POI | Yellow | Point of Interest (Force ability unlock) |
| `?` | Mystery | Cyan | Unknown discovery, lore, or event |
| `@` | Altar | Magenta | Sith altar, corrupting influence |
| `&` | Artifact | Yellow/Bold | Corrupted Jedi artifact in tomb depths |

#### Items & Drops
| Symbol | Meaning | Color | Notes |
|--------|---------|-------|-------|
| `E` | Equipment | Yellow | Weapon, armor, or shield drop |
| `M` | Material | Cyan | Crafting material drop |
| `c` | Consumable | Green | Healing items, stims (legacy symbol) |
| `↑↓` | Token | White | Generic item on ground |

#### UI Overlays
| Symbol | Meaning | Color | Notes |
|--------|---------|-------|-------|
| `X` | Reticle | Magenta/Reverse | Targeting cursor for abilities/weapons/grenades |
| `↗↑↖←↙↓↘→` | Compass | Cyan | Points to nearest tomb entrance |
| `•` | Fog of War | Dark Gray | Unexplored areas |

---

## 📊 Stats Panel (Top Right)

### Character Stats Display

```
┌─────────────────────────┐
│ JEDI PADAWAN            │
│ Level: 12 (Balanced)    │
│ Corruption: 45%  ⚖️     │
├─────────────────────────┤
│ HP:     87/100  [████▓▓]│
│ Force:  65/100  [███▓▓▓]│
├─────────────────────────┤
│ Attack:     15  (+5 wpn)│
│ Defense:    12  (+7 arm)│
│ Accuracy:   78%         │
│ Evasion:    15%         │
│ Stress:     35          │
├─────────────────────────┤
│ Dark XP:  1250/1500     │
│ Light XP:  850/1500     │
└─────────────────────────┘
```

### Stat Explanations:

- **HP**: Current/Max health. Die at 0.
- **Force**: Energy pool for Force powers (0-100)
  - Regenerates +20/turn peaceful, +5/turn combat
  - Powers cost 5-25 Force depending on ability
- **Level**: Your character level (combined Light/Dark)
- **Corruption**: Dark Side percentage (0-100%)
  - 0-20%: Pure Light ✨
  - 21-40%: Light ☀️
  - 41-59%: Balanced ⚖️
  - 60-79%: Dark 🌑
  - 80-100%: Pure Dark ⚡
- **Attack**: Melee/base damage output
- **Defense**: Damage reduction from armor
- **Accuracy**: Hit chance % (base 70 + modifiers)
- **Evasion**: Dodge chance %
- **Stress**: Mental strain (0-100, affects corruption gain)
- **Dark XP / Light XP**: Separate XP pools for dual-path leveling

### Alignment Icons:
- ✨ Pure Light (0-20%): Light powers +45% stronger, -30% cost
- ☀️ Light (21-40%): Light powers +30% stronger, -20% cost
- ⚖️ Balanced (41-59%): All powers at base effectiveness
- 🌑 Dark (60-79%): Dark powers +30% stronger, -20% cost
- ⚡ Pure Dark (80-100%): Dark powers +45% stronger, -30% cost

---

## 🎒 Equipment & Inventory

### Equipment Slots Display

```
┌──────────────────────────┐
│ EQUIPPED:                │
│  Main Hand:              │
│   ⚔ Kyber Lightsaber     │
│   +15 Atk, 90% Acc       │
│   [Sharpened] [Crystal]  │
│                          │
│  Off Hand:               │
│   🛡 Cortosis Shield      │
│   +8 Def, 20% Block      │
│                          │
│  Armor:                  │
│   🛡 Reinforced Robes     │
│   +12 Def, +5% Eva       │
└──────────────────────────┘
```

### Inventory System (7/9 slots shown):

```
INVENTORY (7/9):
 [1] Medkit (3x)         - Heal 50 HP
 [2] Grenade (2x)        - 3-tile AOE damage
 [3] Stimpack            - +20 HP, reduces stress
 [4] Scrap Metal (5x)    - Crafting material
 [5] Cortosis Ore (2x)   - Rare crafting material
 [6] Kyber Crystal       - Legendary material
 [7] Combat Stim         - +10 Attack for 5 turns
```

### Item Types & Colors:
- **Weapons** (Yellow): Melee or ranged, equipped in main/off hand
- **Armor** (Cyan): Body slot, provides defense
- **Shields** (Blue): Off-hand slot, blocks + defense
- **Consumables** (Green): One-time use healing/buffs
- **Materials** (Magenta): Crafting components, stackable
- **Artifacts** (Gold/Bold): Quest items, 3 needed for victory

### Equipment Features:
- **Dual-Wielding**: Equip weapon in offhand for +50% offhand weapon damage
- **Shield Blocking**: Offhand shields provide block chance + defense
- **Weapon Upgrades**: Crafting can add [tags] to weapons (e.g., [Sharpened], [Crystal Focus])
- **Rarity Tiers**: Common → Uncommon → Rare → Epic → Legendary

---

## 💬 Message Log (Bottom Left)

### Message Types & Colors:

**Combat Messages** (Red/White):
```
> You strike Sith Warrior for 22 damage! 
> Sith Warrior attacks with Force Lightning!
> You take 15 damage (reduced by 5)
> Sith Warrior is defeated!
```

**System Messages** (Yellow):
```
> Level up! You are now level 12
> ★★ Sith Trooper dropped Rare Blaster Rifle! ★★
> Picked up Cortosis Ore (Rare crafting material)
> Quest Update: Artifacts collected (2/3)
```

**Force/Ability Messages** (Cyan/Magenta):
```
> You use Force Heal - restored 35 HP (-15 Force)
> You use Force Choke on Sith Acolyte! (18 damage)
> Corruption increased by 3% (now 48%)
> Force regenerated: +20 Force
```

**Exploration Messages** (Green):
```
> You discovered: Ancient Sith Altar
> Force Echo activated - revealing lore...
> Compass updated: Nearest tomb 15 tiles NE
> You entered Sith Tomb Level 3
```

**Crafting Messages** (Yellow/Bold):
```
> ✓ Crafted: Sharpened Edge - weapon upgraded!
> Materials consumed: 2x Scrap Metal, 1x Durasteel
> Lightsaber attack increased to +15 damage
```

**Warning Messages** (Red/Bold):
```
> Inventory full! Can't pick up item.
> Not enough Force energy! (need 20, have 15)
> Cannot equip - no offhand weapon slots!
> You are heavily wounded! (HP below 30)
```

### Message Log Features:
- **Auto-scroll**: New messages push old ones up
- **Max visible**: ~5-8 lines depending on screen size
- **Full history**: Press 'J' to view travel journal (all messages)
- **Color coding**: Instant recognition of message importance
- **Combat clarity**: Damage numbers, hit/miss, status effects

---

## 🎯 Targeting & Reticle System

### Targeting Mode Visual:

```
┌─────────────────────────────────────────┐
│         #####                           │
│         #...###                         │
│         #.@...#   ← You (facing right)  │
│         #..X..#   ← Reticle (targeting) │
│         ###E###   ← Enemy in crosshairs │
│                                         │
│  Message: "Force Choke (5-tile range)  │
│   - Move reticle, press Enter"         │
└─────────────────────────────────────────┘
```

### When Targeting Activates:
1. **Force Abilities**: Press 'F', select power → reticle appears
2. **Ranged Weapons**: Press 'Shift+F' with blaster/rifle equipped
3. **Grenades**: Press 'T' with grenade in inventory

### Reticle Controls:
- **Arrow Keys / HJKL / Numpad**: Move reticle
- **Enter / Space**: Confirm target and execute action
- **Escape**: Cancel targeting mode
- **X (while targeting)**: Inspect tile under reticle

### Reticle Visual States:
- **'X' Magenta/Reverse/Bold**: Standard targeting cursor
- **Red**: Out of range (ability range exceeded)
- **Green**: Valid target (enemy in range)
- **Yellow**: Friendly fire zone (be careful!)

### Range Indicators:
- **Force Abilities**: 5-8 tile range depending on power
- **Blasters**: 5-7 tile range depending on weapon
- **Grenades**: Fixed 3 tile range
- **Line of Sight**: Must have clear path (no walls)

### Targeting Messages:
```
> Fire Weapon (7-tile range) — move reticle, Enter to confirm, Esc to cancel
> Targeting: Force Lightning — move reticle, Enter to confirm, Esc to cancel
> Throw Grenade (3-tile range) — move reticle, Enter to confirm, Esc to cancel
```

---

## 🗺️ Compass System

### Visual Display:
```
Map View with compass arrow:

         ┌─────────────────┐
         │   ~~~~~         │
         │   ~~@~~   ↗     │  ← Compass shows tomb to NE
         │   ~~~~~         │
         │                 │
         └─────────────────┘
```

### Compass Features:
- **Appears**: When tomb entrances exist on current level
- **Points to**: Nearest uncleared tomb entrance
- **Position**: Edge of map panel (context-aware placement)
- **Arrows**: 8 directions (↑↗→↘↓↙←↖)
- **Color**: Cyan, subtle but visible
- **Updates**: Dynamically as you move

### Compass Directions:
- `↑` North (directly up)
- `↗` Northeast (up-right)
- `→` East (directly right)
- `↘` Southeast (down-right)
- `↓` South (directly down)
- `↙` Southwest (down-left)
- `←` West (directly left)
- `↖` Northwest (up-left)

---

## 🛠️ Interactive Menus

### 1. Inventory Menu (Press 'I')

```
╔═══════════════════════════════════════════════════════╗
║               INVENTORY (7/9 slots)                   ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  [1] Kyber Lightsaber  (Legendary Weapon)            ║
║      +15 Attack, 90% Accuracy, 2-tile reach          ║
║      Upgrades: [Sharpened] [Crystal Focus]           ║
║                                                       ║
║  [2] Cortosis Shield  (Rare Shield)                  ║
║      +8 Defense, 20% Block Chance                    ║
║                                                       ║
║  [3] Medkit (x3)  (Uncommon Consumable)              ║
║      Restores 50 HP instantly                        ║
║                                                       ║
║  [4] Scrap Metal (x5)  (Common Material)             ║
║      Basic crafting component                        ║
║                                                       ║
║  [5] Cortosis Ore (x2)  (Rare Material)              ║
║      Can short-circuit lightsabers                   ║
║                                                       ║
║  [6] Kyber Crystal  (Legendary Material)             ║
║      Force-attuned focusing crystal                  ║
║                                                       ║
║  [7] Thermal Detonator  (Rare Consumable)            ║
║      Massive AOE damage (5-tile radius)              ║
║                                                       ║
╠═══════════════════════════════════════════════════════╣
║  E=Equip  U=Use  D=Drop  X=Inspect  Esc=Close        ║
╚═══════════════════════════════════════════════════════╝
```

### 2. Force Powers Menu (Press 'F')

```
╔═══════════════════════════════════════════════════════╗
║              FORCE ABILITIES                          ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  LIGHT SIDE POWERS:                                   ║
║                                                       ║
║  [1] Force Heal  (15 Force)                          ║
║      Restore 35-50 HP • Reduces corruption           ║
║      Mastery: ✨ (+45% healing, -30% cost)           ║
║                                                       ║
║  [2] Force Protect  (20 Force)                       ║
║      +10 Defense for 5 turns                         ║
║                                                       ║
║  [3] Force Meditation  (0 Force)                     ║
║      Restore 30 Force • Out of combat only           ║
║                                                       ║
║  DARK SIDE POWERS:                                    ║
║                                                       ║
║  [4] Force Choke  (20 Force)                         ║
║      25-40 damage • Stuns 1 turn • Corruption +5%    ║
║      Mastery: ⚖️ (base effectiveness)                ║
║                                                       ║
║  [5] Force Lightning  (25 Force)                     ║
║      30-50 damage • Chain to nearby foes             ║
║                                                       ║
║  [6] Force Drain Life  (15 Force)                    ║
║      20 damage • Heal for 50% of damage dealt        ║
║                                                       ║
╠═══════════════════════════════════════════════════════╣
║  1-9=Select  Esc=Cancel  ?=Details                   ║
╚═══════════════════════════════════════════════════════╝
```

### 3. Crafting Menu (Press 'C')

```
╔═══════════════════════════════════════════════════════╗
║             ═══ CRAFTING BENCH ═══                    ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  WEAPON UPGRADES:                                     ║
║                                                       ║
║  ✓ ⚔ Sharpened Edge                                  ║
║     Sharpen blade edges for +2 Attack                ║
║     Needs: 2x Scrap Metal, 1x Durasteel Plate        ║
║                                                       ║
║  ✗ ⚔ Crystal Focus                                   ║
║     Add crystal focusing for +3 Attack               ║
║     Needs: 1x Focusing Lens, 1x Synthetic Crystal    ║
║                                                       ║
║  ✓ ⚔ Balanced Grip                                   ║
║     Improve weapon balance for +5 Accuracy           ║
║     Needs: 1x Scrap Metal, 2x Fused Wire             ║
║                                                       ║
║  ✗ ⚔ Kyber Attunement  (Legendary)                   ║
║     Attune weapon to Kyber crystal                   ║
║     +5 Attack, +10 Accuracy                          ║
║     Needs: 1x Kyber Crystal, 2x Focusing Lens        ║
║                                                       ║
║  ITEM CRAFTING:                                       ║
║                                                       ║
║  ✓ 🛠 Medkit                                          ║
║     Craft healing item (+50 HP)                      ║
║     Needs: 1x Crystal Shard, 1x Electronic Part      ║
║                                                       ║
║  ✗ 🛠 Thermal Detonator                              ║
║     Craft explosive (massive AOE damage)             ║
║     Needs: 1x Compact Power Core, 1x Ionization      ║
║                                                       ║
╠═══════════════════════════════════════════════════════╣
║  ✓ = Have materials  ✗ = Missing materials          ║
║  1-9=Craft  Esc=Close                                ║
╚═══════════════════════════════════════════════════════╝
```

### 4. Equipment Menu (Press 'E')

```
╔═══════════════════════════════════════════════════════╗
║            EQUIP ITEM: Kyber Lightsaber               ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  This is a legendary weapon attuned to the Force.     ║
║  Its blade hums with ancient power.                   ║
║                                                       ║
║  Stats:                                               ║
║   • Type: Lightsaber (Melee)                         ║
║   • Damage: +15 Attack                               ║
║   • Accuracy: +10%                                   ║
║   • Range: 2 tiles                                   ║
║   • Rarity: Legendary                                ║
║   • Upgrades: [Sharpened] [Crystal Focus]            ║
║                                                       ║
║  Current Equipment:                                   ║
║   Main Hand: Vibroblade (+8 Attack)                  ║
║   Off Hand: (Empty)                                  ║
║                                                       ║
║  Where to equip?                                      ║
║   [M] Main Hand (replace Vibroblade)                 ║
║   [O] Off Hand                                       ║
║   [Esc] Cancel                                       ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
```

### 5. Travel Journal (Press 'J')

```
╔═══════════════════════════════════════════════════════╗
║                TRAVEL JOURNAL                         ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  Turn 234 - Sith Tomb Level 3                        ║
║   > Descended deeper into the tomb...                ║
║   > The darkness presses in from all sides.          ║
║                                                       ║
║  Turn 235                                             ║
║   > Encountered Sith Warrior (HP: 85)                ║
║   > Used Force Choke - dealt 32 damage              ║
║   > Corruption increased to 48%                      ║
║                                                       ║
║  Turn 236                                             ║
║   > Defeated Sith Warrior!                           ║
║   > Gained 45 XP (Dark Side)                         ║
║   > ★★ Dropped: Cortosis Ore (Rare) ★★              ║
║                                                       ║
║  Turn 237                                             ║
║   > Found crafting material: Cortosis Ore            ║
║   > Scavenged resource for my arsenal (Dark)         ║
║                                                       ║
║  Turn 240                                             ║
║   > Opened Crafting Bench                            ║
║   > Crafted: Sharpened Edge upgrade                  ║
║   > Lightsaber attack increased to +15!              ║
║                                                       ║
╠═══════════════════════════════════════════════════════╣
║  ↑↓=Scroll  Home/End=Jump  Esc=Close                 ║
╚═══════════════════════════════════════════════════════╝
```

### 6. Sith Codex (Press 'K')

```
╔═══════════════════════════════════════════════════════╗
║                  SITH CODEX                           ║
║            Knowledge of the Dark Side                 ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  [1] ⚡ Force Lightning                               ║
║      "Power flows through absolute conviction."      ║
║      Manifesting raw Force energy as electrical      ║
║      discharge. Pure, unrestrained power.            ║
║                                                       ║
║  [2] 🌀 Force Drain                                   ║
║      "The essence of one becomes strength for        ║
║      another."                                       ║
║      Siphoning life force from enemies to sustain    ║
║      yourself. The Sith way of endurance.            ║
║                                                       ║
║  [3] 💀 Dark Side Corruption                          ║
║      "Fear leads to anger. Anger leads to hate."     ║
║      Each step toward darkness promises power,       ║
║      but demands sacrifice of your soul.             ║
║                                                       ║
║  [4] 🏛️ Ancient Sith Tombs                            ║
║      "Here lie the architects of galactic empires."  ║
║      The tombs contain both treasures and curses.    ║
║      Proceed with caution... or abandon it.          ║
║                                                       ║
║  [5] ⚔️ Rule of Two                                   ║
║      "One to embody power, one to crave it."         ║
║      The Sith Code evolved to prevent infighting.    ║
║      Master and apprentice, in eternal conflict.     ║
║                                                       ║
╠═══════════════════════════════════════════════════════╣
║  Entries unlocked: 5/50 • Read more to learn...      ║
║  1-9=Read  ↑↓=Scroll  Esc=Close                      ║
╚═══════════════════════════════════════════════════════╝
```

---

## 🎮 Keyboard Controls Reference

### Movement & Basic Actions
| Key | Action | Notes |
|-----|--------|-------|
| `↑↓←→` | Move (Cardinal) | Primary movement |
| `YUBN` | Diagonal Movement | Y=NW, U=NE, B=SW, N=SE |
| `HJKL` | Vi-style Movement | H=left, J=down, K=up, L=right |
| `Numpad` | 8-way Movement | Classic roguelike |
| `.` or `Space` | Wait/Rest | Skip turn, regenerate Force |
| `G` | Get/Pickup | Pick up item at your feet |
| `X` | Inspect/Examine | Look at tile details |

### Inventory & Equipment
| Key | Action | Notes |
|-----|--------|-------|
| `I` | Inventory | View all items |
| `E` | Equip | Equip weapon/armor from inventory |
| `U` | Use | Use consumable item |
| `D` | Drop | Drop item from inventory |
| `C` | Crafting Menu | Upgrade weapons, craft items |

### Combat & Abilities
| Key | Action | Notes |
|-----|--------|-------|
| `F` | Force Powers | Select and use Force abilities |
| `Shift+F` | Fire Weapon | Ranged weapon targeting mode |
| `T` | Throw Grenade | Grenade targeting mode (3-tile range) |
| `M` | Meditate | Restore Force (out of combat only) |

### Information & Menus
| Key | Action | Notes |
|-----|--------|-------|
| `J` | Travel Journal | Full message log history |
| `K` | Sith Codex | Lore entries and Force knowledge |
| `S` | Stats | Detailed character stats screen |
| `?` | Help | Key binding reference |
| `Q` | Quit | Exit game (with confirmation) |

### Targeting Mode (when reticle active)
| Key | Action | Notes |
|-----|--------|-------|
| `↑↓←→` / `HJKL` | Move Reticle | Position targeting cursor |
| `Enter` / `Space` | Confirm Target | Execute ability/weapon/grenade |
| `Escape` | Cancel | Exit targeting mode |
| `X` | Inspect Target | Examine tile under reticle |

### Menu Navigation
| Key | Action | Notes |
|-----|--------|-------|
| `↑↓` or `JK` | Scroll Up/Down | Navigate menu items |
| `1-9` | Quick Select | Choose numbered option |
| `Enter` | Confirm | Select highlighted item |
| `Escape` | Back/Cancel | Close menu |
| `Home` / `End` | Jump to Top/Bottom | Fast navigation |

---

## 🎨 Color Palette System

### Color Pairs (curses color system):

| Color ID | Foreground | Background | Usage |
|----------|------------|------------|-------|
| 1 | Red | Black | Enemies, damage, warnings |
| 2 | Green | Black | Healing, positive effects, trees |
| 3 | Yellow | Black | Items, POIs, important info |
| 4 | Blue | Black | Water, shields, light side |
| 5 | Magenta | Black | Tombs, bosses, dark side |
| 6 | Cyan | Black | Info, ghosts, materials |
| 7 | White | Black | Player, text, UI borders |
| 8 | Gray | Black | Floor, fog, inactive elements |
| 9 | Bold White | Black | Emphasized text, headers |

### Visual Hierarchy:
1. **Player** = White/Bold (always visible)
2. **Enemies** = Red (immediate threat)
3. **Items/Loot** = Yellow (desirable)
4. **Interactive** = Cyan/Magenta (exploration)
5. **Terrain** = Gray/Green (background)

---

## 📱 Responsive Layout

### Standard Terminal (80x24 minimum):
```
Map: 50 cols x 18 rows
SILQ Panel: 28 cols x 24 rows
Message Log: 50 cols x 4 rows
Status Bar: 80 cols x 1 row
```

### Large Terminal (120x40):
```
Map: 80 cols x 30 rows
SILQ Panel: 38 cols x 40 rows
Message Log: 80 cols x 8 rows
Status Bar: 120 cols x 1 row
```

### Minimum Requirements:
- **Width**: 80 columns (absolute minimum)
- **Height**: 24 rows (absolute minimum)
- **Colors**: 8 color support required
- **Unicode**: UTF-8 for special symbols

---

## 🔧 UI States & Modes

### 1. Exploration Mode (Default)
- Full map visible
- Stats panel always shown
- Message log scrolling
- Compass active (when tombs exist)
- Free movement

### 2. Targeting Mode (Force/Weapon/Grenade)
- Reticle overlays map
- Range indicator in message
- Movement keys control reticle
- Enter confirms, Escape cancels
- Target info shown in panel

### 3. Inventory Mode (Menu)
- Map dimmed/background
- Full-screen item list
- Item details on selection
- Action prompts (E/U/D/X)
- Escape returns to exploration

### 4. Combat Mode (Automatic)
- Enemy stats shown on hover
- Damage numbers in messages
- HP bars visible
- Status effects displayed
- Force regeneration reduced

### 5. Dialogue Mode (Story Events)
- Map hidden
- Full-screen text box
- Alignment choices shown
- Press key to continue
- Returns to exploration after

### 6. Death Screen (Game Over)
- Map hidden
- Stats summary shown
- Corruption final tally
- Ending text based on alignment
- Option to view full journal

---

## 🌟 Advanced UI Features

### 1. Dynamic Stats Display
- Stats update in real-time
- Color changes with alignment:
  - Pure Light: Blue glow
  - Balanced: White
  - Pure Dark: Red glow
- Warning indicators (low HP flashes red)
- Buffs/debuffs shown with icons

### 2. Context-Aware Messages
- Messages adapt to alignment:
  - **Light**: "You defended yourself reluctantly..."
  - **Dark**: "You struck down the fool mercilessly!"
  - **Balanced**: "You defeated the enemy."
- Emotional tone matches corruption level
- Lore reveals change based on Force mastery

### 3. Smart Inventory
- Materials stack automatically (Scrap Metal x5)
- Items sorted by type (weapons, armor, consumables, materials)
- Equipped items marked with [E]
- Rarity color-coded
- Quick-use hotkeys (1-9)

### 4. Crafting Availability
- ✓ Green checkmark = have materials
- ✗ Red X = missing materials
- Recipe type icons:
  - ⚔ = Weapon upgrade
  - 🛠 = Item craft
  - 🔧 = Repair
- Skill requirements shown (future feature)

### 5. Tooltip System
- Hover over symbols for info
- Enemy stats on inspect
- Item details on selection
- Ability costs and ranges
- Terrain effects explained

---

## 🐛 UI Polish & Feedback

### Visual Polish Elements:
- **Borders**: Box-drawing characters (═ ║ ╔ ╗ ╚ ╝)
- **Separators**: Clean section dividers
- **Alignment**: Centered titles, justified text
- **Spacing**: Generous padding for readability
- **Emphasis**: Bold for important info, colors for urgency

### Audio Feedback (Terminal Beeps):
- Error actions → single beep
- Level up → double beep
- Death → long beep
- Victory → triple beep
- (Note: Most terminals support `\a` beep character)

### Animation (Subtle):
- HP/Force bars fill/drain smoothly
- Messages slide up gently
- Reticle pulses when active
- Damage numbers briefly flash

### Accessibility:
- High contrast text (white on black)
- No color-only information (text labels too)
- Keyboard-only control (no mouse required)
- Clear visual hierarchy
- Large readable font recommended

---

## 📚 UI Best Practices

### For Players:
1. **Keep terminal large**: 100x30+ for best experience
2. **Use monospace font**: Courier, Consolas, or Menlo
3. **Enable 256 colors**: Modern terminals support this
4. **Check key bindings**: Press `?` in-game for reference
5. **Read messages**: Combat feedback is crucial

### For Developers:
1. **Curses optimization**: Minimize refresh calls
2. **Buffer updates**: Batch UI changes
3. **Error handling**: Graceful degradation for small terminals
4. **Color fallbacks**: Work in 8-color mode
5. **Testing**: Test on different terminal sizes

---

## 🆕 Recent Updates (v2.1)

### Targeting System Fix (Nov 14, 2025):
- **Fixed**: Ranged weapons and grenades now show reticle cursor
- **Changed**: `ui_renderer.py` line 268-273 now checks for:
  - `pending_force_ability` (Force powers) ✓
  - `pending_gun_shot` (Ranged weapons) ✓ NEW
  - `pending_grenade_throw` (Grenades) ✓ NEW
- **Result**: All targeting modes now display the 'X' reticle

### Crafting System Integration:
- **New Menu**: Press 'C' to open crafting bench
- **Visual Indicators**: ✓/✗ show material availability
- **Recipe Display**: Type icons (⚔ 🛠 🔧) for quick recognition
- **Materials**: New 'M' token for material drops on map
- **Inventory**: Materials shown with quantity (e.g., "Scrap Metal (3x)")

### Material Drops:
- **Drop Rate**: 20% chance on enemy death
- **Visual**: 'M' cyan token on map
- **Rarity Based**: Enemy tier determines material quality
  - Common enemies → Common materials
  - Legendary enemies → Kyber Crystals, Beskar
- **Pickup**: Same system as equipment drops

### Equipment Improvements:
- **Offhand Debug**: Added debug messages for shield equip issues
- **Dual-Wield**: Clarified offhand weapon vs shield handling
- **Weapon Upgrades**: Crafted upgrades show as [tags] on weapon names
- **Material Stacking**: Multiple same materials = 1 inventory slot

### Lore Integration:
- **Loading Messages**: 50+ Sith lore snippets replace DEBUG messages
- **Travel Journal**: Crafting actions add narrative entries
- **Alignment Flavor**: Material pickup messages reflect Light/Dark alignment
- **Codex Expansion**: Crafting lore entries unlock through gameplay

---

## 📖 Glossary of UI Terms

- **SILQ**: Stats-Info-Log-Quest panel (right side)
- **Reticle**: Targeting cursor ('X') for abilities/weapons
- **Compass**: Directional arrow pointing to objectives
- **POI**: Point of Interest (Force ability unlock)
- **Tooltip**: Hover information for symbols/items
- **Token**: Map symbol representing an object ('E', 'M', etc.)
- **Rarity**: Item quality (Common → Legendary)
- **Material**: Crafting component (stackable)
- **Corruption**: Dark Side alignment percentage (0-100%)
- **Force Pool**: Energy bar (0-100) for Force powers
- **Dual-Wield**: Weapons in both main + offhand slots
- **Mastery**: Alignment power bonus (0-3 levels)

---

## 🎯 Quick Start UI Checklist

### New Player UI Orientation:
1. ✓ Locate yourself (`@` symbol on map)
2. ✓ Check HP bar (top right) - don't let it hit 0!
3. ✓ Note Force energy (regenerates over time)
4. ✓ Watch message log (bottom left) for feedback
5. ✓ Find nearest tomb with compass arrow
6. ✓ Press `?` for full key reference
7. ✓ Press `I` to check starting inventory
8. ✓ Press `S` for detailed stats explanation
9. ✓ Learn targeting: press `F` to test Force powers
10. ✓ Check corruption % - track your alignment

### Mid-Game UI Mastery:
1. ✓ Use 'X' inspect to learn enemy stats before fighting
2. ✓ Monitor Force regeneration (+20 peaceful, +5 combat)
3. ✓ Watch for material drops ('M' tokens)
4. ✓ Open crafting menu ('C') when you have materials
5. ✓ Check travel journal ('J') to track story progression
6. ✓ Dual-wield weapons for +50% offhand damage
7. ✓ Keep inventory organized (stack materials)
8. ✓ Use meditate ('M') to restore Force out of combat
9. ✓ Read Sith Codex ('K') for lore and ability info
10. ✓ Balance corruption for optimal power builds

---

## 🔮 Future UI Enhancements (Planned)

### Short-term:
- **Mini-map**: Small overview map in corner
- **Skill Tree**: Visual progression for crafting skills
- **Combat Log**: Separate tab for combat-only messages
- **Quest Tracker**: Active objective display

### Long-term:
- **Mouse Support**: Click to move/interact (optional)
- **Custom Keybinds**: User-configurable controls
- **UI Themes**: Light/dark mode options
- **Sound Effects**: Optional audio cues
- **Replay System**: Watch your run as ASCII animation

---

## 📝 Credits & Contact

**UI Design**: SILQ system - Stats/Info/Log/Quest architecture  
**Inspiration**: Classic roguelikes (NetHack, DCSS, ToME)  
**Engine**: Python 3.11+ with curses library  
**Terminal**: Optimized for modern terminal emulators

**For questions or suggestions about the UI:**
- Check in-game help (`?` key)
- Consult KEY_BINDINGS.md for detailed controls
- Read PROGRESSION_SYSTEM.md for game mechanics

---

## ⚡ Performance Tips

### Smooth UI Experience:
1. Use **dedicated terminal**: Not IDE embedded terminals
2. Enable **GPU acceleration**: iTerm2, Windows Terminal support this
3. Use **native terminal apps**: Better than browser-based
4. Set **reasonable size**: 100x30 is optimal, 120x40 max
5. Close **background apps**: Free up CPU for smooth rendering

### Troubleshooting:
- **Flickering**: Increase terminal refresh rate
- **Lag**: Reduce terminal size
- **Colors wrong**: Enable 256-color mode
- **Keys don't work**: Check terminal key bindings
- **Text overlap**: Use monospace font only

---

**May the Force guide your UI navigation, and may your terminal never crash!**

*Last updated: November 14, 2025 - Version 2.1*  
*Compatible with: Jedi Fugitive v1.8+*
