"""Headless smoke tests for Jedi Fugitive subsystems.
Run from project root. This script is non-interactive and prints short results.
"""
import sys
from pathlib import Path
proj_root = Path(__file__).resolve().parents[1]
src = proj_root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

import traceback

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game import projectiles, equipment, map_features
from jedi_fugitive.game import force_abilities as fa_mod
from jedi_fugitive.items import consumables

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
        # ignore printing
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
        if self._inputs:
            v = self._inputs.pop(0)
            # if stored as str, convert to ord
            if isinstance(v, str) and len(v) == 1:
                return ord(v)
            return v
        return -1


def run():
    print("Starting headless smoke tests...")
    try:
        dummy = DummyStdScr(inputs=['1'])
        gm = GameManager(dummy)
        try:
            gm.initialize()
            gm.generate_world()
        except Exception:
            print("Initialize/generate_world failed (continuing):")
            traceback.print_exc()

        # check force abilities and consumables
        try:
            print("FORCE_ABILITIES:", [type(a).__name__ for a in fa_mod.FORCE_ABILITIES])
        except Exception:
            print("Failed to import FORCE_ABILITIES:")
            traceback.print_exc()
        try:
            print("CONSUMABLES tokens:", [i['token'] for i in consumables.ITEM_DEFS])
        except Exception:
            print("Failed to read ITEM_DEFS:")
            traceback.print_exc()

        # simulate pickup by directly adding an item to inventory
        try:
            med = consumables.ITEM_DEFS[0]
            print("Adding medkit to inventory:", med['name'])
            gm.player.inventory.append({
                'token': med['token'], 'name': med['name'], 'effect': med['effect']
            })
            print("HP before:", gm.player.hp)
            # call use_item which will consume first item (DummyStdScr returns '1')
            equipment.use_item(gm)
            print("HP after:", gm.player.hp)
            print("Inventory now:", gm.player.inventory)
            if getattr(gm.ui, 'messages', None):
                print("Recent messages:", getattr(gm.ui.messages, 'messages', [])[-3:])
        except Exception:
            print("Consumable use failed:")
            traceback.print_exc()

        # projectile test
        try:
            sx, sy = gm.player.x, gm.player.y
            tx, ty = sx + 5, sy
            print(f"Spawning blaster from {(sx,sy)} to {(tx,ty)}")
            p = projectiles.spawn_blaster(gm, sx, sy, tx, ty, damage=5, owner=gm.player, max_range=10)
            print("Projectile spawned:", p)
            for i in range(4):
                projectiles.advance_projectiles(gm)
                print("Tick", i+1, "projectiles:", [(pr.x, pr.y, pr.alive, pr.range_remaining) for pr in getattr(gm, 'projectiles', [])])
        except Exception:
            print("Projectile test failed:")
            traceback.print_exc()

        # Level-up test: grant large XP to trigger level_up and verify messages/stats
        try:
            before_lvl = getattr(gm.player, 'level', 1)
            print('Granting 1000 XP to force level up...')
            gm.player.gain_xp(1000)
            print('Level after:', gm.player.level, 'HP/Max:', gm.player.hp, '/', gm.player.max_hp)
            try:
                print('Recent msg:', getattr(gm.ui.messages, 'messages', [])[-3:])
            except Exception:
                pass
        except Exception:
            print('Level-up test failed:')
            traceback.print_exc()

        # tomb/floor test: attempt to enter a tomb via map_features.enter_tomb
        try:
            ok = map_features.enter_tomb(gm)
            print("enter_tomb() returned:", ok)
            if ok:
                print("Tomb floors:", len(getattr(gm, 'tomb_levels', [])))
                # try change_floor if more than 1
                if len(getattr(gm, 'tomb_levels', [])) > 1:
                    before = getattr(gm, 'tomb_floor', None)
                    changed = gm.change_floor(1)
                    print("change_floor(1) ->", changed, "now floor", getattr(gm, 'tomb_floor', None), "was", before)
                # simulate several enemy turns to surface taunts
                try:
                    print("Simulating 8 enemy turns to observe taunts...")
                    for t in range(8):
                        gm.turn_count = getattr(gm, 'turn_count', 0) + 1
                        try:
                            gm.process_enemies()
                        except Exception:
                            traceback.print_exc()
                        # print recent messages
                        try:
                            msgs = getattr(gm.ui.messages, 'messages', [])
                            if msgs:
                                print(f"Turn {gm.turn_count} recent msg:", msgs[-1])
                        except Exception:
                            pass
                except Exception:
                    traceback.print_exc()
        except Exception:
            print("Tomb test failed:")
            traceback.print_exc()

    except Exception:
        print("Headless smoke harness failed:")
        traceback.print_exc()

if __name__ == '__main__':
    run()
