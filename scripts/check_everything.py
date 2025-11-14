"""
Sanity check for the project:
 - compile all Python files under src
 - try importing key modules
 - instantiate GameManager with a dummy stdscr and run minimal lifecycle:
   initialize(), generate_world(), compute_visibility(), draw()
This runs without requiring a real terminal curses session.
"""
import compileall
import importlib
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# Ensure local src is on sys.path so imports like 'jedi_fugitive.*' work when running the script directly.
try:
    spath = str(SRC.resolve())
    if spath not in sys.path:
        sys.path.insert(0, spath)
        print(f"Inserted {spath} into sys.path for local imports")
except Exception:
    pass

def compile_src():
    print("1) compileall src...")
    ok = compileall.compile_dir(str(SRC), force=False, quiet=1)
    print("  compileall ok:", ok)
    return ok

def try_imports(mods):
    results = {}
    for m in mods:
        try:
            importlib.invalidate_caches()
            mod = importlib.import_module(m)
            print(f"  OK import: {m}")
            results[m] = (True, None)
        except Exception as e:
            print(f"  FAIL import: {m}")
            traceback.print_exc(limit=10)
            results[m] = (False, e)
    return results

class DummyWin:
    """Minimal window shim implementing the small subset used by SILQUI / ui_renderer."""
    def __init__(self, h=24, w=80, y=0, x=0):
        self._h = h; self._w = w; self._y = y; self._x = x
    def getmaxyx(self): return (self._h, self._w)
    def subwin(self, h, w, y, x): return DummyWin(h or self._h, w or self._w, y, x)
    def clear(self): pass
    def erase(self): pass
    def border(self): pass
    def addstr(self, *args, **kwargs): pass
    def addnstr(self, *args, **kwargs): pass
    def refresh(self): pass
    def noutrefresh(self): pass
    def resize(self, h, w): self._h = h; self._w = w
    def mvwin(self, y, x): self._y = y; self._x = x
    def move(self, y, x): pass
    def clrtoeol(self): pass
    def getch(self): return -1

class DummyStdScr(DummyWin):
    def __init__(self):
        super().__init__(h=24, w=80, y=0, x=0)
    def subwin(self, h, w, y, x):
        return DummyWin(h, w, y, x)

def instantiate_game_manager():
    try:
        # import the GameManager class
        gm_mod = importlib.import_module("jedi_fugitive.game.game_manager")
        GM = getattr(gm_mod, "GameManager", None)
        if GM is None:
            print("GameManager not found in module.")
            return False
        dummy = DummyStdScr()
        # instantiate manager
        g = GM(dummy)
        print("  GameManager instantiated.")
        # run minimal lifecycle
        try:
            g.initialize()
            print("  initialize() OK")
        except Exception:
            print("  initialize() FAILED")
            traceback.print_exc(limit=10)
            return False
        try:
            g.generate_world()
            print("  generate_world() OK")
        except Exception:
            print("  generate_world() FAILED")
            traceback.print_exc(limit=10)
            return False
        try:
            g.compute_visibility()
            print("  compute_visibility() OK")
        except Exception:
            print("  compute_visibility() FAILED")
            traceback.print_exc(limit=10)
            return False
        try:
            g.draw()
            print("  draw() OK")
        except Exception:
            print("  draw() FAILED")
            traceback.print_exc(limit=10)
            return False
        return True
    except Exception:
        print("Failed to instantiate GameManager:")
        traceback.print_exc(limit=20)
        return False

def main():
    print("Project root:", ROOT)
    ok = compile_src()
    if not ok:
        print("Compile step failed — fix syntax errors first.")
    modules = [
        "jedi_fugitive.ui.silq_ui",
        "jedi_fugitive.game.game_manager",
        "jedi_fugitive.game.ui_renderer",
        "jedi_fugitive.game.enemy",
        "jedi_fugitive.game.projectiles",
        "jedi_fugitive.game.map_features",
        "jedi_fugitive.game.player",
        "jedi_fugitive.game.input_handler",
        "jedi_fugitive.game.combat",
    ]
    print("\n2) Import checks")
    results = try_imports(modules)
    if not all(r[0] for r in results.values()):
        print("One or more imports failed. Fix the tracebacks above.")
    else:
        print("All selected imports OK.")

    print("\n3) Instantiate GameManager headlessly and run minimal lifecycle")
    ok2 = instantiate_game_manager()
    print("\nSummary: GameManager lifecycle ok:", ok2)
    if not ok or not ok2:
        print("\nIf failures occurred, paste the errors here and I will create precise patches.")
    else:
        print("\nBasic checks passed. Try running in terminal: PYTHONPATH=src python -m jedi_fugitive.main")

if __name__ == "__main__":
    main()