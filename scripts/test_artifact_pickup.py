"""Test artifact pickup wiring.

Run with: PYTHONPATH=src python3 scripts/test_artifact_pickup.py
"""
import sys
from pathlib import Path
proj_root = Path(__file__).resolve().parents[1]
src = proj_root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game import equipment

class DummyStdScr:
    def getmaxyx(self):
        return (24, 80)
    def subwin(self, h, w, y, x): return self
    def clear(self): pass
    def erase(self): pass
    def border(self): pass
    def addstr(self, *a, **k): pass
    def refresh(self): pass
    def getch(self): return -1


def run_test():
    print("Starting artifact pickup test...")
    g = GameManager(DummyStdScr())
    g.initialize()
    g.generate_world()
    # place player
    g.player.x = 10
    g.player.y = 6
    # place an artifact tile next to player
    from jedi_fugitive.game.level import Display
    tx, ty = g.player.x + 1, g.player.y
    if 0 <= ty < len(g.game_map) and 0 <= tx < len(g.game_map[0]):
        g.game_map[ty][tx] = Display.ARTIFACT
    # call pick_up (player needs to be on tile)
    g.player.x, g.player.y = tx, ty
    equipment.pick_up(g)
    print("Inventory:", g.player.inventory)
    try:
        print("Codex discovered entries:", getattr(g.sith_codex, 'discovered_entries', None))
    except Exception:
        pass
    print("Force points:", getattr(g.player, 'force_points', None))
    print("Stress:", getattr(g.player, 'stress', None))

if __name__ == '__main__':
    run_test()
