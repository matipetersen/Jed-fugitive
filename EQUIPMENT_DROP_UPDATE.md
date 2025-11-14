# Equipment Drop System Update

## Summary

Expanded the drop system from weapons-only to **full equipment drops** including weapons, armor, and consumables.

## What Changed

### Previous System (Weapons Only)
- Enemies dropped only weapons
- Map token: 'w'
- Storage: `game.weapon_drops`

### New System (All Equipment)
- Enemies drop **weapons (60%)**, **armor (25%)**, and **consumables (15%)**
- Map token: 'E' (Equipment)
- Storage: `game.equipment_drops`

## Equipment Available

### Weapons (22 total)
- Common (6): DL-44 Blaster, E-11 Rifle, Electrostaff, etc.
- Uncommon (7): Heavy Blaster, Vibroblade, Force Pike, etc.
- Rare (6): Bowcaster, Cortosis Blade, Disruptor, etc.
- Legendary (3): Lightsabers (Single/Dual/Pike)

### Armor (4 total)
- **Cloth Robes** (Common): +1 DEF, +5 EVA
- **Scout Vest** (Uncommon): +2 DEF, +3 EVA, +5 HP
- **Stormtrooper Armor** (Rare): +5 DEF, -2 EVA, +10 HP
- **Inquisitor Plate** (Epic): +8 DEF, -4 EVA, +20 HP

### Consumables (10 total)
- **Healing**: Medkit (+10 HP), Stimpack (+5 HP), Ration (+8 HP), etc.
- **Stress Relief**: Meditation Focus (-40), Calming Tea (-25), etc.
- **Combat**: Thermal Grenade (12 area damage)
- **Utility**: Compass (tomb finder)

## Drop Mechanics

### Drop Chances by Enemy
| Enemy Type | Drop Rate | Equipment Tier |
|------------|-----------|----------------|
| Trooper/Guard | 30% | Common |
| Acolyte/Warrior/Assassin | 40% | Common/Uncommon |
| Officer/Sorcerer | 60% | Uncommon/Rare |
| Elite/Beasts | 60-90% | Rare/Epic |
| Bosses | 100% | Epic/Legendary |

### Equipment Type Distribution
- 60% Weapons
- 25% Armor
- 15% Consumables

## Implementation

### Modified Files

**input_handler.py** (~150 lines added):
- Imports armor and consumables
- Equipment type selection logic
- Separate pools for weapons, armor, consumables
- Tier-based consumable distribution
- Changed token from 'w' to 'E'
- Changed storage from `weapon_drops` to `equipment_drops`

**game_manager.py** (~30 lines modified):
- Equipment type detection on pickup
- Type-specific inventory item creation
- Armor includes defense/evasion/hp_bonus/slot
- Consumables include id/effect/description
- Changed token from 'w' to 'E'

### Testing

Created comprehensive test: `scripts/test_equipment_drops.py`

Test results (100 kills per enemy type):
```
Sith Trooper:
- 30% drop rate
- 40% weapons, 50% armor, 10% consumables
- 90% Common

Sith Officer:
- 58% drop rate
- 60% weapons, 26% armor, 14% consumables
- 35% Common, 52% Uncommon

Sith Sorcerer:
- 62% drop rate
- 47% weapons, 42% armor, 11% consumables
- 23% Uncommon, 39% Rare, 27% Epic

Sith Lord:
- 100% drop rate
- 55% weapons, 23% armor, 22% consumables
- 47% Rare, 13% Epic, 18% Legendary
```

## Benefits

1. **More Variety**: Players get different types of rewards
2. **Better Balance**: Can now find armor and healing items from combat
3. **Strategic Choices**: Decide between offense (weapons) and defense (armor)
4. **Consumable Economy**: Healing and utility items now drop naturally
5. **Rarity Excitement**: All equipment types have rare drops to discover

## Backward Compatibility

⚠️ **Breaking Change**: 
- Old saves using `game.weapon_drops` will not have these drops
- Map token changed from 'w' to 'E'
- Pickup logic now requires type detection

Existing weapons in inventory are unaffected.
