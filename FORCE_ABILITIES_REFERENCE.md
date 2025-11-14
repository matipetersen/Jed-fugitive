# Phase 1 Force Abilities Quick Reference

## Force Energy System
- **Total Capacity:** 100 Force Energy
- **Regeneration (Peaceful):** +20 per turn
- **Regeneration (Combat):** +5 per turn
- **UI Display:** Force bar shows [████████░░░░] Current/Max

## Alignment Mastery Tiers

| Corruption | Alignment   | Mastery | Light Power | Dark Power | Light Cost | Dark Cost |
|-----------|-------------|---------|-------------|------------|------------|-----------|
| 0-20      | Pure Light  | 3       | 1.45x       | 0.5x       | 0.70x      | 2.0x      |
| 21-40     | Light       | 2       | 1.30x       | 0.5x       | 0.80x      | 2.0x      |
| 41-59     | Balanced    | 1       | 1.00x       | 1.0x       | 1.00x      | 1.0x      |
| 60-79     | Dark        | 2       | 0.5x        | 1.30x      | 2.0x       | 0.80x     |
| 80-100    | Pure Dark   | 3       | 0.5x        | 1.45x      | 2.0x       | 0.70x     |

## Light Side Abilities

### Force Protect
- **Cost:** 15 Force (12 at Pure Light)
- **Effect:** +3-5 defense for 4-5 turns
- **Target:** Self
- **Side Effect:** -5 stress
- **Best At:** Pure Light (21 defense at mastery 3)

### Force Meditation
- **Cost:** 0 Force (free)
- **Effect:** Restore 20 Force, reduce 15 stress
- **Target:** Self
- **Restriction:** Cannot use in combat
- **Best At:** Pure Light (29 Force + 21 stress at mastery 3)
- **Use Case:** Resource recovery between fights

## Dark Side Abilities

### Force Choke
- **Cost:** 20 Force (14 at Pure Dark)
- **Effect:** 12 damage + stun for 1 turn
- **Target:** Single enemy
- **Side Effect:** +10 stress
- **Best At:** Pure Dark (17 damage at mastery 3)
- **Use Case:** Crowd control, disable dangerous enemies

### Force Drain
- **Cost:** 18 Force (13 at Pure Dark)
- **Effect:** 10 damage to enemy, heal self for same amount
- **Target:** Single enemy
- **Side Effect:** +8 stress
- **Best At:** Pure Dark (14 damage/heal at mastery 3)
- **Use Case:** Sustain in long battles

### Force Fear
- **Cost:** 25 Force (18 at Pure Dark)
- **Effect:** All visible enemies flee for 3 turns
- **Target:** Area effect
- **Side Effect:** +15 stress
- **Best At:** Pure Dark (powerful area control)
- **Use Case:** Escape, reposition, break enemy formations

## Legacy Abilities (Still Available)

### Force Push/Pull
- **Cost:** 1 Force
- **Effect:** Move enemy up to 3 tiles
- **Alignment:** Neutral
- **Note:** No mastery scaling

### Force Reveal
- **Cost:** 2 Force
- **Effect:** Reveal hidden areas
- **Alignment:** Light
- **Note:** Benefits from Light mastery

### Force Heal
- **Cost:** 3 Force
- **Effect:** Restore HP
- **Alignment:** Light
- **Note:** Benefits from Light mastery

### Force Lightning
- **Cost:** 4 Force
- **Effect:** Damage single enemy
- **Alignment:** Dark
- **Note:** Benefits from Dark mastery, adds stress

## Strategy Tips

### Pure Light Build (Corruption 0-20)
- **Strengths:** Cheap defensive abilities, free meditation
- **Best Combo:** Protect → Fight → Meditate → Repeat
- **Weakness:** Dark abilities cost double (avoid)

### Balanced Build (Corruption 41-59)
- **Strengths:** Flexibility, can use any ability
- **Best Use:** Adapt to situation, no penalties
- **Weakness:** No mastery bonuses

### Pure Dark Build (Corruption 80-100)
- **Strengths:** Powerful offensive abilities, life steal
- **Best Combo:** Drain → Choke → Fear (escape)
- **Weakness:** Light abilities cost double (avoid), stress management critical

## Combat Flow Examples

### Defensive Light Side Flow
1. Enter combat with 100 Force
2. Use Protect (15 Force) → 85 Force, +5 defense
3. Fight for 4 turns → Regen 20 Force (4 × 5 combat regen)
4. Defeat enemies, exit combat → 105 Force
5. Meditate (0 Force) → 100 Force (cap), -15 stress
6. Ready for next fight at full Force

### Aggressive Dark Side Flow
1. Enter combat with 100 Force
2. Use Choke on strongest enemy (20 Force) → 80 Force, enemy stunned
3. Use Drain on wounded enemy (18 Force) → 62 Force, +10 HP
4. Fight normally → Regen 15 Force (3 turns × 5)
5. Use Fear if overwhelmed (25 Force) → 52 Force, all enemies flee
6. Meditation unavailable (Dark), must wait for passive regen

## Movement Improvements

### Diagonal Movement (3 Methods)
- **Vi keys:** y (↖), u (↗), b (↙), n (↘)
- **Numpad:** 7 (↖), 9 (↗), 1 (↙), 3 (↘)
- **Arrow keys:** Combine arrow keys for diagonals

## Force Energy Management

### When to Use Abilities
- **Full Force (100):** Use expensive abilities (Fear, Choke)
- **Medium Force (50-99):** Use medium abilities (Protect, Drain)
- **Low Force (<50):** Conserve, use cheap abilities (Push/Pull)
- **Very Low (<20):** Avoid combat, meditate if possible

### Regeneration Optimization
- **In Combat:** +5/turn = 20 turns to full from empty
- **Out of Combat:** +20/turn = 5 turns to full from empty
- **Strategy:** End fights quickly to maximize regen rate

### Meditation Strategy (Light Side)
- Use after every 2-3 combats
- Best when Force <80 and stress >30
- Cannot use during combat (plan ahead)
- Free resource recovery (no Force cost)

## Cross-Alignment Penalties

### Using Opposing Abilities
- **Cost:** 2x Force (expensive!)
- **Power:** 0.5x effectiveness (weak!)
- **Stress:** Additional stress penalties
- **Fail Chance:** 10% per mastery level

### When It's Worth It
- Emergency situations only
- Critical utility (Heal when Dark, Fear when Light)
- You have excess Force to spare
- Better than dying

### When to Avoid
- Regular combat (too expensive)
- Low Force situations
- When aligned abilities available
- Building towards mastery

---

**Note:** This is Phase 1 implementation. Phase 2 will add mastery XP progression, ability trees, and more advanced abilities. Phase 3 will add Force Crystals, combos, and environmental abilities.
