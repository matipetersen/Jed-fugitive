import curses
import os
import sys
import datetime
from typing import Optional, Tuple
import pkgutil
import importlib
import random

from jedi_fugitive.ui.silq_ui import SILQUI
from jedi_fugitive.game.player import Player
from jedi_fugitive.game import projectiles, force_abilities, map_features, input_handler, ui_renderer, equipment
from jedi_fugitive.game.enemy import Enemy, EnemyType, process_enemies as enemy_process_enemies
from jedi_fugitive.game.personality import EnemyPersonality, ENEMY_TAUNTS
from jedi_fugitive.game.level import generate_crash_site, generate_dungeon_level, Display
from jedi_fugitive.ui.dialog import DialogueSystem, UIMessageBuffer
from jedi_fugitive.config import MAP_RATIO_W, MAP_RATIO_H, STATS_RATIO_W, DIFFICULTY_MULTIPLIER, MAP_SCALE, DEPTH_DIFFICULTY_RATE
from jedi_fugitive.game.combat import player_attack, calculate_hit
from jedi_fugitive.game import abilities, map_features as mf
from jedi_fugitive.game.sith_codex import SithCodex, populate_canon, populate_artifacts

class GameManager:
    """Clean, defensive GameManager suitable to drive the curses UI and other subsystems."""

    def __init__(self, stdscr):
        print("⟳ Initializing Jedi Fugitive...")
        self.stdscr = stdscr
        # Get term size for later use
        self.term_w = self.stdscr.getmaxyx()[1]
        self.ui = SILQUI(stdscr)
        self.ui.init_colors()
        self.dialog = DialogueSystem()
        self.player = Player(0, 0)
        self.enemies = []
        self.game_map = []
        self.tomb_entrances = set()
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
        self.enemies_per_respawn = 1  # Start with 1 enemy per respawn cycle
        self.key_bindings = {}
        self.key_help = {}
        self.last_size = (0, 0)
        self.layout = {}
        self.show_codex = False  # Toggle for Sith Codex display
        # default splash/instruction lines exposed to the command/help panel
        self.splash_instructions = [
            "═══════════════════ CONTROLS ═══════════════════",
            "Movement: ↑↓←→ arrows  hjkl cardinal  ybn/7913 diagonal",
            "Actions: g=pickup  e=equip  u=use  d=drop  x=inspect",
            "Combat: Walk into enemy  t=grenade  F=shoot",
            "Force: f=abilities  c=compass  m=meditate",
            "Info: j=journal  i=inventory  v=codex  @=character",
            "Meta: ?=help  C=craft  q=quit  ESC=cancel",
            "════════════════════════════════════════════════",
            "Artifacts: 'a'=ABSORB (Dark) or 'd'=DESTROY (Light)",
            "Your choices shape your Force alignment and abilities!",
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
        # Loading...
        # compute layout and notify UI (robust, minimal)
        try:
            # Loading...
            self.ui.term_h, self.ui.term_w = self.stdscr.getmaxyx()
        except Exception as e:
            # Loading...
            self.ui.term_h, self.ui.term_w = 40, 140
        # Loading...
        mw, mh, sw, aw, mhmsg, cmdh = self._compute_layout()
        # Loading...
        try:
            # Loading...
            self.ui.create_layout(mw, mh, sw, aw, mhmsg, cmdh)
        except Exception as e:
            # Loading...
            pass
        self.panels_ready = True
        # ensure message buffer
        try:
            # Loading...
            self.ui.messages = UIMessageBuffer()
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
            # Loading...
            try:
                self.ui.messages = UIMessageBuffer() if 'UIMessageBuffer' in globals() else None
            except Exception:
                self.ui.messages = None
        # Wire UI/game references into player so player.level_up can present UI prompts
        try:
            # Loading...
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
            # Loading...
            pass
        # Give the player a small starting inventory: 2 compasses and 1 stimpack
        try:
            # Loading...
            if not hasattr(self.player, 'inventory') or self.player.inventory is None:
                self.player.inventory = []
            # Create lightweight dict entries for the consumables so they display correctly
            from jedi_fugitive.items.consumables import ITEM_DEFS
            # helper to get a copy of an item def by id
            def _lookup(id_):
                try:
                    for it in ITEM_DEFS:
                        if it.get('id') == id_:
                            return dict(it)
                except Exception:
                    pass
                return {'id': id_, 'name': id_}
            # add two compasses and one stimpack (stimpack id is 'stimpack')
            try:
                self.player.inventory.append(_lookup('compass'))
                self.player.inventory.append(_lookup('compass'))
            except Exception:
                try: self.player.inventory.extend([{'id':'compass','name':'Compass'},{'id':'compass','name':'Compass'}])
                except Exception: pass
            try:
                self.player.inventory.append(_lookup('stimpack'))
            except Exception:
                try: self.player.inventory.append({'id':'stimpack','name':'Stimpack'})
                except Exception: pass
        except Exception as e:
            # Loading...
            pass
        # initial commands hint
        self.last_commands = "Move: h/j/k/l or arrows. g=pickup f=force q=quit"
        # register inspect key so it appears in the commands/help panel
        try:
            # Loading...
            # register a no-op handler; input handling for 'x' is implemented in input_handler
            self.register_command('x', lambda: None, 'Inspect')
        except Exception as e:
            # Loading...
            try:
                # best-effort: set help entry directly
                self.key_help['x'] = 'Inspect'
                self.update_command_gui()
            except Exception:
                pass
        # register a scan/compass ability (key 'c') to help locate tombs
        try:
            # Loading...
            self.register_command('c', lambda: self.perform_scan(), 'Scan (compass)')
        except Exception as e:
            # Loading...
            try:
                self.key_help['c'] = 'Scan (compass)'
                self.update_command_gui()
            except Exception:
                pass
        # Initialize Sith Codex (optional subsystem). Safe: if anything fails we keep going.
        try:
            # Loading...
            self.sith_codex = SithCodex()
            populate_canon(self.sith_codex)
            populate_artifacts(self.sith_codex)
        except Exception as e:
            # Loading...
            self.sith_codex = None

        # Loading...

    def generate_world(self):
        print("⟳ Generating galaxy...")
        try:
            map_features.generate_world(self)
            print("✓ World generated successfully")
        except Exception:
            print("✗ World generation failed")
            try: self.ui.messages.add("World generation failed.") 
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
        
        # Add initial travel log entries
        try:
            if hasattr(self.player, 'add_log_entry'):
                self.player.add_log_entry("My ship crashed on this forsaken world. I am alone, but alive.", 0)
                self.player.add_log_entry("The Force echoes with dark power here. Every choice I make will define who I become.", 1)
                self.player.add_log_entry("Will I resist the darkness, or embrace it? The path ahead is mine to choose.", 2)
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
        self.initialize()
        self.generate_world()
        # main loop
        while self.running:
            # redraw
            try:
                self.draw()
            except Exception:
                try: self.dump_debug_state()
                except Exception: pass
            # input
            try:
                key = self.stdscr.getch()
                input_handler.handle_input(self, key)
            except Exception:
                try: self.ui.messages.add("Input handler error.")
                except Exception: pass

            # process game tick
            try:
                self.turns += 1
                
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
                        self.player.regenerate_force(in_combat=in_combat)
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
                    # Generate death log entry for stress overload deaths
                    try:
                        if getattr(self, '_breaking_point_triggered', False):
                            # Stress death - different narrative
                            body_fate = ""
                            in_tomb = getattr(self, 'in_tomb', False)
                            if in_tomb:
                                tomb_floor = getattr(self, 'tomb_floor', 1)
                                body_fate = f"Your broken mind left your body a hollow shell in the depths of the Sith Tomb Level {tomb_floor}."
                            else:
                                biome = getattr(self, 'current_biome', 'unknown wasteland')
                                body_fate = f"Your sanity shattered, you collapsed in the {biome}, never to rise again."
                            
                            death_entry = f"[DEATH] Succumbed to overwhelming stress and mental anguish. {body_fate} The darkness of this place proved too much to bear."
                            self.player.add_to_travel_log(death_entry)
                    except Exception:
                        try:
                            self.player.add_to_travel_log("[DEATH] Fell to stress overload.")
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
                    # Loading...
                    sys.stdout.flush()
                    self.running = False
                    break
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
        try:
            # prefer map_features implementation (import at top as mf)
            try:
                entered = mf.enter_tomb(self)
            except Exception:
                # fallback to direct import in case alias not present
                from jedi_fugitive.game import map_features as _mf
                entered = _mf.enter_tomb(self)
            if not entered:
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
            return True
        except Exception as e:
            try:
                with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                    fh.write("GameManager.enter_tomb exception:\n")
                    import traceback; traceback.print_exc(file=fh)
            except Exception:
                pass
            try:
                if getattr(self, "ui", None) and getattr(self.ui, "messages", None):
                    self.ui.messages.add("Failed to enter tomb (see /tmp/jedi_fugitive_debug.txt).")
            except Exception:
                pass
            return False

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
                turn = entry.get('turn', 0)
                text = entry.get('text', '')
                
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
                        f.write("=== Jedi Fugitive debug snapshot ===\n")
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
                f"    ║{'JEDI FUGITIVE: ECHOES OF THE FALLEN'.center(box_width)}║",
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
                    "Master Yoda will oversee your recovery and debriefing.",
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
                "May the Force be with you, always.",
                "",
                "═" * min(term_w, 80),
            ]
            
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
            
            # Wait for final exit
            try:
                input("\nPress Enter to exit...")
            except Exception:
                pass
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
                "A momentary distraction, nothing more. The Empire marches on.",
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
            
            # Wait for final exit
            try:
                input("\nPress Enter to exit...")
            except Exception:
                pass
        except Exception:
            print("GAME OVER")
            print("Press any key to exit.")

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

            # After moving: process Sith lore discovery
            try:
                self.process_sith_lore_discovery(self.player)
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
                                        self.items_on_map.remove(it)
                                        self.game_map[ny][nx] = getattr(Display, 'FLOOR', '.')
                                    except Exception:
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

            # After moving: handle stepping on special tiles (tombs / dungeon entrances)
            try:
                # consider digits 1/2/3 (int or str), or SITH_ENTRANCE constant or recorded tomb_entrances
                entrance_hit = False
                if tstr in ("D",):
                    entrance_hit = True
                try:
                    if target == getattr(Display, "SITH_ENTRANCE", None):
                        entrance_hit = True
                except Exception:
                    pass
                try:
                    if (nx, ny) in getattr(self, "tomb_entrances", set()):
                        entrance_hit = True
                except Exception:
                    pass

                # If the player stepped on stairs glyphs, automatically change floor
                try:
                    stairs_down = getattr(Display, 'STAIRS_DOWN', '>')
                    stairs_up = getattr(Display, 'STAIRS_UP', '<')
                    if tstr == str(stairs_down):
                        try:
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
                            entered = map_features.enter_tomb(self)
                        except Exception as e:
                            entered = False
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
                                boss_type = EnemyType.JEDI_MASTER
                                boss_name = "Jedi Master Alara"
                                taunt_msg = "A figure in tan robes appears. 'I sense great darkness in you. You will not escape!'"
                                combat_start = "The Jedi Master ignites a blue lightsaber and assumes a defensive stance."
                            else:
                                # Light Side player -> Sith Master hunts you
                                boss_type = EnemyType.SITH_LORD
                                boss_name = "Darth Malice"
                                taunt_msg = "A crimson blade pierces the darkness. 'The Light makes you weak, Jedi filth!'"
                                combat_start = "The Sith Lord attacks with vicious fury!"
                            
                            boss = Enemy(boss_type, level=lvl)
                            boss.is_boss = True
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
                            
                            # Place boss near ship
                            try:
                                boss.x = nx
                                boss.y = ny
                            except Exception:
                                try:
                                    boss.x = getattr(player, 'x', 0)
                                    boss.y = getattr(player, 'y', 0)
                                except Exception:
                                    boss.x = 0
                                    boss.y = 0
                            
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
                        # clear tomb-related fields
                        try:
                            delattr = setattr
                        except Exception:
                            delattr = None
                        for attr in ('tomb_levels', 'tomb_rooms', 'tomb_enemies', 'tomb_items', 'tomb_stairs', 'tomb_floor', 'tomb_stairs'):
                            try:
                                if hasattr(self, attr):
                                    try: delattr(self, attr, None)
                                    except Exception: pass
                            except Exception:
                                pass
                        self.current_depth = 1
                        try:
                            if getattr(self.ui, 'messages', None):
                                self.ui.messages.add("You return to the surface.")
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
                        self.ui.messages.add(f"You go {'down' if delta>0 else 'up'} the stairs to level {self.tomb_floor+1}.")
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
                    if in_combat and turn_count % 3 == 0:  # Every 3rd turn instead of every turn
                        try:
                            # Scale stress by number of nearby enemies (1-3 enemies)
                            stress_amount = min(3, max(1, nearby_enemies // 2))
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
                    
                    # Only apply low HP stress every 4th turn instead of every turn
                    if hp_pct <= 0.25 and turn_count % 4 == 0:
                        # Reduced from 5 to 3
                        self.player.add_stress(3, source='low_hp')
                        if getattr(self.ui, 'messages', None) and turn_count % 12 == 0:
                            low_hp_messages = [
                                "Your wounds make every breath a struggle.",
                                "Pain clouds your thoughts.",
                                "You're barely holding on."
                            ]
                            import random
                            self.ui.messages.add(random.choice(low_hp_messages))
                    # New: Very low HP (<10%) gets extra stress but still not every turn
                    elif hp_pct <= 0.10 and turn_count % 3 == 0:
                        self.player.add_stress(4, source='critical_hp')
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
                            # Reduced from 20 to 15
                            self.player.add_stress(15, source='surrounded')
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
                                    self.player.add_to_travel_log(f"[BREAKING POINT] The pressure became unbearable in the {biome}, but my connection to the Light Side saved me. I found clarity in the chaos and recovered my composure.")
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
                                    self.player.add_to_travel_log(f"[BREAKING POINT] I lost control in the {biome}. Pure rage erupted from me, striking down everything nearby. The dark side flows through me freely now... it felt good.")
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
                                    self.player.add_to_travel_log(f"[BREAKING POINT] My mind shut down in the {biome}. I couldn't fight, couldn't move, couldn't think. I just... stopped. For how long, I'm not sure.")
                                except Exception:
                                    pass
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
                    
                    if (dist_to_player > min_distance and 
                        self.game_map[ry][rx] == floor):
                        
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
        """Perform a compass-like scan towards the nearest tomb.

        Produces a message describing approximate distance and cardinal direction.
        Sets a cooldown on the player (player.scan_cooldown) to prevent spamming.
        """
        try:
            # cooldown check
            cd = int(getattr(self.player, 'scan_cooldown', 0) or 0)
            if cd > 0:
                try:
                    self.add_message(f"Scan recharging: {cd} turn(s) remaining.")
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
                            if ch not in (floor_ch, wreckage_ch, 'O', 'L', '?', '!', '@', '$', '%', '&', '*', 'C', 'S', 'M', 'r'):
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
            return getattr(self, "visible", set())
