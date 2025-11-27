# Enhanced Game Statistics System

## Overview

The Jedi Fugitive game now features a comprehensive persistent statistics tracking system that records and displays lifetime achievements across all game runs. This includes K/D ratios, win streaks, total kills, and detailed performance metrics.

## Features Implemented

### 1. **Persistent Statistics Tracking**
- Statistics are saved to `~/.jedi_fugitive/game_stats.json`
- Data persists across game sessions and system restarts
- Automatic file creation and corruption recovery

### 2. **Core Statistics**

#### Game Counters
- **Total Runs**: Total number of games played
- **Victories**: Number of successful completions
- **Deaths**: Number of failed runs
- **Win Rate**: Victory percentage (Victories / Total Runs × 100)

#### Combat Statistics
- **Total Kills**: Lifetime enemy kills across all runs
- **K/D Ratio**: Kill/Death ratio (Total Kills / Total Deaths)
- **Most Enemies Killed**: Highest kill count in a single run
- **Highest Level**: Highest level achieved across all runs

#### Performance Metrics
- **Win Streak**: Current consecutive victories
- **Best Win Streak**: Longest win streak achieved
- **Fastest Victory**: Quickest completion time in turns
- **Total Turns Played**: Cumulative turn count

### 3. **Integration Points**

#### Main Menu Display
```
💫 Force Echo #15
   ⭐ Souls Redeemed: 8
   💀 Fallen to Darkness: 7
   ⚖️ Balance Ratio: 53.3%
   ⚔️ Total Kills: 456
   📊 K/D Ratio: 65.14
   🔥 Best Streak: 4
```

#### Victory Screen
```
═══ LIFETIME STATISTICS ═══
Total Runs: 15
Victories: 8
Deaths: 7
Win Rate: 53.3%
Total Kills: 456
K/D Ratio: 65.14
Win Streak: 2
```

#### Death Screen
```
=== LIFETIME STATISTICS ===
Total Runs: 15
Victories: 8
Deaths: 7
Win Rate: 53.3%
Total Kills: 456
K/D Ratio: 65.14
```

## Technical Implementation

### File Structure

**Location**: `src/jedi_fugitive/utils/game_stats.py`

**Data Storage**: JSON file at `~/.jedi_fugitive/game_stats.json`

**Sample Data Format**:
```json
{
  "total_runs": 15,
  "total_victories": 8,
  "total_deaths": 7,
  "highest_level": 12,
  "most_enemies_killed": 67,
  "total_kills": 456,
  "best_win_streak": 4,
  "current_win_streak": 2,
  "total_turns_played": 3450,
  "fastest_victory_turns": 187
}
```

### Key Classes and Methods

#### GameStats Class

**Initialization**:
```python
from jedi_fugitive.utils.game_stats import get_game_stats

stats = get_game_stats()  # Singleton instance
```

**Recording Outcomes**:
```python
# Record a victory
stats.record_victory(
    player_level=10,
    enemies_killed=52,
    turns_taken=234
)

# Record a death
stats.record_death(
    player_level=6,
    enemies_killed=28,
    turns_taken=145
)
```

**Retrieving Statistics**:
```python
total_runs = stats.get_total_runs()
victories = stats.get_total_victories()
deaths = stats.get_total_deaths()
win_rate = stats.get_win_rate()  # Returns percentage
kd_ratio = stats.get_kill_death_ratio()
total_kills = stats.get_total_kills()
win_streak = stats.get_current_win_streak()
best_streak = stats.get_best_win_streak()
```

**Formatted Summary**:
```python
summary = stats.get_stats_summary()
print(summary)
```

### Game Manager Integration

**Victory Recording** (`game_manager.py` line ~2617):
```python
from jedi_fugitive.utils.game_stats import get_game_stats
game_stats = get_game_stats()
game_stats.record_victory(
    player_level=level,
    enemies_killed=getattr(self.player, 'kills_count', 0),
    turns_taken=self.turn_count
)
```

**Death Recording** (`game_manager.py` line ~2784):
```python
game_stats.record_death(
    player_level=level,
    enemies_killed=getattr(self.player, 'kills_count', 0),
    turns_taken=self.turn_count
)
```

## K/D Ratio Calculation

The K/D (Kill/Death) ratio is calculated as:
```
K/D Ratio = Total Kills / Total Deaths
```

**Special Cases**:
- If deaths = 0 and kills > 0: Returns total kills as the ratio
- If deaths = 0 and kills = 0: Returns 0.0

**Examples**:
- 150 kills / 3 deaths = 50.00 K/D
- 75 kills / 1 death = 75.00 K/D
- 42 kills / 0 deaths = 42.00 K/D

## Win Streak System

### Streak Building
- Each victory increments the current streak
- Current streak is compared to best streak
- Best streak is updated if current exceeds it

### Streak Reset
- Death resets current streak to 0
- Best streak is preserved

### Example Flow
```
Run 1: Victory → Current: 1, Best: 1
Run 2: Victory → Current: 2, Best: 2
Run 3: Victory → Current: 3, Best: 3
Run 4: Death   → Current: 0, Best: 3 (preserved)
Run 5: Victory → Current: 1, Best: 3
```

## Testing

### Unit Tests
**Location**: `scripts/test_enhanced_stats.py`

**Run Tests**:
```bash
python scripts/test_enhanced_stats.py
```

**Coverage**:
- ✅ Initial state validation
- ✅ Run counter increment
- ✅ Victory recording
- ✅ Death recording
- ✅ K/D ratio calculation (with and without deaths)
- ✅ Win streak building and reset
- ✅ Win rate calculation
- ✅ Statistics persistence
- ✅ Fastest victory tracking
- ✅ Summary generation

### Demo Script
**Location**: `scripts/demo_enhanced_stats.py`

**Run Demo**:
```bash
python scripts/demo_enhanced_stats.py
```

**Demonstrates**:
- Multiple game run simulation
- Real-time stat updates after each run
- Win streak progression
- K/D ratio changes
- Fastest victory tracking
- Data persistence verification

## Usage Examples

### Example 1: First-Time Player
```
💫 Force Echo #1
```
No additional stats shown on first run.

### Example 2: Returning Player
```
💫 Force Echo #23
   ⭐ Souls Redeemed: 12
   💀 Fallen to Darkness: 11
   ⚖️ Balance Ratio: 52.2%
   ⚔️ Total Kills: 587
   📊 K/D Ratio: 53.36
   🔥 Best Streak: 5
```

### Example 3: Victory Screen
```
═══ LIFETIME STATISTICS ═══
Total Runs: 23
Victories: 12
Deaths: 11
Win Rate: 52.2%
Total Kills: 587
K/D Ratio: 53.36
Win Streak: 2
```

### Example 4: Perfect Run (No Deaths)
```
Total Runs: 5
Victories: 5
Deaths: 0
Win Rate: 100.0%
Total Kills: 213
K/D Ratio: 213.00
Win Streak: 5 (Best: 5)
```

## Files Modified

### Core System
- `src/jedi_fugitive/utils/game_stats.py` - Enhanced with new metrics
  - Added `total_kills` tracking
  - Added `best_win_streak` and `current_win_streak`
  - Added `total_turns_played` and `fastest_victory_turns`
  - Added `get_kill_death_ratio()` method
  - Added `get_total_kills()` method
  - Added `get_best_win_streak()` method
  - Enhanced `record_victory()` with turns and streak tracking
  - Enhanced `record_death()` with turns and streak reset
  - Enhanced `get_stats_summary()` with new metrics

### Game Integration
- `src/jedi_fugitive/game/game_manager.py`
  - Updated `record_victory()` call with `turns_taken` parameter (line ~2619)
  - Updated `record_death()` call with `turns_taken` parameter (line ~2786)
  - Added K/D ratio and win streak display in victory screen (line ~2627-2628)
  - Added K/D ratio and total kills display in death screen (line ~2794-2795)

- `src/jedi_fugitive/main.py`
  - Enhanced main menu stats display (line ~100-105)
  - Added total kills, K/D ratio, and best streak display

### Test Files
- `scripts/test_enhanced_stats.py` - Comprehensive unit tests (NEW)
- `scripts/demo_enhanced_stats.py` - Interactive demonstration (NEW)

## Benefits

### For Players
1. **Progression Tracking**: See improvement over time
2. **Achievement System**: Track personal bests and streaks
3. **Performance Metrics**: Understand strengths and weaknesses
4. **Motivation**: Win streaks encourage consistent performance
5. **Bragging Rights**: K/D ratio and fastest victory records

### For Game Design
1. **Player Retention**: Persistent stats encourage replay
2. **Difficulty Tuning**: Aggregate win rate data shows balance
3. **Engagement Metrics**: Track player commitment via total runs
4. **Feedback Loop**: Players can measure skill progression

## Future Enhancements (Potential)

- [ ] Online leaderboards
- [ ] Per-character class statistics
- [ ] Light Side vs Dark Side win rate comparison
- [ ] Death cause statistics
- [ ] Location-based kill tracking
- [ ] Boss kill records
- [ ] Speedrun mode with dedicated timing
- [ ] Achievement system based on stats
- [ ] Graphical stat visualization
- [ ] Export stats to CSV/JSON

## Backward Compatibility

The system is fully backward compatible:
- Missing stats default to 0
- Old save files automatically upgrade
- No data loss on version updates
- Graceful fallback if stats file is corrupted

## Error Handling

The stats system includes robust error handling:
- Creates directory if missing (`~/.jedi_fugitive/`)
- Handles JSON corruption (resets to defaults)
- Fails silently to avoid interrupting gameplay
- Logs warnings without crashing the game

## Conclusion

The enhanced game statistics system provides comprehensive lifetime tracking that rewards player skill and encourages replayability. With K/D ratios, win streaks, and detailed performance metrics, players can measure their progression and compete for personal bests across multiple runs.

The system is fully tested, persistent across sessions, and seamlessly integrated into the game's victory/death screens and main menu.
