# Enemy System Improvements

## Summary
Fixed creature taunt behavior and assigned unique visual symbols to all planetary enemies for better gameplay clarity.

---

## 1. Creature Taunt System Fix

### Problem
Sandworms and other non-sentient creatures were using English personality taunts instead of appropriate creature sounds.

### Solution
- Added `is_creature` attribute to all non-sentient beasts
- Modified taunt logic in `enemy.py` to check for `is_creature` flag
- Creatures now exclusively use `get_massive_creature_taunt()` which returns sound effects like:
  - `*Massive creature stirs*`
  - `*Creature roars in fury*`
  - `*Beast circles warily*`

### Affected Files
- `src/jedi_fugitive/game/enemy.py` (lines 1019-1031)
- `src/jedi_fugitive/game/planetary_enemies.py` (all creature definitions)

---

## 2. Unique Enemy Symbols

### Problem
Many enemies shared the same visual symbols, making combat confusing:
- `S` used by both Sith Lords and Water Serpents
- `B` used by Boulder Brutes and Bosses
- Basic ASCII letters (r, w, d, etc.) were hard to distinguish

### Solution
Assigned unique Unicode symbols to all 19 planetary creatures:

#### Desert Biome
- **Desert Raider**: `☠` (skull and crossbones) - dangerous humanoid
- **Sandworm Spawn**: `⛬` (worm/serpent) - burrowing creature
- **Dust Stalker**: `Ψ` (psi) - stalking predator

#### Forest Biome
- **Forest Ambusher**: `Θ` (theta) - stealthy hunter
- **Vine Beast**: `Θ` (plant symbol) - plant-covered beast
- **Canopy Hunter**: `Φ` (phi) - agile tree predator

#### Rocky Biome
- **Rock Lizard**: `Λ` (lambda) - camouflaged reptile
- **Cliff Raider**: `↑` (up arrow) - high ground attacker
- **Boulder Brute**: `⚉` (boulder) - massive stone beast

#### Plains Biome
- **Plains Stalker**: `Ξ` (xi) - swift grassland hunter
- **Pack Hunter**: `Ω` (omega) - coordinated predator
- **Plains Charger**: `⚈` (heavy block) - charging beast

#### River Biome
- **River Lurker**: `≈` (wave) - amphibious predator
- **Swamp Crawler**: `Π` (pi) - toxic marsh dweller
- **Water Serpent**: `≋` (serpent wave) - aquatic hunter

#### Crash Site Biome
- **Scrap Scavenger**: `⚙` (gear) - tech scavenger
- **Radiation Mutant**: `☮` (radiation) - mutated creature

### Benefits
- **Visual Clarity**: Each enemy type is instantly recognizable
- **Thematic Coherence**: Symbols match enemy themes (waves for water creatures, gears for scavengers)
- **Improved Gameplay**: Players can identify threats at a glance
- **Reduced Confusion**: No more mistaking a Water Serpent for a Sith Lord

---

## 3. Creature Classification

All non-sentient beasts now have `is_creature = True`:
- Sandworm Spawn
- Dust Stalker
- Forest Ambusher
- Vine Beast
- Canopy Hunter
- Rock Lizard
- Boulder Brute
- Plains Stalker
- Pack Hunter
- Plains Charger
- River Lurker
- Swamp Crawler
- Water Serpent
- Scrap Scavenger
- Radiation Mutant

**Sentient Enemies** (keep personality taunts):
- Desert Raider
- Cliff Raider
- All Sith enemies (Lords, Acolytes, etc.)

---

## Testing Checklist

- [x] Syntax validation passed
- [ ] Verify sandworm produces creature sounds (not English)
- [ ] Check all 19 creatures display unique symbols
- [ ] Confirm creatures don't use personality taunts
- [ ] Test symbol visibility in terminal
- [ ] Verify no symbol conflicts with Sith enemies

---

## Technical Details

### Taunt Logic Flow (enemy.py)
```python
1. Check if enemy has is_creature or is_massive attribute
2. If yes → use get_massive_creature_taunt() (sound effects)
3. If no and has personality → use personality.get_taunt() (English dialogue)
4. Fallback to contextual taunts if needed
```

### Symbol Encoding
All symbols use Unicode characters for cross-platform compatibility. Ensure terminal supports UTF-8 encoding.

---

## Old Republic Compliance

All creature names and descriptions maintain Old Republic era consistency:
- No references to Galactic Empire or New Republic
- Emphasizes ancient, wild, and untamed nature of Korriban's wilderness
- Creatures feel like natural inhabitants of a forgotten Sith world
