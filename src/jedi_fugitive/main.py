import argparse
import sys
import traceback
import os


def _parse_args(argv=None):
    p = argparse.ArgumentParser(prog="jedi-fugitive", description="Jedi Fugitive: Echoes of the Fallen")
    p.add_argument("--terminal", action="store_true",
                   help="classic curses UI in the terminal instead of the graphical window")
    p.add_argument("--realtime", action="store_true",
                   help="start in real-time mode (graphical UI only; F2 toggles in game)")
    p.add_argument("--tick-ms", type=int, default=200,
                   help="real-time world tick length in milliseconds (default: 200)")
    p.add_argument("--fullscreen", action="store_true", help="start fullscreen (F11 toggles)")
    p.add_argument("--no-intro", action="store_true", help="skip the crash cinematic")
    p.add_argument("--size", default=None, help="window size, e.g. 1600x960")
    p.add_argument("--world-size", default="large", choices=["small", "normal", "large", "huge"],
                   help="overworld size (default: large, 440x300 tiles)")
    # PyInstaller/macOS may pass extra arguments (e.g. -psn_*); ignore them
    args, _unknown = p.parse_known_args(argv)
    return args


def _gui_available():
    try:
        import pygame  # noqa: F401
    except Exception:
        return False
    if sys.platform.startswith("linux") or "bsd" in sys.platform:
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or os.environ.get("SDL_VIDEODRIVER"))
    return True


def _main_gui(args):
    """Graphical front-end: pygame window, curses calls served by the shim."""
    from jedi_fugitive.gfx import pgcurses
    sys.modules["curses"] = pgcurses
    from jedi_fugitive.gfx.app import GfxApp
    size = None
    if args.size:
        try:
            w, h = args.size.lower().split("x")
            size = (int(w), int(h))
        except Exception:
            size = None
    app = GfxApp(size=size, fullscreen=args.fullscreen)
    app.install_console_capture()
    try:
        from jedi_fugitive.game.game_manager import GameManager
        from jedi_fugitive.game.sith_codex import get_random_loading_message
        GameManager.show_splash_static(100)
        input("Press Enter to begin your journey...")
        print(get_random_loading_message())
        gm = GameManager(app.stdscr)
        gm.world_size = args.world_size
        gm.tick_seconds = max(0.05, args.tick_ms / 1000.0)
        # the crash cinematic plays while the world is generated in the background
        intro = None
        if not args.no_intro:
            from jedi_fugitive.gfx.intro import Intro
            intro = Intro(app)
        app.run_loading(lambda: (gm.initialize(), gm.generate_world()), intro=intro)
        if args.realtime:
            gm.set_realtime(True)
        gm.run(skip_init=True)
        if getattr(gm, "death", False):
            gm.show_death_stats()
        elif getattr(gm, "victory", False):
            gm.show_victory_stats()
    except SystemExit:
        pass
    finally:
        app.shutdown()


_WORLD_SIZE = "large"


def _curses_main(stdscr):
    from jedi_fugitive.game.game_manager import GameManager
    # Existing initialization entrypoint expected by the project
    try:
        gm = GameManager(stdscr)
        gm.world_size = _WORLD_SIZE
        gm.run()
        # Return the game manager so we can check death/victory state
        return gm
    except Exception as e:
        # Try to ensure curses cleans up
        try:
            import curses
            curses.endwin()
        except Exception:
            pass
        raise

def main(argv=None):
    args = _parse_args(argv)
    if not args.terminal and _gui_available():
        return _main_gui(args)
    if args.realtime:
        sys.stderr.write("Real-time mode needs the graphical UI (pygame); starting turn-based.\n")
    return _main_terminal(args.world_size)


def _main_terminal(world_size="large"):
    global _WORLD_SIZE
    _WORLD_SIZE = world_size
    import curses
    from jedi_fugitive.game.game_manager import GameManager
    from jedi_fugitive.game.sith_codex import get_random_loading_message
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║        JEDI FUGITIVE: ECHOES OF THE FALLEN               ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    try:
        # Show splash before curses starts
        try:
            term_size = os.get_terminal_size()
            term_w = term_size.columns
            GameManager.show_splash_static(term_w)
            sys.stdout.flush()  # Ensure splash is visible
            # Wait for user to press Enter before starting curses
            input("\nPress Enter to begin your journey...")
        except Exception as e:
            print(f"⚠ Splash screen initialization issue: {e}")
            sys.stdout.flush()
        print(get_random_loading_message())
        # Primary: run under curses wrapper (requires a real terminal)
        gm = curses.wrapper(_curses_main)
        
        # After curses exits, show death or victory screen if applicable
        if gm and hasattr(gm, 'death') and gm.death:
            sys.stdout.flush()
            gm.show_death_stats()
        elif gm and hasattr(gm, 'victory') and gm.victory:
            sys.stdout.flush()
            gm.show_victory_stats()
    except curses.error as e:
        sys.stderr.write("Curses initialization failed: " + repr(e) + "\n")
        sys.stderr.write("Make sure you run the game in a real terminal (Terminal.app / iTerm) and TERM is set, e.g.:\n")
        sys.stderr.write("  export TERM=xterm-256color\n")
        sys.stderr.write("Or configure your VS Code launch config to use an external terminal.\n")
        sys.stderr.write("Attempting a headless initialization for diagnostics...\n")
        # Headless diagnostic fallback: instantiate GameManager with a minimal dummy stdscr
        try:
            class DummyStdScr:
                def __init__(self, h=24, w=80):
                    self._h = h; self._w = w
                def getmaxyx(self): return (self._h, self._w)
                def subwin(self, h, w, y, x): return self
                def clear(self): pass
                def erase(self): pass
                def border(self): pass
                def addstr(self, *args, **kwargs): pass
                def addnstr(self, *args, **kwargs): pass
                def refresh(self): pass
                def noutrefresh(self): pass
                def resize(self, h, w): self._h = h; self._w = w
                def mvwin(self, y, x): pass
                def move(self, y, x): pass
                def clrtoeol(self): pass
                def getch(self): return -1

            dummy = DummyStdScr()
            print(get_random_loading_message())
            gm = GameManager(dummy)
            try:
                print(get_random_loading_message())
                gm.initialize()
                print(get_random_loading_message())
                gm.generate_world()
                print(get_random_loading_message())
                gm.compute_visibility()
                print(get_random_loading_message())
                gm.draw()
                print("✓ Headless initialization successful")
                sys.stderr.write("Headless initialization successful. The UI draw completed without a TTY.\n")
                sys.stderr.write("Run in a proper terminal to play the game.\n")
            except Exception as e:
                print(f"⚠ Headless initialization encountered an issue: {e}")
                sys.stderr.write("Headless initialization failed:\n")
                traceback.print_exc(limit=20)
        except Exception as e:
            print(f"⚠ Error during diagnostics: {e}")
            sys.stderr.write("Unexpected error while attempting headless diagnostics:\n")
            traceback.print_exc(limit=20)
    except Exception as e:
        print(f"⚠ Unexpected error: {e}")
        # Any other errors: ensure curses cleaned up, then print traceback
        try:
            curses.endwin()
        except Exception:
            pass
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()