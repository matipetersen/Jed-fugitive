import curses
import sys
import traceback
import os

from jedi_fugitive.game.game_manager import GameManager

def _curses_main(stdscr):
    # Existing initialization entrypoint expected by the project
    try:
        gm = GameManager(stdscr)
        gm.run()
        # Return the game manager so we can check death/victory state
        return gm
    except Exception as e:
        # Try to ensure curses cleans up
        try:
            curses.endwin()
        except Exception:
            pass
        raise

def main():
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