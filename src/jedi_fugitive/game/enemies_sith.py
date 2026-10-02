"""Sith-era enemies: factories that produce Enemy instances compatible with
the existing `jedi_fugitive.game.enemy.Enemy` class.

These are lightweight, data-driven factories that attach small custom
`take_turn(game)` hooks where needed. Keep changes non-invasive so the
main enemy processing loop continues to work.
"""

from jedi_fugitive.game import logger
log = logger  # the Logger itself (logger.log is a bound method with no .error/.info)
from typing import Optional
import random
from jedi_fugitive.game.enemy import Enemy
from jedi_fugitive.game.personality import EnemyPersonality
from jedi_fugitive.game import force_abilities


def _floor():
    from jedi_fugitive.game.level import Display  # local: level imports enemy
    return Display.FLOOR


def _attach_take_turn(e: Enemy, fn):
    # Simply assign a callable that accepts one arg (game). process_enemies will call it.
    try:
        e.take_turn = lambda game, _fn=fn: _fn(game, e)
    except Exception as e1:
        if log:
            log.exception("Failed to attach take_turn (lambda _fn)", exc_info=e1)
        try:
            e.take_turn = lambda game: fn(game, e)
        except Exception as e2:
            if log:
                log.exception("Failed to attach take_turn (lambda fallback)", exc_info=e2)


def create_sith_acolyte(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Sith Acolyte", 14 + level * 2, 6 + level, 2 + level//3, 5, EnemyPersonality(), 20, x, y, level=level)
    e.symbol = 'a'  # Acolyte
    e.color = 1  # Red
    e.faction = 'Sith Empire'  # Faction assignment
    return e


def create_sith_warrior(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Sith Warrior", 28 + level * 6, 12 + int(level * 1.5), 6 + level//2, 6, EnemyPersonality(), 60, x, y, level=level)
    e.symbol = 'W'  # Warrior
    e.color = 1  # Red
    e.faction = 'Sith Empire'  # Faction assignment
    return e


def create_sith_assassin(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    # highly evasive short-lived assassin; special: first strike bonus and occasional vanish
    e = Enemy("Sith Assassin", 12 + level * 2, 10 + level, 2 + level//4, 20 + level, EnemyPersonality(), 80, x, y, level=level)
    e.symbol = 'A'  # Assassin
    e.color = 5  # Magenta/Purple
    e.faction = 'Sith Empire'  # Faction assignment

    def assassin_ai(game, self):
        try:
            # attempt to vanish (simulate stealth) with small chance
            if random.random() < 0.12 and not getattr(self, '_is_stealthed', False):
                try:
                    self._is_stealthed = True
                    if getattr(game.ui, 'messages', None):
                        game.ui.messages.add(f"{self.name} melts into the shadows!")
                except Exception as e:
                    if log:
                        log.exception("Assassin vanish error", exc_info=e)

            # if stealthed, have a chance to teleport behind player and strike
            player = getattr(game, 'player', None)
            if getattr(self, '_is_stealthed', False) and player is not None:
                if random.random() < 0.35:
                    try:
                        # place adjacent to player if tile is floor (best-effort)
                        px, py = getattr(player, 'x', 0), getattr(player, 'y', 0)
                        # candidate positions around player
                        cand = [(px+1,py),(px-1,py),(px,py+1),(px,py-1)]
                        for nx, ny in cand:
                            if 0 <= ny < len(game.game_map) and 0 <= nx < len(game.game_map[0]) and game.game_map[ny][nx] == _floor():
                                # avoid colliding with player or other enemies
                                if not any(getattr(o,'x',None)==nx and getattr(o,'y',None)==ny for o in game.enemies):
                                    self.x = nx; self.y = ny
                                    break
                    except Exception as e:
                        if log:
                            log.exception("Assassin teleport error", exc_info=e)
                    # perform a heavy attack on player
                    try:
                        dmg = max(1, int(getattr(self, 'attack', 5) * 1.4))
                        if hasattr(player, 'hp'):
                            player.hp = max(0, getattr(player, 'hp', 0) - dmg)
                        if getattr(game.ui, 'messages', None):
                            game.ui.messages.add(f"{self.name} ambushes you for {dmg} damage!")
                    except Exception as e:
                        if log:
                            log.exception("Assassin ambush error", exc_info=e)
                    # break stealth after attack
                    try:
                        self._is_stealthed = False
                    except Exception as e:
                        if log:
                            log.exception("Assassin break stealth error", exc_info=e)
                    return True

            return False
        except Exception as e:
            if log:
                log.exception("Assassin AI error", exc_info=e)
            return False

    _attach_take_turn(e, assassin_ai)
    return e


def create_sith_sorcerer(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Sith Sorcerer", 18 + level * 3, 6 + level, 3 + level//3, 8, EnemyPersonality(), 100, x, y, level=level)
    e.symbol = 's'  # Sorcerer
    e.color = 5  # Magenta/Purple
    e.faction = 'Sith Empire'  # Faction assignment
    # give a couple of force abilities for ranged behavior
    try:
        e.force_abilities = {
            'lightning': force_abilities.ForceLightning(damage=6 + level),
            'reveal': force_abilities.ForceReveal(duration=6, bonus=3)
        }
        # sorcerer has a modest pool
        e.force_points = 3 + level//2
    except Exception as e:
        if log:
            log.exception("Failed to assign force abilities to Sith Sorcerer", exc_info=e)
        e.force_abilities = {}

    def sorcerer_ai(game, self):
        try:
            player = getattr(game, 'player', None)
            if not player:
                return False
            dist = abs(getattr(player,'x',0)-getattr(self,'x',0)) + abs(getattr(player,'y',0)-getattr(self,'y',0))
            # attempt lightning if in range and available
            fa = getattr(self, 'force_abilities', {}) or {}
            lightning = fa.get('lightning')
            if lightning and dist <= 8:
                last = getattr(self, '_ability_last_used', {}).get(getattr(lightning,'name',str(lightning)), -9999)
                cooldown = getattr(lightning, 'cooldown', 3)
                if getattr(game, 'turn_count', 0) - last >= cooldown:
                    try:
                        used = lightning.use(self, player, game.game_map, getattr(game.ui,'messages', None), getattr(self,'level',1))
                        if used:
                            try: self._ability_last_used[getattr(lightning,'name',str(lightning))] = getattr(game,'turn_count',0)
                            except Exception: pass
                            return True
                    except Exception as e:
                        if log:
                            log.exception("Sith Sorcerer AI error", exc_info=e)

            # else possibly reveal to increase LOS for itself
            reveal = fa.get('reveal')
            if reveal:
                last = getattr(self, '_ability_last_used', {}).get(getattr(reveal,'name',str(reveal)), -9999)
                cooldown = getattr(reveal, 'cooldown', 4)
                if getattr(game, 'turn_count', 0) - last >= cooldown:
                    try:
                        # Check if enemy has enough force points before attempting
                        cost = getattr(reveal, 'base_cost', 1)
                        enemy_fp = getattr(self, 'force_points', 0)
                        
                        if enemy_fp >= cost:
                            # Use null messages to prevent spam to player
                            null_messages = type('NullMessages', (), {'add': lambda self, msg: None})()
                            used = reveal.use(self, None, game.game_map, null_messages, getattr(self,'level',1))
                            if used:
                                try: self._ability_last_used[getattr(reveal,'name',str(reveal))] = getattr(game,'turn_count',0)
                                except Exception: pass
                                return True
                        # If not enough force points, just skip silently
                    except Exception:
                        pass

            return False
        except Exception:
            return False

    _attach_take_turn(e, sorcerer_ai)
    return e


def create_sith_wardroid(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Sith WarDroid", 32 + level * 8, 10 + level//1, 8 + level//2, 3, EnemyPersonality(), 120, x, y, level=level)
    e.symbol = 'd'  # Droid
    e.color = 7  # White/Gray
    e.faction = 'Sith Empire'  # Faction assignment
    # war droids are slow but tanky; no special AI needed
    return e


def create_tukata(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Tuk'ata", 12 + level * 3, 8 + level//1, 1 + level//4, 12, EnemyPersonality(), 40, x, y, level=level)
    e.symbol = 'w'  # Wolf/beast
    e.color = 1  # Red
    e.faction = 'Sith Empire'  # Faction assignment (Sith war beasts)
    # fast: occasionally move two steps; reuse default behavior but mark aggressiveness
    return e


def create_terentatek(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Terentatek", 80 + level * 20, 20 + level * 2, 10 + level//1, 2, EnemyPersonality(), 400, x, y, level=level)
    e.symbol = 'm'  # Monster
    e.color = 1  # Red
    e.faction = 'Sith Empire'  # Faction assignment (Sith-bred creatures)
    e.is_massive = True
    return e


def create_sith_trooper(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Sith Trooper", 16 + level * 3, 9 + level, 3 + level//2, 6, EnemyPersonality(), 30, x, y, level=level)
    e.symbol = 'T'  # Trooper
    e.color = 1  # Red
    e.faction = 'Sith Empire'  # Faction assignment
    return e


def create_sith_officer(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Sith Officer", 22 + level * 4, 10 + level, 5 + level//2, 8, EnemyPersonality(), 120, x, y, level=level)
    e.symbol = 'O'  # Officer
    e.color = 3  # Yellow
    e.faction = 'Sith Empire'  # Faction assignment

    def officer_ai(game, self):
        try:
            # Occasionally buff a nearby ally's attack (non-stackable, short-lived)
            if random.random() < 0.18:
                for oth in list(getattr(game, 'enemies', []) or []):
                    try:
                        if oth is self:
                            continue
                        if abs(getattr(oth,'x',0)-getattr(self,'x',0)) + abs(getattr(oth,'y',0)-getattr(self,'y',0)) <= 3:
                            # apply a one-time buff via attribute
                            oth._temp_attack_buff = max(getattr(oth,'_temp_attack_buff', 0), 3 + self.level//2)
                            if getattr(game.ui, 'messages', None):
                                game.ui.messages.add(f"{self.name} rallies {oth.name}!")
                            return True
                    except Exception:
                        continue
            return False
        except Exception:
            return False

    _attach_take_turn(e, officer_ai)
    return e


def create_sith_lord(level: int = 5, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Sith Lord", 70 + level * 12, 18 + level * 2, 8 + level, 6, EnemyPersonality(), 800, x, y, level=level)
    e.symbol = 'L'  # Lord
    e.color = 1  # Red
    e.faction = 'Sith Empire'  # Faction assignment
    e.is_boss = True
    # grant boss-level force abilities
    try:
        e.force_abilities = {
            'lightning': force_abilities.ForceLightning(damage=12 + level * 2),
            'heal': force_abilities.ForceHeal(amount=12 + level * 2),
            'pushpull': force_abilities.ForcePushPull()
        }
        e.force_points = 8 + level
    except Exception:
        e.force_abilities = {}

    return e


def create_dread_inquisitor(level: int = 6, x: int = 0, y: int = 0) -> Enemy:
    """A feared inquisitor who specializes in draining Force and unleashing brutal lightning."""
    e = Enemy("Dread Inquisitor", 90 + level * 18, 20 + level * 2, 10 + level, 10, EnemyPersonality(), 1200, x, y, level=level)
    e.symbol = 'I'  # Inquisitor
    e.color = 5  # Magenta/Purple
    e.faction = 'Sith Empire'  # Faction assignment
    e.is_boss = True
    try:
        e.force_abilities = {
            'lightning': force_abilities.ForceLightning(damage=18 + level * 3),
            'heal': force_abilities.ForceHeal(amount=10 + level * 2),
        }
        e.force_points = 10 + level
    except Exception:
        e.force_abilities = {}

    def inquisitor_ai(game, self):
        try:
            player = getattr(game, 'player', None)
            if not player:
                return False
            dist = abs(getattr(player,'x',0)-getattr(self,'x',0)) + abs(getattr(player,'y',0)-getattr(self,'y',0))
            fa = getattr(self, 'force_abilities', {}) or {}
            # prefer lightning when in range
            lightning = fa.get('lightning')
            if lightning and dist <= 8:
                last = getattr(self, '_ability_last_used', {}).get(getattr(lightning,'name',str(lightning)), -9999)
                cooldown = getattr(lightning, 'cooldown', 3)
                if getattr(game, 'turn_count', 0) - last >= cooldown:
                    try:
                        used = lightning.use(self, player, game.game_map, getattr(game.ui,'messages', None), getattr(self,'level',1))
                        if used:
                            try: self._ability_last_used[getattr(lightning,'name',str(lightning))] = getattr(game,'turn_count',0)
                            except Exception: pass
                            return True
                    except Exception:
                        pass

            # otherwise attempt a force-drain: steal a force point and increase player's stress
            # Only if player can see the enemy and within reasonable range
            if getattr(game, 'turn_count', 0) % 3 == 0 and dist <= 8:
                try:
                    # Check if player can see this enemy (line of sight)
                    player_can_see_enemy = False
                    try:
                        if hasattr(game, 'is_visible'):
                            player_can_see_enemy = game.is_visible(getattr(self, 'x', 0), getattr(self, 'y', 0))
                        elif hasattr(game, 'player') and hasattr(game.player, 'los_radius'):
                            # Fallback: use simple distance check with LOS radius
                            player_can_see_enemy = dist <= getattr(game.player, 'los_radius', 6)
                    except Exception:
                        # If visibility check fails, assume player can't see enemy
                        player_can_see_enemy = False
                    
                    if player_can_see_enemy and hasattr(player, 'force_points') and player.force_points > 0:
                        player.force_points = max(0, player.force_points - 1)
                        # Inquisitor regains a small amount
                        self.force_points = getattr(self, 'force_points', 0) + 1
                        if getattr(game.ui, 'messages', None):
                            game.ui.messages.add(f"{self.name} drains your Force! You lose 1 Force point.")
                        return True
                except Exception:
                    pass

            # fallback: no special action
            return False
        except Exception:
            return False

    _attach_take_turn(e, inquisitor_ai)
    return e


def create_sith_inquisitor(level: int = 7, x: int = 0, y: int = 0) -> Enemy:
    """The ultimate challenge: a Sith Lord who guards the legendary weapon in the Sith Keep."""
    # Canon Sith Lord names from various eras
    sith_lord_names = [
        "Darth Malak",
        "Darth Revan", 
        "Darth Bane",
        "Darth Nihilus",
        "Darth Sion",
        "Darth Traya",
        "Darth Malgus",
        "Darth Marr",
        "Darth Nox",
        "Darth Thanaton",
        "Darth Baras",
        "Darth Zash",
        "Darth Jadus",
        "Darth Vindican"
    ]
    
    sith_name = random.choice(sith_lord_names)
    base_hp = 100 + level * 20
    e = Enemy(sith_name, int(base_hp * 2.5), 22 + level * 2, 12 + level, 8, EnemyPersonality(), 2000, x, y, level=level)
    e.symbol = 'U'  # Changed from 'L' to 'U' to avoid Lightsaber conflict
    e.faction = 'Sith Empire'  # Faction assignment
    e.is_boss = True
    try:
        e.force_abilities = {
            'lightning': force_abilities.ForceLightning(damage=20 + level * 3),
            'heal': force_abilities.ForceHeal(amount=15 + level * 2),
            'pushpull': force_abilities.ForcePushPull()
        }
        e.force_points = 12 + level
    except Exception:
        e.force_abilities = {}

    def inquisitor_ai(game, self):
        try:
            player = getattr(game, 'player', None)
            if not player:
                return False
            dist = abs(getattr(player,'x',0)-getattr(self,'x',0)) + abs(getattr(player,'y',0)-getattr(self,'y',0))
            fa = getattr(self, 'force_abilities', {}) or {}
            
            # Aggressive lightning attacks
            lightning = fa.get('lightning')
            if lightning and dist <= 10:
                last = getattr(self, '_ability_last_used', {}).get(getattr(lightning,'name',str(lightning)), -9999)
                cooldown = getattr(lightning, 'cooldown', 3)
                if getattr(game, 'turn_count', 0) - last >= cooldown:
                    try:
                        used = lightning.use(self, player, game.game_map, getattr(game.ui,'messages', None), getattr(self,'level',1))
                        if used:
                            try: self._ability_last_used[getattr(lightning,'name',str(lightning))] = getattr(game,'turn_count',0)
                            except Exception: pass
                            return True
                    except Exception:
                        pass

            # Heal when wounded
            if self.hp < self.max_hp * 0.4:
                heal = fa.get('heal')
                if heal:
                    last = getattr(self, '_ability_last_used', {}).get(getattr(heal,'name',str(heal)), -9999)
                    cooldown = getattr(heal, 'cooldown', 5)
                    if getattr(game, 'turn_count', 0) - last >= cooldown:
                        try:
                            used = heal.use(self, self, game.game_map, getattr(game.ui,'messages', None), getattr(self,'level',1))
                            if used:
                                try: self._ability_last_used[getattr(heal,'name',str(heal))] = getattr(game,'turn_count',0)
                                except Exception: pass
                                return True
                        except Exception:
                            pass

            # Force drain every 4 turns (only if player can see the enemy)
            if getattr(game, 'turn_count', 0) % 4 == 0 and dist <= 10:
                try:
                    # Check if player can see this enemy (line of sight)
                    player_can_see_enemy = False
                    try:
                        if hasattr(game, 'is_visible'):
                            player_can_see_enemy = game.is_visible(getattr(self, 'x', 0), getattr(self, 'y', 0))
                        elif hasattr(game, 'player') and hasattr(game.player, 'los_radius'):
                            # Fallback: use simple distance check with LOS radius
                            player_can_see_enemy = dist <= getattr(game.player, 'los_radius', 6)
                    except Exception:
                        # If visibility check fails, assume player can't see enemy
                        player_can_see_enemy = False
                    
                    if player_can_see_enemy and hasattr(player, 'force_points') and player.force_points > 0:
                        player.force_points = max(0, player.force_points - 2)
                        self.force_points = getattr(self, 'force_points', 0) + 2
                        if getattr(game.ui, 'messages', None):
                            game.ui.messages.add(f"{self.name} siphons your Force essence! You lose 2 Force points.")
                        return True
                except Exception:
                    pass

            # If no force abilities were used, fall back to normal attack behavior
            # This ensures the Sith will always try to attack if close enough
            if dist <= 2:  # Adjacent or close
                # Let the default enemy AI handle movement and attacks
                return False  # Return False to allow default AI to take over
            
            # Try to move closer to player for combat
            px, py = getattr(player, 'x', 0), getattr(player, 'y', 0)
            sx, sy = getattr(self, 'x', 0), getattr(self, 'y', 0)
            
            # Simple pathfinding toward player
            dx = 1 if px > sx else (-1 if px < sx else 0)
            dy = 1 if py > sy else (-1 if py < sy else 0)
            
            new_x, new_y = sx + dx, sy + dy
            
            # Check if we can move there
            try:
                if (hasattr(game, 'game_map') and 
                    0 <= new_y < len(game.game_map) and 
                    0 <= new_x < len(game.game_map[0]) and
                    game.game_map[new_y][new_x] in ['.', 'H', '?', '+']):
                    
                    # Check if position is not occupied by another enemy
                    position_free = True
                    if hasattr(game, 'enemies'):
                        for other_enemy in game.enemies:
                            if (other_enemy != self and 
                                getattr(other_enemy, 'x', -1) == new_x and 
                                getattr(other_enemy, 'y', -1) == new_y):
                                position_free = False
                                break
                    
                    if position_free:
                        self.x, self.y = new_x, new_y
                        return True
            except Exception:
                pass

            return False
        except Exception:
            return False

    _attach_take_turn(e, inquisitor_ai)
    return e


def create_obsidian_regent(level: int = 7, x: int = 0, y: int = 0) -> Enemy:
    """An ancient regent who manipulates the battlefield and summons brief guardians."""
    e = Enemy("Obsidian Regent", 120 + level * 22, 14 + level * 2, 12 + level, 6, EnemyPersonality(), 1600, x, y, level=level)
    e.symbol = 'R'  # Regent
    e.color = 6  # Cyan
    e.is_boss = True
    try:
        e.force_abilities = {
            'reveal': force_abilities.ForceReveal(duration=5, bonus=4),
            'heal': force_abilities.ForceHeal(amount=12 + level * 2)
        }
        e.force_points = 6 + level
    except Exception:
        e.force_abilities = {}

    def regent_ai(game, self):
        try:
            # occasionally summon a minor guardian (warrior) adjacent
            if random.random() < 0.08:
                try:
                    # find adjacent free tile
                    for dx in (-1,0,1):
                        for dy in (-1,0,1):
                            nx, ny = getattr(self,'x',0)+dx, getattr(self,'y',0)+dy
                            if 0 <= ny < len(game.game_map) and 0 <= nx < len(game.game_map[0]) and game.game_map[ny][nx] == _floor():
                                minion = create_sith_warrior(level=max(1, int(self.level/2)))
                                minion.x, minion.y = nx, ny
                                try: game.enemies.append(minion)
                                except Exception: pass
                                if getattr(game.ui,'messages',None):
                                    game.ui.messages.add(f"{self.name} summons a guardian!")
                                return True
                except Exception:
                    pass
            # otherwise occasionally cast reveal to increase its awareness
            fa = getattr(self, 'force_abilities', {}) or {}
            reveal = fa.get('reveal')
            if reveal and random.random() < 0.12:
                last = getattr(self, '_ability_last_used', {}).get(getattr(reveal,'name',str(reveal)), -9999)
                cooldown = getattr(reveal, 'cooldown', 4)
                if getattr(game,'turn_count',0) - last >= cooldown:
                    try:
                        # Check if enemy has enough force points before attempting
                        cost = getattr(reveal, 'base_cost', 1)
                        enemy_fp = getattr(self, 'force_points', 0)
                        
                        if enemy_fp >= cost:
                            # Use null messages to prevent spam to player
                            null_messages = type('NullMessages', (), {'add': lambda self, msg: None})()
                            used = reveal.use(self, None, game.game_map, null_messages, getattr(self,'level',1))
                            if used:
                                try: self._ability_last_used[getattr(reveal,'name',str(reveal))] = getattr(game,'turn_count',0)
                                except Exception: pass
                                return True
                        # If not enough force points, just skip silently
                    except Exception:
                        pass
            # If no special abilities were used, fall back to normal combat
            px, py = getattr(game.player, 'x', 0), getattr(game.player, 'y', 0)
            sx, sy = getattr(self, 'x', 0), getattr(self, 'y', 0)
            dist = abs(px - sx) + abs(py - sy)  # Recalculate distance
            
            if dist <= 2:  # Close combat range
                return False  # Let default AI handle movement and attacks
            
            # Try to move closer to player
            
            # Simple movement toward player
            dx = 1 if px > sx else (-1 if px < sx else 0)
            dy = 1 if py > sy else (-1 if py < sy else 0)
            
            new_x, new_y = sx + dx, sy + dy
            
            # Check if we can move there
            try:
                if (hasattr(game, 'game_map') and 
                    0 <= new_y < len(game.game_map) and 
                    0 <= new_x < len(game.game_map[0]) and
                    game.game_map[new_y][new_x] in ['.', 'H', '?', '+']):
                    
                    # Check if position is not occupied
                    position_free = True
                    if hasattr(game, 'enemies'):
                        for other_enemy in game.enemies:
                            if (other_enemy != self and 
                                getattr(other_enemy, 'x', -1) == new_x and 
                                getattr(other_enemy, 'y', -1) == new_y):
                                position_free = False
                                break
                    
                    if position_free:
                        self.x, self.y = new_x, new_y
                        return True
            except Exception:
                pass
                
            return False
        except Exception:
            return False

    _attach_take_turn(e, regent_ai)
    return e


def create_crimson_leviathan(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Apex predator of the desert wastes - massive creature with blood frenzy abilities."""
    e = Enemy("Crimson Leviathan", 180 + level * 15, 35 + level * 3, 12 + level, 6, EnemyPersonality(), 800, x, y, level=level)
    e.symbol = 'L'
    e.is_massive = True
    e.size = 3  # 3x3 creature
    e.alert_range = 15
    return e


def create_bone_crusher(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Skeletal behemoth that manipulates bones - cavern dweller with crushing attacks."""
    e = Enemy("Bone Crusher", 220 + level * 18, 42 + level * 4, 8 + level, 4, EnemyPersonality(), 1000, x, y, level=level)
    e.symbol = 'B'
    e.is_massive = True
    e.size = 2  # 2x2 creature
    e.alert_range = 12
    return e


def create_void_tendril(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Sith-corrupted entity that phases through reality - void-touched horror."""
    e = Enemy("Void Tendril", 150 + level * 12, 28 + level * 2, 15 + level, 8, EnemyPersonality(), 600, x, y, level=level)
    e.symbol = 'V'
    e.is_massive = True
    e.size = 2  # 2x2 creature
    e.alert_range = 20  # Senses through the Force
    return e


def create_shadow_stalker(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Dark side-enhanced predator with incredible speed and stealth abilities."""
    e = Enemy("Shadow Stalker", 130 + level * 10, 38 + level * 3, 6 + level, 12, EnemyPersonality(), 700, x, y, level=level)
    e.symbol = 'S'
    e.is_massive = True
    e.size = 2  # 2x2 creature
    e.alert_range = 18
    return e


def create_stone_titan(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Colossal mountain guardian with earth manipulation and seismic attacks."""
    e = Enemy("Stone Titan", 300 + level * 25, 45 + level * 4, 10 + level, 3, EnemyPersonality(), 1200, x, y, level=level)
    e.symbol = 'T'
    e.is_massive = True
    e.size = 4  # 4x4 creature - largest
    e.alert_range = 25
    return e


def create_tomb_serpent(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Ancient serpentine guardian of Sith tombs with constriction abilities."""
    e = Enemy("Tomb Serpent", 250 + level * 20, 40 + level * 3, 18 + level, 7, EnemyPersonality(), 1500, x, y, level=level)
    e.symbol = 'H'  # H for serpent/snake
    e.is_massive = True
    e.size = 3  # 3x3 creature
    e.alert_range = 30
    return e


def create_dark_weaver(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Force-sensitive arachnid that weaves illusions and psychic attacks."""
    e = Enemy("Dark Weaver", 160 + level * 14, 32 + level * 2, 8 + level, 10, EnemyPersonality(), 750, x, y, level=level)
    e.symbol = 'W'
    e.is_massive = True
    e.size = 3  # 3x3 creature
    e.alert_range = 22
    return e


def create_frost_behemoth(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Cold-adapted beast with freezing attacks and ice armor."""
    e = Enemy("Frost Behemoth", 200 + level * 16, 48 + level * 4, 12 + level, 5, EnemyPersonality(), 1100, x, y, level=level)
    e.symbol = 'F'
    e.is_massive = True
    e.size = 3  # 3x3 creature
    e.alert_range = 16
    return e


def create_jedi_master(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """
    Jedi Master boss - spawns when player corruption >= 60%.
    Defensive, uses Force abilities, wields blue lightsaber.
    """
    e = Enemy(
        "Jedi Master", 
        40 + level * 8,  # High HP for endgame boss
        15 + int(level * 1.8),  # Strong attack
        10 + level,  # High defense
        8 + level//2,  # Good evasion
        EnemyPersonality(is_jedi=True), 
        200,  # High XP reward
        x, y, 
        level=level
    )
    e.symbol = 'J'
    e.is_boss = True
    e.lightsaber_color = "blue"
    e.combat_stance = "defensive"
    e.faction = 'Republic'  # Jedi Master belongs to Republic faction
    e.color = 4  # Blue color for Republic
    
    try:
        e.force_abilities = {
            'push': force_abilities.ForcePushPull(),
            'heal': force_abilities.ForceHeal(amount=15 + level * 2),
            'reveal': force_abilities.ForceReveal(duration=8, bonus=5)
        }
        e.force_points = 8 + level
    except Exception:
        e.force_abilities = {}

    def jedi_master_ai(game, self):
        """Jedi Master AI: prioritizes healing when low HP, uses Force push in combat"""
        try:
            player = getattr(game, 'player', None)
            if not player:
                return False
            
            current_hp_ratio = getattr(self, 'hp', 1) / getattr(self, 'max_hp', 1)
            dist = abs(getattr(player,'x',0)-getattr(self,'x',0)) + abs(getattr(player,'y',0)-getattr(self,'y',0))
            
            fa = getattr(self, 'force_abilities', {}) or {}
            
            # Heal if HP < 40%
            if current_hp_ratio < 0.4:
                heal = fa.get('heal')
                if heal:
                    last = getattr(self, '_ability_last_used', {}).get(getattr(heal,'name',str(heal)), -9999)
                    cooldown = getattr(heal, 'cooldown', 5)
                    if getattr(game,'turn_count',0) - last >= cooldown:
                        try:
                            used = heal.use(self, self, game.game_map, getattr(game.ui,'messages',None), getattr(self,'level',1))
                            if used:
                                try: 
                                    if not hasattr(self, '_ability_last_used'):
                                        self._ability_last_used = {}
                                    self._ability_last_used[getattr(heal,'name',str(heal))] = getattr(game,'turn_count',0)
                                except Exception: pass
                                return True
                        except Exception:
                            pass
            
            # Use Force push if player is close
            push = fa.get('push')
            if push and dist <= 5:
                last = getattr(self, '_ability_last_used', {}).get(getattr(push,'name',str(push)), -9999)
                cooldown = getattr(push, 'cooldown', 3)
                if getattr(game,'turn_count',0) - last >= cooldown:
                    try:
                        used = push.use(self, player, game.game_map, getattr(game.ui,'messages',None), getattr(self,'level',1))
                        if used:
                            try: 
                                if not hasattr(self, '_ability_last_used'):
                                    self._ability_last_used = {}
                                self._ability_last_used[getattr(push,'name',str(push))] = getattr(game,'turn_count',0)
                            except Exception: pass
                            return True
                    except Exception:
                        pass
            
            # Occasionally use reveal to track player
            reveal = fa.get('reveal')
            if reveal and random.random() < 0.15:
                last = getattr(self, '_ability_last_used', {}).get(getattr(reveal,'name',str(reveal)), -9999)
                cooldown = getattr(reveal, 'cooldown', 4)
                if getattr(game,'turn_count',0) - last >= cooldown:
                    try:
                        # Check if enemy has enough force points before attempting
                        cost = getattr(reveal, 'base_cost', 1)
                        enemy_fp = getattr(self, 'force_points', 0)
                        
                        if enemy_fp >= cost:
                            # Use null messages to prevent spam to player
                            null_messages = type('NullMessages', (), {'add': lambda self, msg: None})()
                            used = reveal.use(self, None, game.game_map, null_messages, getattr(self,'level',1))
                        else:
                            used = False  # Skip silently if not enough force points
                        
                        if used:
                            try: 
                                if not hasattr(self, '_ability_last_used'):
                                    self._ability_last_used = {}
                                self._ability_last_used[getattr(reveal,'name',str(reveal))] = getattr(game,'turn_count',0)
                            except Exception: pass
                            return True
                    except Exception:
                        pass
            
            return False
        except Exception:
            return False

    _attach_take_turn(e, jedi_master_ai)
    return e


# ═══════════════════════════════════════════════════════════════════════════
#  SPECIAL DUNGEON ENEMIES - Unique enemies for thematic dungeons
# ═══════════════════════════════════════════════════════════════════════════

def create_memory_wraith(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Memory Wraith - Steals your memories and confuses you."""
    e = Enemy("Memory Wraith", 20 + level * 4, 8 + level, 4 + level//2, 12, EnemyPersonality(), 70, x, y, level=level)
    e.symbol = 'M'
    e.description = "A ghostly entity formed from stolen memories"
    return e


def create_crystal_guardian(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Crystal Guardian - Heavily armored crystal construct."""
    e = Enemy("Crystal Guardian", 35 + level * 7, 10 + level, 8 + level, 4, EnemyPersonality(), 80, x, y, level=level)
    e.symbol = 'D'
    e.description = "A living crystal formation animated by dark energy"
    return e


def create_shadow_stalker(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Shadow Stalker - Fast, evasive, strikes from darkness."""
    e = Enemy("Shadow Stalker", 15 + level * 3, 12 + int(level * 1.5), 3 + level//3, 18 + level, EnemyPersonality(), 90, x, y, level=level)
    e.symbol = 'B'
    e.description = "A being of living shadow that hunts in darkness"
    return e


def create_bone_wraith(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Bone Wraith - Undead guardian of the bone cathedral."""
    e = Enemy("Bone Wraith", 25 + level * 5, 9 + level, 5 + level//2, 8, EnemyPersonality(), 75, x, y, level=level)
    e.symbol = 'b'  # Bone wraith
    e.description = "A vengeful spirit bound to ancient bones"
    return e


def create_echo_banshee(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Echo Banshee - Sonic attacks, screams that damage."""
    e = Enemy("Echo Banshee", 18 + level * 4, 10 + level, 3 + level//3, 10, EnemyPersonality(), 85, x, y, level=level)
    e.symbol = 'N'
    e.description = "A creature of pure sound that screams eternally"
    return e


def create_knowledge_seeker(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Knowledge Seeker - Corrupted scholar seeking forbidden lore."""
    e = Enemy("Knowledge Seeker", 22 + level * 4, 7 + level, 5 + level//2, 9, EnemyPersonality(), 95, x, y, level=level)
    e.symbol = 'P'
    e.description = "A scholar driven mad by forbidden knowledge"
    return e


def create_pain_wraith(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Pain Wraith - Born from suffering, inflicts agony."""
    e = Enemy("Pain Wraith", 23 + level * 5, 11 + level, 4 + level//2, 7, EnemyPersonality(), 80, x, y, level=level)
    e.symbol = 'C'
    e.description = "An entity forged from accumulated suffering"
    return e


def create_nightmare_herald(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    """Nightmare Herald - Manifests your fears."""
    e = Enemy("Nightmare Herald", 26 + level * 5, 10 + level, 5 + level//2, 11, EnemyPersonality(), 85, x, y, level=level)
    e.symbol = 'H'
    e.description = "A creature from the realm of nightmares"
    return e
