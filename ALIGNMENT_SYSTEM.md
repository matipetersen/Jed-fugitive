# Alignment System - Complete Design Document

## 🎯 Core Concept

The alignment system tracks the player's moral choices through **Dark Corruption** (0-100), starting at **50 (Balanced)** and shifting based on actions.

### Alignment Ranges:
- **0-20**: Pure Light Side (Jedi)
- **21-40**: Light-Leaning (Guardian)
- **41-59**: Balanced (Gray Jedi)
- **60-79**: Dark-Leaning (Fallen)
- **80-100**: Pure Dark Side (Sith)

---

## ⚖️ Alignment Triggers

### **Dark Side Actions** (Increase Corruption)

| Action | Corruption Change | XP Type | Notes |
|--------|-------------------|---------|-------|
| **Absorb Artifact** | +15 | Dark XP +30-50 | Major corruption |
| **Absorb POI Energy (A key)** | +8 | Dark XP +10-18 | Moderate corruption |
| **Kill Neutral/Non-hostile** | +5 | Dark XP +10 | Murder penalty |
| **Execute Surrendered Enemy** | +10 | Dark XP +20 | Merciless |
| **Steal from Corpse** | +3 | - | Looting morality |
| **Use Dark Force Powers** | +2 per use | - | Force Lightning, Choke |
| **Torture for Info** | +12 | Dark XP +15 | Extreme cruelty |
| **Betray Ally** | +20 | Dark XP +30 | Ultimate betrayal |
| **Consume Innocent Life** | +15 | HP +20 | Life drain |

### **Light Side Actions** (Decrease Corruption)

| Action | Corruption Change | XP Type | Notes |
|--------|-------------------|---------|-------|
| **Destroy Artifact** | -10 | Light XP +30-50 | Major purification |
| **Destroy POI (D key)** | -5 | Light XP +15-25 | Cleansing evil |
| **Spare Defeated Enemy** | -8 | Light XP +15 | Mercy |
| **Heal Others** | -3 | Light XP +5 | Compassion |
| **Protect Innocent** | -5 | Light XP +10 | Selfless |
| **Use Light Force Powers** | -2 per use | - | Heal, Protect |
| **Meditate** | -1 | Stress -10 | Mindfulness |
| **Free Prisoners** | -10 | Light XP +20 | Liberation |
| **Share Resources** | -4 | - | Generosity |

### **Neutral Actions** (No Change)

- Combat with hostile enemies
- Self-defense
- Exploring
- Crafting
- Trading
- Picking up items (except gold from corpses)
- Using consumables

---

## 📊 Current Implementation Status

### ✅ **Currently Implemented:**
1. Artifact Absorb (+15 corruption) / Destroy (-10 corruption)
2. POI Absorb ('A' key, +8 corruption) / Destroy ('D' key, -5 corruption)
3. Dark corruption starts at **0** (should be 50)
4. Alignment thresholds: 60+ = Dark, 30- = Light

### ❌ **Missing Implementations:**
1. Corruption from combat actions (spare/execute)
2. Corruption from Force power usage
3. Corruption from moral choices (steal, betray, torture)
4. **Starting corruption at 50 (Balanced)**
5. More granular alignment ranges

---

## 🔧 Required Changes

### 1. **Change Starting Corruption**
**File**: `player.py` line 34
```python
# OLD:
self.dark_corruption = 0  # 0-100 scale, increases with artifact use

# NEW:
self.dark_corruption = 50  # 0-100 scale, starts Balanced
```

### 2. **Update Alignment Ranges**
**File**: `player.py` get_alignment() function
```python
# OLD:
if corruption >= 60:
    return 'dark'
elif corruption <= 30:
    return 'light'
else:
    return 'balanced'

# NEW:
if corruption >= 80:
    return 'pure_dark'    # 80-100: Sith
elif corruption >= 60:
    return 'dark'         # 60-79: Fallen
elif corruption >= 41:
    return 'balanced'     # 41-59: Gray Jedi
elif corruption >= 21:
    return 'light'        # 21-40: Guardian
else:
    return 'pure_light'   # 0-20: Jedi Master
```

### 3. **Add Combat Morality**
**New System**: Enemy surrender chance based on low HP

When enemy HP < 20%:
- Enemy may surrender (shows message)
- Player choice:
  - Attack = Execute (+10 corruption, +20 Dark XP)
  - Walk away = Spare (-8 corruption, +15 Light XP)

### 4. **Track Force Power Usage**
**File**: `force_abilities.py`

Add corruption modifiers:
- Dark Powers (Lightning, Choke, Drain): +2 corruption per use
- Light Powers (Heal, Protect, Meditation): -2 corruption per use
- Neutral Powers (Push/Pull, Jump): No change

### 5. **Add Looting Morality**
**File**: `equipment.py` pick_up()

Check if gold is on enemy corpse:
- If yes: +3 corruption ("Looted corpse")
- If no: No change

### 6. **Update UI Corruption Display**
Show more detailed alignment status:
```
Corruption: 65/100 [Dark-Leaning]
Light XP: 120 | Dark XP: 180
```

---

## 🎮 Gameplay Impact

### **Alignment-Based Mechanics**

#### **Force Power Costs**
- **Pure Light (0-20)**: Light powers -20% cost, Dark powers +50% cost
- **Light (21-40)**: Light powers -10% cost, Dark powers +20% cost
- **Balanced (41-59)**: All powers normal cost
- **Dark (60-79)**: Dark powers -10% cost, Light powers +20% cost
- **Pure Dark (80-100)**: Dark powers -20% cost, Light powers +50% cost

#### **Story Branches**
- **Pure Light**: Jedi ending, restore order
- **Light**: Become teacher, train new Jedi
- **Balanced**: Gray Jedi, walk your own path
- **Dark**: Sith apprentice, seek power
- **Pure Dark**: Sith Lord, rule through fear

#### **NPC Reactions**
- Light Side: NPCs trust you, offer help
- Balanced: Neutral reactions
- Dark Side: NPCs fear you, may flee or attack

#### **Equipment Restrictions**
- Some items require alignment:
  - Jedi Guardian Shield: Corruption < 40
  - Sith Battle Shield: Corruption > 60
  - Balanced items: Always available

---

## 📈 Example Playthrough Tracking

### **Light Side Playthrough**
```
Start: 50 corruption (Balanced)
Destroy Artifact: 40 (Light-Leaning)
Destroy POI: 35 (Light-Leaning)
Spare Enemy: 27 (Light)
Heal Others: 24 (Light)
Meditate: 23 (Light)
Destroy Artifact: 13 (Pure Light)
```

### **Dark Side Playthrough**
```
Start: 50 corruption (Balanced)
Absorb Artifact: 65 (Dark-Leaning)
Absorb POI: 73 (Dark-Leaning)
Execute Enemy: 83 (Pure Dark)
Use Force Lightning: 85 (Pure Dark)
Betray Ally: 100 (Maximum Dark)
```

### **Balanced Playthrough**
```
Start: 50 corruption (Balanced)
Destroy Artifact: 40 (Light-Leaning)
Absorb Artifact: 55 (Balanced)
Spare Enemy: 47 (Balanced)
Use Force Push: 47 (Balanced - neutral power)
Meditate: 46 (Balanced)
Absorb POI: 54 (Balanced)
```

---

## 🔄 Dynamic Feedback

### **Messages on Alignment Shift**

When crossing thresholds, show narrative:

**Crossing into Pure Light (50 → 20):**
> "You feel the Force flowing through you with clarity and peace. The path of the Jedi calls to you."

**Crossing into Pure Dark (50 → 80):**
> "Dark power surges through your veins. You hunger for more. The Sith way beckons."

**Returning to Balanced (30 → 50):**
> "You find balance within yourself. Neither light nor dark, you walk your own path."

### **Visual Indicators**
- Corruption bar with color gradient
- Character icon changes (blue → gray → red)
- Force power colors shift

---

## 🛠️ Implementation Priority

### **Phase 1** (Immediate):
1. ✅ Change starting corruption to 50
2. ✅ Update alignment ranges (5 tiers)
3. ✅ Adjust POI corruption values
4. ✅ Update artifact corruption values

### **Phase 2** (Next):
5. Add enemy surrender mechanic
6. Add Force power corruption tracking
7. Add looting morality system
8. Update UI with detailed corruption display

### **Phase 3** (Future):
9. Alignment-based Force power costs
10. NPC reaction system
11. Equipment alignment restrictions
12. Multiple endings based on final corruption

---

## 📝 Balance Notes

- **Corruption changes should be meaningful but reversible**
- Average playthrough: 15-20 artifacts, 30-40 POIs
- Pure paths require consistent choices (80%+ same alignment)
- Balanced path is easiest but offers no specialization bonuses
- Dark path: Higher damage, lower defense
- Light path: Higher defense, lower damage
- Balanced path: Middle ground, flexibility

---

## 🎯 Summary

The alignment system creates **meaningful moral choices** where:
1. Players start **Balanced** (50 corruption)
2. Actions push them toward **Light** or **Dark**
3. Extreme paths (Pure Light/Dark) require **commitment**
4. Changing paths is possible but requires **effort**
5. Alignment affects **gameplay mechanics**, **story**, and **abilities**
6. Every choice **matters** and has **consequences**
