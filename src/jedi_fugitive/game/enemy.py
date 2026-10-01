from enum import Enum
import random
import math
from jedi_fugitive.game.personality import ENEMY_TAUNTS, EnemyPersonality
from jedi_fugitive.utils.logger import get_logger
log = get_logger("enemy")


# ============ AI Helper Functions ============

def ai_should_retreat(enemy, game):
    """Determine if enemy should retreat due to low HP."""
    try:
        hp_percent = getattr(enemy, 'hp', 1) / max(1, getattr(enemy, 'max_hp', 1))
        
        # Massive creatures are more aggressive and retreat less often
        if getattr(enemy, 'is_massive', False):
            return hp_percent < 0.1  # Only retreat when almost dead
            
        # Bosses never retreat
        if getattr(enemy, 'is_boss', False):
            return False
            
        # Regular enemies retreat at 30% HP
        if hp_percent < 0.3:
            return True
            
        return False
    except Exception as e:
        if log:
            log.exception("ai_should_retreat error", exc_info=e)
        return False


def ai_find_retreat_direction(enemy, game):
    """Find direction away from player for retreating."""
    try:
        ex, ey = getattr(enemy, 'x', 0), getattr(enemy, 'y', 0)
        px, py = getattr(game.player, 'x', 0), getattr(game.player, 'y', 0)
        # Move away from player
        dx = -1 if px > ex else (1 if px < ex else 0)
        dy = -1 if py > ey else (1 if py < ey else 0)
        # If no diagonal, pick perpendicular random direction
        if dx == 0 and dy == 0:
            dx = random.choice([-1, 1])
        return dx, dy
    except Exception as e:
        if log:
            log.exception("ai_find_retreat_direction error", exc_info=e)
        return (0, 0)


def ai_count_nearby_allies(enemy, game, radius=3):
    """Count nearby allied enemies within radius."""
    try:
        ex, ey = getattr(enemy, 'x', 0), getattr(enemy, 'y', 0)
        count = 0
        for other in getattr(game, 'enemies', []):
            if other is enemy:
                continue
            ox, oy = getattr(other, 'x', 0), getattr(other, 'y', 0)
            dist = abs(ox - ex) + abs(oy - ey)
            if dist <= radius:
                count += 1
        return count
    except Exception as e:
        if log:
            log.exception("ai_count_nearby_allies error", exc_info=e)
        return 0


def ai_find_flanking_position(enemy, game):
    """Find position to flank player (perpendicular to direct line)."""
    try:
        ex, ey = getattr(enemy, 'x', 0), getattr(enemy, 'y', 0)
        px, py = getattr(game.player, 'x', 0), getattr(game.player, 'y', 0)
        
        # Cache flanking calculations to avoid repeated computation
        if not hasattr(game, '_flanking_cache'):
            game._flanking_cache = {}
            
        cache_key = f"flank_{ex}_{ey}_{px}_{py}"
        if cache_key in game._flanking_cache:
            return game._flanking_cache[cache_key]
        
        # Direct approach vector
        direct_dx = 1 if px > ex else (-1 if px < ex else 0)
        direct_dy = 1 if py > ey else (-1 if py < ey else 0)
        
        # Try perpendicular directions for flanking
        perp_options = []
        if direct_dx != 0:
            perp_options.extend([(direct_dx, 1), (direct_dx, -1)])
        if direct_dy != 0:
            perp_options.extend([(1, direct_dy), (-1, direct_dy)])
        
        # If no perpendicular options, use direct approach
        if not perp_options:
            result = (direct_dx, direct_dy)
        else:
            # Pick random perpendicular direction for variation
            result = random.choice(perp_options)
            
        # Cache result with small cache limit to prevent memory growth
        if len(game._flanking_cache) < 50:
            game._flanking_cache[cache_key] = result
            
        return result
    except Exception as e:
        if log:
            log.exception("ai_find_flanking_position error", exc_info=e)
        return (0, 0)


def ai_maintain_range(enemy, game, preferred_distance=4):
    """Move to maintain preferred distance from player (for ranged enemies)."""
    try:
        ex, ey = getattr(enemy, 'x', 0), getattr(enemy, 'y', 0)
        px, py = getattr(game.player, 'x', 0), getattr(game.player, 'y', 0)
        
        # Cache range calculations for performance
        if not hasattr(game, '_range_cache'):
            game._range_cache = {}
            
        cache_key = f"range_{ex}_{ey}_{px}_{py}_{preferred_distance}"
        if cache_key in game._range_cache:
            return game._range_cache[cache_key]
        
        dist = abs(px - ex) + abs(py - ey)
        result = (0, 0)
        
        # Too close - move away
        if dist < preferred_distance - 1:
            dx = -1 if px > ex else (1 if px < ex else 0)
            dy = -1 if py > ey else (1 if py < ey else 0)
            result = (dx, dy)
        
        # Too far - move closer
        elif dist > preferred_distance + 2:
            dx = 1 if px > ex else (-1 if px < ex else 0)
            dy = 1 if py > ey else (-1 if py < ey else 0)
            result = (dx, dy)
        
        # Good distance - hold or sidestep
        else:
            # Sidestep perpendicular 50% of time
            if random.random() < 0.5:
                result = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            else:
                result = (0, 0)
        
        # Cache with limit to prevent memory growth
        if len(game._range_cache) < 30:
            game._range_cache[cache_key] = result
            
        return result
    except Exception as e:
        if log:
            log.exception("ai_maintain_range error", exc_info=e)
        return (0, 0)


def ai_can_move_to(game, x, y, exclude_enemy=None):
    """Check if position is valid floor tile and not occupied."""
    try:
        # Performance optimization: cache pathfinding results
        if not hasattr(game, '_pathfinding_cache'):
            game._pathfinding_cache = {}
            
        # Create cache key (exclude enemy ID from key for general validity)
        cache_key = f"move_{x}_{y}"
        
        # Check cache for static terrain (walls, bounds)
        if cache_key in game._pathfinding_cache:
            is_walkable_terrain = game._pathfinding_cache[cache_key]
        else:
            # Check bounds and terrain
            if not (0 <= y < len(game.game_map) and 0 <= x < len(game.game_map[0])):
                game._pathfinding_cache[cache_key] = False
                return False
            
            from jedi_fugitive.game.level import Display
            tile = str(game.game_map[y][x])
            # Check if NOT a wall or mountain (allow all floor tiles including special dungeon floors)
            # Include special dungeon wall tiles
            non_walkable = {
                '\u2588',  # Display.WALL / Shadowmaze walls
                '#',  # Legacy wall tile
                '^',  # Mountains (impassable)
                '\u2593',  # Memory Vault crystal walls
                '\u2666',  # Crystal Garden walls
                '\u256c',  # Bone Cathedral walls
                '\u2551',  # Echo Chambers acoustic walls
                '\u25a4',  # Twisted Library bookshelf walls
                '\u25a3',  # Pain Forge metal walls
                '\u224b',  # Dream Nexus fluid walls
                '\u2663',  # Trees (Display.TREE)
                '\u2248',  # Waves/dunes (Display.DUNE)
                '~',  # Water/waves
                'T',  # Legacy tree symbol
            }
            is_walkable_terrain = tile not in non_walkable
            game._pathfinding_cache[cache_key] = is_walkable_terrain
        
        if not is_walkable_terrain:
            return False
        
        # Check dynamic occupants (player and enemies) - can't cache these
        if x == getattr(game.player, 'x', -1) and y == getattr(game.player, 'y', -1):
            return False
        
        # Check other enemies
        for other in getattr(game, 'enemies', []):
            if other is exclude_enemy:
                continue
            if getattr(other, 'x', -1) == x and getattr(other, 'y', -1) == y:
                return False
        
        return True
    except Exception as e:
        if log:
            log.exception("ai_can_move_to error", exc_info=e)
        return False


def ai_count_nearby_enemies(game, radius=8):
    """Count total enemies near player within radius."""
    try:
        px, py = getattr(game.player, 'x', 0), getattr(game.player, 'y', 0)
        count = 0
        for enemy in getattr(game, 'enemies', []):
            ex, ey = getattr(enemy, 'x', 0), getattr(enemy, 'y', 0)
            dist = abs(ex - px) + abs(ey - py)
            if dist <= radius:
                count += 1
        return count
    except Exception:
        return 0


def ai_should_charge(enemy, game):
    """Determine if enemy should participate in coordinated charge (3+ enemies nearby)."""
    try:
        # Check if 3 or more enemies are within 8 tiles of player
        nearby_count = ai_count_nearby_enemies(game, radius=8)
        if nearby_count >= 3:
            # Don't charge if already adjacent or too low HP
            dist = abs(getattr(enemy, 'x', 0) - getattr(game.player, 'x', 0)) + abs(getattr(enemy, 'y', 0) - getattr(game.player, 'y', 0))
            hp_percent = getattr(enemy, 'hp', 1) / max(1, getattr(enemy, 'max_hp', 1))
            if dist > 1 and hp_percent > 0.25:
                return True
        return False
    except Exception:
        return False


def ai_get_enemy_behavior(enemy):
    """Determine enemy's combat behavior based on type."""
    try:
        enemy_type = getattr(enemy, 'enemy_behavior', None)
        if enemy_type:
            return enemy_type
        
        # Infer from name if no explicit behavior
        name = getattr(enemy, 'name', '').lower()
        if 'sniper' in name or 'marksman' in name:
            return 'sniper'
        elif 'brawler' in name or 'berserker' in name or 'warrior' in name:
            return 'aggressive'
        elif 'scout' in name or 'assassin' in name:
            return 'flanker'
        elif 'trooper' in name or 'soldier' in name:
            return 'ranged'
        else:
            return 'standard'
    except Exception:
        return 'standard'


class EnemyType(Enum):
    SITH_TROOPER = 1
    SITH_GHOST = 2
    INQUISITOR = 3
    JEDI_MASTER = 4
    SITH_LORD = 5
    FAUNA = "fauna"


def _pdef(player):
    """Player defense including lightsaber stance bonus."""
    try:
        from jedi_fugitive.game import form_combat
        return form_combat.total_defense(player)
    except Exception:
        return getattr(player, "defense", 0) or 0


class Enemy:
    def __init__(self, *args, **kwargs):
        """Flexible constructor: supports typed and legacy signatures."""
        # typed signature if first arg is an EnemyType
        if len(args) > 0 and isinstance(args[0], EnemyType):
            enemy_type = args[0]
            level = kwargs.get("level", args[1] if len(args) > 1 else 1)
            self.type = enemy_type
            self.level = max(1, int(level))
            # populate base stats via typed helper
            self._init_from_type()
            # apply level scaling
            self.scale_with_level()
            self.hp = self.max_hp
            self.x = kwargs.get("x", 0)
            self.y = kwargs.get("y", 0)
            self.personality = kwargs.get("personality", None)
        else:
            # legacy signature: name, hp, attack, defense, evasion, personality, xp_value=10, x=0, y=0, level=1
            name = args[0] if len(args) > 0 else kwargs.get("name", "Enemy")
            hp = args[1] if len(args) > 1 else kwargs.get("hp", kwargs.get("base_hp", 10))
            attack = args[2] if len(args) > 2 else kwargs.get("attack", 1)
            defense = args[3] if len(args) > 3 else kwargs.get("defense", 0)
            evasion = args[4] if len(args) > 4 else kwargs.get("evasion", 0)
            personality = args[5] if len(args) > 5 else kwargs.get("personality", None)
            xp_value = args[6] if len(args) > 6 else kwargs.get("xp_value", 10)
            x = args[7] if len(args) > 7 else kwargs.get("x", 0)
            y = args[8] if len(args) > 8 else kwargs.get("y", 0)
            level = kwargs.get("level", kwargs.get("lvl", 1))
            # assign legacy fields
            self.name = name
            self.base_hp = int(hp)
            self.max_hp = int(hp)
            self.hp = int(hp)
            self.attack = int(attack)
            self.defense = int(defense)
            self.evasion = int(evasion)
            self.personality = personality
            self.xp_value = int(xp_value)
            self.x = int(x)
            self.y = int(y)
            self.level = max(1, int(level))
            self.symbol = getattr(self, "symbol", "E")
            if self.level > 1:
                # call legacy scaling if present
                try:
                    self.scale_by_level(self.level)
                except Exception:
                    pass
        # taunt/voice bookkeeping (turn index of last taunt)
        try:
            self._last_taunt_turn = getattr(self, "_last_taunt_turn", -9999)
            self._taunt_cooldown = getattr(self, "_taunt_cooldown", 6)
        except Exception:
            self._last_taunt_turn = -9999
            self._taunt_cooldown = 6
        # ability cooldown bookkeeping
        try:
            self._ability_last_used = getattr(self, '_ability_last_used', {}) or {}
        except Exception:
            self._ability_last_used = {}

    # typed init helper
    def _init_from_type(self):
        # defaults for typed EnemyType
        self.x = 0; self.y = 0
        et = getattr(self, "type", None)
        if et == EnemyType.SITH_TROOPER:
            self.name = "Sith Trooper"
            self.symbol = 'T'
            self.base_hp = 12
            self.max_hp = 12
            self.attack = 8
            self.defense = 2
            self.accuracy = 60
            self.xp_value = 8  # Reduced from 25
            self.alert_range = 6
        elif et == EnemyType.SITH_GHOST:
            self.name = "Sith Ghost"
            self.symbol = 'G'
            self.base_hp = 25
            self.max_hp = 25
            self.attack = 12
            self.defense = 4
            self.accuracy = 75
            self.xp_value = 15  # Reduced from 50
            self.alert_range = 8
        elif et == EnemyType.INQUISITOR:
            self.name = "Inquisitor"
            self.symbol = 'I'
            self.base_hp = 60
            self.max_hp = 60
            self.attack = 16
            self.defense = 6
            self.accuracy = 85
            self.xp_value = 90  # Reduced from 300
            self.alert_range = 12
        elif et == EnemyType.JEDI_MASTER:
            self.name = "Jedi Master"
            self.symbol = 'J'
            self.base_hp = 80
            self.max_hp = 80
            self.attack = 15
            self.defense = 8
            self.accuracy = 90
            self.xp_value = 1000
            self.alert_range = 14
            self.is_boss = True
        elif et == EnemyType.SITH_LORD:
            self.name = "Sith Lord"
            self.symbol = 'L'
            self.is_boss = True
            self.base_hp = 80
            self.max_hp = 80
            self.attack = 17
            self.defense = 7
            self.accuracy = 88
            self.xp_value = 1000
            self.alert_range = 14
        else:
            # fallback generic enemy
            self.name = "Enemy"
            self.symbol = "E"
            self.base_hp = 10
            self.max_hp = 10
            self.attack = 4
            self.defense = 1
            self.accuracy = 60
            self.xp_value = 10
            self.alert_range = 6

    def set_base_stats(self):
        # preserved for compatibility; recalculates base stats from current type/name
        try:
            if hasattr(self, "type"):
                self._init_from_type()
        except Exception:
            pass

    def scale_with_level(self):
        # scale stats using a slightly different per-level progression and
        # respect the global DIFFICULTY_MULTIPLIER when available so tuning
        # can be done from config.py without changing code.
        try:
            from jedi_fugitive.config import DIFFICULTY_MULTIPLIER
        except Exception:
            DIFFICULTY_MULTIPLIER = 1.0

        lvl = max(1, int(getattr(self, "level", 1)))
        # HP grows more moderately and attack a bit more aggressively in the
        # alternate tuning below. These numbers are chosen to rebalance
        # survivability vs threat.
        hp_growth_per_level = 0.12  # ~12% HP per level (reduced)
        atk_growth_per_level = 0.11  # ~11% attack per level (increased)
        def_growth_per_level = 0.06  # ~6% defense per level (unchanged)

        mult = max(0.01, float(DIFFICULTY_MULTIPLIER))
        hp_factor = 1.0 + (lvl - 1) * hp_growth_per_level * mult
        atk_factor = 1.0 + (lvl - 1) * atk_growth_per_level * mult
        def_factor = 1.0 + (lvl - 1) * def_growth_per_level * mult

        try:
            base_hp = int(getattr(self, "base_hp", getattr(self, "max_hp", 10)))
            self.max_hp = max(1, int(base_hp * hp_factor))
        except Exception:
            self.max_hp = getattr(self, "max_hp", getattr(self, "base_hp", 10))
        try:
            self.attack = max(0, int(getattr(self, "attack", 1) * atk_factor))
        except Exception:
            pass
        try:
            self.defense = max(0, int(getattr(self, "defense", 0) * def_factor))
        except Exception:
            pass
        # clamp current hp to the new max
        self.hp = min(getattr(self, "hp", self.max_hp), self.max_hp)

    def is_alive(self) -> bool:
        return getattr(self, "hp", 0) > 0

    def take_damage(self, amount: int, game=None) -> int:
        """Apply damage to enemy. If game is provided and enemy dies, award XP to player."""
        actual = max(1, int(amount) - int(getattr(self, "defense", 0)))
        was_alive = self.hp > 0
        try:
            self.hp -= actual
        except Exception:
            self.hp = getattr(self, "hp", 0) - actual
        
        # Award Dark XP if enemy died from this damage (killing is dark path)
        if was_alive and self.hp <= 0 and game is not None:
            try:
                xp_reward = int(getattr(self, 'xp_value', 10) * 0.3)  # Reduced by 70%
                if hasattr(game, 'player'):
                    game.player.dark_xp = getattr(game.player, 'dark_xp', 0) + xp_reward
                    
                    # Check for dark level up - USE UNIFIED SYSTEM
                    while game.player.dark_xp >= getattr(game.player, 'xp_to_next_dark', 100):
                        game.player.dark_level = getattr(game.player, 'dark_level', 1) + 1
                        game.player.dark_xp -= getattr(game.player, 'xp_to_next_dark', 100)
                        game.player.xp_to_next_dark = int(game.player.xp_to_next_dark * 1.5)
                        game.player.level = max(getattr(game.player, 'light_level', 1), game.player.dark_level)
                        
                        # Call unified level_up() which shows interactive menu
                        game.player.level_up()
                        if hasattr(game, 'ui') and hasattr(game.ui, 'messages'):
                            game.ui.messages.add(f"#1#DARK SIDE LEVEL UP!#0# Now Dark Level {game.player.dark_level}")
                    
                    if hasattr(game, 'ui') and hasattr(game.ui, 'messages'):
                        enemy_name = getattr(self, 'name', 'enemy')
                        game.ui.messages.add(f"Gained {xp_reward} Dark XP from {enemy_name}!")
            except Exception:
                pass  # Don't let XP errors break combat
        
        return actual

    def maybe_speak(self):
        # simple probabilistic check retained for compatibility
        try:
            return random.random() < 0.06
        except Exception:
            return False

    def scale_by_level(self, level: int):
        """Backwards-compatible level scaler used by some legacy code paths."""
        try:
            from jedi_fugitive.config import DIFFICULTY_MULTIPLIER
        except Exception:
            DIFFICULTY_MULTIPLIER = 1.0

        lvl = max(1, int(level))
        mult = max(0.01, float(DIFFICULTY_MULTIPLIER))
        # legacy scaler kept but tuned to be slightly less aggressive than
        # the newer scale_with_level implementation.
        hp_scale = 1.0 + 0.12 * (lvl - 1) * mult
        stat_scale = 1.0 + 0.07 * (lvl - 1) * mult
        try:
            base = int(getattr(self, "base_hp", getattr(self, "max_hp", 10)))
            self.max_hp = max(1, int(base * hp_scale))
            self.hp = min(getattr(self, "hp", self.max_hp), self.max_hp)
        except Exception:
            pass
        try:
            self.attack = int(getattr(self, "attack", 1) * stat_scale)
            self.defense = int(getattr(self, "defense", 0) * stat_scale)
            self.evasion = int(getattr(self, "evasion", 0) * stat_scale)
        except Exception:
            pass

    def attempt_ranged_shot(self, game):
        """Stormtrooper blaster shot (range 2-4). Animation stops at first blocking tile."""
        try:
            # identify sith trooper type robustly
            et = getattr(self, "type", None)
            is_trooper = False
            try:
                from jedi_fugitive.game.enemy import EnemyType
                if et == getattr(EnemyType, "SITH_TROOPER", None):
                    is_trooper = True
            except Exception:
                pass
            if not is_trooper:
                name = getattr(self, "name", "") or ""
                if "sith trooper" in name.lower() or "trooper" in name.lower():
                    is_trooper = True
            if not is_trooper:
                return False

            player = getattr(game, "player", None)
            if not player:
                return False
            px, py = getattr(player, "x", -999), getattr(player, "y", -999)
            sx, sy = getattr(self, "x", -999), getattr(self, "y", -999)
            dx = px - sx
            dy = py - sy
            cheb = max(abs(dx), abs(dy))
            if cheb < 2 or cheb > 4:
                return False

            # simple Bresenham
            def _bresenham_line(x0, y0, x1, y1):
                dx_ = abs(x1 - x0)
                dy_ = -abs(y1 - y0)
                sx_ = 1 if x0 < x1 else -1
                sy_ = 1 if y0 < y1 else -1
                err_ = dx_ + dy_
                x_, y_ = x0, y0
                while True:
                    yield x_, y_
                    if x_ == x1 and y_ == y1:
                        break
                    e2 = 2 * err_
                    if e2 >= dy_:
                        err_ += dy_
                        x_ += sx_
                    if e2 <= dx_:
                        err_ += dx_
                        y_ += sy_

            wall_ch = getattr(game, "Display", None) and getattr(game.Display, "WALL", "#") or "#"
            tree_ch = getattr(game, "Display", None) and getattr(game.Display, "TREE", "T") or "T"

            # find the stopping point: first blocking tile encountered (or player)
            stop_x, stop_y = px, py
            blocked = False
            for bx, by in _bresenham_line(sx, sy, px, py):
                if (bx, by) == (sx, sy):
                    continue
                if (bx, by) == (px, py):
                    stop_x, stop_y = px, py
                    break
                try:
                    ch = game.game_map[by][bx]
                except Exception:
                    ch = None
                if ch in (wall_ch, tree_ch) or (isinstance(ch, str) and ch and ch[0] in ("#", "|", "+")):
                    # stop at the blocking tile (the bolt hits the wall/tree)
                    stop_x, stop_y = bx, by
                    blocked = True
                    break

            try:
                game.ui.messages.add(f"{getattr(self,'name','A trooper')} fires a blaster bolt!")
            except Exception:
                pass

            # animate to stopping point (GameManager will clip to viewport)
            try:
                if hasattr(game, "animate_projectile"):
                    game.animate_projectile(sx, sy, stop_x, stop_y, symbol='*', delay=0.035)
            except Exception:
                pass

            if blocked:
                try:
                    game.ui.messages.add(f"The bolt hits {stop_x},{stop_y} and fizzles out.")
                except Exception:
                    pass
                return True

            # Check for deflection
            deflected = False
            if player:
                # Check if player has lightsaber
                has_lightsaber = False
                weapon = getattr(player, 'equipped_weapon', None)
                if weapon:
                    w_type = getattr(weapon, 'weapon_type', None)
                    # Check enum or string
                    if str(w_type) in ['WeaponType.LIGHTSABER', 'WeaponType.DUAL_LIGHTSABER', 'WeaponType.LIGHTSABER_PIKE']:
                        has_lightsaber = True
                    elif "lightsaber" in getattr(weapon, 'name', '').lower():
                        has_lightsaber = True
                
                if has_lightsaber:
                    # Calculate deflection chance
                    # Base 20% + (Accuracy - 50)/2 + Form bonuses
                    deflect_chance = 0.20
                    acc_stat = getattr(player, 'accuracy', 60)
                    deflect_chance += max(0, (acc_stat - 50) * 0.005)
                    
                    # Form bonuses
                    from jedi_fugitive.game import form_combat as _fc
                    active_form = _fc.form_key(player) or 'Shii-Cho'
                    if active_form == 'Soresu': # Defensive form
                        deflect_chance += 0.25
                    elif active_form == 'Shien': # Blaster deflection form
                        deflect_chance += 0.35
                    
                    if random.random() < deflect_chance:
                        deflected = True
                        try:
                            # Check for reflection (Shien form specializes in this)
                            reflect_chance = 0.0
                            if active_form == 'Shien':
                                reflect_chance = 0.50
                            elif active_form == 'Soresu':
                                reflect_chance = 0.10
                            elif active_form == 'Niman':
                                reflect_chance = 0.25
                            
                            # Accuracy bonus to reflection
                            reflect_chance += max(0, (acc_stat - 60) * 0.005)
                            
                            if random.random() < reflect_chance:
                                game.ui.messages.add(f"#11#You reflect the bolt back at the shooter!#0#")
                                # Animate return bolt
                                if hasattr(game, "animate_projectile"):
                                    game.animate_projectile(px, py, sx, sy, symbol='*', delay=0.02)
                                
                                # Apply damage to shooter
                                reflect_damage = random.randint(4, 8) + int((acc_stat - 50) / 5)
                                self.take_damage(reflect_damage, game=game)
                                game.ui.messages.add(f"The reflected bolt hits {getattr(self, 'name', 'Enemy')} for {reflect_damage} damage!")
                            else:
                                game.ui.messages.add(f"#11#You deflect the blaster bolt with your lightsaber!#0#")
                                # Animate deflection (spark)
                                if hasattr(game, "animate_projectile"):
                                    # Just a quick flash at player pos
                                    game.animate_projectile(px, py, px, py, symbol='X', delay=0.1)
                        except Exception:
                            pass

            if deflected:
                return True # Shot blocked

            # otherwise bolt reached player tile -> resolve hit using distance-based accuracy
            acc = 0.30 + max(0, (4 - cheb)) * 0.15
            roll = random.random()
            if roll <= acc:
                base_damage = random.randint(1, 4)
                p_def = _pdef(player)
                damage = max(0, base_damage - int(p_def * 0.5))
                try:
                    player.hp = max(0, getattr(player, "hp", getattr(player, "max_hp", 0)) - damage)
                except Exception:
                    try:
                        setattr(player, "hp", max(0, getattr(player, "hp", 0) - damage))
                    except Exception:
                        pass
                try:
                    game.ui.messages.add(f"Hit! You take {damage} damage.")
                except Exception:
                    pass
                return True
            else:
                try:
                    game.ui.messages.add("The bolt misses!")
                except Exception:
                    pass
                return True
        except Exception:
            return False

    def take_turn(self, game):
        """Optional AI hook for enemies to perform complex actions (boss abilities, force use).
        Return True if the enemy consumed its action (no further movement/attacks)."""
        try:
            # only living enemies act
            if not getattr(self, 'is_alive', lambda: True)():
                return False

            # Boss or inquisitor special AI: use force abilities if available
            is_boss = getattr(self, 'is_boss', False) or (getattr(self, 'type', None) == EnemyType.INQUISITOR)
            if not is_boss:
                return False

            ui_msgs = getattr(game, 'ui', None) and getattr(game.ui, 'messages', None)
            # Ensure abilities always receive an object with .add(text) even when
            # the UI message buffer is not present (e.g., during some tests or
            # unusual startup races). Fall back to a thin wrapper over
            # game.add_message so ability code can call messages.add(...).
            try:
                if ui_msgs is None and getattr(game, 'add_message', None):
                    class _FallbackMsgs:
                        def __init__(self, gm):
                            self._gm = gm
                        def add(self, text, color=0):
                            try:
                                self._gm.add_message(str(text))
                            except Exception:
                                try:
                                    print(text)
                                except Exception:
                                    pass
                    ui_msgs = _FallbackMsgs(game)
            except Exception:
                pass
            player = getattr(game, 'player', None)

            fa_map = getattr(self, 'force_abilities', None)
            # if boss was given a dict of abilities, use its values; else attempt to copy from player if missing
            if not fa_map and player is not None:
                fa_map = getattr(self, 'force_abilities', None)

            abilities = []
            try:
                if fa_map:
                    if hasattr(fa_map, 'values'):
                        abilities = list(fa_map.values())
                    else:
                        abilities = list(fa_map)
            except Exception:
                abilities = []

            # choose defensive heal first if low HP (respect cooldown)
            try:
                if abilities and getattr(self, 'hp', 0) <= max(1, int(0.35 * getattr(self, 'max_hp', 1))):
                    for a in abilities:
                        try:
                            aname = getattr(a, 'name', '')
                            last = getattr(self, '_ability_last_used', {}).get(aname, -9999)
                            cooldown = getattr(a, 'cooldown', 3)
                            if getattr(game, 'turn_count', 0) - last < cooldown:
                                continue
                            if 'heal' in aname.lower():
                                used = a.use(self, self, game.game_map, ui_msgs, getattr(self, 'level', 1))
                                if used:
                                    try:
                                        self._ability_last_used[aname] = getattr(game, 'turn_count', 0)
                                    except Exception:
                                        pass
                                    return True
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                if player is not None:
                    dist = abs(getattr(player, 'x', 0) - getattr(self, 'x', 0)) + abs(getattr(player, 'y', 0) - getattr(self, 'y', 0))
                else:
                    dist = 999
                # prefer lightning for ranged damage; consider kill opportunity and cooldowns
                best_off = None
                best_off_score = -9999
                for a in abilities:
                    try:
                        aname = getattr(a, 'name', '')
                        last = getattr(self, '_ability_last_used', {}).get(aname, -9999)
                        cooldown = getattr(a, 'cooldown', 3)
                        if getattr(game, 'turn_count', 0) - last < cooldown:
                            continue
                        if 'lightning' in aname.lower() and dist <= 8:
                            est = getattr(a, 'damage', getattr(a, 'damage', 5)) + getattr(self, 'level', 1)
                            # prioritize lethal
                            score = est + (1000 if est >= getattr(player, 'hp', 0) else 0)
                            if score > best_off_score:
                                best_off = a; best_off_score = score
                    except Exception:
                        continue
                if best_off is not None:
                    try:
                        used = best_off.use(self, player, game.game_map, ui_msgs, getattr(self, 'level', 1))
                        if used:
                            try: self._ability_last_used[getattr(best_off, 'name', str(best_off))] = getattr(game, 'turn_count', 0)
                            except Exception: pass
                            return True
                    except Exception:
                        pass

                # use push/pull to reposition when in melee
                for a in abilities:
                    try:
                        aname = getattr(a, 'name', '')
                        last = getattr(self, '_ability_last_used', {}).get(aname, -9999)
                        cooldown = getattr(a, 'cooldown', 2)
                        if getattr(game, 'turn_count', 0) - last < cooldown:
                            continue
                        if 'push' in aname.lower() and dist <= 2:
                            used = a.use(self, player, game.game_map, ui_msgs, getattr(self, 'level', 1))
                            if used:
                                try: self._ability_last_used[aname] = getattr(game, 'turn_count', 0)
                                except Exception: pass
                                return True
                    except Exception:
                        continue

                # use reveal if not enough sight
                for a in abilities:
                    try:
                        aname = getattr(a, 'name', '')
                        last = getattr(self, '_ability_last_used', {}).get(aname, -9999)
                        cooldown = getattr(a, 'cooldown', 4)
                        if getattr(game, 'turn_count', 0) - last < cooldown:
                            continue
                        if 'reveal' in aname.lower():
                            used = a.use(self, None, game.game_map, ui_msgs, getattr(self, 'level', 1))
                            if used:
                                try: self._ability_last_used[aname] = getattr(game, 'turn_count', 0)
                                except Exception: pass
                                return True
                    except Exception:
                        continue
            except Exception:
                pass

            return False
        except Exception:
            return False


# EnemyPersonality is now imported from jedi_fugitive.game.personality


def find_enemy_target(enemy, game):
    """
    Find the best target for an enemy based on faction relationships.
    Returns (target_x, target_y, target_object, target_type) where target_type is 'player' or 'enemy'.
    If no valid target, returns (None, None, None, None).
    """
    try:
        # Get enemy's faction
        enemy_faction = getattr(enemy, 'faction', None)
        if not enemy_faction:
            # No faction = always target player
            return (getattr(game.player, 'x', 0), getattr(game.player, 'y', 0), game.player, 'player')
        
        # Get faction manager
        faction_manager = getattr(game, 'faction_manager', None)
        if not faction_manager:
            # No faction system = always target player
            return (getattr(game.player, 'x', 0), getattr(game.player, 'y', 0), game.player, 'player')
        
        # Check if player is hostile with this enemy's faction
        player_is_hostile = faction_manager.is_player_hostile_to_faction(enemy_faction)
        player_is_friendly = faction_manager.is_player_friendly_to_faction(enemy_faction)
        
        # Get enemy position
        ex = getattr(enemy, 'x', 0)
        ey = getattr(enemy, 'y', 0)
        
        # Find nearest hostile target (player or other faction enemies)
        nearest_hostile = None
        nearest_hostile_dist = 9999
        nearest_hostile_type = None
        
        # Check other enemies for hostile factions
        for other in getattr(game, 'enemies', []):
            if other is enemy:
                continue
            if not getattr(other, 'is_alive', lambda: False)():
                continue
            
            other_faction = getattr(other, 'faction', None)
            if not other_faction:
                continue  # No faction = not a valid inter-faction target
            
            # Check if factions are hostile
            if faction_manager.are_factions_hostile(enemy_faction, other_faction):
                ox = getattr(other, 'x', 0)
                oy = getattr(other, 'y', 0)
                dist = abs(ex - ox) + abs(ey - oy)
                
                if dist < nearest_hostile_dist:
                    nearest_hostile = other
                    nearest_hostile_dist = dist
                    nearest_hostile_type = 'enemy'
        
        # Check player as potential target
        px = getattr(game.player, 'x', 0)
        py = getattr(game.player, 'y', 0)
        player_dist = abs(ex - px) + abs(ey - py)
        
        # Priority system:
        # 1. If player is hostile (rep < -20), they are a valid target
        # 2. If player is friendly (rep > 20), never target them
        # 3. If player is neutral, only target if no hostile faction enemies nearby
        
        if player_is_friendly:
            # Player is friendly, only target hostile faction enemies
            if nearest_hostile:
                return (getattr(nearest_hostile, 'x', 0), getattr(nearest_hostile, 'y', 0), nearest_hostile, 'enemy')
            else:
                # No targets, patrol or stay
                return (None, None, None, None)
        
        elif player_is_hostile:
            # Player is hostile, prioritize closest hostile target
            if nearest_hostile and nearest_hostile_dist < player_dist:
                return (getattr(nearest_hostile, 'x', 0), getattr(nearest_hostile, 'y', 0), nearest_hostile, 'enemy')
            else:
                return (px, py, game.player, 'player')
        
        else:
            # Player is neutral - prioritize faction enemies, but target player if close
            if nearest_hostile and nearest_hostile_dist < min(player_dist, 10):
                # Hostile faction enemy is closer or player is far
                return (getattr(nearest_hostile, 'x', 0), getattr(nearest_hostile, 'y', 0), nearest_hostile, 'enemy')
            elif player_dist <= 6:
                # Player is close and neutral = potential target
                return (px, py, game.player, 'player')
            elif nearest_hostile:
                # Target distant faction enemy
                return (getattr(nearest_hostile, 'x', 0), getattr(nearest_hostile, 'y', 0), nearest_hostile, 'enemy')
            else:
                # No targets
                return (None, None, None, None)
    
    except Exception:
        # Fallback to player on any error
        return (getattr(game.player, 'x', 0), getattr(game.player, 'y', 0), game.player, 'player')


def process_enemies(game):
    """Process enemy turns: movement, taunts and attacks. Defensive and respects depth/difficulty."""
    from jedi_fugitive.config import DIFFICULTY_MULTIPLIER, DEPTH_DIFFICULTY_RATE
    
    # Advance projectiles FIRST so blaster bolts move before enemies act
    try:
        from jedi_fugitive.game import projectiles as proj
        proj.advance_projectiles(game)
    except Exception:
        pass
    
    # Performance optimization: batch processing and distance caching
    try:
        enemies = list(getattr(game, "enemies", []) or [])
        if not enemies:
            return
            
        # Cache player position for distance calculations
        px = getattr(game.player, "x", 0)
        py = getattr(game.player, "y", 0)
        
        # Pre-calculate distances and sort by proximity for better AI
        enemy_distances = []
        for e in enemies:
            if getattr(e, "is_alive", lambda: True)():
                ex = getattr(e, "x", 0)
                ey = getattr(e, "y", 0)
                dist = abs(px - ex) + abs(py - ey)
                enemy_distances.append((e, dist, ex, ey))
        
        # Process enemies in proximity order (closest first for tactical AI)
        enemy_distances.sort(key=lambda x: x[1])
        
        for e, dist, ex, ey in enemy_distances:
            try:
                # hallucinations are not real enemies: vanish when approached
                try:
                    if getattr(e, '_is_hallucination', False):
                        # use pre-calculated distance
                        if dist <= 1:
                            try:
                                if getattr(game.ui, 'messages', None):
                                    apparition_name = getattr(e,'name','An apparition')
                                    biome = getattr(game, 'current_biome', 'unknown')
                                    
                                    # Environmental hallucination descriptions
                                    fade_messages = {
                                        'desert': f"{apparition_name} dissolves like a mirage in the desert heat — it was never real.",
                                        'forest': f"{apparition_name} melts back into the forest shadows — your mind conjured phantoms.",
                                        'mountains': f"{apparition_name} vanishes like morning mist in the mountain air — only illusion.",
                                        'tomb': f"{apparition_name} fades into the tomb's ancient darkness — the dead playing tricks on your mind.",
                                        'crash_site': f"{apparition_name} flickers out like a broken hologram — trauma creates false visions."
                                    }
                                    
                                    message = fade_messages.get(biome, f"{apparition_name} fades as you approach — it was only in your mind.")
                                    game.ui.messages.add(message)
                            except Exception:
                                pass
                            try:
                                game.enemies.remove(e)
                            except Exception:
                                pass
                        # otherwise, hallucination does not act
                        continue
                except Exception:
                    # safe fallback if hallucination flags or ui are missing
                    pass
                if not getattr(e, "is_alive", lambda: False)():
                    try:
                        game.enemies.remove(e)
                    except Exception:
                        pass
                    continue

                # Awareness: enemies far from the player sleep until approached, and
                # alerted ones eventually lose the trail. Hunters never give up.
                # (Keeps a large world populated without every enemy converging.)
                try:
                    far = abs(getattr(e, "x", 0) - getattr(game.player, "x", 0)) + abs(getattr(e, "y", 0) - getattr(game.player, "y", 0))
                    if getattr(e, 'cordon', False) and not getattr(e, '_has_spotted', False):
                        continue  # holding the cordon ring (moved by game.cordon.update_cordon)
                    if not getattr(e, 'is_hunter', False):
                        if getattr(e, '_has_spotted', False):
                            if far > int(getattr(game, 'enemy_lose_track_radius', 45)):
                                e._has_spotted = False
                                continue
                        elif far > int(getattr(game, 'enemy_wake_radius', 28)):
                            continue
                except Exception:
                    pass

                # Stormtroopers may attempt a ranged blaster shot first (consumes their turn if fired)
                try:
                    if hasattr(e, "attempt_ranged_shot"):
                        tried_shot = False
                        try:
                            tried_shot = e.attempt_ranged_shot(game)
                        except Exception:
                            tried_shot = False
                        if tried_shot:
                            # shot consumed this enemy's action; skip movement/other actions
                            continue
                except Exception:
                    pass

                # allow enemy-specific AI hook (bosses or scripted enemies)
                try:
                    if hasattr(e, 'take_turn') and callable(e.take_turn):
                        acted = False
                        try:
                            acted = e.take_turn(game)
                        except Exception:
                            acted = False
                        if acted:
                            # custom AI consumed the enemy's action
                            continue
                except Exception:
                    pass

                # Use pre-calculated distance from batch processing
                # dist, ex, ey already available from outer loop

                # if enemy notices the player for the first time, increase stress
                try:
                    alert = int(getattr(e, 'alert_range', 6))
                    if dist <= alert and not getattr(e, '_has_spotted', False):
                        try:
                            e._has_spotted = True
                            added = 0
                            try:
                                added = game.player.add_stress(5, source='spotted')
                            except Exception:
                                pass
                            try:
                                if getattr(game.ui, 'messages', None):
                                    enemy_name = getattr(e,'name','An enemy')
                                    biome = getattr(game, 'current_biome', 'unknown')
                                    
                                    # Environmental awareness for spotting messages
                                    spot_messages = {
                                        'desert': f"{enemy_name} emerges from behind a dune and spots you! (+{added} stress)",
                                        'forest': f"{enemy_name} steps out from the forest shadows and locks eyes with you! (+{added} stress)",
                                        'mountains': f"{enemy_name} appears on a rocky outcrop above and spots you! (+{added} stress)",
                                        'tomb': f"{enemy_name} emerges from the tomb's darkness and fixes you with a hostile gaze! (+{added} stress)",
                                        'crash_site': f"{enemy_name} rises from the wreckage and turns aggressive attention to you! (+{added} stress)"
                                    }
                                    
                                    message = spot_messages.get(biome, f"{enemy_name} spots you! (+{added} stress)")
                                    game.ui.messages.add(message)
                            except Exception:
                                pass
                        except Exception:
                            pass
                except Exception:
                    pass

                # occasional contextual taunt when in range -> increases stress
                try:
                    if hasattr(e, "personality") and getattr(game, "turn_count", None) is not None:
                        now = getattr(game, "turn_count", 0)
                        last = getattr(e, "_last_taunt_turn", -9999)
                        cooldown = getattr(e, "_taunt_cooldown", None)
                        if cooldown is None:
                            try:
                                # more aggressive personalities taunt more often
                                cooldown = max(3, 8 - int(getattr(e.personality, "aggressiveness", 50) / 12))
                            except Exception:
                                cooldown = 6
                        # only taunt if cooldown expired and within audible range
                        if now - last >= cooldown and dist <= 6:
                            # choose situation-aware taunt
                            situation = "attack"
                            try:
                                if getattr(e, "hp", getattr(e, "max_hp", 1)) <= max(1, int(0.3 * getattr(e, "max_hp", 1))):
                                    situation = "low_hp"
                                elif dist <= 2:
                                    situation = "attack"
                                else:
                                    situation = "defend"
                            except Exception:
                                situation = "attack"

                            taunt = None
                            
                            # Check if this is a creature (non-sentient beast)
                            try:
                                if getattr(e, 'is_creature', False) or getattr(e, 'is_massive', False):
                                    from jedi_fugitive.game.personality import get_massive_creature_taunt
                                    creature_name = getattr(e, 'name', 'unknown').lower()
                                    taunt = get_massive_creature_taunt(creature_name, situation)
                            except Exception:
                                pass
                            
                            # Regular enemy personality taunts (only for sentient enemies)
                            if not taunt and e.personality is not None:
                                try:
                                    # Pass game context for environmental and situational awareness
                                    taunt = e.personality.get_taunt(situation, game.player, game)
                                except Exception:
                                    taunt = None

                            # fallback to contextual taunts with environment awareness
                            if not taunt:
                                try:
                                    from jedi_fugitive.game.personality import get_contextual_taunt
                                    taunt = get_contextual_taunt(game.player, situation, game)
                                except Exception:
                                    pass
                            
                            # Ultimate fallback to basic taunts
                            if not taunt:
                                try:
                                    taunt = random.choice(ENEMY_TAUNTS.get(situation, ["..."]))
                                except Exception:
                                    taunt = "..."

                            # One taunt every few turns across ALL enemies: with a squad around you
                            # taunts were ~a quarter of all messages and the main source of stress.
                            _tnow = getattr(game, 'turn_count', 0)
                            if _tnow - getattr(game, '_last_global_taunt', -99) >= 4:
                                game._last_global_taunt = _tnow
                                # post the taunt
                                try:
                                    # include a short prefix sometimes for flavor
                                    prefix = f"{getattr(e,'name','Enemy')}: "
                                    game.ui.messages.add(prefix + taunt)
                                except Exception:
                                    pass

                                # increase player stress modestly when taunted
                                try:
                                    # stronger taunts from officers or inquisitors
                                    taunt_stress = 5
                                    try:
                                        et = getattr(e, 'type', None)
                                        from jedi_fugitive.game.enemy import EnemyType
                                        if et == getattr(EnemyType, 'INQUISITOR', None):
                                            taunt_stress = 20
                                    except Exception:
                                        # fallback to name-based heuristic
                                        if 'officer' in (getattr(e, 'name', '') or '').lower():
                                            taunt_stress = 15
                                    # apply stress via helper so resilience is respected
                                    try:
                                        added = game.player.add_stress(taunt_stress, source='taunt')
                                    except Exception:
                                        added = taunt_stress
                                    try:
                                        if getattr(game.ui, 'messages', None):
                                            game.ui.messages.add(f"(Stress +{added})")
                                    except Exception:
                                        pass
                                except Exception:
                                    pass

                            # record last taunt turn on enemy
                            try:
                                e._last_taunt_turn = now
                            except Exception:
                                pass
                except Exception:
                    pass

                # If this enemy has a patrol route and hasn't spotted the player yet,
                # follow the patrol instead of moving directly toward the player.
                try:
                    patrol = getattr(e, 'patrol_points', None)
                    if patrol and not getattr(e, '_has_spotted', False):
                        # ensure an index exists
                        try:
                            idx = int(getattr(e, '_patrol_index', 0) or 0)
                        except Exception:
                            idx = 0
                        tgt = patrol[idx % len(patrol)] if patrol else None
                        if tgt:
                            tx, ty = tgt
                            # compute a single-step move toward patrol target
                            move_dx = 1 if tx > getattr(e, 'x', 0) else (-1 if tx < getattr(e, 'x', 0) else 0)
                            move_dy = 1 if ty > getattr(e, 'y', 0) else (-1 if ty < getattr(e, 'y', 0) else 0)
                            # attempt move (only onto floor)
                            try:
                                new_x = getattr(e, 'x', 0) + move_dx
                                new_y = getattr(e, 'y', 0) + move_dy
                                if 0 <= new_y < len(game.game_map) and 0 <= new_x < len(game.game_map[0]):
                                    target_cell = game.game_map[new_x and new_y or new_y][new_x] if False else game.game_map[new_y][new_x]
                                    from jedi_fugitive.game.level import Display
                                    floor_char = getattr(Display, 'FLOOR', '.')
                                    if target_cell == floor_char and not any((getattr(o, 'x', -1) == new_x and getattr(o, 'y', -1) == new_y) for o in game.enemies) and not (new_x == getattr(game.player, 'x', -1) and new_y == getattr(game.player, 'y', -1)):
                                        e.x = new_x
                                        e.y = new_y
                            except Exception:
                                pass
                            # if reached target, advance index
                            try:
                                if getattr(e, 'x', None) == tx and getattr(e, 'y', None) == ty:
                                    try:
                                        e._patrol_index = (idx + 1) % len(patrol)
                                    except Exception:
                                        e._patrol_index = 0
                            except Exception:
                                pass
                            # patrol movement consumes the enemy's action
                            continue
                except Exception:
                    pass

                # Find target based on faction relationships
                target_x, target_y, target_obj, target_type = find_enemy_target(e, game)
                
                # If no target, skip this enemy's turn
                if target_x is None:
                    continue
                
                # Recalculate distance to actual target (not just player)
                target_dist = abs(ex - target_x) + abs(ey - target_y)
                
                # Update dist and px/py to target for movement/attack logic
                px_actual = target_x
                py_actual = target_y
                dist_actual = target_dist
                
                # depth influenced scaling
                depth = max(1, getattr(game, "current_depth", 1))
                try:
                    depth_factor = 1.0 + max(0.0, (depth - 1)) * DEPTH_DIFFICULTY_RATE * float(DIFFICULTY_MULTIPLIER)
                except Exception:
                    depth_factor = 1.0

                attack_range = 1 + (depth // 3)

                # attack if in range (target can be player or enemy)
                if dist_actual <= attack_range:
                    try:
                        atk_stat = int(getattr(e, "attack", 0) * depth_factor)
                    except Exception:
                        atk_stat = int(getattr(e, "attack", 0))
                    
                    # Calculate hit chance against target (player or enemy)
                    try:
                        from jedi_fugitive.game.combat import calculate_hit
                        target_evasion = getattr(target_obj, "evasion", 0)
                        try:
                            from jedi_fugitive.game import form_combat
                            target_evasion += form_combat.evasion_bonus(target_obj)
                        except Exception:
                            pass
                        hit = calculate_hit(atk_stat, target_evasion)
                    except Exception:
                        hit = False
                    
                    if not hit and target_type != 'enemy':
                        try:
                            from jedi_fugitive.game import form_combat
                            form_combat.on_enemy_miss(game, e)
                        except Exception:
                            pass

                    if hit and target_type == 'enemy':
                        # Enemy-vs-Enemy combat
                        try:
                            target_defense = getattr(target_obj, "defense", 0)
                            dmg = max(1, int((getattr(e, "attack", 1) - target_defense) * depth_factor))
                            target_obj.hp -= dmg
                            
                            # Message for inter-faction combat
                            try:
                                if getattr(game.ui, 'messages', None) and random.random() < 0.3:
                                    attacker_name = getattr(e, 'name', 'Enemy')
                                    target_name = getattr(target_obj, 'name', 'Enemy')
                                    game.ui.messages.add(f"#6#[FACTION WAR]#0# {attacker_name} strikes {target_name} for {dmg} damage!")
                            except Exception:
                                pass
                            
                            # Check if target died
                            if getattr(target_obj, 'hp', 0) <= 0:
                                try:
                                    if getattr(game.ui, 'messages', None):
                                        attacker_name = getattr(e, 'name', 'Enemy')
                                        target_name = getattr(target_obj, 'name', 'Enemy')
                                        game.ui.messages.add(f"#2#{attacker_name} defeats {target_name}!#0#")
                                    game.enemies.remove(target_obj)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    elif hit:
                        try:
                            dmg = max(1, int((getattr(e, "attack", 1) - _pdef(game.player)) * depth_factor))
                        except Exception:
                            dmg = max(1, int(getattr(e, "attack", 1) - _pdef(game.player)))
                        try:
                            game.player.hp -= dmg
                            # Track attacker info for death log
                            game.player.last_attacking_enemy = getattr(e, "name", "Enemy")
                            game.player.last_damage_taken = dmg
                            game.player.last_attack_type = "melee attack"
                            
                            # Add combat log entry for non-fatal hits
                            if game.player.hp > 0:
                                try:
                                    if hasattr(game, 'combat_log'):
                                        log_entry = f"Turn {getattr(game, 'turn_count', 0)}: {getattr(e, 'name', 'Enemy')} hits for {dmg} damage (HP: {game.player.hp})"
                                        game.combat_log.append(log_entry)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        try:
                            # Generate immersive combat description with environmental context
                            player_hp = getattr(game.player, "hp", 1)
                            enemy_name = getattr(e, "name", "Enemy")
                            
                            # Determine environment for contextual descriptions
                            current_biome = getattr(game, 'current_biome', 'unknown')
                            in_tomb = getattr(game, 'in_tomb', False)
                            location_context = 'tomb' if in_tomb else current_biome
                            
                            # Use enhanced combat narrator for rich descriptions
                            try:
                                from jedi_fugitive.game.combat_narrator import combat_narrator
                                
                                if player_hp <= 0:
                                    # Generate dramatic death description
                                    death_desc = combat_narrator.get_death_description(
                                        enemy_name, location_context, dmg, "combat"
                                    )
                                    game.ui.messages.add(death_desc)
                                else:
                                    # Generate contextual attack description
                                    attack_desc = combat_narrator.get_attack_description(
                                        enemy_name, dmg, "melee", "torso", location_context
                                    )
                                    game.ui.messages.add(attack_desc)
                                    
                            except Exception:
                                # Fallback to enhanced manual descriptions
                                body_parts = ['arm', 'leg', 'shoulder', 'side', 'chest', 'back']
                                
                                if player_hp <= 0:
                                    # Enhanced fatal blow descriptions with environment
                                    death_messages = [
                                        f"{enemy_name} delivers a fatal strike to your {random.choice(body_parts)}! [{dmg} damage]",
                                        f"{enemy_name}'s attack pierces your {random.choice(body_parts)} - you fall! [{dmg} damage]",
                                        f"A mortal wound to your {random.choice(body_parts)} from {enemy_name}! [{dmg} damage]",
                                        f"{enemy_name} cuts through your {random.choice(body_parts)} - darkness takes you! [{dmg} damage]",
                                        f"In this {location_context}, {enemy_name} delivers your final blow! [{dmg} damage]"
                                    ]
                                    game.ui.messages.add(random.choice(death_messages))
                                elif dmg >= 8:
                                    # Enhanced heavy damage descriptions with dramatic impact
                                    heavy_messages = [
                                        f"{enemy_name} savagely strikes your {random.choice(body_parts)}! [{dmg} damage]",
                                        f"{enemy_name}'s attack tears into your {random.choice(body_parts)}! [{dmg} damage]",
                                        f"A brutal hit to your {random.choice(body_parts)} from {enemy_name}! [{dmg} damage]",
                                        f"{enemy_name} slashes your {random.choice(body_parts)} viciously! [{dmg} damage]",
                                        f"The violence echoes through the {location_context} as {enemy_name} wounds you! [{dmg} damage]",
                                        f"{enemy_name}'s devastating blow crushes your {random.choice(body_parts)}! [{dmg} damage]",
                                        f"A vicious strike from {enemy_name} rends your {random.choice(body_parts)}! [{dmg} damage]",
                                        f"{enemy_name} unleashes a powerful attack on your {random.choice(body_parts)}! [{dmg} damage]",
                                        f"Blood sprays as {enemy_name}'s weapon tears through your {random.choice(body_parts)}! [{dmg} damage]",
                                        f"The force of {enemy_name}'s attack sends pain exploding through your {random.choice(body_parts)}! [{dmg} damage]"
                                    ]
                                    game.ui.messages.add(random.choice(heavy_messages))
                                else:
                                    # Enhanced normal damage descriptions with cinematic flair
                                    hit_messages = [
                                        f"{enemy_name} strikes your {random.choice(body_parts)}. [{dmg} damage]",
                                        f"{enemy_name} hits you in the {random.choice(body_parts)}! [{dmg} damage]",
                                        f"{enemy_name}'s attack wounds your {random.choice(body_parts)}. [{dmg} damage]",
                                        f"You take a hit to the {random.choice(body_parts)} from {enemy_name}! [{dmg} damage]",
                                        f"In the {location_context}, {enemy_name} finds its mark! [{dmg} damage]",
                                        f"{enemy_name}'s blade grazes your {random.choice(body_parts)}. [{dmg} damage]",
                                        f"A swift strike from {enemy_name} catches your {random.choice(body_parts)}! [{dmg} damage]",
                                        f"{enemy_name} lunges forward, cutting your {random.choice(body_parts)}. [{dmg} damage]",
                                        f"Pain flares as {enemy_name} strikes your {random.choice(body_parts)}! [{dmg} damage]",
                                        f"The {location_context} echoes with your cry as {enemy_name} hits! [{dmg} damage]"
                                    ]
                                    game.ui.messages.add(random.choice(hit_messages))
                        except Exception:
                            game.ui.messages.add(f"{e.name} hits you for {dmg}!")
                        if getattr(game.player, "hp", 1) <= 0:
                            try:
                                game.ui.messages.add("You died!")
                            except Exception:
                                pass
                            
                            # Generate comprehensive death log entry
                            try:
                                # Get enemy info for death narrative
                                enemy_name = getattr(game.player, 'last_attacking_enemy', getattr(e, 'name', 'an enemy'))
                                damage = getattr(game.player, 'last_damage_taken', dmg)
                                attack_type = getattr(game.player, 'last_attack_type', 'melee attack')
                                
                                # If no damage info was tracked, use current attack
                                if damage == 0:
                                    damage = dmg
                                    enemy_name = getattr(e, 'name', 'an enemy')
                                
                                # Generate enemy taunt
                                taunt = ""
                                try:
                                    if hasattr(e, 'personality') and e.personality:
                                        taunt = e.personality.get_taunt('attack', game.player)
                                    else:
                                        taunt = random.choice(ENEMY_TAUNTS.get('attack', ['You have fallen!']))
                                except Exception:
                                    taunt = "You have been defeated!"
                                
                                # Generate body fate based on location
                                body_fate = ""
                                try:
                                    in_tomb = getattr(game, 'in_tomb', False)
                                    if in_tomb:
                                        tomb_floor = getattr(game, 'tomb_floor', 1)
                                        tomb_name = "the Sith Tomb"
                                        body_fate = f"Your corpse will rot in the darkness of {tomb_name} Level {tomb_floor}, never to be recovered. The dark side claims another victim."
                                    else:
                                        biome = getattr(game, 'current_biome', 'unknown wasteland')
                                        if biome == 'desert':
                                            body_fate = "Your body lies broken among the desert sands, to be buried by the shifting dunes and forgotten by time."
                                        elif biome == 'forest':
                                            body_fate = "Your corpse will feed the scavengers in the dense forest, becoming one with the wilderness."
                                        elif biome == 'mountains':
                                            body_fate = "Your broken form rests on the mountain slopes, a grim warning to those who dare venture here."
                                        elif biome == 'crash_site':
                                            body_fate = "Your body lies among the wreckage of the crash site, another casualty of this ill-fated journey."
                                        else:
                                            body_fate = f"Your remains are abandoned in the {biome}, destined to be lost to the elements."
                                except Exception:
                                    body_fate = "Your body lies where it fell, abandoned and forgotten."
                                
                                # Add comprehensive death entry to travel log
                                death_entry = f"[DEATH] Struck down by {enemy_name}'s {attack_type} for {damage} damage. {body_fate} The {enemy_name} taunts: '{taunt}'"
                                turn = getattr(game, 'turn_count', 0)
                                game.player.add_log_entry(death_entry, turn)
                            except Exception as ex:
                                # Fallback if death logging fails
                                try:
                                    turn = getattr(game, 'turn_count', 0)
                                    game.player.add_log_entry(f"[DEATH] Fell in combat.", turn)
                                except Exception:
                                    pass
                            
                            # Set death metadata for post-game display
                            try:
                                game.death = True
                                game.death_cause = 'enemy attack'
                                game.death_biome = getattr(game, 'current_biome', 'unknown')
                                game.death_pos = (getattr(game.player, 'x', None), getattr(game.player, 'y', None))
                            except Exception:
                                pass
                            game.running = False
                            return
                    else:
                        try:
                            enemy_name = getattr(e, 'name', 'Enemy')
                            biome = getattr(game, 'current_biome', 'unknown')
                            
                            # Environmental miss descriptions
                            miss_messages = {
                                'desert': [
                                    f"{enemy_name}'s attack goes wide, striking only sand!",
                                    f"The desert wind deflects {enemy_name}'s blow!",
                                    f"{enemy_name} stumbles in the shifting sand and misses!"
                                ],
                                'forest': [
                                    f"{enemy_name}'s strike hits a tree trunk instead!",
                                    f"Forest shadows confuse {enemy_name}'s aim!",
                                    f"{enemy_name} gets tangled in undergrowth and misses!"
                                ],
                                'mountains': [
                                    f"{enemy_name} loses footing on the rocky terrain!",
                                    f"The mountain wind throws off {enemy_name}'s attack!",
                                    f"{enemy_name} strikes stone instead of flesh!"
                                ],
                                'tomb': [
                                    f"{enemy_name}'s attack is swallowed by the tomb's darkness!",
                                    f"Ancient dust clouds {enemy_name}'s vision!",
                                    f"{enemy_name} strikes a stone pillar in the gloom!"
                                ]
                            }
                            
                            messages = miss_messages.get(biome, [f"{enemy_name} missed you."])
                            game.ui.messages.add(random.choice(messages))
                        except Exception:
                            pass
                else:
                    # Enhanced AI: coordinated charging, behavior-based tactics, retreat, flanking
                    dx, dy = 0, 0
                    
                    try:
                        # Get enemy's behavioral style
                        behavior = ai_get_enemy_behavior(e)
                        
                        # Cache AI state for batch processing optimization  
                        if not hasattr(game, '_ai_cache'):
                            game._ai_cache = {}
                        
                        # COORDINATED CHARGE: if 3+ enemies nearby, all charge together!
                        cache_key = f"charge_{ex}_{ey}"
                        if cache_key not in game._ai_cache:
                            game._ai_cache[cache_key] = ai_should_charge(e, game)
                        
                        if game._ai_cache[cache_key]:
                            # Direct aggressive movement toward target (can be player or enemy)
                            if px_actual > ex:
                                dx = 1
                            elif px_actual < ex:
                                dx = -1
                            if py_actual > ey:
                                dy = 1
                            elif py_actual < ey:
                                dy = -1
                            # Message on first charge
                            try:
                                if not getattr(e, '_charge_announced', False) and random.random() < 0.3:
                                    e._charge_announced = True
                                    if getattr(game.ui, 'messages', None):
                                        target_name = "you" if target_type == 'player' else getattr(target_obj, 'name', 'enemy')
                                        game.ui.messages.add(f"{getattr(e,'name','Enemies')} coordinate an assault on {target_name}!")
                            except Exception:
                                pass
                        
                        # Check if should retreat due to low HP
                        elif ai_should_retreat(e, game):
                            dx, dy = ai_find_retreat_direction(e, game)
                            try:
                                if getattr(game.ui, 'messages', None) and random.random() < 0.3:
                                    game.ui.messages.add(f"{getattr(e,'name','Enemy')} falls back!")
                            except Exception:
                                pass
                        
                        # SNIPER: stay at long range from target, don't approach
                        elif behavior == 'sniper':
                            if dist_actual < 5:
                                # Move away from target to maintain distance
                                dx, dy = ai_find_retreat_direction(e, game)
                            else:
                                # Hold position or sidestep
                                if random.random() < 0.4:
                                    dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                        
                        # AGGRESSIVE/BRAWLER: always charge directly toward target, ignore tactics
                        elif behavior == 'aggressive':
                            if px_actual > getattr(e, "x", 0):
                                dx = 1
                            elif px_actual < getattr(e, "x", 0):
                                dx = -1
                            if dx == 0:
                                if py_actual > getattr(e, "y", 0):
                                    dy = 1
                                elif py_actual < getattr(e, "y", 0):
                                    dy = -1
                        
                        # FLANKER: always try to attack from sides (of target)
                        elif behavior == 'flanker':
                            if dist_actual > 2:
                                # For flanking, still use AI functions but they'll use actual target
                                dx, dy = ai_find_flanking_position(e, game)
                            else:
                                # Close enough, move in toward target
                                if px_actual > getattr(e, "x", 0):
                                    dx = 1
                                elif px_actual < getattr(e, "x", 0):
                                    dx = -1
                                if dx == 0:
                                    if py_actual > getattr(e, "y", 0):
                                        dy = 1
                                    elif py_actual < getattr(e, "y", 0):
                                        dy = -1
                        
                        # RANGED: maintain preferred distance from target
                        elif behavior == 'ranged' or hasattr(e, 'attempt_ranged_shot') or getattr(e, 'preferred_range', 0) > 0:
                            preferred_dist = getattr(e, 'preferred_range', 4)
                            dx, dy = ai_maintain_range(e, game, preferred_dist)
                        
                        # Flanking logic: if 2+ allies nearby and not adjacent to target, try flanking
                        elif dist_actual > 2 and ai_count_nearby_allies(e, game, radius=5) >= 2:
                            if random.random() < 0.4:  # 40% chance to flank instead of direct approach
                                dx, dy = ai_find_flanking_position(e, game)
                        
                        # Default: direct pursuit toward target (use target positions)
                        else:
                            if px_actual > ex:
                                dx = 1
                            elif px_actual < ex:
                                dx = -1
                            if dx == 0:
                                if py_actual > ey:
                                    dy = 1
                                elif py_actual < ey:
                                    dy = -1
                    except Exception:
                        # Fallback to simple pursuit toward target
                        try:
                            if px_actual > getattr(e, "x", 0):
                                dx = 1
                            elif px_actual < getattr(e, "x", 0):
                                dx = -1
                            if dx == 0:
                                if py_actual > getattr(e, "y", 0):
                                    dy = 1
                                elif py_actual < getattr(e, "y", 0):
                                    dy = -1
                        except Exception:
                            dx, dy = 0, 0

                    # Deeper levels grant occasional extra movement step
                    steps = 1
                    try:
                        prob = min(0.5, 0.05 * depth * float(DIFFICULTY_MULTIPLIER))
                        if random.random() < prob:
                            steps = 2
                    except Exception:
                        steps = 1

                    # Execute movement steps
                    for _ in range(steps):
                        try:
                            new_x = getattr(e, "x", 0) + dx
                            new_y = getattr(e, "y", 0) + dy
                            # Use enhanced pathfinding helper
                            if ai_can_move_to(game, new_x, new_y, exclude_enemy=e):
                                e.x = new_x
                                e.y = new_y
                        except Exception:
                            # ignore movement failure for this step
                            pass

            except Exception:
                pass  # Close the try block for each enemy defensively

        # After enemy loop: reduce stress on level up / gaining abilities and build confidence
        try:
            cur_level = getattr(game.player, "level", 1)
            if cur_level > getattr(game, "last_level", cur_level):
                # Increased stress reduction - represents growing confidence and mastery
                game.player.reduce_stress(20, source='victory')  # Increased from 10
                game.last_level = cur_level
            cur_abil_count = 0
            try:
                cur_abil_count = len(game.player.get_available_abilities() or [])
            except Exception:
                cur_abil_count = getattr(game, "last_ability_count", 0)
            if cur_abil_count > getattr(game, "last_ability_count", cur_abil_count):
                # Increased stress reduction per gained ability
                reduce_amt = 10 * (cur_abil_count - getattr(game, "last_ability_count", cur_abil_count))  # Increased from 5
                game.player.reduce_stress(reduce_amt, source='victory')
                game.last_ability_count = cur_abil_count
        except Exception:
            pass
        
        # Track successful combat for confidence building
        try:
            enemies_defeated_this_turn = 0
            for e in list(game.enemies):
                if getattr(e, 'hp', 1) <= 0 and not getattr(e, '_counted_for_confidence', False):
                    enemies_defeated_this_turn += 1
                    e._counted_for_confidence = True
            
            if enemies_defeated_this_turn > 0:
                # Build confidence with each victory
                game.player._successful_combats = getattr(game.player, '_successful_combats', 0) + enemies_defeated_this_turn
                # Small stress reduction per kill (scales with confidence)
                stress_reduction = min(5, enemies_defeated_this_turn * 2)
                game.player.reduce_stress(stress_reduction, source='victory')
        except Exception:
            pass
            
        # Clear AI caches after processing to prevent stale data
        try:
            # Clear coordination cache
            if hasattr(game, '_ai_cache'):
                game._ai_cache.clear()
            # Clear pathfinding caches (but keep terrain cache for next turn)
            if hasattr(game, '_flanking_cache'):
                game._flanking_cache.clear()
            if hasattr(game, '_range_cache'):
                game._range_cache.clear()
        except Exception:
            pass

    except Exception:
        try:
            game.ui.messages.add("Enemy processing error.")
        except Exception:
            pass
