"""Minimal demo that spawns a small Sith encounter and runs a few headless turns.

Usage: PYTHONPATH=src python3 scripts/demo_sith_encounter.py
"""
import sys
from pathlib import Path
proj_root = Path(__file__).resolve().parents[1]
src = proj_root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

import traceback
import random

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game import enemies_sith as sith


class DummyStdScr:
    def __init__(self, h=24, w=80):
        self._h = h; self._w = w
    def getmaxyx(self):
        return (self._h, self._w)
    def subwin(self, h, w, y, x): return self
    def clear(self): pass
    def erase(self): pass
    def border(self): pass
    def addstr(self, *a, **k): pass
    def refresh(self): pass
    def getch(self): return -1


def run_demo(turns: int = 8):
    print("Starting Sith encounter demo...")
    dummy = DummyStdScr()
    gm = GameManager(dummy)
    try:
        gm.initialize()
    except Exception:
        traceback.print_exc()

    # Ensure a world/map exists so POIs and tiles can be placed for the demo
    try:
        gm.generate_world()
    except Exception:
        pass

    # place player roughly centered
    try:
        gm.player.x = 20; gm.player.y = 10
    except Exception:
        pass

    # spawn a small party around the player
    party = []
    try:
        party.append(sith.create_sith_acolyte(level=1, x=gm.player.x+3, y=gm.player.y))
        party.append(sith.create_sith_warrior(level=2, x=gm.player.x-3, y=gm.player.y))
        party.append(sith.create_sith_sorcerer(level=2, x=gm.player.x, y=gm.player.y+4))
        party.append(sith.create_sith_assassin(level=2, x=gm.player.x, y=gm.player.y-4))
    except Exception:
        traceback.print_exc()

    for p in party:
        try:
            gm.enemies.append(p)
        except Exception:
            pass

    # place a lore POI adjacent to the player so we can demo codex discovery
    try:
        px, py = gm.player.x, gm.player.y
        tx, ty = px + 1, py
        # ensure map big enough
        if 0 <= ty < len(gm.game_map) and 0 <= tx < len(gm.game_map[0]):
            try:
                gm.game_map[ty][tx] = 'l'
            except Exception:
                pass
            try:
                # ensure map_lore exists and mark the lore entry for level 0 (surface)
                if not hasattr(gm, 'map_lore') or not isinstance(getattr(gm, 'map_lore', None), dict):
                    gm.map_lore = {}
                gm.map_lore[(0, tx, ty)] = ('sith_philosophy', 'code')
            except Exception:
                pass
            # move player onto the lore tile to trigger discovery
            try:
                gm.player.x = tx; gm.player.y = ty
                gm.process_sith_lore_discovery(gm.player)
            except Exception:
                pass
    except Exception:
        pass

    # run several turns of enemy processing to observe behavior
    for t in range(turns):
        gm.turn_count = getattr(gm, 'turn_count', 0) + 1
        print(f"--- Turn {gm.turn_count} ---")
        try:
            gm.process_enemies()
        except Exception:
            traceback.print_exc()
        # print recent messages if any
        try:
            msgs = getattr(gm.ui.messages, 'messages', [])
            if msgs:
                print("MSG:", msgs[-3:])
        except Exception:
            pass
        # print enemy positions and HP
        for e in gm.enemies:
            try:
                print(f"{e.name} @{getattr(e,'x',None)},{getattr(e,'y',None)} hp={getattr(e,'hp',None)}")
            except Exception:
                pass

    print("Demo finished.")

if __name__ == '__main__':
    run_demo(8)
