# Combat Descriptions & Unified Projectile System

## Summary
Enhanced combat logging with cinematic descriptions for all ranged weapons and Force abilities. Unified projectile system ensures player and enemy projectiles behave identically.

## Changes Made

### 1. Ranged Weapon Combat Descriptions (input_handler.py)
**Location**: Lines 2049-2125

Added **5 varied firing messages** when player uses auto-aim (f key):
- "Your {weapon} hums as it fires a searing bolt at {enemy}!"
- "Crimson energy lances from your {weapon} toward {enemy}!"
- "You squeeze the trigger - your {weapon} unleashes deadly plasma at {enemy}!"
- "A brilliant bolt of energy streaks from your {weapon} toward {enemy}!"
- "Your {weapon} erupts with blaster fire - the bolt races toward {enemy}!"

### 2. Projectile Hit Descriptions (projectiles.py)
**Location**: Lines 185-220

Added **descriptive messages** when projectiles strike enemies:

**Fatal Hits** (4 variants):
- "Your bolt strikes true - {enemy} falls with a final cry!"
- "The energy blast tears through {enemy}'s defenses - they collapse!"
- "{enemy} staggers and drops as your shot finds its deadly mark!"
- "A perfect hit! {enemy} crumples to the ground, defeated!"

**Non-Fatal Hits** (5 variants):
- "Your shot slams into {enemy}!"
- "Direct hit on {enemy}!"
- "The bolt scores a solid hit on {enemy}!"
- "{enemy} reels from your accurate fire!"
- "Your aim is true - {enemy} takes the hit!"

### 3. Force Lightning Descriptions (force_abilities.py)
**Location**: Lines 355-385

**Fatal Lightning** (4 variants):
- "Crackling dark energy erupts from your fingertips - {enemy} convulses and falls!"
- "Force Lightning arcs through {enemy}'s body - they collapse in a smoking heap!"
- "Blue-white electricity engulfs {enemy} - their scream cuts short as they drop!"
- "You channel the dark side's fury - {enemy} spasms violently and dies!"

**Non-Fatal Lightning** (5 variants):
- "Dark lightning lances from your hands, striking {enemy}!"
- "Tendrils of crackling energy surge into {enemy}!"
- "You unleash the storm - {enemy} writhes in agony!"
- "Force Lightning tears through {enemy}'s defenses!"
- "Sith fury manifests as pure energy, scorching {enemy}!"

### 4. Force Push/Pull Descriptions (abilities.py)
**Location**: Lines 125-145

**Push Messages** (4 variants):
- "You thrust your hand forward - an invisible Force wave erupts outward!"
- "The Force surges through you, hurling everything before you backward!"
- "With a commanding gesture, you unleash a telekinetic blast!"
- "Raw Force energy explodes from your palm!"

**Pull Messages** (4 variants):
- "You clench your fist - the Force yanks your target toward you!"
- "An invisible grip seizes your foe, dragging them closer!"
- "You reach out through the Force, pulling your enemy inexorably forward!"
- "With a sharp gesture, you command the Force to bring them to you!"

### 5. Force Choke Descriptions (force_abilities.py)
**Location**: Lines 615-640

**Fatal Choke** (4 variants):
- "You close your fist - {enemy}'s throat crushes with a sickening crack!"
- "An invisible grip tightens around {enemy}'s neck - they collapse, lifeless!"
- "{enemy} claws desperately at their throat as the Force crushes the life from them!"
- "The dark side flows through you - {enemy} expires with a strangled gasp!"

**Non-Fatal Choke** (5 variants):
- "You reach out with the Force - {enemy} clutches at their throat, gasping!"
- "An invisible hand grips {enemy}'s windpipe - they struggle for air!"
- "{enemy} chokes and sputters as you crush their throat with the Force!"
- "You clench your fist - {enemy} writhes in agony, unable to breathe!"
- "The dark side surges through you, strangling {enemy} from afar!"

### 6. Force Drain Descriptions (force_abilities.py)
**Location**: Lines 690-715

**Fatal Drain** (4 variants):
- "You rip the life essence from {enemy} - they wither into a desiccated husk!"
- "{enemy}'s vitality flows into you as they age decades in seconds and collapse!"
- "Tendrils of dark energy drain {enemy} completely - their corpse falls like ash!"
- "You feast on {enemy}'s life force until nothing remains but an empty shell!"

**Non-Fatal Drain** (5 variants):
- "Dark tendrils snake out, siphoning {enemy}'s life essence into you!"
- "You feel invigorated as {enemy}'s vitality pours into your body!"
- "{enemy} weakens and pales as you drain their life force!"
- "Crimson energy flows from {enemy} to you - their strength becomes yours!"
- "You channel the dark side, leeching life from {enemy}'s trembling form!"

### 7. Enhanced Combat Narrator (combat_narrator.py)
**Location**: Lines 14-25

Added weapon type classifications:
- **blaster**: "blaster bolt", "searing plasma", "crimson energy", "deadly shot"
- **rifle**: "rifle blast", "high-powered bolt", "precision shot", "rifle fire"
- **force_lightning**: "crackling lightning", "dark electricity", "Sith fury", "Force storm"
- **force_push**: "Force wave", "telekinetic blast", "invisible force", "kinetic shockwave"

## Unified Projectile System

### How It Works
All projectiles (player and enemy) now use the **same system**:

1. **Creation**: `spawn_blaster(game, sx, sy, tx, ty, damage, symbol, color_pair)`
   - Creates a `Projectile` object with trajectory (dx, dy)
   - Adds to `game.projectiles` list
   - Player projectiles: color_pair=11 (cyan)
   - Enemy projectiles: color_pair=12 (red)

2. **Movement**: `advance_projectiles(game)`
   - Called **every turn** in `enemy.py process_enemies()`
   - Moves all projectiles one step
   - Checks for collisions with enemies/player
   - Applies damage on hit
   - Shows damage popups

3. **Display**: `ui_renderer.py` lines 360-380
   - Renders all projectiles from `game.projectiles` list
   - Uses projectile's `symbol` and `color_pair` attributes
   - Distinguishes player vs enemy projectiles by color

### Key Differences from Old System
- **OLD**: Enemy projectiles used `animate_projectile()` (instant animation)
- **NEW**: All projectiles use `Projectile` objects that persist and move each turn
- **RESULT**: Consistent behavior - bolts travel across screen gradually, not instantly

### Projectile Attributes
```python
@dataclass
class Projectile:
    x: int                    # Current position
    y: int
    dx: int                   # Direction of movement
    dy: int
    symbol: str = "-"         # Display character
    damage: int = 1           # Damage on hit
    owner: object = None      # Who fired it (player/enemy)
    range_remaining: int = 8  # How far it can travel
    alive: bool = True        # Whether still active
    color_pair: int = 9       # Display color
```

## Color Scheme
- **#2#** = Green (weapon fire initiation)
- **#9#** = Yellow (fatal hits, victories)
- **#11#** = Cyan (Force abilities, telekinesis)
- **#13#** = Magenta (dark side powers - Lightning, Choke, Drain)

## Testing Notes
1. Press **'f'** to auto-aim fire blaster at nearest enemy
   - Should see varied firing message
   - Bolt should travel across screen
   - Hit message when bolt strikes

2. Press **'z'** to use Force abilities
   - Push/Pull: see telekinetic descriptions
   - Lightning: see crackling energy descriptions
   - Choke: see suffocation descriptions
   - Drain: see life-stealing descriptions

3. All projectiles move at same speed (1 tile per turn)
4. Damage popups appear on hit location
5. Messages indicate fatal vs non-fatal hits

## Files Modified
1. `/src/jedi_fugitive/game/input_handler.py` - Blaster firing messages
2. `/src/jedi_fugitive/game/projectiles.py` - Hit descriptions, unified system
3. `/src/jedi_fugitive/game/force_abilities.py` - Force ability descriptions
4. `/src/jedi_fugitive/game/abilities.py` - Push/Pull descriptions
5. `/src/jedi_fugitive/game/combat_narrator.py` - Weapon type classifications

## Status
✅ All ranged weapons have descriptive combat logs
✅ All Force abilities have cinematic descriptions
✅ Projectile system unified (player and enemy use same code)
✅ Bolts travel consistently across screen
✅ Fatal vs non-fatal hit messages differentiated
✅ Color-coded messages for different attack types
