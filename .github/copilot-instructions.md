# Jedi Fugitive - Copilot Instructions

Terminal-based roguelike built with Python curses. Star Wars-themed Jedi fugitive simulator with stress/alignment psychology system, Force abilities, and procedurally generated maps.

## Architecture Overview

**GameManager** (`game/game_manager.py`) is the ~2000-line central orchestrator managing:
- Player state, enemy list, map data structures
- UI panels via SILQUI (`ui/silq_ui.py`)
- Turn-based game loop and event processing
- Initialization: `gm.initialize()` → `gm.generate_world()` → `gm.run()`

**Player** (`game/player.py`) tracks:
- Core stats: HP, attack, defense, evasion, accuracy
- Psychological state: `stress` (0-100+) and `alignment_score` (0-100 Light/Dark balance)
- Pristine `_base_stats` dict preserved before equipment modifiers are applied
- Force abilities dict and force points
- Stress affects: Force costs via `get_force_cost_multiplier()` (1.05x-1.35x), accuracy via `get_effective_accuracy()` (10%-40% penalty)

**Equipment System** (`game/equipment.py`) supports three item formats:
- String tokens: `'v'` (vibroblade), `'b'` (blaster), `'s'` (shield)
- Dicts with `token` key: `{'token': 'v', 'name': 'Vibroblade', 'attack': 3}`
- Objects with attributes: `weapon.attack`, `armor.defense`
- **Critical**: Always call `_remove_equipment_effects()` before equipping new items to prevent stat stacking
- Modifiers applied additively on top of `player._base_stats`

**Combat System** (`game/combat.py`):
- Hit calculation: `chance = max(5, min(95, accuracy - evasion + 50))`
- Damage from `equipped_weapon.get_damage()` or fallback to `player.attack`
- `calculate_hit()` returns bool, `player_attack()` returns `(hit: bool, damage: int)`

**Map Representation**: 2D list accessed as `game_map[y][x]`
- Glyphs: `#` walls, `.` floor, `>` downstairs, `<` upstairs, `@` player, letters for enemies/items
- Scaling: `config.MAP_SCALE` multiplies base dimensions (default 4x)
- FOV/visibility tracked in `game.visible` and `game.explored` sets

**Force Abilities** (`game/force_abilities.py`):
- Base class `ForceAbility` with `name`, `base_cost`, `target_type`, `description`
- `use()` method signature: `(user, target, game_map, messages, player_rank=0, **kwargs)`
- Push/Pull resolves coordinate targets by checking `game.enemies` list
- Caller must handle actual movement physics after resource validation

## Critical Patterns

### Defensive Coding (Pervasive)
Extensive `getattr()` with defaults and try/except blocks due to evolving schemas and test harnesses:
```python
try:
    val = int(getattr(obj, 'attribute', 0))
except Exception:
    val = 0
```

Always assume attributes may be missing or wrong type. Check before mutation:
```python
enemy.hp = getattr(enemy, "hp", 0) - damage  # Not: enemy.hp -= damage
```

### Message Buffer Safety
UI message buffer may not exist in headless tests. Use the helper method:
```python
game.add_message("Action completed")  # Safe: falls back to print()
```
Or handle explicitly:
```python
try:
    game.ui.messages.add("Action completed")
except Exception:
    pass
```

### Turn System and Stress Accumulation
- Actions that consume a turn increment `game.turn_count`
- `process_turn_effects()` applies per-turn stress from:
  - Combat proximity: +2 stress when enemy within attack range
  - Low HP: +5 stress when HP < 30%
  - Surrounded: +20 stress when 3+ adjacent enemies (once per condition)
  - Darkness: +10 stress in unexplored dark tiles
  - Being hunted: +5 stress per turn when flagged
- Stress ≥100 triggers breaking point: player may resist or turn dark

### Equipment Workflow
When equipping items:
1. Call `_remove_equipment_effects(game, slot)` to restore base stats
2. Clear the slot: `game.player.equipped_weapon = None`
3. Apply new item: `_apply_equipment_effects(game, item, slot)`
4. Re-apply all other equipped items to avoid losing their bonuses

## Development Workflows

### Running the Game
**Requires real terminal** (not VS Code integrated terminal):
```bash
export TERM=xterm-256color
python -m jedi_fugitive.main
```

VS Code users: Configure launch.json to use external terminal or run from Terminal.app/iTerm.

### Testing
**DummyStdScr mock** (`tests/run_tests.py`) simulates curses for headless tests:
```python
class DummyStdScr:
    def getmaxyx(self): return (40, 160)
    def getch(self): return -1
    # ... minimal curses API stub
```

Run tests:
```bash
python -m pytest tests/
python scripts/headless_smoke.py  # System integration tests
```

Check specific scripts in `scripts/` for targeted validation (e.g., `test_equip_stats.py`, `test_leveling.py`).

### Building Executables
**macOS**: `./scripts/build_mac.sh` (creates `.venv_build`, runs PyInstaller)
**Windows**: `scripts\build_windows.ps1`
**CI**: `.github/workflows/build.yml` builds on push to main, uploads artifacts

PyInstaller config: `--onefile --name "jedi-fugitive" src/jedi_fugitive/main.py`

### Tuning Difficulty
Edit `config.py`:
- `DIFFICULTY_MULTIPLIER`: Global enemy stat scaling (default 1.0)
- `DEPTH_DIFFICULTY_RATE`: Per-depth difficulty increment (default 0.20)
- `MAP_SCALE`: Map size multiplier (default 4)

## Module Organization

```
src/jedi_fugitive/
├── main.py                  # Entry point, curses wrapper, headless fallback
├── config.py                # Global constants (map ratios, difficulty, save file)
├── game/
│   ├── game_manager.py      # Central orchestrator (2000+ lines)
│   ├── player.py            # Player stats, stress, leveling, force abilities
│   ├── enemy.py             # Enemy class, types, AI processing
│   ├── enemies_sith.py      # Sith-specific enemy definitions
│   ├── combat.py            # Hit calculation, attack resolution
│   ├── equipment.py         # Equip/unequip, stat application, inventory chooser
│   ├── force_abilities.py   # ForceAbility base class, Push/Pull, etc.
│   ├── projectiles.py       # Blaster bolts, projectile physics
│   ├── level.py             # Map generation (crash site, dungeons, tombs)
│   ├── map_features.py      # Tomb entrances, stairs, feature interaction
│   ├── input_handler.py     # Keyboard input routing
│   └── ui_renderer.py       # Draw logic for game state
├── items/
│   ├── weapons.py           # Weapon classes (vibroblade, blaster, lightsaber)
│   ├── armor.py             # Armor definitions
│   ├── consumables.py       # Medkits, stimpacks, item effects
│   └── tokens.py            # Token-to-item mapping
├── ui/
│   ├── silq_ui.py           # SILQUI panel manager, color init, centered dialogs
│   └── dialog.py            # DialogueSystem, UIMessageBuffer
└── abilities/               # (Seems unused; force abilities in game/ instead)
```

## Common Tasks

**Adding a new Force ability**:
1. Subclass `ForceAbility` in `game/force_abilities.py`
2. Set `name`, `base_cost`, `target_type`, `description`
3. Implement `use()` method with cost validation
4. Add to `FORCE_ABILITIES` list
5. Grant to player via `player.force_abilities[ability.name] = ability`

**Adding a new enemy type**:
1. Add entry to `EnemyType` enum in `game/enemy.py`
2. Define stats in enemy spawn functions (see `game/enemies_sith.py`)
3. Add personality via `EnemyPersonality` if taunts/behavior needed
4. Update `process_enemies()` if special AI required

**Modifying stress thresholds**:
- Edit `get_force_cost_multiplier()` and `get_effective_accuracy()` in `player.py`
- Adjust per-turn stress sources in `game_manager.process_turn_effects()`
- Tune `_stress_resilience_per_level` for per-level mitigation

**Debugging map generation**:
- Run `scripts/test_map_tokens.py` to verify token placement
- Check `generate_crash_site()` and `generate_dungeon_level()` in `level.py`
- Inspect `game.game_map`, `game.items_on_map`, `game.tomb_entrances`

## Important Notes
- Project uses extensive defensive coding due to iterative refactoring and test harness variations
- SILQUI is a custom curses panel manager; not a third-party library
- Force abilities stored in player's dict, not a separate manager
- Equipment system intentionally flexible to support legacy token strings, dicts, and objects
- Stress system is core mechanic: affects costs, accuracy, and triggers alignment shifts
- Map coordinates follow `game_map[y][x]` convention (row-major access)
- Tests use `DummyStdScr` to simulate curses for headless execution
- Always prefer `game.add_message()` over direct `ui.messages.add()` for broader compatibility
- When debugging, check `/tmp/jedi_fugitive_debug.txt` for detailed state snapshots
