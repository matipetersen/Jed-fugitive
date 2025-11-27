# Combat Logging Fixes - Issue Resolution

## Issues Identified

You were experiencing two main problems with combat logging:

1. **Invisible Enemy Attacks**: Sometimes enemies would kill you without being visible on screen
2. **Vague Death Messages**: Death logs didn't show precise damage amounts, only that something killed you

## Root Causes Found

### 1. Force Lightning Range vs Visibility
- **Problem**: Sith enemies (Inquisitors, Lords) could use Force Lightning at range 8 tiles
- **Issue**: No visibility check was performed before using Force Lightning
- **Result**: Players were being attacked by enemies they couldn't see through walls/obstacles

### 2. Incomplete Damage Tracking  
- **Problem**: Force Lightning attacks weren't properly tracking attacker information
- **Issue**: Death logs would show generic "struck down by an enemy" instead of specific details
- **Result**: Players couldn't tell what actually killed them or how much damage it dealt

### 3. Missing Combat Log Entries
- **Problem**: Non-fatal attacks weren't being logged for reference
- **Issue**: Players had no combat history to review what was happening
- **Result**: Difficulty understanding combat flow and damage patterns

## Fixes Implemented

### 1. Visibility Checks for Force Lightning ✅
```python
# Added visibility check before Force Lightning attacks
if player_can_see_enemy:
    # Only use Force Lightning if player can see the enemy
    lightning.use(self, player, game.game_map, messages, level)
```
- **Location**: `src/jedi_fugitive/game/enemies_sith.py` - Inquisitor AI
- **Effect**: Enemies can no longer use Force Lightning through walls or from outside vision range

### 2. Enhanced Force Lightning Damage Tracking ✅
```python
# Track Force Lightning attack info for death logging
target.last_attacking_enemy = getattr(user, "name", "Sith Enemy")
target.last_damage_taken = dmg
target.last_attack_type = "Force Lightning"
```
- **Location**: `src/jedi_fugitive/game/force_abilities.py` - ForceLightning class
- **Effect**: Death logs now show "Struck down by Darth Thanaton's Force Lightning for 15 damage"

### 3. Improved Death Log Fallbacks ✅
```python
# If no damage info was tracked, use current attack
if damage == 0:
    damage = dmg
    enemy_name = getattr(e, 'name', 'an enemy')
```
- **Location**: `src/jedi_fugitive/game/enemy.py` - Enemy processing
- **Effect**: Death logs always show precise damage amounts and attacker names

### 4. Combat History Tracking ✅
```python
# Add combat log entry for non-fatal hits
if game.player.hp > 0:
    log_entry = f"Turn {turn_count}: {enemy_name} hits for {dmg} damage (HP: {remaining_hp})"
    game.combat_log.append(log_entry)
```
- **Location**: `src/jedi_fugitive/game/enemy.py` - Melee combat
- **Effect**: All attacks are now logged with precise damage and HP remaining

### 5. Better Force Lightning Messages ✅
```python
# Enhanced messaging based on damage outcome
if target.hp <= 0:
    messages.add(f"{enemy_name} strikes {target_name} down with Force Lightning! [{dmg} damage]")
else:
    messages.add(f"{enemy_name} blasts {target_name} with Force Lightning! [{dmg} damage]")
```
- **Location**: `src/jedi_fugitive/game/force_abilities.py`
- **Effect**: Clear distinction between fatal and non-fatal Force Lightning attacks

## Testing Results

All fixes have been validated:
- ✅ Force Lightning now requires line of sight
- ✅ Force Lightning damage is properly tracked for death logs  
- ✅ Death logs show precise damage amounts and attack types
- ✅ Combat log tracks all attacks with HP remaining
- ✅ Enhanced messaging distinguishes fatal vs non-fatal attacks

## Player Experience Improvements

### Before Fixes:
- "You died!" (no context)
- "Struck down by an enemy in the crash site" (vague)
- Surprise deaths from invisible attackers
- No combat history to review

### After Fixes:
- "Darth Thanaton strikes you down with Force Lightning! [15 damage]"
- "[DEATH] Struck down by Darth Thanaton's Force Lightning for 15 damage"
- Only visible enemies can use ranged abilities
- Complete combat log showing all attacks and remaining HP

The combat system now provides clear, precise feedback about what's happening in fights, making deaths feel fair and informative rather than mysterious.