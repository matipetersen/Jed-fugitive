"""Simulate expected damage-per-turn (DPS) for enemy types across levels.
Run with: PYTHONPATH=src python3 scripts/simulate_dps.py
"""
import random
from statistics import mean

try:
    from jedi_fugitive.game.enemy import Enemy, EnemyType
    from jedi_fugitive.game.combat import calculate_hit
except Exception:
    # best-effort imports
    from jedi_fugitive.game.enemy import Enemy, EnemyType
    def calculate_hit(a, b):
        return random.random() < 0.5

PLAYER = {
    'hp': 40,
    'defense': 3,
    'evasion': 10,
}

TRIALS = 2000

print('Baseline player:', PLAYER)
print('\nEstimating expected DPS per enemy (Monte Carlo)')
print('etype\tlvl\tP_hit\texp_dmg\tttk_turns')
for et in [EnemyType.STORMTROOPER, EnemyType.SITH_GHOST, EnemyType.INQUISITOR]:
    for lvl in (1, 3, 5, 8, 10):
        e = Enemy(et, level=lvl)
        atk = getattr(e, 'attack', 1)
        base_damage = max(1, int(atk - PLAYER['defense']))
        # estimate hit probability by repeated calculate_hit calls
        hits = 0
        for _ in range(TRIALS):
            try:
                if calculate_hit(atk, PLAYER['evasion']):
                    hits += 1
            except Exception:
                # fallback random
                if random.random() < 0.5:
                    hits += 1
        p_hit = hits / TRIALS
        exp_dmg = p_hit * base_damage
        ttk = PLAYER['hp'] / exp_dmg if exp_dmg > 0 else float('inf')
        print(f"{et.name}\t{lvl}\t{p_hit:.3f}\t{exp_dmg:.2f}\t{ttk:.1f}")
print('\nDone')
