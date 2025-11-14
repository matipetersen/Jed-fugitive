# Crafting, Dual-Wielding & Shields - Implementation Summary

## 🎯 Features Implemented

### 1. **Shields System** ✅
**File**: `src/jedi_fugitive/items/shields.py`

**Shield Types:**
- Physical Shields (riot shields, metal shields)
- Energy Shields (force fields, bucklers)
- Cortosis Shields (lightsaber resistant)
- Force Shields (Jedi/Sith infused)

**Shield Stats:**
- **Defense Bonus**: +1 to +8
- **Evasion Bonus**: -2 to +4 (heavy shields reduce evasion)
- **Weight**: Affects carry capacity
- **Special Abilities**: Lightsaber Resist, Energy Absorption, Fear Aura

**Examples:**
- **Scrap Metal Shield** (Common): +2 Defense, -2 Evasion
- **Personal Force Field** (Rare): +6 Defense, +2 Evasion
- **Jedi Guardian Shield** (Legendary): +6 Defense, +4 Evasion, Force Enhanced

### 2. **Dual-Wielding System** ✅
**File**: `src/jedi_fugitive/game/equipment.py` (functions: `equip_offhand`, `unequip_offhand`)

**Mechanics:**
- Equip two 1H weapons for dual-wield
- Offhand weapon grants 50% of its bonuses
- Main weapon: Full attack + accuracy bonus
- Offhand weapon: Half attack + half accuracy bonus

**Restrictions:**
- Cannot dual-wield with 2H weapons
- Cannot use shield when dual-wielding
- Both weapons must have `HandRequirement.ONE_HAND`

**Examples:**
```
Main: Vibroblade (+5 Attack, +8 Accuracy)
Off:  Electro-Sword (+3 Attack, +3.5 Accuracy) [50% bonus]
Total: +8 Attack, +11.5 Accuracy
```

### 3. **Crafting System** ✅
**Files**: 
- `src/jedi_fugitive/items/crafting.py` (materials, recipes)
- `src/jedi_fugitive/game/equipment.py` (crafting functions)

#### **Materials System**

**Material Types:**
- **Common**: Scrap Metal, Durasteel Plate, Fused Wire, Power Cell
- **Uncommon**: Plasteel Composite, Focusing Lens, Advanced Circuitry
- **Rare**: Cortosis Ore, Phrik Alloy, Synthetic Crystal, Compact Power Core
- **Legendary**: Beskar Ingot, Kyber Crystal

**Material Tokens** (dungeon spawns):
- `m` = Scrap Metal
- `M` = Durasteel Plate  
- `w` = Fused Wire
- `P` = Power Cell
- `p` = Plasteel Composite
- `l` = Focusing Lens
- `C` = Advanced Circuitry
- `o` = Cortosis Ore
- `K` = Kyber Crystal

#### **Crafting Recipes**

**Weapon Upgrades:**
1. **Sharpened Edge** (2x Scrap Metal, 1x Durasteel) → +2 Attack
2. **Balanced Grip** (1x Scrap Metal, 2x Fused Wire) → +5 Accuracy
3. **Reinforced Frame** (2x Durasteel, 1x Plasteel) → +20 Durability
4. **Ion Capacitor** (2x Power Cell, 1x Advanced Circuitry) → +3 Damage vs Droids
5. **Cortosis Weave** (1x Cortosis Ore, 2x Fused Wire) → +3 Defense, Lightsaber Resist
6. **Power Cell Overcharge** (3x Power Cell, 1x Compact Core) → +5 Damage
7. **Crystal Focus** (1x Focusing Lens, 1x Synthetic Crystal) → +8 Accuracy, +3 Attack
8. **Beskar Reinforcement** (1x Beskar Ingot, 2x Durasteel) → +8 Defense, +50 Durability
9. **Kyber Attunement** (1x Kyber Crystal, 2x Focusing Lens) → +10 Attack, +10 Accuracy, Force Resonance

**Item Crafting:**
1. **Medkit** (1x Scrap Metal, 1x Fused Wire) → Restores 30 HP
2. **Energy Shield Generator** (3x Power Cell, 2x Advanced Circuitry, 1x Plasteel) → Energy Buckler shield
3. **Thermal Detonator** (2x Power Cell, 1x Advanced Circuitry, 1x Ionization Chamber) → Grenade

#### **Crafting Interface**
- Press **'C'** to open Crafting Bench
- Shows all recipes with material requirements
- **[✓]** = Can craft (have materials)
- **[✗]** = Cannot craft (missing materials)
- Consumes materials and creates/upgrades items

#### **Travel Log Integration**
Every crafted item adds narrative entries:
- **Light Side**: "Carefully crafted upgrade to improve my weapon."
- **Dark Side**: "Forged upgrade - my weapon grows deadlier!"
- **Balanced**: "Crafted upgrade for weapon."

### 4. **Equipment Slots System** ✅

**Equipment Display:**
```
=== EQUIPMENT ===
Main Hand: Vibroblade [1H]
Off Hand:  Riot Shield [offhand]
Armor:     None
```

**Hand Requirements:**
- **[1H]**: One-handed (pistols, blades, daggers)
- **[2H]**: Two-handed (rifles, staffs, pikes)
- **[Dual]**: Dual-wield special (dual lightsabers)

**Valid Combinations:**
1. **1H Weapon + Shield** → Defensive tank
2. **1H Weapon + 1H Weapon** → Dual-wield DPS
3. **1H Blaster + 1H Blade** → Ranged/melee hybrid
4. **2H Weapon + Nothing** → Heavy damage
5. **Dual Weapon + Nothing** → Berserker offense

### 5. **Material Spawning** ✅
**File**: `src/jedi_fugitive/game/level.py` (place_items function)

**Spawn Rates by Depth:**
- **Depth 1-1**: Common materials (30% chance per item)
- **Depth 2-3**: Common + Uncommon materials
- **Depth 4-5**: Common + Uncommon + Rare materials
- **Depth 6+**: All materials including Legendary (Kyber Crystal)

**Balance:**
- Food reduced to 8% (from 20%)
- Materials: 30% spawn chance
- Gold: 35%
- Potions: 12%

---

## 🎮 Keybindings

### New Commands:
- **C** = Open Crafting Bench (upgrade weapons, craft items)
- **e** = Equip item (now handles shields and offhand weapons)

### Existing Commands:
- **f** = Force abilities (or fire ranged weapon if no ability chosen)
- **F** = Fire ranged weapon directly
- **i** = Inventory
- **@** = Character sheet (shows offhand equipment)

---

## 💡 Gameplay Examples

### Example 1: Tank Build
```
1. Find Riot Shield in dungeon
2. Press 'e' → Equip Riot Shield
3. Result: +3 Defense, -1 Evasion
4. Can still use 1H weapon in main hand
```

### Example 2: Dual-Wielding
```
1. Equip Vibroblade in main hand (+5 Attack)
2. Find Combat Knife
3. Press 'e' → Equip Combat Knife in offhand
4. Result: +5 Attack (main) + 1 Attack (offhand 50%)
```

### Example 3: Crafting Upgrade
```
1. Collect materials: 2x Scrap Metal, 1x Durasteel Plate
2. Press 'C' to open Crafting Bench
3. Select "Sharpened Edge" [✓]
4. Equipped weapon gains +2 Attack
5. Travel log: "Forged Sharpened Edge - my weapon grows deadlier!"
```

### Example 4: Crafting Medkit
```
1. Collect: 1x Scrap Metal, 1x Fused Wire
2. Press 'C' → Craft "Medkit"
3. Materials consumed, medkit added to inventory
4. Use with 'u' to restore 30 HP
```

---

## 🔧 Technical Details

### Function Overview:

**equipment.py:**
- `equip_offhand(game, item)` - Equip shield or offhand weapon
- `unequip_offhand(game)` - Remove offhand equipment
- `open_crafting_menu(game)` - Show crafting recipes
- `craft_item(game, recipe_name)` - Execute crafting recipe

**crafting.py:**
- `check_materials(inventory, materials_needed)` - Verify materials
- `consume_materials(inventory, materials_needed)` - Remove used materials
- `get_recipe_by_name(name)` - Fetch recipe object

### Player Attributes:
- `player.equipped_weapon` - Main hand weapon
- `player.equipped_offhand` - Offhand weapon or shield
- `player.equipped_armor` - Body armor

---

## 🎨 Balance Considerations

**Shields:**
- Heavy shields (+5-8 Defense) reduce Evasion (-1 to -2)
- Light shields (+1-3 Defense) increase Evasion (+2 to +4)
- Trade-off: Block vs Dodge

**Dual-Wielding:**
- Offhand at 50% effectiveness prevents overpowered stacking
- Cannot use with 2H weapons (balance restriction)
- More attacks but no shield defense

**Crafting:**
- Materials found in dungeons (risk/reward)
- Higher depth = better materials
- Encourages exploration
- Progression system (upgrade weapons over time)

**Material Rarity:**
- Common: Depth 1+
- Uncommon: Depth 2+
- Rare: Depth 4+
- Legendary: Depth 6+

---

## 📊 Stats Impact

### Offensive Builds:
- **Dual-Wield**: +150% attack (main + 50% offhand)
- **Two-Handed**: +200% attack (2H weapons have higher base damage)
- **Crafted Upgrades**: +2 to +10 Attack per upgrade

### Defensive Builds:
- **Shield + 1H**: +3 to +8 Defense, still attack with main
- **Heavy Armor**: Body armor slot (separate)
- **Cortosis/Beskar**: Lightsaber resistance

### Hybrid Builds:
- **Pistol + Blade**: Range + melee flexibility
- **Shield + Ranged**: Defense while shooting
- **Balanced Stats**: Moderate attack + defense

---

## 🎯 Future Expansion Ideas

1. **Shield Bash** - Active ability to stun with shield
2. **Dual-Wield Combo Attacks** - Special moves when dual-wielding
3. **Crafting Specialization** - Weapon types (blaster mods vs blade sharpening)
4. **Material Harvesting** - Break down items for materials
5. **Legendary Crafting** - Unique named weapons with special abilities
6. **Set Bonuses** - Matching weapon/shield/armor sets
7. **Weapon Durability** - Items degrade, need repair with materials
8. **Advanced Recipes** - Multi-step crafting trees

---

## ✅ Testing Checklist

- [✅] Shields equip to offhand
- [✅] Offhand weapons equip with 50% bonus
- [✅] 2H weapons prevent offhand use
- [✅] Crafting menu displays recipes
- [✅] Materials spawn in dungeons
- [✅] Crafting consumes materials
- [✅] Weapon upgrades apply bonuses
- [✅] Travel log records crafting events
- [✅] Equipment display shows all slots
- [✅] Hand requirements display correctly

---

## 📝 Files Modified

1. **Created:**
   - `src/jedi_fugitive/items/shields.py` - Shield definitions
   - `src/jedi_fugitive/items/crafting.py` - Materials and recipes

2. **Modified:**
   - `src/jedi_fugitive/items/weapons.py` - Added HandRequirement enum
   - `src/jedi_fugitive/items/tokens.py` - Added material tokens
   - `src/jedi_fugitive/game/player.py` - Added equipped_offhand slot
   - `src/jedi_fugitive/game/equipment.py` - Added crafting and offhand functions
   - `src/jedi_fugitive/game/input_handler.py` - Added 'C' keybinding, updated help
   - `src/jedi_fugitive/game/level.py` - Added material spawning

---

## 🚀 Quick Start Guide

**For Players:**
1. Explore dungeons to find materials (m, M, w, P, etc.)
2. Press **C** to open Crafting Bench
3. Check which recipes you can craft [✓]
4. Select recipe to upgrade equipped weapon
5. Find shields ('s' token) and equip with **e**
6. Dual-wield by equipping second 1H weapon

**For Testing:**
1. Add materials to inventory manually
2. Test crafting with `craft_item(game, "Sharpened Edge")`
3. Verify offhand equipment with character sheet (@)
4. Check travel log (j) for crafting entries
