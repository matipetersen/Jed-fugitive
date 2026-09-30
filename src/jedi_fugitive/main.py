# Global for passing load_save to _curses_main
_LOAD_SAVE_FOR_CURSES = False

import argparse
import shutil
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
        # Import GameManager and save system only after curses is initialized
        from jedi_fugitive.game.game_manager import GameManager
        gm = GameManager(stdscr)
        gm.world_size = _WORLD_SIZE

        # Load save if requested
        global _LOAD_SAVE_FOR_CURSES
        if _LOAD_SAVE_FOR_CURSES:
            try:
                from jedi_fugitive.game.save_system import load_game, apply_save_data, get_autosave_path
                save_data = load_game(get_autosave_path())
                if save_data and apply_save_data(gm, save_data):
                    if hasattr(gm, 'ui') and hasattr(gm.ui, 'messages'):
                        gm.ui.messages.add("Game loaded! Welcome back, wanderer.")
                else:
                    if hasattr(gm, 'ui') and hasattr(gm.ui, 'messages'):
                        gm.ui.messages.add("Failed to load save. Starting new game...")
            except Exception as e:
                if hasattr(gm, 'ui') and hasattr(gm.ui, 'messages'):
                    gm.ui.messages.add(f"Load error: {e}. Starting new game...")

        gm.run()
        # Return the game manager so we can check death/victory state
        return gm
    except Exception as e:
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
    from jedi_fugitive.game.save_system import get_autosave_path, list_saves
    
    # === INITIAL SPLASH SCREEN (printed to terminal before game starts) ===
    # Get terminal width for centering
    try:
        term_width = shutil.get_terminal_size().columns
    except:
        term_width = 80
    
    # Center function for variable-width content
    def center_line(text):
        """Center a line of text in the terminal"""
        if len(text) >= term_width:
            return text
        padding = (term_width - len(text)) // 2
        return ' ' * padding + text
    
    # Box components (already sized)
    box_line = "╔═══════════════════════════════════════════════════════════════════════════╗"
    empty_line = "║                                                                           ║"
    dark_line1 = "║                       ██████╗  █████╗ ██████╗ ██╗  ██╗                   ║"
    dark_line2 = "║                       ██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝                   ║"
    dark_line3 = "║                       ██║  ██║███████║██████╔╝█████╔╝                    ║"
    dark_line4 = "║                       ██║  ██║██╔══██║██╔══██╗██╔═██╗                    ║"
    dark_line5 = "║                       ██████╔╝██║  ██║██║  ██║██║  ██╗                   ║"
    dark_line6 = "║                       ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝                   ║"
    merid_line1 = "║           ███╗   ███╗███████╗██████╗ ██╗██████╗ ██╗ █████╗ ███╗   ██╗   ║"
    merid_line2 = "║           ████╗ ████║██╔════╝██╔══██╗██║██╔══██╗██║██╔══██╗████╗  ██║   ║"
    merid_line3 = "║           ██╔████╔██║█████╗  ██████╔╝██║██║  ██║██║███████║██╔██╗ ██║   ║"
    merid_line4 = "║           ██║╚██╔╝██║██╔══╝  ██╔══██╗██║██║  ██║██║██╔══██║██║╚██╗██║   ║"
    merid_line5 = "║           ██║ ╚═╝ ██║███████╗██║  ██║██║██████╔╝██║██║  ██║██║ ╚████║   ║"
    merid_line6 = "║           ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ║"
    box_bottom = "╚═══════════════════════════════════════════════════════════════════════════╝"
    
    print("\n" * 3)
    print(center_line("="*80))
    print()
    print(center_line(box_line))
    print(center_line(empty_line))
    print(center_line(dark_line1))
    print(center_line(dark_line2))
    print(center_line(dark_line3))
    print(center_line(dark_line4))
    print(center_line(dark_line5))
    print(center_line(dark_line6))
    print(center_line(empty_line))
    print(center_line(merid_line1))
    print(center_line(merid_line2))
    print(center_line(merid_line3))
    print(center_line(merid_line4))
    print(center_line(merid_line5))
    print(center_line(merid_line6))
    print(center_line(empty_line))
    print(center_line(box_bottom))
    print()
    print(center_line("="*80))
    print()
    print(center_line("═══════════════════════════════════════════════════════════════════════"))
    print()
    print(center_line("Your transport burns in the wastes of Korriban, the ancient"))
    print(center_line("Sith homeworld. The crash site smolders behind you - your"))
    print(center_line("only hope of escape reduced to twisted metal and ash."))
    print()
    print(center_line("Towering tombs pierce the crimson sky. Sith Lords long dead"))
    print(center_line("whisper through the Force, their power seeping into the very"))
    print(center_line("stones beneath your feet. The dark side is strong here..."))
    print()
    print(center_line("YOUR MISSION: Recover stolen Jedi holocrons from the tombs"))
    print(center_line("YOUR CHALLENGE: Resist the corruption gnawing at your soul"))
    print(center_line("YOUR FATE: Escape with your life... and your light intact"))
    print()
    print(center_line("═══════════════════════════════════════════════════════════════════════"))
    print()
    print(center_line("\"The dark places of the galaxy hold many secrets -\""))
    print(center_line("\"treasures of power, and terrible truths. Few who\""))
    print(center_line("\"seek them return unchanged.\"  - Master Kreia"))
    print()
    print(center_line("═══════════════════════════════════════════════════════════════════════"))
    print()
    print(center_line("Press [ENTER] to start your journey..."))
    print()
    
    # Wait for user to read splash screen
    input()

    # Check for save files and allow selection
    load_save = False
    try:
        saves = list_saves()
        if saves:
            print("\n>>> ECHOES FROM THE PAST <<<")
            for i, save in enumerate(saves, 1):
                timestamp = save.get('timestamp', 'Unknown time')
                level = save.get('level', 1)
                turn = save.get('turn', 0)
                print(f"> {i}. {save['name']} - Depth {level}, Turn {turn}")
                print(f"   Recorded: {timestamp}")
            
            print("\n[C] Continue your dark journey")
            print("⭐ [N] Begin anew - face your destiny")
            print("💀 [Q] Abandon hope, return to the void")
            
            choice = input("\n🌟 Choose your path, fallen Jedi: ").strip().upper()
            if choice == 'C':
                load_save = True
            elif choice == 'Q':
                print("⚡ The darkness claims another soul. May the Force be with you... ⚡")
                sys.exit(0)
        else:
            # No saves - just wait for enter
            pass
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
        print(f"\n💫 Force Echo #{run_number}")
        if run_number > 1:
            print(f"   ⭐ Souls Redeemed: {game_stats.get_total_victories()}")
            print(f"   💀 Fallen to Darkness: {game_stats.get_total_deaths()}")
            print(f"   ⚖️ Balance Ratio: {game_stats.get_win_rate():.1f}%")
            print(f"   ⚔️ Total Kills: {game_stats.get_total_kills()}")
            print(f"   📊 K/D Ratio: {game_stats.get_kill_death_ratio():.2f}")
            if game_stats.get_best_win_streak() > 0:
                print(f"   🔥 Best Streak: {game_stats.get_best_win_streak()}")
    except Exception as e:
        print(f"⚠ Could not initialize stats tracker: {e}")
        game_stats = None
    
    play_again = True
    while play_again:
        try:
            # Show loading message
            print()
            print(get_random_loading_message())
            sys.stdout.flush()

            # Primary: run under curses wrapper (requires a real terminal)
            try:
                global _LOAD_SAVE_FOR_CURSES
                _LOAD_SAVE_FOR_CURSES = load_save
                gm = curses.wrapper(_curses_main)
            except Exception as e:
                print(f"[DEBUG] Exception in curses.wrapper: {e}")
                import traceback
                traceback.print_exc()
                raise

            # Ensure curses is properly ended before showing ending screens
            try:
                curses.endwin()
            except Exception:
                pass
            
            # After curses exits, show death or victory screen if applicable
            restart = False
            if gm and hasattr(gm, 'death') and gm.death:
                restart = gm.show_death_stats()
            elif gm and hasattr(gm, 'victory') and gm.victory:
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
            print("\n" + "="*60)
            print("⚠️  TERMINAL INCOMPATIBILITY DETECTED")
            print("="*60)
            print("\nThis game requires a proper terminal with curses support.")
            print("\n❌ Current environment cannot display the game interface.")
            print("\n✅ To play the game, run it in:")
            print("   • macOS: Terminal.app or iTerm2")
            print("   • Linux: gnome-terminal, konsole, xterm")
            print("   • Windows: Windows Terminal or WSL")
            print("\n📝 Quick fix for macOS/Linux:")
            print("   export TERM=xterm-256color")
            print("   python -m jedi_fugitive.main")
            print("\n💡 VS Code users: Configure launch.json to use external terminal")
            print("="*60 + "\n")
            play_again = False
            # Skip headless diagnostic since it confuses users
            if logger:
                logger.close()
            return

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