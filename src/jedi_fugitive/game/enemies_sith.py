"""Sith-era enemies: factories that produce Enemy instances compatible with
the existing `jedi_fugitive.game.enemy.Enemy` class.

These are lightweight, data-driven factories that attach small custom
`take_turn(game)` hooks where needed. Keep changes non-invasive so the
main enemy processing loop continues to work.
"""
from typing import Optional
import random
from jedi_fugitive.game.enemy import Enemy
from jedi_fugitive.game.personality import EnemyPersonality
from jedi_fugitive.game import force_abilities


def _attach_take_turn(e: Enemy, fn):
    # Simply assign a callable that accepts one arg (game). process_enemies will call it.
    try:
        e.take_turn = lambda game, _fn=fn: _fn(game, e)
    except Exception:
        try:
            e.take_turn = lambda game: fn(game, e)
        except Exception:
            pass


def create_sith_acolyte(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Sith Acolyte", 14 + level * 2, 6 + level, 2 + level//3, 5, EnemyPersonality(), 20, x, y, level=level)
    e.symbol = 'a'
    return e


def create_sith_warrior(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Sith Warrior", 28 + level * 6, 12 + int(level * 1.5), 6 + level//2, 6, EnemyPersonality(), 60, x, y, level=level)
    e.symbol = 'w'
    return e


def create_sith_assassin(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    # highly evasive short-lived assassin; special: first strike bonus and occasional vanish
    e = Enemy("Sith Assassin", 12 + level * 2, 10 + level, 2 + level//4, 20 + level, EnemyPersonality(), 80, x, y, level=level)
    e.symbol = 's'

    def assassin_ai(game, self):
        try:
            # attempt to vanish (simulate stealth) with small chance
            if random.random() < 0.12 and not getattr(self, '_is_stealthed', False):
                try:
                    self._is_stealthed = True
                    if getattr(game.ui, 'messages', None):
                        game.ui.messages.add(f"{self.name} melts into the shadows!")
                except Exception:
                    pass

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
                            if 0 <= ny < len(game.game_map) and 0 <= nx < len(game.game_map[0]) and game.game_map[ny][nx] == getattr(game.Display, 'FLOOR', '.'):
                                # avoid colliding with player or other enemies
                                if not any(getattr(o,'x',None)==nx and getattr(o,'y',None)==ny for o in game.enemies):
                                    self.x = nx; self.y = ny
                                    break
                    except Exception:
                        pass
                    # perform a heavy attack on player
                    try:
                        dmg = max(1, int(getattr(self, 'attack', 5) * 1.4))
                        if hasattr(player, 'hp'):
                            player.hp = max(0, getattr(player, 'hp', 0) - dmg)
                        if getattr(game.ui, 'messages', None):
                            game.ui.messages.add(f"{self.name} ambushes you for {dmg} damage!")
                    except Exception:
                        pass
                    # break stealth after attack
                    try:
                        self._is_stealthed = False
                    except Exception:
                        pass
                    return True

            return False
        except Exception:
            return False

    _attach_take_turn(e, assassin_ai)
    return e


def create_sith_sorcerer(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Sith Sorcerer", 18 + level * 3, 6 + level, 3 + level//3, 8, EnemyPersonality(), 100, x, y, level=level)
    e.symbol = 'S'
    # give a couple of force abilities for ranged behavior
    try:
        e.force_abilities = {
            'lightning': force_abilities.ForceLightning(damage=6 + level),
            'reveal': force_abilities.ForceReveal(duration=6, bonus=3)
        }
        # sorcerer has a modest pool
        e.force_points = 3 + level//2
    except Exception:
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
                    except Exception:
                        pass

            # else possibly reveal to increase LOS for itself
            reveal = fa.get('reveal')
            if reveal:
                last = getattr(self, '_ability_last_used', {}).get(getattr(reveal,'name',str(reveal)), -9999)
                cooldown = getattr(reveal, 'cooldown', 4)
                if getattr(game, 'turn_count', 0) - last >= cooldown:
                    try:
                        used = reveal.use(self, None, game.game_map, getattr(game.ui,'messages', None), getattr(self,'level',1))
                        if used:
                            try: self._ability_last_used[getattr(reveal,'name',str(reveal))] = getattr(game,'turn_count',0)
                            except Exception: pass
                            return True
                    except Exception:
                        pass

            return False
        except Exception:
            return False

    _attach_take_turn(e, sorcerer_ai)
    return e


def create_sith_wardroid(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Sith WarDroid", 32 + level * 8, 10 + level//1, 8 + level//2, 3, EnemyPersonality(), 120, x, y, level=level)
    e.symbol = 'd'
    # war droids are slow but tanky; no special AI needed
    return e


def create_tukata(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Tuk'ata", 12 + level * 3, 8 + level//1, 1 + level//4, 12, EnemyPersonality(), 40, x, y, level=level)
    e.symbol = 't'
    # fast: occasionally move two steps; reuse default behavior but mark aggressiveness
    return e


def create_terentatek(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Terentatek", 80 + level * 20, 20 + level * 2, 10 + level//1, 2, EnemyPersonality(), 400, x, y, level=level)
    e.symbol = 'T'
    return e


def create_sith_trooper(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Sith Trooper", 16 + level * 3, 9 + level, 3 + level//2, 6, EnemyPersonality(), 30, x, y, level=level)
    e.symbol = 'm'
    return e


def create_sith_officer(level: int = 1, x: int = 0, y: int = 0) -> Enemy:
    e = Enemy("Sith Officer", 22 + level * 4, 10 + level, 5 + level//2, 8, EnemyPersonality(), 120, x, y, level=level)
    e.symbol = 'o'

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
    e.symbol = 'L'
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
    e.symbol = 'K'
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
            if getattr(game, 'turn_count', 0) % 3 == 0:
                try:
                    if hasattr(player, 'force_points') and player.force_points > 0:
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


def create_obsidian_regent(level: int = 7, x: int = 0, y: int = 0) -> Enemy:
    """An ancient regent who manipulates the battlefield and summons brief guardians."""
    e = Enemy("Obsidian Regent", 120 + level * 22, 14 + level * 2, 12 + level, 6, EnemyPersonality(), 1600, x, y, level=level)
    e.symbol = 'Z'
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
                            if 0 <= ny < len(game.game_map) and 0 <= nx < len(game.game_map[0]) and game.game_map[ny][nx] == getattr(game.Display,'FLOOR','.'):
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
                        used = reveal.use(self, None, game.game_map, getattr(game.ui,'messages',None), getattr(self,'level',1))
                        if used:
                            try: self._ability_last_used[getattr(reveal,'name',str(reveal))] = getattr(game,'turn_count',0)
                            except Exception: pass
                            return True
                    except Exception:
                        pass
            return False
        except Exception:
            return False

    _attach_take_turn(e, regent_ai)
    return e
