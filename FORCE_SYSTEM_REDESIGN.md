# Force Ability System Redesign

## Current Problems
1. **Limited Force Points** - Players run out too quickly, making abilities feel weak
2. **Binary Light/Dark** - Abilities aren't meaningfully tied to alignment progression
3. **Passive Unlocking** - No meaningful choices in ability progression
4. **Flat Scaling** - Abilities don't grow stronger with player level/alignment
5. **No Risk/Reward** - Using dark powers has no meaningful consequences beyond stress

## Proposed System: **Force Attunement & Mastery**

### Core Concept
Force abilities scale with **alignment mastery** - the deeper you go into Light or Dark, the more powerful your aligned abilities become, but misaligned abilities become more costly or ineffective.

---

## 1. Force Regeneration System

**Replace limited Force Points with regenerating Force Energy:**

```
Force Energy: 100 (max)
Regeneration: +20 per turn (out of combat), +5 per turn (in combat)
```

**Benefits:**
- Players can use abilities more freely without feeling punished
- Encourages strategic ability usage timing
- Combat becomes more dynamic with resource management

---

## 2. Alignment Mastery Tiers

Each alignment tier unlocks and enhances different abilities:

### **Pure Light (0-20 Corruption)**
**Mastery Level: 3**
- Heal: 15 HP (up from 8), -1 Force cost
- Protect: +5 defense for 5 turns (NEW)
- Meditation: Restore 20 Force, -15 stress (NEW)
- Mind Trick: Confuse enemy for 3 turns (NEW)

### **Light (21-40 Corruption)**
**Mastery Level: 2**
- Heal: 12 HP, normal cost
- Protect: +3 defense for 4 turns
- Reveal: +6 LOS for 10 turns

### **Balanced (41-59 Corruption)**
**Mastery Level: 1**
- Push/Pull: 4 tiles range
- Reveal: +4 LOS for 8 turns
- Basic Heal: 8 HP
- Basic Lightning: 8 damage

### **Dark (60-79 Corruption)**
**Mastery Level: 2**
- Lightning: 15 damage (up from 10), -1 Force cost
- Force Choke: 12 damage + stun 1 turn (NEW)
- Drain Life: Steal 10 HP from enemy (NEW)
- Fear: Enemies flee for 3 turns (NEW)

### **Pure Dark (80-100 Corruption)**
**Mastery Level: 3**
- Lightning Storm: 20 damage to 3x3 area (NEW)
- Death Field: AOE drain, 8 damage + heal 15 (NEW)
- Force Rage: +10 attack for 5 turns (NEW)
- Dark Vision: See through walls for 10 turns (NEW)

---

## 3. Cross-Alignment Penalties

Using abilities misaligned with your path has consequences:

### Light Side using Dark Powers
- **2x Force cost**
- **+15 stress** on use
- **+5 corruption** per use
- Chance to **fail** (10% per mastery level difference)

### Dark Side using Light Powers
- **2x Force cost**
- **50% effectiveness**
- Slowly **reduces corruption** (-3 per use - path to redemption!)

### Balanced Path
- Can use both sides freely
- No mastery bonuses
- Abilities at base power
- Path of flexibility but no specialization

---

## 4. Force Mastery Progression

### Experience System
- Using aligned abilities grants **Mastery XP**
- Each mastery level requires: `100 * level` XP
- Mastery levels unlock **enhanced versions** of abilities

### Example Progression (Lightning)
```
Level 1: 10 damage, 15 Force cost, 10m range
Level 2: 15 damage, 12 Force cost, 12m range, chains to 1 nearby enemy
Level 3: 20 damage, 10 Force cost, 15m range, chains to 2 enemies, -10% enemy evasion
```

---

## 5. Ability Trees

### Light Side Tree
```
         [Mind Trick]
              |
         [Heal] ──┬── [Battle Meditation] (party buff)
                  │
              [Protect] ── [Force Barrier] (absorb damage)
                  │
         [Meditation] ── [Force Harmony] (full heal + cleanse)
```

### Dark Side Tree
```
         [Force Choke]
              |
         [Lightning] ──┬── [Lightning Storm] (AOE)
                       │
              [Drain] ── [Death Field] (AOE drain)
                       │
         [Fear] ──────── [Force Scream] (mass fear + damage)
```

### Universal Tree
```
[Push/Pull] ── [Force Blast] (knockback + damage)
     |
[Reveal] ──── [Force Sense] (detect enemies/traps)
     |
[Jump] ──────── [Force Speed] (extra movement)
```

---

## 6. Ability Customization

Players can **upgrade** abilities with found/crafted **Force Crystals**:

### Crystal Types
- **Adegan Crystal** - Reduces Force cost by 20%
- **Kyber Crystal** - +50% damage/healing
- **Meditation Crystal** - +10 Force regen per turn
- **Focus Crystal** - -50% stress from Dark powers
- **Corrupted Crystal** - Dark powers ignore armor

### Installation
- Each ability has 2 crystal slots
- Crystals can be swapped (not destroyed)
- Found in tombs, crafted with rare materials

---

## 7. Situational Abilities

Add **context-aware** abilities that trigger based on state:

### Environmental
- **Force Jump** - Leap over chasms/obstacles (costs 10 Force)
- **Force Breath** - Survive toxic gas/underwater (5 Force/turn)
- **Wall Run** - Move through difficult terrain freely (8 Force)

### Combat State
- **Desperate Power** - When HP < 30%, abilities cost 50% less
- **Sith Fury** - When corrupt > 80, gain +2 Force per kill
- **Jedi Serenity** - When corrupt < 20, reduce all damage by 20%

---

## 8. Cooldown System (Alternative)

Instead of Force cost, some powerful abilities have **cooldowns**:

```
Lightning Storm: 20 damage AOE, 0 Force cost, 10 turn cooldown
Force Barrier: Absorb 30 damage, 0 Force cost, 15 turn cooldown
Death Field: 15 damage + 15 heal AOE, 0 Force cost, 12 turn cooldown
```

**Benefits:**
- Powerful abilities feel impactful
- Encourages diverse ability usage
- No "spamming" one strong ability

---

## 9. Combo System

Abilities can **chain together** for bonus effects:

### Light Combos
- **Heal → Protect** = +2 defense for 8 turns (instead of 5)
- **Reveal → Mind Trick** = Affect all visible enemies
- **Meditation → Heal** = Heal 2x amount

### Dark Combos
- **Lightning → Choke** = Stun for 2 turns (instead of 1)
- **Fear → Lightning** = +50% damage to feared enemies
- **Drain → Lightning** = Chain to 3 enemies (instead of 1)

---

## 10. Implementation Priority

### Phase 1 (Core)
1. ✅ Force Energy regeneration system
2. ✅ Alignment mastery scaling
3. ✅ Cross-alignment penalties
4. ✅ New Light/Dark abilities (4 each)

### Phase 2 (Enhancement)
5. Force Mastery XP progression
6. Ability trees with prerequisites
7. Visual feedback for Force usage (particles, screen effects)

### Phase 3 (Polish)
8. Force Crystal customization
9. Combo system
10. Environmental abilities
11. Situational passives

---

## Code Structure

```python
class ForceAbility:
    name: str
    base_cost: int
    alignment: str  # "light", "dark", "neutral"
    mastery_level: int  # 0-3
    cooldown: int = 0
    current_cooldown: int = 0
    
    def get_actual_cost(self, player):
        """Calculate cost with alignment penalties/bonuses"""
        pass
    
    def can_use(self, player):
        """Check if player can use this ability"""
        pass
    
    def use(self, player, target, game):
        """Execute ability with all bonuses/penalties"""
        pass
    
    def get_power_scale(self, player):
        """Calculate power based on alignment mastery"""
        pass
```

---

## User Experience

### In-Game Feedback
- **Force Bar**: Visual meter showing current/max Force Energy
- **Ability Icons**: Show cooldown timers, mastery level, alignment color
- **Combat Log**: "Lightning (Mastery 2) dealt 15 damage! (+5 from dark mastery)"
- **Alignment Shift**: "Your dark powers grow stronger... [Dark Mastery: Level 3]"

### Discoverability
- **Ability Book**: Press 'B' to view all abilities, requirements, upgrades
- **Mastery Progress**: See XP toward next level for each ability
- **Crystal Slots**: Visual indicator of installed crystals and effects

---

## Summary

This redesign makes Force abilities:
1. **More accessible** - Regenerating resource instead of scarce points
2. **Meaningful choices** - Alignment affects power, creating build diversity
3. **Progressive** - Abilities grow with you through mastery
4. **Strategic** - Combos, cooldowns, and situational effects
5. **Immersive** - Alignment actually matters mechanically

The system rewards specialization while allowing flexibility, and ties directly into the existing corruption/alignment mechanics.
