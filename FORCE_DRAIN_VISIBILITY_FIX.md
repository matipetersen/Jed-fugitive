# Force Drain Visibility Fix Implementation

## 🎯 **Dark Meridian: Force Drain Line-of-Sight Fix**

### **Issue Identified:**
Players were receiving messages about Sith Lords siphoning Force energy, but couldn't see any enemies on the map. The Sith Inquisitors were draining Force energy from across the map without proper line-of-sight checks.

### **Root Cause:**
Both **Dread Inquisitor** and **Sith Inquisitor** had Force drain abilities that operated with insufficient visibility checks:

1. **Dread Inquisitor**: No distance or visibility check (could drain from anywhere)
2. **Sith Inquisitor**: Distance check (≤12 tiles) but no line-of-sight verification

### **Changes Made:**

#### 1. **Dread Inquisitor Force Drain** (`src/jedi_fugitive/game/enemies_sith.py`)
- **Before**: No distance or visibility restrictions
- **After**: 
  - Distance limit: ≤8 tiles  
  - Line-of-sight check required
  - Proper visibility validation before draining

#### 2. **Sith Inquisitor Force Drain** (`src/jedi_fugitive/game/enemies_sith.py`)  
- **Before**: Distance ≤12 tiles, no LOS check
- **After**:
  - Distance limit: ≤10 tiles (reduced)
  - Line-of-sight check required
  - Proper visibility validation before draining

### **Technical Implementation:**

#### **Visibility Check Logic:**
```python
# Check if player can see this enemy (line of sight)
player_can_see_enemy = False
try:
    if hasattr(game, 'is_visible'):
        player_can_see_enemy = game.is_visible(getattr(self, 'x', 0), getattr(self, 'y', 0))
    elif hasattr(game, 'player') and hasattr(game.player, 'los_radius'):
        # Fallback: use simple distance check with LOS radius
        player_can_see_enemy = dist <= getattr(game.player, 'los_radius', 6)
except Exception:
    # If visibility check fails, assume player can't see enemy
    player_can_see_enemy = False

if player_can_see_enemy and hasattr(player, 'force_points') and player.force_points > 0:
    # Perform force drain
```

#### **Dread Inquisitor Changes:**
- **Trigger**: Every 3 turns → Every 3 turns + distance ≤8 + LOS
- **Range**: Unlimited → 8 tiles maximum
- **Force Drain**: 1 point → 1 point (unchanged)
- **Visibility**: None → Required

#### **Sith Inquisitor Changes:**
- **Trigger**: Every 4 turns → Every 4 turns + distance ≤10 + LOS  
- **Range**: 12 tiles → 10 tiles maximum
- **Force Drain**: 2 points → 2 points (unchanged)
- **Visibility**: None → Required

### **Fallback Mechanisms:**

1. **Primary**: Uses `game.is_visible(x, y)` method for accurate LOS calculation
2. **Fallback**: Uses `player.los_radius` for simple distance-based visibility
3. **Safety**: If visibility check fails, assumes enemy is not visible (no drain)

### **Testing Results:**

#### **Visibility Tests Passed:**
- ✅ Force drain works when enemy is visible and within range
- ✅ Force drain blocked when enemy is outside LOS radius
- ✅ Force drain blocked when enemy is too far away
- ✅ No drain messages shown for invisible enemies
- ✅ Proper fallback behavior when visibility system unavailable

#### **Distance Limits:**
- **Dread Inquisitor**: ≤8 tiles + LOS required
- **Sith Inquisitor**: ≤10 tiles + LOS required
- **Player LOS**: Typically 6 tiles (so most drains occur at close range)

### **Impact:**

#### **Before Fix:**
- ❌ Sith Lords could drain Force energy from across the map
- ❌ Players received drain messages without seeing enemies  
- ❌ Force energy would mysteriously decrease to 2 with no visible cause
- ❌ Confusing and immersion-breaking gameplay

#### **After Fix:**  
- ✅ Force drain only works when player can see the enemy
- ✅ Drain messages only appear for visible enemies
- ✅ Reasonable distance limits prevent long-range draining
- ✅ Clear cause-and-effect relationship between visible enemies and Force drain
- ✅ Improved tactical gameplay (players can use cover to avoid drain)

### **Player Experience:**

#### **New Behavior:**
1. **Visual Confirmation**: Player sees Sith Inquisitor on map
2. **Proximity Warning**: Enemy must be within 8-10 tiles  
3. **Line-of-Sight**: Enemy must be visible (not behind walls/obstacles)
4. **Clear Feedback**: Drain message only shows for visible enemies
5. **Tactical Options**: Players can use distance/cover to avoid drains

#### **Strategic Implications:**
- Players can now strategically position to avoid Force drains
- Cover and distance become valuable defensive tools
- Force drain becomes a tactical close-range threat, not map-wide harassment
- Visual enemy identification is now reliable for Force drain sources

### **Compatibility:**
- ✅ Maintains all existing Force drain mechanics
- ✅ Preserves enemy AI behavior patterns  
- ✅ No impact on other Force abilities
- ✅ Backward compatible with existing saves
- ✅ Works with both visibility systems (is_visible() and los_radius fallback)

---

**Fix Status**: ✅ **COMPLETE**
**Testing Status**: ✅ **VERIFIED**
**Integration Status**: ✅ **READY FOR GAMEPLAY**