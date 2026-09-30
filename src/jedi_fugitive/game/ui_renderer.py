import curses
import math
from jedi_fugitive.game.level import Display

def _bresenham_line(x0, y0, x1, y1):
    """Yield points on a line from (x0,y0) to (x1,y1) (inclusive) using Bresenham."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        yield x, y
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy

def draw(game):
    # delegate to panel drawers
    draw_map_panel(game)
    draw_stats_panel(game)
    draw_abilities_panel(game)
    draw_commands_panel(game)
    try:
        game.ui.message_panel_draw()
    except Exception:
        pass
    
    # Draw Sith Codex overlay if toggled
    try:
        if getattr(game, 'show_codex', False) and getattr(game, 'sith_codex', None):
            game.ui.draw_sith_codex(game.sith_codex, game.show_codex)
    except Exception:
        pass

def draw_map_panel(game):
    # Check if map display is toggled off
    if not getattr(game, 'map_visible', True):
        panel = game.ui.panels.get('map') if getattr(game.ui, "panels", None) else None
        if panel:
            try:
                panel.clear()
                panel.border()
                panel.addstr(1, 2, "Map Display: OFF", curses.A_BOLD | curses.color_pair(6))
                panel.addstr(2, 2, "Press 'M' to toggle", curses.color_pair(4))
                panel.refresh()
            except Exception:
                pass
        return
        
    panel = game.ui.panels.get('map') if getattr(game.ui, "panels", None) else None
    if not panel:
        panel = game.stdscr
    try:
        panel.clear()
        try: 
            panel.border()
            # Add decorative map title
            try:
                title = " ◈ MAP ◈ "
                panel.addstr(0, 2, title, curses.A_BOLD | curses.color_pair(2))
            except:
                pass
        except Exception: pass
        ph, pw = panel.getmaxyx()
        view_h = max(1, ph - 2)
        view_w = max(1, pw - 2)
        map_h = len(game.game_map)
        map_w = len(game.game_map[0]) if map_h else 0

        px = max(0, min(getattr(game.player, "x", 0), map_w - 1 if map_w else 0))
        py = max(0, min(getattr(game.player, "y", 0), map_h - 1 if map_h else 0))
        half_w = view_w // 2
        half_h = view_h // 2
        start_x = px - half_w
        start_y = py - half_h
        if map_w <= view_w:
            start_x = 0
        else:
            start_x = max(0, min(start_x, map_w - view_w))
        if map_h <= view_h:
            start_y = 0
        else:
            start_y = max(0, min(start_y, map_h - view_h))

        # Use precomputed visibility when available and restrict computations to the viewport.
        # compute_visibility() already considers blocking tiles; here we just intersect with the
        # current viewport to avoid scanning the entire map every frame.
        try:
            global_vis = getattr(game, 'visible', None)
            fog = bool(getattr(game, 'fog_of_war', True))
            if global_vis is None:
                # no precomputed visibility available: fall back to a viewport-local LOS check
                # but limit it to the displayed window for performance
                local_vis = set()
                blocking_chars = {getattr(Display, "WALL", "#"), getattr(Display, "TREE", "T"), getattr(Display, "ROCK", "r")}
                r_min_y = max(0, py - getattr(game.player, 'los_radius', 6))
                r_max_y = min(map_h, py + getattr(game.player, 'los_radius', 6) + 1)
                r_min_x = max(0, px - getattr(game.player, 'los_radius', 6))
                r_max_x = min(map_w, px + getattr(game.player, 'los_radius', 6) + 1)
                for ty in range(max(start_y, r_min_y), min(start_y + view_h, r_max_y)):
                    for tx in range(max(start_x, r_min_x), min(start_x + view_w, r_max_x)):
                        blocked = False
                        for lx, ly in _bresenham_line(px, py, tx, ty):
                            if lx == px and ly == py:
                                continue
                            try:
                                ch = game.game_map[ly][lx]
                            except Exception:
                                ch = None
                            if (ch in blocking_chars or (isinstance(ch, str) and ch and ch[0] in ("#", "|", "+"))):
                                if (lx, ly) == (tx, ty):
                                    # blocking target visible
                                    blocked = False
                                else:
                                    blocked = True
                                break
                        if not blocked:
                            local_vis.add((tx, ty))
                local_visible = local_vis
            else:
                # intersect global visibility with viewport to reduce per-frame checks
                local_visible = set((x, y) for (x, y) in global_vis if start_x <= x < start_x + view_w and start_y <= y < start_y + view_h)
        except Exception:
            local_visible = getattr(game, "visible", set())

        # Render each visible row into the panel as we compute it
        for vy in range(view_h):
            my = start_y + vy
            # clear or empty row if outside map bounds
            if not (0 <= my < map_h):
                try:
                    panel.move(1 + vy, 1); panel.clrtoeol()
                except Exception:
                    pass
                continue

            row = game.game_map[my]
            line_chars = []
            for vx in range(view_w):
                mx = start_x + vx
                if not (0 <= mx < map_w):
                    line_chars.append((' ', curses.color_pair(4)))
                    continue
                ch = row[mx]
                visible = (mx, my) in local_visible
                explored = (mx, my) in getattr(game, "explored", set())
                # If fog_of_war is enabled, hide tiles that are neither visible nor explored.
                explored_flag = explored or (not fog)
                if not visible and not explored_flag:
                    line_chars.append((' ', curses.color_pair(4))); continue

                # Glyph choice: use lowercase for alphabetic tokens when not currently visible (smaller visual)
                glyph = ch
                if isinstance(ch, str) and ch.isalpha():
                    if not visible and explored:
                        glyph = ch.lower()
                    else:
                        glyph = ch

                # Color choices (with biome-aware floor variants)
                try:
                    if ch == Display.WALL:
                        color = curses.color_pair(5)
                    elif ch in (getattr(Display, "GOLD", "G"), getattr(Display, "ARTIFACT", None), getattr(Display, "POTION", None)):
                        color = curses.color_pair(3)
                    elif ch == getattr(Display, "WRECKAGE", None):
                        color = curses.color_pair(7)
                    elif ch == getattr(Display, "TREE", "T"):
                        color = curses.color_pair(8)
                    elif ch == getattr(Display, "ROCK", "r"):
                        # rocks / boulders render with a rocky glyph and distinct color
                        color = curses.color_pair(15)
                        glyph = '^'
                    elif ch == getattr(Display, "FLOOR", '.'):
                        # choose biome glyph/color when tile is a floor
                        try:
                            biome = None
                            if getattr(game, 'map_biomes', None) and 0 <= my < len(game.map_biomes) and 0 <= mx < len(game.map_biomes[0]):
                                biome = game.map_biomes[my][mx]
                            if biome == 'forest':
                                # grassy floor
                                glyph = ',' if visible else ','
                                color = curses.color_pair(10)
                                line_chars.append((glyph, color)); continue
                            elif biome == 'desert':
                                glyph = '~' if visible else '~'
                                color = curses.color_pair(14)
                                line_chars.append((glyph, color)); continue
                            elif biome == 'rocky':
                                glyph = '^' if visible else '^'
                                color = curses.color_pair(15)
                                line_chars.append((glyph, color)); continue
                            else:
                                # plains / fallback
                                color = curses.color_pair(4)
                        except Exception:
                            color = curses.color_pair(4)
                    elif ch == 'D' or ch == getattr(Display, "SITH_TOMB", "X") or ch == getattr(Display, "SITH_ENTRANCE", "D"):
                        # TOMB ENTRANCE: Render 'D' tiles with ominous dark red color and make them stand out
                        glyph = 'D'
                        color = curses.color_pair(2) | curses.A_BOLD  # Bright red, bold
                    else:
                        # Check if this character is a token and use its color
                        try:
                            from jedi_fugitive.items.tokens import TOKEN_MAP
                            if ch in TOKEN_MAP:
                                token_color = TOKEN_MAP[ch].get('color', 'white')
                                color_map = {
                                    'red': curses.color_pair(2), 'green': curses.color_pair(10), 'blue': curses.color_pair(1),
                                    'cyan': curses.color_pair(11), 'yellow': curses.color_pair(3), 'magenta': curses.color_pair(6),
                                    'white': curses.color_pair(4)
                                }
                                color = color_map.get(token_color, curses.color_pair(4)) | curses.A_BOLD
                            else:
                                color = curses.color_pair(4)
                        except Exception:
                            color = curses.color_pair(4)
                except Exception:
                    color = curses.color_pair(4)
                # If tile is not currently visible but has been explored, render it dimmer
                try:
                    attr = color
                    if not visible:
                        # explored but not visible -> dim the glyph
                        attr = color | curses.A_DIM
                    line_chars.append((glyph, attr))
                except Exception:
                    line_chars.append((glyph, color))

            # overlays for this row: player, enemies, projectiles
            player_vx = px - start_x
            player_vy = py - start_y
            if vy == player_vy and 0 <= player_vx < view_w:
                if 0 <= player_vx < len(line_chars):
                    # Player color changes based on dark corruption from artifacts
                    try:
                        corruption = getattr(game.player, 'dark_corruption', 0)
                        if corruption >= 75:
                            # Deep corruption - red/dark
                            player_color = curses.color_pair(2) | curses.A_BOLD  # Red like enemies
                        elif corruption >= 50:
                            # Moderate corruption - orange/yellow
                            player_color = curses.color_pair(3) | curses.A_BOLD  # Yellow
                        elif corruption >= 25:
                            # Light corruption - dim
                            player_color = curses.color_pair(1) | curses.A_DIM  # Dimmed cyan
                        else:
                            # Pure - bright cyan
                            player_color = curses.color_pair(1) | curses.A_BOLD  # Normal cyan
                    except Exception:
                        player_color = curses.color_pair(1) | curses.A_BOLD
                    line_chars[player_vx] = ('@', player_color)

            # Render fauna encounters on the map
            try:
                if hasattr(game, 'fauna_manager') and hasattr(game.fauna_manager, 'active_encounters'):
                    for encounter_key, encounter in game.fauna_manager.active_encounters.items():
                        try:
                            # Use stored encounter location if available, otherwise near player
                            if hasattr(encounter, 'location_x') and hasattr(encounter, 'location_y'):
                                fauna_x = encounter.location_x
                                fauna_y = encounter.location_y
                            else:
                                # Fallback to player position with offset
                                fauna_x = px + (hash(encounter_key) % 3) - 1  # -1 to +1 offset
                                fauna_y = py + (hash(encounter_key + "y") % 3) - 1
                            
                            # Ensure fauna is within map bounds
                            if hasattr(game, 'game_map') and game.game_map:
                                fauna_x = max(0, min(fauna_x, len(game.game_map[0]) - 1))
                                fauna_y = max(0, min(fauna_y, len(game.game_map) - 1))
                            
                            if start_x <= fauna_x < start_x + view_w and start_y <= fauna_y < start_y + view_h:
                                if (fauna_x, fauna_y) in local_visible:
                                    fvx = fauna_x - start_x
                                    fvy = fauna_y - start_y
                                    if fvy == vy and 0 <= fvx < len(line_chars):
                                        # Choose fauna symbol and color based on creature type
                                        fauna_type = encounter.fauna_data.get('type', 'neutral')
                                        fauna_size = encounter.fauna_data.get('size', 'medium')
                                        
                                        # Size-based symbols
                                        if fauna_size == 'tiny':
                                            symbol = '·'  # Small dot
                                        elif fauna_size == 'small':
                                            symbol = 'o'  # Small circle
                                        elif fauna_size == 'medium':
                                            symbol = 'Ω'  # Medium symbol
                                        elif fauna_size == 'large':
                                            symbol = '♦'  # Large diamond
                                        else:  # massive
                                            symbol = '█'  # Massive block
                                        
                                        # Type-based colors with visual distinction
                                        if fauna_type == 'force_sensitive':
                                            color = curses.color_pair(1) | curses.A_BOLD  # Bright cyan
                                        elif fauna_type == 'corrupted':
                                            color = curses.color_pair(6) | curses.A_BOLD  # Dark purple
                                        elif fauna_type == 'aggressive':
                                            color = curses.color_pair(2) | curses.A_BOLD  # Bright red
                                        elif fauna_type == 'passive':
                                            color = curses.color_pair(8) | curses.A_NORMAL # Green
                                        else:  # neutral
                                            color = curses.color_pair(3) | curses.A_NORMAL # Yellow
                                        
                                        line_chars[fvx] = (symbol, color)
                        except Exception:
                            continue
            except Exception:
                pass

            for e in getattr(game, "enemies", []):
                try:
                    if not getattr(e, "is_alive", lambda: False)(): continue
                    ex, ey = getattr(e, "x", -1), getattr(e, "y", -1)
                    if start_x <= ex < start_x + view_w and start_y <= ey < start_y + view_h:
                        if (ex, ey) in local_visible:
                            evx = ex - start_x; evy = ey - start_y
                            if evy == vy and 0 <= evx < len(line_chars):
                                # Enemy symbol based on type - check both 'char' and 'symbol' attributes
                                symbol = getattr(e, 'symbol', getattr(e, 'char', 'E'))
                                
                                # Use single-width Unicode symbols for specific enemy types
                                # Avoid emoji (they're double-width and cause alignment issues)
                                if symbol == 'E': symbol = 'E'   # Generic enemy
                                elif symbol == 'T': symbol = 'T' # Trooper
                                elif symbol == 'G': symbol = 'G' # Ghost
                                elif symbol == 'I': symbol = 'I' # Inquisitor
                                elif symbol == 'J': symbol = 'J' # Jedi Master
                                elif symbol == 'S': symbol = 'S' # Sith
                                elif symbol == 'D': symbol = 'D' # Droid
                                elif symbol == 'B': symbol = 'B' # Boss
                                elif symbol == 'M': symbol = 'M' # Massive creature
                                elif symbol == 'F': symbol = 'f' # Fauna
                                # Otherwise keep the original symbol
                                
                                # Use faction color if available, otherwise default to red
                                enemy_color = getattr(e, 'color', None)
                                if enemy_color is not None:
                                    color = curses.color_pair(enemy_color) | curses.A_BOLD
                                else:
                                    # Default red for enemies without faction
                                    color = curses.color_pair(2) | curses.A_BOLD
                                
                                line_chars[evx] = (symbol, color)
                except Exception:
                    continue

            # Render NPCs on the map
            try:
                npcs_on_map = getattr(game, 'npcs_on_map', {})
                for (npc_x, npc_y), npc in npcs_on_map.items():
                    try:
                        if start_x <= npc_x < start_x + view_w and start_y <= npc_y < start_y + view_h:
                            if (npc_x, npc_y) in local_visible:
                                nvx = npc_x - start_x
                                nvy = npc_y - start_y
                                if nvy == vy and 0 <= nvx < len(line_chars):
                                    # Get NPC symbol and color (use @ to avoid double-width issues)
                                    symbol = '@'
                                    color = curses.color_pair(11) | curses.A_BOLD  # Cyan for NPCs
                                    line_chars[nvx] = (symbol, color)
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                for p in list(getattr(game, "projectiles", []) or []):
                    try:
                        pxp, pyp = int(getattr(p, "x", -999)), int(getattr(p, "y", -999))
                        if start_x <= pxp < start_x + view_w and start_y <= pyp < start_y + view_h:
                            pvx = pxp - start_x; pvy = pyp - start_y
                            if pvy == vy and 0 <= pvx < len(line_chars):
                                sym = str(getattr(p, "symbol", "*"))
                                # choose color based on owner (player vs enemy) when possible
                                try:
                                    owner = getattr(p, 'owner', None)
                                    if owner is getattr(game, 'player', None):
                                        col = curses.color_pair(11) | curses.A_BOLD
                                    else:
                                        col = curses.color_pair(12) | curses.A_BOLD
                                except Exception:
                                    col = curses.color_pair(9) | curses.A_BOLD
                                line_chars[pvx] = (sym, col)
                    except Exception:
                        continue
            except Exception:
                pass

            # write this row to the panel
            x = 1
            for ch, color in line_chars:
                try:
                    panel.addstr(1 + vy, x, ch, color)
                except curses.error:
                    pass
                x += 1

        # draw reticle if using abilities, grenades, or ranged weapons (after all rows drawn)
        is_targeting = (getattr(game, "pending_force_ability", None) is not None or 
                       getattr(game, "pending_gun_shot", False) or 
                       getattr(game, "pending_grenade_throw", False))
        if is_targeting:
            tx, ty = getattr(game, "target_x", 0), getattr(game, "target_y", 0)
            if start_x <= tx < start_x + view_w and start_y <= ty < start_y + view_h:
                cvx = tx - start_x; cvy = ty - start_y
                try: panel.addstr(1 + cvy, 1 + cvx, 'X', curses.color_pair(9) | curses.A_REVERSE | curses.A_BOLD)
                except curses.error: pass

        # HUD arrow: draw a subtle compass arrow at the edge of the map panel
        try:
            tombs = getattr(game, 'tomb_entrances', None) or set()
            if tombs:
                # find nearest tomb
                px = max(0, min(getattr(game.player, "x", 0), map_w - 1 if map_w else 0))
                py = max(0, min(getattr(game.player, "y", 0), map_h - 1 if map_h else 0))
                best = None; best_dist = None
                for (tx, ty) in tombs:
                    try:
                        dx = int(tx) - px; dy = int(ty) - py
                        dist = (dx*dx + dy*dy) ** 0.5
                        if best_dist is None or dist < best_dist:
                            best_dist = dist; best = (tx, ty, dx, dy)
                    except Exception:
                        continue
                if best:
                    tx, ty, dx, dy = best
                    # compute primary compass direction
                    try:
                        import math
                        angle = (math.degrees(math.atan2(-dy, dx)) + 360.0) % 360.0
                        if 22.5 <= angle < 67.5:
                            arrow = '↗'; pos = (1, view_w - 2)
                        elif 67.5 <= angle < 112.5:
                            arrow = '↑'; pos = (1, view_w//2)
                        elif 112.5 <= angle < 157.5:
                            arrow = '↖'; pos = (1, 1)
                        elif 157.5 <= angle < 202.5:
                            arrow = '←'; pos = (view_h//2, 1)
                        elif 202.5 <= angle < 247.5:
                            arrow = '↙'; pos = (view_h - 1, 1)
                        elif 247.5 <= angle < 292.5:
                            arrow = '↓'; pos = (view_h - 1, view_w//2)
                        elif 292.5 <= angle < 337.5:
                            arrow = '↘'; pos = (view_h - 1, view_w - 2)
                        else:
                            arrow = '→'; pos = (view_h//2, view_w - 2)
                    except Exception:
                        arrow = '*'; pos = (view_h//2, view_w - 2)
                    # draw arrow near the border but inside the panel
                    try:
                        ay, ax = pos
                        ay = max(1, min(view_h, ay))
                        ax = max(1, min(view_w - 1, ax))
                        panel.addstr(ay, 1 + ax, arrow, curses.color_pair(3) | curses.A_BOLD)
                    except Exception:
                        pass
        except Exception:
            pass

        # draw per-map popups (positioned over tiles) and age them
        # advance popup ages and purge expired entries
        try:
            game.ui.tick_popups()
        except Exception:
            pass
        if getattr(game, "show_popups", False):
            for p in list(getattr(game.ui, "popups", []) or []):
                try:
                    pxp = int(p.get("x", -999))
                    pyp = int(p.get("y", -999))
                    text = str(p.get("text", ""))
                    col = int(p.get("color", 9))
                    # draw the popup only if within current viewport
                    if start_x <= pxp < start_x + view_w and start_y <= pyp < start_y + view_h:
                        pvx = pxp - start_x; pvy = pyp - start_y
                        # attempt to draw the text at the tile (clamped to view width)
                        try:
                            panel.addstr(1 + pvy, 1 + pvx, text[: max(1, min(len(text), view_w - pvx))], curses.color_pair(col) | curses.A_BOLD)
                        except Exception:
                            pass
                except Exception:
                    # ignore malformed popup entries
                    pass
        try: panel.refresh()
        except curses.error: pass
    except Exception:
        pass

def draw_stats_panel(game):
    panel = getattr(game.ui, "panels", {}).get("stats")
    if not panel: return
    
    # Performance optimization: check if stats changed before redrawing
    # TEMPORARILY DISABLED: Force redraw to ensure corruption property fix displays
    # current_stats_hash = hash(str(getattr(game.player, 'get_stats_display', lambda: [])()))
    # last_hash = getattr(game, '_last_stats_hash', None)
    # 
    # if last_hash == current_stats_hash:
    #     return  # Skip redraw if nothing changed
    # 
    # game._last_stats_hash = current_stats_hash
    
    try:
        panel.clear(); panel.border()
        # SITH AESTHETIC: Dark side header with ominous symbols
        try:
            panel.addstr(0, 2, "╬", curses.A_BOLD | curses.color_pair(7))
            panel.addstr(0, 3, " ◈ POWER STATUS ◈ ", curses.A_BOLD | curses.color_pair(1))
            panel.addstr(0, 21, "╬", curses.A_BOLD | curses.color_pair(7))
        except:
            panel.addstr(0, 2, " POWER STATUS ", curses.A_BOLD | curses.color_pair(1))
        
        # Show objective: Collect 3 Jedi Artifacts
        try:
            artifacts_collected = getattr(game, 'artifacts_collected', 0)
            artifacts_needed = getattr(game, 'artifacts_needed', 3)
            
            # Build objective text based on progress
            if artifacts_collected >= artifacts_needed:
                obj_line = f"⭐ OBJECTIVE COMPLETE: Return to ship! ({artifacts_collected}/{artifacts_needed} artifacts)"
                obj_color = curses.color_pair(2) | curses.A_BOLD  # Green
            elif artifacts_collected > 0:
                obj_line = f"OBJECTIVE: Collect Jedi Artifacts ({artifacts_collected}/{artifacts_needed})"
                obj_color = curses.color_pair(3) | curses.A_BOLD  # Yellow
            else:
                obj_line = f"OBJECTIVE: Find and collect 3 Jedi Artifacts from Sith tombs (0/3)"
                obj_color = curses.color_pair(3)  # Yellow
            
            try:
                panel.addstr(0, max(2, panel.getmaxyx()[1]//2 - len(obj_line)//2), obj_line[: panel.getmaxyx()[1] - 4], obj_color)
            except Exception:
                try: panel.addstr(1, 2, obj_line[: panel.getmaxyx()[1] - 4], obj_color)
                except Exception: pass
        except Exception:
            pass
        stats_lines = game.player.get_stats_display()
        if isinstance(stats_lines, str): stats_lines = stats_lines.splitlines()
        elif not isinstance(stats_lines, (list, tuple)):
            try: stats_lines = list(stats_lines)
            except Exception: stats_lines = [str(stats_lines)]
        for i, line in enumerate(stats_lines[: panel.getmaxyx()[0] - 3]):
            panel.addstr(1 + i, 2, str(line)[: panel.getmaxyx()[1] - 4])
        lower_lines = "\n".join(stats_lines).lower()
        has_lvl = ("level" in lower_lines) or ("xp" in lower_lines) or ("experience" in lower_lines)
        ph = panel.getmaxyx()[0]; left = 2; cur_row = 1 + len(stats_lines)
        if not has_lvl:
            try:
                # Display dual path system clearly
                light_level = getattr(game.player, 'light_level', 1)
                dark_level = getattr(game.player, 'dark_level', 1)
                light_xp = getattr(game.player, 'light_xp', 0)
                dark_xp = getattr(game.player, 'dark_xp', 0)
                light_xp_next = getattr(game.player, 'xp_to_next_light', light_level * 100)
                dark_xp_next = getattr(game.player, 'xp_to_next_dark', dark_level * 100)
                
                # Show Light Side progress
                panel.addstr(cur_row, left, f"#2#Light Level: {light_level}#0# ({light_xp}/{light_xp_next} XP)"[: panel.getmaxyx()[1] - 4])
                cur_row += 1
                
                # Show Dark Side progress
                panel.addstr(cur_row, left, f"#1#Dark Level: {dark_level}#0# ({dark_xp}/{dark_xp_next} XP)"[: panel.getmaxyx()[1] - 4])
                cur_row += 1
                
                # Show Detection Level (Pursuit System)
                if hasattr(game, 'pursuit_system'):
                    detection = game.pursuit_system.detection_level
                    # Color based on level: Green < 30, Yellow < 70, Red >= 70
                    det_color = "#2#" if detection < 30 else "#3#" if detection < 70 else "#1#"
                    panel.addstr(cur_row, left, f"{det_color}Detection: {detection}%#0#"[: panel.getmaxyx()[1] - 4])
                    cur_row += 1
                
            except Exception:
                # Fallback to basic display
                light_level = getattr(game.player, 'light_level', 1)
                dark_level = getattr(game.player, 'dark_level', 1)
                panel.addstr(cur_row, left, f"Light: {light_level}  Dark: {dark_level}"[: panel.getmaxyx()[1] - 4])
                cur_row += 1
            # Stress as a compact bar with description
            # Only show if stress system is active (after first tomb entry) AND currently in a tomb
            try:
                # Check if player is in tomb (tomb_floor is not None)
                in_tomb = getattr(game, 'tomb_floor', None) is not None
                if getattr(game.player, '_stress_system_active', False) and in_tomb:
                    stress = int(getattr(game.player, 'stress', 0) or 0)
                    max_stress = int(getattr(game.player, 'max_stress', 100) or 100)
                    
                    # Get stress description
                    try:
                        desc, color_code = game.player.get_stress_description()
                    except Exception:
                        desc = "Unknown"
                        color_code = 4
                    
                    bw = max(6, min(20, panel.getmaxyx()[1] - left - 10))
                    filled = int(max(0, min(bw, int((stress / max_stress) * bw)))) if max_stress > 0 else 0
                    bar = '[' + ('#' * filled) + ('-' * (bw - filled)) + ']' 
                    
                    # choose a color hint for the bar (low->green, med->yellow, high->red)
                    try:
                        if stress <= max(30, int(0.3 * max_stress)):
                            col = curses.color_pair(2)  # Green
                        elif stress <= max(60, int(0.6 * max_stress)):
                            col = curses.color_pair(3)  # Yellow
                        elif stress < 100:
                            col = curses.color_pair(1) | curses.A_BOLD  # Red bold
                        else:
                            col = curses.color_pair(1) | curses.A_BOLD | curses.A_BLINK  # Red blinking
                    except Exception:
                        col = curses.color_pair(4)
                    
                    # Render stress label with description
                    label = f"Stress [{desc}]: "
                    try:
                        panel.addstr(cur_row + 1, left, label)
                    except Exception:
                        pass
                    try:
                        max_bar_w = max(1, panel.getmaxyx()[1] - (left + len(label) + 2))
                        panel.addstr(cur_row + 1, left + len(label), bar[:max_bar_w], col)
                    except Exception:
                        try:
                            panel.addstr(cur_row + 1, left + len(label), bar[:max(0, panel.getmaxyx()[1] - (left + len(label) - 1))])
                        except Exception:
                            pass
            except Exception:
                try:
                    # Check if player is in tomb (tomb_floor is not None)
                    in_tomb = getattr(game, 'tomb_floor', None) is not None
                    if getattr(game.player, '_stress_system_active', False) and in_tomb:
                        panel.addstr(cur_row + 1, left, f"Stress: {getattr(game.player,'stress',0)}/{getattr(game.player,'max_stress',100)}"[: panel.getmaxyx()[1] - 4])
                except Exception:
                    pass
            # Force Energy bar (Phase 1 system) - Visual bar with tokens
            try:
                # Use new Force Energy system if available
                if hasattr(game.player, 'force_energy'):
                    force_cur = int(getattr(game.player, 'force_energy', 100))
                    force_max = int(getattr(game.player, 'max_force_energy', 100))
                    
                    # Calculate bar width (fits in panel)
                    panel_width = panel.getmaxyx()[1] - 4
                    label = "Force: "
                    bar_width = min(20, panel_width - len(label) - 10)  # Leave room for numbers
                    filled = int((force_cur / force_max) * bar_width) if force_max > 0 else 0
                    
                    # Use block characters for visual meter
                    bar = '█' * filled + '░' * (bar_width - filled)
                    
                    # Color based on Force level
                    if force_cur >= force_max * 0.7:
                        color = curses.color_pair(6) | curses.A_BOLD  # Cyan/bright
                    elif force_cur >= force_max * 0.3:
                        color = curses.color_pair(4)  # Blue
                    else:
                        color = curses.color_pair(5)  # Magenta/warning
                    
                    try:
                        panel.addstr(cur_row + 2, left, label)
                        panel.addstr(cur_row + 2, left + len(label), bar, color)
                        panel.addstr(cur_row + 2, left + len(label) + bar_width + 1, f"{force_cur}/{force_max}")
                    except Exception:
                        # Fallback to simple text
                        panel.addstr(cur_row + 2, left, f"Force: {force_cur}/{force_max}"[: panel.getmaxyx()[1] - 4])
                else:
                    # Fallback to legacy Force Points display
                    fp = int(getattr(game.player, 'force_points', 0) or 0)
                    # Show actual force points number instead of limited dots
                    try:
                        panel.addstr(cur_row + 2, left, f"Force Points: {fp}"[: panel.getmaxyx()[1] - 4])
                    except Exception:
                        panel.addstr(cur_row + 2, left, f"Force: {getattr(game.player,'force_points',0)}"[: panel.getmaxyx()[1] - 4])
            except Exception:
                try:
                    panel.addstr(cur_row + 2, left, f"Force: {getattr(game.player,'force_points',0)}"[: panel.getmaxyx()[1] - 4])
                except Exception:
                    pass
            
            # Display crafting level
            try:
                craft_level = getattr(game.player, 'craft_level', 1)
                craft_xp = getattr(game.player, 'craft_xp', 0)
                craft_xp_to_next = getattr(game.player, 'craft_xp_to_next', 100)
                panel.addstr(cur_row + 3, left, f"Crafting: Lv.{craft_level} ({craft_xp}/{craft_xp_to_next} XP)"[: panel.getmaxyx()[1] - 4])
            except Exception:
                pass
            
            inv_start = cur_row + 5
        else:
            # Display crafting level even when not showing detailed stats
            try:
                craft_level = getattr(game.player, 'craft_level', 1)
                panel.addstr(cur_row, left, f"Crafting: Lv.{craft_level}"[: panel.getmaxyx()[1] - 4])
                inv_start = cur_row + 1
            except Exception:
                inv_start = cur_row
        # --- SYSTEM INTEGRATION: Pursuit, Disguise, Faction, Corruption, Saber ---
        row = inv_start
        panel.addstr(row, 2, "-" * (panel.getmaxyx()[1] - 4))
        row += 1
        # Pursuit/Detection
        pursuit = getattr(game, 'pursuit_system', None)
        if pursuit:
            detection = getattr(pursuit, 'detection_level', None)
            if detection is not None:
                panel.addstr(row, 2, f"Detection: {detection}"[: panel.getmaxyx()[1] - 4], curses.color_pair(3))
                row += 1
        # Suspicion/Disguise
        disguise = getattr(game.player, 'disguise', None)
        suspicion = getattr(game.player, 'suspicion', None)
        if disguise:
            panel.addstr(row, 2, f"Disguise: {getattr(disguise, 'name', str(disguise))}"[: panel.getmaxyx()[1] - 4], curses.color_pair(4))
            row += 1
        if suspicion is not None:
            panel.addstr(row, 2, f"Suspicion: {suspicion}"[: panel.getmaxyx()[1] - 4], curses.color_pair(1))
            row += 1
        # Faction Reputation
        factions = getattr(game, 'faction_manager', None)
        if factions:
            rep = getattr(factions, 'reputation', None)
            if rep:
                for fname, val in rep.items():
                    panel.addstr(row, 2, f"{fname} Rep: {val}"[: panel.getmaxyx()[1] - 4], curses.color_pair(6))
                    row += 1
        # Corruption/Moral
        corruption = getattr(game.player, 'corruption', None)
        if corruption is not None:
            panel.addstr(row, 2, f"Corruption: {corruption}"[: panel.getmaxyx()[1] - 4], curses.color_pair(5))
            row += 1
        # Dynamic Lightsaber
        saber = getattr(game.player, 'lightsaber', None)
        if saber:
            saber_name = getattr(saber, 'name', 'Custom Saber')
            saber_parts = getattr(saber, 'parts', None)
            saber_desc = saber_name
            if saber_parts:
                saber_desc += " [" + ", ".join([getattr(p, 'name', str(p)) for p in saber_parts]) + "]"
            panel.addstr(row, 2, f"Saber: {saber_desc}"[: panel.getmaxyx()[1] - 4], curses.color_pair(2))
            row += 1
        # --- END SYSTEM INTEGRATION ---
        panel.addstr(row, 2, "Inventory:", curses.A_UNDERLINE)
        row += 1
        token_names = {"v": "Vibroblade", "s": "Energy Shield", "b": "Blaster Pistol"}
        inv_lines_limit = max(0, panel.getmaxyx()[0] - row - 3)
        def _item_name(item):
            try:
                if isinstance(item, str):
                    return token_names.get(item, item)
                if isinstance(item, dict):
                    return item.get('name', str(item))
                return getattr(item, 'name', str(item))
            except Exception:
                try: return str(item)
                except Exception: return 'Unknown'

        for i, item in enumerate(game.player.inventory[: inv_lines_limit]):
            name = _item_name(item)
            panel.addstr(row + i, 2, f"- {name}"[: panel.getmaxyx()[1] - 4])
        row += inv_lines_limit
        try:
            panel.addstr(row, 2, "-" * (panel.getmaxyx()[1] - 4))
            # format equipped names safely
            try:
                ew = getattr(game.player, 'equipped_weapon', None)
                eo = getattr(game.player, 'equipped_offhand', None)
                ea = getattr(game.player, 'equipped_armor', None)
                def _fmt(eq):
                    if eq is None:
                        return 'None'
                    if isinstance(eq, dict):
                        return eq.get('name', str(eq))
                    if isinstance(eq, str):
                        return token_names.get(eq, eq)
                    return getattr(eq, 'name', str(eq))
                # Main weapon with ammo if applicable
                weapon_line = f"Main: {_fmt(ew)}"
                ammo_display = ""
                if ew:
                    ammo = None
                    max_ammo = None
                    if isinstance(ew, dict):
                        ammo = ew.get('ammo', None)
                        max_ammo = ew.get('max_ammo', None)
                    elif hasattr(ew, 'ammo'):
                        ammo = getattr(ew, 'ammo', None)
                        max_ammo = getattr(ew, 'max_ammo', None)
                    if ammo is not None:
                        if ammo > 0:
                            if max_ammo and max_ammo > 0:
                                bullet_count = min(10, max_ammo)
                                filled = int((ammo / max_ammo) * bullet_count)
                                ammo_display = f" {'●' * filled}{'○' * (bullet_count - filled)}"
                            else:
                                ammo_display = f" [{ammo}rds]"
                        else:
                            ammo_display = " [EMPTY]"
                try:
                    panel.addstr(row + 1, 2, weapon_line[: panel.getmaxyx()[1] - 4 - len(ammo_display)])
                    if ammo_display:
                        if "[EMPTY]" in ammo_display:
                            color = curses.color_pair(1) | curses.A_BOLD
                        elif '●' in ammo_display:
                            bullets_filled = ammo_display.count('●')
                            bullets_total = ammo_display.count('●') + ammo_display.count('○')
                            if bullets_filled >= bullets_total * 0.7:
                                color = curses.color_pair(2)
                            elif bullets_filled >= bullets_total * 0.3:
                                color = curses.color_pair(3)
                            else:
                                color = curses.color_pair(1)
                        else:
                            color = curses.color_pair(7)
                        panel.addstr(row + 1, 2 + len(weapon_line), ammo_display, color)
                except Exception:
                    panel.addstr(row + 1, 2, (weapon_line + ammo_display)[: panel.getmaxyx()[1] - 4])
                # Offhand
                offhand_line = f"Off: {_fmt(eo)}"
                ammo_display = ""
                if eo:
                    ammo = None
                    max_ammo = None
                    if isinstance(eo, dict):
                        ammo = eo.get('ammo', None)
                        max_ammo = eo.get('max_ammo', None)
                    elif hasattr(eo, 'ammo'):
                        ammo = getattr(eo, 'ammo', None)
                        max_ammo = getattr(eo, 'max_ammo', None)
                    if ammo is not None:
                        if ammo > 0:
                            if max_ammo and max_ammo > 0:
                                bullet_count = min(10, max_ammo)
                                filled = int((ammo / max_ammo) * bullet_count)
                                ammo_display = f" {'●' * filled}{'○' * (bullet_count - filled)}"
                            else:
                                ammo_display = f" [{ammo}rds]"
                        else:
                            ammo_display = " [EMPTY]"
                try:
                    panel.addstr(row + 2, 2, offhand_line[: panel.getmaxyx()[1] - 4 - len(ammo_display)])
                    if ammo_display:
                        if "[EMPTY]" in ammo_display:
                            color = curses.color_pair(1) | curses.A_BOLD
                        elif '●' in ammo_display:
                            bullets_filled = ammo_display.count('●')
                            bullets_total = ammo_display.count('●') + ammo_display.count('○')
                            if bullets_filled >= bullets_total * 0.7:
                                color = curses.color_pair(2)
                            elif bullets_filled >= bullets_total * 0.3:
                                color = curses.color_pair(3)
                            else:
                                color = curses.color_pair(1)
                        else:
                            color = curses.color_pair(7)
                        panel.addstr(row + 2, 2 + len(offhand_line), ammo_display, color)
                except Exception:
                    panel.addstr(row + 2, 2, (offhand_line + ammo_display)[: panel.getmaxyx()[1] - 4])
                # Armor
                panel.addstr(row + 3, 2, f"Armor: {_fmt(ea)}"[: panel.getmaxyx()[1] - 4])
            except Exception:
                try:
                    panel.addstr(row + 1, 2, f"W: {getattr(game.player, 'equipped_weapon', 'None')}"[: panel.getmaxyx()[1] - 4])
                    panel.addstr(row + 2, 2, f"Off: {getattr(game.player, 'equipped_offhand', 'None')}"[: panel.getmaxyx()[1] - 4])
                    panel.addstr(row + 3, 2, f"A: {getattr(game.player, 'equipped_armor', 'None')}"[: panel.getmaxyx()[1] - 4])
                except Exception:
                    pass
        except Exception: pass
        # Show what's directly in front of the player at the bottom of the stats panel
        try:
            ph, pw = panel.getmaxyx()
            # compute tile ahead using player's facing (fallback to (1,0))
            px = int(getattr(game.player, 'x', 0) or 0)
            py = int(getattr(game.player, 'y', 0) or 0)
            facing = getattr(game.player, 'facing', (1, 0)) or (1, 0)
            try:
                fx = int(px + int(facing[0]))
                fy = int(py + int(facing[1]))
            except Exception:
                fx, fy = px + 1, py

            ahead_desc = None
            # enemy first
            try:
                for e in getattr(game, 'enemies', []) or []:
                    try:
                        if int(getattr(e, 'x', -999)) == fx and int(getattr(e, 'y', -999)) == fy and getattr(e, 'is_alive', (lambda: True))():
                            ename = getattr(e, 'name', str(e))
                            lvl = getattr(e, 'level', None)
                            hp = getattr(e, 'hp', '?')
                            max_hp = getattr(e, 'max_hp', '?')
                            dist = max(abs(fx - px), abs(fy - py))  # Chebyshev distance
                            
                            # Build detailed ahead description
                            if lvl is not None:
                                ahead_desc = f"{ename} (Lv{lvl}) HP:{hp}/{max_hp} [{dist}t]"
                            else:
                                ahead_desc = f"{ename} HP:{hp}/{max_hp} [{dist}t]"
                            break
                    except Exception:
                        continue
            except Exception:
                ahead_desc = None

            # item on map
            if ahead_desc is None:
                try:
                    for it in getattr(game, 'items_on_map', []) or []:
                        try:
                            if int(it.get('x', -999)) == fx and int(it.get('y', -999)) == fy:
                                # try to resolve name from item defs or token map
                                name = it.get('name') or it.get('token') or str(it)
                                try:
                                    from jedi_fugitive.items.consumables import ITEM_DEFS
                                    tok = it.get('token') or (it.get('item') and it.get('item').get('token'))
                                    if tok:
                                        for d in ITEM_DEFS:
                                            if d.get('token') == tok or d.get('id') == tok:
                                                name = d.get('name') + (" - " + d.get('description', ''))
                                                break
                                except Exception:
                                    pass
                                try:
                                    from jedi_fugitive.items.tokens import TOKEN_MAP as _tmap
                                    tok = it.get('token') or (it.get('item') and it.get('item').get('token'))
                                    if tok and tok in _tmap:
                                        tinfo = _tmap.get(tok, {})
                                        name = (tinfo.get('name') or tok)
                                except Exception:
                                    pass
                                ahead_desc = f"{name}"
                                break
                        except Exception:
                            continue
                except Exception:
                    pass

            # landmark
            if ahead_desc is None:
                try:
                    lm = getattr(game, 'map_landmarks', {}) or {}
                    if (fx, fy) in lm:
                        info = lm.get((fx, fy), {})
                        ahead_desc = info.get('name') or info.get('description') or 'Point of Interest'
                except Exception:
                    pass

            # tile glyph fallback
            if ahead_desc is None:
                try:
                    ch = None
                    if 0 <= fy < len(game.game_map) and 0 <= fx < len(game.game_map[0]):
                        ch = game.game_map[fy][fx]
                    if ch is None:
                        ahead_desc = 'Nothing ahead.'
                    else:
                        from jedi_fugitive.game.level import Display
                        if ch == getattr(Display, 'FLOOR', '.'):
                            ahead_desc = 'Open ground.'
                        elif ch == getattr(Display, 'WALL', '#'):
                            ahead_desc = 'Wall.'
                        elif ch == getattr(Display, 'TREE', 'T'):
                            ahead_desc = 'Tree.'
                        elif ch == getattr(Display, 'SHIP', 'S'):
                            ahead_desc = 'Crashed ship.'
                        elif ch == getattr(Display, 'COMMS', 'C'):
                            ahead_desc = 'Comms terminal.'
                        elif ch == getattr(Display, 'SITH_ENTRANCE', 'D'):
                            ahead_desc = '⚠️ TOMB ENTRANCE - Walk forward to enter'
                        elif ch == getattr(Display, 'STAIRS_DOWN', '>'):
                            ahead_desc = 'Stairs down.'
                        elif ch == getattr(Display, 'STAIRS_UP', '<'):
                            ahead_desc = 'Stairs up.'
                        else:
                            ahead_desc = f"Tile '{str(ch)}'"
                except Exception:
                    ahead_desc = 'Unknown.'

            try:
                panel.addstr(ph - 2, 2, ("Ahead: " + str(ahead_desc))[: pw - 4])
            except Exception:
                try: panel.addstr(ph - 3, 2, ("Ahead: " + str(ahead_desc))[: pw - 4])
                except Exception: pass
        except Exception:
            pass
        panel.refresh()
    except curses.error: pass

def draw_abilities_panel(game):
    panel = getattr(game.ui, "panels", {}).get("abilities")
    if not panel: return
    try:
        panel.clear(); panel.border()
        # ASCII art header with Force symbol
        try:
            panel.addstr(0, 2, "╣", curses.A_BOLD)
            panel.addstr(0, 3, " ✦ ABILITIES ✦ ", curses.A_BOLD | curses.color_pair(5))
            panel.addstr(0, 18, "╠", curses.A_BOLD)
        except:
            panel.addstr(0, 2, " ABILITIES ", curses.A_BOLD)
        abilities = game.player.get_available_abilities() or []
        expanded = []
        for a in abilities:
            from jedi_fugitive.game.force_abilities import ForcePushPull
            if isinstance(a, ForcePushPull):
                class _W:
                    def __init__(self, base, mode):
                        self._base = base; self.mode = mode
                        self.name = f"{mode.capitalize()} - {getattr(base,'name',str(base))}"
                    def __repr__(self): return self.name
                    def use(self, *args, **kwargs):
                        try: return self._base.use(*args, mode=self.mode, **kwargs)
                        except TypeError:
                            try: return self._base.use(*args, self.mode, **kwargs)
                            except Exception: return False
                expanded.append(_W(a, "push")); expanded.append(_W(a, "pull"))
            else:
                expanded.append(a)
        # Calculate available space for abilities
        panel_height = panel.getmaxyx()[0]
        available_space = panel_height - 5  # Leave space for atmospheric events
        
        for i, a in enumerate(expanded[: available_space]):
            a_name = getattr(a, "name", str(a))
            cost = getattr(a, "base_cost", getattr(a, "cost", ""))
            panel.addstr(1 + i, 2, f"{a_name} (Cost:{cost})"[: panel.getmaxyx()[1] - 4])
        
        # Display active atmospheric events at the bottom
        try:
            if hasattr(game, 'atmospheric_manager'):
                events = game.atmospheric_manager.get_active_event_info()
                if events:
                    # Separator line
                    separator_y = min(panel_height - 4, 1 + len(expanded[:available_space]) + 1)
                    panel.addstr(separator_y, 2, "─" * (panel.getmaxyx()[1] - 4))
                    
                    # Events header
                    try:
                        panel.addstr(separator_y + 1, 2, "[ATMOSPHERIC]", curses.A_BOLD | curses.color_pair(3))
                    except:
                        panel.addstr(separator_y + 1, 2, "ATMOSPHERIC:", curses.A_BOLD)
                    
                    # Show first active event
                    if events:
                        event = events[0]  # Show most recent event
                        event_line = f"{event['name']} ({event['remaining']}t)"
                        try:
                            panel.addstr(separator_y + 2, 2, event_line[: panel.getmaxyx()[1] - 4], curses.color_pair(3))
                        except:
                            panel.addstr(separator_y + 2, 2, event_line[: panel.getmaxyx()[1] - 4])
        except Exception:
            pass
            
        panel.refresh()
    except curses.error: pass

def draw_commands_panel(game):
    # Place the commands GUI at the bottom of the terminal (always).
    try:
        panels = getattr(game.ui, "panels", {})
        panel = panels.get("commands")
        th = game.ui.term_h if hasattr(game.ui, "term_h") else game.stdscr.getmaxyx()[0]
        tw = game.ui.term_w if hasattr(game.ui, "term_w") else game.stdscr.getmaxyx()[1]
        cmdh = 5
        cmdw = max(40, tw - 2)
        # bottom: leave 1 line for terminal border
        y = max(0, th - cmdh - 1)
        x = 1
        if not panel:
            try:
                panel = curses.newwin(cmdh, cmdw, y, x)
                panel.border()
                panels["commands"] = panel
                game.ui.panels = panels
            except Exception:
                panel = None
        if not panel:
            return
        panel.clear(); panel.border()
        # ASCII art header with action symbol
        try:
            panel.addstr(0, 2, "╣", curses.A_BOLD)
            panel.addstr(0, 3, " [COMMANDS] ", curses.A_BOLD | curses.color_pair(3))
            panel.addstr(0, 18, "╠", curses.A_BOLD)
        except:
            panel.addstr(0, 2, " COMMANDS ", curses.A_BOLD)
        
        # Compact, organized command layout
        cmds = [
            "Move: ↑↓←→ hjkl  Diag: yubn │ g:Get  e:Equip  u:Use  d:Drop  i:Inventory",
            "Combat: Walk=melee  F:Shoot(2-7 tiles)  t:Grenade │ f:Force  m:Meditate  C:Craft",
            "Info: x:Inspect  j:Journal  K:Codex  S:Stats │ H:Help  Q:Quit"
        ]
        
        ph, pw = panel.getmaxyx()
        for i, line in enumerate(cmds[: max(0, ph - 2)]):
            try: 
                # Center align and truncate if needed
                display_line = line[: max(0, pw - 4)]
                panel.addstr(1 + i, 2, display_line)
            except Exception: 
                pass
        try: panel.refresh()
        except Exception: pass
    except curses.error:
        pass

def animate_projectile(game, sx, sy, ex, ey, symbol='*', delay=0.03, color_pair=9):
    """Animate a projectile from (sx,sy) to (ex,ey) on the map panel (non-blocking UI restore)."""
    try:
        import time, curses
        panel = game.ui.panels.get('map') if getattr(game.ui, "panels", None) else None
        if not panel:
            panel = game.stdscr
        ph, pw = panel.getmaxyx()
        view_h = max(1, ph - 2)
        view_w = max(1, pw - 2)
        # viewport like draw_map_panel (center on player)
        map_h = len(game.game_map)
        map_w = len(game.game_map[0]) if map_h else 0
        px = max(0, min(getattr(game.player, "x", 0), map_w - 1 if map_w else 0))
        py = max(0, min(getattr(game.player, "y", 0), map_h - 1 if map_h else 0))
        half_w = view_w // 2
        half_h = view_h // 2
        start_x = px - half_w
        start_y = py - half_h
        if map_w <= view_w:
            start_x = 0
        else:
            start_x = max(0, min(start_x, map_w - view_w))
        if map_h <= view_h:
            start_y = 0
        else:
            start_y = max(0, min(start_y, map_h - view_h))
        # animate along Bresenham points
        for x, y in _bresenham_line(sx, sy, ex, ey):
            if start_x <= x < start_x + view_w and start_y <= y < start_y + view_h:
                vx = x - start_x
                vy = y - start_y
                try:
                    panel.addstr(1 + vy, 1 + vx, symbol, curses.color_pair(color_pair) | curses.A_BOLD)
                except Exception:
                    pass
                try:
                    panel.refresh()
                except Exception:
                    pass
                # small pause to show travel; very short to avoid blocking UI too long
                try: time.sleep(delay)
                except Exception: pass
        # final redraw to restore correct tiles / actors
        try:
            draw(game)
        except Exception:
            # best-effort fallback to map panel refresh
            try: panel.refresh()
            except Exception: pass
    except Exception:
        # don't raise from animation
        try:
            draw(game)
        except Exception:
            pass