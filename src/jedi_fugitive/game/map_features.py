from jedi_fugitive.game.level import Display, generate_crash_site, generate_dungeon_level, place_items
import random
import traceback
import sys
from jedi_fugitive.game.enemy import Enemy, EnemyPersonality, EnemyType
from jedi_fugitive.game.sith_codex import SITH_LORE
from jedi_fugitive.game import enemies_sith as sith

def generate_world(game):
    """Generate crash site map, scale it, place fewer trees, spawn enemies and place items/tomb entrances."""
    try:
        from jedi_fugitive.game.sith_codex import get_random_loading_message
        print(get_random_loading_message())
        # allow a configurable inflation of the base crash-site size (adds N to width/height)
        crash_inflate = int(getattr(game, 'crash_inflate', 60) or 60)
        base_w = 60
        base_h = 30
        cm, rooms = generate_crash_site(width=base_w + crash_inflate, height=base_h + crash_inflate)
    except Exception as e:
        print(f"⚠ Warning: Crash site generation encountered an issue: {e}")
        try:
            game.ui.messages.add("Crash site generator failed.")
        except Exception:
            pass
        return

    # create a larger surface map but keep the crash_site clearing unchanged
    try:
        outer_scale = int(getattr(game, 'outer_map_scale', 25) or 25)
        try:
            if getattr(game, 'randomize_map_size', True):
                min_scale = max(2, outer_scale // 2)
                max_scale = max(2, outer_scale * 2)
                outer_scale = random.randint(min_scale, max_scale)
        except Exception:
            pass
        h = len(cm)
        w = len(cm[0]) if h else 0
        new_h = max(h, h * outer_scale)
        new_w = max(w, w * outer_scale)

        # initialize a big canvas filled with walls
        big = [[getattr(Display, 'WALL', '#') for _ in range(new_w)] for _ in range(new_h)]

        # compute offsets to center the crash site on the big map
        off_y = (new_h - h) // 2
        off_x = (new_w - w) // 2

        # paste crash site into the center of big canvas
        for yy in range(h):
            for xx in range(w):
                try:
                    big[off_y + yy][off_x + xx] = cm[yy][xx]
                except Exception:
                    continue

        game.game_map = big
        # Expand the pasted crash clearing outward so the walkable area scales
        try:
            floor_ch = getattr(Display, 'FLOOR', '.')
            wall_ch = getattr(Display, 'WALL', '#')
            try:
                walkable_expansion = int(getattr(game, 'walkable_expansion', max(30, crash_inflate // 4)))
            except Exception:
                walkable_expansion = max(30, crash_inflate // 6)
            mh_big = len(game.game_map)
            mw_big = len(game.game_map[0]) if mh_big else 0
            if walkable_expansion > 0 and mh_big and mw_big:
                base_chance = float(getattr(game, 'walkable_expansion_base_chance', 1.0))
                floor_positions = [(x, y) for y in range(mh_big) for x in range(mw_big) if game.game_map[y][x] == floor_ch]
                random.shuffle(floor_positions)
                for (fx, fy) in floor_positions:
                    try:
                        if abs(fx - getattr(game.player, 'x', 0)) + abs(fy - getattr(game.player, 'y', 0)) <= 1:
                            continue
                    except Exception:
                        pass
                    for ddx in range(-walkable_expansion, walkable_expansion + 1):
                        for ddy in range(-walkable_expansion, walkable_expansion + 1):
                            tx = fx + ddx
                            ty = fy + ddy
                            if tx < 0 or ty < 0 or ty >= mh_big or tx >= mw_big:
                                continue
                            try:
                                if game.game_map[ty][tx] != wall_ch:
                                    continue
                            except Exception:
                                continue
                            dist = abs(ddx) + abs(ddy)
                            if dist == 0:
                                continue
                            prob = base_chance * max(0.0, 1.0 - (dist / float(max(1, walkable_expansion + 1))))
                            if random.random() < prob:
                                try:
                                    game.game_map[ty][tx] = floor_ch
                                except Exception:
                                    pass
        except Exception:
            pass

        scaled_rooms = []
        for r in (rooms or []):
            try:
                sx, sy, sw, sh = int(r[0] + off_x), int(r[1] + off_y), int(r[2]), int(r[3])
                scaled_rooms.append((sx, sy, sw, sh))
            except Exception:
                scaled_rooms.append(r)
    except Exception:
        game.game_map = cm
        scaled_rooms = rooms or []

    # Center player on wreckage
    try:
        start = scaled_rooms[0] if scaled_rooms else (0, 0, len(game.game_map[0]), len(game.game_map))
        cx = start[0] + start[2] // 2
        cy = start[1] + start[3] // 2
        
        # Find a wreckage tile in the crash site area
        wreckage_ch = getattr(Display, 'WRECKAGE', 'x')
        found_wreckage = False
        for dy in range(-start[3]//2, start[3]//2 + 1):
            for dx in range(-start[2]//2, start[2]//2 + 1):
                nx = cx + dx
                ny = cy + dy
                if (0 <= nx < len(game.game_map[0]) and 0 <= ny < len(game.game_map) and
                    game.game_map[ny][nx] == wreckage_ch):
                    game.player.x = nx
                    game.player.y = ny
                    found_wreckage = True
                    break
            if found_wreckage:
                break
        
        if not found_wreckage:
            # Fallback to floor tile in crash site
            floor_ch = getattr(Display, 'FLOOR', '.')
            for dy in range(-start[3]//2, start[3]//2 + 1):
                for dx in range(-start[2]//2, start[2]//2 + 1):
                    nx = cx + dx
                    ny = cy + dy
                    if (0 <= nx < len(game.game_map[0]) and 0 <= ny < len(game.game_map) and
                        game.game_map[ny][nx] == floor_ch):
                        game.player.x = nx
                        game.player.y = ny
                        found_wreckage = True
                        break
                if found_wreckage:
                    break
            
            if not found_wreckage:
                game.player.x = cx
                game.player.y = cy
    except Exception:
        game.player.x = 1
        game.player.y = 1

    # generate simple biome regions across the larger map: assign each tile a biome
    try:
        mh = len(game.game_map)
        mw = len(game.game_map[0]) if mh else 0
        biome_types = ['forest', 'desert', 'rocky', 'plains', 'river', 'mountain_pass']
        centers = []
        for _b in range(min(12, max(6, mw * mh // 4000) + 6)):
            cx = random.randint(0, max(0, mw - 1))
            cy = random.randint(0, max(0, mh - 1))
            b = random.choice(biome_types)
            centers.append((cx, cy, b))
        biome_map = [[None for _ in range(mw)] for _ in range(mh)]
        for y in range(mh):
            for x in range(mw):
                best = None
                bdist = None
                for (cx, cy, b) in centers:
                    d = abs(cx - x) + abs(cy - y)
                    if bdist is None or d < bdist:
                        bdist = d
                        best = b
                biome_map[y][x] = best or 'plains'
        game.map_biomes = biome_map
    except Exception:
        game.map_biomes = None

    # Place terrain features (trees, rocks) with biome-specific densities
    try:
        tree_char = getattr(Display, "TREE", "T")
        rock_char = getattr(Display, "ROCK", 'r')
        dune_ch = getattr(Display, 'DUNE', '~')
        floor = getattr(Display, "FLOOR", ".")
        mh = len(game.game_map)
        mw = len(game.game_map[0]) if mh else 0
        area = max(1, mh * mw)
        max_features = int(getattr(game, 'max_trees', max(2000, int(area * 0.08))) or max(2000, int(area * 0.08)))

        forest_density = float(getattr(game, 'tree_density_floor_forest', 0.20) or 0.20)
        plains_density = float(getattr(game, 'tree_density_floor', 0.06) or 0.06)
        rocky_density = float(getattr(game, 'rock_density_floor', 0.12) or 0.12)
        desert_rock_density = float(getattr(game, 'desert_rock_density', 0.08) or 0.08)

        candidates_by_biome = {'forest': [], 'plains': [], 'rocky': [], 'desert': [], 'river': [], 'mountain_pass': []}
        for y in range(mh):
            for x in range(mw):
                try:
                    if game.game_map[y][x] != floor:
                        continue
                except Exception:
                    continue
                b = None
                try:
                    if getattr(game, 'map_biomes', None):
                        b = game.map_biomes[y][x]
                except Exception:
                    b = None
                if b not in candidates_by_biome:
                    b = 'plains'
                candidates_by_biome[b].append((x, y))

        player_clear_radius = int(getattr(game, 'player_clear_radius', 12))

        # Place trees in forest
        placed = 0
        forest_tiles = list(candidates_by_biome['forest'])
        random.shuffle(forest_tiles)
        target_forest = max(1, int(len(forest_tiles) * forest_density))
        for i in range(min(target_forest, len(forest_tiles))):
            tx, ty = forest_tiles[i]
            if placed >= max_features:
                break
            try:
                if (tx, ty) == (game.player.x, game.player.y):
                    continue
                if abs(tx - getattr(game.player, 'x', 0)) + abs(ty - getattr(game.player, 'y', 0)) <= player_clear_radius:
                    continue
            except Exception:
                pass
            game.game_map[ty][tx] = tree_char
            placed += 1

        # Place rocks in rocky biome
        rocky_tiles = list(candidates_by_biome['rocky'])
        random.shuffle(rocky_tiles)
        target_rocky = max(1, int(len(rocky_tiles) * rocky_density))
        for i in range(min(target_rocky, len(rocky_tiles))):
            tx, ty = rocky_tiles[i]
            if placed >= max_features:
                break
            try:
                if (tx, ty) == (game.player.x, game.player.y):
                    continue
                if abs(tx - getattr(game.player, 'x', 0)) + abs(ty - getattr(game.player, 'y', 0)) <= player_clear_radius:
                    continue
            except Exception:
                pass
            game.game_map[ty][tx] = rock_char
            placed += 1

        # Desert rocks
        desert_tiles = list(candidates_by_biome['desert'])
        random.shuffle(desert_tiles)
        target_desert = int(len(desert_tiles) * max(0.04, desert_rock_density))
        for i in range(min(target_desert, len(desert_tiles))):
            tx, ty = desert_tiles[i]
            if placed >= max_features:
                break
            try:
                if (tx, ty) == (game.player.x, game.player.y):
                    continue
                if abs(tx - getattr(game.player, 'x', 0)) + abs(ty - getattr(game.player, 'y', 0)) <= player_clear_radius:
                    continue
            except Exception:
                pass
            if random.random() < 0.6:
                game.game_map[ty][tx] = dune_ch
                placed += 1
            elif random.random() < desert_rock_density:
                game.game_map[ty][tx] = rock_char
                placed += 1

        # Generate rivers with bridges
        river_tiles = list(candidates_by_biome['river'])
        random.shuffle(river_tiles)
        water_char = '~'  # Water tile
        bridge_char = '='  # Bridge tile
        river_density = 0.15  # Density of water tiles in river biome
        
        # Create river paths
        river_paths = []
        num_rivers = max(1, len(river_tiles) // 800)  # 1 river per ~800 tiles
        for _ in range(num_rivers):
            if not river_tiles:
                break
            # Start river from edge
            start_edge = random.choice(['top', 'bottom', 'left', 'right'])
            if start_edge == 'top':
                start_x = random.randint(0, mw-1)
                start_y = 0
            elif start_edge == 'bottom':
                start_x = random.randint(0, mw-1)
                start_y = mh-1
            elif start_edge == 'left':
                start_x = 0
                start_y = random.randint(0, mh-1)
            else:  # right
                start_x = mw-1
                start_y = random.randint(0, mh-1)
            
            # Create winding river path
            path = [(start_x, start_y)]
            current_x, current_y = start_x, start_y
            direction = random.choice(['horizontal', 'vertical', 'diagonal'])
            
            for _ in range(min(50, max(mw, mh) // 4)):  # River length
                if direction == 'horizontal':
                    current_x += random.choice([-1, 1])
                elif direction == 'vertical':
                    current_y += random.choice([-1, 1])
                else:  # diagonal
                    current_x += random.choice([-1, 1])
                    current_y += random.choice([-1, 1])
                
                current_x = max(0, min(mw-1, current_x))
                current_y = max(0, min(mh-1, current_y))
                path.append((current_x, current_y))
                
                # Occasionally change direction
                if random.random() < 0.3:
                    direction = random.choice(['horizontal', 'vertical', 'diagonal'])
            
            river_paths.append(path)
        
        # Place river water and bridges
        for path in river_paths:
            for x, y in path:
                if (x, y) in [(game.player.x, game.player.y)]:
                    continue
                if abs(x - getattr(game.player, 'x', 0)) + abs(y - getattr(game.player, 'y', 0)) <= player_clear_radius:
                    continue
                # Check if this tile is in river biome
                try:
                    if game.map_biomes and game.map_biomes[y][x] == 'river':
                        game.game_map[y][x] = water_char
                except:
                    pass
        
        # Add bridges across rivers
        for path in river_paths:
            # Find potential bridge locations (straight sections)
            for i in range(1, len(path)-1):
                x, y = path[i]
                prev_x, prev_y = path[i-1]
                next_x, next_y = path[i+1]
                
                # Check if this is a straight section
                if (prev_x == x == next_x) or (prev_y == y == next_y):
                    # Place bridge if water is here
                    if game.game_map[y][x] == water_char:
                        game.game_map[y][x] = bridge_char
                        break  # One bridge per river

        # Generate mountain passes
        mountain_tiles = list(candidates_by_biome['mountain_pass'])
        random.shuffle(mountain_tiles)
        mountain_density = 0.25  # Density of mountain tiles
        
        target_mountains = max(1, int(len(mountain_tiles) * mountain_density))
        for i in range(min(target_mountains, len(mountain_tiles))):
            tx, ty = mountain_tiles[i]
            if placed >= max_features:
                break
            try:
                if (tx, ty) == (game.player.x, game.player.y):
                    continue
                if abs(tx - getattr(game.player, 'x', 0)) + abs(ty - getattr(game.player, 'y', 0)) <= player_clear_radius:
                    continue
            except Exception:
                pass
            # Use walls (#) for mountains, but create passes (gaps)
            if random.random() < 0.8:  # 80% chance of mountain, 20% chance of pass
                game.game_map[ty][tx] = getattr(Display, 'WALL', '#')
                placed += 1
    except Exception:
        pass

    # Place richer landmarks and POIs across the larger surface map (increased count)
    try:
        if not hasattr(game, 'map_landmarks') or not isinstance(getattr(game, 'map_landmarks', None), dict):
            game.map_landmarks = {}
        mh = len(game.game_map)
        mw = len(game.game_map[0]) if mh else 0
        area = max(1, mw * mh)
        # Increased POI count - now spawns more landmarks across the map
        landmark_count = max(20, min(80, area // 600))

        templates = [
            (getattr(Display, 'MONOLITH', 'M'), 'Ancient Monolith', 'A towering monolith carved with unreadable runes.'),
            (getattr(Display, 'OUTPOST', 'O'), 'Sith Outpost', 'A fortified outpost bearing Sith sigils and patrol traces.'),
            (getattr(Display, 'ANTENNA', 'A'), 'Comms Antenna', 'A tall antenna, cracked and sparking.'),
            (getattr(Display, 'CRATER', 'o'), 'Impact Crater', 'A shallow crater with scorched earth.'),
            (getattr(Display, 'DRONE', 'd'), 'Scattered Droids', 'A cluster of broken maintenance droids.'),
            (getattr(Display, 'WATCHTOWER', 'W'), 'Ruined Watchtower', 'A collapsed watchtower with vantage.'),
            (getattr(Display, 'STATUE', 'Y'), 'Dark Statue', 'A weathered statue of a hooded Sith Lord, eyes glowing faintly.'),
            (getattr(Display, 'SHRINE', 'H'), 'Sacrificial Shrine', 'An altar stained with ancient rituals, dark energy lingers.'),
            (getattr(Display, 'OBELISK', 'I'), 'Sith Obelisk', 'A black obelisk inscribed with the Sith Code in High Sith.'),
            (getattr(Display, 'ARCHIVE', 'V'), 'Forbidden Archive', 'A sealed vault containing holocrons and forbidden texts.'),
            (getattr(Display, 'FORGE', 'F'), 'Dark Forge', 'A dormant forge where Sith weapons were once crafted.'),
            (getattr(Display, 'ALTAR', 'U'), 'Blood Altar', 'An altar of black stone, channels for dark rituals still visible.'),
            (getattr(Display, 'PILLAR', 'P'), 'Force Pillar', 'A crystalline pillar humming with corrupted Force energy.'),
            (getattr(Display, 'SARCOPHAGUS', 'Q'), 'Sith Sarcophagus', 'An ornate tomb, its occupant long gone but presence felt.'),
            (getattr(Display, 'GATEWAY', 'G'), 'Darksight Gateway', 'A portal frame crackling with unstable dark side energy.'),
            (getattr(Display, 'NEXUS', 'N'), 'Force Nexus', 'A convergence point where the Force tears reality.'),
            (getattr(Display, 'CACHE', 'B'), 'Hidden Cache', 'A concealed stash of weapons and artifacts.'),
            (getattr(Display, 'BEACON', 'J'), 'Sith Beacon', 'A pulsing beacon transmitting ancient Sith frequencies.'),
            (getattr(Display, 'RUINS', 'R'), 'Temple Ruins', 'Collapsed temple chambers, once centers of dark teachings.'),
        ]

        placed_outpost = False
        try:
            cr = scaled_rooms[0] if scaled_rooms else (0, 0, len(game.game_map[0]), len(game.game_map))
            c_rx, c_ry, c_rw, c_rh = cr[0], cr[1], cr[2], cr[3]
        except Exception:
            c_rx = c_ry = c_rw = c_rh = 0

        attempts = 0
        while sum(1 for _ in game.map_landmarks) < landmark_count and attempts < landmark_count * 50:
            attempts += 1
            tpl = random.choice(templates)
            glyph, name, desc = tpl
            lx = random.randint(1, max(1, mw - 2))
            ly = random.randint(1, max(1, mh - 2))
            try:
                if (lx, ly) == (game.player.x, game.player.y):
                    continue
                if name == 'Sith Outpost' and not placed_outpost:
                    try:
                        ox = min(mw - 3, c_rx + c_rw + random.randint(2, max(3, c_rw // 2)))
                        oy = c_ry + random.randint(0, max(0, c_rh - 1))
                        if 0 <= oy < mh and 0 <= ox < mw and game.game_map[oy][ox] == getattr(Display, 'FLOOR', '.'):
                            lx, ly = ox, oy
                    except Exception:
                        pass
                if game.game_map[ly][lx] != getattr(Display, 'FLOOR', '.'):
                    continue
                too_close = False
                for (ex, ey), _v in game.map_landmarks.items():
                    if abs(ex - lx) + abs(ey - ly) < 6:
                        too_close = True
                        break
                if too_close:
                    continue
                game.game_map[ly][lx] = glyph
                entry = {'glyph': glyph, 'name': name, 'description': desc}
                if name == 'Sith Outpost':
                    entry['lore'] = [
                        'A fortified Sith outpost established to monitor the crash site.',
                        'Armored patrols sweep the area; a guarded cache lies nearby.'
                    ]
                    placed_outpost = True
                    # Place guards with patrols
                    guards_needed = random.randint(1, 3)
                    for gi in range(guards_needed):
                        try:
                            g = sith.create_sith_warrior(level=max(1, getattr(game.player, 'level', 1)), x=0, y=0)
                            placed = False
                            for ddx in range(-2, 3):
                                for ddy in range(-2, 3):
                                    gx, gy = lx + ddx, ly + ddy
                                    if 0 <= gy < mh and 0 <= gx < mw and game.game_map[gy][gx] == getattr(Display, 'FLOOR', '.') and (gx, gy) != (game.player.x, game.player.y):
                                        g.x, g.y = gx, gy
                                        game.enemies.append(g)
                                        # Assign patrol
                                        if random.random() < float(getattr(game, 'guard_patrol_chance', 0.6)):
                                            patrol = []
                                            for pi in range(3):
                                                ox = gx + random.randint(-3, 3)
                                                oy = gy + random.randint(-3, 3)
                                                if (0 <= oy < mh and 0 <= ox < mw and game.game_map[oy][ox] == floor and
                                                    abs(ox - game.player.x) + abs(oy - game.player.y) > player_clear_radius):
                                                    patrol.append((ox, oy))
                                            if patrol:
                                                g.patrol_points = patrol
                                                g._patrol_index = 0
                                        placed = True
                                        break
                                if placed:
                                    break
                        except Exception:
                            continue
                    # Place cache
                    for ddx in range(-3, 4):
                        for ddy in range(-3, 4):
                            nx, ny = lx + ddx, ly + ddy
                            if 0 <= ny < mh and 0 <= nx < mw and game.game_map[ny][nx] == getattr(Display, 'FLOOR', '.') and (nx, ny) not in game.map_landmarks:
                                game.game_map[ny][nx] = 'L'
                                loot = {'x': nx, 'y': ny, 'token': 'L', 'name': 'Guarded Supply Cache', 'description': 'A sealed cache; sensors show movement nearby.', 'guarded': True}
                                game.items_on_map.append(loot)
                                break
                        else:
                            continue
                        break
                game.map_landmarks[(lx, ly)] = entry
                
                # Assign lore entries to new POIs for Sith Codex discovery
                try:
                    if not hasattr(game, 'map_lore'):
                        game.map_lore = {}
                    level = getattr(game, 'tomb_floor', 0)
                    
                    # Map POI names to Sith Codex categories and entry IDs
                    lore_mappings = {
                        'Dark Statue': ('sith_lords', 'exar_kun'),
                        'Sacrificial Shrine': ('sith_sorcery', 'blood_sacrifice'),
                        'Sith Obelisk': ('sith_philosophy', 'code'),
                        'Forbidden Archive': ('sith_artifacts', 'ancient_holocrons'),
                        'Dark Forge': ('sith_artifacts', 'sith_swords'),
                        'Blood Altar': ('sith_techniques', 'force_drain'),
                        'Force Pillar': ('sith_techniques', 'force_storm'),
                        'Sith Sarcophagus': ('sith_betrayals', 'plagueis_murdered'),
                        'Darksight Gateway': ('sith_sorcery', 'gate_darkside'),
                        'Force Nexus': ('sith_techniques', 'force_walk'),
                        'Hidden Cache': ('sith_artifacts', 'meditation_spheres'),
                        'Sith Beacon': ('sith_prophecies', 'dark_convergence'),
                        'Temple Ruins': ('sith_history', 'old_republic_war'),
                    }
                    
                    if name in lore_mappings:
                        category, entry_id = lore_mappings[name]
                        game.map_lore[(level, lx, ly)] = (category, entry_id)
                except Exception:
                    pass
                    
            except Exception:
                continue
    except Exception:
        pass

    # Decorative POIs
    try:
        mh = len(game.game_map)
        mw = len(game.game_map[0]) if mh else 0
        floor = getattr(Display, 'FLOOR', '.')
        poi_count = 10  # Increased
        for _p in range(poi_count):
            for _attempt in range(200):
                rx = random.randint(2, max(2, mw - 3))
                ry = random.randint(2, max(2, mh - 3))
                if game.game_map[ry][rx] != floor:
                    continue
                if abs(rx - game.player.x) + abs(ry - game.player.y) < 6:
                    continue
                coords = [(rx, ry), (rx - 1, ry), (rx + 1, ry), (rx, ry - 1), (rx, ry + 1)]
                for cx, cy in coords:
                    try:
                        if 0 <= cy < mh and 0 <= cx < mw and game.game_map[cy][cx] == floor:
                            game.game_map[cy][cx] = '*'
                    except Exception:
                        continue
                break
    except Exception:
        pass

    # Spawn enemies
    try:
        game.enemies = list(getattr(game, 'enemies', []) or [])
        mh = len(game.game_map)
        mw = len(game.game_map[0]) if mh else 0
        area = max(1, mw * mh)
        try:
            from jedi_fugitive.config import DIFFICULTY_MULTIPLIER
        except Exception:
            DIFFICULTY_MULTIPLIER = 0.75
        player_level = getattr(getattr(game, 'player', None), 'level', 1) or 1
        base_spawn = max(2, min(20, int(area // 1000)))
        spawn_factor = 1.0 + max(0, (player_level - 1)) * 0.12 * float(DIFFICULTY_MULTIPLIER)
        spawn_count = max(2, min(8, int(base_spawn * spawn_factor * 0.5)))  # Reduced from 10 to 8 max, and 0.75 to 0.5 multiplier

        # Crash guards - spread them out across the map
        try:
            crash_guard_count = random.randint(1, 2)  # Reduced from 1-3 to 1-2
            floor = getattr(Display, 'FLOOR', '.')
            player_clear_radius = int(getattr(game, 'player_clear_radius', 80))  # Increased from 45 to 80
            
            for i in range(crash_guard_count):
                try:
                    g = sith.create_sith_warrior(level=max(1, getattr(game.player, 'level', 1)), x=0, y=0)
                    
                    # Try to place away from player
                    attempts = 0
                    placed = False
                    while attempts < 100 and not placed:
                        tx = random.randint(1, mw - 2)
                        ty = random.randint(1, mh - 2)
                        if (abs(tx - game.player.x) + abs(ty - game.player.y) > player_clear_radius and
                            game.game_map[ty][tx] == floor):
                            g.x, g.y = tx, ty
                            game.enemies.append(g)
                            placed = True
                        attempts += 1
                    
                    if not placed:
                        # Fallback near ship/comms
                        shippos = getattr(game, 'ship_pos', None)
                        commspos = getattr(game, 'comms_pos', None)
                        target = shippos or commspos or (game.player.x, game.player.y)
                        tx = target[0] + random.randint(-5, 5)
                        ty = target[1] + random.randint(-5, 5)
                        if (0 <= ty < mh and 0 <= tx < mw and 
                            game.game_map[ty][tx] == floor and 
                            (tx, ty) != (game.player.x, game.player.y)):
                            g.x, g.y = tx, ty
                            game.enemies.append(g)
                    
                    # Patrol for crash guards
                    if hasattr(g, 'x') and hasattr(g, 'y'):
                        if random.random() < float(getattr(game, 'crash_guard_patrol_chance', 0.6)):
                            p = []
                            for _r in range(2):
                                ox = g.x + random.randint(-4, 4)
                                oy = g.y + random.randint(-4, 4)
                                if 0 <= oy < mh and 0 <= ox < mw and game.game_map[oy][ox] == floor:
                                    p.append((ox, oy))
                            if p:
                                g.patrol_points = p
                                g._patrol_index = 0
                except Exception:
                    continue
        except Exception:
            pass

        for _ in range(spawn_count):
            personality = EnemyPersonality()
            choice_roll = random.random()
            if choice_roll < 0.4:
                lvl = max(1, min(player_level + random.randint(-1, 1), max(1, player_level + 2)))
                e = sith.create_sith_trooper(level=lvl)
            elif choice_roll < 0.65:
                lvl = max(1, min(player_level + random.randint(0, 2), player_level + 3))
                e = sith.create_sith_acolyte(level=lvl)
            elif choice_roll < 0.85:
                lvl = max(1, player_level + random.randint(0, 3))
                e = sith.create_sith_warrior(level=lvl)
            elif choice_roll < 0.95:
                lvl = max(1, player_level + random.randint(0, 2))
                e = sith.create_sith_sorcerer(level=lvl)
            else:
                lvl = max(2, player_level + random.randint(1, 4))
                e = sith.create_sith_officer(level=lvl)
            try:
                # Spawn across entire map, not just crash site, but keep minimum distance from player
                player_clear_radius = int(getattr(game, 'player_clear_radius', 80))  # Increased from 50 to 80
                attempts = 0
                while attempts < 200:
                    rx = random.randint(1, mw - 2)
                    ry = random.randint(1, mh - 2)
                    if (abs(rx - game.player.x) + abs(ry - game.player.y) > player_clear_radius and
                        game.game_map[ry][rx] == floor):
                        break
                    attempts += 1
                else:
                    # Fallback further from player if we can't find a spot
                    rx = max(1, min(mw - 2, game.player.x + random.randint(-20, 20)))
                    ry = max(1, min(mh - 2, game.player.y + random.randint(-20, 20)))
                    if game.game_map[ry][rx] != floor:
                        for dy in range(-3, 4):
                            for dx in range(-3, 4):
                                nx, ny = rx + dx, ry + dy
                                if 0 <= ny < mh and 0 <= nx < mw and game.game_map[ny][nx] == floor:
                                    rx, ry = nx, ny
                                    break
                            else:
                                continue
                            break
                e.x, e.y = rx, ry
            except Exception:
                e.x = game.player.x + random.choice([-2, -1, 1, 2])
                e.y = game.player.y + random.choice([-2, -1, 1, 2])
            game.enemies.append(e)
            # Patrol for spawned enemies
            try:
                if True:  # Always assign patrol to prevent enemies moving towards player
                    sx, sy = int(getattr(e, 'x', 0)), int(getattr(e, 'y', 0))
                    patrol = []
                    # Wider patrol range to keep enemies spread out
                    for _p in range(random.randint(2, 4)):
                        nx = sx + random.randint(-8, 8)  # Increased from -4,4 to -8,8
                        ny = sy + random.randint(-8, 8)  # Increased from -4,4 to -8,8
                        if (0 <= ny < mh and 0 <= nx < mw and game.game_map[ny][nx] == floor and
                            abs(nx - game.player.x) + abs(ny - game.player.y) > player_clear_radius):
                            patrol.append((nx, ny))
                    if patrol:
                        e.patrol_points = patrol
                        e._patrol_index = 0
            except Exception:
                pass
    except Exception:
        pass

    # Place items
    try:
        mh = len(game.game_map)
        mw = len(game.game_map[0]) if mh else 0
        floor = getattr(Display, "FLOOR", ".")
        try:
            from jedi_fugitive.items.tokens import TOKEN_MAP
            tokens = list(TOKEN_MAP.keys())
            # Weight lightsaber
            try:
                if 'L' in tokens:
                    weight = int(getattr(game, 'lightsaber_weight', 3) or 3)
                    tokens.extend(['L'] * max(0, weight - 1))
            except Exception:
                pass
        except Exception:
            tokens = ['v', 'b', 's']
        game.items_on_map = getattr(game, "items_on_map", []) or []
        placed = 0
        max_items = max(1, min(12, (mw * mh) // 400))
        while placed < max_items and attempts < max_items * 200:
            attempts += 1
            rx = random.randrange(0, mw)
            ry = random.randrange(0, mh)
            try:
                if game.game_map[ry][rx] == floor and (rx, ry) != (game.player.x, game.player.y):
                    token = random.choice(tokens)
                    game.game_map[ry][rx] = token
                    try:
                        from jedi_fugitive.items.tokens import TOKEN_MAP
                        info = TOKEN_MAP.get(token, {})
                        entry = {"x": rx, "y": ry, "token": token, "name": info.get('name'), "type": info.get('type'), "description": info.get('description'), "effect": info.get('effect')}
                    except Exception:
                        entry = {"x": rx, "y": ry, "token": token}
                    game.items_on_map.append(entry)
                    placed += 1
            except Exception:
                continue
    except Exception:
        pass

    # Place one tomb per biome type
    try:
        game.tomb_entrances = set()
        mh = len(game.game_map)
        mw = len(game.game_map[0]) if mh else 0
        floor = getattr(Display, 'FLOOR', '.')

        # Get available biomes from the biome map
        available_biomes = set()
        if hasattr(game, 'map_biomes') and game.map_biomes:
            for y in range(mh):
                for x in range(mw):
                    biome = game.map_biomes[y][x]
                    if biome:
                        available_biomes.add(biome)

        # Place one tomb per biome
        biome_types = ['forest', 'desert', 'rocky', 'plains', 'river', 'mountain_pass']
        placed_tombs = []

        for biome in biome_types:
            if biome not in available_biomes:
                continue

            # Find all floor tiles in this biome
            biome_floor_tiles = []
            for y in range(mh):
                for x in range(mw):
                    if (game.game_map[y][x] == floor and
                        hasattr(game, 'map_biomes') and game.map_biomes and
                        game.map_biomes[y][x] == biome):
                        biome_floor_tiles.append((x, y))

            if not biome_floor_tiles:
                continue

            # Remove tiles too close to player start
            player_clear_radius = int(getattr(game, 'player_clear_radius', 15))
            px, py = game.player.x, game.player.y
            biome_floor_tiles = [(x, y) for x, y in biome_floor_tiles
                               if abs(x - px) + abs(y - py) > player_clear_radius]

            if not biome_floor_tiles:
                continue

            # Choose a random tile in this biome, preferring ones far from other tombs
            random.shuffle(biome_floor_tiles)
            best_tile = None
            best_min_dist = 0

            for tile_x, tile_y in biome_floor_tiles:
                min_dist = float('inf')
                for placed_x, placed_y in placed_tombs:
                    dist = abs(tile_x - placed_x) + abs(tile_y - placed_y)
                    min_dist = min(min_dist, dist)

                # If no tombs placed yet, or this is farther than current best
                if not placed_tombs or min_dist > best_min_dist:
                    best_min_dist = min_dist
                    best_tile = (tile_x, tile_y)

            if best_tile:
                placed_tombs.append(best_tile)
                game.tomb_entrances.add(best_tile)
                # Mark on map with tomb number
                tomb_number = len(placed_tombs)
                game.game_map[best_tile[1]][best_tile[0]] = 'D'

    except Exception:
        # Fallback: place tombs near crash site if randomization fails
        try:
            for y in range(mh):
                for x in range(mw):
                    cell = game.game_map[y][x]
                    try:
                        if str(cell) in ("D",):
                            game.tomb_entrances.add((x, y))
                            try:
                                game.game_map[y][x] = getattr(Display, "SITH_ENTRANCE", str(cell))
                            except Exception:
                                game.game_map[y][x] = str(cell)
                        elif cell == getattr(Display, "SITH_ENTRANCE", None):
                            game.tomb_entrances.add((x, y))
                    except Exception:
                        continue
        except Exception:
            pass

    # Place random Sith lore POIs
    try:
        if not hasattr(game, 'map_landmarks') or not isinstance(getattr(game, 'map_landmarks', None), dict):
            game.map_landmarks = {}

        mh = len(game.game_map)
        mw = len(game.game_map[0]) if mh else 0
        floor = getattr(Display, 'FLOOR', '.')
        area = max(1, mw * mh)

        # Randomize number of lore POIs - SIGNIFICANTLY increased for better engagement during travel
        # With much more lore content available, spawn 20-40 POIs across the map
        lore_poi_count = random.randint(20, min(40, max(20, area // 5000)))

        # Collect all available lore entries
        all_lore_entries = []
        for category, entries in SITH_LORE.items():
            for entry_id, entry_data in entries.items():
                all_lore_entries.append((category, entry_id, entry_data))

        # Shuffle the lore entries
        random.shuffle(all_lore_entries)

        # Available POI glyphs (avoiding conflicts with existing ones)
        # Expanded glyph set for more POIs - mix of question/exclamation with symbols
        poi_glyphs = ['?', '!', '@', '#', '$', '%', '&', '*', '~', '^', '+', '=', '§', '¶', '†', '‡']
        used_glyphs = set()

        # Get existing landmarks to avoid conflicts
        existing_positions = set(game.map_landmarks.keys()) if game.map_landmarks else set()
        existing_positions.update(game.tomb_entrances)

        floor_tiles = [(x, y) for y in range(mh) for x in range(mw)
                      if game.game_map[y][x] == floor and (x, y) not in existing_positions]

        # Remove tiles too close to player start
        player_clear_radius = int(getattr(game, 'player_clear_radius', 40))
        px, py = game.player.x, game.player.y
        floor_tiles = [(x, y) for x, y in floor_tiles if abs(x - px) + abs(y - py) > player_clear_radius]

        random.shuffle(floor_tiles)

        placed_lore = 0
        lore_index = 0

        for tile_x, tile_y in floor_tiles:
            if placed_lore >= lore_poi_count or lore_index >= len(all_lore_entries):
                break

            # Get lore entry
            category, entry_id, entry_data = all_lore_entries[lore_index]
            lore_index += 1

            # Choose a glyph
            available_glyphs = [g for g in poi_glyphs if g not in used_glyphs]
            if not available_glyphs:
                continue
            glyph = random.choice(available_glyphs)
            used_glyphs.add(glyph)

            # Place the POI
            game.game_map[tile_y][tile_x] = glyph

            # Create landmark entry
            lore_entry = {
                'glyph': glyph,
                'name': f"Sith Lore: {entry_data['title']}",
                'description': f"A mysterious artifact containing Sith knowledge: {entry_data['title']}",
                'lore': [entry_data['content']],
                'sith_lore': {
                    'category': category,
                    'entry_id': entry_id,
                    'title': entry_data['title'],
                    'content': entry_data['content'],
                    'force_echo': entry_data.get('force_echo', False)
                }
            }

            game.map_landmarks[(tile_x, tile_y)] = lore_entry
            placed_lore += 1

    except Exception:
        pass

    # Place ship and comms
    try:
        ship_ch = getattr(Display, 'SHIP', 'S')
        comms_ch = getattr(Display, 'COMMS', 'C')
        floor = getattr(Display, 'FLOOR', '.')
        mh = len(game.game_map)
        mw = len(game.game_map[0]) if mh else 0
        placed_ship = False
        for _ in range(300):
            try:
                cr = scaled_rooms[0] if scaled_rooms else (0, 0, len(game.game_map[0]), len(game.game_map))
                cx = cr[0] + cr[2] // 2
                cy = cr[1] + cr[3] // 2
                sx = max(1, min(mw - 2, cx + random.randint(-cr[2] // 2 - 6, cr[2] // 2 + 6)))
                sy = max(1, min(mh - 2, cy + random.randint(-cr[3] // 2 - 6, cr[3] // 2 + 6)))
                if game.game_map[sy][sx] == floor and (sx, sy) != (game.player.x, game.player.y):
                    game.game_map[sy][sx] = ship_ch
                    game.ship_pos = (sx, sy)
                    placed_ship = True
                    break
            except Exception:
                continue
        placed_comms = False
        for _ in range(200):
            try:
                cx = max(1, min(mw - 2, game.player.x + random.randint(-6, 6)))
                cy = max(1, min(mh - 2, game.player.y + random.randint(-6, 6)))
                if game.game_map[cy][cx] == floor and (cx, cy) != (game.player.x, game.player.y):
                    game.game_map[cy][cx] = comms_ch
                    game.comms_pos = (cx, cy)
                    placed_comms = True
                    break
            except Exception:
                continue
        if placed_ship:
            if not hasattr(game, 'map_landmarks'):
                game.map_landmarks = {}
            sx, sy = game.ship_pos
            ship_entry = game.map_landmarks.get((sx, sy), {})
            ship_entry.update({
                'glyph': ship_ch,
                'name': 'Jedi Ship Wreck',
                'description': 'The charred wreck of your Jedi vessel.',
                'lore': [
                    "You recognize the hull plating — it's your ship, crippled and half-buried.",
                    "Comms and power are dead; the ship's logs might hold clues to the crash.",
                    "There may still be salvageable components here, but something watches the wreck."
                ]
            })
            game.map_landmarks[(sx, sy)] = ship_entry
            try:
                game.ui.messages.add("You spot the wreckage of your ship nearby.")
            except Exception:
                pass
    except Exception:
        pass

    # Add directional hints
    try:
        if getattr(game, 'map_landmarks', None) and getattr(game, 'tomb_entrances', None):
            def _dir_from_dxdy(dx, dy):
                if abs(dx) <= 1 and dy < 0:
                    return 'north'
                if abs(dx) <= 1 and dy > 0:
                    return 'south'
                if dx > 0 and abs(dy) <= 1:
                    return 'east'
                if dx < 0 and abs(dy) <= 1:
                    return 'west'
                if dx > 0 and dy < 0:
                    return 'northeast'
                if dx < 0 and dy < 0:
                    return 'northwest'
                if dx > 0 and dy > 0:
                    return 'southeast'
                if dx < 0 and dy > 0:
                    return 'southwest'
                return 'nearby'
            for (lx, ly), info in list(game.map_landmarks.items()):
                try:
                    best = None
                    bdist = None
                    for (tx, ty) in list(game.tomb_entrances):
                        d = abs(tx - lx) + abs(ty - ly)
                        if bdist is None or d < bdist:
                            bdist = d
                            best = (tx, ty)
                    if best and bdist <= int(getattr(game, 'poi_hint_radius', 80)):
                        dx = best[0] - lx
                        dy = best[1] - ly
                        direction = _dir_from_dxdy(dx, dy)
                        hint = f"You find marks here that point {direction}."
                        lore = info.get('lore', []) or []
                        if hint not in lore:
                            lore = list(lore) + [hint]
                            info['lore'] = lore
                            game.map_landmarks[(lx, ly)] = info
                except Exception:
                    continue
    except Exception:
        pass

    # Recompute visibility
    try:
        game.compute_visibility()
    except Exception:
        pass

def enter_tomb(game):
    """Enter a tomb: save surface state, generate dungeon levels, and descend."""
    try:
        # Check if player is on a tomb entrance
        px, py = getattr(game.player, 'x', 0), getattr(game.player, 'y', 0)
        if (px, py) not in getattr(game, 'tomb_entrances', set()):
            return False

        # Save surface state
        game.surface_map = game.game_map
        game.surface_enemies = list(getattr(game, 'enemies', []))
        game.surface_items_on_map = list(getattr(game, 'items_on_map', []))
        game.surface_player_pos = (px, py)
        game.surface_los_radius = getattr(game.player, 'los_radius', 6)

        # Generate dungeon levels (3-5 levels)
        num_levels = random.randint(3, 5)
        game.tomb_levels = []
        game.tomb_rooms = []
        game.tomb_enemies = []
        game.tomb_items = []
        game.tomb_stairs = []

        for depth in range(1, num_levels + 1):
            # Generate level
            level_map, rooms = generate_dungeon_level(depth)
            game.tomb_levels.append(level_map)
            game.tomb_rooms.append(rooms)

            # Find stairs positions
            stairs = {}
            for y in range(len(level_map)):
                for x in range(len(level_map[0])):
                    if level_map[y][x] == Display.STAIRS_UP:
                        stairs['up'] = (x, y)
                    elif level_map[y][x] == Display.STAIRS_DOWN:
                        stairs['down'] = (x, y)
            game.tomb_stairs.append(stairs)

            # Generate enemies for this level
            level_enemies = []
            for room in rooms:
                num_enemies = random.randint(1, 3)
                for _ in range(num_enemies):
                    # Spawn enemies in room
                    ex = random.randint(room[0] + 1, room[0] + room[2] - 2)
                    ey = random.randint(room[1] + 1, room[1] + room[3] - 2)
                    if level_map[ey][ex] == Display.FLOOR:
                        # Create appropriate enemy for depth
                        if depth == 1:
                            enemy = sith.create_sith_trooper(level=max(1, getattr(game.player, 'level', 1)))
                        elif depth == 2:
                            enemy = sith.create_sith_acolyte(level=max(1, getattr(game.player, 'level', 1) + 1))
                        else:
                            enemy = sith.create_sith_warrior(level=max(1, getattr(game.player, 'level', 1) + depth - 1))
                        enemy.x, enemy.y = ex, ey
                        level_enemies.append(enemy)
            game.tomb_enemies.append(level_enemies)

            # Generate items for this level
            level_items = []
            place_items(level_map, rooms, depth)
            
            # Place corrupted Jedi Artifact on the final level
            if depth == num_levels and rooms:
                from jedi_fugitive.items.tokens import TOKEN_MAP
                # Place in the last room (deepest chamber - Sith altar)
                last_room = rooms[-1]
                artifact_x = last_room[0] + last_room[2] // 2
                artifact_y = last_room[1] + last_room[3] // 2
                # Clear the spot and place the artifact
                level_map[artifact_y][artifact_x] = 'Q'
                token_info = TOKEN_MAP.get('Q', {'name': 'Jedi Artifact', 'type': 'quest_item'})
                artifact_entry = {
                    'x': artifact_x, 'y': artifact_y, 'token': 'Q',
                    'name': token_info.get('name', 'Jedi Artifact'),
                    'type': token_info.get('type', 'quest_item'),
                    'description': token_info.get('description', 'Corrupted Jedi relic pulsing with dark energy'),
                    'quest': True
                }
                level_items.append(artifact_entry)
            
            # Convert map items to item objects
            for y in range(len(level_map)):
                for x in range(len(level_map[0])):
                    tile = level_map[y][x]
                    if tile in [Display.GOLD, Display.FOOD, Display.POTION, Display.ARTIFACT]:
                        from jedi_fugitive.items.tokens import TOKEN_MAP
                        token_info = TOKEN_MAP.get(tile, {'name': 'Item', 'type': 'misc'})
                        item_entry = {
                            'x': x, 'y': y, 'token': tile,
                            'name': token_info.get('name', 'Item'),
                            'type': token_info.get('type', 'misc'),
                            'description': token_info.get('description', ''),
                            'effect': token_info.get('effect', '')
                        }
                        level_items.append(item_entry)
            game.tomb_items.append(level_items)

        # Set initial tomb state
        game.tomb_floor = 0
        game.current_depth = 1

        # Set player to first level entrance (stairs up position)
        first_stairs = game.tomb_stairs[0].get('up')
        if first_stairs:
            game.player.x, game.player.y = first_stairs
        else:
            # Fallback to center of first room
            first_room = game.tomb_rooms[0][0] if game.tomb_rooms[0] else (1, 1, 10, 6)
            game.player.x = first_room[0] + first_room[2] // 2
            game.player.y = first_room[1] + first_room[3] // 2

        # Load first level
        game.game_map = game.tomb_levels[0]
        game.enemies = game.tomb_enemies[0]
        game.items_on_map = game.tomb_items[0]

        # Reduce LOS in dungeon
        game.player.los_radius = max(3, getattr(game.player, 'los_radius', 6) - 2)
        
        # First tomb entry - activate permanent stress system
        if not getattr(game.player, '_stress_system_active', False):
            try:
                game.player._stress_system_active = True
                # Add initial stress from the chase
                game.player.stress = 40  # Start at "Tense" level
                
                # Add dramatic message about the initial chase
                if getattr(game, 'ui', None) and getattr(game.ui, 'messages', None):
                    game.ui.messages.add("=== ENTERING THE TOMB ===")
                    game.ui.messages.add("The fanatic's relentless pursuit haunts you still.")
                    game.ui.messages.add("Fear grips your heart - you can't shake the memory of running for your life.")
                    game.ui.messages.add("The stress of the chase lingers... it may never fully leave you.")
                
                # Add to journal
                try:
                    game.player.add_to_travel_log(
                        "[FIRST TOMB] I descended into the darkness, but the terror of being hunted won't leave me. "
                        "The fanatic's pursuit was relentless - I barely escaped with my life. That fear has burrowed "
                        "deep into my mind. I can still hear their footsteps echoing behind me."
                    )
                except Exception:
                    pass
            except Exception:
                pass

        return True

    except Exception as e:
        print(f"Error entering tomb: {e}")
        return False
