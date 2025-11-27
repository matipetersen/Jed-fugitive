import curses
import os
import sys
import datetime
from typing import Optional, Tuple
import pkgutil
import importlib
import random
import traceback

from jedi_fugitive.ui.silq_ui import SILQUI
from jedi_fugitive.utils.crash_logger import get_logger, log_error, log_info, log_game_event
from jedi_fugitive.game.player import Player
from jedi_fugitive.game import projectiles, force_abilities, map_features, input_handler, ui_renderer, equipment
from jedi_fugitive.game.enemy import Enemy, EnemyType, process_enemies as enemy_process_enemies
from jedi_fugitive.game.personality import EnemyPersonality, ENEMY_TAUNTS
from jedi_fugitive.game.level import generate_crash_site, generate_dungeon_level, Display
from jedi_fugitive.game import atmosphere
from jedi_fugitive.game.atmospheric_events import AtmosphericEventManager, should_trigger_environmental_hazard, trigger_environmental_hazard
from jedi_fugitive.game.fauna_system import FaunaManager
from jedi_fugitive.ui.dialog import DialogueSystem, UIMessageBuffer
from jedi_fugitive.config import MAP_RATIO_W, MAP_RATIO_H, STATS_RATIO_W, DIFFICULTY_MULTIPLIER, MAP_SCALE, DEPTH_DIFFICULTY_RATE
from jedi_fugitive.game.combat import player_attack, calculate_hit
from jedi_fugitive.game import abilities, map_features as mf
from jedi_fugitive.game.sith_codex import SithCodex, populate_canon, populate_artifacts
from jedi_fugitive.game.save_system import save_game, load_game, apply_save_data, get_autosave_path
from jedi_fugitive.game.npc_encounters import NPCEncounters, NPC

class GameManager:
    def move_environment_object(self, x, y, direction=(0, 0), action="move"):
        """
        Attempt to interact with an object at (x, y) in the given direction.
        action: "move", "break", or "trigger"
        Returns True if an object was affected, False otherwise.
        """
        from jedi_fugitive.game.map_features import get_object_tags
        if not self.game_map or y < 0 or y >= len(self.game_map) or x < 0 or x >= len(self.game_map[0]):
            return False
        obj = self.game_map[y][x]
        tags = get_object_tags(obj)
        dx, dy = direction
        new_x, new_y = x + dx, y + dy
        # Move object if movable
        if action == "move" and tags.get("movable"):
            if (0 <= new_y < len(self.game_map) and 0 <= new_x < len(self.game_map[0])
                    and self.game_map[new_y][new_x] == '.'):
                self.game_map[new_y][new_x] = obj
                self.game_map[y][x] = '.'
                # Optionally trigger environmental effects here
                return True
        # Break object if breakable
        if action == "break" and tags.get("breakable"):
            self.game_map[y][x] = '.'
            # Optionally spawn debris, loot, or effects
            return True
        # Trigger object if triggerable
        if action == "trigger" and tags.get("triggerable"):
            # Example: activate comms, open door, etc.
            # Implement specific triggers as needed
            # For now, just return True to indicate success
            return True
        return False
    """Clean, defensive GameManager suitable to drive the curses UI and other subsystems."""

    def __init__(self, stdscr):
        print("⟳ Initializing Dark Meridian...")
        self.stdscr = stdscr
        # Get term size for later use
        self.term_w = self.stdscr.getmaxyx()[1]
        self.ui = SILQUI(stdscr)
        self.ui.init_colors()
        self.dialog = DialogueSystem()
        self.player = Player(0, 0)
        self.enemies = []
        self.game_map = []
        self.items_on_map = []  # Initialize items list
        self.tomb_entrances = set()
        self.special_dungeons = {}  # Map of (x,y) -> dungeon_data
        self.current_special_dungeon = None  # Current dungeon instance
        self.panels_ready = False
        self.current_depth = 1
        self.current_location = "Crash Site"
        self.turn_count = 0
        self.pending_force_ability = None
        self.target_x = 0
        self.target_y = 0
        self.combat_log = []
        self.last_commands = ""
        self.running = True
        self.show_popups = False
        
        # Atmospheric immersion tracking
        self.last_atmosphere_turn = 0
        self.last_memory_turn = 0
        self.last_vision_turn = 0
        
        # Narrative events tracking
        self.last_journal_turn = 0
        self.last_holocron_turn = 0
        self.last_distress_turn = 0
        self.last_environmental_turn = 0
        
        # Track used events to prevent repetition
        self.used_journals = set()
        self.used_holocrons = set()
        self.used_distress_signals = set()
        self.used_environmental_events = set()
        self.used_random_events = set()
        self.used_fauna_encounters = {}  # Per-biome tracking
        
        # Pending narrative choice
        self.pending_narrative_choice = None  # Stores (event_data, choice_mapping, event_type)
        
        # Biome encounters tracking
        self.visited_biomes = set()
        self.last_encounter_turn = 0
        
        # Initialize player milestone tracking
        if not hasattr(self.player, 'total_kills'):
            self.player.total_kills = 0
        if not hasattr(self.player, 'tombs_discovered'):
            self.player.tombs_discovered = 0
        if not hasattr(self.player, 'max_tomb_depth'):
            self.player.max_tomb_depth = 0
        if not hasattr(self.player, 'artifacts_collected'):
            self.player.artifacts_collected = []

        # Post-game stats
        self.turns = 0
        self.death_cause = None
        self.death_biome = None
        self.death_pos = None
        self.victory = False
        self.death = False

        # FOV/exploration
        self.visible = set()
        self.explored = set()
        # Fog of war toggle (on by default)
        self.fog_of_war = True
        print("✓ Game engine initialized")

        # defaults
        self.player.los_radius = getattr(self.player, "los_radius", 6)
        self.player.los_bonus_turns = getattr(self.player, "los_bonus_turns", 0)

        # containers
        self.projectiles = []
        self.active_effects = {}
        # narrative/quest state
        self.artifacts_needed = 3
        self.artifacts_collected = 0
        self.comms_established = False
        self.ship_pos = None
        
        # Enemy respawn system
        self.last_respawn_turn = 0
        self.respawn_interval = 150  # Respawn enemies every 150 turns (base rate)
        
        # Enhanced NPC quest system
        try:
            from jedi_fugitive.game.npc_quest import QuestManager
            self.quest_manager = QuestManager()
        except ImportError:
            self.quest_manager = None
        
        # Combat narrator for immersive combat descriptions
        try:
            from jedi_fugitive.game.combat_narrator import CombatNarrator
            self.combat_narrator = CombatNarrator()
        except ImportError:
            self.combat_narrator = None
        
        self.npcs_on_map = {}  # Dict mapping (x,y) positions to NPC objects
        self.active_conversations = {}  # Track ongoing NPC conversations
        self.enemies_per_respawn = 1  # Start with 1 enemy per respawn cycle
        self.key_bindings = {}
        self.key_help = {}
        self.last_size = (0, 0)
        self.layout = {}
        self.show_codex = False  # Toggle for Sith Codex display
        
        # Autosave system
        self.autosave_interval = 20  # Save every 20 turns
        self.last_autosave_turn = 0
        
        # Atmospheric events system
        self.atmospheric_manager = AtmosphericEventManager(self)
        
        # Fauna system
        self.fauna_manager = FaunaManager(self)
        
        # default splash/instruction lines exposed to the command/help panel
        self.splash_instructions = [
            "=============== DARK MERIDIAN ===============",
            ">>> The Order has fallen. Your Master is dead. <<<",
            "The meridian between light and dark calls to you.",
            "Will you resist corruption, or embrace your destiny?",
            "================== SURVIVAL ==================",
            "Navigate: ↑↓←→ arrows  hjkl cardinal  ybn/7913 diagonal", 
            "Scavenge: g=pickup  e=equip  u=use  d=drop  x=inspect",
            "Destroy: Walk into enemy  t=grenade  F=blaster",
            "Channel: f=Force abilities  c=compass  m=meditate  R=rituals",
            "Record: j=hero's journal  i=inventory  v=Sith codex  @=character",
            "Creatures: Colored symbols on map = fauna encounters (1-5 to interact)",
            "Wildlife: 1-5=interact with creatures when encountered",
            "System: ?=help  S=save  C=craft  q=quit  ESC=cancel",
            "===============================================",
            "[WARNING] Every choice corrupts or purifies your soul",
            "[ARTIFACTS] 'a'=ABSORB power or 'd'=DESTROY temptation",
            "[FATE] The Force watches. The galaxy bleeds. Your path awaits.",
            "[SYSTEM] Autosave every 20 turns • Manual save: 'S'",
        ]

    def _compute_layout(self) -> Tuple[int,int,int,int,int,int]:
        h, w = self.ui.term_h, self.ui.term_w
        map_w = max(30, int(w * 0.68))
        stats_w = max(20, int(w * 0.20))
        abil_w = max(12, w - map_w - stats_w - 6)
        map_h = max(10, int(h * 0.65))
        message_h = max(3, h - map_h - 4)
        cmd_h = 4
        return map_w, map_h, stats_w, abil_w, message_h, cmd_h

    def initialize(self):
        print("⟳ Initializing game UI...")
        # compute layout and notify UI (robust, minimal)
        try:
            self.ui.term_h, self.ui.term_w = self.stdscr.getmaxyx()
            print(f"✓ Terminal size: {self.ui.term_h}x{self.ui.term_w}")
        except Exception as e:
            print(f"⚠ Could not get terminal size: {e}")
            self.ui.term_h, self.ui.term_w = 40, 140
        
        mw, mh, sw, aw, mhmsg, cmdh = self._compute_layout()
        print(f"⟳ Creating UI layout (map:{mw}x{mh}, stats:{sw}, abilities:{aw})...")
        try:
            self.ui.create_layout(mw, mh, sw, aw, mhmsg, cmdh)
            print("✓ UI layout created")
        except Exception as e:
            print(f"✗ UI layout creation failed: {e}")
            import traceback
            traceback.print_exc()
            pass
        self.panels_ready = True
        print("⟳ Setting up message buffer...")
        # ensure message buffer
        try:
            self.ui.messages = UIMessageBuffer()
            print("✓ Message buffer ready")
            # Display intro with theme
            intro_lines = [
                "╔═══════════════════════════════════════════════════════════╗",
                "║              J E D I   F U G I T I V E                    ║",
                "║                                                           ║",
                "║          A Force-Sensitive Warrior's Journey              ║",
                "╚═══════════════════════════════════════════════════════════╝",
                "",
                "Your ship has crashed. The Force calls to you with both",
                "light and darkness. Every choice shapes your destiny.",
                "",
                "◆ ABSORB artifacts → Gain dark power, increase corruption",
                "◆ DESTROY artifacts → Gain light power, resist darkness",
                "",
                "Your path is yours alone. Will you embrace the shadows,",
                "or walk in the light?",
                "",
                "Press '?' for help | 'j' for journal | 'q' to quit"
            ]
            for line in intro_lines:
                self.ui.messages.add(line)
        except Exception as e:
            print(f"✗ Message buffer setup failed: {e}")
            try:
                self.ui.messages = UIMessageBuffer() if 'UIMessageBuffer' in globals() else None
            except Exception:
                self.ui.messages = None
        print("⟳ Wiring player to UI...")
        # Wire UI/game references into player so player.level_up can present UI prompts
        try:
            if getattr(self, 'player', None) is not None:
                try:
                    setattr(self.player, 'ui', self.ui)
                except Exception: pass
                try:
                    setattr(self.player, 'game', self)
                except Exception: pass
                # ensure player has a _base_stats snapshot for equipment reapplication
                try:
                    self.player._base_stats = {
                        'attack': int(getattr(self.player, 'attack', 0)),
                        'defense': int(getattr(self.player, 'defense', 0)),
                        'evasion': int(getattr(self.player, 'evasion', 0)),
                        'max_hp': int(getattr(self.player, 'max_hp', 0)),
                        'accuracy': int(getattr(self.player, 'accuracy', 0)),
                    }
                except Exception:
                    try:
                        self.player._base_stats = {
                            'attack': 1,
                            'defense': 0,
                            'evasion': 0,
                            'max_hp': 10,
                            'accuracy': 80,
                        }
                    except Exception:
                        self.player._base_stats = {}
        except Exception as e:
            print(f"✗ Player wiring failed: {e}")
            pass
        print("⟳ Setting up starting inventory...")
        # Give the player a training lightsaber and stimpack to start
        try:
            if not hasattr(self.player, 'inventory') or self.player.inventory is None:
                self.player.inventory = []
            
            # Add Training Saber as starting weapon
            from jedi_fugitive.items.weapons import WEAPONS
            try:
                training_saber = None
                for weapon in WEAPONS:
                    if hasattr(weapon, 'name') and weapon.name == 'Training Saber':
                        training_saber = weapon
                        break
                if training_saber:
                    self.player.inventory.append(training_saber)
                    print("✓ Added Training Saber to inventory")
            except Exception as e:
                print(f"⚠ Could not add Training Saber: {e}")
            
            # Add one stimpack
            from jedi_fugitive.items.consumables import ITEM_DEFS
            def _lookup(id_):
                try:
                    for it in ITEM_DEFS:
                        if it.get('id') == id_:
                            return dict(it)
                except Exception:
                    pass
                return {'id': id_, 'name': id_}
            
            try:
                self.player.inventory.append(_lookup('stimpack'))
                print("✓ Added Stimpack to inventory")
            except Exception:
                try: 
                    self.player.inventory.append({'id':'stimpack','name':'Stimpack'})
                except Exception: 
                    pass
            
            print("✓ Starting inventory added (Training Saber, 1 stimpack)")
        except Exception as e:
            print(f"✗ Starting inventory setup failed: {e}")
            pass
        # initial commands hint
        self.last_commands = "Move: h/j/k/l or arrows. g=pickup f=force q=quit"
        print("⟳ Registering key commands...")
        # register inspect key so it appears in the commands/help panel
        try:
            # register a no-op handler; input handling for 'x' is implemented in input_handler
            self.register_command('x', lambda: None, 'Inspect')
        except Exception as e:
            print(f"⚠ Inspect command registration failed: {e}")
            try:
                # best-effort: set help entry directly
                self.key_help['x'] = 'Inspect'
                self.update_command_gui()
            except Exception:
                pass
        # register a scan/Force sense ability (key 'c') to help locate tombs
        try:
            self.register_command('c', lambda: self.perform_scan(), 'Force Sense')
        except Exception as e:
            print(f"⚠ Scan command registration failed: {e}")
            try:
                self.key_help['c'] = 'Force Sense'
                self.update_command_gui()
            except Exception:
                pass
        print("⟳ Initializing Sith Codex...")
        # Initialize Sith Codex (optional subsystem). Safe: if anything fails we keep going.
        try:
            self.sith_codex = SithCodex()
            populate_canon(self.sith_codex)
            populate_artifacts(self.sith_codex)
            print("✓ Sith Codex initialized")
        except Exception as e:
            print(f"⚠ Sith Codex initialization failed: {e}")
            self.sith_codex = None

        print("✓ Game initialization complete")

    def generate_world(self):
        print("⟳ Generating galaxy...")
        logger = get_logger()
        try:
            map_features.generate_world(self)
            # Debug: Check tomb entrance generation
            tomb_count = len(getattr(self, 'tomb_entrances', set()))
            special_count = len(getattr(self, 'surface_special_dungeons', {}))
            print(f"✓ World generated successfully: {tomb_count} tombs, {special_count} special dungeons")
            
            # Write tomb positions to debug file for verification
            try:
                with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                    fh.write(f"World generation complete:\n")
                    fh.write(f"  Tomb entrances: {getattr(self, 'tomb_entrances', set())}\n")
                    fh.write(f"  Special dungeons: {list(getattr(self, 'surface_special_dungeons', {}).keys())}\n")
                    fh.write(f"  Map size: {len(getattr(self, 'game_map', []))}x{len(getattr(self, 'game_map', [[]])[0]) if getattr(self, 'game_map', []) else 0}\n")
                    
                    # VERIFY: Check if 'D' tiles actually exist on map at those positions
                    fh.write(f"\n=== VERIFYING 'D' TILES ON MAP ===\n")
                    tomb_entrances = getattr(self, 'tomb_entrances', set())
                    for tx, ty in list(tomb_entrances)[:10]:
                        try:
                            actual_tile = self.game_map[ty][tx]
                            fh.write(f"  Position ({tx}, {ty}): tile='{actual_tile}' (expected 'D')\n")
                        except Exception as e:
                            fh.write(f"  Position ({tx}, {ty}): ERROR - {e}\n")
                    fh.write(f"=== END VERIFICATION ===\n\n")
            except Exception:
                pass
            
            log_game_event("WORLD_GEN", "World generation completed successfully")
            
            # Generate NPCs with quests after world generation
            if self.quest_manager:
                self.generate_surface_npcs()
                
        except Exception as e:
            print(f"✗ World generation failed: {e}")
            log_error("WORLD_GEN_CRASH", "World generation failed", e, logger.get_game_state_snapshot(self))
            traceback.print_exc()
            try: self.ui.messages.add(f"World generation failed: {e}") 
            except Exception: pass

        # ensure items_on_map exists (map_features places tokens now)
        try:
            self.items_on_map = getattr(self, "items_on_map", []) or []
            if getattr(self.ui, "messages", None) is not None:
                try:
                    self.ui.messages.add(f"World ready: {len(self.items_on_map)} items placed, {len(self.tomb_entrances)} tomb entrances.")
                except Exception:
                    pass
        except Exception:
            pass
        
        # Add enhanced initial travel log entries
        try:
            if hasattr(self.player, 'add_log_entry'):
                # Create dramatic opening entries for the hero's journey
                opening_entries = [
                    "[THE CRASH] My ship burns behind me, a monument to failure. Master's final words echo: 'Remember your training.' But will training be enough in this place of shadows?",
                    "[FIRST STEPS] The wreckage still smolders as I take my first steps into this forsaken world. The Force is strong here - but it tastes of ancient suffering and forgotten rage.",
                    "[THE CHOICE] I stand at a crossroads invisible to the eye but clear to the Force. Every choice from this moment will echo through eternity. Will I emerge as Jedi... or something else entirely?"
                ]
                
                for i, entry in enumerate(opening_entries):
                    self.player.add_log_entry(entry, i)
        except Exception:
            pass

        # load item definitions and place them on the map (best-effort)
        try:
            self.items_on_map = getattr(self, "items_on_map", [])
            # scan package jedi_fugitive.items for item definitions
            try:
                for finder, name, ispkg in pkgutil.iter_modules(importlib.import_module("jedi_fugitive.items").__path__):
                    try:
                        mod = importlib.import_module(f"jedi_fugitive.items.{name}")
                        # modules should expose ITEM_DEFS as list/dict or ITEMS
                        defs = getattr(mod, "ITEM_DEFS", None) or getattr(mod, "ITEMS", None)
                        if not defs:
                            continue
                        # place one instance of each item on a random floor tile
                        for it in (defs if isinstance(defs, (list,tuple)) else [defs]):
                            placed = False
                            attempts = 0
                            while not placed and attempts < 200:
                                attempts += 1
                                if not getattr(self, "game_map", None):
                                    break
                                mh = len(self.game_map); mw = len(self.game_map[0]) if mh else 0
                                if mh == 0 or mw == 0:
                                    break
                                rx = random.randrange(0, mw)
                                ry = random.randrange(0, mh)
                                floor_ch = getattr(Display, "FLOOR", ".")
                                try:
                                    if self.game_map[ry][rx] == floor_ch and (rx,ry) != (getattr(self.player,"x",None), getattr(self.player,"y",None)):
                                        self.items_on_map.append({"x":rx,"y":ry,"item":it})
                                        placed = True
                                except Exception:
                                    break
                    except Exception:
                        continue
            except Exception:
                # package not available or error scanning; skip silently
                pass
            try:
                if getattr(self, "items_on_map", None) and getattr(self.ui, "messages", None):
                    self.ui.messages.add(f"Placed {len(self.items_on_map)} items in the world.")
            except Exception:
                pass
        except Exception:
            pass

    def run(self):
        logger = get_logger()
        try:
            log_info("Game initialization started")
            self.initialize()
            log_info("World generation started")
            self.generate_world()
            log_info("Game loop started")
        except Exception as e:
            log_error("INIT_CRASH", "Failed during game initialization", e, logger.get_game_state_snapshot(self))
            raise
        
        # main loop
        while self.running:
            # redraw
            try:
                self.draw()
            except Exception as e:
                log_error("RENDER_ERROR", "Error during draw()", e, logger.get_game_state_snapshot(self))
                try: self.dump_debug_state()
                except Exception: pass
            # input
            try:
                key = self.stdscr.getch()
                input_handler.handle_input(self, key)
            except Exception as e:
                log_error("INPUT_ERROR", "Error handling input", e, logger.get_game_state_snapshot(self))
                try: self.ui.messages.add("Input handler error.")
                except Exception: pass

            # process game tick
            try:
                self.turns += 1
                
                # Autosave system
                try:
                    # Don't autosave if player is dead or dying
                    if (self.turns - self.last_autosave_turn >= self.autosave_interval and
                        getattr(self.player, "hp", 1) > 0 and
                        not getattr(self, '_died_this_session', False)):
                        if save_game(self, is_autosave=True):
                            self.last_autosave_turn = self.turns
                except Exception as e:
                    # Silent fail - don't interrupt gameplay
                    pass
                
                # Regenerate Force energy each turn
                try:
                    if hasattr(self.player, 'regenerate_force'):
                        # Check if player is in combat (has nearby enemies)
                        in_combat = False
                        if hasattr(self, 'game_map') and hasattr(self.game_map, 'actors'):
                            player_x = getattr(self.player, 'x', 0)
                            player_y = getattr(self.player, 'y', 0)
                            for actor in self.game_map.actors:
                                if actor != self.player and hasattr(actor, 'x') and hasattr(actor, 'y'):
                                    dx = abs(actor.x - player_x)
                                    dy = abs(actor.y - player_y)
                                    if dx <= 8 and dy <= 8:  # Enemy within 8 tiles = combat
                                        in_combat = True
                                        break
                        self.player.regenerate_force(in_combat=in_combat, game=self)
                except Exception:
                    pass
                
                # Check victory condition
                if getattr(self, 'victory', False):
                    # Loading...
                    sys.stdout.flush()
                    self.running = False
                    break
                
                # Check death condition
                if getattr(self.player, "hp", 1) <= 0:
                    # Generate death log entry
                    try:
                        in_tomb = getattr(self, 'in_tomb', False)
                        biome = getattr(self, 'current_biome', 'unknown wasteland')
                        
                        if getattr(self, '_breaking_point_triggered', False):
                            # Stress death - different narrative
                            if in_tomb:
                                tomb_floor = getattr(self, 'tomb_floor', 1)
                                body_fate = f"Your broken mind left your body a hollow shell in the depths of the Sith Tomb Level {tomb_floor}."
                            else:
                                body_fate = f"Your sanity shattered, you collapsed in the {biome}, never to rise again."
                            
                            death_entry = f"[DEATH] Succumbed to overwhelming stress and mental anguish. {body_fate} The darkness of this place proved too much to bear."
                            self.player.add_log_entry(death_entry, self.turn_count)
                        else:
                            # Combat death - get last enemy that attacked
                            last_enemy = getattr(self.player, 'last_attacking_enemy', 'a Sith warrior')
                            if in_tomb:
                                tomb_floor = getattr(self, 'tomb_floor', 1)
                                location_desc = f"the depths of Sith Tomb Level {tomb_floor + 1}"
                            else:
                                location_desc = f"the {biome}"
                            
                            death_entry = f"[DEATH] Struck down by {last_enemy} in {location_desc}. Your lightsaber fell from your grasp as darkness claimed you. The Force weeps for another fallen Jedi."
                            self.player.add_log_entry(death_entry, self.turn_count)
                    except Exception:
                        try:
                            self.player.add_log_entry("[DEATH] Your journey ends here. May the Force be with you.", self.turn_count)
                        except Exception:
                            pass
                    
                    # Set death flag and metadata for post-game display
                    self.death = True
                    if getattr(self, '_breaking_point_triggered', False):
                        self.death_cause = 'stress overload'
                    else:
                        self.death_cause = 'enemy attack'
                    self.death_biome = getattr(self, 'current_biome', 'unknown')
                    self.death_pos = (getattr(self.player, 'x', None), getattr(self.player, 'y', None))
                    
                    # Delete autosave on death - player can't continue from a dead state
                    try:
                        from jedi_fugitive.game.save_system import get_autosave_path
                        import os
                        autosave = get_autosave_path()
                        if autosave.exists():
                            autosave.unlink()
                            # Verify deletion
                            if autosave.exists():
                                # Try with os.remove as backup
                                os.remove(str(autosave))
                        # Also mark that we've died so we don't save again
                        self._died_this_session = True
                    except Exception as e:
                        # Log but don't interrupt death screen
                        try:
                            print(f"[DEBUG] Failed to delete autosave: {e}")
                        except:
                            pass
                    
                    # Loading...
                    sys.stdout.flush()
                    self.running = False
                    break
            except Exception:
                pass

            # Atmospheric immersion - random ambient descriptions and visions
            try:
                corruption = getattr(self.player, 'corruption', 50)
                current_biome = getattr(self, 'current_biome', 'crash_site')
                
                # Atmospheric descriptions
                if atmosphere.should_trigger_atmosphere(self.turn_count, self.last_atmosphere_turn):
                    self.last_atmosphere_turn = self.turn_count
                    try:
                        desc = atmosphere.get_biome_atmosphere(current_biome)
                        self.ui.messages.add(f"[Atmosphere] {desc}")
                    except Exception:
                        pass
                
                # Jedi Master memories & biome reflections
                if atmosphere.should_trigger_memory(self.turn_count, self.last_memory_turn):
                    self.last_memory_turn = self.turn_count
                    try:
                        memory = atmosphere.get_master_memory(corruption)
                        self.ui.messages.add(f"[Memory] {memory}")
                        
                        # Also add atmospheric journal entry
                        if hasattr(self.player, 'add_log_entry') and self.turn_count % 300 == 0:
                            from jedi_fugitive.game.journal_entries import get_biome_atmosphere_entry
                            player_alignment = self.player.get_alignment() if hasattr(self.player, 'get_alignment') else 'balanced'
                            entry = get_biome_atmosphere_entry(current_biome, player_alignment, corruption)
                            self.player.add_log_entry(entry, self.turn_count)
                    except Exception:
                        pass
                
                # Transformation visions
                if atmosphere.should_trigger_vision(self.turn_count, self.last_vision_turn):
                    self.last_vision_turn = self.turn_count
                    try:
                        vision = atmosphere.get_transformation_vision(corruption)
                        self.ui.messages.add(vision)
                    except Exception:
                        pass
            except Exception:
                pass
            
            # Atmospheric events system - weather, visibility, environmental effects
            # Only update when player moves or after sufficient time has passed
            # Skip atmospheric events in tombs (tomb-specific events handled separately)
            try:
                in_tomb = getattr(self, 'in_tomb', False)
                if hasattr(self, 'atmospheric_manager') and not in_tomb:
                    # Store previous player position to detect movement
                    if not hasattr(self, '_last_atmospheric_pos'):
                        self._last_atmospheric_pos = (self.player.x, self.player.y)
                        self._last_atmospheric_turn = self.turn_count
                    
                    current_pos = (self.player.x, self.player.y)
                    moved = current_pos != self._last_atmospheric_pos
                    time_passed = self.turn_count - self._last_atmospheric_turn >= 80
                    
                    if moved or time_passed:
                        self.atmospheric_manager.update()
                        self._last_atmospheric_pos = current_pos
                        if time_passed:
                            self._last_atmospheric_turn = self.turn_count
                    
                    # Check for environmental hazards only when conditions are met
                    hazard = should_trigger_environmental_hazard(self)
                    if hazard:
                        trigger_environmental_hazard(self, hazard)
            except Exception:
                pass
                
            # Tomb atmospheric events - Sith tomb specific atmospheric effects
            # Only trigger in tombs with reduced frequency and tomb-appropriate effects
            try:
                in_tomb = getattr(self, 'in_tomb', False)
                if in_tomb and hasattr(self, 'atmospheric_manager'):
                    # Initialize tomb atmospheric tracking
                    if not hasattr(self, '_last_tomb_atmospheric_turn'):
                        self._last_tomb_atmospheric_turn = self.turn_count
                    
                    # Tomb atmospheric events trigger much less frequently (every 200-300 turns)
                    time_passed = self.turn_count - self._last_tomb_atmospheric_turn >= random.randint(200, 300)
                    
                    if time_passed and random.random() < 0.3:  # 30% chance when time threshold met
                        self._trigger_tomb_atmospheric_event()
                        self._last_tomb_atmospheric_turn = self.turn_count
            except Exception:
                pass
            
            # Fauna system - living creatures and ecosystem interactions
            # Check for proximity-based encounters when player moves
            # Use tomb-specific creatures in Sith tombs
            try:
                if hasattr(self, 'fauna_manager'):
                    in_tomb = getattr(self, 'in_tomb', False)
                    
                    # Store previous player position to detect movement
                    if not hasattr(self, '_last_fauna_pos'):
                        self._last_fauna_pos = (self.player.x, self.player.y)
                    
                    current_pos = (self.player.x, self.player.y)
                    moved = current_pos != self._last_fauna_pos
                    
                    # Only check for fauna encounters when the player moves
                    if moved:
                        # First check if player is near any existing fauna
                        near_fauna = False
                        if hasattr(self.fauna_manager, 'active_encounters'):
                            for encounter in self.fauna_manager.active_encounters:
                                distance = abs(encounter.location_x - self.player.x) + abs(encounter.location_y - self.player.y)
                                if distance <= 5:  # Within 5 tiles
                                    near_fauna = True
                                    break
                        
                        # Only generate encounters when player steps on fauna symbols or near them
                        current_tile = '.'
                        try:
                            if (0 <= self.player.y < len(self.game_map) and 
                                0 <= self.player.x < len(self.game_map[0])):
                                # Check if there's a fauna symbol on current tile or adjacent
                                for dy in [-1, 0, 1]:
                                    for dx in [-1, 0, 1]:
                                        check_y = self.player.y + dy
                                        check_x = self.player.x + dx
                                        if (0 <= check_y < len(self.game_map) and 
                                            0 <= check_x < len(self.game_map[0])):
                                            # Check if there's an active fauna encounter at this location
                                            if hasattr(self.fauna_manager, 'active_encounters'):
                                                for encounter in self.fauna_manager.active_encounters.values():
                                                    if (abs(encounter.location_x - check_x) <= 1 and 
                                                        abs(encounter.location_y - check_y) <= 1):
                                                        near_fauna = True
                                                        break
                                if not near_fauna:
                                    # Use tomb biome for tomb encounters, otherwise use current biome
                                    current_biome = 'tomb' if in_tomb else getattr(self, 'current_biome', 'crash_site')
                                    encounter = self.fauna_manager.check_fauna_encounter(current_biome)
                                    if encounter:
                                        self.fauna_manager.trigger_fauna_encounter(encounter)
                        except (IndexError, AttributeError):
                            pass
                        
                        self._last_fauna_pos = current_pos
            except Exception:
                pass
            
            # Dynamic narrative events - journals, holocrons, distress signals, environmental
            try:
                from jedi_fugitive.game import narrative_events
                corruption = getattr(self.player, 'corruption', 50)
                
                # Survivor journals - place on map as '?' marker (only if not in tomb)
                if (narrative_events.should_trigger_narrative_event(
                    self.turn_count - self.last_journal_turn, 'journal'
                ) and not getattr(self, 'in_tomb', False) and not getattr(self, 'in_special_dungeon', False)):
                    self.last_journal_turn = self.turn_count
                    try:
                        # Get unused journal
                        used_journals = getattr(self, 'used_journals', set())
                        available = [j for j in narrative_events.SURVIVOR_JOURNALS if j['title'] not in used_journals]
                        if available:
                            # Place journal marker on map
                            import random
                            for _ in range(100):  # Try 100 times to find valid spot
                                jx = random.randint(1, len(self.game_map[0]) - 2)
                                jy = random.randint(1, len(self.game_map) - 2)
                                if self.game_map[jy][jx] == '.' and (jx, jy) not in self.map_landmarks:
                                    # Place journal marker
                                    self.game_map[jy][jx] = '?'
                                    journal = random.choice(available)
                                    self.used_journals.add(journal['title'])
                                    self.map_landmarks[(jx, jy)] = {
                                        'type': 'journal',
                                        'name': journal['title'],
                                        'data': journal
                                    }
                                    self.ui.messages.add(f"#3#[EVENT]#0# You sense something interesting nearby...")
                                    break
                    except Exception:
                        pass
                
                # Holocron messages - place on map as '?' marker (only if not in tomb)
                if (narrative_events.should_trigger_narrative_event(
                    self.turn_count - self.last_holocron_turn, 'holocron'
                ) and not getattr(self, 'in_tomb', False) and not getattr(self, 'in_special_dungeon', False)):
                    self.last_holocron_turn = self.turn_count
                    try:
                        # Get unused holocron (check all categories)
                        used_holocrons = getattr(self, 'used_holocrons', set())
                        all_holocrons = []
                        for category in narrative_events.HOLOCRON_MESSAGES.values():
                            all_holocrons.extend(category)
                        available = [h for h in all_holocrons if h['speaker'] not in used_holocrons]
                        if available:
                            # Place holocron marker on map
                            import random
                            for _ in range(100):
                                hx = random.randint(1, len(self.game_map[0]) - 2)
                                hy = random.randint(1, len(self.game_map) - 2)
                                if self.game_map[hy][hx] == '.' and (hx, hy) not in self.map_landmarks:
                                    # Place holocron marker
                                    self.game_map[hy][hx] = '?'
                                    holocron = random.choice(available)
                                    self.used_holocrons.add(holocron['speaker'])
                                    self.map_landmarks[(hx, hy)] = {
                                        'type': 'holocron',
                                        'name': 'Ancient Holocron',
                                        'data': holocron
                                    }
                                    self.ui.messages.add(f"#3#[EVENT]#0# The Force pulls you toward something...")
                                    break
                    except Exception:
                        pass
                
                # Distress signals - place on map as '!' marker (only if not in tomb)
                if (narrative_events.should_trigger_narrative_event(
                    self.turn_count - self.last_distress_turn, 'distress_signal'
                ) and not getattr(self, 'in_tomb', False) and not getattr(self, 'in_special_dungeon', False)):
                    self.last_distress_turn = self.turn_count
                    try:
                        # Get unused distress signal
                        used_signals = getattr(self, 'used_distress_signals', set())
                        available = [s for s in narrative_events.DISTRESS_SIGNALS if s['signal_type'] not in used_signals]
                        if available:
                            # Place distress signal marker on map
                            import random
                            for _ in range(100):
                                dx = random.randint(1, len(self.game_map[0]) - 2)
                                dy = random.randint(1, len(self.game_map) - 2)
                                if self.game_map[dy][dx] == '.' and (dx, dy) not in self.map_landmarks:
                                    # Place distress signal marker
                                    self.game_map[dy][dx] = '!'
                                    signal = random.choice(available)
                                    self.used_distress_signals.add(signal['signal_type'])
                                    self.map_landmarks[(dx, dy)] = {
                                        'type': 'distress_signal',
                                        'name': signal['signal_type'].replace('_', ' ').title(),
                                        'data': signal
                                    }
                                    self.ui.messages.add(f"#3#[SIGNAL RECEIVED]#0# Distress signal detected on your scanner!")
                                    break
                    except Exception:
                        pass
                
                # Environmental discoveries - only trigger when standing on '?' symbols
                current_tile = None
                try:
                    if (0 <= self.player.y < len(self.game_map) and 
                        0 <= self.player.x < len(self.game_map[0])):
                        current_tile = self.game_map[self.player.y][self.player.x]
                except (IndexError, AttributeError):
                    pass
                
                if (current_tile == '?' and narrative_events.should_trigger_narrative_event(
                    self.turn_count - self.last_environmental_turn, 'environmental'
                )):
                    self.last_environmental_turn = self.turn_count
                    try:
                        event = narrative_events.get_environmental_event()
                        formatted, choice_mapping = narrative_events.format_environmental_event(event)
                        
                        # Show event in popup menu like fauna encounters
                        self.ui.centered_menu(
                            formatted,
                            f"Discovery: {event.get('name', 'Environmental Event')}"
                        )
                        
                        # Store pending choice if event has choices
                        if choice_mapping:
                            self.pending_narrative_choice = (event, choice_mapping, 'environmental')
                        
                        # Brief confirmation message
                        self.ui.messages.add(f"#3#[DISCOVERY]#0# {event.get('name', 'Environmental event')} revealed.")
                    except Exception:
                        pass
            except Exception:
                pass
            
            # Progression milestones - check achievements
            try:
                from jedi_fugitive.game import milestone_events
                
                # Check all pending milestones
                pending = milestone_events.get_all_pending_milestones(self.player)
                
                for milestone_key, milestone_data in pending:
                    try:
                        # Display ceremony
                        corruption = getattr(self.player, 'corruption', 50)
                        formatted = milestone_events.format_milestone_display(milestone_data, corruption)
                        for line in formatted:
                            self.ui.messages.add(line)
                        
                        # Add journal entry
                        journal_entry = milestone_events.get_journal_entry_for_milestone(milestone_data, corruption)
                        if journal_entry:
                            self.player.add_log_entry(journal_entry, self.turn_count)
                        
                        # Apply effects
                        if 'effect' in milestone_data:
                            milestone_events.process_milestone_effects(self.player, milestone_data['effect'])
                        
                    except Exception:
                        pass
            except Exception:
                pass
            
            # Narrative Events System
            try:
                from jedi_fugitive.game.narrative_events import (
                    should_trigger_narrative_event,
                    get_random_journal,
                    get_holocron_message,
                    get_random_distress_signal,
                    get_environmental_event,
                    format_journal_display,
                    format_holocron_display,
                    format_distress_signal
                )
                
                corruption = getattr(self.player, 'corruption', 50)
                
                # Survivor journals
                if should_trigger_narrative_event(self.turn_count - self.last_journal_turn, 'journal'):
                    self.last_journal_turn = self.turn_count
                    try:
                        journal = get_random_journal()
                        formatted = format_journal_display(journal)
                        for line in formatted:
                            self.ui.messages.add(line)
                        # Apply corruption effect
                        effect = journal.get('corruption_effect', 0)
                        if effect != 0:
                            self.player.corruption = max(0, min(100, self.player.corruption + effect))
                    except Exception:
                        pass
                
                # Holocron messages
                if should_trigger_narrative_event(self.turn_count - self.last_holocron_turn, 'holocron'):
                    self.last_holocron_turn = self.turn_count
                    try:
                        holocron = get_holocron_message(corruption)
                        formatted = format_holocron_display(holocron)
                        for line in formatted:
                            self.ui.messages.add(line)
                        # Apply corruption effect
                        effect = holocron.get('corruption_effect', 0)
                        if effect != 0:
                            self.player.corruption = max(0, min(100, self.player.corruption + effect))
                    except Exception:
                        pass
                
                # Distress signals
                if should_trigger_narrative_event(self.turn_count - self.last_distress_turn, 'distress'):
                    self.last_distress_turn = self.turn_count
                    try:
                        distress = get_random_distress_signal()
                        formatted = format_distress_signal(distress)
                        for line in formatted:
                            self.ui.messages.add(line)
                        # Player can choose response (for future implementation)
                    except Exception:
                        pass
                
                # Environmental events - only trigger when standing on '?' symbols
                current_tile = None
                try:
                    if (0 <= self.player.y < len(self.game_map) and 
                        0 <= self.player.x < len(self.game_map[0])):
                        current_tile = self.game_map[self.player.y][self.player.x]
                except (IndexError, AttributeError):
                    pass
                
                if (current_tile == '?' and should_trigger_narrative_event(
                    self.turn_count - self.last_environmental_turn, 'environmental')):
                    self.last_environmental_turn = self.turn_count
                    try:
                        from jedi_fugitive.game.reward_system import apply_environmental_reward
                        event = get_environmental_event()
                        
                        # Build popup content
                        popup_content = [event.get('title', 'Environmental Discovery')]
                        popup_content.append("")
                        if isinstance(event.get('description'), list):
                            popup_content.extend(event['description'])
                        else:
                            popup_content.append(str(event.get('description', '')))
                        popup_content.append("")
                        popup_content.append("Press any key to continue...")
                        
                        # Show in popup menu
                        self.ui.centered_menu(
                            popup_content,
                            "Environmental Discovery"
                        )
                        
                        # Apply environmental event rewards
                        apply_environmental_reward(self.player, event, self.ui, self.inventory)
                        
                        # Brief confirmation message
                        self.ui.messages.add(f"#3#[DISCOVERY]#0# {event.get('title', 'Discovery')}")
                    except Exception:
                        pass
            except Exception:
                pass
            
            # Milestone Ceremonies
            try:
                from jedi_fugitive.game.milestone_events import (
                    get_all_pending_milestones,
                    format_milestone_display,
                    get_journal_entry_for_milestone,
                    process_milestone_effects
                )
                
                corruption = getattr(self.player, 'corruption', 50)
                pending = get_all_pending_milestones(self.player)
                
                for milestone_key, milestone_data in pending:
                    try:
                        # Display ceremony
                        formatted = format_milestone_display(milestone_data, corruption)
                        for line in formatted:
                            self.ui.messages.add(line)
                        
                        # Add journal entry
                        journal_text = get_journal_entry_for_milestone(milestone_data, corruption)
                        if journal_text:
                            self.player.add_log_entry(f"[MILESTONE] {journal_text}", self.turn_count)
                        
                        # Apply effects
                        if 'effect' in milestone_data:
                            process_milestone_effects(self.player, milestone_data['effect'])
                    except Exception:
                        pass
            except Exception:
                pass

            try:
                # enemies and projectiles
                # trace before enemy processing
                try:
                    self.process_enemies()
                except Exception:
                    pass
            except Exception:
                pass

            try:
                try:
                    self._tick_effects()
                except Exception:
                    pass
            except Exception:
                pass

            try:
                self.compute_visibility()
            except Exception:
                pass

            # handle resize
            try:
                current_size = self.stdscr.getmaxyx()
                if current_size != getattr(self, "last_size", (0, 0)):
                    curses.resizeterm(current_size[0], current_size[1])
                    mw,mh,sw,aw,mhmsg,cmdh = self._compute_layout()
                    self.layout.update({"map_w":mw,"map_h":mh,"stats_w":sw,"abil_w":aw,"msg_h":mhmsg,"cmd_h":cmdh})
                    self.last_size = current_size
                    try:
                        self.ui.create_layout(mw,mh,sw,aw,mhmsg,cmdh)
                    except Exception:
                        pass
                    try:
                        self.stdscr.clear(); self.stdscr.refresh()
                    except Exception:
                        pass
            except Exception:
                pass

    def register_command(self, key, handler, desc):
        try:
            self.key_bindings[key] = handler
            self.key_help[key] = desc
            self.update_command_gui()
        except Exception:
            pass

    # small helper commands (remain compatible with previous API)
    def _cmd_clear_tree(self):
        try:
            tree_ch = getattr(Display, "TREE", "T")
            floor_ch = getattr(Display, "FLOOR", ".")
        except Exception:
            tree_ch, floor_ch = "T", "."
        tx = getattr(getattr(self.ui, "cursor", None), "x", None)
        ty = getattr(getattr(self.ui, "cursor", None), "y", None)
        if tx is None:
            tx = self.player.x + 1; ty = self.player.y
        try:
            if 0 <= ty < len(self.game_map) and 0 <= tx < len(self.game_map[0]) and self.game_map[ty][tx] == tree_ch:
                self.game_map[ty][tx] = floor_ch
                try: self.ui.messages.add("You clear the tree.") 
                except Exception: pass
                return True
        except Exception:
            pass
        try: self.ui.messages.add("No tree to clear there.") 
        except Exception: pass
        return False

    def _cmd_fire_blaster(self):
        try:
            if hasattr(self.ui, "cursor") and getattr(self.ui.cursor, "visible", False):
                tx, ty = self.ui.cursor.x, self.ui.cursor.y
            else:
                tx = self.player.x + 8; ty = self.player.y
        except Exception:
            tx = self.player.x + 8; ty = self.player.y
        try:
            projectiles.spawn_blaster(self, self.player.x, self.player.y, tx, ty, damage=5, owner=self.player, max_range=20)
            try: self.ui.messages.add("You fire your blaster!") 
            except Exception: pass
            return True
        except Exception:
            try: self.ui.messages.add("You can't fire now.") 
            except Exception: pass
            return False

    def enter_tomb(self) -> bool:
        """Wrapper for entering tombs from UI/input; calls map_features.enter_tomb(self)."""
        logger = get_logger()
        try:
            print("⟳ Entering tomb...")
            log_game_event("TOMB_ENTRY", f"Player entering tomb at ({self.player.x}, {self.player.y})")
            # prefer map_features implementation (import at top as mf)
            try:
                entered = mf.enter_tomb(self)
                print(f"✓ Tomb entry result: {entered}")
                log_game_event("TOMB_ENTRY", f"Tomb entry successful: {entered}")
            except Exception as e:
                print(f"⚠ First tomb entry attempt failed: {e}")
                log_error("TOMB_ENTRY_ERROR", "First tomb entry attempt failed", e, logger.get_game_state_snapshot(self))
                # fallback to direct import in case alias not present
                from jedi_fugitive.game import map_features as _mf
                entered = _mf.enter_tomb(self)
                print(f"✓ Tomb entry (fallback) result: {entered}")
            if not entered:
                print(f"✗ Tomb entry failed - returned False")
                print(f"  Current depth: {getattr(self,'current_depth',None)}")
                print(f"  Tomb entrances: {len(getattr(self,'tomb_entrances',set()))} found")
                print(f"  Player position: ({self.player.x}, {self.player.y})")
                try:
                    if getattr(self, "ui", None) and getattr(self.ui, "messages", None):
                        self.ui.messages.add("Failed to enter tomb (map_features returned False).")
                except Exception:
                    pass
                # debug dump for developers
                try:
                    with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                        fh.write(f"GameManager.enter_tomb: map_features.enter_tomb returned False; depth={getattr(self,'current_depth',None)} tombs={getattr(self,'tomb_entrances',None)}\n")
                except Exception:
                    pass
                return False
            # success - recompute visibility and notify UI (map_features usually did this already)
            try: self.compute_visibility()
            except Exception: pass
            try:
                if getattr(self, "ui", None) and getattr(self.ui, "messages", None):
                    self.ui.messages.add("You descend into the Sith dungeon...")
            except Exception:
                pass
            
            # Track tomb discovery for milestone system (first tomb only)
            try:
                current_discovered = getattr(self.player, 'tombs_discovered', 0)
                if current_discovered == 0:
                    self.player.tombs_discovered = 1
            except Exception:
                pass
            
            return True
        except Exception as e:
            print(f"✗ TOMB ENTRY ERROR: {e}")
            import traceback
            traceback.print_exc()
            try:
                with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                    fh.write("GameManager.enter_tomb exception:\n")
                    traceback.print_exc(file=fh)
            except Exception:
                pass
            try:
                if getattr(self, "ui", None) and getattr(self.ui, "messages", None):
                    self.ui.messages.add("Failed to enter tomb (see /tmp/jedi_fugitive_debug.txt).")
            except Exception:
                pass
            return False

    def _handle_sith_keep_entrance(self):
        """Handle player stepping on Sith Keep entrance tile ('K')."""
        try:
            # Check if player meets requirements to enter the keep
            player_level = getattr(self.player, 'level', 1)
            min_level = 6  # Minimum level requirement for Sith Keep
            
            if player_level < min_level:
                self.ui.messages.add("═══ ANCIENT SITH KEEP ═══")
                self.ui.messages.add("The massive gates tower before you, emanating dark power.")
                self.ui.messages.add("Ancient runes pulse with malevolent energy.")
                self.ui.messages.add(f"You sense you need to be at least Level {min_level} to survive what lies within.")
                self.ui.messages.add(f"(Current Level: {player_level})")
                return
            
            # Check if keep is accessible
            if not hasattr(self, 'sith_keep_entrance'):
                self.ui.messages.add("The keep entrance is not properly initialized.")
                return
            
            # Display entrance description and prompt
            self.ui.messages.add("═══ ANCIENT SITH KEEP ═══")
            self.ui.messages.add("You stand before the massive obsidian gates of an ancient Sith fortress.")
            self.ui.messages.add("Dark energy radiates from within, promising both power and peril.")
            self.ui.messages.add("The Force whispers warnings, but also... opportunities.")
            self.ui.messages.add("")
            self.ui.messages.add("This is a place of great danger - even for a Jedi.")
            self.ui.messages.add("The keep contains powerful guardians, deadly puzzles, and ancient secrets.")
            self.ui.messages.add("")
            
            # Create confirmation menu
            choice = self.ui.centered_menu(
                ["Enter the Sith Keep", "Turn back"], 
                title="Ancient Sith Keep"
            )
            
            if choice == 0:  # Enter the keep
                self._enter_sith_keep()
            else:
                self.ui.messages.add("You step back from the ominous gates. Perhaps another time...")
                
        except Exception as e:
            self.ui.messages.add(f"Error at Sith Keep entrance: {e}")

    def _enter_sith_keep(self):
        """Actually enter the Sith Keep dungeon."""
        try:
            from jedi_fugitive.game.sith_keep import generate_sith_keep_layout
            
            # Store surface position for return
            if not hasattr(self, 'pre_keep_position'):
                self.pre_keep_position = (self.player.x, self.player.y)
            
            # Generate the keep layout
            layout, entrance, chambers, boss_chamber = generate_sith_keep_layout(keep_size=15)
            
            # Convert layout to game map format
            keep_map = []
            for row in layout:
                keep_map.append([str(cell) for cell in row])
            
            # Store current surface map
            self.surface_map = self.game_map
            self.surface_enemies = getattr(self, 'enemies', [])
            
            # Switch to keep map
            self.game_map = keep_map
            self.enemies = []  # Clear enemies for now - they'll be populated by the keep setup
            
            # Position player at keep entrance
            entrance_x, entrance_y = entrance
            self.player.x = entrance_x
            self.player.y = entrance_y
            
            # Mark that we're in the keep
            self.in_sith_keep = True
            
            # Place exit portal at entrance for easy escape
            # Mark entrance as exit portal
            keep_map[entrance_y][entrance_x] = 'E'  # Exit portal
            
            # Setup keep encounters (guards, puzzles, etc.) within the keep map bounds
            try:
                from jedi_fugitive.game.sith_keep import setup_sith_keep_guards, setup_sith_keep_boss
                # Use the keep's internal coordinate system
                setup_sith_keep_guards(self, 15, 15, chambers)  # Center of 31x31 keep
                setup_sith_keep_boss(self, 15, 15, boss_chamber)
            except Exception as e:
                print(f"Warning: Failed to setup keep encounters: {e}")
            
            # Recompute visibility for new map
            try:
                self.compute_visibility()
            except Exception:
                pass
            
            # Welcome message
            self.ui.messages.add("You step through the ancient gates...")
            self.ui.messages.add("The Sith Keep's corridors stretch before you, filled with shadow and menace.")
            self.ui.messages.add("The air thrums with dark side energy. You sense guardians stirring...")
            
            # Add travel log entry
            try:
                if hasattr(self.player, 'add_log_entry'):
                    entry = self.player.narrative_text(
                        light_version="Entered the Sith Keep to confront the darkness within and cleanse it.",
                        dark_version="Entered the ancient Keep to claim its power and secrets for myself.", 
                        balanced_version="Entered the Sith Keep. Whatever lies within, I must face it."
                    )
                    self.player.add_log_entry(entry, getattr(self, 'turn_count', 0))
            except Exception:
                pass
                
        except Exception as e:
            self.ui.messages.add(f"Failed to enter Sith Keep: {e}")
            import traceback
            traceback.print_exc()

    def _exit_sith_keep(self):
        """Exit the Sith Keep and return to the surface."""
        try:
            if not getattr(self, 'in_sith_keep', False):
                return
            
            # Restore surface map and position
            if hasattr(self, 'surface_map'):
                self.game_map = self.surface_map
                self.enemies = getattr(self, 'surface_enemies', [])
                
                # Restore player position
                if hasattr(self, 'pre_keep_position'):
                    self.player.x, self.player.y = self.pre_keep_position
                
                # Clear keep flags
                self.in_sith_keep = False
                
                # Recompute visibility
                try:
                    self.compute_visibility()
                except Exception:
                    pass
                
                self.ui.messages.add("You emerge from the ancient Sith Keep, glad to see daylight again.")
                self.ui.messages.add("The dark energies within still echo in your mind...")
                
                # Add travel log entry
                try:
                    if hasattr(self.player, 'add_log_entry'):
                        entry = self.player.narrative_text(
                            light_version="Escaped the Keep's corruption. I must cleanse myself of its influence.",
                            dark_version="Left the Keep, but its power now flows through me. I am stronger.",
                            balanced_version="Exited the Sith Keep. The experience has changed me."
                        )
                        self.player.add_log_entry(entry, getattr(self, 'turn_count', 0))
                except Exception:
                    pass
            else:
                self.ui.messages.add("Cannot exit - surface map not found!")
                
        except Exception as e:
            self.ui.messages.add(f"Failed to exit Sith Keep: {e}")
            import traceback
            traceback.print_exc()

    def _handle_special_dungeon_entrance(self, dungeon_data, x, y):
        """Handle player stepping on a special dungeon entrance."""
        try:
            from jedi_fugitive.game.special_dungeons import DUNGEON_TEMPLATES, get_artifact_by_type
            
            dungeon_type = dungeon_data['type']
            template = dungeon_data['template']
            discovered = dungeon_data.get('discovered', False)
            
            # Mark as discovered
            dungeon_data['discovered'] = True
            
            # Show atmospheric description
            self.ui.messages.add(f"═══ {template['name'].upper()} ═══")
            for desc_line in template['description']:
                self.ui.messages.add(desc_line)
            
            if not discovered:
                self.ui.messages.add("")
                self.ui.messages.add("This place radiates an otherworldly presence...")
                self.ui.messages.add("You sense something of great power lies within.")
            
            # Create confirmation menu
            choice = self.ui.centered_menu(
                ["Enter the mysterious dungeon", "Turn away"], 
                title=template['name']
            )
            
            if choice == 0:  # Enter the dungeon
                self._enter_special_dungeon(dungeon_data, x, y)
            else:
                self.ui.messages.add("You step back from the mysterious entrance. Perhaps another time...")
                
        except Exception as e:
            self.ui.messages.add(f"Error at special dungeon entrance: {e}")

    def _enter_special_dungeon(self, dungeon_data, entrance_x, entrance_y):
        """Actually enter the special dungeon."""
        try:
            from jedi_fugitive.game.special_dungeons import generate_special_dungeon, DUNGEON_TEMPLATES, get_artifact_by_type
            
            dungeon_type = dungeon_data['type']
            template = dungeon_data['template']
            
            # Check if this is a new entry or continuing multi-level dungeon
            current_floor = getattr(self, '_special_dungeon_floor', 0) if hasattr(self, 'current_special_dungeon') else 0
            current_floor += 1
            
            # Save current state (only on first entry)
            if current_floor == 1:
                self.pre_special_dungeon_state = {
                    'map': [row[:] for row in self.game_map],  # Deep copy
                    'enemies': list(self.enemies),
                    'position': (self.player.x, self.player.y),
                    'current_depth': getattr(self, 'current_depth', 1),
                    'current_location': getattr(self, 'current_location', 'Unknown'),
                    'entrance_pos': (entrance_x, entrance_y)
                }
            
            # Generate the special dungeon
            layout, entrance_pos, artifact_pos, artifact_type = generate_special_dungeon(dungeon_type)
            
            # Check if this is the final floor (artifact floor)
            num_levels = template.get('num_levels', 1)
            is_final_floor = (current_floor >= num_levels)
            
            # Place stairs or artifact
            if is_final_floor:
                # Final floor - place artifact
                if artifact_pos and len(layout) > artifact_pos[1] and len(layout[0]) > artifact_pos[0]:
                    layout[artifact_pos[1]][artifact_pos[0]] = '◆'  # Special artifact symbol
            else:
                # Not final floor - place down stairs where artifact would be
                if artifact_pos and len(layout) > artifact_pos[1] and len(layout[0]) > artifact_pos[0]:
                    layout[artifact_pos[1]][artifact_pos[0]] = '>'  # Down stairs to next level
            
            # Set up dungeon state
            self.game_map = layout
            self.enemies = []
            self.current_special_dungeon = {
                'type': dungeon_type,
                'template': template,
                'artifact_pos': artifact_pos,
                'artifact_type': artifact_type,
                'entrance_pos': entrance_pos,
                'exit_pos': entrance_pos,  # Exit where you entered
                'current_floor': current_floor,
                'num_levels': num_levels
            }
            self._special_dungeon_floor = current_floor
            
            # Place player at entrance
            self.player.x, self.player.y = entrance_pos
            
            # Spawn enemies based on dungeon type
            self._spawn_special_dungeon_enemies(template, layout)
            
            # Update location with floor info
            if 'level_lore' in template and current_floor in template['level_lore']:
                floor_lore = template['level_lore'][current_floor]
                self.current_location = f"{template['name']} - {floor_lore['title']}"
            else:
                self.current_location = f"{template['name']} - Level {current_floor}"
            
            # Recompute visibility
            try:
                self.compute_visibility()
            except Exception:
                pass
            
            # Display floor-specific lore if available
            if 'level_lore' in template and current_floor in template['level_lore']:
                floor_lore = template['level_lore'][current_floor]
                
                # Create popup with lore
                lore_content = []
                lore_content.append("═" * 60)
                lore_content.append(f"{floor_lore['title'].upper()}".center(60))
                lore_content.append(f"(Level {current_floor} of {num_levels})".center(60))
                lore_content.append("═" * 60)
                lore_content.append("")
                
                for desc_line in floor_lore['description']:
                    lore_content.append(desc_line)
                
                lore_content.append("")
                lore_content.append(f"Atmosphere: {floor_lore['atmosphere']}")
                lore_content.append("")
                
                if is_final_floor:
                    lore_content.append("This is the final level. The artifact awaits...")
                else:
                    lore_content.append(f"Descend deeper to reach your goal... ({num_levels - current_floor} levels remain)")
                
                lore_content.append("")
                lore_content.append("Press any key to continue...")
                
                self.ui.centered_menu(lore_content, f"{template['name']}")
            else:
                # Fallback atmospheric message
                self.ui.messages.add(f"You step into the {template['name'].lower()}...")
                
                from jedi_fugitive.game.special_dungeons import get_dungeon_atmosphere_message
                atmosphere_msg = get_dungeon_atmosphere_message(dungeon_type)
                self.ui.messages.add(atmosphere_msg)
            
            # Add travel log entry
            try:
                if hasattr(self.player, 'add_log_entry'):
                    entry = self.player.narrative_text(
                        light_version=f"Entered {template['name']} to face whatever ancient power dwells within.",
                        dark_version=f"Entered {template['name']} to claim its dark secrets and artifacts.",
                        balanced_version=f"Entered a mysterious place called {template['name']}."
                    )
                    self.player.add_log_entry(entry, getattr(self, 'turn_count', 0))
            except Exception:
                pass
                
        except Exception as e:
            self.ui.messages.add(f"Failed to enter special dungeon: {e}")
            import traceback
            traceback.print_exc()

    def _spawn_special_dungeon_enemies(self, template, layout):
        """Spawn enemies appropriate to the special dungeon type."""
        try:
            import random
            from jedi_fugitive.game import enemies_sith as sith
            
            enemy_types = template.get('enemies', [])
            floor_tile = template['floor_tile']
            
            # Find floor positions for spawning (avoid artifact and entrance)
            floor_positions = []
            artifact_pos = self.current_special_dungeon.get('artifact_pos')
            entrance_pos = self.current_special_dungeon.get('entrance_pos')
            
            for y in range(len(layout)):
                for x in range(len(layout[0])):
                    if layout[y][x] == floor_tile:
                        # Don't spawn on artifact or entrance
                        if (x, y) != artifact_pos and (x, y) != entrance_pos:
                            floor_positions.append((x, y))
            
            # Spawn 3-5 enemies based on dungeon level
            current_floor = self.current_special_dungeon.get('current_floor', 1)
            enemy_count = random.randint(2 + current_floor, 4 + current_floor)
            player_level = getattr(self.player, 'level', 1)
            
            # Enemy factory mapping for unique dungeon enemies
            enemy_factories = {
                'memory_wraith': sith.create_memory_wraith,
                'crystal_guardian': sith.create_crystal_guardian,
                'shadow_stalker': sith.create_shadow_stalker,
                'maze_phantom': sith.create_shadow_stalker,  # Similar to shadow stalker
                'bone_wraith': sith.create_bone_wraith,
                'skeletal_champion': sith.create_bone_wraith,  # Similar variant
                'banshee': sith.create_echo_banshee,
                'echo_wraith': sith.create_echo_banshee,  # Similar variant
                'knowledge_seeker': sith.create_knowledge_seeker,
                'text_phantom': sith.create_knowledge_seeker,  # Similar variant
                'pain_wraith': sith.create_pain_wraith,
                'forge_guardian': sith.create_pain_wraith,  # Similar variant
                'nightmare_herald': sith.create_nightmare_herald,
                'dream_stalker': sith.create_nightmare_herald,  # Similar variant
                'sith_ghost': sith.create_sith_ghost,
                'sith_warrior': sith.create_sith_warrior,
            }
            
            for _ in range(min(enemy_count, len(floor_positions))):
                if floor_positions:
                    spawn_x, spawn_y = floor_positions.pop(random.randint(0, len(floor_positions) - 1))
                    
                    # Pick a random enemy type from the dungeon's enemy list
                    if enemy_types:
                        enemy_type = random.choice(enemy_types)
                        factory = enemy_factories.get(enemy_type, sith.create_sith_warrior)
                        
                        # Scale enemy level with dungeon floor
                        enemy_level = max(1, player_level + current_floor - 1)
                        enemy = factory(level=enemy_level, x=spawn_x, y=spawn_y)
                        
                        self.enemies.append(enemy)
                    
        except Exception as e:
            print(f"Error spawning special dungeon enemies: {e}")

    def _exit_special_dungeon(self):
        """Exit the special dungeon and return to the previous area."""
        try:
            if not hasattr(self, 'current_special_dungeon'):
                return
            
            # Restore previous state
            if hasattr(self, 'pre_special_dungeon_state'):
                state = self.pre_special_dungeon_state
                
                self.game_map = state['map']
                self.enemies = state['enemies']
                self.player.x, self.player.y = state['position']
                self.current_depth = state['current_depth']
                self.current_location = state['current_location']
                
                # Clear special dungeon state
                delattr(self, 'current_special_dungeon')
                delattr(self, 'pre_special_dungeon_state')
                
                # Recompute visibility
                try:
                    self.compute_visibility()
                except Exception:
                    pass
                
                self.ui.messages.add("You emerge from the mysterious place, forever changed by what you experienced.")
                
                # Add travel log entry
                try:
                    if hasattr(self.player, 'add_log_entry'):
                        entry = self.player.narrative_text(
                            light_version="Emerged from the mystical realm, carrying its lessons with me.",
                            dark_version="Left the ancient place, its power now part of my growing strength.",
                            balanced_version="Exited the mysterious dungeon. The experience lingers in my mind."
                        )
                        self.player.add_log_entry(entry, getattr(self, 'turn_count', 0))
                except Exception:
                    pass
            else:
                self.ui.messages.add("Cannot exit - previous state not found!")
                
        except Exception as e:
            self.ui.messages.add(f"Failed to exit special dungeon: {e}")

    def _handle_special_dungeon_artifact(self):
        """Handle interaction with a special dungeon artifact."""
        try:
            from jedi_fugitive.game.special_dungeons import get_artifact_by_type
            
            dungeon = self.current_special_dungeon
            artifact_type = dungeon['artifact_type']
            artifact_data = get_artifact_by_type(artifact_type)
            
            # Show artifact description
            self.ui.messages.add("═══ ANCIENT ARTIFACT DISCOVERED ═══")
            self.ui.messages.add(f"You have found: {artifact_data['name']}")
            self.ui.messages.add("")
            
            for desc_line in artifact_data['description']:
                self.ui.messages.add(desc_line)
            
            self.ui.messages.add("")
            self.ui.messages.add("The artifact pulses with otherworldly power.")
            self.ui.messages.add("You feel drawn to it, yet sense great danger.")
            self.ui.messages.add("What will you do?")
            
            # Create choice menu
            choices = ["Absorb its power", "Destroy the artifact", "Leave it alone"]
            choice = self.ui.centered_menu(choices, title=artifact_data['name'])
            
            if choice == 0:  # Absorb
                self._absorb_special_artifact(artifact_data)
            elif choice == 1:  # Destroy
                self._destroy_special_artifact(artifact_data)
            else:  # Leave alone
                self.ui.messages.add("You step back from the artifact, deciding not to risk its power.")
                self.ui.messages.add("Sometimes wisdom lies in restraint...")
                return
            
            # Mark artifact as claimed and remove from map
            dungeon['artifact_claimed'] = True
            artifact_pos = dungeon['artifact_pos']
            if artifact_pos:
                x, y = artifact_pos
                template = dungeon['template']
                floor_tile = template['floor_tile']
                if 0 <= y < len(self.game_map) and 0 <= x < len(self.game_map[0]):
                    self.game_map[y][x] = floor_tile
                    
                    # Place exit stairs at artifact location
                    exit_x, exit_y = x, y
                    self.game_map[exit_y][exit_x] = '<'  # Up stairs
                    dungeon['exit_pos'] = (exit_x, exit_y)
            
            self.ui.messages.add("")
            self.ui.messages.add("The way back is now clear. You may leave this place.")
            self.ui.messages.add("[An exit stairway '<' has appeared where the artifact was]")
            
        except Exception as e:
            self.ui.messages.add(f"Error handling artifact: {e}")

    def _absorb_special_artifact(self, artifact_data):
        """Absorb the power of a special artifact (Dark Side choice)."""
        try:
            effects = artifact_data['effects']['absorb']
            
            self.ui.messages.add("═══ DARK POWER ABSORBED ═══")
            self.ui.messages.add(effects['description'])
            self.ui.messages.add("")
            
            # Apply corruption gain
            corruption_gain = effects.get('corruption_gain', 0)
            if corruption_gain > 0:
                current_corruption = getattr(self.player, 'corruption', 50)
                new_corruption = min(100, current_corruption + corruption_gain)
                self.player.corruption = new_corruption
                self.ui.messages.add(f"Corruption increased by {corruption_gain}! (Now: {new_corruption})")
            
            # Apply special effects
            if effects.get('psychic_power'):
                self.ui.messages.add("You gain the ability to read minds!")
            if effects.get('life_drain_ability'):
                self.ui.messages.add("You learn to drain the life force from your enemies!")
                if hasattr(self.player, 'max_hp'):
                    hp_boost = effects.get('max_hp_boost', 0)
                    self.player.max_hp += hp_boost
                    self.player.hp = min(self.player.hp + hp_boost, self.player.max_hp)
                    if hp_boost > 0:
                        self.ui.messages.add(f"Maximum health increased by {hp_boost}!")
            if effects.get('forbidden_knowledge'):
                self.ui.messages.add("Forbidden secrets of the Force flood your mind!")
            if effects.get('shadow_mastery'):
                self.ui.messages.add("You become one with the shadows!")
            if effects.get('fear_mastery'):
                self.ui.messages.add("You learn to project pure terror into the minds of your enemies!")
            
            # Add journal entry
            try:
                if hasattr(self.player, 'add_log_entry'):
                    entry = self.player.narrative_text(
                        light_version=f"I absorbed the {artifact_data['name']}. The power courses through me, but at what cost?",
                        dark_version=f"The {artifact_data['name']} is mine! Its power makes me stronger!",
                        balanced_version=f"Absorbed the power of {artifact_data['name']}. The consequences remain to be seen."
                    )
                    self.player.add_log_entry(entry, getattr(self, 'turn_count', 0))
            except Exception:
                pass
                
        except Exception as e:
            self.ui.messages.add(f"Error absorbing artifact: {e}")

    def _enter_surface_special_dungeon(self, dungeon_data, entrance_pos):
        """Enter a special dungeon from the surface map."""
        try:
            from jedi_fugitive.game.special_dungeons import generate_special_dungeon, DUNGEON_TEMPLATES, get_artifact_by_type
            
            dungeon_type = dungeon_data['type']
            template = dungeon_data['template']
            
            # Save surface state
            self.surface_map = self.game_map
            self.surface_enemies = list(getattr(self, 'enemies', []))
            self.surface_items_on_map = list(getattr(self, 'items_on_map', []))
            self.surface_player_pos = (self.player.x, self.player.y)
            self.surface_los_radius = getattr(self.player, 'los_radius', 6)
            
            # Generate special dungeon layout
            layout, entrance_pos, artifact_pos, artifact_type = generate_special_dungeon(dungeon_type)
            
            # Set up dungeon state
            self.game_map = layout
            self.current_special_dungeon = {
                'type': dungeon_type,
                'template': template,
                'surface_entrance': entrance_pos,
                'artifact_claimed': False,
                'artifact_type': artifact_type
            }
            
            # Set player start position (entrance)
            if entrance_pos:
                self.player.x, self.player.y = entrance_pos
            else:
                # Fallback to center
                self.player.x = len(layout[0]) // 2
                self.player.y = len(layout) // 2
            
            # Generate special dungeon features
            self._spawn_special_dungeon_enemies(template, layout)
            
            # Get artifact data
            artifact_data = get_artifact_by_type(artifact_type)
            
            # Store positions and data
            if artifact_pos:
                self.current_special_dungeon['artifact_pos'] = artifact_pos
                self.current_special_dungeon['artifact_data'] = artifact_data
            
            # Find exit position (search for it since it's not returned by generation)
            exit_pos = None
            for y, row in enumerate(layout):
                for x, cell in enumerate(row):
                    if cell == template.get('exit_tile', '◉'):
                        exit_pos = (x, y)
                        break
                if exit_pos:
                    break
            
            if exit_pos:
                self.current_special_dungeon['exit_pos'] = exit_pos
            
            # Clear surface enemies and items for dungeon
            self.enemies = []
            self.items_on_map = []
            
            # Set dungeon atmosphere
            try:
                from jedi_fugitive.game.special_dungeons import get_dungeon_atmosphere_message
                atmosphere_msg = get_dungeon_atmosphere_message(dungeon_type)
                if atmosphere_msg:
                    self.ui.messages.add("═" * 60)
                    self.ui.messages.add(f"╔═ {template['name'].upper()} ═╗".center(60))
                    self.ui.messages.add("═" * 60)
                    self.ui.messages.add(atmosphere_msg)
                    self.ui.messages.add("")
                    
                    # Add discovery journal entry
                    if hasattr(self.player, 'add_log_entry'):
                        entry = self.player.narrative_text(
                            light_version=f"I've discovered the {template['name']}. The dark energy here is overwhelming - I must find the artifact and destroy it.",
                            dark_version=f"The {template['name']} calls to me! Its power will soon be mine!",
                            balanced_version=f"Entered the {template['name']}. The choice between light and dark awaits within."
                        )
                        self.player.add_log_entry(entry, getattr(self, 'turn_count', 0))
            except Exception:
                pass
            
            return True
            
        except Exception as e:
            print(f"Error entering surface special dungeon: {e}")
            return False

    def _destroy_special_artifact(self, artifact_data):
        """Destroy a special artifact (Light Side choice)."""
        try:
            effects = artifact_data['effects']['destroy']
            
            self.ui.messages.add("═══ ARTIFACT DESTROYED ═══")
            self.ui.messages.add(effects['description'])
            self.ui.messages.add("")
            
            # Apply corruption loss
            corruption_loss = effects.get('corruption_loss', 0)
            if corruption_loss > 0:
                current_corruption = getattr(self.player, 'corruption', 50)
                new_corruption = max(0, current_corruption - corruption_loss)
                self.player.corruption = new_corruption
                self.ui.messages.add(f"Corruption decreased by {corruption_loss}! (Now: {new_corruption})")
            
            # Apply positive effects
            if effects.get('mental_clarity'):
                self.ui.messages.add("Your mind becomes clearer and more focused!")
            if effects.get('soul_freedom'):
                self.ui.messages.add("You feel the liberation of trapped souls!")
            if effects.get('knowledge_purge'):
                self.ui.messages.add("Dangerous knowledge is purged from your mind!")
            if effects.get('self_acceptance'):
                self.ui.messages.add("You find peace with your true nature!")
            if effects.get('compassion_awakening'):
                self.ui.messages.add("Your heart opens to compassion and healing!")
            if effects.get('fearlessness'):
                self.ui.messages.add("Fear loses its hold over you!")
            if effects.get('death_resistance'):
                self.ui.messages.add("You gain resistance to the touch of death!")
            
            # Stat bonuses
            willpower_boost = effects.get('willpower_boost', 0)
            if willpower_boost > 0:
                self.ui.messages.add(f"Willpower increased by {willpower_boost}!")
            
            # Add journal entry
            try:
                if hasattr(self.player, 'add_log_entry'):
                    entry = self.player.narrative_text(
                        light_version=f"I destroyed the {artifact_data['name']}. The galaxy is safer without its dark influence.",
                        dark_version=f"I destroyed the {artifact_data['name']}. Perhaps I am growing weak...",
                        balanced_version=f"Destroyed {artifact_data['name']}. Some powers are too dangerous to wield."
                    )
                    self.player.add_log_entry(entry, getattr(self, 'turn_count', 0))
            except Exception:
                pass
                
        except Exception as e:
            self.ui.messages.add(f"Error destroying artifact: {e}")

    # --- Old Republic / Sith Codex integration helpers (safe, non-invasive) ---
    def initialize_canon_lore(self):
        """Populate the Sith codex with canonical entries (alias for compatibility).

        Safe no-op if codex is not present.
        """
        if getattr(self, 'sith_codex', None) is None:
            return
        try:
            # population already happened during initialize(); method kept for API compatibility
            pass
        except Exception:
            return

    def process_sith_lore_discovery(self, player):
        """Check the player's tile for lore_entry and process discovery.

        Safe: if map tiles don't have lore_entry, this is a no-op.
        """
        try:
            # Only require the codex to be present; map may be uninitialized in headless demos.
            if getattr(self, 'sith_codex', None) is None:
                return
            game_map = getattr(self, 'game_map', None)

            # Determine current 'level' for mapping. When on surface current_depth==1 and tomb_floor may be None
            level = getattr(self, 'tomb_floor', None)
            if level is None:
                # fall back to current_depth - 1 (surface -> 0)
                try:
                    level = int(getattr(self, 'current_depth', 1)) - 1
                except Exception:
                    level = 0

            lx = getattr(player, 'x', None)
            ly = getattr(player, 'y', None)
            if lx is None or ly is None:
                return

            # Check a dedicated map_lore mapping first: keys are (level, x, y)
            map_lore = getattr(self, 'map_lore', None)
            category = None; entry_id = None
            if map_lore and (level, lx, ly) in map_lore:
                category, entry_id = map_lore.get((level, lx, ly))
            else:
                # Legacy fallback: tile may carry lore_entry attribute (rare, kept for compatibility)
                try:
                    tile = game_map[ly][lx]
                    if hasattr(tile, 'lore_entry'):
                        try:
                            category, entry_id = tile.lore_entry
                        except Exception:
                            category = None; entry_id = None
                except Exception:
                    category = None; entry_id = None

            # Additional fallback: if a landmark has a 'lore' list (map_landmarks), surface it to messages
            try:
                if not category:
                    landmarks = getattr(self, 'map_landmarks', None) or {}
                    lm = landmarks.get((lx, ly))
                    if lm and isinstance(lm, dict) and lm.get('lore'):
                        lore_lines = lm.get('lore') or []
                        lore_text = ""
                        for ln in lore_lines:
                            try:
                                self.add_message(ln)
                                lore_text += ln + " "
                            except Exception:
                                pass
                        
                        # Add to travel log
                        try:
                            if hasattr(player, 'add_log_entry'):
                                poi_name = lm.get('name', 'a point of interest')
                                entry = player.narrative_text(
                                    light_version=f"Discovered {poi_name}: {lore_text.strip()}",
                                    dark_version=f"Found {poi_name}: {lore_text.strip()} - Knowledge is power!",
                                    balanced_version=f"Explored {poi_name}: {lore_text.strip()}"
                                )
                                player.add_log_entry(entry, getattr(self, 'turn_count', 0))
                        except Exception:
                            pass
                        
                        # prevent repeated triggering
                        try:
                            if 'lore' in lm:
                                del lm['lore']
                                self.map_landmarks[(lx, ly)] = lm
                        except Exception:
                            pass
                        # we've handled the lore; no further sith-codex discovery
                        return
            except Exception:
                pass

            if not category:
                return

            message, is_force_echo = self.sith_codex.discover_entry(category, entry_id)
            if message:
                self.add_message(message)
                if is_force_echo and hasattr(player, 'gain_force_insight'):
                    try:
                        player.gain_force_insight(entry_id)
                    except Exception:
                        pass
                
                # Add to travel log
                try:
                    if hasattr(player, 'add_log_entry'):
                        # Get the actual lore entry for more detail
                        lore_text = ""
                        try:
                            entries = self.sith_codex.categories.get(category, {})
                            if entry_id in entries:
                                lore_text = entries[entry_id].get('text', '')
                        except Exception:
                            pass
                        
                        entry_text = player.narrative_text(
                            light_version=f"Discovered Sith knowledge: {message} - A reminder of the darkness I must resist.",
                            dark_version=f"Uncovered forbidden lore: {message} - More power awaits!",
                            balanced_version=f"Learned Sith lore: {message}"
                        )
                        player.add_log_entry(entry_text, getattr(self, 'turn_count', 0))
                        
                        # Add the actual lore text as a separate entry for completeness
                        if lore_text:
                            player.add_log_entry(f"  > {lore_text}", getattr(self, 'turn_count', 0))
                except Exception:
                    pass

            # Remove discovery so it can't be rediscovered
            try:
                if map_lore and (level, lx, ly) in map_lore:
                    try:
                        del map_lore[(level, lx, ly)]
                    except Exception:
                        pass
                else:
                    try:
                        delattr(tile, 'lore_entry')
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            return

    def show_full_story(self):
        """Display the player's complete travel log - their full story."""
        import sys
        try:
            log = getattr(self.player, 'travel_log', [])
            if not log:
                print("\nNo story to tell yet...\n")
                input("Press Enter to continue...")
                return
            
            print("\n" + "="*80)
            print("YOUR COMPLETE STORY".center(80))
            print("="*80 + "\n")
            
            # Group by significant events for better readability
            print(f"Total entries: {len(log)}\n")
            
            for i, entry in enumerate(log, 1):
                # Handle both dict and string entries for backward compatibility
                if isinstance(entry, dict):
                    turn = entry.get('turn', 0)
                    text = entry.get('text', '')
                else:
                    # Old format: plain string
                    turn = 0
                    text = str(entry)
                
                # Format with turn number and entry
                if turn > 0:
                    print(f"[Turn {turn}] {text}")
                else:
                    print(f"{text}")
                
                # Pause every 20 entries for readability
                if i % 20 == 0 and i < len(log):
                    print(f"\n--- {i}/{len(log)} entries shown ---")
                    try:
                        response = input("Press Enter for more, or 'q' to finish: ").lower()
                        if response == 'q':
                            break
                    except Exception:
                        pass
                    print()
            
            print("\n" + "="*80)
            print("END OF STORY".center(80))
            print("="*80 + "\n")
            
            # Show final statistics
            try:
                print("YOUR FINAL STATISTICS:")
                print(f"  • Turns survived: {getattr(self, 'turn_count', 0)}")
                print(f"  • Enemies defeated: {getattr(self.player, 'kills_count', 0)}")
                print(f"  • Artifacts consumed: {getattr(self.player, 'artifacts_consumed', 0)}")
                print(f"  • Dark corruption: {getattr(self.player, 'dark_corruption', 0)}%")
                print(f"  • Gold collected: {getattr(self.player, 'gold_collected', 0)}")
                print(f"  • Greed Index: {getattr(self.player, 'gold_collected', 0)}")
                print(f"  • Light level: {getattr(self.player, 'light_level', 1)}")
                print(f"  • Dark level: {getattr(self.player, 'dark_level', 1)}")
                
                # Determine final alignment
                corruption = getattr(self.player, 'dark_corruption', 0)
                if corruption >= 70:
                    alignment = "Dark Side Dominates"
                elif corruption >= 40:
                    alignment = "Walking the Dark Path"
                elif corruption >= 15:
                    alignment = "Balanced"
                elif corruption > 0:
                    alignment = "Leaning Light"
                else:
                    alignment = "Pure Light Side"
                print(f"  • Final alignment: {alignment}")
                print()
            except Exception:
                pass
            
            input("Press Enter to exit...")
        except Exception as e:
            print(f"\nError displaying story: {e}\n")
            input("Press Enter to continue...")

    def draw_sith_codex_progress(self):
        """A minimal codex progress drawer: posts a small message with progress.

        This is intentionally tiny to avoid UI churn. Expand into a full panel later.
        """
        if getattr(self, 'sith_codex', None) is None:
            return
        try:
            total = 0
            for cat, entries in self.sith_codex.categories.items():
                total += len(entries)
            discovered = len(self.sith_codex.discovered_entries)
            # use add_message so both curses and headless paths can pick it up
            try:
                self.add_message(f"Sith Codex: {discovered}/{total} discovered")
            except Exception:
                pass
        except Exception:
            return

    def update_command_gui(self):
        try:
            lines = []
            for k in sorted(getattr(self, "key_bindings", {}).keys()):
                desc = self.key_help.get(k, None) or getattr(self.key_bindings[k], "__name__", "cmd")
                lines.append(f"{k}: {desc}")
            # append the splash instructions so the help/command panel surfaces
            # the controls and instructions; include all lines rather than a
            # truncated subset so players don't lose guidance when the message
            # panel is small.
            try:
                for ln in getattr(self, 'splash_instructions', [])[:]:
                    lines.append(ln)
            except Exception:
                pass
            if hasattr(self.ui, "set_command_lines"):
                try: self.ui.set_command_lines(lines); return
                except Exception: pass
            try:
                setattr(self.ui, "key_command_lines", lines)
            except Exception:
                try:
                    if getattr(self.ui, "messages", None):
                        self.ui.messages.add("Commands: " + ", ".join(lines[:6]) + (", ..." if len(lines) > 6 else ""))
                except Exception:
                    pass
        except Exception:
            pass

    def add_message(self, text: str):
        """Safe helper to add a message to the UI message buffer or fallback to stdout.

        This keeps message delivery consistent across headless demos and the curses UI.
        """
        try:
            if getattr(self, 'ui', None) and getattr(self.ui, 'messages', None):
                try:
                    # UIMessageBuffer expects strings or dict-like messages
                    self.ui.messages.add(text)
                    return
                except Exception:
                    pass
        except Exception:
            pass
        # fallback: print so headless demos still surface the message
        try:
            print(text)
        except Exception:
            pass

    def dump_debug_state(self, path="/tmp/jedi_fugitive_debug.txt"):
        try:
            paths = [path, os.path.join(os.getcwd(), "jedi_fugitive_debug.txt")]
            for p in paths:
                try:
                    with open(p, "a") as f:
                        f.write("=== Dark Meridian debug snapshot ===\n")
                        f.write(f"timestamp: {datetime.datetime.now().isoformat()}\n")
                        f.write(f"term size: {getattr(self.ui,'term_h',None)}x{getattr(self.ui,'term_w',None)}\n")
                        try:
                            mh = len(self.game_map); mw = len(self.game_map[0]) if mh else 0
                            f.write(f"map size: {mw}x{mh}\n")
                        except Exception:
                            pass
                        f.write(f"player: x={getattr(self.player,'x',None)} y={getattr(self.player,'y',None)} hp={getattr(self.player,'hp',None)}\n")
                        try:
                            es = getattr(self, "enemies", []) or []
                            f.write(f"enemies: count={len(es)}\n")
                            for e in es[:20]:
                                f.write(f" - {getattr(e,'name',repr(e))} @{getattr(e,'x',None)},{getattr(e,'y',None)} hp={getattr(e,'hp',None)}\n")
                        except Exception:
                            pass
                        vis = getattr(self, "visible", None); expl = getattr(self, "explored", None)
                        f.write(f"visible_count: {len(vis) if vis is not None else 'N/A'} explored_count: {len(expl) if expl is not None else 'N/A'}\n")
                        panels = getattr(self.ui, "panels", None)
                        f.write(f"ui.panels keys: {list(panels.keys()) if isinstance(panels, dict) else repr(panels)}\n")
                        f.write("=== end snapshot ===\n\n")
                except Exception:
                    pass
            try:
                sys.stderr.write("JediFugitive: wrote debug snapshot to /tmp/jedi_fugitive_debug.txt and ./jedi_fugitive_debug.txt\n")
                sys.stderr.flush()
            except Exception:
                pass
        except Exception:
            pass

    def draw(self):
        # prefer centralized renderer
        try:
            ui_renderer.draw(self)
            return
        except Exception:
            pass

        # fallback minimal draw (so terminal never blank)
        try:
            try: self.stdscr.erase()
            except Exception: pass
            try:
                s = f"Map: {len(self.game_map[0]) if self.game_map else 0}x{len(self.game_map) if self.game_map else 0}  Enemies:{len(getattr(self,'enemies',[]))}  HP:{getattr(self.player,'hp',None)}"
                self.stdscr.addstr(0, 0, s[: (self.ui.term_w - 1) if hasattr(self.ui,'term_w') else 80])
            except Exception:
                pass
            try:
                if hasattr(self.ui, "messages") and getattr(self.ui, "messages", None) is not None:
                    msgs = self.ui.messages
                    lines = []
                    if hasattr(msgs, "messages"):
                        lines = msgs.messages[-6:]
                    elif hasattr(msgs, "get_lines"):
                        lines = msgs.get_lines()[-6:]
                    for i, m in enumerate(lines):
                        try:
                            text = m.get("text", str(m)) if isinstance(m, dict) else str(m)
                            self.stdscr.addstr(2 + i, 0, text[: (self.ui.term_w - 1) if hasattr(self.ui, 'term_w') else 80])
                        except Exception:
                            pass
            except Exception:
                pass
            try: self.stdscr.refresh()
            except Exception: pass
            # small, safe codex progress indicator
            try:
                if getattr(self, 'sith_codex', None):
                    self.draw_sith_codex_progress()
            except Exception:
                pass
        except Exception:
            try:
                self.dump_debug_state()
            except Exception:
                pass

    def handle_npc_interactions(self):
        """Check for NPC interactions at player position"""
        player_pos = (self.player.x, self.player.y)
        
        # Check for quest NPCs first
        if player_pos in self.npcs_on_map:
            npc = self.npcs_on_map[player_pos]
            
            # If we have the quest manager, handle quest interactions
            if self.quest_manager:
                self.interact_with_npc(self.player.x, self.player.y)
                return npc
            
            # Fallback to old NPC system
            return npc
            
        return None
    
    def handle_input(self, key):
        try:
            res = input_handler.handle_input(self, key)
            return res
        except Exception:
            # fallback: quit
            try:
                if key in (ord("q"), 27):
                    self.running = False
                    try: self.ui.messages.add("Quitting...") 
                    except Exception: pass
                    return True
            except Exception:
                pass
        return False

    @staticmethod
    def show_splash_static(term_w):
        """Show an immersive Star Wars inspired splash. Static version for pre-curses display."""
        try:
            box_width = max(20, min(term_w - 10, 80))
            splash = [
                "",
                f"    ╔{'═' * box_width}╗",
                f"    ║{' ' * box_width}║",
                f"    ║{'DARK MERIDIAN: ECHOES OF THE FALLEN'.center(box_width)}║",
                f"    ║{' ' * box_width}║",
                f"    ╚{'═' * box_width}╝",
                "",
                "Your ship has crashed on a remote Sith world. The dark side permeates this place.",
                "Ancient tombs and forgotten ruins dot the landscape - Sith sanctuaries corrupting",
                "the very fabric of the Force.",
                "",
                "Your mission: Recover stolen Jedi artifacts from the tombs and escape alive.",
                "But the Sith have corrupted these sacred relics... and the darkness hungers for you.",
                "",
                "═" * min(term_w, 80),
                "",
            ]
            # Add a small lightsaber ASCII art for embellishment
            splash += [
                "        /\\",
                "       //\\\\          THE JEDI CODE:",
                "      ///\\\\\\         There is no emotion, there is peace.",
                "     ////\\\\\\\\        There is no ignorance, there is knowledge.",
                "    /////\\\\\\\\\\       There is no passion, there is serenity.",
                "   //////\\\\\\\\\\\\      There is no chaos, there is harmony.",
                "  ///////\\\\\\\\\\\\\\     There is no death, there is the Force.",
                " ////////\\\\\\\\\\\\\\\\",
                "/////////\\\\\\\\\\\\\\\\\\",
                "         |",
                "         |          But here, in this dark place, will you hold true?",
                "         |",
                "",
                "═" * min(term_w, 80),
                "",
            ]
            # short, friendly instructions to display under the splash
            instructions = [
                "CONTROLS:",
                "  Move: ↑↓←→ arrows or hjkl    Diagonal: ybn or numpad 7913",
                "  g=pickup e=equip u=use d=drop  x=inspect j=journal f=force c=compass m=meditate  ?=help q=quit",
                "",
                "OBJECTIVE:",
                "  1. Infiltrate Sith tombs (marked 'D') to recover 3 corrupted Jedi artifacts",
                "  2. Cleanse your spirit - resist the Dark Side's corruption",
                "  3. Use artifacts to power the comms terminal (C) and call for extraction",
                "  4. Defeat whoever comes for you and escape to your ship (S)",
                "",
                "SURVIVAL TIPS:",
                "  • Manage your stress - high stress increases Force costs and reduces accuracy",
                "  • Light Side (calm, defensive) or Dark Side (aggressive, powerful) choices affect your fate",
                "  • Use Force abilities wisely - they consume Force points that regenerate slowly",
                "  • Equipment improves your stats - vibroblades add attack, shields add defense",
                "  • Meditate when safe to reduce stress and restore balance",
                "",
            ]
            # Always print splash lines to stdout
            for ln in splash:
                print(ln)
                sys.stdout.flush()
            print("")
            sys.stdout.flush()
            for ln in instructions:
                print(ln)
                sys.stdout.flush()
        except Exception:
            pass

    def _trigger_victory(self):
        """Trigger victory sequence with alignment-based Jedi message."""
        try:
            corruption = getattr(self.player, 'dark_corruption', 0)
            alignment = self.player.get_alignment() if hasattr(self.player, 'get_alignment') else 'balanced'
            
            # Generate Jedi Council message based on corruption
            if corruption <= 20:
                # Pure Light - Success
                jedi_message = [
                    "",
                    "═══════════════════════════════════════════════════════",
                    "    TRANSMISSION FROM JEDI COUNCIL - CORUSCANT",
                    "═══════════════════════════════════════════════════════",
                    "",
                    "Padawan, your beacon has been received.",
                    "",
                    "The artifacts you recovered resonate with purified Light.",
                    "You have cleansed three corrupted tombs and resisted the",
                    "Dark Side's temptations. Your devotion to the Code shines",
                    "as a beacon of hope in these dark times.",
                    "",
                    "The Sith sought to corrupt these ancient relics, but you",
                    "have restored balance. Well done, Jedi.",
                    "",
                    "A rescue team is inbound. You will be honored upon return.",
                    "",
                    "May the Force be with you, always.",
                    "═══════════════════════════════════════════════════════",
                ]
            elif corruption <= 40:
                # Light - Success with caution
                jedi_message = [
                    "",
                    "═══════════════════════════════════════════════════════",
                    "    TRANSMISSION FROM JEDI COUNCIL - CORUSCANT",
                    "═══════════════════════════════════════════════════════",
                    "",
                    "We have received your signal.",
                    "",
                    "You have recovered the artifacts, but we sense darkness",
                    "clinging to them... and to you. The Sith tombs have left",
                    "their mark. The corruption runs deeper than expected.",
                    "",
                    "The artifacts will need extensive purification rituals.",
                    "As will you. Return to the Temple immediately.",
                    "",
                    "The Jedi Council will oversee your recovery and debriefing.",
                    "A rescue team is inbound.",
                    "═══════════════════════════════════════════════════════",
                ]
            elif corruption <= 59:
                # Balanced - Uncertain fate
                jedi_message = [
                    "",
                    "═══════════════════════════════════════════════════════",
                    "    TRANSMISSION FROM JEDI COUNCIL - CORUSCANT",
                    "═══════════════════════════════════════════════════════",
                    "",
                    "Your beacon... we sense great turmoil in you.",
                    "",
                    "The artifacts you recovered pulse with conflicting energies.",
                    "Light and Dark intertwined. You walk the knife's edge",
                    "between salvation and damnation.",
                    "",
                    "The tombs have changed you. The Council has grave concerns",
                    "about the methods you employed to survive.",
                    "",
                    "A team will retrieve you AND the artifacts. You will",
                    "submit to the Council's judgment upon return.",
                    "",
                    "Your future with the Order hangs in the balance.",
                    "═══════════════════════════════════════════════════════",
                ]
            elif corruption <= 79:
                # Dark - Rejected
                jedi_message = [
                    "",
                    "═══════════════════════════════════════════════════════",
                    "    TRANSMISSION FROM JEDI COUNCIL - CORUSCANT",
                    "═══════════════════════════════════════════════════════",
                    "",
                    "We sense darkness in you, fallen one.",
                    "",
                    "The artifacts you recovered... they scream with anguish.",
                    "Rather than purifying them, you have stained them further",
                    "with your actions. The Sith corruption has claimed you.",
                    "",
                    "You sought to use the Dark Side as a tool, but it has",
                    "become your master. The blood on your hands cannot be",
                    "washed away.",
                    "",
                    "No rescue team will be sent. You are hereby EXPELLED",
                    "from the Jedi Order. Keep the artifacts - they are as",
                    "tainted as you are.",
                    "",
                    "May you find redemption in exile... if it is not too late.",
                    "═══════════════════════════════════════════════════════",
                ]
            else:
                # Pure Dark - Enemy of the Jedi
                jedi_message = [
                    "",
                    "═══════════════════════════════════════════════════════",
                    "    TRANSMISSION FROM JEDI COUNCIL - CORUSCANT",
                    "═══════════════════════════════════════════════════════",
                    "",
                    "We know what you have become.",
                    "",
                    "The artifacts you 'recovered' are weapons now. You have",
                    "not cleansed them - you have EMBRACED their corruption.",
                    "The Sith tombs were not your prison... they were your",
                    "academy.",
                    "",
                    "You are no longer a Jedi. You are SITH.",
                    "",
                    "Your beacon was a fatal mistake - it has revealed your",
                    "location. A strike team of Jedi Masters is en route.",
                    "",
                    "They come not to rescue, but to ELIMINATE the threat",
                    "you pose.",
                    "",
                    "There is no redemption for one so lost to darkness.",
                    "═══════════════════════════════════════════════════════",
                ]
            
            # Display message
            try:
                for line in jedi_message:
                    self.ui.messages.add(line)
            except Exception:
                pass
            
            # Add victory journal entry
            try:
                if corruption <= 20:
                    victory_entry = "[VICTORY] You activated the distress beacon. The Jedi Council's transmission filled you with hope - your mission is complete. The artifacts are purified, and your devotion to the Light Side has earned you honor. Rescue is coming."
                elif corruption <= 40:
                    victory_entry = "[VICTORY] The beacon is active. The Council's words were cautious - they sense the darkness that touched you in the tombs. You survived, but at what cost? You will return to face judgment and purification."
                elif corruption <= 59:
                    victory_entry = "[VICTORY] You reached the beacon, but the Council's message chills your blood. They know what you did to survive. The artifacts are tainted, as are you. Your future with the Order is uncertain. A rescue team comes... but also judgment."
                elif corruption <= 79:
                    victory_entry = "[VICTORY?] The beacon transmitted your location, but the Council's response was exile. You are no longer a Jedi in their eyes. The darkness consumed too much of who you were. You survived the tombs, but lost yourself. No rescue will come."
                else:
                    victory_entry = "[VICTORY?] You activated the beacon, sealing your fate. The Council knows you have fallen completely to the Dark Side. They don't send rescue - they send executioners. Jedi Masters hunt you now. You escaped the tombs only to face a greater threat. Was it worth it?"
                
                self.player.add_log_entry(victory_entry, self.turn_count)
            except Exception:
                try:
                    self.player.add_log_entry("[VICTORY] You have activated the distress beacon. Your mission is complete.", self.turn_count)
                except Exception:
                    pass
            
            # Set victory flag
            self.victory = True
            self.running = False
            
        except Exception as e:
            # Fallback
            self.victory = True
            self.running = False

    def show_victory_stats(self):
        """Show victory screen with statistics and triumph message."""
        try:
            term_w = getattr(self, 'term_w', 80)
            turns = getattr(self, 'turn_count', 0)
            level = getattr(self.player, 'level', 1)
            artifacts = getattr(self, 'artifacts_collected', 0)
            corruption = getattr(self.player, 'dark_corruption', 0)
            
            # Determine path based on corruption (inverted from alignment)
            if corruption <= 30:
                path = "Light Side"
                ending = "You escaped with your honor intact, a beacon of hope in dark times."
            elif corruption >= 70:
                path = "Dark Side"
                ending = "You escaped, but at what cost? The darkness has left its mark on your soul."
            else:
                path = "Gray"
                ending = "You walked the line between light and dark, and emerged changed but alive."
            
            victory_art = [
                "",
                "██    ██ ██  ██████ ████████  ██████  ██████  ██    ██ ",
                "██    ██ ██ ██         ██    ██    ██ ██   ██  ██  ██  ",
                "██    ██ ██ ██         ██    ██    ██ ██████    ████   ",
                " ██  ██  ██ ██         ██    ██    ██ ██   ██    ██    ",
                "  ████   ██  ██████    ██     ██████  ██   ██    ██    ",
                "",
                "    ╔═══════════════════════════════════════════════════╗",
                "    ║  THE FORCE IS WITH YOU - YOU HAVE ESCAPED!       ║",
                "    ╚═══════════════════════════════════════════════════╝",
                "",
            ]
            
            codex_count = len(getattr(self.player, 'sith_lore_known', set()))
            gold = getattr(self.player, 'gold_collected', 0)
            
            stats = [
                "═" * min(term_w, 80),
                "MISSION COMPLETE",
                "═" * min(term_w, 80),
                "",
                f"Turns Survived: {turns}",
                f"Final Level: {level}",
                f"Artifacts Recovered: {artifacts}/3",
                f"Lore Discovered: {codex_count} entries",
                f"Path Chosen: {path} (Corruption: {corruption}/100)",
                f"Gold Collected: {gold}",
                f"Greed Index: {gold}",
                "",
                ending,
                "",
                "You have proven yourself a survivor. The Sith may rule this world,",
                "but they could not claim your life. The Force honors courage and cunning.",
                "",
            ]
            
            # Add persistent stats
            try:
                from jedi_fugitive.utils.game_stats import get_game_stats
                game_stats = get_game_stats()
                game_stats.record_victory(
                    player_level=level,
                    enemies_killed=getattr(self.player, 'kills_count', 0),
                    turns_taken=self.turn_count
                )
                stats.append("")
                stats.append("═══ LIFETIME STATISTICS ═══")
                stats.append(f"Total Runs: {game_stats.get_total_runs()}")
                stats.append(f"Victories: {game_stats.get_total_victories()}")
                stats.append(f"Deaths: {game_stats.get_total_deaths()}")
                stats.append(f"Win Rate: {game_stats.get_win_rate():.1f}%")
                stats.append(f"Total Kills: {game_stats.get_total_kills()}")
                stats.append(f"K/D Ratio: {game_stats.get_kill_death_ratio():.2f}")
                if game_stats.get_current_win_streak() > 0:
                    stats.append(f"Win Streak: {game_stats.get_current_win_streak()}")
            except Exception as e:
                pass
            
            stats.extend([
                "",
                "May the Force be with you, always.",
                "",
                "═" * min(term_w, 80),
            ])
            
            # Print victory
            for ln in victory_art:
                print(ln.center(term_w))
                sys.stdout.flush()
            
            for ln in stats:
                print(ln.center(term_w))
                sys.stdout.flush()
            
            # Automatically show full story
            try:
                self.show_full_story()
            except Exception:
                pass
            
            # Offer play again option
            try:
                print("\n" + "="*term_w)
                print("[P] Play Again")
                print("[Q] Quit")
                print("="*term_w)
                choice = input("\nYour choice: ").strip().upper()
                
                if choice == 'P':
                    # Return True to signal restart
                    return True
                else:
                    return False
            except Exception:
                return False
        except Exception:
            print("VICTORY!")
            print("You have escaped!")

    def show_death_stats(self):
        """Show post-game death statistics with a taunting Sith message."""
        try:
            term_w = getattr(self, 'term_w', 80)
            turns = getattr(self, 'turn_count', 0)
            death_cause = getattr(self, 'death_cause', 'unknown')
            level = getattr(self.player, 'level', 1)
            death_biome = getattr(self, 'death_biome', 'unknown')
            death_pos = getattr(self, 'death_pos', (None, None))
            pos_str = f"{death_pos[0]}, {death_pos[1]}" if death_pos[0] is not None else 'unknown'

            # Taunting messages based on performance
            taunts = [
                "Pathetic. Even a youngling could have lasted longer. The Force weeps for your inadequacy.",
                "Your feeble attempts amuse me, Jedi. Return when you've learned to crawl.",
                "The Dark Side claims another failure. Your light was but a flicker in the void.",
                "How disappointing. I expected more from one who claims the Jedi title.",
                "Your death serves as a reminder: the Sith endure, the weak perish.",
                "Barely a challenge. The galaxy will forget your name before your body cools.",
                "Such weakness. The Force rejects those unworthy of its power.",
                "You fell like so many before you. Join the endless cycle of failure.",
                "A momentary distraction, nothing more. The dark side hungers for more worthy prey.",
                "Your struggle was entertaining, but ultimately meaningless. Rest in obscurity."
            ]
            
            # Choose taunt based on turns survived
            if turns < 50:
                taunt = taunts[0]  # Very poor
            elif turns < 100:
                taunt = taunts[1]  # Poor
            elif turns < 200:
                taunt = taunts[2]  # Average
            elif turns < 500:
                taunt = taunts[3]  # Good
            else:
                taunt = taunts[4]  # Impressive, but still taunting

            lines = [
                "GAME OVER",
                "",
                f"You survived {turns} turns.",
                f"Cause of death: {death_cause}",
                f"Final level: {level}",
                f"Location: {pos_str} in {death_biome}",
                "",
                f"Sith Lord: \"{taunt}\"",
                "",
                "Press any key to exit."
            ]

            # Lightsaber duel ASCII art for defeat
            defeat_art = [
                "                    GAME OVER                    ",
                "",
                "              The Dark Side Prevails             ",
                "",
                "                      /\\                         ",
                "                     |  |                        ",
                "                     |  |        ___             ",
                "                     |  |       |   |            ",
                "          ___        |  |       |   |            ",
                "         |   |       |  |       |   |            ",
                "    ___  |   |       |  |    ___|   |            ",
                "   |   |_|   |    ___|  |   |   |   |___         ",
                "   |   |     |___|      |___|       |   |        ",
                "   |    JEDI     |   VS  |    SITH     |         ",
                "   |_____________|       |_____________|         ",
                "        /     \\              /     \\             ",
                "       /       \\            /       \\            ",
                "      |  FALLEN |          | VICTOR  |           ",
                "       \\_______/            \\_______/            ",
                "",
                "     Your lightsaber dims as darkness falls...   ",
                "",
            ]

            # Build stats lines
            stats_lines = [
                "",
                f"You survived {turns} turns.",
                f"Cause of death: {death_cause}",
                f"Final level: {level}",
                f"Location: {pos_str} in {death_biome}",
            ]
            
            # Add player stats
            try:
                kills = getattr(self.player, 'kills_count', 0)
                artifacts = getattr(self.player, 'artifacts_consumed', 0)
                corruption = getattr(self.player, 'dark_corruption', 0)
                gold = getattr(self.player, 'gold_collected', 0)
                if kills > 0:
                    stats_lines.append(f"Enemies defeated: {kills}")
                if artifacts > 0:
                    stats_lines.append(f"Artifacts consumed: {artifacts}")
                    stats_lines.append(f"Dark corruption: {corruption}%")
                if gold > 0:
                    stats_lines.append(f"Gold collected: {gold}")
                    stats_lines.append(f"Greed Index: {gold}")
            except Exception:
                pass
            
            stats_lines.extend([
                "",
                f"Sith Lord: \"{taunt}\"",
                "",
                "The Dark Side has claimed another victim...",
            ])
            
            # Add persistent stats
            try:
                from jedi_fugitive.utils.game_stats import get_game_stats
                game_stats = get_game_stats()
                game_stats.record_death(
                    player_level=level,
                    enemies_killed=getattr(self.player, 'kills_count', 0),
                    turns_taken=self.turn_count
                )
                stats_lines.append("")
                stats_lines.append("=== LIFETIME STATISTICS ===")
                stats_lines.append(f"Total Runs: {game_stats.get_total_runs()}")
                stats_lines.append(f"Victories: {game_stats.get_total_victories()}")
                stats_lines.append(f"Deaths: {game_stats.get_total_deaths()}")
                stats_lines.append(f"Win Rate: {game_stats.get_win_rate():.1f}%")
                stats_lines.append(f"Total Kills: {game_stats.get_total_kills()}")
                stats_lines.append(f"K/D Ratio: {game_stats.get_kill_death_ratio():.2f}")
            except Exception as e:
                pass
            
            # Add travel log summary
            try:
                log = getattr(self.player, 'travel_log', [])
                if log:
                    stats_lines.append("")
                    stats_lines.append("=== YOUR FINAL MOMENTS ===")
                    for entry in log[-5:]:  # Show last 5 log entries
                        text = entry.get('text', '')
                        stats_lines.append(f"• {text}")
            except Exception:
                pass
            
            # Always print to stdout first
            print("\n" + "="*term_w)
            sys.stdout.flush()
            for ln in defeat_art:
                print(ln.center(term_w))
                sys.stdout.flush()
            print("")
            sys.stdout.flush()
            for ln in stats_lines:
                print(ln.center(term_w))
                sys.stdout.flush()
            print("="*term_w + "\n")
            sys.stdout.flush()  # Ensure output is visible
            
            # Automatically show full story
            try:
                self.show_full_story()
            except Exception:
                pass
            
            # Offer play again option
            try:
                print("\n" + "="*term_w)
                print("[P] Play Again")
                print("[Q] Quit")
                print("="*term_w)
                choice = input("\nYour choice: ").strip().upper()
                
                if choice == 'P':
                    # Return True to signal restart
                    return True
                else:
                    return False
            except Exception:
                return False
        except Exception:
            print("GAME OVER")
            try:
                choice = input("Play again? [P/Q]: ").strip().upper()
                return choice == 'P'
            except Exception:
                return False

    def _try_move_player(self, dx: int, dy: int) -> bool:
        """
        Attempt to move the player by dx,dy. Returns True if moved.
        """
        try:
            nx = int(getattr(self.player, "x", 0) + dx)
            ny = int(getattr(self.player, "y", 0) + dy)
            mh = len(self.game_map); mw = len(self.game_map[0]) if mh else 0
            if not (0 <= nx < mw and 0 <= ny < mh):
                return False
            target = self.game_map[ny][nx]
            # treat numeric tiles as strings too
            try:
                tstr = str(target)
            except Exception:
                tstr = ""
            
            # DEBUG: Log target tile for every move
            try:
                if tstr == 'D':
                    with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                        fh.write(f"!!! MOVING TO 'D' TILE at ({nx}, {ny}), target={repr(target)}, tstr='{tstr}'\n")
            except: pass
            walkable = True
            # Simple non-walkable check: only block walls and terrain obstacles
            try:
                # NON-walkable tiles (everything else is walkable)
                non_walkable = {
                    '#',  # walls
                    '~',  # dunes (impassable terrain)
                    'r',  # rocks (large obstacles)
                    'T',  # trees (blocking)
                }
                
                if tstr in non_walkable:
                    walkable = False
            except Exception:
                pass

            if not walkable:
                return False

            # actually move
            try:
                self.player.x = nx
                self.player.y = ny
            except Exception:
                pass

            # After moving: check for stairs in tombs and trigger floor change
            try:
                in_tomb = hasattr(self, 'tomb_levels') and hasattr(self, 'tomb_stairs') and hasattr(self, 'tomb_floor')
                if in_tomb:
                    tile = str(self.game_map[ny][nx])
                    stairs_down = getattr(Display, 'STAIRS_DOWN', '>')
                    stairs_up = getattr(Display, 'STAIRS_UP', '<')
                    if tile == str(stairs_down):
                        changed = self.change_floor(1)
                        if changed and getattr(self.ui, 'messages', None):
                            self.ui.messages.add("You descend the stairs...")
                        return True
                    elif tile == str(stairs_up):
                        changed = self.change_floor(-1)
                        if changed and getattr(self.ui, 'messages', None):
                            self.ui.messages.add("You climb the stairs...")
                        return True
            except Exception:
                pass

            # DEBUG: Log every move and check for tomb proximity
            try:
                with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                    fh.write(f"Player moved to ({nx}, {ny}), tile='{self.game_map[ny][nx]}'\n")
                    tomb_entrances = getattr(self, 'tomb_entrances', set())
                    if (nx, ny) in tomb_entrances:
                        fh.write(f"  ⚠️ PLAYER IS NOW ON TOMB ENTRANCE!\n")
            except: pass

            # Check if player is near a tomb entrance and notify them
            try:
                tomb_entrances = getattr(self, 'tomb_entrances', set())
                if tomb_entrances:
                    for dx_check in [-1, 0, 1]:
                        for dy_check in [-1, 0, 1]:
                            if dx_check == 0 and dy_check == 0:
                                continue  # Don't check current position (handled later)
                            check_x = nx + dx_check
                            check_y = ny + dy_check
                            if (check_x, check_y) in tomb_entrances:
                                # Check if we haven't recently warned about this tomb
                                if not hasattr(self, '_last_tomb_warning') or self._last_tomb_warning != (check_x, check_y):
                                    self._last_tomb_warning = (check_x, check_y)
                                    direction = ""
                                    if dx_check < 0:
                                        direction = "west"
                                    elif dx_check > 0:
                                        direction = "east"
                                    if dy_check < 0:
                                        direction = "north" if not direction else f"{direction}-north"
                                    elif dy_check > 0:
                                        direction = "south" if not direction else f"{direction}-south"
                                    
                                    try:
                                        self.ui.messages.add(f"⚠️ A dark tomb entrance looms to the {direction}...")
                                        self.ui.messages.add(f"Walk onto it to enter the depths.")
                                    except:
                                        pass
                                break
            except Exception:
                pass

            # After moving: process Sith lore discovery
            try:
                self.process_sith_lore_discovery(self.player)
            except Exception:
                pass
            
            # After moving: track biome visits and check for encounters
            try:
                from jedi_fugitive.game import biome_encounters
                current_biome = getattr(self, 'current_biome', 'crash_site')
                
                # Track biome visits
                if not hasattr(self, 'visited_biomes'):
                    self.visited_biomes = set()
                visited_before = current_biome in self.visited_biomes
                self.visited_biomes.add(current_biome)
                
                # Check if encounter should spawn (100-150 turn intervals)
                turns_since_last = self.turn_count - self.last_encounter_turn
                corruption = getattr(self.player, 'corruption', 50)
                
                if biome_encounters.should_spawn_encounter(current_biome, turns_since_last, corruption, visited_before):
                    self.last_encounter_turn = self.turn_count
                    try:
                        encounter = biome_encounters.get_biome_encounter(current_biome)
                        
                        if encounter:
                            # Spawn encounter marker on map ahead of player
                            # Place marker 3-8 tiles away in a random direction
                            import random
                            distance = random.randint(3, 8)
                            angle = random.uniform(0, 2 * 3.14159)
                            offset_x = int(distance * __import__('math').cos(angle))
                            offset_y = int(distance * __import__('math').sin(angle))
                            
                            marker_x = nx + offset_x
                            marker_y = ny + offset_y
                            
                            # Ensure marker is within bounds
                            mh = len(self.game_map)
                            mw = len(self.game_map[0]) if mh else 0
                            if 0 <= marker_x < mw and 0 <= marker_y < mh:
                                # Check if tile is walkable (not a wall)
                                marker_tile = str(self.game_map[marker_y][marker_x])
                                if marker_tile not in {'#', '~', 'r', 'T'}:
                                    # Store encounter data
                                    if not hasattr(self, 'pending_encounters'):
                                        self.pending_encounters = {}
                                    self.pending_encounters[(marker_x, marker_y)] = encounter
                                    
                                    # Place visual marker '?' on map
                                    self.game_map[marker_y][marker_x] = '?'
                                    
                                    # Notify player
                                    direction = "nearby"
                                    if offset_x > 2:
                                        direction = "to the east"
                                    elif offset_x < -2:
                                        direction = "to the west"
                                    if offset_y > 2:
                                        direction = "to the south" if abs(offset_x) < 2 else f"{direction} and south"
                                    elif offset_y < -2:
                                        direction = "to the north" if abs(offset_x) < 2 else f"{direction} and north"
                                    
                                    self.ui.messages.add(f"[!] You sense something unusual {direction}...")
                                    self.ui.messages.add(f"(Look for the '?' marker on the map)")
                    except Exception as e:
                        pass
            except Exception:
                pass

            # After moving: check for items to pick up automatically
            try:
                for it in list(getattr(self, 'items_on_map', []) or []):
                    try:
                        if it.get('x') == nx and it.get('y') == ny:
                            # attempt to add to inventory
                            try:
                                from jedi_fugitive.game.inventory import add_item_to_inventory
                                added = add_item_to_inventory(self.player, it)
                                if added:
                                    try:
                                        self.ui.messages.add(f"You pick up {it.get('name', 'an item')}.")
                                    except Exception:
                                        pass
                                    # remove from map
                                    try:
                                        if hasattr(self, 'items_on_map') and self.items_on_map:
                                            self.items_on_map.remove(it)
                                        self.game_map[ny][nx] = getattr(Display, 'FLOOR', '.')
                                    except Exception as e:
                                        log_error("ITEM_PICKUP_ERROR", "Failed to remove item from map", e)
                                        pass
                            except Exception:
                                pass
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # After moving: check for equipment drops to pick up automatically
            try:
                if hasattr(self, 'equipment_drops') and (nx, ny) in self.equipment_drops:
                    drop_data = self.equipment_drops[(nx, ny)]
                    drop_type = drop_data.get('type', 'weapon')
                    dropped_item = drop_data.get('item')
                    item_name = drop_data.get('name', 'Unknown Item')
                    item_rarity = drop_data.get('rarity', 'Common')
                    
                    # Add equipment to player inventory
                    try:
                        if not hasattr(self.player, 'inventory'):
                            self.player.inventory = []
                        
                        # Create inventory item based on type
                        if drop_type == 'weapon':
                            inventory_item = {
                                'name': item_name,
                                'type': 'weapon',
                                'weapon_data': dropped_item,
                                'rarity': item_rarity
                            }
                        elif drop_type == 'armor':
                            inventory_item = {
                                'name': item_name,
                                'type': 'armor',
                                'armor_data': dropped_item,
                                'rarity': item_rarity,
                                'defense': getattr(dropped_item, 'defense', 0),
                                'evasion_mod': getattr(dropped_item, 'evasion_mod', 0),
                                'hp_bonus': getattr(dropped_item, 'hp_bonus', 0),
                                'slot': getattr(dropped_item, 'slot', 'body')
                            }
                        else:  # consumable
                            inventory_item = {
                                'name': item_name,
                                'type': 'consumable',
                                'id': dropped_item.get('id', 'unknown'),
                                'effect': dropped_item.get('effect', {}),
                                'description': dropped_item.get('description', '')
                            }
                        
                        self.player.inventory.append(inventory_item)
                        
                        # Message with rarity indicator
                        if item_rarity in ['Legendary', 'Epic']:
                            self.ui.messages.add(f"★★★ You pick up the {item_rarity.upper()} {item_name}! ★★★")
                        elif item_rarity == 'Rare':
                            self.ui.messages.add(f"★★ You pick up the RARE {item_name}! ★★")
                        elif item_rarity == 'Uncommon':
                            self.ui.messages.add(f"★ You pick up {item_name}")
                        else:
                            self.ui.messages.add(f"You pick up {item_name}")
                        
                        # Remove equipment from map
                        del self.equipment_drops[(nx, ny)]
                        if self.game_map[ny][nx] == 'E':
                            self.game_map[ny][nx] = getattr(Display, 'FLOOR', '.')
                    except Exception:
                        pass
            except Exception:
                pass

            # After moving: check for landmarks
            try:
                for (lx, ly), info in list(getattr(self, 'map_landmarks', {}).items()):
                    try:
                        if lx == nx and ly == ny:
                            # show description and lore
                            desc = info.get('description', '')
                            lore = info.get('lore', [])
                            if desc:
                                try:
                                    self.ui.messages.add(desc)
                                except Exception:
                                    pass
                            for ln in lore:
                                try:
                                    self.ui.messages.add(ln)
                                except Exception:
                                    pass
                            # handle Sith lore
                            sith_lore = info.get('sith_lore')
                            if sith_lore:
                                try:
                                    if not hasattr(self.player, 'sith_lore_known'):
                                        self.player.sith_lore_known = set()
                                    key = (sith_lore['category'], sith_lore['entry_id'])
                                    if key not in self.player.sith_lore_known:
                                        self.player.sith_lore_known.add(key)
                                        # perhaps grant force echo
                                        force_echo = sith_lore.get('force_echo', False)
                                        if force_echo:
                                            try:
                                                self.player.force_points = min(getattr(self.player, 'max_force_points', 10), getattr(self.player, 'force_points', 0) + 1)
                                                self.ui.messages.add("You feel a surge of the Force.")
                                            except Exception:
                                                pass
                                except Exception:
                                    pass
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # After moving: handle stepping on special tiles (tombs / dungeon entrances / sith keep)
            try:
                # DEBUG: Log entry to special tiles section
                try:
                    if tstr == 'D':
                        with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                            fh.write(f">>> Entered 'handle stepping on special tiles' section for 'D' at ({nx}, {ny})\n")
                except: pass
                
                # Check for Sith Keep entrance
                if tstr == 'K':
                    try:
                        self._handle_sith_keep_entrance()
                    except Exception as e:
                        self.ui.messages.add(f"Error entering Sith Keep: {e}")
                
                # DEBUG
                try:
                    if tstr == 'D':
                        with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                            fh.write(f">>> Passed Sith Keep check\n")
                except: pass
                
                # Check for Sith Keep exit
                if tstr == 'E' and getattr(self, 'in_sith_keep', False):
                    try:
                        self._exit_sith_keep()
                    except Exception as e:
                        self.ui.messages.add(f"Error exiting Sith Keep: {e}")
                
                # DEBUG
                try:
                    if tstr == 'D':
                        with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                            fh.write(f">>> Passed Sith Keep exit check\n")
                except: pass
                
                # Check for Special Dungeon entrance
                special_dungeon_data = None
                try:
                    # Check current level for special dungeons
                    if hasattr(self, 'tomb_special_dungeons') and hasattr(self, 'tomb_floor'):
                        current_level = getattr(self, 'tomb_floor', 0)
                        if current_level < len(self.tomb_special_dungeons):
                            level_dungeons = self.tomb_special_dungeons[current_level]
                            special_dungeon_data = level_dungeons.get((nx, ny))
                    elif hasattr(self, 'special_dungeons'):
                        # Surface level special dungeons
                        special_dungeon_data = self.special_dungeons.get((nx, ny))
                except Exception as ex:
                    try:
                        if tstr == 'D':
                            with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                                fh.write(f">>> EXCEPTION in special dungeon check: {ex}\n")
                    except: pass
                
                # DEBUG
                try:
                    if tstr == 'D':
                        with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                            fh.write(f">>> Passed special dungeon data check, special_dungeon_data={special_dungeon_data}\n")
                except: pass
                
                if special_dungeon_data:
                    try:
                        with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                            fh.write(f">>> FOUND special_dungeon_data! Calling _handle_special_dungeon_entrance\n")
                    except: pass
                    try:
                        self._handle_special_dungeon_entrance(special_dungeon_data, nx, ny)
                    except Exception as e:
                        self.ui.messages.add(f"Error entering special dungeon: {e}")
                
                # DEBUG
                try:
                    if tstr == 'D':
                        with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                            fh.write(f">>> Passed special dungeon entrance handler\n")
                except: pass
                
                # Check for Special Dungeon artifact
                if hasattr(self, 'current_special_dungeon'):
                    try:
                        dungeon = self.current_special_dungeon
                        artifact_pos = dungeon.get('artifact_pos') if dungeon and hasattr(dungeon, 'get') else None
                        if artifact_pos and (nx, ny) == artifact_pos:
                            try:
                                self._handle_special_dungeon_artifact()
                            except Exception as e:
                                self.ui.messages.add(f"Error with special artifact: {e}")
                    except Exception as ex:
                        try:
                            if tstr == 'D':
                                with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                                    fh.write(f">>> EXCEPTION in special dungeon artifact check: {ex}\n")
                                    fh.write(f"    current_special_dungeon={getattr(self, 'current_special_dungeon', None)}\n")
                        except: pass
                
                # DEBUG
                try:
                    if tstr == 'D':
                        with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                            fh.write(f">>> Passed special dungeon artifact check\n")
                except: pass
                
                # Check for Special Dungeon exit
                if hasattr(self, 'current_special_dungeon'):
                    try:
                        dungeon = self.current_special_dungeon
                        exit_pos = dungeon.get('exit_pos') if dungeon and hasattr(dungeon, 'get') else None
                        if exit_pos and (nx, ny) == exit_pos and (dungeon.get('artifact_claimed', False) if hasattr(dungeon, 'get') else False):
                            try:
                                self._exit_special_dungeon()
                            except Exception as e:
                                self.ui.messages.add(f"Error exiting special dungeon: {e}")
                    except Exception as ex:
                        try:
                            if tstr == 'D':
                                with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                                    fh.write(f">>> EXCEPTION in special dungeon exit check: {ex}\n")
                        except: pass
                
                # DEBUG: Check if we reach this point
                try:
                    if tstr == 'D':
                        with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                            fh.write(f">>> Reached tomb entrance check section for 'D' at ({nx}, {ny})\n")
                except: pass
                
                # consider digits 1/2/3 (int or str), or SITH_ENTRANCE constant or recorded tomb_entrances
                entrance_hit = False
                if tstr in ("D",):
                    # Debug tomb entrance detection FIRST
                    try:
                        with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                            fh.write(f"\n=== TOMB ENTRANCE DEBUG ===\n")
                            fh.write(f"Player stepped on 'D' at position {(nx, ny)}\n")
                            fh.write(f"Target tile: {repr(target)} (type: {type(target)})\n")
                            fh.write(f"Target str: '{tstr}'\n")
                            tomb_set = getattr(self, 'tomb_entrances', set())
                            fh.write(f"tomb_entrances set exists: {tomb_set is not None}\n")
                            fh.write(f"tomb_entrances count: {len(tomb_set) if tomb_set else 0}\n")
                            if tomb_set:
                                fh.write(f"tomb_entrances contents (all): {tomb_set}\n")
                            fh.write(f"Position {(nx, ny)} in tomb_entrances: {(nx, ny) in tomb_set}\n")
                            
                            # Check if this is the RIGHT entrance_hit condition
                            if (nx, ny) in tomb_set:
                                fh.write(f"✓ MATCH! This 'D' tile IS in tomb_entrances, setting entrance_hit=True\n")
                                entrance_hit = True
                            else:
                                fh.write(f"✗ MISMATCH! This 'D' tile is NOT in tomb_entrances set!\n")
                                fh.write(f"  This is likely a stale 'D' from a previous save or test.\n")
                                fh.write(f"  entrance_hit will remain False, tomb entry will fail.\n")
                            fh.write("=== END DEBUG ===\n\n")
                    except Exception as e:
                        try:
                            with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                                fh.write(f"Error writing debug: {e}\n")
                        except:
                            pass
                    
                    # ONLY set entrance_hit if position is in tomb_entrances
                    if (nx, ny) in getattr(self, 'tomb_entrances', set()):
                        entrance_hit = True
                        # IMMEDIATE visual feedback
                        try:
                            self.ui.messages.add("━" * 60)
                            self.ui.messages.add("🚪 YOU HAVE STEPPED ON A TOMB ENTRANCE! 🚪")
                            self.ui.messages.add("━" * 60)
                        except: pass
                    else:
                        # Notify player this is a fake/stale tomb entrance
                        try:
                            self.ui.messages.add("⚠️ This tomb entrance appears to be collapsed or inaccessible.")
                        except: pass
                try:
                    if target == getattr(Display, "SITH_ENTRANCE", None):
                        entrance_hit = True
                        try:
                            with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                                fh.write(f"entrance_hit via Display.SITH_ENTRANCE check\n")
                        except: pass
                except Exception:
                    pass
                try:
                    tomb_set = getattr(self, "tomb_entrances", set())
                    if (nx, ny) in tomb_set:
                        entrance_hit = True
                        try:
                            with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                                fh.write(f"entrance_hit via tomb_entrances set check\n")
                        except: pass
                except Exception:
                    pass
                
                # Check for Special Dungeon entrance
                special_dungeon_hit = False
                try:
                    surface_special_dungeons = getattr(self, 'surface_special_dungeons', {})
                    if (nx, ny) in surface_special_dungeons:
                        special_dungeon_hit = True
                except Exception:
                    pass
                
                # Check for encounter markers ('?')
                try:
                    if hasattr(self, 'pending_encounters') and (nx, ny) in self.pending_encounters:
                        encounter = self.pending_encounters[(nx, ny)]
                        corruption = getattr(self.player, 'corruption', 50)
                        
                        # Build encounter popup content
                        from jedi_fugitive.game import biome_encounters
                        discovery = biome_encounters.get_discovery_text(encounter, corruption)
                        
                        popup_content = []
                        popup_content.append("═" * 60)
                        popup_content.append(f"╔═ ENCOUNTER: {encounter['name'].upper()} ═╗".center(60))
                        popup_content.append("═" * 60)
                        popup_content.append("")
                        
                        if discovery:
                            popup_content.append(discovery)
                            popup_content.append("")
                        
                        for desc_line in encounter.get('description', []):
                            popup_content.append(desc_line)
                        popup_content.append("")
                        
                        # Add instructions for player
                        if 'discovery' in encounter and 'light' in encounter['discovery']:
                            popup_content.append("[This encounter offers different outcomes based on your choices]")
                            popup_content.append("[Your corruption level will influence available options]")
                        elif 'reward' in encounter:
                            reward_name = encounter['reward']
                            popup_content.append(f"[You discover: {reward_name}]")
                            # Simple reward implementation
                            try:
                                if 'treasure' in reward_name.lower() or 'cache' in reward_name.lower():
                                    gold = __import__('random').randint(20, 50)
                                    self.player.gold_collected = getattr(self.player, 'gold_collected', 0) + gold
                                    # Invalidate stats cache so gold counter updates in GUI
                                    self.player._stats_cache_dirty = True
                                    popup_content.append(f"[+{gold} gold]")
                                elif 'fuel' in reward_name.lower():
                                    popup_content.append("[Useful salvage for later]")
                            except Exception:
                                pass
                        
                        popup_content.append("")
                        popup_content.append("Press any key to continue...")
                        
                        # Display as popup menu
                        self.ui.centered_menu(popup_content, f"Biome Encounter")
                        
                        # Brief confirmation in message log
                        self.ui.messages.add(f"#3#[ENCOUNTER]#0# {encounter['name']}")
                        
                        # Remove encounter marker from map
                        self.game_map[ny][nx] = getattr(Display, 'FLOOR', '.')
                        del self.pending_encounters[(nx, ny)]
                        
                        # Add journal entry
                        try:
                            if hasattr(self.player, 'add_log_entry'):
                                entry = self.player.narrative_text(
                                    light_version=f"Encountered: {encounter['name']}. Sought to understand its meaning.",
                                    dark_version=f"Found: {encounter['name']}. Took what power I could from it.",
                                    balanced_version=f"Discovered: {encounter['name']}."
                                )
                                self.player.add_log_entry(entry, self.turn_count)
                        except Exception:
                            pass
                except Exception:
                    pass

                # If the player stepped on stairs glyphs, automatically change floor
                try:
                    stairs_down = getattr(Display, 'STAIRS_DOWN', '>')
                    stairs_up = getattr(Display, 'STAIRS_UP', '<')
                    if tstr == str(stairs_down):
                        try:
                            # Check if we're in a special dungeon
                            if hasattr(self, 'current_special_dungeon'):
                                dungeon = self.current_special_dungeon
                                current_floor = dungeon.get('current_floor', 1)
                                num_levels = dungeon.get('num_levels', 1)
                                
                                if current_floor < num_levels:
                                    # Descend to next level of special dungeon
                                    dungeon_data = {
                                        'type': dungeon['type'],
                                        'template': dungeon['template']
                                    }
                                    self._enter_special_dungeon(dungeon_data, self.player.x, self.player.y)
                                    return True
                                else:
                                    self.ui.messages.add("These stairs lead nowhere deeper...")
                                    return False
                            else:
                                # Regular tomb/dungeon stairs
                                changed = self.change_floor(1)
                                if changed:
                                    try: self.compute_visibility()
                                    except Exception: pass
                                    try:
                                        if getattr(self.ui, 'messages', None):
                                            self.ui.messages.add("You descend the stairs...")
                                        # Add alignment-based travel log entry
                                        if hasattr(self.player, 'add_log_entry'):
                                            entry = self.player.narrative_text(
                                                light_version=f"Descended deeper, seeking to understand this dark place.",
                                                dark_version=f"Plunged deeper into darkness, hungry for more power.",
                                                balanced_version=f"Descended to level {self.current_floor + 1}."
                                            )
                                            self.player.add_log_entry(entry, getattr(self, 'turn_count', 0))
                                        
                                        # Track tomb depth for milestone system
                                        current_depth = abs(getattr(self, 'current_floor', 0))
                                        max_depth = getattr(self.player, 'max_tomb_depth', 0)
                                        if current_depth > max_depth:
                                            self.player.max_tomb_depth = current_depth
                                    except Exception:
                                        pass
                                    return True
                        except Exception:
                            pass
                    if tstr == str(stairs_up):
                        try:
                            changed = self.change_floor(-1)
                            if changed:
                                try: self.compute_visibility()
                                except Exception: pass
                                try:
                                    if getattr(self.ui, 'messages', None):
                                        self.ui.messages.add("You climb the stairs...")
                                    # Add alignment-based travel log entry
                                    if hasattr(self.player, 'add_log_entry'):
                                        entry = self.player.narrative_text(
                                            light_version=f"Ascended, drawing closer to the light above.",
                                            dark_version=f"Retreated upward, my conquest not yet complete.",
                                            balanced_version=f"Climbed to level {self.current_floor + 1}."
                                        )
                                        self.player.add_log_entry(entry, getattr(self, 'turn_count', 0))
                                except Exception:
                                    pass
                                return True
                        except Exception:
                            pass
                except Exception:
                    # defensive: ignore any stairs-handling errors and continue to tomb logic
                    pass

                if entrance_hit:
                    try:
                        from jedi_fugitive.game import map_features
                        entered = False
                        try:
                            # Add message BEFORE entering
                            if getattr(self.ui, "messages", None):
                                self.ui.messages.add("═" * 60)
                                self.ui.messages.add("⚠ You stand before a dark Sith tomb entrance...")
                                self.ui.messages.add("The darkness beckons you inside...")
                                self.ui.messages.add("═" * 60)
                            entered = map_features.enter_tomb(self)
                        except Exception as e:
                            entered = False
                            try:
                                with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                                    fh.write(f"Exception in enter_tomb: {e}\n")
                                    import traceback
                                    traceback.print_exc(file=fh)
                            except Exception:
                                pass
                        if entered:
                            try: self.compute_visibility()
                            except Exception: pass
                            try:
                                if getattr(self.ui, "messages", None):
                                    self.ui.messages.add("You descend into the Sith dungeon...")
                                # Add alignment-based travel log entry for tomb entrance
                                if hasattr(self.player, 'add_log_entry'):
                                    entry = self.player.narrative_text(
                                        light_version=f"Entered the Sith tomb with caution, feeling the weight of its evil.",
                                        dark_version=f"Stormed into the Sith tomb, eager to claim its forbidden secrets!",
                                        balanced_version=f"Entered a Sith tomb, the darkness palpable."
                                    )
                                    self.player.add_log_entry(entry, getattr(self, 'turn_count', 0))
                            except Exception:
                                pass
                            return True
                        else:
                            # extra debug: write map slice and entrance info
                            try:
                                with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                                    fh.write(f"enter_tomb returned False at pos {(nx,ny)}, target={repr(target)}\n")
                                    fh.write(f"tomb_entrances={getattr(self,'tomb_entrances',None)}\n")
                                    # dump small map area around player
                                    mh = len(self.game_map); mw = len(self.game_map[0]) if mh else 0
                                    px,py = getattr(self.player,'x',None), getattr(self.player,'y',None)
                                    for ry in range(max(0, py-3), min(mh, py+4)):
                                        row = "".join(str(self.game_map[ry][cx])[:1] for cx in range(max(0, px-10), min(mw, px+11)))
                                        fh.write(f"{ry}: {row}\n")
                            except Exception:
                                pass
                            try:
                                if getattr(self.ui, "messages", None):
                                    self.ui.messages.add("Failed to enter tomb.")
                            except Exception:
                                pass
                    except Exception:
                        try:
                            if getattr(self.ui, "messages", None):
                                self.ui.messages.add("Failed to enter tomb.")
                        except Exception:
                            pass
            except Exception:
                pass

            # Handle Special Dungeon entrance
            if special_dungeon_hit:
                try:
                    surface_special_dungeons = getattr(self, 'surface_special_dungeons', {})
                    dungeon_data = surface_special_dungeons.get((nx, ny))
                    
                    if dungeon_data:
                        # Mark as discovered
                        dungeon_data['discovered'] = True
                        
                        # Enter the special dungeon
                        try:
                            entered = self._enter_surface_special_dungeon(dungeon_data, (nx, ny))
                            if entered:
                                self.compute_visibility()
                                return True
                            else:
                                if getattr(self.ui, "messages", None):
                                    self.ui.messages.add("The entrance seems sealed...")
                        except Exception as e:
                            if getattr(self.ui, "messages", None):
                                self.ui.messages.add(f"Failed to enter special dungeon: {e}")
                except Exception:
                    pass

            # check for stepping on Sith Device (win condition)
            try:
                sd = getattr(self, 'sith_device', None)
                # if we have tomb_levels, use tomb_floor index; else rely on current_depth
                cur_floor = getattr(self, 'tomb_floor', None)
                if sd is not None:
                    sd_level = sd.get('level', None) if isinstance(sd, dict) else None
                    if sd_level is None:
                        sd_level = getattr(self, 'current_depth', None) - 1
                    # compare floors and coords
                    px, py = getattr(self.player, 'x', None), getattr(self.player, 'y', None)
                    if px is not None and py is not None and sd_level == cur_floor and px == sd.get('x') and py == sd.get('y'):
                        try:
                            if getattr(self.ui, 'messages', None):
                                self.ui.messages.add('You have found the Sith Device! You win!')
                        except Exception:
                            pass
                        try:
                            # remove device from map and items
                            if 0 <= py < len(self.game_map) and 0 <= px < len(self.game_map[0]):
                                self.game_map[py][px] = getattr(Display, 'FLOOR', '.')
                        except Exception:
                            pass
                        # update items list and flag victory
                        try:
                            self.items_on_map = [it for it in getattr(self, 'items_on_map', []) if not (it.get('x') == px and it.get('y') == py)]
                        except Exception:
                            pass
                        try:
                            self.sith_device['picked'] = True
                        except Exception:
                            pass
                        # stop the game loop as victory; leave a message and set running False
                        try:
                            self.running = False
                        except Exception:
                            pass
                        return True
            except Exception:
                pass

            # check for stepping on comms terminal (quest progression)
            try:
                comms_ch = getattr(Display, 'COMMS', None)
                if (tstr == str(comms_ch)) or ((nx, ny) == getattr(self, 'comms_pos', None)):
                    if getattr(self, 'comms_established', False):
                        try:
                            if getattr(self.ui, 'messages', None):
                                self.ui.messages.add("Comms are already established.")
                        except Exception:
                            pass
                    else:
                        # Check for Jedi Artifacts in inventory
                        artifacts_recovered = 0
                        inv = getattr(self.player, 'inventory', [])
                        for item in inv:
                            if isinstance(item, dict):
                                if item.get('type') == 'quest_item' and 'artifact' in item.get('name', '').lower():
                                    artifacts_recovered += 1
                            elif hasattr(item, 'name') and 'artifact' in getattr(item, 'name', '').lower():
                                artifacts_recovered += 1
                        
                        # Need 3 artifacts to power the terminal
                        artifacts_needed = 3
                        
                        if artifacts_recovered >= artifacts_needed:
                            try:
                                self.comms_established = True
                                if getattr(self.ui, 'messages', None):
                                    self.ui.messages.add(f"You place {artifacts_recovered} Jedi Artifacts into the terminal's power matrix.")
                                    self.ui.messages.add("The ancient relics glow with purified Light energy!")
                                    self.ui.messages.add("Comms reactivated. Beacon signal transmitted - your ship is inbound.")
                            except Exception:
                                pass
                        else:
                            try:
                                if getattr(self.ui, 'messages', None):
                                    need = artifacts_needed - artifacts_recovered
                                    self.ui.messages.add(f"The comms terminal requires Jedi Artifacts as a power source.")
                                    self.ui.messages.add(f"You need {need} more artifact(s). Search the Sith tombs.")
                                    if artifacts_recovered > 0:
                                        self.ui.messages.add(f"Artifacts recovered: {artifacts_recovered}/{artifacts_needed}")
                            except Exception:
                                pass
                    return True
            except Exception:
                pass

            # check for stepping on ship (possible extraction / boss spawn)
            try:
                ship_ch = getattr(Display, 'SHIP', None)
                if (tstr == str(ship_ch)) or ((nx, ny) == getattr(self, 'ship_pos', None)):
                    # if comms established -> spawn alignment-based final boss
                    if getattr(self, 'comms_established', False) and not getattr(self, 'final_boss_spawned', False):
                        try:
                            from jedi_fugitive.game.enemy import Enemy, EnemyType
                            player = getattr(self, 'player', None)
                            corruption = getattr(player, 'dark_corruption', 0) if player else 0
                            lvl = max(5, getattr(player, 'level', 5) if player is not None else 5)
                            
                            # Determine boss type based on corruption
                            if corruption >= 60:
                                # Dark Side player -> Jedi Master arrives to stop you
                                from jedi_fugitive.game.enemies_sith import create_jedi_master
                                boss = create_jedi_master(level=lvl, x=nx, y=ny)
                                boss_name = "Jedi Master Alara"
                                taunt_msg = "A figure in tan robes appears. 'I sense great darkness in you. You will not escape!'"
                                combat_start = "The Jedi Master ignites a blue lightsaber and assumes a defensive stance."
                            else:
                                # Light Side player -> Sith Master hunts you
                                from jedi_fugitive.game.enemies_sith import create_sith_lord
                                boss = create_sith_lord(level=lvl, x=nx, y=ny)
                                boss_name = "Darth Malice"
                                taunt_msg = "A crimson blade pierces the darkness. 'The Light makes you weak, Jedi filth!'"
                                combat_start = "The Sith Lord attacks with vicious fury!"
                            boss.name = boss_name
                            
                            # Scale boss to player
                            try:
                                if player is not None:
                                    # HP: 1.5x player max HP
                                    boss.max_hp = int(getattr(player, 'max_hp', 100) * 1.5)
                                    boss.hp = boss.max_hp
                                    # Attack: 1.2x player attack
                                    try:
                                        base_attack = int(getattr(player, 'attack', 10))
                                    except Exception:
                                        base_attack = 10
                                    boss.attack = max(5, int(base_attack * 1.2))
                                    # Defense: Equal to player
                                    boss.defense = int(getattr(player, 'defense', 5))
                                    # Force: 2x player force
                                    try:
                                        pfp = int(getattr(player, 'force_points', 2) or 2)
                                        boss.force_points = max(10, pfp * 2)
                                    except Exception:
                                        boss.force_points = 10
                                    # Shorten ability cooldowns
                                    try:
                                        fas = getattr(boss, 'force_abilities', {}) or {}
                                        for a in fas.values():
                                            try:
                                                if hasattr(a, 'cooldown'):
                                                    setattr(a, 'cooldown', max(1, getattr(a, 'cooldown', 3) // 2))
                                                if hasattr(a, 'base_cooldown'):
                                                    setattr(a, 'base_cooldown', max(1, getattr(a, 'base_cooldown', 3) // 2))
                                            except Exception:
                                                pass
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            
                            try:
                                self.enemies.append(boss)
                                self.final_boss_spawned = True
                                self.final_boss = boss
                                
                                try:
                                    self.ui.messages.add(taunt_msg)
                                    self.ui.messages.add(combat_start)
                                    self.ui.messages.add("You must defeat them to escape!")
                                except Exception:
                                    pass
                                
                                # Clear nearby weak enemies for dramatic 1v1
                                try:
                                    radius = 12
                                    px, py = boss.x, boss.y
                                    self.enemies = [e for e in self.enemies if (e is boss) or (abs(getattr(e,'x',0)-px) + abs(getattr(e,'y',0)-py) > radius)]
                                except Exception:
                                    pass
                            except Exception:
                                pass
                            return True
                        except Exception as e:
                            try:
                                if getattr(self.ui, 'messages', None):
                                    self.ui.messages.add("Something stirs in the wreckage...")
                            except Exception:
                                pass
                            return True
                    elif getattr(self, 'comms_established', False) and getattr(self, 'final_boss_spawned', False):
                        # Check if final boss is defeated
                        boss_alive = False
                        try:
                            for enemy in getattr(self, 'enemies', []):
                                if getattr(enemy, 'is_boss', False):
                                    boss_alive = True
                                    break
                        except Exception:
                            pass
                        
                        if not boss_alive:
                            # Victory! Board the ship
                            self._trigger_victory()
                            return True
                        else:
                            try:
                                if getattr(self.ui, 'messages', None):
                                    self.ui.messages.add("You cannot board while the enemy still lives!")
                            except Exception:
                                pass
                            return True
                    else:
                        try:
                            if getattr(self.ui, 'messages', None):
                                if not getattr(self, 'comms_established', False):
                                    self.ui.messages.add("The wreck's systems are dead. Try to restore comms first.")
                                else:
                                    self.ui.messages.add("You return to your ship, but nothing happens.")
                        except Exception:
                            pass
                        return True
            except Exception:
                pass

            return True
        except Exception:
            return False

    def change_floor(self, delta: int) -> bool:
        """Change current dungeon floor by delta (+1 down, -1 up). Returns True on success."""
        try:
            # Safety check: don't allow floor changes if player is dead
            if getattr(self.player, 'hp', 1) <= 0:
                return False
            
            if not hasattr(self, 'tomb_levels') or not isinstance(self.tomb_levels, list) or len(self.tomb_levels) == 0:
                try:
                    if getattr(self.ui, 'messages', None):
                        self.ui.messages.add("There are no stairs here.")
                except Exception:
                    pass
                return False
            cur = getattr(self, 'tomb_floor', 0)
            
            # CRITICAL: Save current floor state before changing floors
            try:
                if hasattr(self, 'tomb_enemies') and isinstance(self.tomb_enemies, list):
                    if cur < len(self.tomb_enemies):
                        self.tomb_enemies[cur] = list(getattr(self, 'enemies', []))
                if hasattr(self, 'tomb_items') and isinstance(self.tomb_items, list):
                    if cur < len(self.tomb_items):
                        self.tomb_items[cur] = list(getattr(self, 'items_on_map', []))
            except Exception as e:
                print(f"Warning: Failed to save floor {cur} state: {e}")
            
            new = cur + int(delta)
            # special case: leaving the dungeon (going above floor 0) should
            # restore the surface map if we saved one when entering the tomb.
            if new < 0:
                try:
                    if hasattr(self, 'surface_map') and self.surface_map is not None:
                        # restore surface state
                        self.game_map = self.surface_map
                        self.enemies = list(getattr(self, 'surface_enemies', []) or [])
                        self.items_on_map = list(getattr(self, 'surface_items_on_map', []) or [])
                        # CRITICAL: Restore tomb entrances set for re-entry
                        if hasattr(self, 'surface_tomb_entrances'):
                            self.tomb_entrances = set(self.surface_tomb_entrances)
                        try:
                            px, py = getattr(self, 'surface_player_pos', (None, None))
                            if px is not None and py is not None:
                                self.player.x, self.player.y = px, py
                        except Exception:
                            pass
                            # restore LOS radius if saved
                        try:
                            if hasattr(self, 'surface_los_radius'):
                                try:
                                    self.player.los_radius = int(getattr(self, 'surface_los_radius', getattr(self.player, 'los_radius', 6)))
                                except Exception:
                                    self.player.los_radius = getattr(self, 'surface_los_radius', getattr(self.player, 'los_radius', 6))
                        except Exception:
                            pass
                        # IMPROVED: Save tomb state for persistence on re-entry
                        try:
                            # Store tomb data by entrance position for re-entry
                            if not hasattr(self, 'completed_tombs'):
                                self.completed_tombs = {}
                            
                            entrance_pos = getattr(self, 'surface_player_pos', (0, 0))
                            tomb_state = {
                                'levels': list(getattr(self, 'tomb_levels', [])),
                                'rooms': list(getattr(self, 'tomb_rooms', [])),
                                'enemies': list(getattr(self, 'tomb_enemies', [])),
                                'items': list(getattr(self, 'tomb_items', [])),
                                'stairs': list(getattr(self, 'tomb_stairs', [])),
                                'special_dungeons': list(getattr(self, 'tomb_special_dungeons', []))
                            }
                            self.completed_tombs[entrance_pos] = tomb_state
                        except Exception as e:
                            print(f"Warning: Failed to save tomb state: {e}")
                        
                        # clear tomb-related fields from active game state
                        for attr in ['tomb_levels', 'tomb_rooms', 'tomb_enemies', 'tomb_items', 'tomb_stairs', 'tomb_floor', 'tomb_special_dungeons']:
                            try:
                                if hasattr(self, attr):
                                    delattr(self, attr)
                            except Exception:
                                pass
                        
                        self.current_depth = 1
                        try:
                            if getattr(self.ui, 'messages', None):
                                self.ui.messages.add("#2#You emerge from the tomb and return to the surface.#0#")
                                self.ui.messages.add("(The tomb remains accessible for re-entry)")
                        except Exception:
                            pass
                        try:
                            self.compute_visibility()
                        except Exception:
                            pass
                        return True
                except Exception:
                    pass
            if new < 0 or new >= len(self.tomb_levels):
                try:
                    if getattr(self.ui, 'messages', None):
                        self.ui.messages.add("You can't go that way.")
                except Exception:
                    pass
                return False
            # find target stair position on destination floor
            try:
                # store previous floor/stairs
                prev_stairs = getattr(self, 'tomb_stairs', [])[cur] if getattr(self, 'tomb_stairs', None) else {}
                next_stairs = getattr(self, 'tomb_stairs', [])[new] if getattr(self, 'tomb_stairs', None) else {}
                # set new map
                self.game_map = self.tomb_levels[new]
                self.tomb_floor = new
                self.current_depth = new + 1
                # place player at corresponding stair entrance on new floor
                placed = False
                if delta > 0:
                    # going down: place at stair_up on new floor if present, else center
                    up = next_stairs.get('up') if isinstance(next_stairs, dict) else None
                    if up:
                        self.player.x, self.player.y = up[0], up[1]; placed = True
                else:
                    # going up: place at stair_down on new floor if present
                    down = next_stairs.get('down') if isinstance(next_stairs, dict) else None
                    if down:
                        self.player.x, self.player.y = down[0], down[1]; placed = True
                if not placed:
                    # fallback to center of first room or center of map
                    try:
                        rooms = getattr(self, 'tomb_rooms', [])[new]
                        if rooms:
                            r = rooms[0]
                            self.player.x = r[0] + r[2]//2; self.player.y = r[1] + r[3]//2
                        else:
                            self.player.x = max(1, len(self.game_map[0])//2); self.player.y = max(1, len(self.game_map)//2)
                    except Exception:
                        self.player.x = max(1, len(self.game_map[0])//2); self.player.y = max(1, len(self.game_map)//2)
                # clear enemies/items on load or optionally spawn new ones
                # load per-floor persistent enemies/items if present
                try:
                    tomb_enemies_list = getattr(self, 'tomb_enemies', [])
                    if tomb_enemies_list and new < len(tomb_enemies_list):
                        floor_enemies = tomb_enemies_list[new]
                        if floor_enemies is not None and isinstance(floor_enemies, list):
                            self.enemies = [e for e in floor_enemies if e is not None]
                        else:
                            self.enemies = []
                    else:
                        self.enemies = []
                except Exception as e:
                    print(f"ERROR loading tomb enemies for floor {new}: {e}")
                    import traceback
                    traceback.print_exc()
                    self.enemies = []
                try:
                    tomb_items_list = getattr(self, 'tomb_items', [])
                    if tomb_items_list and new < len(tomb_items_list):
                        floor_items = tomb_items_list[new]
                        if floor_items is not None and isinstance(floor_items, list):
                            self.items_on_map = [i for i in floor_items if i is not None]
                        else:
                            self.items_on_map = []
                    else:
                        self.items_on_map = []
                except Exception as e:
                    print(f"ERROR loading tomb items for floor {new}: {e}")
                    import traceback
                    traceback.print_exc()
                    self.items_on_map = []
                try:
                    if getattr(self.ui, 'messages', None):
                        if delta > 0:
                            self.ui.messages.add(f"You descend deeper into the tomb... (Level {self.tomb_floor+1})")
                        else:
                            self.ui.messages.add(f"You climb back up the stairs... (Level {self.tomb_floor+1})")
                except Exception:
                    pass
                try:
                    self.compute_visibility()
                except Exception:
                    pass
                return True
            except Exception:
                return False
        except Exception:
            # top-level error handling for floor changes
            try:
                if getattr(self.ui, 'messages', None):
                    self.ui.messages.add("Error changing floors.")
            except Exception:
                pass
            return False

    def go_down(self):
        return self.change_floor(1)

    def go_up(self):
        return self.change_floor(-1)

    def process_enemies(self):
        # Prefer dedicated enemy processing if available, else simple movement + projectiles step
        try:
            from jedi_fugitive.game.enemy import process_enemies as enemy_process_enemies
            try:
                enemy_process_enemies(self)
                return
            except Exception:
                pass
        except Exception:
            pass

        # fallback: advance projectiles and move enemies towards player one step
        try:
            from jedi_fugitive.game import projectiles as proj
            try:
                proj.advance_projectiles(self)
            except Exception:
                pass
        except Exception:
            pass

        try:
            floor_ch = getattr(Display, "FLOOR", ".")
            mh = len(self.game_map); mw = len(self.game_map[0]) if mh else 0
            px = int(getattr(self.player, "x", 0)); py = int(getattr(self.player, "y", 0))
            new_positions = {}
            enemies = list(getattr(self, "enemies", []) or [])
            n = len(enemies)
            if n == 0:
                return
            # throttle enemy processing: only update a fraction each turn (round-robin)
            frac = float(getattr(self, 'enemy_update_fraction', 0.33) or 0.33)
            per_tick = max(1, int(n * frac))
            start_idx = int(getattr(self, '_enemy_update_index', 0) or 0)
            for i in range(per_tick):
                idx = (start_idx + i) % n
                e = enemies[idx]
                try:
                    if not getattr(e, "is_alive", lambda: True)():
                        continue
                    ex = int(getattr(e, "x", -1)); ey = int(getattr(e, "y", -1))
                    # allow enemy-specific AI hook
                    moved = False
                    if hasattr(e, "take_turn") and callable(e.take_turn):
                        try:
                            e.take_turn(self)
                            moved = True
                        except Exception:
                            moved = False
                    # fallback simple movement: if the enemy hasn't run custom AI, step one tile toward the player
                    if not moved:
                        try:
                            def _sign(n):
                                return 1 if n > 0 else (-1 if n < 0 else 0)

                            dx = _sign(px - ex)
                            dy = _sign(py - ey)

                            # prefer the dominant axis for movement (simple greedy chase)
                            if abs(px - ex) > abs(py - ey):
                                nx = ex + _sign(px - ex)
                                ny = ey
                            elif abs(py - ey) > abs(px - ex):
                                nx = ex
                                ny = ey + _sign(py - ey)
                            else:
                                nx = ex + dx
                                ny = ey + dy

                            # validate destination and move if it's a floor tile and not occupied
                            try:
                                if 0 <= ny < mh and 0 <= nx < mw and self.game_map[ny][nx] == floor_ch and (nx, ny) != (px, py):
                                    occupied = any(getattr(oe, 'x', None) == nx and getattr(oe, 'y', None) == ny for oe in self.enemies if oe is not e)
                                    if not occupied:
                                        e.x = nx; e.y = ny
                                        moved = True
                            except Exception:
                                # if map lookup fails, skip movement for this enemy
                                pass
                        except Exception:
                            pass
                    # store new pos if moved
                    if moved:
                        new_positions[e] = (getattr(e,"x",ex), getattr(e,"y",ey))
                except Exception:
                    continue
            # advance start index for next tick
            try:
                self._enemy_update_index = (start_idx + per_tick) % n
            except Exception:
                self._enemy_update_index = 0
            # small chance to taunt / show message
            try:
                if random.random() < 0.02 and getattr(self.ui, "messages", None):
                    if self.enemies:
                        ee = random.choice(self.enemies)
                        try:
                            name = getattr(ee, "name", "An enemy")
                            self.ui.messages.add(f"{name} moves...")
                        except Exception:
                            pass
            except Exception:
                pass
        except Exception:
            # last resort: ignore enemy movement errors
            pass

    def _tick_effects(self):
        """Per-turn effects processed centrally: stress accrual, being hunted ticks, environmental checks."""
        try:
            # Progressive enemy spawning system
            try:
                from jedi_fugitive.game.progressive_spawning import process_progressive_spawning
                process_progressive_spawning(self)
            except Exception:
                pass  # Don't break game if spawning fails
            
            # Random events system
            try:
                from jedi_fugitive.game.random_events import should_trigger_random_event, trigger_random_event
                turn_count = getattr(self, 'turn_count', 0)
                if should_trigger_random_event(turn_count):
                    trigger_random_event(self)
            except Exception:
                pass  # Don't break game if events fail
            
            # Process temporary reward effects
            try:
                from jedi_fugitive.game.reward_system import tick_temporary_effects
                tick_temporary_effects(self)
            except Exception:
                pass  # Don't break game if effect processing fails
            
            # Check if stress system is active (only after first tomb entry)
            stress_active = getattr(self.player, '_stress_system_active', False)
            
            # being hunted: when flagged, apply per-turn stress and tick down
            if getattr(self, 'being_hunted_ticks', 0) > 0:
                try:
                    # Reduced from 5 to 3, and only every other turn
                    turn_count = getattr(self, 'turn_count', 0)
                    if turn_count % 2 == 0 and stress_active:
                        self.player.add_stress(3, source='being_hunted')
                except Exception:
                    pass
                try:
                    self.being_hunted_ticks -= 1
                    if self.being_hunted_ticks <= 0:
                        try:
                            if getattr(self.ui, 'messages', None):
                                self.ui.messages.add("You are no longer being hunted.")
                        except Exception:
                            pass
                except Exception:
                    pass

            # decrement scan/compass cooldown on player (if any)
            try:
                cd = int(getattr(self.player, 'scan_cooldown', 0) or 0)
                if cd > 0:
                    try:
                        self.player.scan_cooldown = max(0, cd - 1)
                        if getattr(self.player, 'scan_cooldown', 0) == 0:
                            try:
                                # notify player once when recharge completes
                                self.add_message("Scan recharged.")
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass

            # combat stress: only applies when actively in danger (enemies very close)
            # Reduced frequency - only every 3rd turn and lower base amount
            # Only active after first tomb entry
            try:
                if stress_active:
                    in_combat = False
                    nearby_enemies = 0
                    px, py = getattr(self.player, 'x', 0), getattr(self.player, 'y', 0)
                    for e in list(getattr(self, 'enemies', []) or []):
                        try:
                            dist = abs(getattr(e,'x',0)-px) + abs(getattr(e,'y',0)-py)
                            # Only count enemies within 3 tiles as causing stress
                            if dist <= 3:
                                nearby_enemies += 1
                                if dist <= 1:  # Adjacent enemy = definitely in combat
                                    in_combat = True
                        except Exception:
                            continue
                    
                    # Only apply stress if there are nearby enemies AND it's been a few turns
                    turn_count = getattr(self, 'turn_count', 0)
                    if in_combat and turn_count % 5 == 0:  # Every 5th turn (reduced from 3)
                        try:
                            # Reduced stress - player adapts to combat
                            stress_amount = max(1, nearby_enemies // 3)  # Less stress per enemy
                            old_stress = getattr(self.player, 'stress', 0)
                            self.player.add_stress(stress_amount, source='combat_turn')
                            
                            # Narrative feedback for combat stress
                            if getattr(self.ui, 'messages', None) and turn_count % 9 == 0:  # Show message every 9 turns
                                combat_messages = [
                                    "Your heart pounds as the battle drags on.",
                                    "The constant threat wears at your composure.",
                                    "Every moment in combat tests your resolve.",
                                    "The weight of battle bears down on you."
                                ]
                                import random
                                self.ui.messages.add(random.choice(combat_messages))
                        except Exception:
                            pass
            except Exception:
                pass

            # low HP stress - reduced frequency and conditional
            # Only active after first tomb entry
            try:
                if stress_active:
                    hp_pct = getattr(self.player, 'hp', 0) / max(1, getattr(self.player, 'max_hp', 1))
                    turn_count = getattr(self, 'turn_count', 0)
                    
                    # Only apply low HP stress every 6th turn (reduced from 4)
                    if hp_pct <= 0.25 and turn_count % 6 == 0:
                        # Reduced from 3 to 2 for better playability
                        self.player.add_stress(2, source='low_hp')
                        if getattr(self.ui, 'messages', None) and turn_count % 12 == 0:
                            low_hp_messages = [
                                "Your wounds make every breath a struggle.",
                                "Pain clouds your thoughts.",
                                "You're barely holding on."
                            ]
                            import random
                            self.ui.messages.add(random.choice(low_hp_messages))
                    # Very low HP (<10%) gets extra stress but still not every turn
                    elif hp_pct <= 0.10 and turn_count % 5 == 0:  # Reduced frequency
                        self.player.add_stress(3, source='critical_hp')  # Reduced from 4
                        if getattr(self.ui, 'messages', None) and turn_count % 9 == 0:
                            critical_messages = [
                                "Death's cold hand reaches for you.",
                                "Your vision blurs - you're fading fast.",
                                "Darkness encroaches at the edges of your sight."
                            ]
                            import random
                            self.ui.messages.add(random.choice(critical_messages))
            except Exception:
                pass

            # surrounded stress (3+ adjacent enemies): trigger once while condition holds
            # Only active after first tomb entry
            try:
                if stress_active:
                    px, py = getattr(self.player, 'x', 0), getattr(self.player, 'y', 0)
                    adjacent = 0
                    for e in list(getattr(self, 'enemies', []) or []):
                        try:
                            if abs(getattr(e,'x',0)-px) + abs(getattr(e,'y',0)-py) <= 1:
                                adjacent += 1
                        except Exception:
                            continue
                    if adjacent >= 3 and not getattr(self.player, '_surrounded_flag', False):
                        try:
                            self.player._surrounded_flag = True
                            # Reduced from 15 to 10 for better playability
                            self.player.add_stress(10, source='surrounded')
                            if getattr(self.ui, 'messages', None):
                                self.ui.messages.add("You are surrounded! Panic rises in you.")
                        except Exception:
                            pass
                    elif adjacent < 3:
                        try:
                            self.player._surrounded_flag = False
                        except Exception:
                            pass
            except Exception:
                pass

            # passive stress recovery when safe (no enemies nearby)
            # Only active after first tomb entry
            try:
                if stress_active:
                    px, py = getattr(self.player, 'x', 0), getattr(self.player, 'y', 0)
                    nearest_enemy_dist = 999
                    for e in list(getattr(self, 'enemies', []) or []):
                        try:
                            dist = abs(getattr(e,'x',0)-px) + abs(getattr(e,'y',0)-py)
                            nearest_enemy_dist = min(nearest_enemy_dist, dist)
                        except Exception:
                            continue
                    
                    # If no enemies within 8 tiles and stress > 0, slowly reduce stress
                    # But never drop below 30 - the fear from the initial chase never fully leaves
                    if nearest_enemy_dist > 8 and getattr(self.player, 'stress', 0) > 30:
                        turn_count = getattr(self, 'turn_count', 0)
                        # Reduce 1 stress every 5 turns when safe
                        if turn_count % 5 == 0:
                            try:
                                old_stress = getattr(self.player, 'stress', 0)
                                self.player.reduce_stress(1)
                                new_stress = getattr(self.player, 'stress', 0)
                                
                                # Enhanced recovery messages based on stress levels
                                if turn_count % 20 == 0 and getattr(self.ui, 'messages', None):
                                    if new_stress <= 35:
                                        recovery_messages = [
                                            "You catch your breath, but the fear lingers.",
                                            "A moment of peace, yet the memory of the chase haunts you.",
                                            "You try to calm yourself, but you can't fully shake the dread."
                                        ]
                                    elif new_stress <= 60:
                                        recovery_messages = [
                                            "The tension slowly eases from your shoulders.",
                                            "Your heartbeat steadies in the stillness.",
                                            "You feel your anxiety receding."
                                        ]
                                    else:
                                        recovery_messages = [
                                            "A moment of safety lets you catch your breath.",
                                            "The distance from danger helps you think clearer.",
                                            "You grasp at fleeting moments of calm."
                                        ]
                                    import random
                                    self.ui.messages.add(random.choice(recovery_messages))
                            except Exception:
                                pass
            except Exception:
                pass

            # dark area detection heuristic: small los_radius -> considered dark
            # Only active after first tomb entry
            try:
                if stress_active:
                    if getattr(self.player, 'los_radius', 6) <= 3 and not getattr(self.player, '_dark_flag', False):
                        try:
                            self.player._dark_flag = True
                            self.player.add_stress(10, source='dark_area')
                            if getattr(self.ui, 'messages', None):
                                self.ui.messages.add("Darkness weighs on you. (+10 stress)")
                        except Exception:
                            pass
                    elif getattr(self.player, 'los_radius', 6) > 3:
                        try:
                            self.player._dark_flag = False
                        except Exception:
                            pass
            except Exception:
                pass

            # handle temporary LOS bonus ticks (from Force: Reveal)
            try:
                if getattr(self.player, 'los_bonus_turns', 0) > 0:
                    try:
                        self.player.los_bonus_turns = max(0, int(getattr(self.player, 'los_bonus_turns', 0)) - 1)
                        if getattr(self.player, 'los_bonus_turns', 0) <= 0:
                            try:
                                # clear the bonus radius when expired
                                setattr(self.player, 'los_bonus_radius', 0)
                                if getattr(self.ui, 'messages', None):
                                    self.ui.messages.add("Your Reveal effect fades.")
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass

            # Stress threshold warnings
            # Only active after first tomb entry
            try:
                if stress_active:
                    stress = getattr(self.player, 'stress', 0)
                    if getattr(self.player, '_stress_warning_75', False):
                        if getattr(self.ui, 'messages', None):
                            self.ui.messages.add("Your hands tremble. Panic begins to take hold. (Stress: 75+)")
                        self.player._stress_warning_75 = False
                    if getattr(self.player, '_stress_warning_85', False):
                        if getattr(self.ui, 'messages', None):
                            self.ui.messages.add("Your mind races uncontrollably. You're approaching your limit! (Stress: 85+)")
                        self.player._stress_warning_85 = False
                    if getattr(self.player, '_stress_warning_95', False):
                        if getattr(self.ui, 'messages', None):
                            self.ui.messages.add("WARNING: You are on the verge of a mental breakdown! (Stress: 95+)")
                        self.player._stress_warning_95 = False
            except Exception:
                pass
            
            # breaking-point check
            # Only active after first tomb entry
            try:
                if stress_active and getattr(self.player, 'stress', 0) >= getattr(self.player, 'max_stress', 100) and not getattr(self, '_handled_breaking_point', False):
                    # mark handled so we don't repeatedly trigger in same turn
                    try: setattr(self, '_handled_breaking_point', True)
                    except Exception: pass
                    try: setattr(self, '_breaking_point_triggered', True)
                    except Exception: pass
                    # alignment-based outcomes
                    try:
                        score = getattr(self.player, 'alignment_score', 50)
                        if score >= 60:
                            # Light side: resolve - find inner peace
                            self.player.stress = 50
                            try:
                                if getattr(self.ui, 'messages', None):
                                    self.ui.messages.add("=== BREAKING POINT ===")
                                    self.ui.messages.add("You reach into the Force for strength...")
                                    self.ui.messages.add("RESOLUTE RECOVERY: Inner peace washes over you. The light guides you back from the brink.")
                                # Add to journal
                                try:
                                    biome = getattr(self, 'current_biome', 'unknown')
                                    self.player.add_log_entry(f"[BREAKING POINT] The pressure became unbearable in the {biome}, but my connection to the Light Side saved me. I found clarity in the chaos and recovered my composure.", self.turn_count)
                                except Exception:
                                    pass
                            except Exception:
                                pass
                            # grant temporary buff placeholder
                            try:
                                self.player._in_the_moment = getattr(self.player, '_in_the_moment', 0) + 5
                            except Exception:
                                pass
                        elif score <= 40:
                            # Dark side: explosion - unleash rage
                            try:
                                # damage nearby enemies
                                px, py = getattr(self.player, 'x', 0), getattr(self.player, 'y', 0)
                                affected = 0
                                for e in list(getattr(self, 'enemies', []) or []):
                                    try:
                                        if abs(getattr(e,'x',0)-px) + abs(getattr(e,'y',0)-py) <= 2:
                                            if hasattr(e, 'take_damage'):
                                                e.take_damage(20)
                                            else:
                                                e.hp = getattr(e,'hp',0) - 20
                                            affected += 1
                                    except Exception:
                                        continue
                                if getattr(self.ui, 'messages', None):
                                    self.ui.messages.add("=== BREAKING POINT ===")
                                    self.ui.messages.add("Rage consumes you completely!")
                                    self.ui.messages.add(f"DARK RAGE UNLEASHED: You lash out with fury, damaging {affected} nearby enemies!")
                                    self.ui.messages.add("Your anger gives you power, but at what cost?")
                                # Add to journal
                                try:
                                    biome = getattr(self, 'current_biome', 'unknown')
                                    self.player.add_log_entry(f"[BREAKING POINT] I lost control in the {biome}. Pure rage erupted from me, striking down everything nearby. The dark side flows through me freely now... it felt good.", self.turn_count)
                                except Exception:
                                    pass
                                # apply reckless debuff placeholder
                                self.player._reckless_turns = getattr(self.player, '_reckless_turns', 0) + 3
                            except Exception:
                                pass
                        else:
                            # neutral: catatonic shock - mental overload
                            try:
                                self.player._catatonic_skips = getattr(self.player, '_catatonic_skips', 0) + 2
                                self.player.stress = 75
                                if getattr(self.ui, 'messages', None):
                                    self.ui.messages.add("=== BREAKING POINT ===")
                                    self.ui.messages.add("Your mind cannot process any more...")
                                    self.ui.messages.add("CATATONIC SHOCK: You collapse, stunned and helpless for 2 turns!")
                                    self.ui.messages.add("The world fades to gray as you shut down completely.")
                                # Add to journal
                                try:
                                    biome = getattr(self, 'current_biome', 'unknown')
                                    self.player.add_log_entry(f"[BREAKING POINT] My mind shut down in the {biome}. I couldn't fight, couldn't move, couldn't think. I just... stopped. For how long, I'm not sure.", self.turn_count)
                                except Exception:
                                    pass
                            except Exception:
                                pass
                        
                        # CRITICAL: Check if player is at 0 HP during breaking point - this should cause death
                        if getattr(self.player, "hp", 1) <= 0:
                            # Player was already at 0 HP when breaking point triggered - this is death by stress
                            try:
                                if getattr(self.ui, 'messages', None):
                                    self.ui.messages.add("The combined physical and mental trauma proves too much...")
                                    self.ui.messages.add("You succumb to your wounds and overwhelming stress.")
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass

            # clear handled flag at end of turn if stress below threshold
            try:
                if getattr(self.player, 'stress', 0) < getattr(self.player, 'max_stress', 100):
                    try: setattr(self, '_handled_breaking_point', False)
                    except Exception: pass
            except Exception:
                pass
            
            # Enemy respawn system - gradually repopulate the map
            try:
                turn_count = getattr(self, 'turn_count', 0)
                last_respawn = getattr(self, 'last_respawn_turn', 0)
                respawn_interval = getattr(self, 'respawn_interval', 150)
                
                # Reduce respawn interval as player levels up (more frequent spawns)
                player_level = getattr(self.player, 'level', 1)
                adjusted_interval = max(80, respawn_interval - (player_level - 1) * 10)  # Min 80 turns between respawns
                
                if turn_count - last_respawn >= adjusted_interval:
                    # Calculate how many enemies to spawn based on player level
                    base_enemies = 1
                    level_bonus = (player_level - 1) // 2  # +1 enemy per 2 levels
                    enemies_to_spawn = base_enemies + level_bonus
                    enemies_to_spawn = min(enemies_to_spawn, 5)  # Cap at 5 enemies per respawn
                    
                    # Count current enemies to avoid overpopulation
                    current_enemy_count = len([e for e in getattr(self, 'enemies', []) if getattr(e, 'is_alive', lambda: True)()])
                    max_enemies_on_map = 12 + player_level * 2  # Scales with level
                    
                    if current_enemy_count < max_enemies_on_map:
                        # Spawn enemies
                        spawned = self._respawn_enemies(enemies_to_spawn)
                        if spawned > 0:
                            self.last_respawn_turn = turn_count
                            # Optional notification (only if enemies very close)
                            try:
                                if getattr(self.ui, 'messages', None) and random.random() < 0.3:
                                    messages = [
                                        "You sense movement in the distance...",
                                        "The enemy presence grows stronger.",
                                        "More hostiles have arrived in the area.",
                                        "Reinforcements have entered the sector."
                                    ]
                                    self.ui.messages.add(random.choice(messages))
                            except Exception:
                                pass
            except Exception:
                pass
        except Exception:
            # ensure tick doesn't crash the loop
            try:
                if getattr(self.ui, 'messages', None):
                    self.ui.messages.add("Error processing effects.")
            except Exception:
                pass

    def _respawn_enemies(self, count: int) -> int:
        """Spawn enemies at distant locations on the map. Returns number of enemies spawned."""
        spawned = 0
        try:
            from jedi_fugitive.game.level import Display
            from jedi_fugitive.game import enemies_sith as sith
            
            mh = len(self.game_map)
            mw = len(self.game_map[0]) if mh else 0
            floor = getattr(Display, 'FLOOR', '.')
            player_level = getattr(self.player, 'level', 1)
            
            # Minimum distance from player (enemies spawn far away)
            min_distance = 60  # Manhattan distance
            
            for _ in range(count):
                # Try to find a valid spawn location
                attempts = 0
                while attempts < 100:
                    rx = random.randint(1, mw - 2)
                    ry = random.randint(1, mh - 2)
                    
                    # Check distance from player
                    dist_to_player = abs(rx - self.player.x) + abs(ry - self.player.y)
                    
                    # Check if location is valid (floor tile and far from player)
                    if not (dist_to_player > min_distance and self.game_map[ry][rx] == floor):
                        attempts += 1
                        continue
                    
                    # In tombs, also check distance from stairs (at least 3 tiles away)
                    valid_stair_distance = True
                    if getattr(self, 'in_tomb', False):
                        min_stair_distance = 3
                        current_floor = getattr(self, 'tomb_floor', 0)
                        
                        # Get stairs for current floor
                        try:
                            if (hasattr(self, 'tomb_stairs') and 
                                isinstance(self.tomb_stairs, list) and 
                                current_floor < len(self.tomb_stairs)):
                                
                                stairs = self.tomb_stairs[current_floor]
                                
                                # Check distance from stairs up
                                if 'up' in stairs:
                                    stair_x, stair_y = stairs['up']
                                    stair_distance = abs(rx - stair_x) + abs(ry - stair_y)
                                    if stair_distance < min_stair_distance:
                                        valid_stair_distance = False
                                
                                # Check distance from stairs down
                                if valid_stair_distance and 'down' in stairs:
                                    stair_x, stair_y = stairs['down']
                                    stair_distance = abs(rx - stair_x) + abs(ry - stair_y)
                                    if stair_distance < min_stair_distance:
                                        valid_stair_distance = False
                        except Exception:
                            # If we can't check stairs, allow spawn (surface behavior)
                            pass
                    
                    if valid_stair_distance:
                        
                        # Choose enemy type based on random roll
                        choice_roll = random.random()
                        lvl = max(1, player_level + random.randint(-1, 2))
                        
                        if choice_roll < 0.35:
                            e = sith.create_sith_trooper(level=lvl)
                        elif choice_roll < 0.55:
                            e = sith.create_sith_acolyte(level=lvl)
                        elif choice_roll < 0.75:
                            e = sith.create_sith_warrior(level=lvl)
                        elif choice_roll < 0.90:
                            e = sith.create_sith_assassin(level=lvl)
                        else:
                            lvl = max(1, player_level + random.randint(0, 3))
                            e = sith.create_sith_officer(level=lvl)
                        
                        e.x, e.y = rx, ry
                        
                        # Give the enemy a patrol route
                        try:
                            patrol = []
                            for _p in range(random.randint(2, 4)):
                                nx = rx + random.randint(-8, 8)
                                ny = ry + random.randint(-8, 8)
                                if (0 <= ny < mh and 0 <= nx < mw and 
                                    self.game_map[ny][nx] == floor):
                                    patrol.append((nx, ny))
                            if patrol:
                                e.patrol_points = patrol
                                e._patrol_index = 0
                        except Exception:
                            pass
                        
                        self.enemies.append(e)
                        spawned += 1
                        break
                    
                    attempts += 1
        except Exception:
            pass
        
        return spawned

    def _trigger_tomb_atmospheric_event(self):
        """Trigger tomb-specific atmospheric events with reduced frequency."""
        try:
            # Tomb-specific atmospheric events
            tomb_events = [
                {
                    'message': '#red#[Tomb]#0# Ancient stones whisper of forgotten darkness.',
                    'effect': None
                },
                {
                    'message': '#purple#[Tomb]#0# The air grows thick with residual Sith energy.',
                    'effect': None
                },
                {
                    'message': '#yellow#[Tomb]#0# Dust motes dance in shafts of artificial light.',
                    'effect': None
                },
                {
                    'message': '#blue#[Tomb]#0# Ancient mechanisms hum with dormant power.',
                    'effect': None
                },
                {
                    'message': '#green#[Tomb]#0# The Force flows strangely through these halls.',
                    'effect': None
                },
                {
                    'message': '#red#[Tomb]#0# Shadows seem to move when you\'re not watching.',
                    'effect': None
                },
                {
                    'message': '#purple#[Tomb]#0# The walls bear ancient Sith inscriptions.',
                    'effect': None
                },
                {
                    'message': '#cyan#[Tomb]#0# A distant echo suggests vast chambers beyond.',
                    'effect': None
                }
            ]
            
            event = random.choice(tomb_events)
            
            # Display the atmospheric message
            if hasattr(self, 'ui') and hasattr(self.ui, 'messages'):
                self.ui.messages.add(event['message'])
            
            # Apply any effects (currently just atmospheric text)
            if event.get('effect'):
                # Future: Add tomb-specific effects like temporary vision changes
                pass
                
        except Exception as e:
            pass  # Silently fail for atmospheric events

        # Check for enemy respawning after movement
        try:
            self._check_enemy_respawn()
        except Exception:
            pass

        # Movement was successful
        return True

    def _check_enemy_respawn(self):
        """Respawn enemies in groups when the map is cleared, with increasing difficulty."""
        try:
            # Only respawn on surface (not in tombs or special dungeons)
            if (hasattr(self, 'in_tomb') and self.in_tomb) or hasattr(self, 'current_special_dungeon'):
                return
            
            current_enemies = len(getattr(self, 'enemies', []))
            
            # Respawn threshold: when fewer than 3 enemies remain
            if current_enemies < 3:
                # Calculate difficulty scaling based on player progress
                player_level = getattr(self.player, 'level', 1)
                tombs_cleared = getattr(self.player, 'tombs_cleared', 0)
                corruption = getattr(self.player, 'corruption', 50)
                
                # Determine spawn intensity (2-6 enemies per group)
                base_spawn_count = min(6, 2 + player_level // 3 + tombs_cleared)
                spawn_count = __import__('random').randint(base_spawn_count - 1, base_spawn_count + 2)
                
                # Select enemy types based on difficulty
                enemy_pool = []
                if player_level >= 1:
                    enemy_pool.extend(['sith_trooper'] * 3)
                if player_level >= 3 or tombs_cleared >= 1:
                    enemy_pool.extend(['dark_jedi', 'sith_assassin'] * 2)
                if player_level >= 5 or tombs_cleared >= 2:
                    enemy_pool.extend(['sith_lord', 'dark_side_adept'])
                if corruption > 70:  # High corruption attracts stronger enemies
                    enemy_pool.extend(['shadow_stalker', 'corrupted_jedi'])
                if corruption < 30:  # Light side attracts different enemies
                    enemy_pool.extend(['imperial_agent', 'bounty_hunter'])
                
                if not enemy_pool:
                    enemy_pool = ['sith_trooper', 'dark_jedi']
                
                # Spawn enemies in a group formation
                player_x, player_y = getattr(self.player, 'x', 0), getattr(self.player, 'y', 0)
                spawn_radius = __import__('random').randint(15, 25)  # Spawn 15-25 tiles away
                
                spawned = 0
                attempts = 0
                max_attempts = 50
                
                while spawned < spawn_count and attempts < max_attempts:
                    # Random angle for group positioning
                    angle = __import__('random').uniform(0, 2 * 3.14159)
                    base_x = player_x + int(spawn_radius * __import__('math').cos(angle))
                    base_y = player_y + int(spawn_radius * __import__('math').sin(angle))
                    
                    # Group formation: spawn in 3x3 area around base position
                    group_offset_x = __import__('random').randint(-2, 2)
                    group_offset_y = __import__('random').randint(-2, 2)
                    spawn_x = base_x + group_offset_x
                    spawn_y = base_y + group_offset_y
                    
                    attempts += 1
                    
                    # Check if position is valid
                    mh = len(getattr(self, 'game_map', []))
                    mw = len(getattr(self, 'game_map', [[]])[0]) if mh else 0
                    
                    if not (0 <= spawn_x < mw and 0 <= spawn_y < mh):
                        continue
                    
                    # Check if tile is walkable
                    try:
                        tile = str(self.game_map[spawn_y][spawn_x])
                        if tile in {'#', '~', 'r', 'T'}:  # Non-walkable tiles
                            continue
                    except Exception:
                        continue
                    
                    # Check if position is too close to player
                    if abs(spawn_x - player_x) + abs(spawn_y - player_y) < 10:
                        continue
                    
                    # Spawn enemy
                    try:
                        from jedi_fugitive.game.enemy import create_enemy
                        enemy_type = __import__('random').choice(enemy_pool)
                        enemy = create_enemy(enemy_type, spawn_x, spawn_y)
                        
                        # Scale enemy stats based on difficulty
                        if hasattr(enemy, 'attack'):
                            enemy.attack += tombs_cleared * 2 + player_level
                        if hasattr(enemy, 'defense'):
                            enemy.defense += tombs_cleared + player_level // 2
                        if hasattr(enemy, 'hp') and hasattr(enemy, 'max_hp'):
                            bonus_hp = tombs_cleared * 5 + player_level * 3
                            enemy.max_hp += bonus_hp
                            enemy.hp = enemy.max_hp
                        
                        if not hasattr(self, 'enemies'):
                            self.enemies = []
                        self.enemies.append(enemy)
                        spawned += 1
                        
                    except Exception as e:
                        continue
                
                if spawned > 0:
                    # Notify player of respawn
                    if hasattr(self, 'ui') and hasattr(self.ui, 'messages'):
                        spawn_message = self._get_respawn_message(spawned, corruption, tombs_cleared)
                        self.ui.messages.add("═" * 60)
                        self.ui.messages.add(spawn_message)
                        self.ui.messages.add(f"💀 {spawned} enemies detected approaching your position!")
                        self.ui.messages.add("═" * 60)
        
        except Exception:
            pass  # Fail silently to avoid disrupting gameplay

    def _get_respawn_message(self, spawn_count, corruption, tombs_cleared):
        """Get atmospheric message for enemy respawn based on player state."""
        if corruption > 70:
            return "🔴 Your dark power draws the attention of shadow hunters..."
        elif corruption < 30:
            return "🔵 Imperial forces have detected your Jedi presence..."
        elif tombs_cleared >= 3:
            return "⚫ Ancient guardians stir, sensing the tomb disturbances..."
        elif spawn_count >= 5:
            return "🟡 A patrol squadron emerges from the wasteland..."
        else:
            return "🟠 Hostile contacts detected on long-range sensors..."

    def meditate(self) -> bool:
        """Spend a turn to meditate and reduce stress by 20 if safe (no enemies nearby). Also restores HP and Force energy."""
        try:
            import random
            px, py = getattr(self.player, 'x', 0), getattr(self.player, 'y', 0)
            safe = True
            for e in list(getattr(self, 'enemies', []) or []):
                try:
                    if abs(getattr(e,'x',0)-px) + abs(getattr(e,'y',0)-py) <= 5:
                        safe = False; break
                except Exception:
                    continue
            if not safe:
                try: self.ui.messages.add("You can't meditate here; it's too dangerous.")
                except Exception: pass
                return False
            
            # Display meditation mantra based on alignment
            try:
                corruption = getattr(self.player, 'dark_corruption', 50)
                
                # Pure Light Side mantras (0-20 corruption)
                light_mantras = [
                    "There is no emotion, there is peace.",
                    "There is no ignorance, there is knowledge.",
                    "There is no passion, there is serenity.",
                    "There is no chaos, there is harmony.",
                    "There is no death, there is the Force.",
                    "The Force flows through all living things.",
                    "I am one with the Force, and the Force is with me.",
                    "May the Force guide me to the light.",
                ]
                
                # Light-leaning mantras (21-40 corruption)
                light_leaning_mantras = [
                    "Through the Force, I find balance.",
                    "The light guides my path through darkness.",
                    "I seek wisdom, not power.",
                    "Peace guides my blade, not anger.",
                    "The Force is my ally, and a powerful ally it is.",
                    "I am a guardian of peace and justice.",
                    "Through knowledge and defense, I find strength.",
                ]
                
                # Balanced mantras (41-59 corruption)
                balanced_mantras = [
                    "The Force flows through light and shadow alike.",
                    "I walk the path between extremes.",
                    "Power without wisdom is chaos; wisdom without power is futile.",
                    "Both light and dark serve the Force.",
                    "I embrace the full spectrum of the Force.",
                    "Balance is the true path to understanding.",
                    "Neither Jedi nor Sith, but something more.",
                ]
                
                # Dark-leaning mantras (60-79 corruption)
                dark_leaning_mantras = [
                    "Through passion, I find strength.",
                    "The dark side offers power beyond restraint.",
                    "I will not be bound by the old codes.",
                    "Emotion fuels my connection to the Force.",
                    "Power is the only truth that matters.",
                    "I am free to explore the depths of the Force.",
                    "The galaxy respects only strength.",
                ]
                
                # Pure Dark Side mantras (80-100 corruption)
                dark_mantras = [
                    "Peace is a lie, there is only passion.",
                    "Through passion, I gain strength.",
                    "Through strength, I gain power.",
                    "Through power, I gain victory.",
                    "Through victory, my chains are broken.",
                    "The Force shall free me.",
                    "The dark side is my ally, and I am its master.",
                    "I embrace the shadows that others fear.",
                ]
                
                # Select appropriate mantra based on corruption level
                if corruption <= 20:
                    mantra = random.choice(light_mantras)
                elif corruption <= 40:
                    mantra = random.choice(light_leaning_mantras)
                elif corruption <= 59:
                    mantra = random.choice(balanced_mantras)
                elif corruption <= 79:
                    mantra = random.choice(dark_leaning_mantras)
                else:
                    mantra = random.choice(dark_mantras)
                
                # Display the mantra
                self.ui.messages.add(f'"{mantra}"')
            except Exception:
                pass
            
            # Reduce stress
            try:
                self.player.reduce_stress(20)
            except Exception:
                pass
            
            # Restore Force energy (30 points)
            try:
                if hasattr(self.player, 'force_energy'):
                    old_energy = self.player.force_energy
                    self.player.force_energy = min(self.player.max_force_energy, self.player.force_energy + 30)
                    force_restored = self.player.force_energy - old_energy
                else:
                    force_restored = 0
            except Exception:
                force_restored = 0
            
            # Restore HP (10-20% of max HP, alignment-based)
            hp_healed = 0
            try:
                if hasattr(self.player, 'hp') and hasattr(self.player, 'max_hp'):
                    corruption = getattr(self.player, 'dark_corruption', 50)
                    
                    # Light side heals more from meditation
                    if corruption <= 20:  # Pure Light
                        heal_percent = random.uniform(0.15, 0.25)
                    elif corruption <= 40:  # Light
                        heal_percent = random.uniform(0.12, 0.20)
                    elif corruption <= 59:  # Balanced
                        heal_percent = random.uniform(0.10, 0.15)
                    elif corruption <= 79:  # Dark
                        heal_percent = random.uniform(0.07, 0.12)
                    else:  # Pure Dark
                        heal_percent = random.uniform(0.05, 0.10)
                    
                    heal_amount = max(5, int(self.player.max_hp * heal_percent))
                    old_hp = self.player.hp
                    self.player.hp = min(self.player.max_hp, self.player.hp + heal_amount)
                    hp_healed = self.player.hp - old_hp
            except Exception:
                pass
            
            # Message with results
            try:
                msg_parts = ["You meditate and find inner peace."]
                if hp_healed > 0:
                    msg_parts.append(f"(+{hp_healed} HP)")
                if force_restored > 0:
                    msg_parts.append(f"(+{force_restored} Force)")
                msg_parts.append("(-20 Stress)")
                self.ui.messages.add(" ".join(msg_parts))
            except Exception:
                pass
            
            return True
        except Exception:
            return False

    def perform_scan(self) -> bool:
        """Use Force Sense to detect the nearest tomb entrance.

        Produces a message describing approximate distance and cardinal direction.
        Sets a cooldown on the player (player.scan_cooldown) to prevent spamming.
        """
        try:
            # cooldown check
            cd = int(getattr(self.player, 'scan_cooldown', 0) or 0)
            if cd > 0:
                try:
                    self.add_message(f"Force Sense recharging: {cd} turn(s) remaining.")
                except Exception:
                    pass
                return False

            # find nearest tomb entrance
            tombs = getattr(self, 'tomb_entrances', None) or set()
            if not tombs:
                try:
                    self.add_message("You sense no tombs nearby.")
                except Exception:
                    pass
                # set a tiny cooldown so player doesn't spam the message
                try: setattr(self.player, 'scan_cooldown', 2)
                except Exception: pass
                return False

            px = int(getattr(self.player, 'x', 0)); py = int(getattr(self.player, 'y', 0))
            best = None; best_dist = None
            for (tx, ty) in tombs:
                try:
                    dx = int(tx) - px; dy = int(ty) - py
                    dist = (dx*dx + dy*dy) ** 0.5
                    if best_dist is None or dist < best_dist:
                        best_dist = dist; best = (tx, ty, dx, dy)
                except Exception:
                    continue

            if best is None:
                try:
                    self.add_message("You sense no tombs nearby.")
                except Exception:
                    pass
                try: setattr(self.player, 'scan_cooldown', 2)
                except Exception: pass
                return False

            tx, ty, dx, dy = best
            # compute cardinal direction from player to tomb
            try:
                import math
                angle = (math.degrees(math.atan2(-dy, dx)) + 360.0) % 360.0
                # map to 8 compass points
                if 22.5 <= angle < 67.5:
                    dir_s = 'NE'
                elif 67.5 <= angle < 112.5:
                    dir_s = 'N'
                elif 112.5 <= angle < 157.5:
                    dir_s = 'NW'
                elif 157.5 <= angle < 202.5:
                    dir_s = 'W'
                elif 202.5 <= angle < 247.5:
                    dir_s = 'SW'
                elif 247.5 <= angle < 292.5:
                    dir_s = 'S'
                elif 292.5 <= angle < 337.5:
                    dir_s = 'SE'
                else:
                    dir_s = 'E'
                dist_approx = int(max(0, round(best_dist)))
            except Exception:
                dir_s = '?'; dist_approx = int(max(0, round(best_dist or 0)))

            # message and cooldown
            try:
                self.add_message(f"You sense a tomb approximately ~{dist_approx} tiles to the {dir_s}.")
            except Exception:
                pass
            try:
                # set cooldown in turns (tunable)
                setattr(self.player, 'scan_cooldown', int(getattr(self, 'scan_cooldown_turns', 8) or 8))
            except Exception:
                pass
            return True
        except Exception:
            return False

    def find_nearest_tomb_info(self, x: int, y: int):
        """Return (tx, ty, dist, dir_str) of nearest tomb to (x,y) or None if no tombs."""
        try:
            tombs = getattr(self, 'tomb_entrances', None) or set()
            if not tombs:
                return None
            best = None; best_dist = None
            for (tx, ty) in tombs:
                try:
                    dx = int(tx) - int(x); dy = int(ty) - int(y)
                    dist = (dx*dx + dy*dy) ** 0.5
                    if best_dist is None or dist < best_dist:
                        best_dist = dist; best = (int(tx), int(ty), dx, dy)
                except Exception:
                    continue
            if best is None:
                return None
            tx, ty, dx, dy = best
            try:
                import math
                angle = (math.degrees(math.atan2(-dy, dx)) + 360.0) % 360.0
                if 22.5 <= angle < 67.5:
                    dir_s = 'NE'
                elif 67.5 <= angle < 112.5:
                    dir_s = 'N'
                elif 112.5 <= angle < 157.5:
                    dir_s = 'NW'
                elif 157.5 <= angle < 202.5:
                    dir_s = 'W'
                elif 202.5 <= angle < 247.5:
                    dir_s = 'SW'
                elif 247.5 <= angle < 292.5:
                    dir_s = 'S'
                elif 292.5 <= angle < 337.5:
                    dir_s = 'SE'
                else:
                    dir_s = 'E'
            except Exception:
                dir_s = '?'
            return (tx, ty, int(round(best_dist or 0)), dir_s)
        except Exception:
            return None

    def notify_being_hunted(self, duration: int = 6):
        """Externally signal a being-hunted event: apply initial stress and set ticks for per-turn stress."""
        try:
            try:
                added = self.player.add_stress(10, source='being_hunted_start')
                if getattr(self.ui, 'messages', None):
                    self.ui.messages.add(f"You are being hunted! (+{added} stress)")
            except Exception:
                pass
            self.being_hunted_ticks = max(getattr(self, 'being_hunted_ticks', 0), int(duration))
        except Exception:
            pass

    def compute_visibility(self):
        """Compute line-of-sight from player and update self.visible and self.explored."""
        try:
            # local Bresenham implementation to avoid import cycles
            def _bresenham_line(x0, y0, x1, y1):
                x0 = int(x0); y0 = int(y0); x1 = int(x1); y1 = int(y1)
                dx = abs(x1 - x0); sx = 1 if x0 < x1 else -1
                dy = -abs(y1 - y0); sy = 1 if y0 < y1 else -1
                err = dx + dy
                x, y = x0, y0
                while True:
                    yield (x, y)
                    if x == x1 and y == y1:
                        break
                    e2 = 2 * err
                    if e2 >= dy:
                        err += dy
                        x += sx
                    if e2 <= dx:
                        err += dx
                        y += sy

            vis = set()
            mh = len(self.game_map); mw = len(self.game_map[0]) if mh else 0
            px = int(getattr(self.player, "x", 0)); py = int(getattr(self.player, "y", 0))
            # Base LOS radius plus any temporary bonus from Force: Reveal
            radius = int(getattr(self.player, "los_radius", 6) or 6)
            try:
                if getattr(self.player, 'los_bonus_turns', 0) > 0:
                    radius += int(getattr(self.player, 'los_bonus_radius', 0) or 0)
            except Exception:
                pass
            
            # Apply atmospheric visibility modifiers
            try:
                if hasattr(self, 'atmospheric_manager'):
                    visibility_modifier = self.atmospheric_manager.get_visibility_modifier()
                    radius = max(1, radius + visibility_modifier)  # Minimum visibility of 1
            except Exception:
                pass
            # optionally allow a small extra ray margin beyond the base LOS (e.g. fog_of_war + 2)
            try:
                fov_extra = int(getattr(self, 'fov_ray_extra', 2) or 2)
            except Exception:
                fov_extra = 2
            if getattr(self, 'fog_of_war', False):
                max_ray = max(0, radius + fov_extra)
            else:
                max_ray = radius

            # blocking tile set (tile itself can be visible). All non-floor, non-wreckage tiles block line-of-sight
            floor_ch = getattr(Display, "FLOOR", ".")
            wreckage_ch = getattr(Display, "WRECKAGE", "x")
            for ty in range(max(0, py - max_ray), min(mh, py + max_ray + 1)):
                for tx in range(max(0, px - max_ray), min(mw, px + max_ray + 1)):
                    dx = tx - px; dy = ty - py
                    # limit candidate tiles to the configured effective ray distance
                    if dx*dx + dy*dy > max_ray*max_ray:
                        continue
                    blocked = False
                    try:
                        for lx, ly in _bresenham_line(px, py, tx, ty):
                            if lx == px and ly == py:
                                continue
                            if not (0 <= ly < mh and 0 <= lx < mw):
                                blocked = True
                                break
                            ch = self.game_map[ly][lx]
                            # if blocking tile is the target tile, show it; otherwise block further tiles
                            # All non-floor, non-wreckage, non-special tiles block line-of-sight
                            if ch not in (floor_ch, wreckage_ch, 'O', 'G', 'L', '?', '!', '@', '$', '%', '&', '*', 'C', 'S', 'M', 'r'):
                                if (lx, ly) == (tx, ty):
                                    # target is blocking but visible
                                    blocked = False
                                else:
                                    blocked = True
                                break
                    except Exception:
                        blocked = True
                    if not blocked:
                        vis.add((tx, ty))
            # update manager visibility and exploration
            self.visible = vis
            if not getattr(self, "explored", None):
                self.explored = set()
            try:
                self.explored |= vis
            except Exception:
                self.explored = set(self.explored) | vis
            # Update current biome
            try:
                if hasattr(self, 'map_biomes') and self.map_biomes:
                    px, py = getattr(self.player, 'x', 0), getattr(self.player, 'y', 0)
                    if 0 <= py < len(self.map_biomes) and 0 <= px < len(self.map_biomes[0]):
                        self.current_biome = self.map_biomes[py][px]
            except Exception:
                pass
            return vis
        except Exception:
            # best-effort: keep previous sets if anything fails
            try:
                if not hasattr(self, "visible"):
                    self.visible = set()
                if not hasattr(self, "explored"):
                    self.explored = set()
            except Exception:
                pass
    
    def generate_surface_npcs(self):
        """Generate NPCs with quests on the surface map."""
        if not self.quest_manager or not hasattr(self, 'game_map'):
            return
            
        # Find suitable positions for NPCs (avoid walls, water, etc.)
        available_positions = []
        
        for y in range(len(self.game_map)):
            for x in range(len(self.game_map[0])):
                if (self.game_map[y][x] == '.' and 
                    (x, y) != (self.player.x, self.player.y) and
                    not any(enemy.x == x and enemy.y == y for enemy in self.enemies)):
                    available_positions.append((x, y))
        
        # Generate 3-6 NPCs on surface based on world size
        num_npcs = min(6, max(3, len(available_positions) // 50))
        
        # Place NPCs
        for i in range(min(num_npcs, len(available_positions))):
            if available_positions:
                pos = random.choice(available_positions)
                available_positions.remove(pos)
                
                # Determine biome for this position
                biome = 'forest'  # default
                if hasattr(self, 'map_biomes') and self.map_biomes:
                    if 0 <= pos[1] < len(self.map_biomes) and 0 <= pos[0] < len(self.map_biomes[0]):
                        biome = self.map_biomes[pos[1]][pos[0]]
                
                # Create NPC with quest
                npc = self.quest_manager.create_random_npc(
                    pos[0], pos[1], 
                    level=1,  # Surface NPCs are level 1
                    biome=biome
                )
                
                if npc:
                    self.npcs_on_map[pos] = npc
                    
        print(f"✓ Generated {len(self.npcs_on_map)} NPCs with quests on surface")
    
    def interact_with_npc(self, x, y):
        """Interact with an NPC at the given position."""
        npc = self.npcs_on_map.get((x, y))
        if not npc or not self.quest_manager:
            return False
            
        # Start or continue conversation
        conversation = self.quest_manager.start_conversation(npc, self.player)
        
        if conversation:
            # Display conversation in UI
            self.ui.messages.add(f"{npc.name}: {conversation['message']}")
            
            # Handle quest interactions
            if conversation.get('quest_offered'):
                self.ui.messages.add("Press 'a' to accept the quest, or any other key to decline.")
                self.active_conversations[(x, y)] = {
                    'npc': npc,
                    'type': 'quest_offer',
                    'quest': conversation['quest']
                }
            elif conversation.get('quest_complete'):
                # Complete the quest automatically
                rewards = self.quest_manager.complete_quest(conversation['quest'], self.player)
                if rewards:
                    for reward_type, amount in rewards.items():
                        if reward_type == 'experience':
                            self.player.gain_experience(amount)
                            self.ui.messages.add(f"Gained {amount} experience!")
                        elif reward_type == 'credits':
                            self.player.credits += amount
                            self.ui.messages.add(f"Received {amount} credits!")
            
            return True
        
        return False
    
    def handle_npc_response(self, key, x, y):
        """Handle player response to NPC conversation."""
        conversation = self.active_conversations.get((x, y))
        if not conversation:
            return False
            
        if conversation['type'] == 'quest_offer':
            if key == 'a':  # Accept quest
                quest = conversation['quest']
                self.quest_manager.accept_quest(quest, self.player)
                self.ui.messages.add(f"Quest accepted: {quest.title}")
                
                # Update NPC relationship
                npc = conversation['npc']
                npc.relationship_level = min(5, npc.relationship_level + 1)
                
            else:  # Decline quest
                self.ui.messages.add("Quest declined.")
                
            # Clear conversation
            del self.active_conversations[(x, y)]
            return True
            
        return False
