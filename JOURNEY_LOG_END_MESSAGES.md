# Journey Log End Messages - Implementation Summary

## Issue
User reported: "i dont see the end message as to why the game ended, can you add something like that on the journey log?"

## Solution
Added comprehensive end-game messages to the player's travel log (journey log) that explain exactly why and how the game ended.

## Implementation

### 1. Death Messages

#### Combat Deaths
When the player dies from enemy attacks, a detailed death entry is added to the travel log:

```python
[DEATH] Struck down by {enemy_name} in {location}. 
Your lightsaber fell from your grasp as darkness claimed you. 
The Force weeps for another fallen Jedi.
```

**Features:**
- Records the name of the enemy that killed the player (tracked via `player.last_attacking_enemy`)
- Includes location context (tomb level or biome name)
- Provides narrative closure

**Example:**
```
[DEATH] Struck down by Sith Inquisitor in the depths of Sith Tomb Level 3. 
Your lightsaber fell from your grasp as darkness claimed you. 
The Force weeps for another fallen Jedi.
```

#### Stress Deaths
When the player dies from stress overload (Breaking Point), a different narrative is used:

```python
[DEATH] Succumbed to overwhelming stress and mental anguish. 
{body_fate} The darkness of this place proved too much to bear.
```

**Body fate varies by location:**
- **In tomb:** "Your broken mind left your body a hollow shell in the depths of the Sith Tomb Level {X}."
- **On surface:** "Your sanity shattered, you collapsed in the {biome}, never to rise again."

**Example:**
```
[DEATH] Succumbed to overwhelming stress and mental anguish. 
Your broken mind left your body a hollow shell in the depths of the Sith Tomb Level 2. 
The darkness of this place proved too much to bear.
```

### 2. Victory Messages

When the player wins by activating the distress beacon, the victory message varies based on dark corruption level:

#### Pure Light (0-20% corruption)
```
[VICTORY] You activated the distress beacon. The Jedi Council's transmission 
filled you with hope - your mission is complete. The artifacts are purified, 
and your devotion to the Light Side has earned you honor. Rescue is coming.
```

#### Light with Caution (21-40% corruption)
```
[VICTORY] The beacon is active. The Council's words were cautious - they sense 
the darkness that touched you in the tombs. You survived, but at what cost? 
You will return to face judgment and purification.
```

#### Balanced/Gray (41-59% corruption)
```
[VICTORY] You reached the beacon, but the Council's message chills your blood. 
They know what you did to survive. The artifacts are tainted, as are you. 
Your future with the Order is uncertain. A rescue team comes... but also judgment.
```

#### Dark (60-79% corruption)
```
[VICTORY?] The beacon transmitted your location, but the Council's response 
was exile. You are no longer a Jedi in their eyes. The darkness consumed too 
much of who you were. You survived the tombs, but lost yourself. No rescue will come.
```

#### Pure Dark (80-100% corruption)
```
[VICTORY?] You activated the beacon, sealing your fate. The Council knows you 
have fallen completely to the Dark Side. They don't send rescue - they send 
executioners. Jedi Masters hunt you now. You escaped the tombs only to face 
a greater threat. Was it worth it?
```

### 3. Display in End-Game Screens

Both death and victory screens automatically display the journey log:

#### Death Screen
- Shows ASCII art defeat scene
- Displays final statistics
- Shows **last 5 travel log entries** (including death message)
- Calls `show_full_story()` for complete log

#### Victory Screen
- Shows ASCII art victory scene
- Displays final statistics
- Calls `show_full_story()` for complete log (including victory message)

### 4. Full Story Display

The `show_full_story()` function displays:
- Complete travel log with turn numbers
- Pauses every 20 entries for readability
- Final statistics summary
- Final alignment determination

**Format:**
```
[Turn 0] [START] You crash-land on the Sith world...
[Turn 10] [COMBAT] Defeated a Sith Acolyte
[Turn 50] [FIRST TOMB] I descended into the darkness...
[Turn 150] [DEATH] Struck down by Sith Warrior in the volcanic wastes...
```

## Code Changes

### Files Modified

1. **src/jedi_fugitive/game/game_manager.py**
   - Lines 404-431: Enhanced death detection to add context-aware death messages
   - Lines 1218-1230: Added victory journal entries based on corruption level
   - Uses `player.last_attacking_enemy` to track killer name

2. **src/jedi_fugitive/game/enemy.py** (already existed)
   - Lines 947-952: Already tracks `player.last_attacking_enemy` on damage

### Files Created

1. **scripts/test_death_victory_messages.py**
   - Test suite validating message formatting
   - Confirms all 5 victory variations
   - Validates combat and stress death messages
   - Tests travel log display format

## Message Markers

All messages use consistent markers for easy parsing:

- `[DEATH]` - Death events
- `[VICTORY]` - Victory events  
- `[VICTORY?]` - Ambiguous victories (dark endings)
- `[START]` - Game start
- `[COMBAT]` - Combat events
- `[FIRST TOMB]` - First tomb entry
- `[ARTIFACT]` - Artifact discoveries
- `[BREAKING POINT]` - Stress breaking points

## Testing

Run the test suite:
```bash
python scripts/test_death_victory_messages.py
```

**All tests pass:**
- ✓ Combat death messages formatted correctly
- ✓ Stress death messages formatted correctly
- ✓ Victory messages formatted correctly (5 variations)
- ✓ Travel log displays messages properly
- ✓ Message markers are consistent

## User Impact

### Before
- Player dies or wins with no journal explanation
- End screen shows stats but no narrative closure
- Unclear why the game ended

### After
- Death messages explain who/what killed the player and where
- Victory messages reflect the player's moral choices (corruption level)
- Travel log provides complete narrative arc
- Clear end-game message visible in last 5 journal entries
- Full story includes the ending message

## Example End-Game Flow

### Death by Combat
1. Player HP drops to 0 from Sith Warrior attack
2. Death entry added: `[DEATH] Struck down by Sith Warrior in the volcanic wastes...`
3. Death screen shows last 5 log entries (including death message)
4. Full story displays complete journey ending with death

### Victory with High Corruption
1. Player activates beacon with 75% corruption
2. Victory entry added: `[VICTORY?] The beacon transmitted your location, but the Council's response was exile...`
3. Victory screen shows final stats
4. Full story displays complete journey ending with dark victory

## Notes

- Death messages automatically detect location (tomb vs surface)
- Victory messages create narrative consequences for player choices
- Message markers make log entries parseable for future features
- All messages maintain consistent tone and lore accuracy
