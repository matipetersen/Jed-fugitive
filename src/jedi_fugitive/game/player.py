def equip_disguise(self, disguise):
        """
        Equip a disguise item (instance of Disguise or string key for DISGUISE_TYPES).
        Updates detection and suspicion accordingly.
        """
        from jedi_fugitive.items.disguises import DISGUISE_TYPES, Disguise
        if isinstance(disguise, str):
            disguise_obj = DISGUISE_TYPES.get(disguise)
        elif isinstance(disguise, Disguise):
            disguise_obj = disguise
        else:
            disguise_obj = None
        if disguise_obj:
            self.disguise = disguise_obj.name
            # Lower detection and suspicion when equipping a disguise
            self.detection_level = max(0, self.detection_level - disguise_obj.detection_bonus)
            self.suspicion = max(0, self.suspicion - 10)
        else:
            self.disguise = None
from typing import Dict, List, Any
from jedi_fugitive.items.weapons import Weapon, WeaponType
from jedi_fugitive.items.armor import Armor
# fix import: use force_abilities module (singular file force_ability likely missing)
from jedi_fugitive.game.force_abilities import FORCE_ABILITIES, ForceAbility, ForcePushPull
from jedi_fugitive.game.lightsaber_forms import get_available_forms, get_form_bonuses, FORMS_BY_NAME
from jedi_fugitive.config import MAX_INVENTORY_SIZE

class LevelUpOption:
    MAX_HP = 1
    FORCE_POWER = 2
    ACCURACY = 3
    EVASION = 4
    CRITICAL_CHANCE = 5

class Player:
    def __init__(self, x, y):
        self.turn_count = 0  # Track the number of turns taken by the player
        self.x = x
        self.y = y
        self._hp = 15  # Use private attribute for property backing
        self.max_hp = 15
        self.attack = 10
        self.defense = 5
        self.evasion = 10
        self.accuracy = 80
        # Performance optimization: cached stats
        self._cached_stats = None
        self._stats_cache_dirty = True
        # Psychological state - Enhanced stress system
        # stress: 0..max_stress (100+ triggers critical checks)
        self.stress = 0
        self.max_stress = 100  # Increases with level (player becomes more resilient)
        # alignment_score: 0..100 where >60 favors Light Side, <40 favors Dark Side
        self.alignment_score = 50
        # per-level stress resilience (reduces incoming stress and penalties)
        self._stress_resilience_per_level = 0.05  # Increased from 0.03 - 5% per level
        self._stress_max_increase_per_level = 5   # Max stress increases 5 per level
        # Stress reduction tracking
        self._stress_reduction_this_level = 0  # Track stress reductions for confidence
        self._successful_combats = 0  # Track victories for confidence building
        # track artifact corruption for visual feedback
        self.artifacts_consumed = 0
        self.dark_corruption = 0  # 0-100 scale, starts at 0 (Pure Light)
        # Travel log - narrative history of the player's journey
        self.travel_log = []
        self.kills_count = 0
        self.tombs_explored = 0
        self.lore_discovered = 0
        self.gold_collected = 0        # Counter for gold picked up (for greed index)
        self.inventory = []            # ensure inventory exists
        self.equipped_weapon = None    # current weapon (main hand)
        self.equipped_offhand = None   # offhand weapon or shield
        self.equipped_armor = None     # body armor
        
        # Weapon and Shield Masteries - improve damage/defense with equipment types
        # Now using ranked system: 0 = no mastery, 1-3 = ranks
        self.melee_mastery = 0      # Bonus damage with melee weapons
        self.ranged_mastery = 0     # Bonus damage with ranged weapons
        self.shield_mastery = 0     # Bonus defense with shields
        self.dual_wield_mastery = 0 # Bonus when dual-wielding
        self.force_mastery = 0      # Force power efficiency

        # --- New System Fields ---
        self.detection_level = 0  # For PursuitSystem integration
        self.disguise = None      # Current disguise item (None, 'civilian', 'stormtrooper', etc.)
        self.suspicion = 0        # Suspicion meter for disguise/suspicion system
        self.faction_reputation = {}  # {faction_name: -100 to 100}
        # System hooks (to be initialized by game manager)
        self.pursuit_system = None
        self.faction_manager = None
        
        # Lightsaber Forms - combat stances
        self.known_forms = ["Shii-Cho"]  # All Jedi start with Form I
        self.active_form = "Shii-Cho"     # Currently active stance

        # Start with a minimal set of force abilities (unlock more when leveling)
        try:
            self.force_abilities = {}
            # grant the basic Push/Pull ability by default if present
            for a in (FORCE_ABILITIES or []):
                if isinstance(a, ForcePushPull):
                    # Create a copy and unlock it for the player
                    import copy
                    player_ability = copy.deepcopy(a)
                    player_ability.unlocked = True
                    self.force_abilities[getattr(player_ability, 'name', 'Push/Pull')] = player_ability
                    break
        except Exception:
            self.force_abilities = {}

        # Force Energy System (Phase 1 redesign)
        self.force_energy = 100  # Current Force energy
        self.max_force_energy = 100  # Maximum Force energy
        self.force_regen_combat = 5  # Regeneration per turn in combat
        self.force_regen_peaceful = 20  # Regeneration per turn out of combat
        self.force_points = 2  # Legacy compatibility
        
        # Crafting Skill System
        self.craft_level = 1  # Starting crafting level
        self.craft_xp = 0     # Current crafting experience
        self.craft_xp_to_next = 100  # XP needed for next crafting level
        
        # Force Mastery System
        self.force_mastery_xp = {}  # Track XP per ability
        self.ability_mastery_level = {}  # Track mastery level per ability
        
        # Dual Path Level system - Light Side and Dark Side progression
        self.level = 1
        self.light_xp = 0  # XP from destroying artifacts (purification)
        self.dark_xp = 0   # XP from absorbing artifacts (corruption)
        self.light_level = 1
        self.dark_level = 1
        self.xp_to_next_light = 100
        self.xp_to_next_dark = 100
        # Legacy XP for backwards compatibility
        self.xp = 0
        self.xp_to_next = 100
        # Initialize default Force abilities (kept for compatibility)
        self.initialize_force_abilities()
        # Snapshot base stats so equipment system can restore them reliably
        try:
            self._base_stats = {
                "attack": int(getattr(self, "attack", 0)),
                "defense": int(getattr(self, "defense", 0)),
                "evasion": int(getattr(self, "evasion", 0)),
                "max_hp": int(getattr(self, "max_hp", 0)),
                "accuracy": int(getattr(self, "accuracy", 0)),
            }
        except Exception:
            try:
                self._base_stats = {"attack": 1, "defense": 0, "evasion": 0, "max_hp": 10, "accuracy": 80}
            except Exception:
                self._base_stats = {}
        # facing direction as a dx,dy tuple - used for inspect and facing-based actions
        try:
            # default facing east
            self.facing = (1, 0)
        except Exception:
            self.facing = (1, 0)
        
        # Death tracking - capture details of fatal blow for journal
        self.last_attacking_enemy = None  # Name of last enemy that hit player
        self.last_damage_taken = 0  # Amount of damage from last hit
        self.last_attack_type = "attack"  # Type of attack (melee, ranged, etc)

    def equip_disguise(self, disguise):
        """
        Equip a disguise item (instance of Disguise or string key for DISGUISE_TYPES).
        Updates detection and suspicion accordingly.
        """
        from jedi_fugitive.items.disguises import DISGUISE_TYPES, Disguise
        if isinstance(disguise, str):
            disguise_obj = DISGUISE_TYPES.get(disguise)
        elif isinstance(disguise, Disguise):
            disguise_obj = disguise
        else:
            disguise_obj = None
        if disguise_obj:
            self.disguise = disguise_obj.name
            # Lower detection and suspicion when equipping a disguise
            self.detection_level = max(0, self.detection_level - disguise_obj.detection_bonus)
            self.suspicion = max(0, self.suspicion - 10)
        else:
            self.disguise = None

    @property
    def corruption(self):
        """Alias for dark_corruption to maintain compatibility."""
        return self.dark_corruption
    
    @corruption.setter
    def corruption(self, value):
        """Setter for corruption property."""
        self.dark_corruption = value

    @property
    def hp(self):
        """HP property that allows getting the current HP value."""
        return self._hp
    
    @hp.setter
    def hp(self, value):
        """HP setter that marks stats cache dirty when HP changes."""
        self._hp = value
        self._stats_cache_dirty = True

    def initialize_force_abilities(self):
        # keep compatibility but do not automatically grant all abilities
        if not self.force_abilities:
            self.force_abilities = {}
        # keep method for compatibility with callers
        return

    def push_effect(self, user, target, game_map, messages, player_rank=1):
        """Push effect: damage and move enemy."""
        if target:
            damage = 10 + player_rank * 2
            target.hp -= damage
            messages.add(f"Force push deals {damage} damage to {target.name}!")
            # Move enemy away (simple implementation)
            dx = target.x - self.x
            dy = target.y - self.y
            new_x = target.x + dx
            new_y = target.y + dy
            if (0 <= new_x < len(game_map[0]) and 0 <= new_y < len(game_map) and game_map[new_y][new_x] != '#'):
                target.x = new_x
                target.y = new_y
            return True
        return False

    def heal_effect(self, user, target, game_map, messages, player_rank=1):
        """Heal effect."""
        heal_amount = 20 + player_rank * 5
        self.hp = min(self.max_hp, self.hp + heal_amount)
        messages.add(f"You heal for {heal_amount} HP!")
        return True

    def lightning_effect(self, user, target, game_map, messages, player_rank=1):
        """Lightning effect."""
        if target:
            damage = 15 + player_rank * 3
            target.hp -= damage
            messages.add(f"Lightning strikes {target.name} for {damage} damage!")
            return True
        return False

    def get_available_abilities(self):
        """Return unlocked abilities as a list.

        Compatible with older code that used a dict for force_abilities.
        """
        if not self.force_abilities:
            return []
        # If force_abilities is a dict (old code), return its values; else return the list
        if hasattr(self.force_abilities, "values"):
            abilities = list(self.force_abilities.values())
        else:
            abilities = list(self.force_abilities)
        # Only return abilities that are explicitly unlocked
        return [a for a in abilities if hasattr(a, 'is_unlocked') and a.is_unlocked()]

    def xp_to_next_level(self, level: int = None) -> int:
        """Return XP required for next level (exponential-ish)."""
        if level is None:
            level = getattr(self, "level", 1)
        # base 100, grows ~1.25^level
        return int(100 * (1.25 ** (level - 1)))

    def gain_xp(self, amount: int) -> bool:
        """Add XP; return True if player leveled up."""
        self.xp = getattr(self, "xp", 0) + int(amount)
        leveled = False
        while self.xp >= self.xp_to_next_level(self.level):
            self.xp -= self.xp_to_next_level(self.level)
            self.level_up()
            leveled = True
        return leveled

    def gain_craft_xp(self, amount: int) -> str:
        """Gain crafting experience and level up if needed. Returns level up message or None."""
        self.craft_xp = getattr(self, 'craft_xp', 0) + amount
        
        while self.craft_xp >= self.craft_xp_to_next:
            self.craft_xp -= self.craft_xp_to_next
            self.craft_level = getattr(self, 'craft_level', 1) + 1
            self.craft_xp_to_next = int(self.craft_xp_to_next * 1.5)  # Progressively harder
            return f"Crafting level increased to {self.craft_level}!"
        
        return None
    
    def can_craft_recipe(self, recipe: dict) -> bool:
        """Check if player can craft this recipe based on skill level."""
        required_level = recipe.get('required_level', 1)
        current_level = getattr(self, 'craft_level', 1)
        return current_level >= required_level

    def _invalidate_stats_cache(self):
        """Mark stats cache as dirty (call when stats change)."""
        self._stats_cache_dirty = True
        self._cached_stats = None

    def level_up(self):
        """Apply level up bonuses (non-destructive)."""
        # Sync player.level with the higher of the two paths (don't double-increment)
        light_level = getattr(self, 'light_level', 1)
        dark_level = getattr(self, 'dark_level', 1)
        old_level = getattr(self, 'level', 1)
        self.level = max(old_level, light_level, dark_level)
        # Invalidate stats cache when leveling up
        self._invalidate_stats_cache()
        
        # REDUCED AUTOMATIC GAINS - choices matter more now
        # IMPORTANT: Update base stats FIRST before adding level bonuses
        if hasattr(self, '_base_stats') and self._base_stats:
            self._base_stats['attack'] = self._base_stats.get('attack', 1) + 1
            self._base_stats['defense'] = self._base_stats.get('defense', 0) + 1
            self._base_stats['max_hp'] = self._base_stats.get('max_hp', 10) + 3  # Reduced from +5
        
        # Reduced automatic stat gains (choices are now more impactful)
        self.max_hp = self.max_hp + 3  # Reduced from +5
        self.hp = min(self.hp, self.max_hp)
        self.attack = self.attack + 1
        self.defense = self.defense + 1
        # Evasion no longer automatic - must choose it
        
        # Skill point for the Jedi skill trees
        try:
            from jedi_fugitive.game import jedi_skills
            _sp_msg = jedi_skills.on_level_up(self)
            if getattr(self, 'ui', None) and getattr(self.ui, 'messages', None):
                self.ui.messages.add(_sp_msg)
        except Exception:
            pass

        # Grant 2 Force Points per level (changed from 1 every 2 levels)
        self.force_points = getattr(self, "force_points", 0) + 2
        try:
            if getattr(self, 'ui', None) and getattr(self.ui, 'messages', None):
                self.ui.messages.add(f"Force connection strengthens! +2 Force Points")
        except Exception:
            pass
        
        # Reduce stress on level up (reduced from 30 to 20)
        try:
            current_stress = getattr(self, 'stress', 0)
            self.stress = max(0, current_stress - 20)  # Reduced from 30
            if getattr(self, 'ui', None) and getattr(self.ui, 'messages', None):
                if current_stress > 0:
                    self.ui.messages.add(f"Level up relieves stress! ({current_stress} → {self.stress})")
                else:
                    self.ui.messages.add("You feel renewed as you level up.")
        except Exception:
            pass
        # Inform UI if present and present a leveled-up chooser (stats or ability)
        try:
            # Get UI and game references from self or passed context
            ui = getattr(self, 'ui', None)
            game = getattr(self, 'game', None)
            
            # Critical fix: If no UI reference, try to get from game
            if not ui and game:
                ui = getattr(game, 'ui', None)
            
            title = f"Level {self.level} - Choose reward"
            
            # Build options list - IMPROVED with forms and ranked masteries
            options = [
                "+10 Max HP",                          # 0 - Increased from +5
                "+2 Attack",                           # 1 - Increased from +1
                "+2 Defense",                          # 2 - New option
                "+3 Evasion",                          # 3 - Increased from +1
                "+3 Force Points",                     # 4 - Increased from +2
                "Learn Lightsaber Form",               # 5 - NEW: Combat stances
                "Improve Mastery (Melee/Ranged/Shield/Force)",  # 6 - NEW: Ranked system
                "Learn Force Ability"                  # 7
            ]

            sel = None
            try:
                if ui and hasattr(ui, 'centered_menu') and callable(ui.centered_menu):
                    sel = ui.centered_menu(options, title=title)
                else:
                    # Debug: UI or centered_menu not available
                    if ui:
                        try:
                            ui.messages.add(f"DEBUG: UI found but centered_menu not available")
                        except (AttributeError, TypeError):
                            pass
            except Exception as e:
                # Debug: Menu failed
                try:
                    if ui and hasattr(ui, 'messages'):
                        ui.messages.add(f"Level up menu error: {e}")
                except (AttributeError, TypeError):
                    pass
                sel = None

            # headless or cancelled: default to first option (+10 Max HP)
            if sel is None:
                try:
                    if getattr(self, 'ui', None) and getattr(self.ui, 'messages', None):
                        self.ui.messages.add(f"═══════════════════════════════════")
                        self.ui.messages.add(f"★ ★ ★ LEVEL UP! ★ ★ ★ Level {self.level}")
                        self.ui.messages.add(f"═══════════════════════════════════")
                        self.ui.messages.add(f"+10 Max HP applied by default")
                    
                    # Add immersive journal entry for level up
                    try:
                        from jedi_fugitive.game.journal_entries import get_level_up_entry
                        player_alignment = self.get_alignment() if hasattr(self, 'get_alignment') else 'balanced'
                        entry = get_level_up_entry(self.level, player_alignment)
                        self.add_log_entry(entry, getattr(self, 'turn_count', 0))
                    except Exception:
                        pass
                except Exception:
                    pass
                # Update base stats first
                if hasattr(self, '_base_stats') and self._base_stats:
                    self._base_stats['max_hp'] = self._base_stats.get('max_hp', 10) + 10
                # Then apply default
                self.max_hp += 10
                self.hp = min(self.max_hp, getattr(self, 'hp', self.max_hp))
            else:
                try:
                    if sel == 0:
                        # +10 Max HP (increased from +5)
                        if hasattr(self, '_base_stats') and self._base_stats:
                            self._base_stats['max_hp'] = self._base_stats.get('max_hp', 10) + 10
                        self.max_hp += 10
                        self.hp = min(self.max_hp, getattr(self, 'hp', self.max_hp))
                        ui.messages.add("Max HP increased by 10.")
                    elif sel == 1:
                        # +2 Attack (increased from +1)
                        if hasattr(self, '_base_stats') and self._base_stats:
                            self._base_stats['attack'] = self._base_stats.get('attack', 1) + 2
                        self.attack += 2
                        ui.messages.add("Attack increased by 2.")
                    elif sel == 2:
                        # +2 Defense (new option)
                        if hasattr(self, '_base_stats') and self._base_stats:
                            self._base_stats['defense'] = self._base_stats.get('defense', 0) + 2
                        self.defense += 2
                        ui.messages.add("Defense increased by 2.")
                    elif sel == 3:
                        # +3 Evasion (increased from +1)
                        if hasattr(self, '_base_stats') and self._base_stats:
                            self._base_stats['evasion'] = self._base_stats.get('evasion', 0) + 3
                        self.evasion += 3
                        ui.messages.add("Evasion increased by 3.")
                    elif sel == 4:
                        # +3 Force Points (increased from +2)
                        self.force_points += 3
                        ui.messages.add(f"Force Points increased by 3! (Total: {self.force_points})")
                    elif sel == 5:
                        # Learn Lightsaber Form
                        available_forms = get_available_forms(self)
                        if not available_forms:
                            ui.messages.add("No new Lightsaber Forms available at your level.")
                        else:
                            form_names = [f.name for f in available_forms]
                            form_choice = ui.centered_menu(form_names, title="Learn Lightsaber Form")
                            if form_choice is not None and 0 <= form_choice < len(available_forms):
                                chosen_form = available_forms[form_choice]
                                self.known_forms.append(chosen_form.name)
                                self.active_form = chosen_form.name
                                
                                # Apply form bonuses immediately (pass self as player object)
                                bonuses = get_form_bonuses(self)
                                if bonuses['attack'] > 0:
                                    self.attack = self.attack + bonuses['attack']
                                if bonuses['defense'] > 0:
                                    self.defense = self.defense + bonuses['defense']
                                if bonuses['evasion'] > 0:
                                    self.evasion = self.evasion + bonuses['evasion']
                                    
                                ui.messages.add(f"═══ FORM {chosen_form.number}: {chosen_form.name.upper()} ═══")
                                ui.messages.add(f"Learned and activated {chosen_form.name}!")
                                ui.messages.add(f"Focus: {chosen_form.focus}")
                                # Show bonuses
                                if chosen_form.attack_bonus:
                                    ui.messages.add(f"  +{chosen_form.attack_bonus} Attack (Applied!)")
                                if chosen_form.defense_bonus:
                                    ui.messages.add(f"  +{chosen_form.defense_bonus} Defense (Applied!)")
                                if chosen_form.evasion_bonus:
                                    ui.messages.add(f"  +{chosen_form.evasion_bonus} Evasion (Applied!)")
                    elif sel == 6:
                        # Improve Mastery (Ranked system)
                        mastery_options = []
                        if self.melee_mastery < 3:
                            rank_text = ["I", "II", "III"][self.melee_mastery]
                            mastery_options.append(f"Melee Mastery Rank {rank_text}")
                        if self.ranged_mastery < 3:
                            rank_text = ["I", "II", "III"][self.ranged_mastery]
                            mastery_options.append(f"Ranged Mastery Rank {rank_text}")
                        if self.shield_mastery < 3:
                            rank_text = ["I", "II", "III"][self.shield_mastery]
                            mastery_options.append(f"Shield Mastery Rank {rank_text}")
                        if self.force_mastery < 3:
                            rank_text = ["I", "II", "III"][self.force_mastery]
                            mastery_options.append(f"Force Mastery Rank {rank_text}")
                        
                        if not mastery_options:
                            ui.messages.add("All masteries are at maximum rank!")
                        else:
                            mastery_choice = ui.centered_menu(mastery_options, title="Improve Mastery")
                            if mastery_choice is not None and 0 <= mastery_choice < len(mastery_options):
                                chosen = mastery_options[mastery_choice]
                                if "Melee" in chosen:
                                    self.melee_mastery += 1
                                    ui.messages.add(f"Melee Mastery Rank {self.melee_mastery} acquired!")
                                elif "Ranged" in chosen:
                                    self.ranged_mastery += 1
                                    ui.messages.add(f"Ranged Mastery Rank {self.ranged_mastery} acquired!")
                                elif "Shield" in chosen:
                                    self.shield_mastery += 1
                                    ui.messages.add(f"Shield Mastery Rank {self.shield_mastery} acquired!")
                                elif "Force" in chosen:
                                    self.force_mastery += 1
                                    ui.messages.add(f"Force Mastery Rank {self.force_mastery} acquired!")
                    elif sel == 7:
                        # choose new force ability if available
                        # Filter: 1) exclude already learned, 2) exclude Meditation (mapped to 'm' key), 3) filter by alignment
                        corruption = getattr(self, 'dark_corruption', 0)
                        
                        # Determine alignment: Light Side (<40 corruption), Dark Side (>60 corruption), Neutral (40-60)
                        avail = []
                        for a in (FORCE_ABILITIES or []):
                            name = getattr(a, 'name', None)
                            if not name or name in self.force_abilities:
                                continue
                            
                            # Exclude Meditation - it's always available via 'm' key
                            if name == "Meditation":
                                continue
                            
                            # Filter by alignment
                            alignment = getattr(a, 'alignment', 'neutral')
                            if corruption < 40:  # Light Side path
                                if alignment == 'dark':
                                    continue  # Don't show Dark abilities
                            elif corruption > 60:  # Dark Side path
                                if alignment == 'light':
                                    continue  # Don't show Light abilities
                            # Neutral range (40-60) shows everything
                            
                            avail.append(a)
                        
                        if not avail:
                            ui.messages.add("No new Force abilities available.")
                        else:
                            names = [getattr(a, 'name', str(type(a))) for a in avail]
                            choose = ui.centered_menu(names, title="Learn Force Ability")
                            if choose is not None and 0 <= choose < len(avail):
                                a = avail[choose]
                                # Create a copy and unlock it for the player
                                import copy
                                player_ability = copy.deepcopy(a)
                                player_ability.unlocked = True
                                self.force_abilities[getattr(player_ability, 'name', str(type(player_ability)))] = player_ability
                                ui.messages.add(f"Learned ability: {getattr(player_ability,'name','ability')}")
                except Exception:
                    try: ui.messages.add(f"Leveled up to {self.level}!")
                    except Exception: pass
        except Exception:
            try:
                if getattr(self, 'ui', None) and getattr(self.ui, 'messages', None):
                    self.ui.messages.add(f"Leveled up to {self.level}!")
            except Exception:
                pass

    def get_stats_display(self) -> List[str]:
        """Return a list of lines describing player effective stats for the stats panel (CACHED)."""
        # Use cached stats if available and not dirty
        if not self._stats_cache_dirty and self._cached_stats is not None:
            return self._cached_stats
        
        lines = []
        # Single unified level progression display
        light_lvl = getattr(self, 'light_level', 1)
        dark_lvl = getattr(self, 'dark_level', 1)
        light_xp = getattr(self, 'light_xp', 0)
        dark_xp = getattr(self, 'dark_xp', 0)
        light_next = getattr(self, 'xp_to_next_light', 100)
        dark_next = getattr(self, 'xp_to_next_dark', 100)
        corruption = getattr(self, 'dark_corruption', 0)  # Use dark_corruption for accurate value
        
        # Use the synchronized level (which is max of all level values)
        current_level = getattr(self, 'level', 1)
        
        # Display the dominant path's XP progress
        if dark_lvl >= light_lvl:
            lines.append(f"Level: {current_level} ({dark_xp}/{dark_next} XP)")
        else:
            lines.append(f"Level: {current_level} ({light_xp}/{light_next} XP)")
        lines.append(f"Corruption: {corruption}%")
        
        # HP bar with visual hearts/blocks
        hp_cur = getattr(self, 'hp', 0)
        hp_max = getattr(self, 'max_hp', 0)
        if hp_max > 0:
            # Visual HP bar with blocks
            bar_width = min(20, hp_max // 5)  # Scale bar size
            filled = int((hp_cur / hp_max) * bar_width) if hp_max > 0 else 0
            hp_bar = '█' * filled + '░' * (bar_width - filled)
            lines.append(f"HP: {hp_bar} {hp_cur}/{hp_max}")
        else:
            lines.append(f"HP: {hp_cur}/{hp_max}")
        
        # show both base and effective (with equipment)
        # Get true base from _base_stats if available, otherwise use current attack
        base_stats = getattr(self, '_base_stats', {})
        if base_stats and 'attack' in base_stats:
            base_attack = base_stats['attack']
        else:
            base_attack = getattr(self, 'attack', 0)
        
        current_attack = getattr(self, 'attack', 0)
        weapon_bonus = current_attack - base_attack
        
        if weapon_bonus > 0:
            lines.append(f"Attack: {base_attack} (+{weapon_bonus} weapon) = {current_attack}")
        else:
            lines.append(f"Attack: {current_attack}")
        
        # Show defense with breakdown
        base_defense = getattr(self, 'defense', 0)
        effective_def = getattr(self, "get_effective_defense", lambda: getattr(self, "defense", 0))()
        defense_bonus = effective_def - base_defense
        if defense_bonus > 0:
            lines.append(f"Defense: {base_defense} (+{defense_bonus} equipment) = {effective_def}")
        else:
            lines.append(f"Defense: {effective_def}")
        
        effective_acc = getattr(self, "get_effective_accuracy", lambda: getattr(self, "accuracy", 0))()
        lines.append(f"Accuracy: {getattr(self,'accuracy',0)} -> {effective_acc}")
        # show stress as a stat line
        try:
            lines.append(f"Stress: {getattr(self,'stress',0)}/{getattr(self,'max_stress',100)}")
        except Exception:
            pass
        lines.append(f"Evasion: {getattr(self,'evasion',0)}")
        lines.append(f"Force: {getattr(self,'force_points',0)}")
        lines.append(f"Gold: {getattr(self,'gold_collected',0)}")
        
        # --- New System UI ---
        # Detection/Pursuit
        detection = getattr(self, 'detection_level', 0)
        lines.append(f"Detection: {detection}/100")
        # Disguise
        disguise = getattr(self, 'disguise', None)
        lines.append(f"Disguise: {disguise if disguise else 'None'}")
        # Suspicion
        suspicion = getattr(self, 'suspicion', 0)
        lines.append(f"Suspicion: {suspicion}/100")
        # Faction Reputation
        rep = getattr(self, 'faction_reputation', {})
        if rep:
            lines.append("Faction Reputation:")
            for fname, val in rep.items():
                lines.append(f"  {fname}: {val}")

        # Show masteries if any > 0
        melee_m = getattr(self, 'melee_mastery', 0)
        ranged_m = getattr(self, 'ranged_mastery', 0)
        shield_m = getattr(self, 'shield_mastery', 0)
        dual_m = getattr(self, 'dual_wield_mastery', 0)
        if any([melee_m, ranged_m, shield_m, dual_m]):
            lines.append("")  # Blank line
            lines.append("Masteries:")
            if melee_m > 0:
                lines.append(f"  Melee: +{melee_m} dmg")
            if ranged_m > 0:
                lines.append(f"  Ranged: +{ranged_m} dmg")
            if shield_m > 0:
                lines.append(f"  Shield: +{shield_m} def")
            if dual_m > 0:
                lines.append(f"  Dual Wield: +{dual_m} dmg/weapon")
        
        # Show Force abilities
        force_abilities = getattr(self, 'force_abilities', {})
        if force_abilities:
            lines.append("")  # Blank line for separation
            lines.append("Force Abilities:")
            for ability_name in sorted(force_abilities.keys()):
                lines.append(f"  • {ability_name}")
        
        # equipped items
        w = getattr(self, "equipped_weapon", None)
        a = getattr(self, "equipped_armor", None)
        o = getattr(self, "equipped_offhand", None)
        
        def _fmt_item(it):
            try:
                if it is None:
                    return 'None'
                if isinstance(it, str):
                    # common token mapping fallback
                    token_map = {'v': 'Vibroblade', 's': 'Energy Shield', 'b': 'Blaster Pistol'}
                    return token_map.get(it, it)
                if isinstance(it, dict):
                    return it.get('name', str(it))
                return getattr(it, 'name', str(it))
            except Exception:
                try: return str(it)
                except Exception: return 'Unknown'
        
        def _get_hand_req(it):
            """Get hand requirement display."""
            try:
                from jedi_fugitive.items.weapons import HandRequirement
                if hasattr(it, 'hands'):
                    return f" [{it.hands.value}]"
            except Exception:
                pass
            return ""

        lines.append("")  # Blank line for separation
        lines.append("=== EQUIPMENT ===")
        lines.append(f"Main Hand: {_fmt_item(w)}{_get_hand_req(w)}")
        lines.append(f"Off Hand:  {_fmt_item(o)}{_get_hand_req(o)}")
        lines.append(f"Armor:     {_fmt_item(a)}")
        
        # Cache the result and mark as clean
        self._cached_stats = lines
        self._stats_cache_dirty = False
        return lines

    def get_effective_attack(self) -> int:
        """Return player's effective attack including equipped weapon modifiers."""
        base = int(getattr(self, "attack", 0) or 0)
        w = getattr(self, "equipped_weapon", None)
        if not w:
            return base
        weapon_damage = 0
        # object-like weapon
        try:
            if not isinstance(w, dict):
                weapon_damage = int(getattr(w, "base_damage", getattr(w, "damage", 0) or 0))
            else:
                # dict-backed weapon: prefer explicit keys
                if "base_damage" in w:
                    weapon_damage = int(w.get("base_damage", 0) or 0)
                elif "damage" in w:
                    weapon_damage = int(w.get("damage", 0) or 0)
                elif "attack" in w:
                    # some token entries may expose an 'attack' modifier
                    weapon_damage = int(w.get("attack", 0) or 0)
        except Exception:
            weapon_damage = 0
        return base + int(weapon_damage)

    def get_effective_defense(self) -> int:
        """Return player's effective defense including equipped armor and shield modifiers."""
        base = int(getattr(self, "defense", 0) or 0)
        
        # Add armor defense
        a = getattr(self, "equipped_armor", None)
        arm_def = 0
        if a:
            try:
                if not isinstance(a, dict):
                    arm_def = int(getattr(a, "defense", 0) or 0)
                else:
                    if "defense" in a:
                        arm_def = int(a.get("defense", 0) or 0)
                    elif "max_hp" in a and not isinstance(a.get("max_hp"), bool):
                        # some armors provide HP rather than defense; do not double-count
                        arm_def = 0
            except Exception:
                arm_def = 0
        
        # Add shield defense from equipped_offhand
        offhand = getattr(self, "equipped_offhand", None)
        shield_def = 0
        if offhand:
            try:
                # Check if it's a shield
                is_shield = False
                if hasattr(offhand, 'is_shield') and offhand.is_shield:
                    is_shield = True
                elif hasattr(offhand, 'type') and offhand.type == 'shield':
                    is_shield = True
                elif hasattr(offhand, 'slot') and offhand.slot == 'offhand':
                    is_shield = True
                elif isinstance(offhand, dict) and offhand.get('type') == 'shield':
                    is_shield = True
                
                if is_shield:
                    if not isinstance(offhand, dict):
                        shield_def = int(getattr(offhand, "defense_bonus", 0) or 0)
                    else:
                        shield_def = int(offhand.get("defense_bonus", 0) or 0)
            except Exception:
                shield_def = 0
        
        total_def = base + int(arm_def) + int(shield_def)
        return total_def

    def get_max_inventory(self) -> int:
        """Calculate maximum inventory size including armor capacity bonuses."""
        base_capacity = MAX_INVENTORY_SIZE
        armor_bonus = 0
        
        # Check equipped armor for capacity bonus
        armor = getattr(self, 'equipped_armor', None)
        if armor is not None:
            try:
                armor_bonus = int(getattr(armor, 'capacity_bonus', 0))
            except (ValueError, TypeError):
                armor_bonus = 0
        
        return base_capacity + armor_bonus
    
    def add_stress(self, amount: int, source: str = None):
        """Increase stress with clamping and advanced resilience modifiers."""
        try:
            amt = int(amount)
            old_stress = getattr(self, 'stress', 0)
            
            # Base resilience reduces incoming stress by percent per level
            lvl = max(1, getattr(self, 'level', 1))
            base_reduction = max(0.0, self._stress_resilience_per_level * (lvl - 1))
            
            # Confidence bonus: reduces stress further based on combat success
            confidence_bonus = min(0.20, getattr(self, '_successful_combats', 0) * 0.02)  # Up to 20% from victories
            
            # Mastery bonus: Force and shield mastery reduce mental stress
            mastery_bonus = 0.0
            force_mastery = getattr(self, 'force_mastery', 0)
            shield_mastery = getattr(self, 'shield_mastery', 0)
            mastery_bonus = min(0.15, (force_mastery + shield_mastery) * 0.025)  # Up to 15% from masteries
            
            # Total reduction (capped at 60% max reduction)
            try:
                from jedi_fugitive.game import jedi_skills
                mastery_bonus += 1.0 - jedi_skills.stress_multiplier(self)
            except Exception:
                pass
            total_reduction = min(0.60, base_reduction + confidence_bonus + mastery_bonus)
            effective = int(max(0, amt * (1.0 - total_reduction)))
            # equipment-based mitigations (armor/weapon may reduce stress gains)
            try:
                mitigation = 0.0
                armor = getattr(self, 'equipped_armor', None)
                weapon = getattr(self, 'equipped_weapon', None)
                # armor-provided mitigation via explicit attribute or heuristics
                if armor is not None:
                    try:
                        if hasattr(armor, 'stress_resistance'):
                            mitigation += float(getattr(armor, 'stress_resistance', 0.0))
                        else:
                            aname = getattr(armor, 'name', '') or str(armor)
                            an = aname.lower()
                            if 'robe' in an or 'cloth' in an or 'robe' in an:
                                mitigation += 0.30
                            elif 'vest' in an:
                                mitigation += 0.10
                    except Exception:
                        pass
                # weapon-based mitigation (e.g., kyber crystal or focusing relic)
                if weapon is not None:
                    try:
                        if hasattr(weapon, 'stress_resistance'):
                            mitigation += float(getattr(weapon, 'stress_resistance', 0.0))
                        else:
                            wname = getattr(weapon, 'name', '') or str(weapon)
                            wn = wname.lower()
                            if 'kyber' in wn or 'focus' in wn:
                                mitigation += 0.15
                    except Exception:
                        pass
                # clamp mitigation to sensible maximum (60%)
                mitigation = max(0.0, min(0.6, float(mitigation)))
                if mitigation > 0.0:
                    effective = int(max(0, effective * (1.0 - mitigation)))
            except Exception:
                pass
            self.stress = getattr(self, 'stress', 0) + effective
            # clamp to at least 0
            if self.stress < 0:
                self.stress = 0
            
            # Update max stress with level progression
            base_max_stress = 100
            self.max_stress = base_max_stress + (self._stress_max_increase_per_level * (lvl - 1))
            
            # Track stress threshold crossings for warnings (scaled to max stress)
            new_stress = self.stress
            threshold_75 = int(self.max_stress * 0.75)
            threshold_85 = int(self.max_stress * 0.85)
            threshold_95 = int(self.max_stress * 0.95)
            
            if old_stress < threshold_75 and new_stress >= threshold_75:
                self._stress_warning_75 = True
            if old_stress < threshold_85 and new_stress >= threshold_85:
                self._stress_warning_85 = True
            if old_stress < threshold_95 and new_stress >= threshold_95:
                self._stress_warning_95 = True
            
            # cap not enforced here (breaking point handled elsewhere)
            return effective
        except Exception:
            return 0

    def reduce_stress(self, amount: int, source: str = None):
        """Reduce stress and track for confidence building."""
        try:
            amt = int(amount)
            old_stress = getattr(self, 'stress', 0)
            self.stress = max(0, old_stress - amt)
            
            # Track stress reductions for confidence building
            if source in ['meditation', 'victory', 'rest']:
                self._stress_reduction_this_level = getattr(self, '_stress_reduction_this_level', 0) + amt
            
            return True
        except Exception:
            return False

    def get_stress_level(self) -> int:
        """Return stress tier: 0 (none), 1..4 mapping to design breakpoints, scaled to max stress."""
        s = getattr(self, 'stress', 0)
        max_s = getattr(self, 'max_stress', 100)
        
        # Calculate percentage thresholds
        if s <= (max_s * 0.30):
            return 1
        if s <= (max_s * 0.60):
            return 2
        if s <= (max_s * 0.85):
            return 3
        return 4
    
    def get_stress_description(self) -> tuple:
        """Return (description, color_code) for current stress level scaled to max."""
        s = getattr(self, 'stress', 0)
        max_s = getattr(self, 'max_stress', 100)
        
        if s <= (max_s * 0.30):
            return ("Calm", 2)  # Green
        elif s <= (max_s * 0.60):
            return ("Focused", 3)  # Yellow
        elif s <= (max_s * 0.85):
            return ("Stressed", 3)  # Yellow
        elif s < max_s:
            return ("CRITICAL", 1)  # Red
        else:
            return ("BREAKING", 1)  # Red, flashing

    def get_effective_accuracy(self) -> int:
        """Apply stress-based accuracy penalties with improved scaling and mitigation."""
        base = int(getattr(self, 'accuracy', 0))
        stress_tier = self.get_stress_level()
        
        # Reduced penalties - stress affects accuracy less at higher levels
        penalty_pct = 0.0
        if stress_tier == 1:
            penalty_pct = 0.05  # Reduced from 0.10
        elif stress_tier == 2:
            penalty_pct = 0.10  # Reduced from 0.15
        elif stress_tier == 3:
            penalty_pct = 0.20  # Reduced from 0.25
        elif stress_tier == 4:
            penalty_pct = 0.30  # Reduced from 0.40
        
        # Progressive mitigation: higher level = less penalty impact
        player_level = max(1, getattr(self, 'level', 1))
        level_mitigation = min(0.50, player_level * 0.04)  # Up to 50% mitigation at level 12+
        
        effective_penalty = penalty_pct * (1.0 - level_mitigation)
        final = int(max(0, base * (1.0 - effective_penalty)))
        return final

    def gain_force_insight(self, source_id: str = None, amount: int = 1):
        """Grant the player a small permanent/temporary force insight.

        This increases available force points (small) and records the insight id so it
        isn't double-counted by other systems. Designed to be safe when called from
        GameManager or equipment handlers.
        """
        try:
            if not hasattr(self, 'force_insights') or self.force_insights is None:
                self.force_insights = set()
            # don't double-apply the same insight id
            if source_id and source_id in self.force_insights:
                return False
            if source_id:
                try: self.force_insights.add(source_id)
                except Exception: pass
            # grant force points (small amount)
            try:
                add = int(amount)
            except Exception:
                add = 1
            self.force_points = getattr(self, 'force_points', 0) + add
            return True
        except Exception:
            return False

    def get_force_cost_multiplier(self) -> float:
        """Return multiplier for force ability costs based on stress tier."""
        s = getattr(self, 'stress', 0)
        if s <= 30:
            return 1.05
        if s <= 60:
            return 1.10
        if s <= 85:
            return 1.20
        return 1.35

    def equip_weapon(self, weapon):
        """Equip a weapon object (remove from inventory if present)."""
        try:
            # remove from inventory if present
            if weapon in getattr(self, "inventory", []):
                self.inventory.remove(weapon)
        except Exception:
            pass
        self.equipped_weapon = weapon

    def unequip_weapon(self):
        """Unequip current weapon and return it to inventory. Returns the item or None."""
        w = getattr(self, "equipped_weapon", None)
        if not w:
            return None
        # Return unequipped item to inventory; if inventory full, eject oldest inventory item to ground
        try:
            max_inv = int(getattr(self, 'max_inventory', MAX_INVENTORY_SIZE) or MAX_INVENTORY_SIZE)
            cur_inv = len(getattr(self, 'inventory', []) or [])
            game = getattr(self, 'game', None)
            if cur_inv < max_inv:
                try:
                    self.inventory.append(w)
                    if getattr(self, 'ui', None) and getattr(self.ui, 'messages', None):
                        self.ui.messages.add(f"Returned {getattr(w,'name', str(w))} to inventory.")
                except Exception:
                    try: self.inventory.append(w)
                    except Exception: pass
            else:
                # inventory is full: eject oldest item to the ground if possible
                try:
                    if len(self.inventory) > 0:
                        oldest = None
                        try:
                            oldest = self.inventory.pop(0)
                        except Exception:
                            oldest = None
                        name_old = None
                        try:
                            if isinstance(oldest, dict):
                                name_old = oldest.get('name', str(oldest))
                            elif isinstance(oldest, str):
                                name_old = oldest
                            else:
                                name_old = getattr(oldest, 'name', str(oldest))
                        except Exception:
                            name_old = str(oldest)
                        dropped = False
                        if game is not None and hasattr(game, 'items_on_map'):
                            try:
                                drop = {'name': name_old, 'x': int(getattr(self, 'x', 0)), 'y': int(getattr(self, 'y', 0))}
                                game.items_on_map.append(drop)
                                dropped = True
                                try:
                                    if getattr(game, 'ui', None) and getattr(game.ui, 'messages', None):
                                        game.ui.messages.add(f"Inventory full — ejected {name_old} to the ground.")
                                except Exception:
                                    pass
                            except Exception:
                                dropped = False
                        if not dropped:
                            # fallback: if we couldn't place on map, re-add oldest back to end
                            try: self.inventory.append(oldest)
                            except Exception: pass
                except Exception:
                    pass
                # finally, add the unequipped item to inventory (space freed by ejection)
                try:
                    self.inventory.append(w)
                    if getattr(self, 'ui', None) and getattr(self.ui, 'messages', None):
                        self.ui.messages.add(f"Returned {getattr(w,'name', str(w))} to inventory.")
                except Exception:
                    try: self.inventory.append(w)
                    except Exception: pass
        except Exception:
            try: self.inventory.append(w)
            except Exception: pass
        self.equipped_weapon = None
        return w

    def equip_armor(self, armor):
        """Equip armor object (remove from inventory if present)."""
        try:
            if armor in getattr(self, "inventory", []):
                self.inventory.remove(armor)
        except Exception:
            pass
        self.equipped_armor = armor

    def unequip_armor(self):
        """Unequip current armor and return it to inventory. Returns the item or None."""
        a = getattr(self, "equipped_armor", None)
        if not a:
            return None
        try:
            max_inv = int(getattr(self, 'max_inventory', MAX_INVENTORY_SIZE) or MAX_INVENTORY_SIZE)
            cur_inv = len(getattr(self, 'inventory', []) or [])
            game = getattr(self, 'game', None)
            if cur_inv < max_inv:
                try:
                    self.inventory.append(a)
                    if getattr(self, 'ui', None) and getattr(self.ui, 'messages', None):
                        self.ui.messages.add(f"Returned {getattr(a,'name', str(a))} to inventory.")
                except Exception:
                    try: self.inventory.append(a)
                    except Exception: pass
            else:
                # eject oldest inventory item to ground to make space
                try:
                    if len(self.inventory) > 0:
                        try:
                            oldest = self.inventory.pop(0)
                        except Exception:
                            oldest = None
                        name_old = None
                        try:
                            if isinstance(oldest, dict):
                                name_old = oldest.get('name', str(oldest))
                            elif isinstance(oldest, str):
                                name_old = oldest
                            else:
                                name_old = getattr(oldest, 'name', str(oldest))
                        except Exception:
                            name_old = str(oldest)
                        dropped = False
                        if game is not None and hasattr(game, 'items_on_map'):
                            try:
                                drop = {'name': name_old, 'x': int(getattr(self, 'x', 0)), 'y': int(getattr(self, 'y', 0))}
                                game.items_on_map.append(drop)
                                dropped = True
                                try:
                                    if getattr(game, 'ui', None) and getattr(game.ui, 'messages', None):
                                        game.ui.messages.add(f"Inventory full — ejected {name_old} to the ground.")
                                except Exception:
                                    pass
                            except Exception:
                                dropped = False
                        if not dropped:
                            try: self.inventory.append(oldest)
                            except Exception: pass
                except Exception:
                    pass
                try:
                    self.inventory.append(a)
                    if getattr(self, 'ui', None) and getattr(self.ui, 'messages', None):
                        self.ui.messages.add(f"Returned {getattr(a,'name', str(a))} to inventory.")
                except Exception:
                    try: self.inventory.append(a)
                    except Exception: pass
        except Exception:
            try: self.inventory.append(a)
            except Exception: pass
        self.equipped_armor = None
        return a

    def get_alignment(self):
        """Return the player's current alignment with 5-tier system.
        
        Returns:
            'pure_dark' (80-100): Sith Lord
            'dark' (60-79): Fallen Jedi / Dark Side
            'balanced' (41-59): Gray Jedi
            'light' (21-40): Jedi Guardian / Light Side
            'pure_light' (0-20): Jedi Master
        """
        corruption = getattr(self, 'dark_corruption', 50)
        if corruption >= 80:
            return 'pure_dark'
        elif corruption >= 60:
            return 'dark'
        elif corruption >= 41:
            return 'balanced'
        elif corruption >= 21:
            return 'light'
        else:
            return 'pure_light'

    def narrative_text(self, light_version, dark_version, balanced_version=None):
        """Return narrative text based on player's alignment.
        
        Args:
            light_version: Text for Light Side aligned players (compassionate, restrained)
            dark_version: Text for Dark Side aligned players (aggressive, ruthless)
            balanced_version: Optional text for balanced players (defaults to light_version)
        """
        alignment = self.get_alignment()
        if alignment in ['pure_dark', 'dark']:
            return dark_version
        elif alignment in ['pure_light', 'light']:
            return light_version
        else:
            return balanced_version if balanced_version else light_version
    
    def get_alignment_name(self):
        """Return human-readable alignment name."""
        alignment = self.get_alignment()
        names = {
            'pure_light': 'Jedi Master',
            'light': 'Jedi Guardian',
            'balanced': 'Gray Jedi',
            'dark': 'Fallen Jedi',
            'pure_dark': 'Sith Lord'
        }
        return names.get(alignment, 'Unknown')

    def regenerate_force(self, in_combat=False, game=None):
        """Regenerate Force energy per turn.
        
        Args:
            in_combat: If True, uses slower combat regeneration rate
            game: Game manager instance for atmospheric effects
        """
        regen_amount = self.force_regen_combat if in_combat else self.force_regen_peaceful
        
        # Apply atmospheric modifiers to Force regeneration
        try:
            if game and hasattr(game, 'atmospheric_modifiers'):
                force_regen_modifier = game.atmospheric_modifiers.get('force_regen', 0)
                regen_amount += force_regen_modifier
                
                # Check for dark side bonuses during atmospheric events
                if hasattr(self, 'dark_corruption') and self.dark_corruption >= 60:
                    dark_side_bonus = game.atmospheric_modifiers.get('dark_side_bonus', 0)
                    regen_amount += dark_side_bonus
        except Exception:
            pass
        
        try:
            from jedi_fugitive.game import jedi_skills
            regen_amount += int(jedi_skills.bonus(self, 'force_regen'))
        except Exception:
            pass
        self.force_energy = min(self.max_force_energy, self.force_energy + regen_amount)
        # Update legacy force_points for compatibility
        self.force_points = max(0, int(self.force_energy / 50))
    
    def get_alignment_mastery(self):
        """Get current alignment mastery level (0-3 based on corruption).
        
        Returns:
            int: Mastery level for current alignment
                - Pure Light/Dark (0-20, 80-100): Level 3
                - Light/Dark (21-40, 60-79): Level 2
                - Balanced (41-59): Level 1
        """
        corruption = getattr(self, 'dark_corruption', 0)
        if corruption <= 20 or corruption >= 80:
            return 3  # Pure Light or Pure Dark mastery
        elif corruption <= 40 or corruption >= 60:
            return 2  # Light or Dark mastery
        else:
            return 1  # Balanced (no mastery bonus)
    
    def get_ability_power_scale(self, ability_alignment):
        """Calculate power scaling for an ability based on player alignment.
        
        Args:
            ability_alignment: 'light', 'dark', or 'neutral'
            
        Returns:
            float: Power multiplier (0.5 to 1.5)
        """
        if ability_alignment == 'neutral':
            return 1.0  # Neutral abilities always at base power
        
        player_alignment = self.get_alignment()
        corruption = getattr(self, 'dark_corruption', 0)
        mastery = self.get_alignment_mastery()
        
        # Light abilities
        if ability_alignment == 'light':
            if player_alignment in ['pure_light', 'light']:
                # Aligned: bonus based on mastery
                return 1.0 + (mastery * 0.15)  # 1.15x to 1.45x
            elif player_alignment in ['pure_dark', 'dark']:
                # Opposing: penalty
                return 0.5
            else:
                # Balanced: base power
                return 1.0
        
        # Dark abilities
        if ability_alignment == 'dark':
            if player_alignment in ['pure_dark', 'dark']:
                # Aligned: bonus based on mastery
                return 1.0 + (mastery * 0.15)  # 1.15x to 1.45x
            elif player_alignment in ['pure_light', 'light']:
                # Opposing: penalty
                return 0.5
            else:
                # Balanced: base power
                return 1.0
        
        return 1.0
    
    def get_ability_cost_multiplier(self, ability_alignment):
        """Calculate Force cost multiplier for an ability.
        
        Args:
            ability_alignment: 'light', 'dark', or 'neutral'
            
        Returns:
            float: Cost multiplier (0.7 to 2.0)
        """
        if ability_alignment == 'neutral':
            return 1.0
        
        player_alignment = self.get_alignment()
        mastery = self.get_alignment_mastery()
        
        # Light abilities
        if ability_alignment == 'light':
            if player_alignment in ['pure_light', 'light']:
                # Aligned: reduced cost based on mastery
                return max(0.7, 1.0 - (mastery * 0.1))  # 0.7x to 0.9x cost
            elif player_alignment in ['pure_dark', 'dark']:
                # Opposing: increased cost
                return 2.0
            else:
                return 1.0
        
        # Dark abilities
        if ability_alignment == 'dark':
            if player_alignment in ['pure_dark', 'dark']:
                # Aligned: reduced cost based on mastery
                return max(0.7, 1.0 - (mastery * 0.1))  # 0.7x to 0.9x cost
            elif player_alignment in ['pure_light', 'light']:
                # Opposing: increased cost
                return 2.0
            else:
                return 1.0
        
        return 1.0

    def add_log_entry(self, entry, turn=None):
        """Add entry to travel log with enhanced hero's journey tracking."""
        try:
            if not hasattr(self, 'travel_log'):
                self.travel_log = []
            
            turn = turn or 0
            
            # Try to use enhanced journal system
            try:
                from jedi_fugitive.game.hero_journal import enhance_existing_journal_system, JournalEntryType
                journal = enhance_existing_journal_system(self)
                
                # Determine entry type based on content
                entry_type = JournalEntryType.REFLECTION
                if 'DEATH' in entry or 'died' in entry.lower():
                    entry_type = JournalEntryType.DEATH
                elif 'VICTORY' in entry or 'victory' in entry.lower():
                    entry_type = JournalEntryType.VICTORY
                elif 'combat' in entry.lower() or 'defeated' in entry.lower() or 'killed' in entry.lower():
                    entry_type = JournalEntryType.COMBAT
                elif 'found' in entry.lower() or 'discovered' in entry.lower() or 'artifact' in entry.lower():
                    entry_type = JournalEntryType.DISCOVERY
                elif 'corruption' in entry.lower() or 'dark side' in entry.lower() or 'light side' in entry.lower():
                    entry_type = JournalEntryType.CORRUPTION
                elif 'FAUNA' in entry or 'encountered' in entry.lower():
                    entry_type = JournalEntryType.FAUNA
                elif 'atmosphere' in entry.lower() or entry.startswith('[Atmosphere]'):
                    entry_type = JournalEntryType.ATMOSPHERE
                
                # Add enhanced entry
                journal.add_enhanced_entry(entry, turn, entry_type)
                
            except ImportError:
                # Fallback to simple log entry
                log_entry = {'text': entry, 'turn': turn}
                self.travel_log.append(log_entry)
            
            # Keep log manageable
            if len(self.travel_log) > 200:
                self.travel_log = self.travel_log[-200:]
                
        except Exception:
            # Ultimate fallback
            if not hasattr(self, 'travel_log'):
                self.travel_log = []
            log_entry = {'text': entry, 'turn': turn}
            self.travel_log.append(log_entry)
    def add_to_travel_log(self, entry, turn=None):
        """Alias used by death/tomb/hunt narration (previously missing, so those entries were lost)."""
        if turn is None:
            try:
                turn = int(getattr(getattr(self, 'game', None), 'turn_count', 0) or 0)
            except Exception:
                turn = 0
        self.add_log_entry(entry, turn)
