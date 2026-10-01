"""Simple projectile subsystem.

Provides a lightweight Projectile dataclass and helpers to spawn and advance
projectiles in the game's headless and curses-driven loops.

This module is defensive: it tolerates missing attributes on `game` and
uses fallbacks for enemy damage application and UI popups.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List


def _sign(n: int) -> int:
    return 0 if n == 0 else (1 if n > 0 else -1)

from jedi_fugitive.game import logger
log = logger  # the Logger itself (logger.log is a bound method with no .error/.info)

@dataclass
class Projectile:
    x: int
    y: int
    dx: int
    dy: int
    symbol: str = "-"
    damage: int = 1
    owner: Optional[object] = None
    range_remaining: int = 8
    alive: bool = True
    color_pair: int = 9


def _ensure_store(game) -> List[Projectile]:
    """Ensure game has a projectiles list and return it."""
    if getattr(game, "projectiles", None) is None:
        try:
            game.projectiles = []
        except Exception:
            if not hasattr(_ensure_store, "_local_proj"):
                _ensure_store._local_proj = []
            return _ensure_store._local_proj
    return game.projectiles


def spawn_blaster(game, sx: int, sy: int, tx: int, ty: int, damage: int = 6, symbol: str = '-', color_pair: int = 9, **kwargs):
    """Spawn a simple straight-moving blaster projectile.

    Movement is one tile per advance in the direction towards (tx,ty) with
    dx/dy = sign(tx-sx), sign(ty-sy) (diagonal allowed).
    
    This creates projectiles that move via advance_projectiles() - the same system
    used for all projectiles (player and enemy), ensuring unified behavior.
    """
    proj_list = _ensure_store(game)
    dx = _sign(tx - sx)
    dy = _sign(ty - sy)
    # accept legacy kwargs such as owner, max_range, etc. and ignore unknown ones
    owner = kwargs.get('owner', getattr(game, 'player', None))
    max_range = kwargs.get('max_range', kwargs.get('range', 10))
    p = Projectile(x=sx, y=sy, dx=dx, dy=dy, symbol=symbol, damage=damage,
                   owner=owner, range_remaining=max_range, color_pair=color_pair)
    proj_list.append(p)
    return p


def spawn_grenade(game, sx: int, sy: int, tx: int, ty: int, damage: int = 12, radius: int = 1):
    """Spawn a thrown grenade. It travels a short distance and explodes on impact or when range expires."""
    proj_list = _ensure_store(game)
    dx = _sign(tx - sx)
    dy = _sign(ty - sy)
    p = Projectile(x=sx, y=sy, dx=dx, dy=dy, symbol='*', damage=damage,
                   owner=getattr(game, 'player', None), range_remaining=6, color_pair=13)
    setattr(p, 'is_grenade', True)
    setattr(p, 'blast_radius', radius)
    proj_list.append(p)
    return p


def explode_at(game, cx: int, cy: int, damage: int = 0, radius: int = 1, collapse_popup: bool = True):
    """Apply area damage to enemies near (cx,cy) and create popups.

    Uses Chebyshev distance for the radius.
    """
    enemies = getattr(game, 'enemies', []) or []
    hit_any = False
    for e in list(enemies):
        ex = getattr(e, 'x', None)
        ey = getattr(e, 'y', None)
        if ex is None or ey is None:
            continue
        if max(abs(ex - cx), abs(ey - cy)) <= radius:
            hit_any = True
            # apply damage with best-effort
            if hasattr(e, 'take_damage'):
                try:
                    e.take_damage(damage, game=game)
                except Exception:
                    try:
                        e.hp = max(0, getattr(e, 'hp', 0) - damage)
                        if getattr(e, 'hp', 0) <= 0:
                            setattr(e, 'alive', False)
                    except Exception:
                        pass
            else:
                try:
                    e.hp = max(0, getattr(e, 'hp', 0) - damage)
                    if getattr(e, 'hp', 0) <= 0:
                        setattr(e, 'alive', False)
                except Exception:
                    pass

    ui = getattr(game, 'ui', None)
    if ui is not None:
        try:
            if hit_any or collapse_popup:
                ui.add_popup(cx, cy, "BOOM!", color_pair=13, ttl=8, echo=True, echo_text="Boom!")
            else:
                ui.add_popup(cx, cy, "Boom", color_pair=13, ttl=6, echo=False)
        except Exception:
            pass


def advance_projectiles(game):
    """Advance all projectiles on the game by one step.

    Defensive: tolerates missing map/enemies/ui and will remove projectiles when
    they expire or hit obstacles/enemies.
    """
    proj_list = _ensure_store(game)
    if not proj_list:
        return

    gmap = getattr(game, 'game_map', None)
    max_h = len(gmap) if gmap else 0
    max_w = len(gmap[0]) if max_h else 0
    enemies = getattr(game, 'enemies', []) or []

    for p in list(proj_list):
        if not getattr(p, 'alive', True):
            try:
                proj_list.remove(p)
            except ValueError:
                pass
            continue

        nx = p.x + p.dx
        ny = p.y + p.dy

        blocked = False
        if max_w and max_h:
            if nx < 0 or ny < 0 or ny >= max_h or nx >= max_w:
                blocked = True
        if not blocked and gmap:
            try:
                tile = gmap[ny][nx]
                if tile in ('#', 'T'):
                    blocked = True
            except Exception:
                pass

        if blocked:
            if getattr(p, 'is_grenade', False):
                try:
                    explode_at(game, nx, ny, damage=p.damage, radius=getattr(p, 'blast_radius', 1))
                except Exception:
                    pass
            p.alive = False
            try:
                proj_list.remove(p)
            except ValueError:
                pass
            continue

        p.x = nx
        p.y = ny
        p.range_remaining = max(0, p.range_remaining - 1)

        # Check if projectile hits player (for enemy projectiles)
        player = getattr(game, 'player', None)
        owner = getattr(p, 'owner', None)
        if player and owner != player:
            px = getattr(player, 'x', None)
            py = getattr(player, 'y', None)
            if px is not None and py is not None and px == p.x and py == p.y:
                # Projectile hit player
                damage = getattr(p, 'damage', 5)
                player.hp -= damage
                
                # Track attacker for death message
                if owner:
                    owner_name = getattr(owner, 'name', 'Enemy')
                    player.last_attacking_enemy = owner_name
                    player.last_damage_taken = damage
                    player.last_attack_type = "ranged attack"
                
                # Show damage popup and message
                ui = getattr(game, 'ui', None)
                if ui is not None:
                    try:
                        ui.add_popup(p.x, p.y, str(damage), color_pair=1, ttl=6, echo=False)
                        if player.hp > 0:
                            ui.messages.add(f"#1#Enemy projectile hits you for {damage} damage!#0#")
                    except Exception:
                        pass
                
                # Remove projectile
                p.alive = False
                try:
                    proj_list.remove(p)
                except ValueError:
                    pass
                continue

        hit = None
        for e in enemies:
            try:
                if getattr(e, 'x', None) == p.x and getattr(e, 'y', None) == p.y and getattr(e, 'is_alive', None) is not False:
                    hit = e
                    break
            except Exception:
                continue

        if hit is not None:
            try:
                if hasattr(hit, 'take_damage'):
                    hit.take_damage(p.damage, game=game)
                else:
                    hit.hp = max(0, getattr(hit, 'hp', 0) - p.damage)
                    if getattr(hit, 'hp', 0) <= 0:
                        setattr(hit, 'alive', False)
            except Exception:
                pass
            ui = getattr(game, 'ui', None)
            if ui is not None:
                try:
                    ui.add_popup(p.x, p.y, str(p.damage), color_pair=getattr(p, 'color_pair', 9), ttl=6, echo=False)
                    
                    # Add descriptive hit message
                    enemy_name = getattr(hit, 'name', 'enemy')
                    if getattr(hit, 'hp', 1) <= 0:
                        # Fatal hit messages
                        import random
                        fatal_messages = [
                            f"#9#Your bolt strikes true - {enemy_name} falls with a final cry!#0#",
                            f"#9#The energy blast tears through {enemy_name}'s defenses - they collapse!#0#",
                            f"#9#{enemy_name} staggers and drops as your shot finds its deadly mark!#0#",
                            f"#9#A perfect hit! {enemy_name} crumples to the ground, defeated!#0#",
                        ]
                        try: ui.messages.add(f"{random.choice(fatal_messages)} [{p.damage} damage]")
                        except Exception: pass
                    else:
                        # Hit messages
                        import random
                        hit_messages = [
                            f"#2#Your shot slams into {enemy_name}!#0#",
                            f"#2#Direct hit on {enemy_name}!#0#",
                            f"#2#The bolt scores a solid hit on {enemy_name}!#0#",
                            f"#2#{enemy_name} reels from your accurate fire!#0#",
                            f"#2#Your aim is true - {enemy_name} takes the hit!#0#",
                        ]
                        try: ui.messages.add(f"{random.choice(hit_messages)} [{p.damage} damage]")
                        except Exception: pass
                except Exception:
                    pass
            if getattr(p, 'is_grenade', False):
                try:
                    explode_at(game, p.x, p.y, damage=p.damage, radius=getattr(p, 'blast_radius', 1))
                except Exception:
                    pass
            p.alive = False
            try:
                proj_list.remove(p)
            except ValueError:
                pass
            continue

        if p.range_remaining <= 0:
            if getattr(p, 'is_grenade', False):
                try:
                    explode_at(game, p.x, p.y, damage=p.damage, radius=getattr(p, 'blast_radius', 1))
                except Exception:
                    pass
            p.alive = False
            try:
                proj_list.remove(p)
            except ValueError:
                pass


# provide a minimal public API
__all__ = [
    'Projectile',
    'spawn_blaster',
    'spawn_grenade',
    'advance_projectiles',
    'explode_at',
]
