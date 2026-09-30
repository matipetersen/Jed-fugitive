# Faction Combat System Implementation

## Overview
Implemented a comprehensive faction-based combat system where enemies are color-coded by faction and engage in inter-faction warfare based on their relationships.

## Changes Made

### 1. Faction Relationship System (factions.py)
- **Added inter-faction relationships** (-100 hostile to 100 allied):
  - Sith Empire vs Republic: -80 (mortal enemies)
  - Republic vs Settlers: +40 (protective)
  - Hutt vs Mandalorian: +20 (mercenary contracts)
  - And more...
  
- **Added helper methods**:
  - `are_factions_hostile(faction_a, faction_b)`: Check if two factions are hostile
  - `is_player_hostile_to_faction(faction_name)`: Check player's standing
  - `is_player_friendly_to_faction(faction_name)`: Check friendly reputation

### 2. Enemy Faction Assignments (enemies_sith.py, diverse_enemies.py)
- **All Sith enemies** assigned to 'Sith Empire' faction with red color (1)
  - Sith Acolyte, Warrior, Assassin, Sorcerer
  - Sith Trooper, Officer, Lord, Inquisitor
  - Sith WarDroid, Tuk'ata, Terentatek
  - Obsidian Regent, Dread Inquisitor
  
- **Jedi Master** assigned to 'Republic' faction with blue color (4)

- **Diverse enemies** (diverse_enemies.py) assigned to Sith Empire:
  - Sith Marksman, Berserker, Assassin
  - Sith Trooper, Scout, Guardian
  - Dark Acolyte

- **Massive creatures** remain neutral (no faction) as they are wild beasts

### 3. Visual Color Coding (ui_renderer.py)
- **Modified enemy rendering** to use `enemy.color` attribute
- Enemies now display in their faction colors:
  - Red (1): Sith Empire
  - Blue (4): Republic
  - Cyan (6): Hutt Cartel
  - Yellow (3): Settlers
  - White (7): Mandalorian
  - Red (default): Unfactioned enemies

### 4. Enemy AI Targeting System (enemy.py)
- **Added `find_enemy_target()` function**:
  - Checks enemy's faction
  - Evaluates player reputation with that faction
  - Finds nearest hostile faction enemies
  - Returns best target (player or hostile enemy)

- **Priority System**:
  1. If player is friendly (rep > 20): Only target hostile faction enemies
  2. If player is hostile (rep < -20): Target closest hostile (player or enemy)
  3. If player is neutral: Prioritize hostile faction enemies, but target player if close

- **Modified enemy movement logic**:
  - All movement AI now uses target position (not always player)
  - Aggressive, flanker, sniper behaviors work with any target
  - Coordinated charges work against faction enemies

### 5. Inter-Faction Combat Mechanics
- **Enemy-vs-Enemy combat**:
  - Enemies can now attack other faction enemies
  - Combat uses same hit/damage calculations
  - Messages show faction warfare: `[FACTION WAR] X strikes Y for Z damage!`
  - Defeated enemies are removed from game

- **Combat messaging**:
  - Reduced message frequency (30% chance) to avoid spam
  - Victory messages when enemy kills another: `X defeats Y!`

## Faction Relationships

### Sith Empire
- **Hostile**: Republic (-80), Settlers (-40), Mandalorian (-30), Hutt (-20)
- **Color**: Red (1)

### Republic
- **Hostile**: Sith Empire (-80), Hutt (-30)
- **Friendly**: Settlers (+40), Mandalorian (+10)
- **Color**: Blue (4)

### Hutt Cartel
- **Hostile**: Republic (-30), Sith Empire (-20), Settlers (-10)
- **Friendly**: Mandalorian (+20)
- **Color**: Cyan (6)

### Settlers
- **Hostile**: Sith Empire (-40), Mandalorian (-20), Hutt (-10)
- **Friendly**: Republic (+40)
- **Color**: Yellow (3)

### Mandalorian
- **Hostile**: Sith Empire (-30), Settlers (-20)
- **Friendly**: Hutt (+20), Republic (+10)
- **Color**: White (7)

## Player Reputation Impact

### Friendly Reputation (> 20)
- Faction enemies will **not** target the player
- They focus only on hostile faction enemies
- Player can safely walk past them

### Neutral Reputation (-20 to 20)
- Enemies prioritize hostile faction enemies
- Will target player if no faction enemies nearby
- Or if player is very close (< 6 tiles)

### Hostile Reputation (< -20)
- Player is a valid target
- Enemies target closest hostile (player or faction enemy)
- No protection from faction membership

## Testing Results

All tests passed successfully:
- ✓ Faction relationships configured correctly
- ✓ Enemies assigned proper factions and colors
- ✓ Sith targets hostile Republic enemies
- ✓ Republic targets hostile Sith enemies
- ✓ Friendly player reputation prevents targeting
- ✓ Targeting logic prioritizes hostile factions

## Gameplay Impact

### Before
- All enemies always chased the player
- No distinction between enemy factions
- All enemies rendered in red

### After
- Enemies fight each other based on faction relationships
- Player can improve reputation to avoid combat
- Visual faction identification through color coding
- More dynamic and realistic battlefield scenarios
- Strategic opportunities to let factions weaken each other

## Example Scenarios

### Scenario 1: Sith vs Republic Battle
- Player with neutral reputation encounters Sith Trooper and Jedi Master
- Enemies ignore player and fight each other
- Player can sneak past or assist either side

### Scenario 2: High Republic Reputation
- Player has +50 reputation with Republic
- Encounters Jedi Master and Sith Warriors
- Jedi Master ignores player, fights Sith
- Sith target player (hostile faction to Republic ally)

### Scenario 3: Multi-Faction Chaos
- Hutt Enforcer, Mandalorian Warrior, Sith Trooper spawn nearby
- Mandalorians fight Sith (hostile)
- Hutts might join Mandalorians against Sith
- Player navigates the chaos

## Files Modified
1. `jedi-fugitive/src/jedi_fugitive/game/factions.py` - Faction relationships and helper methods
2. `jedi-fugitive/src/jedi_fugitive/game/enemy.py` - Targeting system and combat mechanics
3. `jedi-fugitive/src/jedi_fugitive/game/ui_renderer.py` - Faction color rendering
4. `jedi-fugitive/src/jedi_fugitive/game/enemies_sith.py` - Faction assignments (15+ enemies)
5. `jedi-fugitive/src/jedi_fugitive/game/diverse_enemies.py` - Faction assignments (7 enemies)

## Future Enhancements
- Add reputation change messages when helping a faction
- Implement faction-specific rewards for assisting in battles
- Add faction diplomacy options
- Create faction strongholds with guards
- Add faction quests and missions
