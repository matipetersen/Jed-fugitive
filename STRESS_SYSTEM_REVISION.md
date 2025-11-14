# Stress System Revision

## Problem Analysis

The original stress system had several issues:

1. **Too Fast Accumulation**: Stress rose every single turn in combat (+2/turn), reaching critical levels in just 12-15 turns
2. **Low HP Punishment**: When HP dropped below 25%, players gained +5 stress every turn, compounding stress problems
3. **No Relief from Victory**: Defeating enemies provided no stress reduction
4. **Limited Recovery**: Stress only reduced through rare consumables or level ups
5. **Exploration Pressure**: No passive stress reduction when safe

### Old System Performance
- Level 1, 15-turn combat: **60 stress** (Tier 2 - Medium)
- Level 1 with low HP: **Critical stress in 12 turns**
- Combat stress alone: +30 in 15 turns
- No reward for defeating enemies

## Revised System Changes

### 1. Reduced Stress Accumulation (50-75% reduction)

**Being Hunted:**
- Old: +5 stress every turn
- New: +3 stress every 2nd turn
- Impact: 70% less stress

**Combat:**
- Old: +2 stress every turn
- New: +1-3 stress every 3rd turn (scaled by nearby enemy count)
- Impact: 67% less stress

**Low HP (<25%):**
- Old: +5 stress every turn
- New: +3 stress every 4th turn
- Impact: 75% less stress

**Critical HP (<10%):**
- New: +4 stress every 3rd turn (replaces low HP stress)
- Impact: Still challenging but not overwhelming

**Surrounded (3+ adjacent enemies):**
- Old: +20 stress (one-time)
- New: +15 stress (one-time)
- Impact: 25% reduction

### 2. NEW: Combat Victory Relief

Defeating enemies now provides stress reduction:
- Normal enemy: **-2 stress**
- Tough enemy (level 3+): **-4 stress**
- Boss enemy: **-8 stress**

Makes combat rewarding instead of purely stressful!

### 3. NEW: Passive Stress Recovery

When safe (no enemies within 8 tiles):
- **-1 stress every 5 turns**
- Encourages exploration and tactical retreats
- Message every 20 turns: "You feel calmer in the safety of distance"

### 4. Improved Ability Recovery

**Force Abilities:**
- Old: -5 stress reduction
- New: -10 stress reduction
- Impact: 100% more effective

Makes Force abilities a meaningful stress management tool.

### 5. Better Level Up Relief

**Level Up:**
- Old: Complete stress reset to 0
- New: -30 stress reduction (not full reset)
- Shows feedback: "Level up relieves stress! (80 → 50)"
- Impact: Still meaningful but not trivializing

### 6. Stress Mitigation Still Works

The existing mitigation system remains:
- **Per-level resilience**: 3% per level (level - 1)
- **Equipment mitigation**: Up to 60% max
  - Cloth Robes: 30%
  - Kyber weapons: 15%
  - Scout Vest: 10%

## Performance Comparison

### Example 1: Level 1, 15-turn Combat
| Metric | Old System | New System | Improvement |
|--------|-----------|------------|-------------|
| Combat stress | +30 | +5 | **83% less** |
| Low HP stress (6 turns) | +30 | +3 | **90% less** |
| Victory relief | 0 | -4 | **NEW** |
| **Total stress** | **60** | **4** | **93% less!** |

### Example 2: Level 5 with Cloth Robes
| Metric | Old System | New System | Improvement |
|--------|-----------|------------|-------------|
| 15-turn combat | +17 | +3 | **82% less** |
| Low HP (6 turns) | +17 | +2 | **88% less** |
| Victory relief | 0 | -4 | **NEW** |
| **Total stress** | **34** | **1** | **97% less!** |

### Turns to Critical Stress (85+)

| Scenario | Old System | New System | Improvement |
|----------|-----------|------------|-------------|
| Level 1, combat only | 42 turns | 85+ turns | **2x longer** |
| Level 1, combat + low HP | 12 turns | 21+ turns | **75% longer** |
| Level 5, with gear | 21 turns | 42+ turns | **2x longer** |
| Level 10, full gear | 42 turns | Never | **Stress-free!** |

## Implementation Details

### Modified Files

**game_manager.py** (~60 lines modified):
- `_tick_effects()`: Reduced being hunted stress (+5→+3), every 2nd turn
- Combat stress: Every 3rd turn, scaled by enemy count (+1-3)
- Low HP stress: Every 4th turn (+3), critical HP every 3rd turn (+4)
- Surrounded stress: Reduced +20→+15
- **NEW**: Passive recovery (-1 stress every 5 turns when safe)

**input_handler.py** (~15 lines added):
- `perform_player_attack()`: Added victory stress relief
  - Normal kill: -2 stress
  - Tough enemy (level 3+): -4 stress
  - Boss: -8 stress

**player.py** (~10 lines modified):
- `gain_xp()`: Changed level up from full reset to -30 stress
- Added feedback message showing stress change

**force_abilities.py** (~6 lines modified):
- Force Reveal: -5→-10 stress reduction
- Force Heal: -5→-10 stress reduction

## Testing

Run the test scripts to see the improvements:

```bash
# Original system analysis
python scripts/analyze_stress_system.py

# Revised system comparison
python scripts/test_revised_stress.py
```

## Summary of Benefits

1. **Stress rises 50-75% slower** - More time to manage and strategize
2. **Victory provides relief** - Combat has positive payoff
3. **Safe exploration naturally reduces stress** - Encourages tactical play
4. **Force abilities more effective** - Better stress management tools
5. **Level ups still meaningful** - But not trivializing the mechanic
6. **Better progression curve** - Low-level players aren't overwhelmed

The stress system is now a **challenge to manage** rather than an **inevitable spiral to failure**.
