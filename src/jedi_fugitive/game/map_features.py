"""
Map Features Module (with logging)
"""
# Map object tags for environmental interaction
OBJECT_TAGS = {
    '#': {"movable": True, "breakable": True},  # Boulder/rock
    'T': {"movable": False, "breakable": True},  # Tree
    'x': {"movable": False, "breakable": True},  # Wreckage
    '=': {"movable": True, "breakable": False},  # Bridge
    'C': {"movable": False, "triggerable": True},  # Comms device
    'D': {"movable": False, "triggerable": True},  # Sith entrance
    # Add more as needed
}

def get_object_tags(tile):
    """Return tag dict for a map tile (movable, breakable, triggerable, etc)."""
    return OBJECT_TAGS.get(tile, {})
from jedi_fugitive.game.level import Display, generate_crash_site, generate_dungeon_level, place_items
import random
import traceback
import sys
from collections import deque
from jedi_fugitive.game.enemy import Enemy, EnemyPersonality, EnemyType
from jedi_fugitive.game.sith_codex import SITH_LORE
from jedi_fugitive.game import enemies_sith as sith

# Surface sizes (tiles). The old generator pasted a ~120x90 crash site into a
# canvas of up to 6000x4500 walls: huge in memory, tiny to explore and ~40 s to
# build. These are real, fully explorable overworlds that generate in seconds.
WORLD_SIZES = {
    'small': (200, 140),
    'normal': (320, 220),
    'large': (440, 300),
    'huge': (640, 440),
}
BIOME_TYPES = ['forest', 'desert', 'rocky', 'plains', 'river', 'mountain_pass']
BLOCKING = frozenset(('#', '~', 'r', 'T'))


def _value_noise(w, h, cell, rnd):
    """Smooth value noise in [0,1] (bilinear + smoothstep over a random lattice)."""
    gw = w // cell + 2
    gh = h // cell + 2
    grid = [[rnd.random() for _ in range(gw)] for _ in range(gh)]
    xi = [x // cell for x in range(w)]
    xt = []
    for x in range(w):
        t = (x % cell) / cell
        xt.append(t * t * (3 - 2 * t))
    out = []
    for y in range(h):
        gy = y // cell
        t = (y % cell) / cell
        ty = t * t * (3 - 2 * t)
        r0 = grid[gy]
        r1 = grid[gy + 1]
        row = [0.0] * w
        for x in range(w):
            i = xi[x]
            tx = xt[x]
            a = r0[i] + (r0[i + 1] - r0[i]) * tx
            b = r1[i] + (r1[i + 1] - r1[i]) * tx
            row[x] = a + (b - a) * ty
        out.append(row)
    return out


def _fractal_noise(w, h, rnd, cells=(48, 20, 8), weights=(0.6, 0.28, 0.12)):
    layers = [_value_noise(w, h, c, rnd) for c in cells]
    out = []
    for y in range(h):
        rows = [layer[y] for layer in layers]
        out.append([sum(wt * r[x] for wt, r in zip(weights, rows)) for x in range(w)])
    return out


def _voronoi_biomes(w, h, centers):
    """Exact Manhattan-Voronoi biome map in O(w*h) via two sweeps per row.

    Values are encoded as distance*64 + center_index so that min() picks the
    nearest center and, on ties, the lowest index (same result as a brute
    force scan over all centers, which cost ~250M operations on big maps).
    """
    n = len(centers)
    big = 1 << 60
    biome_map = []
    for y in range(h):
        row = [big] * w
        for i, (cx, cy, _b) in enumerate(centers):
            v = abs(cy - y) * 64 + i
            if v < row[cx]:
                row[cx] = v
        for x in range(1, w):
            v = row[x - 1] + 64
            if v < row[x]:
                row[x] = v
        for x in range(w - 2, -1, -1):
            v = row[x + 1] + 64
            if v < row[x]:
                row[x] = v
        biome_map.append([centers[v & 63][2] if v < big else 'plains' for v in row])
    return biome_map


def _reachable_from(game_map, sx, sy):
    """Flood fill over walkable tiles; returns the set of reachable positions."""
    from collections import deque
    mh = len(game_map)
    mw = len(game_map[0]) if mh else 0
    seen = {(sx, sy)}
    q = deque([(sx, sy)])
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < mw and 0 <= ny < mh and (nx, ny) not in seen and game_map[ny][nx] not in BLOCKING:
                seen.add((nx, ny))
                q.append((nx, ny))
    return seen


def ensure_reachable(game, targets):
    """Carve old trails so every target tile can be walked to from the player.

    Walls, rocks and trees on the trail become floor; water becomes a bridge.
    Carving stops as soon as the trail meets the already reachable area.
    """
    try:
        gm = game.game_map
        px, py = int(game.player.x), int(game.player.y)
        reach = _reachable_from(gm, px, py)
        floor = getattr(Display, 'FLOOR', '.')
        carved = 0
        for (tx, ty) in list(targets):
            if (tx, ty) in reach:
                continue
            x, y = tx, ty
            path = []
            steps = 0
            while (x, y) not in reach and steps < 4000:
                steps += 1
                # walk towards the player, alternating axes for a less rigid trail
                if x != px and (y == py or (steps // 3) % 2 == 0):
                    x += 1 if px > x else -1
                elif y != py:
                    y += 1 if py > y else -1
                path.append((x, y))
            for (cx, cy) in path:
                ch = gm[cy][cx]
                if ch == '~':
                    gm[cy][cx] = '='
                    carved += 1
                elif ch in BLOCKING:
                    gm[cy][cx] = floor
                    carved += 1
            # the target's own region plus the trail are now connected
            region = _reachable_from(gm, tx, ty)
            reach |= region
        return carved
    except Exception:
        return 0


def _generate_surface(game):
    """Build the overworld: noise terrain, biome regions and the crash clearing."""
    rnd = random
    size_key = str(getattr(game, 'world_size', 'large') or 'large')
    W, H = WORLD_SIZES.get(size_key, WORLD_SIZES['large'])
    floor = getattr(Display, 'FLOOR', '.')
    wall = getattr(Display, 'WALL', '#')

    noise = _fractal_noise(W, H, rnd)
    wall_level = float(getattr(game, 'mountain_level', 0.34))
    gm = [[floor if noise[y][x] >= wall_level else wall for x in range(W)] for y in range(H)]
    for x in range(W):
        gm[0][x] = gm[1][x] = gm[H - 1][x] = gm[H - 2][x] = wall
    for y in range(H):
        gm[y][0] = gm[y][1] = gm[y][W - 1] = gm[y][W - 2] = wall

    # crash clearing in the middle of the world (same layout as before: clearing + wreckage)
    cm, rooms = generate_crash_site(width=72, height=40)
    ch_, cw_ = len(cm), len(cm[0])
    off_x, off_y = (W - cw_) // 2, (H - ch_) // 2
    rx, ry, rw, rh = rooms[0]
    ecx, ecy = off_x + rx + rw / 2.0, off_y + ry + rh / 2.0
    erx, ery = rw * 0.75, rh * 0.8
    for y in range(max(2, int(ecy - ery) - 1), min(H - 2, int(ecy + ery) + 2)):
        for x in range(max(2, int(ecx - erx) - 1), min(W - 2, int(ecx + erx) + 2)):
            if ((x - ecx) / erx) ** 2 + ((y - ecy) / ery) ** 2 <= 1.0:
                gm[y][x] = floor
    for yy in range(ch_):
        for xx in range(cw_):
            if cm[yy][xx] == getattr(Display, 'WRECKAGE', 'x'):
                gm[off_y + yy][off_x + xx] = cm[yy][xx]
    scaled_rooms = [(r[0] + off_x, r[1] + off_y, r[2], r[3]) for r in rooms]
    game.game_map = gm

    # biome regions
    n_centers = max(8, min(60, (W * H) // 4500))
    centers = [(rnd.randint(2, W - 3), rnd.randint(2, H - 3), BIOME_TYPES[i % len(BIOME_TYPES)] if i < len(BIOME_TYPES) else rnd.choice(BIOME_TYPES))
               for i in range(n_centers)]
    game.map_biomes = _voronoi_biomes(W, H, centers)
    return scaled_rooms

# --- LOGGER INIT AT END OF FILE ---
###############################
# LOGGER INIT (for all functions)
###############################
try:
    from jedi_fugitive.game import logger as game_logger
    log = getattr(game_logger, 'get_logger', lambda name=None: None)("map_features")
except Exception:
    log = None

def get_reachable_tiles(game_map, start_x, start_y):
    """Return a set of (x, y) tuples reachable from start position."""
    mh = len(game_map)
    mw = len(game_map[0]) if mh else 0
    floor_ch = getattr(Display, 'FLOOR', '.')
    
    reachable = set()
    queue = deque([(start_x, start_y)])
    reachable.add((start_x, start_y))
    
    while queue:
        cx, cy = queue.popleft()
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < mw and 0 <= ny < mh:
                if (nx, ny) not in reachable:
                    # Check if walkable (use blacklist approach for better special dungeon support)
                    tile = str(game_map[ny][nx])
                    # Block walls and mountains (allow all floors including special dungeon tiles)
                    non_walkable_tiles = {
                        '\u2588',  # Display.WALL / Shadowmaze walls
                        '#',  # Legacy wall
                        '^',  # Mountains
                        '\u2593',  # Memory Vault crystal walls
                        '\u2666',  # Crystal Garden walls
                        '\u256c',  # Bone Cathedral walls
                        '\u2551',  # Echo Chambers acoustic walls
                        '\u25a4',  # Twisted Library bookshelf walls
                        '\u25a3',  # Pain Forge metal walls
                        '\u224b',  # Dream Nexus fluid walls
                    }
                    if tile not in non_walkable_tiles:
                        reachable.add((nx, ny))
                        queue.append((nx, ny))
    return reachable

def generate_world(game):
    """Generate the overworld, place terrain features, enemies, items, tombs, lore, ship and comms."""
    try:
        from jedi_fugitive.game.sith_codex import get_random_loading_message
        print(get_random_loading_message())
        scaled_rooms = _generate_surface(game)
    except Exception as e:
        print(f"⚠ Warning: World generation encountered an issue: {e}")
        try:
            game.ui.messages.add("World generator failed.")
        except Exception:
            pass
        return

    # Center player on wreckage
    try:
        start = scaled_rooms[0] if scaled_rooms else (0, 0, len(game.game_map[0]), len(game.game_map))
        cx = start[0] + start[2] // 2
        cy = start[1] + start[3] // 2
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
            game.player.x = cx
            game.player.y = cy
    except Exception:
        game.player.x = 1
        game.player.y = 1

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
        wasteland_density = float(getattr(game, 'wasteland_rock_density', 0.15) or 0.15)
        volcanic_density = float(getattr(game, 'volcanic_rock_density', 0.18) or 0.18)
        tundra_density = float(getattr(game, 'tundra_rock_density', 0.10) or 0.10)

        candidates_by_biome = {
            'forest': [], 'plains': [], 'rocky': [], 'desert': [], 'river': [], 
            'mountain_pass': [], 'wasteland': [], 'volcanic': [], 'tundra': []
        }
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
        num_rivers = max(1, len(river_tiles) // 2500)  # 1 river per ~2500 tiles (fewer, longer rivers)
        for _ in range(num_rivers):
            if not river_tiles:
                break
            # Start the river inside a river region so the water actually lands there
            start_x, start_y = random.choice(river_tiles)
            
            # Create winding river path
            path = [(start_x, start_y)]
            current_x, current_y = start_x, start_y
            direction = random.choice(['horizontal', 'vertical', 'diagonal'])
            
            for _ in range(min(160, max(50, max(mw, mh) // 3))):  # River length
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

        # Generate mountain passes with guaranteed corridors
        mountain_tiles = list(candidates_by_biome['mountain_pass'])
        random.shuffle(mountain_tiles)
        mountain_density = 0.25  # Density of mountain tiles
        
        # First, identify mountain ranges (contiguous groups)
        # Create corridors every 10-15 tiles to ensure connectivity
        target_mountains = max(1, int(len(mountain_tiles) * mountain_density))
        corridor_spacing = 12  # Guaranteed pass every 12 tiles
        last_corridor_x = -corridor_spacing
        
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
            
            # Check if we need a guaranteed corridor (every corridor_spacing tiles)
            needs_corridor = abs(tx - last_corridor_x) <= 2
            
            if needs_corridor:
                # Force a pass (leave as floor)
                last_corridor_x = tx
                continue
            else:
                # Use walls (#) for mountains, but create natural passes (gaps)
                if random.random() < 0.65:  # 65% chance of mountain, 35% chance of pass (increased from 20%)
                    game.game_map[ty][tx] = getattr(Display, 'WALL', '#')
                    placed += 1
    except Exception as e:
        if log:
            log.exception("Error in generate_world outer", exc_info=e)

    # Place richer landmarks and POIs across the larger surface map (increased count)
    try:
        if not hasattr(game, 'map_landmarks') or not isinstance(getattr(game, 'map_landmarks', None), dict):
            game.map_landmarks = {}
        mh = len(game.game_map)
        mw = len(game.game_map[0]) if mh else 0
        area = max(1, mw * mh)
        # Increased POI count - now spawns more landmarks across the map
        landmark_count = max(20, min(140, area // 1100))

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
                    if abs(ex - lx) + abs(ey - ly) < 25:  # Increased from 6 to 25 for bigger map
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
                                game.game_map[ny][nx] = 'G'  # Changed from 'L' to 'G' (Guarded cache)
                                loot = {'x': nx, 'y': ny, 'token': 'G', 'name': 'Guarded Supply Cache', 'description': 'A sealed cache; sensors show movement nearby.', 'guarded': True}
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
        area_dec = mw * mh
        floor = getattr(Display, 'FLOOR', '.')
        poi_count = max(10, area_dec // 9000)
        for _p in range(poi_count):
            for _attempt in range(50):  # OPTIMIZED: Reduced from 200 to 50 attempts
                rx = random.randint(2, max(2, mw - 3))
                ry = random.randint(2, max(2, mh - 3))
                if game.game_map[ry][rx] != floor:
                    continue
                if abs(rx - game.player.x) + abs(ry - game.player.y) < 20:  # Increased minimum distance from player
                    continue
                # Check distance from other POIs
                too_close_to_poi = False
                for (ex, ey), _v in game.map_landmarks.items():
                    if abs(ex - rx) + abs(ey - ry) < 15:  # Minimum distance between decorative POIs
                        too_close_to_poi = True
                        break
                if too_close_to_poi:
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

    # Place the Sith Keep early (before enemies) to ensure proper connectivity
    try:
        from jedi_fugitive.game.sith_keep import place_sith_keep_on_map
        place_sith_keep_on_map(game)
    except Exception as e:
        print(f"Warning: Failed to place Sith Keep: {e}")
        # Non-critical - continue without keep
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
        # One patrol group per ~4500 tiles; far-away enemies stay dormant until approached
        spawn_count = max(4, min(60, int((area // 4500) * spawn_factor)))
        # Keep the crash site safe: nothing spawns within this radius of the player
        safe_radius = max(25, min(80, min(mw, mh) // 4))
        max_dist = max(1, (mw + mh) // 2)

        # Crash guards - spread them out across the map
        try:
            crash_guard_count = random.randint(3, 6)  # Increased from 1-2 to 3-6
            floor = getattr(Display, 'FLOOR', '.')
            player_clear_radius = safe_radius

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
                        continue
                    
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
        except Exception as e:
            if log:
                log.exception("Error in generate_world (inner)", exc_info=e)

        # Import planetary enemies for biome-specific spawning
        try:
            from jedi_fugitive.game.planetary_enemies import create_biome_enemy
            planetary_enemies_available = True
        except Exception:
            planetary_enemies_available = False
        
        for _ in range(spawn_count):
            personality = EnemyPersonality()
            # pick the spot first: danger grows with distance from the crash site
            player_clear_radius = safe_radius
            rx = ry = None
            for _attempt in range(200):
                cx_ = random.randint(2, mw - 3)
                cy_ = random.randint(2, mh - 3)
                if (abs(cx_ - game.player.x) + abs(cy_ - game.player.y) > player_clear_radius and
                        game.game_map[cy_][cx_] == floor):
                    rx, ry = cx_, cy_
                    break
            if rx is None:
                continue
            zone = min(3, int(3 * (abs(rx - game.player.x) + abs(ry - game.player.y)) / max_dist))
            player_level = (getattr(getattr(game, 'player', None), 'level', 1) or 1) + zone

            # 60% Sith forces hunting the player, 40% planetary locals (fauna / local threats)
            spawn_biome = 'plains'
            try:
                _b = game.map_biomes[ry][rx] if getattr(game, 'map_biomes', None) else None
                if isinstance(_b, str) and _b:
                    spawn_biome = _b
            except Exception:
                pass
            choice_roll = random.random()
            if choice_roll >= 0.6 and planetary_enemies_available:
                lvl = max(1, player_level + random.randint(-1, 2))
                try:
                    e = create_biome_enemy(spawn_biome, level=lvl)
                except Exception:
                    e = sith.create_sith_trooper(level=lvl)
            else:
                sith_roll = random.random()
                if sith_roll < 0.4:
                    lvl = max(1, min(player_level + random.randint(-1, 1), max(1, player_level + 2)))
                    e = sith.create_sith_trooper(level=lvl)
                elif sith_roll < 0.65:
                    lvl = max(1, min(player_level + random.randint(0, 2), player_level + 3))
                    e = sith.create_sith_acolyte(level=lvl)
                elif sith_roll < 0.85:
                    lvl = max(1, player_level + random.randint(0, 3))
                    e = sith.create_sith_warrior(level=lvl)
                elif sith_roll < 0.95:
                    lvl = max(1, player_level + random.randint(0, 2))
                    e = sith.create_sith_sorcerer(level=lvl)
                else:
                    lvl = max(2, player_level + random.randint(1, 4))
                    e = sith.create_sith_officer(level=lvl)
            e.x, e.y = rx, ry
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

    # Spawn NPCs across different biomes
    try:
        spawn_npcs_on_map(game)
    except Exception as e:
        print(f"Error spawning NPCs: {e}")

    # Spawn merchants first (they take priority for placement)
    try:
        spawn_merchants(game, count_per_biome=2)  # 1-2 per biome
    except Exception as e:
        print(f"Warning: Failed to spawn merchants: {e}")
    
    # Spawn guarded loot caches (1-2 per biome, min 60 tiles apart)
    try:
        spawn_loot_caches(game, count=8)
    except Exception as e:
        print(f"Warning: Failed to spawn loot caches: {e}")
    
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
                if '/' in tokens:
                    weight = int(getattr(game, 'lightsaber_weight', 3) or 3)
                    tokens.extend(['/'] * max(0, weight - 1))
                # quest artifacts only exist at the bottom of tombs
                tokens = [t for t in tokens if t != 'Q']
            except Exception:
                pass
        except Exception:
            tokens = ['v', 'b', 's']
        game.items_on_map = getattr(game, "items_on_map", []) or []
        placed = 0
        max_items = max(12, min(60, (mw * mh) // 2500))
        attempts = 0
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
        try:
            with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                fh.write(f"\n=== WORLD GENERATION: TOMB PLACEMENT ===\n")
                fh.write(f"Initializing tomb_entrances set\n")
        except: pass
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

        # Calculate reachable tiles from player position to ensure tombs are accessible (CACHED)
        print("  Calculating reachable tiles for tomb placement...")
        reachable_tiles = get_reachable_tiles(game.game_map, game.player.x, game.player.y)
        print(f"  Found {len(reachable_tiles)} reachable tiles.")
        # Cache reachable tiles for reuse in other placement functions
        game._cached_reachable_tiles = reachable_tiles

        # Place multiple tombs per biome (excluding mountain_pass - too inaccessible)
        # Changed to place 1-2 tombs per biome for total of 7-12 tombs
        biome_types = ['forest', 'desert', 'rocky', 'plains', 'river']
        placed_tombs = []
        target_tomb_count = random.randint(7, 10)  # Aim for 7-10 tombs total
        
        # Calculate tombs per biome - use ceiling division to ensure we hit target
        available_biome_count = sum(1 for b in biome_types if b in available_biomes)
        if available_biome_count > 0:
            # Use ceiling division: place at least 2 per biome if we have 5 biomes
            tombs_per_biome = max(2, (target_tomb_count + available_biome_count - 1) // available_biome_count)
        else:
            tombs_per_biome = 2

        for biome in biome_types:
            if biome not in available_biomes:
                continue

            # Find all floor tiles in this biome with bounds checking AND reachability check
            biome_floor_tiles = []
            for y in range(mh):
                for x in range(mw):
                    # Bounds check to prevent out-of-range access
                    if (0 <= y < mh and 0 <= x < mw and
                        game.game_map[y][x] == floor and
                        hasattr(game, 'map_biomes') and game.map_biomes and
                        0 <= y < len(game.map_biomes) and 0 <= x < len(game.map_biomes[0]) and
                        game.map_biomes[y][x] == biome):
                        # Only include if reachable
                        if (x, y) in reachable_tiles:
                            biome_floor_tiles.append((x, y))

            if not biome_floor_tiles:
                print(f"  Warning: No reachable floor tiles found for biome {biome}")
                continue

            # Tombs lie out in the wilds, well away from the crash site
            player_clear_radius = int(getattr(game, 'tomb_min_distance', max(30, min(mw, mh) // 5)))
            px, py = game.player.x, game.player.y
            biome_floor_tiles = [(x, y) for x, y in biome_floor_tiles
                               if abs(x - px) + abs(y - py) > player_clear_radius]

            if not biome_floor_tiles:
                continue

            # Place multiple tombs in this biome
            for tomb_num in range(tombs_per_biome):
                if len(placed_tombs) >= target_tomb_count:
                    break
                    
                # Choose a random tile in this biome, preferring ones far from other tombs
                random.shuffle(biome_floor_tiles)
                best_tile = None
                best_min_dist = 0

                for tile_x, tile_y in biome_floor_tiles:
                    # Bounds check
                    if not (0 <= tile_y < mh and 0 <= tile_x < mw):
                        continue
                        
                    min_dist = float('inf')
                    for placed_x, placed_y in placed_tombs:
                        dist = abs(tile_x - placed_x) + abs(tile_y - placed_y)
                        min_dist = min(min_dist, dist)

                    # If no tombs placed yet, or this is farther than current best
                    # Ensure minimum distance of 50 tiles from other tombs for better spacing
                    if (not placed_tombs and min_dist > 50) or min_dist > best_min_dist:
                        best_min_dist = min_dist
                        best_tile = (tile_x, tile_y)

                if best_tile and best_min_dist > 50:  # Ensure tombs are well separated
                    placed_tombs.append(best_tile)
                    game.tomb_entrances.add(best_tile)
                    # Mark on map - bounds check before assignment
                    if 0 <= best_tile[1] < mh and 0 <= best_tile[0] < mw:
                        game.game_map[best_tile[1]][best_tile[0]] = 'D'
                    # Remove this tile from future consideration
                    biome_floor_tiles = [(x, y) for x, y in biome_floor_tiles 
                                        if (x, y) != best_tile]
        
        print(f"  Placed {len(placed_tombs)} tombs.")
        try:
            with open("/tmp/jedi_fugitive_debug.txt", "a") as fh:
                fh.write(f"Placed {len(placed_tombs)} tombs successfully\n")
                fh.write(f"tomb_entrances set now contains {len(game.tomb_entrances)} positions:\n")
                for pos in list(game.tomb_entrances)[:10]:
                    fh.write(f"  - {pos}\n")
                fh.write("=== END TOMB PLACEMENT ===\n\n")
        except: pass

    except Exception as e:
        print(f"Error placing tombs: {e}")
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
        lore_poi_count = random.randint(20, min(60, max(20, area // 3000)))

        # Collect all available lore entries
        all_lore_entries = []
        for category, entries in SITH_LORE.items():
            for entry_id, entry_data in entries.items():
                all_lore_entries.append((category, entry_id, entry_data))

        # Shuffle the lore entries
        random.shuffle(all_lore_entries)

        # Available POI glyphs (avoiding conflicts with existing ones)
        # Expanded glyph set for more POIs - mix of question/exclamation with symbols
        # ('#' and '~' used to be in this list: those POIs were walls/water, unreachable)
        poi_glyphs = ['?', '§', '¶', '†', '‡', '%']
        used_glyphs = set()

        # Get existing landmarks to avoid conflicts
        existing_positions = set(game.map_landmarks.keys()) if game.map_landmarks else set()
        existing_positions.update(game.tomb_entrances)

        # Use cached reachable tiles for POI placement (PERFORMANCE OPTIMIZATION)
        if hasattr(game, '_cached_reachable_tiles') and game._cached_reachable_tiles:
            reachable_tiles = game._cached_reachable_tiles
        else:
            reachable_tiles = get_reachable_tiles(game.game_map, game.player.x, game.player.y)
            game._cached_reachable_tiles = reachable_tiles

        floor_tiles = [(x, y) for y in range(mh) for x in range(mw)
                      if game.game_map[y][x] == floor and (x, y) not in existing_positions and (x, y) in reachable_tiles]

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
            glyph = random.choice(poi_glyphs)

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
        # Place comms terminal near the ship wreck, not near player
        if placed_ship:
            ship_x, ship_y = game.ship_pos
            for _ in range(200):
                try:
                    cx = max(1, min(mw - 2, ship_x + random.randint(-6, 6)))
                    cy = max(1, min(mh - 2, ship_y + random.randint(-6, 6)))
                    if game.game_map[cy][cx] == floor and (cx, cy) != (game.player.x, game.player.y) and (cx, cy) != (ship_x, ship_y):
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

    # Place special dungeons on surface (rare standalone encounters)
    try:
        from jedi_fugitive.game.special_dungeons import get_random_dungeon_type, DUNGEON_TEMPLATES
        
        if not hasattr(game, 'surface_special_dungeons'):
            game.surface_special_dungeons = {}
        
        # Place 1-3 special dungeons on the surface for exploration
        special_dungeon_count = random.randint(1, 3)
        floor = getattr(Display, 'FLOOR', '.')
        
        # Get existing positions to avoid conflicts
        existing_positions = set(getattr(game, 'tomb_entrances', set()))
        if hasattr(game, 'map_landmarks'):
            existing_positions.update(game.map_landmarks.keys())
        
        # Use cached reachable tiles for special dungeon placement (PERFORMANCE OPTIMIZATION)
        if hasattr(game, '_cached_reachable_tiles') and game._cached_reachable_tiles:
            reachable_tiles = game._cached_reachable_tiles
        else:
            reachable_tiles = get_reachable_tiles(game.game_map, game.player.x, game.player.y)
            game._cached_reachable_tiles = reachable_tiles
        
        # Find suitable floor tiles for special dungeons (far from player and other features)
        mh = len(game.game_map)
        mw = len(game.game_map[0]) if mh else 0
        px, py = game.player.x, game.player.y
        
        candidate_tiles = []
        for y in range(mh):
            for x in range(mw):
                if (game.game_map[y][x] == floor and 
                    (x, y) not in existing_positions and
                    (x, y) in reachable_tiles and
                    abs(x - px) + abs(y - py) > 50):  # Far from player start
                    candidate_tiles.append((x, y))
        
        random.shuffle(candidate_tiles)
        
        placed_special = 0
        for x, y in candidate_tiles:
            if placed_special >= special_dungeon_count:
                break
                
            # Ensure minimum distance from other special dungeons
            too_close = False
            for sx, sy in game.surface_special_dungeons.keys():
                if abs(x - sx) + abs(y - sy) < 40:  # Minimum 40 tiles apart
                    too_close = True
                    break
            
            if too_close:
                continue
            
            # Generate special dungeon
            dungeon_type = get_random_dungeon_type()
            template = DUNGEON_TEMPLATES[dungeon_type]
            
            # Place entrance symbol on map
            game.game_map[y][x] = template['symbol']
            
            # Store special dungeon data
            game.surface_special_dungeons[(x, y)] = {
                'type': dungeon_type,
                'template': template,
                'discovered': False,
                'name': template['name']
            }
            
            placed_special += 1
            print(f"  Placed special dungeon: {template['name']} at ({x}, {y})")
        
        print(f"✓ Placed {placed_special} special dungeons on surface")
        
    except Exception as e:
        print(f"✗ Special dungeon placement failed: {e}")
        pass

    # Guarantee that every objective can be reached on foot
    try:
        targets = set(getattr(game, 'tomb_entrances', set()) or set())
        for key in ('ship_pos', 'comms_pos'):
            if getattr(game, key, None):
                targets.add(tuple(getattr(game, key)))
        targets |= set((getattr(game, 'map_landmarks', {}) or {}).keys())
        for it in getattr(game, 'items_on_map', []) or []:
            try:
                targets.add((int(it['x']), int(it['y'])))
            except Exception:
                pass
        ensure_reachable(game, targets)
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
        print("⟳ [map_features.enter_tomb] Starting tomb entry process...")
        # Check if player is on a tomb entrance
        px, py = getattr(game.player, 'x', 0), getattr(game.player, 'y', 0)
        tomb_entrances = getattr(game, 'tomb_entrances', set())
        print(f"  Player position: ({px}, {py})")
        print(f"  Tomb entrances: {len(tomb_entrances)} found")
        
        if (px, py) not in tomb_entrances:
            print(f"✗ Player not on tomb entrance")
            return False

        print("✓ Player is on tomb entrance, saving surface state...")
        # Save surface state
        game.surface_map = game.game_map
        # the fanatic loses your trail at the tomb's threshold (the fear stays: see stress below)
        game.surface_enemies = [e for e in getattr(game, 'enemies', []) if not getattr(e, 'is_hunter', False)]
        game.surface_items_on_map = list(getattr(game, 'items_on_map', []))
        game.surface_player_pos = (px, py)
        game.surface_los_radius = getattr(game.player, 'los_radius', 6)
        # CRITICAL: Save tomb entrances set for re-entry after exiting
        game.surface_tomb_entrances = set(tomb_entrances)

        # Check if this tomb has been entered before (persistence)
        if hasattr(game, 'completed_tombs') and (px, py) in game.completed_tombs:
            print("⟳ Restoring previously explored tomb...")
            tomb_state = game.completed_tombs[(px, py)]
            
            # Restore saved tomb state
            game.tomb_levels = tomb_state.get('levels', [])
            game.tomb_rooms = tomb_state.get('rooms', [])
            game.tomb_enemies = tomb_state.get('enemies', [])
            game.tomb_items = tomb_state.get('items', [])
            game.tomb_stairs = tomb_state.get('stairs', [])
            game.tomb_special_dungeons = tomb_state.get('special_dungeons', [])
            
            # Set initial tomb state
            game.tomb_floor = 0
            game.current_depth = 1
            
            # Place player at entrance
            first_stairs = game.tomb_stairs[0].get('up') if game.tomb_stairs else None
            if first_stairs:
                game.player.x, game.player.y = first_stairs
            else:
                first_room = game.tomb_rooms[0][0] if game.tomb_rooms and game.tomb_rooms[0] else (1, 1, 10, 6)
                game.player.x = first_room[0] + first_room[2] // 2
                game.player.y = first_room[1] + first_room[3] // 2
            
            # Load first level
            game.game_map = game.tomb_levels[0]
            game.enemies = game.tomb_enemies[0]
            game.items_on_map = game.tomb_items[0]
            game.player.los_radius = max(3, getattr(game.player, 'los_radius', 6) - 2)
            
            try:
                if getattr(game, 'ui', None) and getattr(game.ui, 'messages', None):
                    game.ui.messages.add("#3#You return to the familiar tomb...#0#")
                    game.ui.messages.add("(Your previous progress has been preserved)")
            except Exception:
                pass
            
            print("✓ Tomb state restored successfully")
            return True
        
        print("⟳ Generating new dungeon levels...")
        # Generate dungeon levels (3-5 levels)
        num_levels = random.randint(3, 5)
        print(f"  Generating {num_levels} levels...")
        game.tomb_levels = []
        game.tomb_rooms = []
        game.tomb_enemies = []
        game.tomb_items = []
        game.tomb_stairs = []

        for depth in range(1, num_levels + 1):
            print(f"  ⟳ Generating level {depth}/{num_levels}...")
            # Generate level
            # deeper floors are larger catacombs (80x24 at the entrance, up to 120x36)
            level_data = generate_dungeon_level(depth, width=min(120, 72 + depth * 10), height=min(36, 22 + depth * 3))
            level_map, rooms = level_data[0], level_data[1]
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
            enemies_spawned = 0
            for room in rooms:
                num_enemies = random.randint(2, 4)  # Increased from 1-3 to 2-4
                for _ in range(num_enemies):
                    # Find valid spawn position (at least 3 tiles from stairs)
                    spawn_attempts = 0
                    max_attempts = 50
                    valid_position = False
                    ex, ey = 0, 0
                    
                    while spawn_attempts < max_attempts:
                        ex = random.randint(room[0] + 1, room[0] + room[2] - 2)
                        ey = random.randint(room[1] + 1, room[1] + room[3] - 2)
                        
                        # Check if position is valid floor tile
                        if level_map[ey][ex] != Display.FLOOR:
                            spawn_attempts += 1
                            continue
                        
                        # Check distance from all stairs (at least 3 tiles away)
                        valid_position = True
                        min_stair_distance = 3
                        
                        # Check distance from stairs up
                        if 'up' in stairs:
                            stair_x, stair_y = stairs['up']
                            distance = abs(ex - stair_x) + abs(ey - stair_y)
                            if distance < min_stair_distance:
                                valid_position = False
                        
                        # Check distance from stairs down  
                        if 'down' in stairs:
                            stair_x, stair_y = stairs['down']
                            distance = abs(ex - stair_x) + abs(ey - stair_y)
                            if distance < min_stair_distance:
                                valid_position = False
                        
                        if valid_position:
                            break  # Found valid position
                        
                        spawn_attempts += 1
                    
                    # Spawn enemy if valid position found
                    if valid_position and ex > 0 and ey > 0:
                        # Create appropriate enemy for depth
                        try:
                            if depth == 1:
                                enemy = sith.create_sith_trooper(level=max(1, getattr(game.player, 'level', 1)))
                            elif depth == 2:
                                enemy = sith.create_sith_acolyte(level=max(1, getattr(game.player, 'level', 1) + 1))
                            else:
                                # Reduced scaling: depth 3 = player+1, depth 4 = player+2, etc.
                                enemy = sith.create_sith_warrior(level=max(1, getattr(game.player, 'level', 1) + max(0, depth - 2)))
                            enemy.x, enemy.y = ex, ey
                            level_enemies.append(enemy)
                            enemies_spawned += 1
                        except Exception as e:
                            print(f"    ⚠ Failed to create enemy: {e}")
            
            print(f"    ✓ Spawned {enemies_spawned} enemies on level {depth}")
            game.tomb_enemies.append(level_enemies)

            # Generate items for this level
            level_items = []
            # (generate_dungeon_level already scattered this floor's items; a second
            # place_items() call here used to double them)
            
            # Place corrupted Jedi Artifact on the final level
            if depth == num_levels and rooms:
                from jedi_fugitive.items.tokens import TOKEN_MAP
                # Place in the last room (deepest chamber - Sith altar)
                last_room = rooms[-1]
                artifact_x = last_room[0] + last_room[2] // 2
                artifact_y = last_room[1] + last_room[3] // 2
                artifact_placed = False
                
                # Ensure floor tile is clear before placing artifact
                if level_map[artifact_y][artifact_x] == Display.FLOOR:
                    level_map[artifact_y][artifact_x] = 'Q'
                    artifact_placed = True
                    print(f"  ✓ Quest artifact 'Q' placed at ({artifact_x}, {artifact_y}) on final level {depth}")
                else:
                    # Find alternative position in last room
                    for attempt in range(20):
                        alt_x = random.randint(last_room[0] + 1, last_room[0] + last_room[2] - 2)
                        alt_y = random.randint(last_room[1] + 1, last_room[1] + last_room[3] - 2)
                        if level_map[alt_y][alt_x] == Display.FLOOR:
                            level_map[alt_y][alt_x] = 'Q'
                            artifact_x, artifact_y = alt_x, alt_y
                            artifact_placed = True
                            print(f"  ✓ Quest artifact 'Q' placed at alternate position ({artifact_x}, {artifact_y})")
                            break
                
                if artifact_placed:
                    token_info = TOKEN_MAP.get('Q', {'name': 'Jedi Artifact', 'type': 'quest_item'})
                    artifact_entry = {
                        'x': artifact_x, 'y': artifact_y, 'token': 'Q',
                        'name': token_info.get('name', 'Jedi Artifact'),
                        'type': token_info.get('type', 'quest_item'),
                        'description': token_info.get('description', 'Corrupted Jedi relic pulsing with dark energy'),
                        'quest': True
                    }
                    level_items.append(artifact_entry)
                    print(f"  ✓ Artifact added to level_items list at ({artifact_x}, {artifact_y})")
                    print(f"  ✓ Artifact 'Q' token placed on map at ({artifact_x}, {artifact_y})")
                    print(f"  ✓ Map tile at artifact location: '{level_map[artifact_y][artifact_x]}'")
                else:
                    print(f"  ✗ WARNING: Failed to place artifact on final level!")
            
            # Convert map items to item objects (including 'Q' artifact token)
            for y in range(len(level_map)):
                for x in range(len(level_map[0])):
                    tile = level_map[y][x]
                    # Include 'Q' in the list of pickable tokens
                    if tile in [Display.GOLD, Display.FOOD, Display.POTION, Display.ARTIFACT, 'Q']:
                        from jedi_fugitive.items.tokens import TOKEN_MAP
                        token_info = TOKEN_MAP.get(tile, {'name': 'Item', 'type': 'misc'})
                        # Don't double-add artifact if already added above
                        if tile == 'Q' and depth == num_levels:
                            continue  # Already added in artifact placement section
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
        
        # Set tomb visibility (dark underground)
        game.player.los_radius = 4  # Reduced visibility in dark tombs

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
        
        # Recompute visibility for tomb
        try:
            game.compute_visibility()
        except Exception:
            pass

        # Reduce LOS in Sith tomb dungeons
        # Sith tombs: 4 tiles (dark, ancient stone corridors with flickering shadows)
        game.player.los_radius = 4
        
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
                    turn = getattr(game, 'turn_count', 0)
                    game.player.add_log_entry(
                        "[FIRST TOMB] I descended into the darkness, but the terror of being hunted won't leave me. "
                        "The fanatic's pursuit was relentless - I barely escaped with my life. That fear has burrowed "
                        "deep into my mind. I can still hear their footsteps echoing behind me.",
                        turn
                    )
                except Exception:
                    pass
            except Exception:
                pass

        print("✓ [map_features.enter_tomb] Tomb entry successful")
        return True

    except Exception as e:
        print(f"✗ [map_features.enter_tomb] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def spawn_merchants(game, count_per_biome=2):
    """Spawn merchant camps across biomes with faction-based inventories."""
    try:
        from jedi_fugitive.game.merchants import MerchantFaction, FACTION_DATA, get_faction_inventory
        
        if not hasattr(game, 'merchants'):
            game.merchants = {}
        
        mh = len(game.game_map)
        mw = len(game.game_map[0]) if mh else 0
        floor = getattr(Display, 'FLOOR', '.')
        merchant_glyph = getattr(Display, 'MERCHANT', 'X')
        
        # Get player position
        player_x = getattr(game.player, 'x', 0)
        player_y = getattr(game.player, 'y', 0)
        
        factions = [
            MerchantFaction.MANDALORIAN_SCOUTS,
            MerchantFaction.REPUBLIC_SURVIVORS,
            MerchantFaction.SCAVENGER_LOOTERS,
            MerchantFaction.NEUTRAL_TRADERS,
            MerchantFaction.BLACK_MARKET,
            MerchantFaction.JEDI_REFUGEE,
        ]
        
        # Get biomes
        biome_positions = {'forest': [], 'plains': [], 'rocky': [], 'desert': []}
        if hasattr(game, 'map_biomes'):
            for y in range(mh):
                for x in range(mw):
                    try:
                        if game.game_map[y][x] == floor:
                            biome = game.map_biomes[y][x]
                            if biome in biome_positions:
                                biome_positions[biome].append((x, y))
                    except:
                        continue
        
        # If no biomes, use all floor tiles
        if not any(biome_positions.values()):
            for y in range(mh):
                for x in range(mw):
                    if game.game_map[y][x] == floor:
                        biome_positions['plains'].append((x, y))
        
        placed_merchants = []
        
        # Spawn merchants in each biome
        for biome, positions in biome_positions.items():
            if not positions:
                continue
            
            for _ in range(count_per_biome):
                attempts = 0
                max_attempts = 100
                
                while attempts < max_attempts:
                    attempts += 1
                    
                    # Pick random position in biome
                    if not positions:
                        break
                    cx, cy = random.choice(positions)
                    
                    # Check minimum distance from player (60 tiles)
                    if abs(cx - player_x) + abs(cy - player_y) < 60:
                        continue
                    
                    # Check minimum distance from other merchants (60 tiles)
                    too_close = False
                    for (mx, my) in placed_merchants:
                        if abs(cx - mx) + abs(cy - my) < 60:
                            too_close = True
                            break
                    if too_close:
                        continue
                    
                    # Check if we can place a 3x3 square
                    can_place = True
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            nx, ny = cx + dx, cy + dy
                            if nx < 1 or ny < 1 or nx >= mw - 1 or ny >= mh - 1:
                                can_place = False
                                break
                            if game.game_map[ny][nx] != floor:
                                can_place = False
                                break
                        if not can_place:
                            break
                    
                    if not can_place:
                        continue
                    
                    # Place the merchant camp (3x3 square of X's with merchant in center)
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            nx, ny = cx + dx, cy + dy
                            game.game_map[ny][nx] = merchant_glyph
                    
                    # Choose random faction
                    faction = random.choice(factions)
                    faction_data = FACTION_DATA[faction]
                    
                    # Generate inventory
                    player_level = getattr(game.player, 'level', 1)
                    inventory = get_faction_inventory(faction, player_level)
                    
                    # Store merchant data
                    game.merchants[(cx, cy)] = {
                        'faction': faction,
                        'name': faction_data['name'],
                        'camp_name': faction_data['camp_name'],
                        'inventory': inventory,
                        'biome': biome
                    }
                    
                    placed_merchants.append((cx, cy))
                    break
        
        if placed_merchants:
            try:
                if hasattr(game, 'ui') and hasattr(game.ui, 'messages'):
                    game.ui.messages.add(f"📦 {len(placed_merchants)} merchant camps established across the land...")
            except Exception:
                pass
        
        return len(placed_merchants)
        
    except Exception as e:
        print(f"Error spawning merchants: {e}")
        import traceback
        traceback.print_exc()
        return 0


def spawn_loot_caches(game, count=8):
    """Spawn guarded loot caches across the map with weapons, armor, and shields."""
    try:
        if not hasattr(game, 'map_landmarks'):
            game.map_landmarks = {}
        if not hasattr(game, 'loot_caches'):
            game.loot_caches = {}
        
        mh = len(game.game_map)
        mw = len(game.game_map[0]) if mh else 0
        floor = getattr(Display, 'FLOOR', '.')
        cache_glyph = getattr(Display, 'CACHE', 'B')
        
        # Get existing positions to avoid conflicts
        existing_positions = set(game.map_landmarks.keys()) if game.map_landmarks else set()
        # Also avoid merchant positions
        if hasattr(game, 'merchants'):
            for (mx, my) in game.merchants.keys():
                # Add 3x3 area around merchant
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        existing_positions.add((mx + dx, my + dy))
        
        player_x = getattr(game.player, 'x', 0)
        player_y = getattr(game.player, 'y', 0)
        
        # Loot cache names with themes
        cache_names = [
            "Sith Weapons Cache",
            "Sith Armory",
            "Smuggler's Stash",
            "Republic Supply Drop",
            "Mandalorian War Cache",
            "Bounty Hunter Equipment",
            "Black Market Stash",
            "Military Stockpile",
            "Mercenary Arsenal",
            "Hidden Weapons Depot"
        ]
        
        # Get biome positions for distribution
        biome_positions = {'forest': [], 'plains': [], 'rocky': [], 'desert': []}
        if hasattr(game, 'map_biomes'):
            for y in range(mh):
                for x in range(mw):
                    try:
                        if game.game_map[y][x] == floor and (x, y) not in existing_positions:
                            biome = game.map_biomes[y][x]
                            if biome in biome_positions:
                                biome_positions[biome].append((x, y))
                    except:
                        continue
        
        # If no biomes, use all floor tiles
        if not any(biome_positions.values()):
            for y in range(mh):
                for x in range(mw):
                    if game.game_map[y][x] == floor and (x, y) not in existing_positions:
                        biome_positions['plains'].append((x, y))
        
        placed_count = 0
        caches_per_biome = max(1, count // len([b for b in biome_positions.values() if b]))
        
        # Place caches distributed across biomes
        for biome, positions in biome_positions.items():
            if not positions:
                continue
            
            for _ in range(caches_per_biome):
                if placed_count >= count:
                    break
                
                attempts = 0
                max_attempts = 100
                
                while attempts < max_attempts:
                    attempts += 1
                    
                    # Pick random position in biome
                    lx, ly = random.choice(positions)
                    
                    # Check if position is valid
                    if (lx, ly) in existing_positions:
                        continue
                    if abs(lx - player_x) + abs(ly - player_y) < 60:  # Min 60 tiles from player
                        continue
                    
                    # Check distance from other caches (60 tiles minimum)
                    too_close = False
                    for (ex, ey) in existing_positions:
                        if abs(ex - lx) + abs(ey - ly) < 60:
                            too_close = True
                            break
                    if too_close:
                        continue
                    
                    break
                else:
                    continue  # Couldn't find valid position in this biome
            
                # Place the cache
                cache_name = cache_names[placed_count % len(cache_names)]
                game.game_map[ly][lx] = cache_glyph
                
                # Create landmark entry
                landmark = {
                    'glyph': cache_glyph,
                    'name': cache_name,
                    'description': 'A fortified weapons cache guarded by hostiles.',
                    'is_loot_cache': True,
                    'looted': False
                }
                game.map_landmarks[(lx, ly)] = landmark
                existing_positions.add((lx, ly))
            
                # Generate loot for this cache
                from jedi_fugitive.items.weapons import WEAPONS
                from jedi_fugitive.items.armor import ARMORS
                
                loot = []
                player_level = getattr(game.player, 'level', 1)
                
                # 2-4 weapons (mix of melee and ranged)
                weapon_count = random.randint(2, 4)
                for _ in range(weapon_count):
                    weapon = random.choice(WEAPONS)
                    loot.append(weapon)
                
                # 1-3 shields
                shield_count = random.randint(1, 3)
                shields = [w for w in WEAPONS if hasattr(w, 'weapon_type') and 
                          str(w.weapon_type).find('ENERGY_SHIELD') >= 0]
                if shields:
                    for _ in range(shield_count):
                        loot.append(random.choice(shields))
                
                # 1-2 armor pieces
                armor_count = random.randint(1, 2)
                for _ in range(armor_count):
                    armor = random.choice(ARMORS)
                    loot.append(armor)
                
                # Store loot
                game.loot_caches[(lx, ly)] = loot
                
                # Spawn 2-4 guards around the cache
                guard_count = random.randint(2, 4)
                guards_placed = 0
                
                for guard_attempt in range(guard_count * 20):
                    if guards_placed >= guard_count:
                        break
                    
                    # Place guard in a 3x3 to 5x5 area around cache
                    gx = lx + random.randint(-3, 3)
                    gy = ly + random.randint(-3, 3)
                    
                    if gx <= 0 or gy <= 0 or gy >= mh or gx >= mw:
                        continue
                    if game.game_map[gy][gx] != floor:
                        continue
                    if (gx, gy) == (player_x, player_y):
                        continue
                    if (gx, gy) == (lx, ly):
                        continue
                    
                    # Check if position is occupied by another enemy
                    occupied = False
                    for enemy in game.enemies:
                        if getattr(enemy, 'x', -1) == gx and getattr(enemy, 'y', -1) == gy:
                            occupied = True
                            break
                    if occupied:
                        continue
                    
                    # Create guard enemy (scaled to player level)
                    guard_level = max(1, player_level + random.randint(-1, 2))
                    guard = sith.create_sith_warrior(level=guard_level, x=gx, y=gy)
                    guard.name = f"Cache Guard (Lvl {guard_level})"
                    
                    # Assign patrol around the cache
                    patrol = []
                    for _ in range(4):
                        px_patrol = lx + random.randint(-4, 4)
                        py_patrol = ly + random.randint(-4, 4)
                        if (0 <= py_patrol < mh and 0 <= px_patrol < mw and 
                            game.game_map[py_patrol][px_patrol] == floor):
                            patrol.append((px_patrol, py_patrol))
                    
                    if patrol:
                        guard.patrol_points = patrol
                        guard._patrol_index = 0
                    
                    game.enemies.append(guard)
                    guards_placed += 1
                
                placed_count += 1
        
        if placed_count > 0:
            try:
                if hasattr(game, 'ui') and hasattr(game.ui, 'messages'):
                    game.ui.messages.add(f"#3#[CACHE]#0# {placed_count} loot caches scattered across the world...")
            except Exception:
                pass
        
        return placed_count
        
    except Exception as e:
        if log:
            log.exception(f"Error spawning loot caches: {e}", exc_info=e)
        return 0


def spawn_npcs_on_map(game):
    """Spawn NPCs across different biomes with appropriate types"""
    try:
        from jedi_fugitive.game.npc_encounters import NPC_TYPES, NPC
        
        if not hasattr(game, 'npcs_on_map'):
            game.npcs_on_map = {}
            
        mh = len(game.game_map)
        mw = len(game.game_map[0]) if mh else 0
        floor = getattr(Display, 'FLOOR', '.')
        
        # Get player position for minimum distance
        player_x = getattr(game.player, 'x', 0)
        player_y = getattr(game.player, 'y', 0)
        
        # Get biome positions if available
        biome_positions = {'forest': [], 'plains': [], 'rocky': [], 'desert': [], 'river': [], 'mountain_pass': []}
        if hasattr(game, 'map_biomes'):
            for y in range(mh):
                for x in range(mw):
                    try:
                        if game.game_map[y][x] == floor:
                            biome = game.map_biomes[y][x]
                            if biome in biome_positions:
                                biome_positions[biome].append((x, y))
                    except:
                        continue
        
        # If no biomes available, use all floor tiles as plains
        if not any(biome_positions.values()):
            for y in range(mh):
                for x in range(mw):
                    if game.game_map[y][x] == floor:
                        biome_positions['plains'].append((x, y))
        
        npcs_spawned = 0
        
        # Try to spawn each NPC type
        for npc_type, npc_data in NPC_TYPES.items():
            spawn_chance = npc_data['spawn_chance']
            suitable_biomes = npc_data['biomes']
            
            # Check if we should spawn this NPC type
            if random.random() > spawn_chance:
                continue
                
            # Find suitable biomes that have positions
            available_positions = []
            for biome in suitable_biomes:
                if biome in biome_positions:
                    available_positions.extend(biome_positions[biome])
            
            if not available_positions:
                continue
                
            # Try to find a good spawn position
            attempts = 0
            max_attempts = 50
            
            while attempts < max_attempts:
                attempts += 1
                
                # Pick random position from suitable biomes
                pos_x, pos_y = random.choice(available_positions)
                
                # Check minimum distance from player (80 tiles)
                if abs(pos_x - player_x) + abs(pos_y - player_y) < 80:
                    continue
                
                # Check minimum distance from other NPCs (40 tiles)
                too_close_to_npc = False
                for (npc_x, npc_y) in game.npcs_on_map.keys():
                    if abs(pos_x - npc_x) + abs(pos_y - npc_y) < 40:
                        too_close_to_npc = True
                        break
                
                if too_close_to_npc:
                    continue
                
                # Check if position is still valid
                if 0 <= pos_y < mh and 0 <= pos_x < mw and game.game_map[pos_y][pos_x] == floor:
                    # Create NPC instance
                    npc = NPC(npc_type, pos_x, pos_y)
                    game.npcs_on_map[(pos_x, pos_y)] = npc
                    npcs_spawned += 1
                    print(f"  Spawned {npc_data['name']} at ({pos_x}, {pos_y})")
                    break
        
        if npcs_spawned > 0:
            try:
                if hasattr(game, 'ui') and hasattr(game.ui, 'messages'):
                    game.ui.messages.add(f"📡 {npcs_spawned} survivors and travelers found across the world...")
            except Exception:
                pass
                
        return npcs_spawned
        
    except Exception as e:
        if log:
            log.exception(f"Error spawning NPCs: {e}", exc_info=e)
        return 0
