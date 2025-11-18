import curses
import sys
import traceback
import os

from jedi_fugitive.game.game_manager import GameManager

def _curses_main(stdscr, load_save=False):
    # Existing initialization entrypoint expected by the project
    try:
        gm = GameManager(stdscr)
        
        # Load save if requested
        if load_save:
            try:
                from jedi_fugitive.game.save_system import load_game, apply_save_data, get_autosave_path
                save_data = load_game(get_autosave_path())
                if save_data and apply_save_data(gm, save_data):
                    # Save was loaded successfully
                    if hasattr(gm, 'ui') and hasattr(gm.ui, 'messages'):
                        gm.ui.messages.add("Game loaded! Welcome back, wanderer.")
                else:
                    # Load failed, start new game
                    if hasattr(gm, 'ui') and hasattr(gm.ui, 'messages'):
                        gm.ui.messages.add("Failed to load save. Starting new game...")
            except Exception as e:
                # Load failed, start new game
                if hasattr(gm, 'ui') and hasattr(gm.ui, 'messages'):
                    gm.ui.messages.add(f"Load error: {e}. Starting new game...")
        
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
    from jedi_fugitive.game.save_system import get_autosave_path, list_saves
    
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║        JEDI FUGITIVE: ECHOES OF THE FALLEN               ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    
    # Check for existing save files
    load_save = False
    try:
        saves = list_saves()
        if saves:
            print("\n═══ SAVED GAMES FOUND ═══")
            for i, save in enumerate(saves, 1):
                timestamp = save.get('timestamp', 'Unknown time')
                level = save.get('level', 1)
                turn = save.get('turn', 0)
                print(f"{i}. {save['name']} - Level {level}, Turn {turn}")
                print(f"   Saved: {timestamp}")
            
            print("\n[C] Continue from autosave")
            print("[N] Start new game")
            print("[Q] Quit")
            
            choice = input("\nYour choice: ").strip().upper()
            if choice == 'C':
                load_save = True
            elif choice == 'Q':
                print("Farewell, wanderer.")
                sys.exit(0)
    except Exception as e:
        print(f"⚠ Error checking for saves: {e}")
    
    # Initialize crash logger
    try:
        from jedi_fugitive.utils.crash_logger import get_logger
        logger = get_logger()
        logger.log_info("Game started")
    except Exception as e:
        print(f"⚠ Could not initialize logger: {e}")
        logger = None
    
    # Initialize game stats tracker
    try:
        from jedi_fugitive.utils.game_stats import get_game_stats
        game_stats = get_game_stats()
        run_number = game_stats.increment_runs()
        print(f"\n🎮 Game Run #{run_number}")
        if run_number > 1:
            print(f"   Total Victories: {game_stats.get_total_victories()}")
            print(f"   Total Deaths: {game_stats.get_total_deaths()}")
            print(f"   Win Rate: {game_stats.get_win_rate():.1f}%")
    except Exception as e:
        print(f"⚠ Could not initialize stats tracker: {e}")
        game_stats = None
    
    play_again = True
    while play_again:
        try:
            # Show splash before curses starts
            try:
                term_size = os.get_terminal_size()
                term_w = term_size.columns
                GameManager.show_splash_static(term_w)
                sys.stdout.flush()  # Ensure splash is visible
                # Wait for user to press Enter before starting curses
                if not load_save:
                    input("\nPress Enter to begin your journey...")
                else:
                    input("\nPress Enter to continue your journey...")
            except Exception as e:
                print(f"⚠ Splash screen initialization issue: {e}")
                sys.stdout.flush()
            print(get_random_loading_message())
            
            # Primary: run under curses wrapper (requires a real terminal)
            gm = curses.wrapper(_curses_main, load_save)
            
            # After curses exits, show death or victory screen if applicable
            restart = False
            if gm and hasattr(gm, 'death') and gm.death:
                sys.stdout.flush()
                restart = gm.show_death_stats()
            elif gm and hasattr(gm, 'victory') and gm.victory:
                sys.stdout.flush()
                restart = gm.show_victory_stats()
            # If neither death nor victory, user quit normally - don't restart
            elif gm and hasattr(gm, 'running') and not gm.running:
                # User quit with 'q' - exit cleanly
                restart = False
            
            # Check if user wants to play again
            play_again = restart
            load_save = False  # Always start fresh game on restart
            
        except curses.error as e:
            if logger:
                logger.log_error("CURSES_ERROR", "Curses initialization failed", e)
            sys.stderr.write("Curses initialization failed: " + repr(e) + "\n")
            sys.stderr.write("Make sure you run the game in a real terminal (Terminal.app / iTerm) and TERM is set, e.g.:\n")
            sys.stderr.write("  export TERM=xterm-256color\n")
            sys.stderr.write("Or configure your VS Code launch config to use an external terminal.\n")
            sys.stderr.write("Attempting a headless initialization for diagnostics...\n")
            play_again = False
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
        except KeyboardInterrupt:
            print("\n\nGame interrupted. Farewell, wanderer.")
            play_again = False
        except Exception as e:
            if logger:
                logger.log_error("CRASH", "Unexpected error in main game loop", e)
            print(f"⚠ Unexpected error: {e}")
            # Any other errors: ensure curses cleaned up, then print traceback
            try:
                curses.endwin()
            except Exception:
                pass
            traceback.print_exc()
            play_again = False
    
    # Close logger
    if logger:
        logger.close()

if __name__ == "__main__":
    main()