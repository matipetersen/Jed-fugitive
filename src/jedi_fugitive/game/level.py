from typing import List, Tuple
from jedi_fugitive.game.enemy import Enemy, EnemyType
import random

class Display:
    # Modern Roguelike Symbols (Unicode)
    WALL = '█'
    FLOOR = '·'
    STAIRS_DOWN = '▼'
    STAIRS_UP = '▲'
    GOLD = '⛃'
    FOOD = '🍖'
    POTION = '🧪'
    ARTIFACT = '🔮'
    WRECKAGE = '✖'
    
    # Narrative & POI
    SHIP = '🚀'
    COMMS = '📡'
    SITH_ENTRANCE = 'D'  # Tomb entrance (Door)
    
    # Landmarks - using ASCII to avoid display issues
    MONOLITH = 'M'  # Monolith
    OUTPOST = 'O'  # Outpost
    ANTENNA = 'A'  # Antenna
    CRATER = 'C'  # Crater
    DRONE = 'd'  # Drone
    WATCHTOWER = 'W'  # Watchtower
    DUNE = '~'  # Dune
    ROCK = 'r'  # Rock
    TREE = 't'  # Tree
    
    # New POI types
    STATUE = 'S'  # Statue
    SHRINE = 'H'  # Shrine
    OBELISK = '⚰'
    ARCHIVE = '📚'
    FORGE = '⚒'
    ALTAR = '♜'
    PILLAR = '║'
    SARCOPHAGUS = '⚰'
    GATEWAY = '⛩'
    NEXUS = '🌀'
    CACHE = '📦'
    BEACON = '🔆'
    RUINS = '🏚'
    MERCHANT = '⛺'

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
    """Generate dungeon level - now uses the updated generation.py function."""
    from jedi_fugitive.map.generation import generate_dungeon_level as gen_level
    return gen_level(depth, width, height)

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