import curses
import traceback
from jedi_fugitive.game.level import Display
from jedi_fugitive.game import equipment


def _fire_gun(game, tx, ty):
    """Fire ranged weapon at target coordinates (tx, ty)."""
    try:
        px = getattr(game.player, "x", 0)
        py = getattr(game.player, "y", 0)
        
        # Get weapon stats
        weapon = getattr(game.player, 'equipped_weapon', None)
        if not weapon:
            try: game.ui.messages.add("No weapon equipped!")
            except Exception: pass
            return False
        
        # Get weapon properties
        weapon_range = 5
        weapon_damage = 10
        weapon_accuracy = 80
        weapon_name = "Weapon"
        weapon_ammo = 0
        
        if isinstance(weapon, dict):
            weapon_range = weapon.get('range', 5)
            weapon_damage = weapon.get('base_damage', weapon.get('damage', 10))
            weapon_accuracy = weapon.get('accuracy', 80)
            weapon_name = weapon.get('name', 'Weapon')
            weapon_ammo = weapon.get('ammo', 0)
        elif hasattr(weapon, 'name'):
            weapon_range = getattr(weapon, 'range', 5)
            weapon_damage = getattr(weapon, 'base_damage', getattr(weapon, 'damage', 10))
            weapon_accuracy = getattr(weapon, 'accuracy', 80)
            weapon_name = weapon.name
            weapon_ammo = getattr(weapon, 'ammo', 0)
        
        # Check ammo
        if weapon_ammo <= 0:
            try: game.ui.messages.add(f"{weapon_name} is out of ammo! Cannot fire.")
            except Exception: pass
            return False
        
        # Check range - minimum 2 tiles, maximum weapon_range
        dist = abs(tx - px) + abs(ty - py)
        if dist < 2:
            try: game.ui.messages.add(f"Target too close! Ranged weapons require at least 2 tiles distance.")
            except Exception: pass
            return False
        if dist > weapon_range:
            try: game.ui.messages.add(f"Target too far! Weapon range: {weapon_range} tiles.")
            except Exception: pass
            return False
        
        # Find enemy at target
        target_enemy = None
        for enemy in getattr(game, 'enemies', []):
            if getattr(enemy, 'x', -1) == tx and getattr(enemy, 'y', -1) == ty:
                target_enemy = enemy
                break
        
        if not target_enemy:
            try: game.ui.messages.add("No enemy at target location!")
            except Exception: pass
            return False
        
        # Calculate hit chance
        import random
        hit_chance = weapon_accuracy - getattr(target_enemy, 'evasion', 0)
        hit_roll = random.randint(1, 100)
        
        if hit_roll <= hit_chance:
            # Hit! Deal damage
            damage = max(1, weapon_damage - getattr(target_enemy, 'defense', 0))
            
            if hasattr(target_enemy, 'take_damage'):
                target_enemy.take_damage(damage)
            else:
                target_enemy.hp = getattr(target_enemy, 'hp', 0) - damage
            
            # Consume ammo
            if isinstance(weapon, dict):
                weapon['ammo'] = weapon.get('ammo', 0) - 1
            elif hasattr(weapon, 'ammo'):
                weapon.ammo = getattr(weapon, 'ammo', 0) - 1
            
            remaining_ammo = weapon.get('ammo', 0) if isinstance(weapon, dict) else getattr(weapon, 'ammo', 0)
            
            try:
                game.ui.messages.add(f"Shot {getattr(target_enemy, 'name', 'enemy')} for {damage} damage! [{remaining_ammo} rounds left]")
            except Exception:
                pass
            
            # Add to travel log
            try:
                if hasattr(game.player, 'add_log_entry'):
                    entry = game.player.narrative_text(
                        light_version=f"Fired {weapon_name} in defense, striking {getattr(target_enemy, 'name', 'enemy')}.",
                        dark_version=f"Gunned down {getattr(target_enemy, 'name', 'enemy')} without hesitation!",
                        balanced_version=f"Shot {getattr(target_enemy, 'name', 'enemy')} with {weapon_name}."
                    )
                    game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
            except Exception:
                pass
        else:
            # Miss! Still consume ammo
            if isinstance(weapon, dict):
                weapon['ammo'] = weapon.get('ammo', 0) - 1
            elif hasattr(weapon, 'ammo'):
                weapon.ammo = getattr(weapon, 'ammo', 0) - 1
            
            remaining_ammo = weapon.get('ammo', 0) if isinstance(weapon, dict) else getattr(weapon, 'ammo', 0)
            
            try:
                game.ui.messages.add(f"Shot missed {getattr(target_enemy, 'name', 'enemy')}! [{remaining_ammo} rounds left]")
            except Exception:
                pass
        
        # Consume turn
        try:
            game.turn_count = getattr(game, 'turn_count', 0) + 1
        except Exception:
            pass
        
        return True
    except Exception as e:
        try: game.ui.messages.add(f"Gun error: {e}")
        except Exception: pass
        return False


def _throw_grenade(game, tx, ty):
    """Throw a grenade at target coordinates (tx, ty)."""
    try:
        px = getattr(game.player, "x", 0)
        py = getattr(game.player, "y", 0)
        
        # Check range (max 3 tiles Manhattan distance)
        dist = abs(tx - px) + abs(ty - py)
        if dist > 3:
            try: game.ui.messages.add("Target too far! Grenades have 3-tile range.")
            except Exception: pass
            return False
        
        # Find grenade in inventory
        inv = getattr(game.player, 'inventory', []) or []
        grenade = None
        grenade_idx = None
        for idx, item in enumerate(inv):
            if isinstance(item, dict) and item.get('id') in ['grenade', 'thermal_grenade']:
                grenade = item
                grenade_idx = idx
                break
        
        if grenade is None:
            try: game.ui.messages.add("No grenades in inventory!")
            except Exception: pass
            return False
        
        # Get grenade stats
        dmg = 12
        radius = 3
        if isinstance(grenade, dict) and 'effect' in grenade:
            eff = grenade['effect']
            dmg = int(eff.get('area_damage', dmg))
            radius = int(eff.get('radius', radius))
        
        # Deal damage to all enemies in radius
        affected = []
        for e in list(getattr(game, 'enemies', []) or []):
            try:
                ex = int(getattr(e, 'x', 0))
                ey = int(getattr(e, 'y', 0))
                dx = ex - tx
                dy = ey - ty
                # Circular radius check
                if (dx*dx + dy*dy) <= (radius * radius):
                    if hasattr(e, 'take_damage'):
                        e.take_damage(dmg)
                    else:
                        e.hp = getattr(e, 'hp', 0) - dmg
                    affected.append(getattr(e, 'name', 'enemy'))
            except Exception:
                continue
        
        # Remove grenade from inventory
        try:
            inv.pop(grenade_idx)
        except Exception:
            pass
        
        # Messages
        try:
            if affected:
                game.ui.messages.add(f"Grenade explodes! {dmg} damage to {len(affected)} enemies: {', '.join(affected[:3])}")
            else:
                game.ui.messages.add(f"Grenade explodes harmlessly.")
        except Exception:
            pass
        
        # Add to travel log
        try:
            if hasattr(game.player, 'add_log_entry') and affected:
                entry = game.player.narrative_text(
                    light_version=f"Used a grenade defensively, catching {len(affected)} enemies.",
                    dark_version=f"Hurled explosive death at {len(affected)} foes, savoring the destruction!",
                    balanced_version=f"Threw a grenade, damaging {len(affected)} enemies."
                )
                game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
        except Exception:
            pass
        
        # Consume turn
        try:
            game.turn_count = getattr(game, 'turn_count', 0) + 1
        except Exception:
            pass
        
        return True
    except Exception as e:
        try: game.ui.messages.add(f"Grenade error: {e}")
        except Exception: pass
        return False


def _show_centered(game, lines, title: str = ""):
    """Try to show a centered dialog in interactive mode; fall back to messages.

    If the UI is headless (getch returns -1) the centered_dialog will return None
    and we then add the same lines to the message buffer so headless runs stay
    non-blocking.
    """
    if not lines:
        return
    try:
        ui = getattr(game, 'ui', None)
        use_popup = getattr(game, 'show_popups', False) and ui is not None and hasattr(ui, 'centered_dialog')
        if use_popup:
            try:
                res = ui.centered_dialog(lines, title=title)
                if res is None:
                    # headless or non-interactive; fall back to messages
                    for ln in lines:
                        try:
                            game.add_message(ln)
                        except Exception:
                            try: ui.messages.add(ln)
                            except Exception: pass
                return
            except Exception:
                # on any UI error fallback to message buffer
                pass
    except Exception:
        pass
    # default message buffer path
    for ln in lines:
        try:
            game.add_message(ln)
        except Exception:
            try: game.ui.messages.add(ln)
            except Exception: pass

def handle_input(game, key):
    """Central input handler: movement, actions and ability targeting.
    Safe, defensive and will report internal errors to game UI messages.
    """
    try:
        if key is None or key < 0:
            return

        move_map = {
            # Arrow keys
            curses.KEY_UP: (0, -1), curses.KEY_DOWN: (0, 1),
            curses.KEY_LEFT: (-1, 0), curses.KEY_RIGHT: (1, 0),
            # Vi keys (hjkl)
            ord('k'): (0, -1), ord('j'): (0, 1),
            ord('h'): (-1, 0), ord('l'): (1, 0),
            # Vi diagonal keys (ybn) - 'u' removed to avoid conflict with use item
            ord('y'): (-1, -1),  # up-left
            ord('b'): (-1, 1),   # down-left
            ord('n'): (1, 1),    # down-right
            # Numpad-style diagonal keys (7893)
            ord('7'): (-1, -1), ord('9'): (1, -1),
            ord('1'): (-1, 1), ord('3'): (1, 1),
        }

        # Reticle / pending ability handling (Force abilities, grenade throwing, OR gun shooting)
        if getattr(game, "pending_force_ability", None) is not None or getattr(game, "pending_grenade_throw", False) or getattr(game, "pending_gun_shot", False):
            # cancel
            if key in (27, ord('c')):
                game.pending_force_ability = None
                game.pending_grenade_throw = False
                game.pending_gun_shot = False
                try: game.ui.messages.add("Action cancelled.") 
                except Exception: pass
                return
            # confirm
            if key in (10, 13, ord(' ')):
                tx = getattr(game, "target_x", getattr(game.player, "x", 0))
                ty = getattr(game, "target_y", getattr(game.player, "y", 0))
                
                # Check if it's a gun shot
                if getattr(game, "pending_gun_shot", False):
                    try:
                        _fire_gun(game, tx, ty)
                    except Exception as e:
                        try: game.ui.messages.add(f"Shot failed: {e}") 
                        except Exception: pass
                    finally:
                        game.pending_gun_shot = False
                # Check if it's a grenade throw
                elif getattr(game, "pending_grenade_throw", False):
                    try:
                        _throw_grenade(game, tx, ty)
                    except Exception as e:
                        try: game.ui.messages.add(f"Grenade throw failed: {e}") 
                        except Exception: pass
                    finally:
                        game.pending_grenade_throw = False
                # Otherwise it's a Force ability
                elif getattr(game, "pending_force_ability", None) is not None:
                    try:
                        from jedi_fugitive.game.abilities import use_force_ability
                        use_force_ability(game, game.pending_force_ability, tx, ty)
                    except Exception:
                        try: game.ui.messages.add("Force use failed.") 
                        except Exception: pass
                    finally:
                        game.pending_force_ability = None
                return
            # move reticle
            if key in move_map:
                dx, dy = move_map[key]
                max_y = len(game.game_map); max_x = len(game.game_map[0]) if max_y else 0
                nx = max(0, min(getattr(game, "target_x", getattr(game.player, "x", 0)) + dx, max_x - 1 if max_x else 0))
                ny = max(0, min(getattr(game, "target_y", getattr(game.player, "y", 0)) + dy, max_y - 1 if max_y else 0))
                
                # Limit grenade throw to 3 tiles range
                if getattr(game, "pending_grenade_throw", False):
                    px = getattr(game.player, "x", 0)
                    py = getattr(game.player, "y", 0)
                    dist = abs(nx - px) + abs(ny - py)  # Manhattan distance
                    if dist <= 3:
                        game.target_x, game.target_y = nx, ny
                # Limit gun shots to weapon range
                elif getattr(game, "pending_gun_shot", False):
                    px = getattr(game.player, "x", 0)
                    py = getattr(game.player, "y", 0)
                    weapon_range = getattr(game, "gun_range", 5)
                    dist = abs(nx - px) + abs(ny - py)
                    if dist <= weapon_range:
                        game.target_x, game.target_y = nx, ny
                else:
                    game.target_x, game.target_y = nx, ny
                return

        # Global keys
        if key in (ord('q'), 27):
            try: game.ui.messages.add("Quitting...") 
            except Exception: pass
            game.running = False
            return

        if key == ord('r'):
            try:
                if hasattr(game, "reveal_map"):
                    game.reveal_map(100)
                try: game.ui.messages.add("Map revealed (debug).")
                except Exception: pass
            except Exception:
                try: game.ui.messages.add("Reveal failed.") 
                except Exception: pass
            return

        if key == ord('p'):
            game.show_popups = not getattr(game, "show_popups", False)
            try: game.ui.messages.add(f"Popups {'on' if game.show_popups else 'off'}.")
            except Exception: pass
            return

        if key == ord('v'):
            game.show_codex = not getattr(game, "show_codex", False)
            try:
                if game.show_codex:
                    game.ui.messages.add("Sith Codex opened. Press 'v' again to close.")
                else:
                    game.ui.messages.add("Sith Codex closed.")
            except Exception: pass
            return

        # Help screen
        if key == ord('?'):
            try:
                help_lines = [
                    "╔═══════════════════════════════════════════════════════════╗",
                    "║              J E D I   F U G I T I V E                    ║",
                    "║                     CONTROLS & HELP                       ║",
                    "╚═══════════════════════════════════════════════════════════╝",
                    "",
                    "MOVEMENT:",
                    "  Arrow Keys = Standard directional (↑↓←→)",
                    "  hjkl       = Vi-style cardinal movement",
                    "  ybn        = Vi-style diagonal (y=↖ b=↙ n=↘)",
                    "  Numpad 1379 = Numpad diagonal (7=↖ 9=↗ 1=↙ 3=↘)",
                    "",
                    "ACTIONS:",
                    "  g = Pick up item at your location",
                    "  e = Equip weapon or armor from inventory",
                    "  u = Use/consume item (stimpack, artifact, etc.)",
                    "  d = Drop item from inventory",
                    "  x = Inspect tile (examine objects/enemies)",
                    "",
                    "COMBAT:",
                    "  Walk into enemy = Attack in melee",
                    "  t = Throw grenade (targeting, 3-tile range)",
                    "  F = Fire ranged weapon (targeting, weapon-dependent range)",
                    "",
                    "FORCE ABILITIES:",
                    "  f = Open Force powers menu",
                    "  c = Scan/Compass (locate nearby tombs)",
                    "",
                    "INFORMATION:",
                    "  j = Journal/Travel Log (view your story)",
                    "  i = Inventory (view/manage items)",
                    "  @ = Character sheet (stats & abilities)",
                    "  v = Sith Codex (lore & discoveries)",
                    "",
                    "CRAFTING & EQUIPMENT:",
                    "  C = Crafting Bench (upgrade weapons, craft items)",
                    "  Shields and offhand weapons available!",
                    "  Dual-wield: Equip 1H weapon + 1H weapon",
                    "  Tank: Equip 1H weapon + Shield",
                    "",
                    "ARTIFACT CHOICES (Critical!):",
                    "  When using artifacts, you'll be prompted:",
                    "    'a' = ABSORB → Dark Side path (+corruption, dark powers)",
                    "    'd' = DESTROY → Light Side path (-corruption, light powers)",
                    "",
                    "ALIGNMENT:",
                    "  Your choices shape who you become:",
                    "    0-30% corruption   = Light Side Jedi",
                    "    31-59% corruption  = Balanced Force User",
                    "    60-100% corruption = Dark Side Sith",
                    "",
                    "OTHER:",
                    "  ? = Show this help screen",
                    "  m = Meditate (reduce stress if safe)",
                    "  r = Reveal map (debug/cheat)",
                    "  q / ESC = Quit game",
                    "",
                    "Press any key to close..."
                ]
                _show_centered(game, help_lines, title="Help")
            except Exception:
                try: game.ui.messages.add("Help display failed.")
                except Exception: pass
            return

        # Fire weapon (uppercase F) — use targeting mode
        if key == ord('F'):
            try:
                # Check if player has ranged weapon equipped
                weapon = getattr(game.player, 'equipped_weapon', None)
                is_ranged = False
                weapon_range = 5
                
                if weapon:
                    # Check if it's a ranged weapon
                    weapon_name = ''
                    if isinstance(weapon, dict):
                        weapon_name = weapon.get('name', '').lower()
                        weapon_range = weapon.get('range', 5)
                    elif hasattr(weapon, 'name'):
                        weapon_name = weapon.name.lower()
                        weapon_range = getattr(weapon, 'range', 5)
                    
                    if 'blaster' in weapon_name or 'pistol' in weapon_name or 'rifle' in weapon_name:
                        is_ranged = True
                
                if not is_ranged:
                    try: game.ui.messages.add('No ranged weapon equipped!')
                    except Exception: pass
                    return
                
                # Enter targeting mode for gun
                game.pending_gun_shot = True
                game.gun_range = weapon_range
                game.target_x = getattr(game.player, "x", 0)
                game.target_y = getattr(game.player, "y", 0)
                try: game.ui.messages.add(f"Fire Weapon ({weapon_range}-tile range) — move reticle and press Enter, Esc to cancel.")
                except Exception: pass
            except Exception:
                try: game.ui.messages.add('Fire command failed.')
                except Exception: pass
            return

        if key == ord('i'):
            try:
                equipment.inventory_chooser(game)
            except Exception:
                try: game.ui.messages.add("Inventory view failed.") 
                except Exception: pass
            return

        # Inspect / examine (what's in a tile or nearby)
        if key == ord('x'):
            try:
                # determine target coords: prefer pending reticle, then UI cursor, else nearby scan
                tx = None; ty = None
                if getattr(game, 'pending_force_ability', None) is not None and hasattr(game, 'target_x'):
                    tx = getattr(game, 'target_x', None); ty = getattr(game, 'target_y', None)
                elif hasattr(game.ui, 'cursor') and getattr(game.ui.cursor, 'visible', False):
                    tx = getattr(game.ui.cursor, 'x', None); ty = getattr(game.ui.cursor, 'y', None)
                # fallback: inspect adjacent tiles and report nearby foes
                nearby = []
                if tx is None or ty is None:
                    # attempt to inspect the tile the player is facing first
                    try:
                        fdx, fdy = getattr(game.player, 'facing', (1, 0))
                        px = getattr(game.player, 'x', 0); py = getattr(game.player, 'y', 0)
                        fx = px + int(fdx); fy = py + int(fdy)
                        # ensure in bounds
                        mh = len(game.game_map); mw = len(game.game_map[0]) if mh else 0
                        if 0 <= fx < mw and 0 <= fy < mh:
                            # check enemy at facing tile
                            for e in getattr(game, 'enemies', []) or []:
                                try:
                                    if getattr(e, 'x', None) == fx and getattr(e, 'y', None) == fy and getattr(e, 'is_alive', lambda: True)():
                                        # reuse the existing inspect-on-tile flow by setting tx/ty
                                        tx, ty = fx, fy
                                        break
                                except Exception:
                                    continue
                            # if we found an item at facing tile and no enemy, set tx/ty
                            if tx is None and ty is None:
                                found = None
                                for it in getattr(game, 'items_on_map', []) or []:
                                    try:
                                        if it.get('x') == fx and it.get('y') == fy:
                                            found = it
                                            break
                                    except Exception:
                                        continue
                                if found is not None:
                                    # directly report item at facing tile
                                    try:
                                        desc = found.get('name') or found.get('token') or str(found)
                                        # try to resolve via ITEM_DEFS first, then TOKEN_MAP fallback
                                        try:
                                            from jedi_fugitive.items.consumables import ITEM_DEFS
                                            tok = found.get('token') or (found.get('item') and found.get('item').get('token'))
                                            if tok:
                                                for d in ITEM_DEFS:
                                                    if d.get('token') == tok or d.get('id') == tok:
                                                        desc = d.get('name') + ' - ' + d.get('description', '')
                                                        break
                                        except Exception:
                                            pass
                                        try:
                                            from jedi_fugitive.items.tokens import TOKEN_MAP as _tmap
                                            tok = found.get('token') or (found.get('item') and found.get('item').get('token'))
                                            if tok and tok in _tmap:
                                                tinfo = _tmap.get(tok, {})
                                                desc = (tinfo.get('name') or tok) + ' - ' + (tinfo.get('description') or '')
                                        except Exception:
                                            pass
                                        _show_centered(game, [f"Item ahead: {desc} @ {fx},{fy}"], title="Inspect")
                                        return
                                    except Exception:
                                        try: game.ui.messages.add("Inspect failed on item.")
                                        except Exception: pass
                                        return
                            # if tx/ty set to facing tile, fall through to detailed tile inspect
                            if tx is not None and ty is not None:
                                pass
                            else:
                                # First: scan a configurable radius around the player for any
                                # registered landmarks that include 'lore'. If found, surface
                                # their lore (centered dialog when interactive, otherwise
                                # message buffer). This ensures the Inspect key checks "all
                                # around" the player for story content rather than only
                                # facing/enemy tiles.
                                try:
                                    inspect_radius = int(getattr(game, 'inspect_radius', 3) or 3)
                                except Exception:
                                    inspect_radius = 3
                                px = getattr(game.player, 'x', 0); py = getattr(game.player, 'y', 0)
                                lm_map = getattr(game, 'map_landmarks', {}) or {}
                                found_lore_blocks = []
                                found_keys = []
                                try:
                                    for (lx, ly), info in list(lm_map.items()):
                                        try:
                                            if abs(lx - px) + abs(ly - py) <= inspect_radius:
                                                if info and isinstance(info, dict) and info.get('lore'):
                                                    title = info.get('name', 'Point of Interest')
                                                    art = info.get('art') or []
                                                    lore = info.get('lore') or []
                                                    desc = info.get('description', '')
                                                    block = []
                                                    if art:
                                                        block.extend(art)
                                                        block.append('')
                                                    if lore:
                                                        block.append(f"-- {title} --")
                                                        for ln in lore:
                                                            block.append(ln)
                                                        block.append('')
                                                    if desc:
                                                        block.append(desc)
                                                    if block:
                                                        found_lore_blocks.append(block)
                                                        found_keys.append((lx, ly))
                                        except Exception:
                                            continue
                                except Exception:
                                    found_lore_blocks = []

                                # If we found any lore, present them together and mark as consumed.
                                if found_lore_blocks:
                                    out_lines = []
                                    for i, blk in enumerate(found_lore_blocks):
                                        if i > 0:
                                            out_lines.append('')
                                        out_lines.extend(blk)
                                    try:
                                        _show_centered(game, out_lines, title="Nearby Lore")
                                    except Exception:
                                        for ln in out_lines:
                                            try: game.add_message(ln)
                                            except Exception:
                                                try: game.ui.messages.add(ln)
                                                except Exception: pass
                                        # Additionally: for each landmark we inspected, compute and append
                                        # a directional hint to the nearest tomb (if any). This gives
                                        # contextual guidance without being obtrusive.
                                        try:
                                            for k in found_keys:
                                                try:
                                                    info = getattr(game, 'find_nearest_tomb_info', None)
                                                    if callable(info):
                                                        res = game.find_nearest_tomb_info(k[0], k[1])
                                                        if res:
                                                            tx, ty, dist, dstr = res
                                                            hint = f"Hint: the ruins suggest a tomb lies ~{dist} tiles to the {dstr}."
                                                            try: game.add_message(hint)
                                                            except Exception: pass
                                                except Exception:
                                                    continue
                                        except Exception:
                                            pass
                                    # mark lore consumed so it doesn't repeatedly trigger
                                    try:
                                        for k in found_keys:
                                            try:
                                                info = lm_map.get(k, {}) or {}
                                                if 'lore' in info:
                                                    del info['lore']
                                                    lm_map[k] = info
                                            except Exception:
                                                continue
                                        try:
                                            setattr(game, 'map_landmarks', lm_map)
                                        except Exception:
                                            pass
                                    except Exception:
                                        pass
                                    return

                                # collect nearby enemies within 2 tiles as before
                                px = getattr(game.player, 'x', 0); py = getattr(game.player, 'y', 0)
                                nearby = []
                                # continue to existing nearby scan below
                        else:
                            px = getattr(game.player, 'x', 0); py = getattr(game.player, 'y', 0)
                            nearby = []
                    except Exception:
                        px = getattr(game.player, 'x', 0); py = getattr(game.player, 'y', 0)
                        nearby = []
                    for e in getattr(game, 'enemies', []) or []:
                        try:
                            if not getattr(e, 'is_alive', lambda: True)():
                                continue
                            ex = int(getattr(e, 'x', -999)); ey = int(getattr(e, 'y', -999))
                            dist = abs(ex - px) + abs(ey - py)
                            if dist <= 2:
                                nearby.append((dist, e))
                        except Exception:
                            continue
                    if nearby:
                        nearby.sort(key=lambda t: t[0])
                        lines = []
                        for d, e in nearby:
                            try:
                                name = getattr(e, 'name', str(e))
                                hp = getattr(e, 'hp', None); mhp = getattr(e, 'max_hp', None)
                                lvl = getattr(e, 'level', None)
                                parts = [f"{name} (dist {d})"]
                                if hp is not None:
                                    parts.append(f"HP: {hp}{('/'+str(mhp)) if mhp else ''}")
                                if lvl is not None:
                                    parts.append(f"Lvl: {lvl}")
                                lines.append(" | ".join(parts))
                            except Exception:
                                continue
                        _show_centered(game, lines, title="Nearby")
                        return
                    # nothing nearby
                    _show_centered(game, ["Nothing of interest nearby."], title="Inspect")
                    return

                # If we have coordinates, inspect that tile
                try:
                    if tx is None or ty is None:
                        try: game.add_message("Inspect target unknown."); return
                        except Exception: return
                    # check for an enemy at that tile
                    enemy = None
                    for e in getattr(game, 'enemies', []) or []:
                        try:
                            if getattr(e, 'x', None) == tx and getattr(e, 'y', None) == ty and getattr(e, 'is_alive', lambda: True)():
                                enemy = e; break
                        except Exception:
                            continue
                    if enemy:
                        try:
                            parts = []
                            parts.append(f"{getattr(enemy,'name','Enemy')} @ {tx},{ty}")
                            if hasattr(enemy, 'hp') and hasattr(enemy, 'max_hp'):
                                parts.append(f"HP: {enemy.hp}/{enemy.max_hp}")
                            elif hasattr(enemy, 'hp'):
                                parts.append(f"HP: {enemy.hp}")
                            if hasattr(enemy, 'level'):
                                parts.append(f"Level: {getattr(enemy,'level')}")
                            if hasattr(enemy, 'attack'):
                                parts.append(f"Atk: {getattr(enemy,'attack')}")
                            if hasattr(enemy, 'defense'):
                                parts.append(f"Def: {getattr(enemy,'defense')}")
                            # abilities summary if present
                            fas = getattr(enemy, 'force_abilities', None)
                            if fas:
                                try:
                                    names = [getattr(a,'name',str(a)) for a in (fas.values() if hasattr(fas,'values') else fas)]
                                    parts.append(f"Abilities: {', '.join(names)}")
                                except Exception:
                                    pass
                            _show_centered(game, [" -- ".join(parts)], title=getattr(enemy,'name','Enemy'))
                        except Exception:
                            try: game.ui.messages.add("Inspect failed on enemy.")
                            except Exception: pass
                        return
                    # else, check items_on_map
                    itm = None
                    for it in getattr(game, 'items_on_map', []) or []:
                        try:
                            if it.get('x') == tx and it.get('y') == ty:
                                itm = it; break
                        except Exception:
                            continue
                    if itm:
                        try:
                            desc = itm.get('name') or itm.get('token') or str(itm)
                            # attempt to resolve token to ITEM_DEFS
                            try:
                                from jedi_fugitive.items.consumables import ITEM_DEFS
                                tok = itm.get('token') or (itm.get('item') and itm.get('item').get('token'))
                                if tok:
                                    for d in ITEM_DEFS:
                                        if d.get('token') == tok or d.get('id') == tok:
                                            desc = d.get('name') + ' - ' + d.get('description', '')
                                            break
                            except Exception:
                                pass
                            # TOKEN_MAP fallback
                            try:
                                from jedi_fugitive.items.tokens import TOKEN_MAP as _tmap
                                tok = itm.get('token') or (itm.get('item') and itm.get('item').get('token'))
                                if tok and tok in _tmap:
                                    tinfo = _tmap.get(tok, {})
                                    desc = (tinfo.get('name') or tok) + ' - ' + (tinfo.get('description') or '')
                            except Exception:
                                pass
                            _show_centered(game, [f"Item: {desc} @ {tx},{ty}"], title="Item")
                        except Exception:
                            try: game.ui.messages.add("Inspect failed on item.")
                            except Exception: pass
                        return
                    # fallback: show tile glyph meaning
                    try:
                        ch = None
                        try: ch = game.game_map[ty][tx]
                        except Exception: ch = None
                        if ch is None:
                            _show_centered(game, ["Nothing at that location."], title="Inspect")
                            return
                        # map common glyphs to words
                        if ch == getattr(Display,'FLOOR','.'):
                            _show_centered(game, [f"Open ground at {tx},{ty}."], title="Tile")
                        elif ch == getattr(Display,'WALL','#'):
                            _show_centered(game, [f"Wall at {tx},{ty}."], title="Tile")
                        elif ch == getattr(Display,'TREE','T'):
                            _show_centered(game, [f"Tree at {tx},{ty}."], title="Tile")
                        elif ch == getattr(Display,'SHIP','S'):
                            _show_centered(game, [f"A crashed ship is here ({tx},{ty})."], title="Tile")
                        elif ch == getattr(Display,'COMMS','C'):
                            _show_centered(game, [f"A comms terminal is here ({tx},{ty})."], title="Tile")
                        else:
                            # check for registered landmarks with lore
                            try:
                                lm = getattr(game, 'map_landmarks', {}) or {}
                                key = (tx, ty)
                                if key in lm:
                                    info = lm.get(key, {})
                                    title = info.get('name', 'Point of Interest')
                                    desc = info.get('description', '')
                                    art = info.get('art')
                                    lore = info.get('lore')
                                    lines = []
                                    if art:
                                        lines.extend(art)
                                        lines.append('')
                                    if lore:
                                        for ln in lore:
                                            lines.append(ln)
                                        lines.append('')
                                    if desc:
                                        lines.append(desc)
                                    if not lines:
                                        lines = [f"{title} at {tx},{ty}"]
                                    _show_centered(game, lines, title=title)
                                else:
                                    _show_centered(game, [f"Tile '{str(ch)}' at {tx},{ty}."], title="Tile")
                            except Exception:
                                _show_centered(game, [f"Tile '{str(ch)}' at {tx},{ty}."], title="Tile")
                    except Exception:
                        try: game.ui.messages.add("Inspect failed (unknown tile).")
                        except Exception: pass
                except Exception:
                    try: game.ui.messages.add("Inspect failed (internal).")
                    except Exception: pass
            except Exception:
                try:
                    game.ui.messages.add("Inspect handling error.")
                except Exception:
                    pass
                # debug trace removed in follow-up
            return

        if key == ord('g'):
            try:
                equipment.pick_up(game)
            except Exception as e:
                try: 
                    import traceback
                    game.ui.messages.add(f"Pick up failed: {str(e)}")
                    # Debug: print to terminal
                    # Error: Pick up error: {e}
                    traceback.print_exc()
                except Exception: pass
            return

        if key == ord('e'):
            try:
                equipment.equip_item(game)
            except Exception as e:
                try: 
                    import traceback
                    game.ui.messages.add(f"Equip failed: {str(e)}")
                    # Debug: print to terminal
                    # Error: Equip error: {e}
                    traceback.print_exc()
                except Exception: pass
            return

        if key == ord('u'):
            try:
                equipment.use_item(game)
            except Exception as e:
                try: 
                    import traceback
                    game.ui.messages.add(f"Use failed: {str(e)}")
                    # Debug: print to terminal
                    # Error: Use error: {e}
                    traceback.print_exc()
                except Exception: pass
            return

        if key == ord('d'):
            try:
                equipment.drop_item(game)
            except Exception:
                try: game.ui.messages.add("Drop failed.") 
                except Exception: pass
            return

        # Destroy POI for XP (capital D) - Light Side action
        if key == ord('D'):
            try:
                px = getattr(game.player, 'x', 0)
                py = getattr(game.player, 'y', 0)
                
                # Check if player is standing on a landmark/POI
                if hasattr(game, 'map_landmarks') and (px, py) in game.map_landmarks:
                    landmark = game.map_landmarks[(px, py)]
                    poi_name = landmark.get('name', 'Point of Interest')
                    
                    # Give XP reward (base 30, plus bonus for certain types) - increased to make Light Side path easier
                    xp_reward = 30
                    
                    # Check if it's a Sith lore POI (give more XP)
                    if 'sith_lore' in landmark:
                        xp_reward = 50
                    
                    # Add XP to player (light side - destroying evil)
                    game.player.light_xp = getattr(game.player, 'light_xp', 0) + xp_reward
                    
                    # Reduce corruption (light side action)
                    game.player.dark_corruption = max(0, game.player.dark_corruption - 5)
                    
                    # Check for level up
                    while game.player.light_xp >= game.player.xp_to_next_light:
                        game.player.light_xp -= game.player.xp_to_next_light
                        game.player.light_level += 1
                        game.player.level = max(game.player.light_level, game.player.dark_level)
                        game.player.xp_to_next_light = int(game.player.xp_to_next_light * 1.5)
                        try:
                            game.player.level_up()
                            try: game.ui.messages.add(f"Level up! Now level {game.player.level}")
                            except Exception: pass
                        except Exception:
                            pass
                    
                    # Remove the POI from map
                    cell = game.game_map[py][px]
                    floor = getattr(Display, "FLOOR", ".")
                    game.game_map[py][px] = floor
                    del game.map_landmarks[(px, py)]
                    
                    # Message with alignment-based narrative
                    try:
                        if hasattr(game.player, 'add_log_entry'):
                            entry = game.player.narrative_text(
                                light_version=f"Destroyed {poi_name} to cleanse this evil place. Gained {xp_reward} XP.",
                                dark_version=f"Destroyed {poi_name}, wasting its power. Gained {xp_reward} XP.",
                                balanced_version=f"Destroyed {poi_name}. Gained {xp_reward} XP."
                            )
                            game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
                    except Exception:
                        pass
                    
                    try: game.ui.messages.add(f"Destroyed {poi_name}! +{xp_reward} XP (Light)")
                    except Exception: pass
                    
                    try:
                        game.turn_count = getattr(game, 'turn_count', 0) + 1
                    except Exception:
                        pass
                else:
                    try: game.ui.messages.add("No POI here to destroy.")
                    except Exception: pass
            except Exception as e:
                try: game.ui.messages.add(f"Destroy failed: {e}")
                except Exception: pass
            return

        # Absorb energy from POI for dark side XP (capital A)
        if key == ord('A'):
            try:
                px = getattr(game.player, 'x', 0)
                py = getattr(game.player, 'y', 0)
                
                # Check if player is standing on a landmark/POI
                if hasattr(game, 'map_landmarks') and (px, py) in game.map_landmarks:
                    landmark = game.map_landmarks[(px, py)]
                    poi_name = landmark.get('name', 'Point of Interest')
                    
                    # Give XP reward (less than destruction - 20 base, 35 for Sith lore) - increased to keep pace
                    xp_reward = 20
                    
                    # Check if it's a Sith lore POI (absorbing Sith energy gives more)
                    if 'sith_lore' in landmark:
                        xp_reward = 35
                    
                    # Add XP to player (dark side - absorbing dark energy)
                    game.player.dark_xp = getattr(game.player, 'dark_xp', 0) + xp_reward
                    
                    # Increase corruption (dark side action)
                    game.player.dark_corruption = min(100, game.player.dark_corruption + 8)
                    
                    # Check for level up
                    while game.player.dark_xp >= game.player.xp_to_next_dark:
                        game.player.dark_xp -= game.player.xp_to_next_dark
                        game.player.dark_level += 1
                        game.player.level = max(game.player.light_level, game.player.dark_level)
                        game.player.xp_to_next_dark = int(game.player.xp_to_next_dark * 1.5)
                        try:
                            game.player.level_up()
                            try: game.ui.messages.add(f"Level up! Now level {game.player.level}")
                            except Exception: pass
                        except Exception:
                            pass
                    
                    # Remove the POI from map
                    cell = game.game_map[py][px]
                    floor = getattr(Display, "FLOOR", ".")
                    game.game_map[py][px] = floor
                    del game.map_landmarks[(px, py)]
                    
                    # Message with alignment-based narrative
                    try:
                        if hasattr(game.player, 'add_log_entry'):
                            entry = game.player.narrative_text(
                                light_version=f"Absorbed dark energy from {poi_name} by necessity. Gained {xp_reward} XP.",
                                dark_version=f"Drained {poi_name}, consuming its dark power! Gained {xp_reward} XP.",
                                balanced_version=f"Absorbed energy from {poi_name}. Gained {xp_reward} XP."
                            )
                            game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
                    except Exception:
                        pass
                    
                    try: game.ui.messages.add(f"Absorbed energy from {poi_name}! +{xp_reward} XP (Dark)")
                    except Exception: pass
                    
                    try:
                        game.turn_count = getattr(game, 'turn_count', 0) + 1
                    except Exception:
                        pass
                else:
                    try: game.ui.messages.add("No POI here to absorb from.")
                    except Exception: pass
            except Exception as e:
                try: game.ui.messages.add(f"Absorb failed: {e}")
                except Exception: pass
            return

        # Throw grenade (targeting mode)
        if key == ord('t'):
            try:
                # Check if player has a grenade
                inv = getattr(game.player, 'inventory', []) or []
                has_grenade = False
                for item in inv:
                    if isinstance(item, dict) and item.get('id') in ['grenade', 'thermal_grenade']:
                        has_grenade = True
                        break
                
                if not has_grenade:
                    try: game.ui.messages.add("No grenades to throw!")
                    except Exception: pass
                    return
                
                # Enter targeting mode
                game.pending_grenade_throw = True
                game.target_x = getattr(game.player, "x", 0)
                game.target_y = getattr(game.player, "y", 0)
                try: game.ui.messages.add("Throw Grenade (3-tile range) — move reticle and press Enter, Esc to cancel.")
                except Exception: pass
            except Exception:
                try: game.ui.messages.add("Grenade throw failed.")
                except Exception: pass
            return

        if key == ord('z'):
            try:
                if hasattr(game, "unequip_item"):
                    game.unequip_item()
                elif hasattr(game.player, "unequip_weapon"):
                    game.player.unequip_weapon(); game.ui.messages.add("Unequipped weapon.")
                else:
                    try: game.ui.messages.add("No unequip available.") 
                    except Exception: pass
            except Exception:
                try: game.ui.messages.add("Unequip failed.") 
                except Exception: pass
            return

        if key == ord('o'):
            try:
                if hasattr(game, "unequip_armor"):
                    game.unequip_armor()
                elif hasattr(game.player, "unequip_armor"):
                    game.player.unequip_armor(); game.ui.messages.add("Unequipped armor.")
                else:
                    try: game.ui.messages.add("No unequip available.") 
                    except Exception: pass
            except Exception:
                try: game.ui.messages.add("Unequip armor failed.") 
                except Exception: pass
            return

        if key == ord('f'):
            try:
                from jedi_fugitive.game.abilities import choose_ability
                chosen = choose_ability(game)
            except Exception:
                chosen = None
            if not chosen:
                # no force ability chosen — try firing ranged weapon instead
                try:
                    weapon = getattr(game.player, 'equipped_weapon', None)
                    is_ranged = False
                    weapon_range = 5
                    
                    if weapon:
                        weapon_name = ''
                        if isinstance(weapon, dict):
                            weapon_name = weapon.get('name', '').lower()
                            weapon_range = weapon.get('range', 5)
                        elif hasattr(weapon, 'name'):
                            weapon_name = weapon.name.lower()
                            weapon_range = getattr(weapon, 'range', 5)
                        
                        if 'blaster' in weapon_name or 'pistol' in weapon_name or 'rifle' in weapon_name or 'bowcaster' in weapon_name:
                            is_ranged = True
                    
                    if is_ranged:
                        # Enter targeting mode for gun
                        game.pending_gun_shot = True
                        game.gun_range = weapon_range
                        game.target_x = getattr(game.player, "x", 0)
                        game.target_y = getattr(game.player, "y", 0)
                        try: game.ui.messages.add(f"Fire Weapon ({weapon_range}-tile range) — move reticle and press Enter, Esc to cancel.")
                        except Exception: pass
                        return
                    else:
                        try: game.ui.messages.add('No Force ability or ranged weapon available.')
                        except Exception: pass
                except Exception:
                    try: game.ui.messages.add('No force ability or ranged fire available.')
                    except Exception: pass
                return
            game.pending_force_ability = chosen
            game.target_x = getattr(game.player, "x", 0); game.target_y = getattr(game.player, "y", 0)
            try: game.ui.messages.add(f"Targeting: {getattr(chosen,'name',str(chosen))} — move reticle and press Enter to confirm, Esc to cancel.")
            except Exception: pass
            return

        # Meditate: spend a turn to reduce stress if safe
        # View travel log (journal)
        if key == ord('j'):
            try:
                log = getattr(game.player, 'travel_log', [])
                if not log:
                    try: game.ui.messages.add("Your journey has just begun...")
                    except Exception: pass
                else:
                    lines = ["=== TRAVEL LOG ===", ""]
                    for entry in log[-10:]:  # Show last 10 entries
                        turn = entry.get('turn', 0)
                        text = entry.get('text', '')
                        lines.append(f"Turn {turn}: {text}")
                    lines.append("")
                    lines.append("Press any key to close.")
                    _show_centered(game, lines, title="Journey")
            except Exception:
                try: game.ui.messages.add("Cannot view travel log.")
                except Exception: pass
            return

        # Crafting menu (capital C)
        if key == ord('C'):
            try:
                equipment.open_crafting_menu(game)
            except Exception:
                try: game.ui.messages.add("Crafting menu failed.")
                except Exception: pass
            return

        if key == ord('m'):
            try:
                acted = False
                if hasattr(game, 'meditate') and callable(game.meditate):
                    acted = game.meditate()
                if acted:
                    # consume a turn and tick effects
                    try:
                        game.turn_count = getattr(game, 'turn_count', 0) + 1
                        if hasattr(game, '_tick_effects') and callable(game._tick_effects):
                            game._tick_effects()
                    except Exception:
                        pass
                    try: game.ui.messages.add("You take a moment to meditate.")
                    except Exception: pass
                return
            except Exception:
                try: game.ui.messages.add("Meditation failed.")
                except Exception: pass
                return

        # Movement
        if key in move_map:
            dx, dy = move_map[key]
            nx = getattr(game.player, "x", 0) + dx
            ny = getattr(game.player, "y", 0) + dy
            # movement pre-check (no debug traces in production)
            max_y = len(game.game_map); max_x = len(game.game_map[0]) if max_y else 0
            if not (0 <= ny < max_y and 0 <= nx < max_x):
                return
            cell = None
            try: cell = game.game_map[ny][nx]
            except Exception: cell = None

            # resolved cell available as 'cell' (no debug trace)

            # deterministic blocking: allow only floor tiles, stairs, ship/comms, '*' or items
            try:
                wall_char = getattr(Display, "WALL", "#")
                cell_str = str(cell) if cell is not None else ''
                
                # NON-walkable tiles (everything else is walkable)
                non_walkable = {
                    '#',  # walls
                    '~',  # dunes (impassable terrain)
                    'r',  # rocks (large obstacles)
                    'T',  # trees (blocking)
                }
                
                # Block only if it's explicitly non-walkable
                if cell_str in non_walkable:
                    try: game.ui.messages.add("Blocked.")
                    except Exception: pass
                    return
            except Exception:
                # If blocking check fails, allow movement (permissive fallback)
                pass

            # attack if enemy there
            enemy = None
            try:
                if hasattr(game, "enemy_at"):
                    enemy = game.enemy_at(nx, ny)
                else:
                    for e in getattr(game, "enemies", []):
                        if getattr(e, "x", -1) == nx and getattr(e, "y", -1) == ny and getattr(e, "is_alive", lambda: True)():
                            enemy = e; break
            except Exception:
                enemy = None

            if enemy:
                try:
                    perform_player_attack(game, enemy)
                except Exception:
                    try: game.ui.messages.add("Attack failed (internal).")
                    except Exception: pass
                return

            # Prefer centralized mover if available (_try_move_player) which already
            # contains canonical blocking logic used elsewhere in the codebase.
            moved = False
            try:
                if hasattr(game, '_try_move_player') and callable(game._try_move_player):
                    moved = game._try_move_player(dx, dy)
                else:
                    # fallback: same behavior as before
                    game.player.x = nx
                    game.player.y = ny
                    moved = True
            except Exception:
                moved = False

            if moved:
                # movement happened; UI will be updated by caller loop
                pass
                try:
                    game.player.facing = (int(dx), int(dy))
                except Exception:
                    pass
                # increment turn and update visibility
                game.turn_count = getattr(game, "turn_count", 0) + 1
                try:
                    if hasattr(game, "compute_visibility"):
                        game.compute_visibility()
                except Exception:
                    pass
            return

    except Exception:
        try: game.ui.messages.add("Input handling error.") 
        except Exception: pass

def perform_player_attack(game, enemy):
    """Defensive attack wrapper: try game combat then fallback to simple damage with messages."""
    try:
        # count attack as a player turn
        try:
            game.turn_count = getattr(game, 'turn_count', 0) + 1
        except Exception:
            pass
        # Try calling combat function if available
        try:
            from jedi_fugitive.game.combat import player_attack
            player_attack(game.player, enemy, messages=getattr(game.ui, "messages", None), game=game)
        except TypeError:
            try:
                from jedi_fugitive.game.combat import player_attack
                player_attack(game.player, enemy)
            except Exception:
                pass
        except Exception:
            pass

        # Fallback simple attack if enemy still alive
        try:
            if getattr(enemy, "hp", None) is None or getattr(enemy, "hp", 1) > 0:
                atk = int(getattr(game.player, "attack", 1) or 1)
                defn = int(getattr(enemy, "defense", 0) or 0)
                dmg = max(1, atk - defn)
                try:
                    enemy.hp = getattr(enemy, "hp", 0) - dmg
                except Exception:
                    pass
                try:
                    game.ui.messages.add(f"You hit {getattr(enemy,'name','enemy')} for {dmg}.")
                except Exception:
                    pass
        except Exception:
            pass

        # check for death; do NOT award XP for kills. XP is awarded by artifact consumption.
        try:
            hp_after = getattr(enemy, "hp", 0)
            if hp_after <= 0:
                try:
                    game.ui.messages.add(f"{getattr(enemy,'name','Enemy')} was defeated!")
                except Exception:
                    pass

                # Add to travel log with alignment-based narrative
                try:
                    if hasattr(game.player, 'add_log_entry'):
                        enemy_name = getattr(enemy, 'name', 'an enemy')
                        if getattr(enemy, 'is_boss', False):
                            # Boss kill - dramatic narrative
                            entry = game.player.narrative_text(
                                light_version=f"Defeated the fearsome {enemy_name}, bringing justice to the galaxy.",
                                dark_version=f"Crushed {enemy_name} utterly, proving your superior power!",
                                balanced_version=f"Defeated the fearsome {enemy_name} in mortal combat!"
                            )
                        else:
                            # Regular enemy kill
                            entry = game.player.narrative_text(
                                light_version=f"Defended myself against {enemy_name}, seeking only to survive.",
                                dark_version=f"Obliterated {enemy_name} without mercy or hesitation.",
                                balanced_version=f"Slew {enemy_name} in battle."
                            )
                        game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
                        game.player.kills_count = getattr(game.player, 'kills_count', 0) + 1
                except Exception:
                    pass

                # Reduce stress when defeating enemies (victory relief)
                try:
                    # Base stress reduction for defeating an enemy
                    stress_reduction = 2
                    
                    # More stress relief for defeating bosses or tough enemies
                    if is_boss:
                        stress_reduction = 8
                    elif enemy_level >= 3:
                        stress_reduction = 4
                    
                    game.player.reduce_stress(stress_reduction)
                except Exception:
                    pass

                # Grant dark path XP for killing enemies (10 points per kill)
                try:
                    game.player.dark_xp = getattr(game.player, 'dark_xp', 0) + 10
                    # Check for dark side level up
                    if game.player.dark_xp >= getattr(game.player, 'xp_to_next_dark', 100):
                        game.player.dark_level = getattr(game.player, 'dark_level', 1) + 1
                        game.player.dark_xp -= getattr(game.player, 'xp_to_next_dark', 100)
                        
                        # Apply stat bonuses: all stats +1, extra +1 attack for dark path
                        game.player.max_hp = getattr(game.player, 'max_hp', 10) + 5
                        game.player.attack = getattr(game.player, 'attack', 10) + 2  # +2 for dark path
                        game.player.defense = getattr(game.player, 'defense', 5) + 1
                        game.player.evasion = getattr(game.player, 'evasion', 10) + 1
                        game.player.accuracy = getattr(game.player, 'accuracy', 80) + 1
                        
                        game.ui.messages.add(f"Level up! You are now Level {game.player.dark_level}")
                        game.ui.messages.add(f"Dark path: +5 HP, +2 ATK, +1 DEF, +1 EVA, +1 ACC")
                except Exception:
                    pass

                # Equipment drop system - better enemies drop better equipment
                try:
                    from jedi_fugitive.items.weapons import WEAPONS
                    from jedi_fugitive.items.armor import ARMORS
                    from jedi_fugitive.items.consumables import ITEM_DEFS
                    import random
                    
                    enemy_name = getattr(enemy, 'name', '').lower()
                    enemy_level = getattr(enemy, 'level', 1)
                    is_boss = getattr(enemy, 'is_boss', False)
                    
                    # Determine drop chance and equipment tier based on enemy type
                    drop_chance = 0.0
                    equipment_tier = 'common'
                    rare_drop_chance = 0.0
                    
                    if is_boss:
                        drop_chance = 1.0  # Bosses always drop
                        equipment_tier = 'legendary'
                        rare_drop_chance = 0.5
                    elif 'lord' in enemy_name or 'regent' in enemy_name:
                        drop_chance = 0.9
                        equipment_tier = 'rare'
                        rare_drop_chance = 0.3
                    elif 'inquisitor' in enemy_name or 'officer' in enemy_name or 'sorcerer' in enemy_name:
                        drop_chance = 0.6
                        equipment_tier = 'uncommon'
                        rare_drop_chance = 0.15
                    elif 'assassin' in enemy_name or 'warrior' in enemy_name or 'acolyte' in enemy_name:
                        drop_chance = 0.4
                        equipment_tier = 'common'
                        rare_drop_chance = 0.08
                    elif 'trooper' in enemy_name or 'guard' in enemy_name:
                        drop_chance = 0.3
                        equipment_tier = 'common'
                        rare_drop_chance = 0.05
                    else:
                        drop_chance = 0.2
                        equipment_tier = 'common'
                        rare_drop_chance = 0.02
                    
                    # Adjust drop chance by enemy level
                    drop_chance = min(0.95, drop_chance + (enemy_level * 0.02))
                    
                    # Check if equipment drops
                    if random.random() < drop_chance:
                        # Decide drop type: 35% weapon, 15% armor, 15% shield, 15% consumable, 20% material
                        drop_roll = random.random()
                        if drop_roll < 0.35:
                            drop_type = 'weapon'
                        elif drop_roll < 0.50:
                            drop_type = 'armor'
                        elif drop_roll < 0.65:
                            drop_type = 'shield'
                        elif drop_roll < 0.80:
                            drop_type = 'consumable'
                        else:
                            drop_type = 'material'
                        
                        dropped_item = None
                        item_name = ''
                        item_rarity = 'Common'
                        
                        if drop_type == 'weapon':
                            # Get weapon pool based on tier
                            weapon_pool = []
                            
                            if equipment_tier == 'legendary' or (equipment_tier == 'rare' and random.random() < rare_drop_chance):
                                weapon_pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                                             w.rarity in ['Legendary', 'Rare'] and hasattr(w, 'name')]
                            elif equipment_tier == 'rare' or (equipment_tier == 'uncommon' and random.random() < rare_drop_chance):
                                weapon_pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                                             w.rarity in ['Rare', 'Uncommon'] and hasattr(w, 'name')]
                            elif equipment_tier == 'uncommon':
                                weapon_pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                                             w.rarity in ['Uncommon', 'Common'] and hasattr(w, 'name')]
                            else:
                                weapon_pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                                             w.rarity == 'Common' and hasattr(w, 'name')]
                            
                            if not weapon_pool:
                                weapon_pool = [w for w in WEAPONS if hasattr(w, 'name')][:5]
                            
                            if weapon_pool:
                                dropped_item = random.choice(weapon_pool)
                                item_name = getattr(dropped_item, 'name', 'Unknown Weapon')
                                item_rarity = getattr(dropped_item, 'rarity', 'Common')
                        
                        elif drop_type == 'armor':
                            # Get armor pool based on tier
                            armor_pool = []
                            
                            if equipment_tier == 'legendary':
                                armor_pool = [a for a in ARMORS if hasattr(a, 'rarity') and 
                                            a.rarity.lower() in ['epic', 'rare'] and hasattr(a, 'name')]
                            elif equipment_tier == 'rare':
                                armor_pool = [a for a in ARMORS if hasattr(a, 'rarity') and 
                                            a.rarity.lower() in ['rare', 'uncommon'] and hasattr(a, 'name')]
                            elif equipment_tier == 'uncommon':
                                armor_pool = [a for a in ARMORS if hasattr(a, 'rarity') and 
                                            a.rarity.lower() in ['uncommon', 'common'] and hasattr(a, 'name')]
                            else:
                                armor_pool = [a for a in ARMORS if hasattr(a, 'rarity') and 
                                            a.rarity.lower() == 'common' and hasattr(a, 'name')]
                            
                            if not armor_pool and ARMORS:
                                armor_pool = ARMORS[:2]  # Fallback
                            
                            if armor_pool:
                                dropped_item = random.choice(armor_pool)
                                item_name = getattr(dropped_item, 'name', 'Unknown Armor')
                                item_rarity = getattr(dropped_item, 'rarity', 'common').capitalize()
                        
                        elif drop_type == 'shield':
                            # Get shield pool based on tier
                            from jedi_fugitive.items.shields import SHIELDS
                            shield_pool = []
                            
                            if equipment_tier == 'legendary':
                                shield_pool = [s for s in SHIELDS if hasattr(s, 'rarity') and 
                                            s.rarity in ['Legendary', 'Rare'] and hasattr(s, 'name')]
                            elif equipment_tier == 'rare':
                                shield_pool = [s for s in SHIELDS if hasattr(s, 'rarity') and 
                                            s.rarity in ['Rare', 'Uncommon'] and hasattr(s, 'name')]
                            elif equipment_tier == 'uncommon':
                                shield_pool = [s for s in SHIELDS if hasattr(s, 'rarity') and 
                                            s.rarity in ['Uncommon', 'Common'] and hasattr(s, 'name')]
                            else:
                                shield_pool = [s for s in SHIELDS if hasattr(s, 'rarity') and 
                                            s.rarity == 'Common' and hasattr(s, 'name')]
                            
                            if not shield_pool and SHIELDS:
                                shield_pool = SHIELDS[:3]  # Fallback
                            
                            if shield_pool:
                                dropped_item = random.choice(shield_pool)
                                item_name = getattr(dropped_item, 'name', 'Unknown Shield')
                                item_rarity = getattr(dropped_item, 'rarity', 'Common')
                        
                        elif drop_type == 'consumable':
                            # Consumables - healing/utility items
                            consumable_pool = []
                            
                            # Better enemies drop better consumables
                            if equipment_tier in ['legendary', 'rare']:
                                # High tier: medkits, grenades, special items
                                consumable_pool = [item for item in ITEM_DEFS 
                                                 if item.get('type') == 'consumable' and 
                                                 item.get('id') in ['medkit_small', 'grenade', 'nutrient_paste', 
                                                                   'jedi_meditation_focus', 'ration']]
                            elif equipment_tier == 'uncommon':
                                # Mid tier: stimpacks, rations
                                consumable_pool = [item for item in ITEM_DEFS 
                                                 if item.get('type') == 'consumable' and 
                                                 item.get('id') in ['stimpack', 'ration', 'water_canteen', 'calming_tea']]
                            else:
                                # Low tier: basic healing
                                consumable_pool = [item for item in ITEM_DEFS 
                                                 if item.get('type') == 'consumable' and 
                                                 item.get('id') in ['water_canteen', 'calming_tea']]
                            
                            if not consumable_pool:
                                consumable_pool = [item for item in ITEM_DEFS if item.get('type') == 'consumable'][:3]
                            
                            if consumable_pool:
                                dropped_item = random.choice(consumable_pool)
                                item_name = dropped_item.get('name', 'Unknown Item')
                                item_rarity = 'Consumable'
                        
                        elif drop_type == 'material':
                            # Crafting materials - rarity based on enemy tier
                            from jedi_fugitive.items.crafting import MATERIALS
                            material_pool = []
                            
                            # Better enemies drop rarer materials
                            if equipment_tier == 'legendary':
                                # Legendary tier: Kyber, Beskar, Phrik
                                material_pool = [m for m in MATERIALS if m.rarity in ['Legendary', 'Epic']]
                            elif equipment_tier == 'rare':
                                # Rare tier: Cortosis, Energy Cells, Rare Alloys
                                material_pool = [m for m in MATERIALS if m.rarity in ['Epic', 'Rare', 'Uncommon']]
                            elif equipment_tier == 'uncommon':
                                # Uncommon tier: Crystals, Electronics, Rare Alloys
                                material_pool = [m for m in MATERIALS if m.rarity in ['Rare', 'Uncommon', 'Common']]
                            else:
                                # Common tier: Scrap Metal, Common Alloy, Basic parts
                                material_pool = [m for m in MATERIALS if m.rarity in ['Common', 'Uncommon']]
                            
                            if not material_pool:
                                material_pool = MATERIALS[:3]  # Fallback to first 3 materials
                            
                            if material_pool:
                                dropped_item = random.choice(material_pool)
                                item_name = dropped_item.name
                                item_rarity = dropped_item.rarity
                        
                        # Place equipment at enemy's location as a token
                        if dropped_item:
                            try:
                                ex, ey = getattr(enemy, 'x', 0), getattr(enemy, 'y', 0)
                                # Use 'M' token for materials, 'E' token for other equipment drops
                                map_token = 'M' if drop_type == 'material' else 'E'
                                if hasattr(game, 'game_map') and 0 <= ey < len(game.game_map) and 0 <= ex < len(game.game_map[0]):
                                    game.game_map[ey][ex] = map_token
                                    
                                    # Store equipment data for pickup
                                    if not hasattr(game, 'equipment_drops'):
                                        game.equipment_drops = {}
                                    game.equipment_drops[(ex, ey)] = {
                                        'type': drop_type,
                                        'item': dropped_item,
                                        'name': item_name,
                                        'rarity': item_rarity
                                    }
                                    
                                    # Message based on rarity
                                    if item_rarity in ['Legendary', 'Epic']:
                                        game.ui.messages.add(f"★★★ {enemy_name} dropped {item_name} ({drop_type})! ★★★")
                                    elif item_rarity == 'Rare':
                                        game.ui.messages.add(f"★★ {enemy_name} dropped {item_name} ({drop_type})! ★★")
                                    elif item_rarity == 'Uncommon':
                                        game.ui.messages.add(f"★ {enemy_name} dropped {item_name} ({drop_type})")
                                    else:
                                        game.ui.messages.add(f"{enemy_name} dropped {item_name} ({drop_type})")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Check if boss was defeated (victory condition)
                try:
                    if getattr(enemy, 'is_boss', False):
                        try:
                            game.ui.messages.add("The Inquisitor falls! You have triumphed!")
                            game.victory = True
                        except Exception:
                            pass
                except Exception:
                    pass

                # remove dead enemy from list (best-effort)
                try:
                    if enemy in getattr(game, "enemies", []):
                        try: game.enemies.remove(enemy)
                        except Exception: pass
                except Exception:
                    pass
        except Exception:
            pass

    except Exception:
        try:
            game.ui.messages.add("Attack failed (internal).")
        except Exception:
            pass