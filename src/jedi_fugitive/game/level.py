from typing import List, Tuple
from jedi_fugitive.game.enemy import Enemy, EnemyType
import random

class Display:
    WALL = '#'; FLOOR = '.'; STAIRS_DOWN = '>'; STAIRS_UP = '<'
    GOLD = '$'; FOOD = ':'; POTION = '!'; ARTIFACT = '&'; WRECKAGE = 'x'
    # narrative glyphs
    SHIP = 'S'
    COMMS = 'C'
    SITH_ENTRANCE = 'D'  # Tomb/dungeon entrance
    # additional landmarks / POI glyphs
    MONOLITH = 'M'
    OUTPOST = 'O'
    ANTENNA = 'A'
    CRATER = 'o'
    DRONE = 'd'
    WATCHTOWER = 'W'
    DUNE = '~'
    ROCK = 'r'
    TREE = 'T'  # Trees for forest biome
    # New POI types for lore and exploration
    STATUE = 'Y'  # Sith statue
    SHRINE = 'H'  # Dark shrine
    OBELISK = 'I'  # Ancient obelisk
    ARCHIVE = 'V'  # Ruined archive
    FORGE = 'F'  # Ancient forge
    ALTAR = 'U'  # Sacrificial altar
    PILLAR = 'P'  # Collapsed pillar
    SARCOPHAGUS = 'Q'  # Exposed sarcophagus
    GATEWAY = 'G'  # Inactive gateway
    NEXUS = 'N'  # Force nexus
    CACHE = 'L'  # Hidden cache
    BEACON = 'B'  # Old beacon
    RUINS = 'R'  # Scattered ruins

def place_items(game_map: List[List[str]], rooms: List[Tuple[int,int,int,int]], depth: int):
    # Reduced food spawning - dungeons are more dangerous now
    # Added crafting materials for weapon upgrades
    item_chances = {Display.GOLD:0.35, Display.FOOD:0.08, Display.POTION:0.12}
    
    # Crafting materials (common to rare based on depth)
    material_tokens = ['m', 'M', 'w', 'P']  # Common materials
    if depth >= 2:
        material_tokens.extend(['p', 'l', 'C'])  # Uncommon materials
    if depth >= 4:
        item_chances[Display.ARTIFACT] = 0.05
        material_tokens.extend(['o'])  # Rare materials
    if depth >= 6:
        material_tokens.extend(['K'])  # Legendary materials
    
    for room in rooms:
        # Fewer items per room (1-2 instead of 1-3)
        for _ in range(random.randint(1,2)):
            x = random.randint(room[0]+1, room[0]+room[2]-2)
            y = random.randint(room[1]+1, room[1]+room[3]-2)
            if game_map[y][x] == Display.FLOOR:
                # 30% chance to spawn material instead of regular item
                if random.random() < 0.3 and material_tokens:
                    game_map[y][x] = random.choice(material_tokens)
                else:
                    game_map[y][x] = random.choices(list(item_chances.keys()), weights=list(item_chances.values()))[0]

def generate_dungeon_level(depth: int, width: int = 80, height: int = 24):
    game_map = [[Display.WALL for _ in range(width)] for _ in range(height)]
    rooms = []
    for _ in range(random.randint(5,8)):
        rw = random.randint(6,12); rh = random.randint(4,8)
        rx = random.randint(1, width - rw - 1); ry = random.randint(1, height - rh - 1)
        overlap = False
        for ox,oy,ow,oh in rooms:
            if (rx < ox + ow + 1 and rx + rw + 1 > ox and ry < oy + oh + 1 and ry + rh + 1 > oy):
                overlap = True; break
        if not overlap:
            for y in range(ry, ry + rh):
                for x in range(rx, rx + rw):
                    game_map[y][x] = Display.FLOOR
            rooms.append((rx,ry,rw,rh))
    # connect
    for i in range(len(rooms)-1):
        r1 = rooms[i]; r2 = rooms[i+1]
        x1 = r1[0] + r1[2]//2; y1 = r1[1] + r1[3]//2
        x2 = r2[0] + r2[2]//2; y2 = r2[1] + r2[3]//2
        for x in range(min(x1,x2), max(x1,x2)+1): game_map[y1][x] = Display.FLOOR
        for y in range(min(y1,y2), max(y1,y2)+1): game_map[y][x2] = Display.FLOOR
    if rooms:
        # Always place stairs up in first room (for returning from deeper levels)
        ux,uy = rooms[0][0]+1, rooms[0][1]+1
        game_map[uy][ux] = Display.STAIRS_UP
        # Always place stairs down in last room (for descending deeper)
        dx,dy = rooms[-1][0]+rooms[-1][2]-2, rooms[-1][1]+rooms[-1][3]-2
        game_map[dy][dx] = Display.STAIRS_DOWN
    place_items(game_map, rooms, depth)
    return game_map, rooms

def generate_crash_site(width: int = 80, height: int = 40):
    """Generate a roomy crash site surface map.

    The map contains a single large cleared room (the crash clearing) and
    a few wreckage tiles. Tomb entrance markers (1/2/3) are placed at
    randomized positions near the room edge so their locations vary each run.
    """
    game_map = [[Display.WALL for _ in range(width)] for _ in range(height)]
    rooms = []
    # central clearing: occupy roughly the central half of the map
    rx, ry = width // 4, height // 4
    rw, rh = max(8, width // 2), max(6, height // 2)
    for y in range(ry, min(ry + rh, height)):
        for x in range(rx, min(rx + rw, width)):
            game_map[y][x] = Display.FLOOR
    rooms.append((rx, ry, rw, rh))

    # small wreckage patch roughly in the center-left of the clearing
    wx, wy = rx + max(1, rw // 3) - 2, ry + max(1, rh // 2) - 1
    for y in range(wy, min(wy + 3, height)):
        for x in range(wx, min(wx + 5, width)):
            if 0 <= x < width and 0 <= y < height:
                game_map[y][x] = Display.WRECKAGE

    # Note: Tomb entrances are now placed by map_features.py using biome-based distribution
    # No numeric markers (1/2/3) are placed here - all tombs use 'D' glyph

    return game_map, rooms