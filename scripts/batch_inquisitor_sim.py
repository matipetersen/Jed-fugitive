"""Batch-run forced Inquisitor simulations and collect summary statistics.
Run from project root. Usage: PYTHONPATH=src python3 scripts/batch_inquisitor_sim.py
"""
import sys
from pathlib import Path
proj_root = Path(__file__).resolve().parents[1]
src = proj_root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

import traceback
import statistics

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game import projectiles

class DummyStdScr:
    def __init__(self, h=24, w=80):
        self._h = h; self._w = w
    def getmaxyx(self):
        return (self._h, self._w)
    def subwin(self, h, w, y, x):
        return self
    def clear(self): pass
    def erase(self): pass
    def border(self): pass
    def addstr(self, *a, **k): pass
    def addnstr(self, *a, **k): pass
    def refresh(self): pass
    def noutrefresh(self): pass
    def resize(self, h, w): self._h, self._w = h, w
    def mvwin(self, y, x): pass
    def move(self, y, x): pass
    def clrtoeol(self): pass
    def getch(self): return -1


def run_one(duel_only=False, max_turns=200):
    dummy = DummyStdScr()
    gm = GameManager(dummy)
    gm.initialize()
    gm.generate_world()
    # --- Test setup: imagine the player is level 10 for this batch ---
    try:
        gm.player.level = 10
        # scale player stats conservatively for level 10
        try:
            gm.player.max_hp = max(int(getattr(gm.player, 'max_hp', 10)), 10 + (gm.player.level - 1) * 5)
            gm.player.hp = gm.player.max_hp
        except Exception:
            pass
        try:
            gm.player.attack = int(getattr(gm.player, 'attack', 1)) + (gm.player.level - 1)
            gm.player.defense = int(getattr(gm.player, 'defense', 0)) + (gm.player.level - 1)
        except Exception:
            pass
        try:
            gm.player.force_points = max(int(getattr(gm.player, 'force_points', 2) or 2), 8)
        except Exception:
            gm.player.force_points = getattr(gm.player, 'force_points', 8) or 8
    except Exception:
        pass
    # Equip player with the best available weapon and best armor for this test
    try:
        from jedi_fugitive.items.weapons import WEAPONS
        from jedi_fugitive.items.armor import ARMORS
        # pick weapon with highest base_damage or damage_range max
        best_weapon = None
        best_w_score = -1
        for w in (WEAPONS or []):
            try:
                score = getattr(w, 'base_damage', 0)
                # prefer weapons with larger top-end damage if base_damage absent
                dr = getattr(w, 'damage_range', None)
                if dr:
                    score = max(score, int(dr[1]))
                if score > best_w_score:
                    best_w_score = score; best_weapon = w
            except Exception:
                continue
        if best_weapon:
            try:
                gm.player.equip_weapon(best_weapon)
            except Exception:
                gm.player.equipped_weapon = best_weapon
        # pick armor with highest defense+hp_bonus
        best_armor = None
        best_a_score = -1
        for a in (ARMORS or []):
            try:
                score = int(getattr(a, 'defense', 0)) + int(getattr(a, 'hp_bonus', 0))
                if score > best_a_score:
                    best_a_score = score; best_armor = a
            except Exception:
                continue
        if best_armor:
            try:
                gm.player.equip_armor(best_armor)
            except Exception:
                gm.player.equipped_armor = best_armor
    except Exception:
        pass
    gm.comms_established = True
    sx, sy = getattr(gm.player, 'x', 0), getattr(gm.player, 'y', 0)
    gm.ship_pos = (sx, sy)
    gm._try_move_player(0, 0)  # trigger spawn

    # find boss
    boss = None
    for e in getattr(gm, 'enemies', []) or []:
        if getattr(e, 'is_boss', False) or (getattr(e, 'name', '') or '').lower().find('inquisitor') >= 0:
            boss = e; break
    if not boss:
        return {'result':'no_boss', 'turns':0}

    # ensure boss has force_points so it can use abilities
    if getattr(boss, 'force_points', None) is None:
        boss.force_points = int(getattr(gm.player, 'force_points', 10) or 10)

    # optionally make it a duel (remove minions)
    if duel_only:
        gm.enemies = [boss]

    # run turns
    for t in range(1, max_turns+1):
        gm.turn_count = getattr(gm, 'turn_count', 0) + 1
        try:
            gm.process_enemies()
        except Exception:
            traceback.print_exc()
        try:
            projectiles.advance_projectiles(gm)
        except Exception:
            pass
        try:
            gm._tick_effects()
        except Exception:
            pass

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
    # timeout
    return {'result':'timeout','turns':max_turns,'boss_hp':getattr(boss,'hp',None),'player_hp':getattr(gm.player,'hp',None),'boss_fp':getattr(boss,'force_points',None),'boss_used_abilities':bool(getattr(boss,'_ability_last_used',{}))}


def main(runs=50, duel_only=False):
    results = []
    for i in range(runs):
        r = run_one(duel_only=duel_only)
        results.append(r)
        print(f"Run {i+1}/{runs}: {r}")
    # aggregate
    wins = sum(1 for r in results if r['result']=='player')
    losses = sum(1 for r in results if r['result']=='boss')
    draws = sum(1 for r in results if r['result']=='draw')
    timeouts = sum(1 for r in results if r['result']=='timeout')
    noboss = sum(1 for r in results if r['result']=='no_boss')
    turns = [r['turns'] for r in results if isinstance(r.get('turns'), int) and r.get('turns')>0]
    boss_hp = [r.get('boss_hp') for r in results if isinstance(r.get('boss_hp'), int)]
    player_hp = [r.get('player_hp') for r in results if isinstance(r.get('player_hp'), int)]
    used_abilities = sum(1 for r in results if r.get('boss_used_abilities'))

    print('\n=== Batch summary ===')
    print(f"Runs: {runs}  Wins(player): {wins}  Losses: {losses}  Draws: {draws}  Timeouts: {timeouts}  NoBoss: {noboss}")
    if turns:
        print(f"Turns: min {min(turns)} max {max(turns)} mean {statistics.mean(turns):.1f} median {statistics.median(turns)}")
    if boss_hp:
        print(f"Boss HP (sample): min {min(boss_hp)} max {max(boss_hp)} mean {statistics.mean(boss_hp):.1f}")
    if player_hp:
        print(f"Player HP (sample): min {min(player_hp)} max {max(player_hp)} mean {statistics.mean(player_hp):.1f}")
    print(f"Boss used abilities in {used_abilities}/{runs} runs")
    return results

if __name__ == '__main__':
    # run full-encounter batch (minions will be removed near spawn by quick-balance logic)
    main(50, duel_only=False)
