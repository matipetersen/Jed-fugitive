# Weapon Classification System

## Hand Requirements

All weapons now have a **hand requirement** classification:

### **1H (One-Handed)**
Can be used with one hand, allowing dual-wielding or pairing with a shield:
- **Blades**: Vibrodagger, Combat Knife, Vibroblade, Electro-Sword, Sith Warblade, Techblade
- **Pistols**: DL-44 Blaster Pistol, Ion Blaster, Holdout Blaster, Disruptor Pistol, Sonic Blaster
- **Light Melee**: Riot Baton, Vibro-Knuckler, Training Saber, Single Lightsaber

**Advantages**: 
- Can equip offhand item (shield, second weapon)
- Faster attack speed
- Better mobility

### **2H (Two-Handed)**
Requires both hands, higher damage but can't use offhand:
- **Staffs/Pikes**: Electrostaff, Force Pike, Vibro-Lance, Lightsaber Pike
- **Heavy Weapons**: Vibro-Axe, Sith Tremor Sword
- **Rifles**: E-11 Blaster Rifle, Bowcaster

**Advantages**:
- Higher base damage
- Longer reach
- Better penetration

### **Dual (Dual-Wield)**
Paired weapons that take both hands but grant special bonuses:
- **Dual Lightsaber** (double-bladed)

**Advantages**:
- Highest damage output
- Multiple hit chances
- Aggressive stance bonuses

---

## Equipment Slots

```
Main Hand:    [Weapon Slot]
Off Hand:     [Shield/Weapon Slot] (if main hand is 1H)
Armor:        [Body Armor Slot]
```

### Combinations:
1. **1H Weapon + Shield** - Defensive tank build
2. **1H Weapon + 1H Weapon** - Dual-wield DPS (future feature)
3. **1H Blaster + 1H Blade** - Ranged/melee hybrid
4. **2H Weapon** - Heavy damage dealer
5. **Dual Weapon** - Berserker offense

---

## Blaster Targeting Fixed

### Keys:
- **'f' (lowercase)**: 
  - First tries Force abilities menu
  - If none chosen AND ranged weapon equipped → enters targeting mode
  - Shows reticle for aiming

- **'F' (uppercase)**: 
  - Direct weapon fire
  - Immediately enters targeting mode if ranged weapon equipped

### Targeting Mode:
- Arrow keys move reticle
- Enter to fire
- Esc to cancel
- Range depends on weapon (5-10 tiles)

---

## Future System Ideas

### 1. **Crafting System** 🔧
- Combine materials found in POIs
- Upgrade weapons (add mods, crystals)
- Craft consumables (medkits, grenades)
- Lightsaber customization (crystal colors, hilt styles)

### 2. **Companion System** 👥
- Recruit NPCs (droids, survivors, defectors)
- Each has unique abilities
- Can equip and level up
- Loyalty based on alignment choices

### 3. **Ship Upgrade System** 🚀
- Repair crashed ship over time
- Unlock new areas via flight
- Install shields, weapons, scanners
- Fuel/resource management

### 4. **Faction Reputation** ⚖️
- Track standing with Jedi remnants, Sith Empire, smugglers
- Unlock unique quests and items
- Affect enemy spawns and NPC interactions
- Trade and barter opportunities

### 5. **Skill Tree System** 🌳
- Separate trees for Light/Dark/Neutral
- Unlock advanced Force powers
- Passive bonuses (combat, survival, social)
- Specialization paths (Guardian, Consular, Sentinel)

### 6. **Environmental Hazards** 🌪️
- Sandstorms reduce visibility
- Radiation zones require protection
- Lava flows, toxic gas
- Weather affects combat and travel

### 7. **Stealth & Detection** 👁️
- Sneak past enemies
- Backstab bonuses
- Enemy alert states
- Line-of-sight mechanics

### 8. **Base Building** 🏠
- Convert crash site into base
- Build defenses against raids
- Resource generation
- Safe rest area with bonuses

### 9. **Quest System** 📜
- Main storyline progression
- Side quests from NPCs
- Dynamic events (distress signals, ambushes)
- Multiple endings based on choices

### 10. **Economy & Trading** 💰
- Merchants in settlements
- Buy/sell equipment
- Currency: Credits + rare materials
- Black market for illegal items

---

## Recommended Next Additions

**High Priority:**
1. ✅ Weapon hand classification (DONE)
2. ✅ Blaster targeting fix (DONE)
3. **Shield items** - Offhand defensive equipment
4. **Dual-wield mechanics** - Attack with both 1H weapons

**Medium Priority:**
5. **Crafting basics** - Combine items, upgrade weapons
6. **Companion system** - At least one recruitable NPC
7. **Skill trees** - Light/Dark specialization

**Low Priority:**
8. Environmental hazards
9. Stealth mechanics
10. Base building

---

## Current Weapon Stats Display

Equipment screen now shows:
```
[Weapon Name] (1H/2H/Dual)
Damage: X-Y
Attack: +Z
Accuracy: +A
Rarity: Common/Uncommon/Rare/Legendary
Special: [Abilities]
```

Example:
```
Single Lightsaber (1H)
Damage: 15-20
Attack: +12
Accuracy: +12
Rarity: Legendary
Special: Deflect Blasters, Ignores Armor, Force Focus
```
