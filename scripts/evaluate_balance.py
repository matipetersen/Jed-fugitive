"""Small utility to show enemy stats across levels and sample spawn counts.
Run from the project root with: PYTHONPATH=src python3 scripts/evaluate_balance.py
"""
from jedi_fugitive.game.enemy import Enemy, EnemyType

try:
    from jedi_fugitive.config import DIFFICULTY_MULTIPLIER
except Exception:
    DIFFICULTY_MULTIPLIER = 1.0

print("DIFFICULTY_MULTIPLIER:", DIFFICULTY_MULTIPLIER)
print()

levels = list(range(1, 11))
for et in [EnemyType.STORMTROOPER, EnemyType.SITH_GHOST, EnemyType.INQUISITOR]:
    print(f"\n== {et.name} ==")
    print("lvl\tmax_hp\tattack\tdefense\txp")
    for l in levels:
        e = Enemy(et, level=l)
        print(f"{l}\t{getattr(e,'max_hp',None)}\t{getattr(e,'attack',None)}\t{getattr(e,'defense',None)}\t{getattr(e,'xp_value',None)}")

# sample spawn counts for three map sizes
print('\nSample spawn_count estimates:')
map_sizes = [(40, 40), (80, 40), (160, 80)]
for mw, mh in map_sizes:
    area = mw * mh
    base_spawn = max(5, min(50, int(area // 200)))
    print(f"Map {mw}x{mh} area={area} base_spawn={base_spawn}")
    for level in (1, 3, 5, 10):
        factor = 1.0 + max(0, (level - 1)) * 0.12 * float(DIFFICULTY_MULTIPLIER)
        spawn = max(3, min(120, int(base_spawn * factor)))
        print(f"  player_level={level} -> spawn_count={spawn}")
print('\nDone')