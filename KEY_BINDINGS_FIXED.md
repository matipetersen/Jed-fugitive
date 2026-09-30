# Key Bindings Reference - FIXED

## ⚠️ CONFLICTS RESOLVED

### Previous Issues:
- **'z' key** had 3 different bindings (use item, unequip, Force abilities) ❌
- **'f' key** was confusing (sometimes Force, sometimes fire weapon) ❌

### Current Solution:
- **'z' key** = Force abilities menu ONLY ✅
- **'f' key** = Fire ranged weapon (auto-aim) ONLY ✅
- **'u' key** = Use/consume item from inventory ✅
- **'q' key** = Unequip weapon ✅

---

## Complete Key Bindings Map

### MOVEMENT
| Key | Action |
|-----|--------|
| Arrow Keys | Cardinal directions (↑↓←→) |
| hjkl | Vi-style cardinal (h=←, j=↓, k=↑, l=→) |
| yubn | Vi-style diagonal (y=↖, u=↗, b=↙, n=↘) |
| Numpad 7931 | Numpad diagonal (7=↖, 9=↗, 1=↙, 3=↘) |
| > | Descend stairs/enter tomb |
| < | Ascend stairs/exit tomb |

### INVENTORY & ITEMS
| Key | Action |
|-----|--------|
| g | Pick up item at location |
| e | Equip weapon/armor from inventory |
| **u** | **Use/consume item** (stimpacks, artifacts, etc.) |
| d | Drop item from inventory |
| **q** | **Unequip weapon** |
| o | Unequip armor/offhand |
| i | Open inventory view |
| x | Inspect tile (5x5 radius) |

### COMBAT
| Key | Action |
|-----|--------|
| Walk into enemy | Melee attack |
| **f** | **Fire ranged weapon (auto-aim to nearest)** |
| F | Fire ranged weapon (manual targeting) |
| G | Throw grenade (manual targeting, 3-tile range) |

### FORCE ABILITIES
| Key | Action |
|-----|--------|
| **z** | **Open Force powers menu** (Push, Lightning, Drain, Heal) |
| r/R | Open Rituals menu (meditation, crystal attunement) |
| m | Meditate (reduce stress if safe) |

### LANDMARKS & CHOICES
| Key | Action |
|-----|--------|
| A | ABSORB POI (Dark Side path, gain power) |
| D | DESTROY POI (Light Side path, gain XP) |

When using artifacts from inventory (press 'u'):
- 'a' = ABSORB (Dark Side, +corruption)
- 'd' = DESTROY (Light Side, -corruption)

### INFORMATION & UI
| Key | Action |
|-----|--------|
| j | Journal/Travel Log |
| i | Inventory |
| v | Sith Codex (lore & discoveries) |
| ? | Help screen |
| p | Toggle popup messages |
| M | Toggle map visibility |

### CRAFTING & TRADING
| Key | Action |
|-----|--------|
| C | Crafting Bench (upgrade weapons) |
| T | Trade with merchant |
| t | Talk to NPC |

### STEALTH & DISGUISE
| Key | Action |
|-----|--------|
| Z | Attempt to hide/stealth |
| D (Shift+d) | Equip disguise |

### SYSTEM
| Key | Action |
|-----|--------|
| S | Save game (manual) |
| P | Reveal map (debug/cheat) |
| q / ESC | Quit game |

---

## Weapon Types & Firing

### Ranged Weapons (use 'f' or 'F'):
- **Blasters**: DL-44 Blaster Pistol, E-11 Blaster Rifle, Heavy Blaster Cannon
- **Bowcasters**: Wookiee Bowcaster
- **Special**: Ion weapons, Disruptors

### Melee Weapons (walk into enemy):
- **Lightsabers**: Single, Dual, Pike
- **Vibroblades**: Vibrosword, Techblade, Combat Knife
- **Force Pikes**: Electrostaff, Guard weapons
- **Ancient**: Sith War Sword, Cortosis Blade, Mandalorian Darksaber

### Grenades (use 'G'):
- Thermal Grenade (area damage)
- Requires manual targeting

---

## Combat Message System

### Player Attacks (from combat.py):
- **Death blows**: "☠ FATAL BLOW ☠ You strike enemy's head - 15 damage!"
- **Critical hits** (≥8 dmg): "★ POWER STRIKE! ★ Your weapon tears through torso! [12 dmg]"
- **Normal hits**: "You strike enemy's arm. [5 damage]"
- **Misses**: "The enemy dodges your attack!"

### Enemy Attacks (from enemy.py):
- **Fatal blows**: "Enemy delivers a fatal strike to your chest! [15 damage]"
- **Heavy damage** (≥8 dmg): "Enemy's devastating blow crushes your shoulder! [10 damage]"
- **Normal hits**: "Enemy strikes your leg. [4 damage]"
- **Cinematic**: "Pain flares as Enemy strikes your back! [6 damage]"

All combat messages now include:
- Body parts (head, torso, arm, leg, chest, shoulder, back, side)
- Damage values in brackets [X damage]
- Environmental context (tomb, wasteland, etc.)
- Varied descriptions for immersion

---

## Key Design Philosophy

1. **Single Purpose**: Each key has ONE clear function
2. **Logical Grouping**: Related actions near each other (e.g., e/q for equip/unequip)
3. **Consistency**: Lowercase = common actions, Uppercase = advanced/destructive actions
4. **Weapon Logic**: 'f' = fire, 'z' = Force abilities (no overlap)
5. **No Conflicts**: No duplicate key bindings in the same context

---

## Changes Made (December 12, 2025)

### Key Binding Fixes:
✅ Changed use_item from 'z' to 'u' (line 1780 in input_handler.py)
✅ Changed unequip from 'z' to 'q' (line 2020 in input_handler.py)
✅ Kept Force abilities on 'z' ONLY (line 2131 in input_handler.py)
✅ Kept ranged weapon firing on 'f' for auto-aim (line 2049)
✅ Kept manual targeting on 'F' (line 1023)
✅ Updated help screen with corrected bindings

### Combat Description Enhancements:
✅ Added 5 more normal hit descriptions (enemy.py line ~1240)
✅ Added 5 more heavy damage descriptions (enemy.py line ~1230)
✅ Enhanced cinematic language ("blood sprays", "pain explodes", etc.)
✅ Maintained environmental context integration

### Weapon Consistency:
✅ All ranged weapons (blasters, pistols, rifles) use 'f' or 'F'
✅ All melee weapons use walk-into-enemy
✅ Grenades use dedicated 'G' key
✅ Force abilities use dedicated 'z' key
