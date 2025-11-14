"""Minimal batch Inquisitor simulations without importing GameManager.
Creates a small fake game environment, spawns an Inquisitor that mirrors a level-10 player,
applies test tweaks (reduced physical attack, boosted force points, lowered cooldowns),
and runs N simulations to collect win/loss/ability usage stats.

Usage:
  PYTHONPATH=src python3 scripts/batch_inquisitor_sim_minimal.py
"""
import sys
from pathlib import Path
proj_root = Path(__file__).resolve().parents[1]
src = proj_root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

import random
import statistics
import traceback

from jedi_fugitive.game.enemy import Enemy, EnemyType, process_enemies
from jedi_fugitive.game.player import Player
from jedi_fugitive.game import force_abilities

class FakeMessages:
    def __init__(self):
        self.messages = []
    def add(self, text):
        try:
            self.messages.append(str(text))
        except Exception:
            pass

class FakeUI:
    def __init__(self):
        self.messages = FakeMessages()
    def add_popup(self, *a, **k):
        return

class FakeGame:
    def __init__(self, width=40, height=20):
        self.ui = FakeUI()
        self.player = Player(0,0)
        self.enemies = []
        self.game_map = [["."]*width for _ in range(height)]
        self.turn_count = 0
        self.current_depth = 1
        self.running = True

def make_boss_for_player(player, x=10, y=10):
    boss = Enemy(EnemyType.INQUISITOR, level=max(3, getattr(player, 'level', 1)))
    boss.is_boss = True
    # mirror core stats
    try:
        boss.level = getattr(player, 'level', boss.level)
        boss.max_hp = int(getattr(player, 'max_hp', getattr(player, 'hp', boss.max_hp)))
        boss.hp = boss.max_hp
    except Exception:
        pass
    try:
        boss.attack = int(getattr(player, 'attack', boss.attack))
        boss.defense = int(getattr(player, 'defense', getattr(player, 'defense', boss.defense)))
    except Exception:
        pass
    # attach player-like abilities: use FORCE_ABILITIES as a source
    try:
        fa = {}
        for a in (getattr(force_abilities, 'FORCE_ABILITIES', []) or []):
            aname = getattr(a, 'name', None) or type(a).__name__
            fa[aname] = a
        if fa:
            boss.force_abilities = fa
    except Exception:
        pass
    # place
    boss.x = x; boss.y = y

    # TEST tweaks: reduce physical attack and boost force points and lower cooldowns
    try:
        boss.attack = max(1, int(getattr(boss, 'attack', 1) * 0.6))
    except Exception:
        pass
    try:
        pfp = int(getattr(player, 'force_points', 2) or 2)
        boss.force_points = max(int(getattr(boss, 'force_points', 0) or 0), pfp + 6)
    except Exception:
        boss.force_points = getattr(boss, 'force_points', 8) or 8
    try:
        for a in getattr(boss, 'force_abilities', {}).values():
            try:
                setattr(a, 'cooldown', 1)
            except Exception:
                pass
    except Exception:
        pass
    return boss


def run_one(duel_only=True, max_turns=200, seed=None):
    if seed is not None:
        random.seed(seed)
    gm = FakeGame()
    # set player to level 10 and buff stats
    try:
        gm.player.level = 10
        gm.player.max_hp = max(int(getattr(gm.player, 'max_hp', 10)), 10 + (gm.player.level - 1) * 5)
        gm.player.hp = gm.player.max_hp
        gm.player.attack = int(getattr(gm.player, 'attack', 1)) + (gm.player.level - 1)
        gm.player.defense = int(getattr(gm.player, 'defense', 0)) + (gm.player.level - 1)
        gm.player.force_points = max(int(getattr(gm.player, 'force_points', 2) or 2), 8)
    except Exception:
        pass

    # equip best items if available (best-effort)
    try:
        from jedi_fugitive.items.weapons import WEAPONS
        from jedi_fugitive.items.armor import ARMORS
        best_weapon = None; best_w_score = -1
        for w in (WEAPONS or []):
            try:
                score = int(getattr(w, 'base_damage', 0))
                dr = getattr(w, 'damage_range', None)
                if dr:
                    score = max(score, int(dr[1]))
                if score > best_w_score:
                    best_w_score = score; best_weapon = w
            except Exception:
                continue
        if best_weapon:
            try: gm.player.equip_weapon(best_weapon)
            except Exception: gm.player.equipped_weapon = best_weapon
        best_armor = None; best_a_score = -1
        for a in (ARMORS or []):
            try:
                score = int(getattr(a, 'defense', 0)) + int(getattr(a, 'hp_bonus', 0))
                if score > best_a_score:
                    best_a_score = score; best_armor = a
            except Exception:
                continue
        if best_armor:
            try: gm.player.equip_armor(best_armor)
            except Exception: gm.player.equipped_armor = best_armor
    except Exception:
        pass

    boss = make_boss_for_player(gm.player, x=15, y=10)
    gm.enemies.append(boss)
    if duel_only:
        gm.enemies = [boss]

    for t in range(1, max_turns+1):
        gm.turn_count = getattr(gm, 'turn_count', 0) + 1
        try:
            process_enemies(gm)
        except Exception:
            traceback.print_exc()
        # check end
        pdead = getattr(gm.player, 'hp', 1) <= 0
        bdead = getattr(boss, 'hp', 0) <= 0
        if pdead or bdead:
            res = 'player' if bdead and not pdead else ('boss' if pdead and not bdead else 'draw')
            return {
                'result': res,
                'turns': t,
                'boss_hp': getattr(boss, 'hp', None),
                'player_hp': getattr(gm.player, 'hp', None),
                'boss_fp': getattr(boss, 'force_points', None),
                'boss_used_abilities': bool(getattr(boss, '_ability_last_used', {}))
            }
    return {'result':'timeout','turns':max_turns,'boss_hp':getattr(boss,'hp',None),'player_hp':getattr(gm.player,'hp',None),'boss_fp':getattr(boss,'force_points',None),'boss_used_abilities':bool(getattr(boss,'_ability_last_used',{}))}


def main(runs=50):
    results = []
    for i in range(runs):
        r = run_one(duel_only=True, seed=i)
        results.append(r)
        print(f"Run {i+1}/{runs}: {r}")
    wins = sum(1 for r in results if r['result']=='player')
    losses = sum(1 for r in results if r['result']=='boss')
    draws = sum(1 for r in results if r['result']=='draw')
    timeouts = sum(1 for r in results if r['result']=='timeout')
    turns = [r['turns'] for r in results if isinstance(r.get('turns'), int) and r.get('turns')>0]
    boss_hp = [r.get('boss_hp') for r in results if isinstance(r.get('boss_hp'), int)]
    player_hp = [r.get('player_hp') for r in results if isinstance(r.get('player_hp'), int)]
    used_abilities = sum(1 for r in results if r.get('boss_used_abilities'))

    print('\n=== Batch summary ===')
    print(f"Runs: {runs}  Wins(player): {wins}  Losses: {losses}  Draws: {draws}  Timeouts: {timeouts}")
    if turns:
        print(f"Turns: min {min(turns)} max {max(turns)} mean {statistics.mean(turns):.1f} median {statistics.median(turns)}")
    if boss_hp:
        print(f"Boss HP (sample): min {min(boss_hp)} max {max(boss_hp)} mean {statistics.mean(boss_hp):.1f}")
    if player_hp:
        print(f"Player HP (sample): min {min(player_hp)} max {max(player_hp)} mean {statistics.mean(player_hp):.1f}")
    print(f"Boss used abilities in {used_abilities}/{runs} runs")
    return results

if __name__ == '__main__':
    main(50)
