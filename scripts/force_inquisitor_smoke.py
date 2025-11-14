"""Force Inquisitor spawn and run a focused headless simulation to observe boss behavior.
Run from project root. This script is non-interactive and prints summarized results.
"""
import sys
from pathlib import Path
proj_root = Path(__file__).resolve().parents[1]
src = proj_root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

import traceback
import time

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game import projectiles

class DummyStdScr:
    def __init__(self, h=24, w=80, inputs=None):
        self._h = h; self._w = w
        self._inputs = list(inputs or [])
    def getmaxyx(self):
        return (self._h, self._w)
    def subwin(self, h, w, y, x):
        return self
    def clear(self):
        pass
    def erase(self):
        pass
    def border(self):
        pass
    def addstr(self, *args, **kwargs):
        pass
    def addnstr(self, *args, **kwargs):
        pass
    def refresh(self):
        pass
    def noutrefresh(self):
        pass
    def resize(self, h, w):
        self._h, self._w = h, w
    def mvwin(self, y, x):
        pass
    def move(self, y, x):
        pass
    def clrtoeol(self):
        pass
    def getch(self):
        return -1


def main(turns=200):
    print("Starting forced Inquisitor smoke...")
    try:
        dummy = DummyStdScr()
        gm = GameManager(dummy)
        gm.initialize()
        gm.generate_world()

        # ensure no pre-existing inquisitor flag
        gm.inquisitor_spawned = False

        # mark comms established so stepping on ship spawns boss
        gm.comms_established = True

        # place ship_pos at player's current coord so stepping "in place" triggers spawn
        sx, sy = getattr(gm.player, 'x', 0), getattr(gm.player, 'y', 0)
        gm.ship_pos = (sx, sy)

        print(f"Player at {(sx,sy)}; setting ship_pos there and forcing spawn via _try_move_player(0,0)")
        spawned = gm._try_move_player(0, 0)
        print("_try_move_player returned:", spawned)
        print("inquisitor_spawned flag:", getattr(gm, 'inquisitor_spawned', False))
        print("Number of enemies after spawn:", len(getattr(gm, 'enemies', []) or []))

        # find boss if present
        def find_boss():
            for e in getattr(gm, 'enemies', []) or []:
                if getattr(e, 'is_boss', False) or getattr(e, 'type', None) == getattr(e, 'INQUISITOR', None):
                    return e
                name = getattr(e, 'name', '').lower() if getattr(e, 'name', None) else ''
                if 'inquisitor' in name:
                    return e
            # fallback: try to match EnemyType enum name
            for e in getattr(gm, 'enemies', []) or []:
                if getattr(e, 'name', '').lower().find('inquisitor') >= 0:
                    return e
            return None

        boss = find_boss()
        if not boss:
            print("No boss found after spawn; listing enemies:")
            for e in getattr(gm, 'enemies', []) or []:
                print(" -", getattr(e, 'name', repr(e)), "@", getattr(e,'x',None), getattr(e,'y',None), "hp=", getattr(e,'hp',None))
            return

        print("Boss found:", getattr(boss, 'name', 'Inquisitor'), "hp=", getattr(boss, 'hp', None), "force_points=", getattr(boss, 'force_points', None))

        # run several turns and print summaries every 10 turns
        for t in range(1, turns + 1):
            gm.turn_count = getattr(gm, 'turn_count', 0) + 1
            try:
                gm.process_enemies()
            except Exception:
                traceback.print_exc()
            try:
                # advance projectiles as a safety
                projectiles.advance_projectiles(gm)
            except Exception:
                pass
            try:
                gm._tick_effects()
            except Exception:
                pass
            try:
                gm.compute_visibility()
            except Exception:
                pass

            # print periodic summaries
            if t % 10 == 0 or t <= 5:
                msgs = []
                try:
                    msgs = getattr(gm.ui, 'messages', None).messages[-6:]
                except Exception:
                    pass
                boss = find_boss()
                boss_hp = getattr(boss, 'hp', None) if boss else None
                boss_fp = getattr(boss, 'force_points', None) if boss else None
                alive_enemies = [e for e in (getattr(gm, 'enemies', []) or []) if getattr(e, 'hp', 0) > 0]
                print(f"Turn {t}: boss_hp={boss_hp} boss_fp={boss_fp} alive_enemies={len(alive_enemies)} recent_msgs={msgs}")

            # early exit if boss dead or player dead
            if boss and getattr(boss, 'hp', 0) <= 0:
                print(f"Boss defeated on turn {t}.")
                break
            if getattr(gm.player, 'hp', 1) <= 0:
                print(f"Player died on turn {t}.")
                break

        print("Finished simulation. Final state:")
        boss = find_boss()
        print("Boss present:", bool(boss))
        if boss:
            print("Boss hp:", getattr(boss, 'hp', None), "force:", getattr(boss, 'force_points', None), "stress:", getattr(boss, 'stress', None))
        print("Player hp:", getattr(gm.player, 'hp', None), "stress:", getattr(gm.player, 'stress', None))
        try:
            print("Recent messages:", getattr(gm.ui, 'messages', None).messages[-12:])
        except Exception:
            pass

    except Exception:
        print("Force inquisitor smoke failed:")
        traceback.print_exc()

if __name__ == '__main__':
    main(200)
