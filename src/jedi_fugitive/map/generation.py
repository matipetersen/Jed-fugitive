from typing import List, Tuple
import random
from jedi_fugitive.game.special_dungeons import get_random_dungeon_type, DUNGEON_TEMPLATES

class Display:
    WALL = '#'; FLOOR = '.'; STAIRS_DOWN = '>'; STAIRS_UP = '<'
    GOLD = '$'; FOOD = ':'; POTION = '!'; ARTIFACT = '&'; WRECKAGE = 'x'
    # Special dungeon entrance symbols
    SPECIAL_ENTRANCE = '◎'

def place_items(game_map: List[List[str]], rooms: List[Tuple[int,int,int,int]], depth: int):
    item_chances = {Display.GOLD:0.3, Display.FOOD:0.2, Display.POTION:0.1}
    if depth >= 4:
        item_chances[Display.ARTIFACT] = 0.05
    for room in rooms:
        for _ in range(random.randint(1,3)):
            x = random.randint(room[0]+1, room[0]+room[2]-2)
            y = random.randint(room[1]+1, room[1]+room[3]-2)
            if game_map[y][x] == Display.FLOOR:
                game_map[y][x] = random.choices(list(item_chances.keys()), weights=list(item_chances.values()))[0]


def place_special_dungeons(game_map: List[List[str]], rooms: List[Tuple[int,int,int,int]], depth: int):
    """Place special dungeon entrances on deeper levels."""
    if depth < 3:  # Only spawn on deeper levels
        return {}
    
    # Chance increases with depth
    spawn_chance = min(0.15 + (depth - 3) * 0.1, 0.4)
    
    special_dungeons = {}
    
    if random.random() < spawn_chance and rooms:
        # Choose a random room to place the entrance
        room = random.choice(rooms)
        
        # Find a suitable position in the room
        attempts = 0
        while attempts < 10:
            x = random.randint(room[0] + 1, room[0] + room[2] - 2)
            y = random.randint(room[1] + 1, room[1] + room[3] - 2)
            
            if game_map[y][x] == Display.FLOOR:
                # Place special dungeon entrance
                dungeon_type = get_random_dungeon_type()
                template = DUNGEON_TEMPLATES[dungeon_type]
                
                game_map[y][x] = template['symbol']
                
                special_dungeons[(x, y)] = {
                    'type': dungeon_type,
                    'template': template,
                    'discovered': False
                }
                break
            
            attempts += 1
    
    return special_dungeons

def generate_dungeon_level(depth: int, width: int = 80, height: int = 24):
    game_map = [[Display.WALL for _ in range(width)] for _ in range(height)]
    rooms = []
    for _ in range(random.randint(5,8)):
        rw = random.randint(6,12); rh = random.randint(4,8)
        rx = random.randint(1, width - rw - 1); ry = random.randint(1, height - rh - 1)
        overlap = False
        for ox,oy,ow,oh in rooms:
            if (rx < ox + ow + 1 and rx + rw + 1 > ox and ry < oy + oh + 1 and ry + rh + 1 > oy):
                overlap = True
                break
        if not overlap:
            for y in range(ry, ry + rh):
                for x in range(rx, rx + rw):
                    game_map[y][x] = Display.FLOOR
            rooms.append((rx,ry,rw,rh))
    # connect rooms with corridors
    for i in range(len(rooms)-1):
        r1 = rooms[i]; r2 = rooms[i+1]
        x1 = r1[0] + r1[2]//2; y1 = r1[1] + r1[3]//2
        x2 = r2[0] + r2[2]//2; y2 = r2[1] + r2[3]//2
        for x in range(min(x1,x2), max(x1,x2)+1): game_map[y1][x] = Display.FLOOR
        for y in range(min(y1,y2), max(y1,y2)+1): game_map[y][x2] = Display.FLOOR
    if rooms:
        # Place stairs up in first room (for returning to previous level)
        # All levels get stairs up so player can always ascend
        ux,uy = rooms[0][0]+1, rooms[0][1]+1
        game_map[uy][ux] = Display.STAIRS_UP
        
        # Place stairs down in last room (for descending to next level)
        # This should be placed on all levels - the game logic will handle
        # whether there's actually a deeper level to go to
        dx,dy = rooms[-1][0]+rooms[-1][2]-2, rooms[-1][1]+rooms[-1][3]-2
        game_map[dy][dx] = Display.STAIRS_DOWN
    place_items(game_map, rooms, depth)
    
    # Place special dungeons and return their data
    special_dungeons = place_special_dungeons(game_map, rooms, depth)
    
    return game_map, rooms, special_dungeons