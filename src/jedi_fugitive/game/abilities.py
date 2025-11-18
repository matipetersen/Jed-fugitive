from jedi_fugitive.game.force_abilities import ForcePushPull

def choose_ability(game):
    abilities = game.player.get_available_abilities() or []
    expanded = []
    for a in abilities:
        if isinstance(a, ForcePushPull):
            class _W:
                def __init__(self, base, mode):
                    self._base = base
                    self.mode = mode
                    self.name = f"{mode.capitalize()} - {getattr(base,'name',str(base))}"
                def __repr__(self):
                    return self.name
                def use(self, *args, **kwargs):
                    try:
                        return self._base.use(*args, mode=self.mode, **kwargs)
                    except TypeError:
                        try:
                            return self._base.use(*args, self.mode, **kwargs)
                        except Exception:
                            return False
            expanded.append(_W(a, "push"))
            expanded.append(_W(a, "pull"))
        else:
            expanded.append(a)
    abilities = expanded
    if not abilities:
        try: game.ui.messages.add("No abilities available.") 
        except Exception: pass
        return None
    for i, a in enumerate(abilities[:9]):
        try: game.ui.messages.add(f"{i+1}) {getattr(a,'name',str(a))}") 
        except Exception: pass
    try:
        from jedi_fugitive.game.ui_renderer import draw
        draw(game)
    except Exception:
        pass
    key = game.stdscr.getch()
    if key >= ord('1') and key <= ord('9'):
        idx = key - ord('1')
        if idx < len(abilities):
            return abilities[idx]
    try: game.ui.messages.add("Ability selection cancelled.") 
    except Exception: pass
    return None

def use_force_ability(game, ability, tx, ty):
    """Call ability.use and, if the ability wrapper exposes a 'mode' of 'push' or 'pull',
    move the target actor away or towards the player up to 3 tiles (blocked by walls/trees/other actors)."""
    from jedi_fugitive.game.level import Display
    prev_w = getattr(game.player, "equipped_weapon", None)
    prev_a = getattr(game.player, "equipped_armor", None)
    used = False
    try:
        try:
            used = ability.use(game.player, (tx, ty), game.game_map, messages=game.ui.messages, game=game)
        except TypeError:
            try:
                used = ability.use(game.player, tx, ty, game.game_map, messages=game.ui.messages, game=game)
            except TypeError:
                try:
                    used = ability.use(game.player, tx, ty)
                except Exception:
                    used = False
    except Exception:
        used = False
    # restore equipment if cleared
    try:
        if prev_w is not None and getattr(game.player, "equipped_weapon", None) is None:
            try: from jedi_fugitive.game.equipment import _apply_equipment_effects; _apply_equipment_effects(game, prev_w, "weapon")
            except Exception: game.player.equipped_weapon = prev_w
        if prev_a is not None and getattr(game.player, "equipped_armor", None) is None:
            try: from jedi_fugitive.game.equipment import _apply_equipment_effects; _apply_equipment_effects(game, prev_a, "armor")
            except Exception: game.player.equipped_armor = prev_a
    except Exception:
        pass

    if used:
        try: game.ui.messages.add(f"Used {getattr(ability,'name',str(ability))}.") 
        except Exception: pass

        # if ability wrapper specified a mode, apply push/pull physics to the actor on (tx,ty)
        mode = getattr(ability, "mode", None)
        if mode in ("push", "pull"):
            try:
                # First, check if target is a boulder (for Sith Keep puzzles)
                map_h = len(game.game_map)
                map_w = len(game.game_map[0]) if map_h else 0
                is_boulder = False
                if 0 <= ty < map_h and 0 <= tx < map_w:
                    cell = game.game_map[ty][tx]
                    if cell == 'O':  # Boulder symbol
                        is_boulder = True
                        try:
                            from jedi_fugitive.game.sith_keep import move_boulder
                            # Determine direction
                            sx = tx - getattr(game.player, "x", 0)
                            sy = ty - getattr(game.player, "y", 0)
                            import math
                            dist = math.hypot(sx, sy)
                            if dist > 0:
                                dx = int(round(sx / dist))
                                dy = int(round(sy / dist))
                                if mode == "pull":
                                    # Reverse direction for pull
                                    dx = -dx
                                    dy = -dy
                                moved = move_boulder(game, tx, ty, dx, dy)
                                if moved:
                                    try: game.ui.messages.add(f"You {mode} the boulder.")
                                    except Exception: pass
                                else:
                                    try: game.ui.messages.add(f"The boulder won't budge.")
                                    except Exception: pass
                            return  # Boulder handled, don't process as enemy
                        except Exception as e:
                            try: game.ui.messages.add(f"Failed to move boulder: {e}")
                            except Exception: pass
                            return
                
                # find a living enemy at target tile
                target = None
                for e in getattr(game, "enemies", []):
                    try:
                        if getattr(e, "is_alive", lambda: False)() and getattr(e, "x", -1) == tx and getattr(e, "y", -1) == ty:
                            target = e; break
                    except Exception:
                        continue
                if target is None:
                    # nothing to move
                    if not is_boulder:
                        try: game.ui.messages.add("No valid target at that location to move.") 
                        except Exception: pass
                else:
                    sx = tx - getattr(game.player, "x", 0)
                    sy = ty - getattr(game.player, "y", 0)
                    import math
                    dist = math.hypot(sx, sy)
                    if dist == 0:
                        ux, uy = 0, 0
                    else:
                        ux = int(round(sx / dist))
                        uy = int(round(sy / dist))
                    steps = 3
                    final_x, final_y = tx, ty
                    map_h = len(game.game_map)
                    map_w = len(game.game_map[0]) if map_h else 0
                    wall_char = getattr(Display, "WALL", "#")
                    tree_char = getattr(Display, "TREE", "T")
                    def is_blocked(x, y):
                        if not (0 <= y < map_h and 0 <= x < map_w): return True
                        ch = game.game_map[y][x]
                        if ch in (wall_char, tree_char): return True
                        if (x, y) == (getattr(game.player, "x", -999), getattr(game.player, "y", -999)): return True
                        for o in getattr(game, "enemies", []):
                            if o is not target and getattr(o, "is_alive", lambda: False)() and getattr(o, "x", -999) == x and getattr(o, "y", -999) == y:
                                return True
                        return False

                    if mode == "push":
                        # try to move outward along (ux,uy) up to steps
                        hit_wall = False
                        for s in range(1, steps + 1):
                            nx = tx + ux * s
                            ny = ty + uy * s
                            if is_blocked(nx, ny):
                                # Check if blocked by wall/obstacle (not another enemy)
                                if 0 <= ny < map_h and 0 <= nx < map_w:
                                    ch = game.game_map[ny][nx]
                                    if ch in (wall_char, tree_char):
                                        hit_wall = True
                                break
                            final_x, final_y = nx, ny
                        moved = (final_x, final_y) != (tx, ty)
                        if moved:
                            # fix: assign both x and y to the target
                            target.x, target.y = final_x, final_y
                            
                            # Apply collision damage if hit wall
                            if hit_wall:
                                collision_damage = 5 + steps  # 6-8 damage depending on distance
                                try:
                                    if hasattr(target, 'take_damage'):
                                        target.take_damage(collision_damage)
                                    else:
                                        target.hp = getattr(target, 'hp', 0) - collision_damage
                                    game.ui.messages.add(f"Pushed {getattr(target,'name', 'target')} into wall! {collision_damage} collision damage!")
                                except Exception:
                                    game.ui.messages.add(f"Pushed {getattr(target,'name', 'target')} to ({final_x},{final_y}).")
                            else:
                                try: game.ui.messages.add(f"Pushed {getattr(target,'name', 'target')} to ({final_x},{final_y}).")
                                except Exception: pass
                        else:
                            try: game.ui.messages.add("Push blocked.") 
                            except Exception: pass
                    else:  # pull
                        # vector from target to player (move closer)
                        tx_to_px = getattr(game.player, "x", 0) - tx
                        ty_to_py = getattr(game.player, "y", 0) - ty
                        dist2 = math.hypot(tx_to_px, ty_to_py)
                        if dist2 == 0:
                            try: game.ui.messages.add("Target is on you; cannot pull.") 
                            except Exception: pass
                        else:
                            ux2 = int(round(tx_to_px / dist2))
                            uy2 = int(round(ty_to_py / dist2))
                            hit_wall = False
                            for s in range(1, steps + 1):
                                nx = tx + ux2 * s
                                ny = ty + uy2 * s
                                # don't allow moving onto player
                                if (nx, ny) == (getattr(game.player, "x", -999), getattr(game.player, "y", -999)):
                                    break
                                if is_blocked(nx, ny):
                                    # Check if blocked by wall/obstacle (not player or another enemy)
                                    if 0 <= ny < map_h and 0 <= nx < map_w:
                                        ch = game.game_map[ny][nx]
                                        if ch in (wall_char, tree_char):
                                            hit_wall = True
                                    break
                                final_x, final_y = nx, ny
                            moved = (final_x, final_y) != (tx, ty)
                            if moved:
                                target.x, target.y = final_x, final_y
                                
                                # Apply collision damage if hit wall
                                if hit_wall:
                                    collision_damage = 5 + steps  # 6-8 damage
                                    try:
                                        if hasattr(target, 'take_damage'):
                                            target.take_damage(collision_damage)
                                        else:
                                            target.hp = getattr(target, 'hp', 0) - collision_damage
                                        game.ui.messages.add(f"Pulled {getattr(target,'name','target')} into obstacle! {collision_damage} collision damage!")
                                    except Exception:
                                        game.ui.messages.add(f"Pulled {getattr(target,'name','target')} to ({final_x},{final_y}).")
                                else:
                                    try: game.ui.messages.add(f"Pulled {getattr(target,'name','target')} to ({final_x},{final_y}).")
                                    except Exception: pass
                            else:
                                try: game.ui.messages.add("Pull blocked.") 
                                except Exception: pass
            except Exception as e:
                try: game.ui.messages.add(f"Force move failed: {e}") 
                except Exception: pass

    return used