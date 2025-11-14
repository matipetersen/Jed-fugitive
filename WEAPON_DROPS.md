# Equipment Drop System

## Overview
Enemies now drop equipment when defeated! The system includes weapons, armor, and consumables with rarity tiers. Better enemies drop better equipment.

## Drop Mechanics

### Drop Rates by Enemy Type
- **Sith Troopers/Guards**: 30% base drop rate → Common equipment
- **Sith Acolytes/Warriors/Assassins**: 40% base drop rate → Common/Uncommon equipment
- **Sith Officers/Sorcerers**: 60% base drop rate → Uncommon/Rare equipment
- **Elite Enemies**: 60-90% drop rate → Rare/Epic equipment
- **Bosses**: 100% drop rate → Legendary/Rare equipment

Drop rates increase by 2% per enemy level, capped at 95%.

### Equipment Type Distribution
When an enemy drops equipment:
- **60% chance**: Weapon
- **25% chance**: Armor
- **15% chance**: Consumable

### Equipment Rarity Tiers

#### Weapons (22 total)

**Common** (6 weapons - 27%):
- DL-44 Blaster Pistol
- E-11 Blaster Rifle
- Electrostaff
- Ion Blaster
- Scatter Gun
- Training Saber

**Uncommon** (7 weapons - 32%):
- Heavy Blaster
- Crossbow
- Vibroblade
- Force Pike
- Vibro-Axe
- Slugthrower Rifle
- Sonic Rifle

**Rare** (6 weapons - 27%):
- Bowcaster
- Thermal Detonator
- Sith War Sword
- Cortosis Blade
- Disruptor Pistol
- Sith Lanvarok

**Legendary** (3 weapons - 14%):
- Single Lightsaber
- Dual Lightsaber
- Lightsaber Pike

#### Armor (4 total)

**Common**:
- Cloth Robes: +1 DEF, +5 EVA

**Uncommon**:
- Scout Vest: +2 DEF, +3 EVA, +5 HP

**Rare**:
- Stormtrooper Armor: +5 DEF, -2 EVA, +10 HP

**Epic**:
- Inquisitor Plate: +8 DEF, -4 EVA, +20 HP

#### Consumables (10 total)

**High Tier** (for elite/boss enemies):
- Small Medkit: Heals 10 HP
- Thermal Grenade: 12 area damage (3 tile radius)
- Nutrient Paste: Heals 12 HP
- Jedi Meditation Focus: -40 stress
- Emergency Ration: Heals 8 HP, -10 stress

**Mid Tier** (for officers/mid-enemies):
- Stimpack: Heals 5 HP, +1 speed for 6 turns
- Calming Tea: -25 stress
- Water Canteen: Heals 5 HP, -15 stress
- Emergency Ration: Heals 8 HP, -10 stress

**Low Tier** (for basic enemies):
- Water Canteen: Heals 5 HP, -15 stress
- Calming Tea: -25 stress

### Visual Indicators

When equipment drops, you'll see messages with rarity stars:
- ★★★ LEGENDARY/EPIC drops (three stars, all caps)
- ★★ RARE drops (two stars)
- ★ Uncommon drops (one star)
- Common drops (no stars)

### How Drops Work

1. **Enemy Defeated**: When you kill an enemy, the system checks if equipment drops
2. **Drop Roll**: Random check against drop rate (varies by enemy type)
3. **Equipment Type Roll**: 60% weapon, 25% armor, 15% consumable
4. **Rarity Roll**: Determines rarity based on enemy tier
5. **Equipment Placement**: Equipment appears on map as 'E' token at enemy's location
6. **Auto-Pickup**: Walk over the equipment to automatically pick it up

### Map Display
- Equipment drops appear as **'E'** on the map
- Walk over them to automatically add to inventory
- Pickup message shows item name, type, and rarity

## Drop Tables

### Basic Enemies (Troopers, Acolytes)
- 30-40% drop rate
- Equipment types: 60% weapons, 25% armor, 15% consumables
- Mostly Common equipment (90%+)
- Rare drop chance: 5-8%

### Mid-Tier (Warriors, Assassins, Officers)
- 40-60% drop rate  
- Equipment types: 60% weapons, 25% armor, 15% consumables
- Mix of Common (35%) and Uncommon (52%), some Rare
- Rare drop chance: 8-15%

### Elite (Sorcerers, Beasts)
- 60-90% drop rate
- Equipment types: 47% weapons, 42% armor, 11% consumables
- Rare (39%), Uncommon (23%), Epic (27%)
- Rare drop chance: 15-30%

### Bosses (Sith Lords, Inquisitors, Regent)
- 90-100% drop rate
- Equipment types: 55% weapons, 23% armor, 22% consumables
- Rare (47%), Epic (13%), Legendary (18%)
- Rare drop chance: 30-50%

## Example Drop Simulation (100 kills each)

**Sith Trooper** (Basic):
- Drops: ~30%
- Equipment: 40% weapons, 50% armor, 10% consumables
- 90% Common

**Sith Officer** (Mid-tier):
- Drops: ~58%
- Equipment: 60% weapons, 26% armor, 14% consumables
- 35% Common, 52% Uncommon, 13% Rare

**Sith Sorcerer** (Elite):
- Drops: ~62%
- Equipment: 47% weapons, 42% armor, 11% consumables
- 23% Uncommon, 39% Rare, 27% Epic, 11% Legendary

**Sith Lord** (Boss):
- Drops: 100%
- Equipment: 55% weapons, 23% armor, 22% consumables
- 47% Rare, 13% Epic, 18% Legendary

## Implementation Details

### Files Modified

1. **input_handler.py** (lines 1138-1290)
   - Enemy defeat detection
   - Drop rate calculation by enemy type
   - Equipment type selection (weapon/armor/consumable)
   - Equipment pool selection by rarity
   - Map token placement ('E')
   - Equipment data storage in `game.equipment_drops`

2. **game_manager.py** (lines 1175-1235)
   - Auto-pickup when walking over 'E' tokens
   - Equipment type handling (weapon/armor/consumable)
   - Inventory addition with proper attributes
   - Map cleanup (removes 'E' token)
   - Pickup messages with rarity indicators

### Data Structure

Equipment is stored in `game.equipment_drops` dictionary:
```python
game.equipment_drops = {
    (x, y): {
        'type': 'weapon',  # or 'armor', 'consumable'
        'item': item_object,
        'name': 'Item Name',
        'rarity': 'Legendary'
    }
}
```

When picked up, equipment is added to player inventory:

**Weapons:**
```python
{
    'name': 'Weapon Name',
    'type': 'weapon',
    'weapon_data': weapon_object,
    'rarity': 'Legendary'
}
```

**Armor:**
```python
{
    'name': 'Armor Name',
    'type': 'armor',
    'armor_data': armor_object,
    'rarity': 'Epic',
    'defense': 8,
    'evasion_mod': -4,
    'hp_bonus': 20,
    'slot': 'body'
}
```

**Consumables:**
```python
{
    'name': 'Item Name',
    'type': 'consumable',
    'id': 'medkit_small',
    'effect': {'heal': 10},
    'description': 'Heals 10 HP when used.'
}
```

## Testing

Run the test script to verify drop rates and rarity distribution:
```bash
python scripts/test_equipment_drops.py
```

This shows:
- Available equipment (weapons, armor, consumables)
- Equipment type distribution (60/25/15 split)
- Consumable tiers by enemy type
- Simulated drops from 100 kills per enemy type

For detailed weapon-only testing:
```bash
python scripts/test_weapon_drops.py
```
