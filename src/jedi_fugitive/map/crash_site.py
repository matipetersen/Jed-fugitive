from typing import List, Tuple
from .generation import Display
import random

def generate_crash_site(width: int = 60, height: int = 30) -> Tuple[List[List[str]], List[Tuple[int,int,int,int]]]:
    game_map = [[Display.WALL for _ in range(width)] for _ in range(height)]
    rooms = []
    rx, ry = width//4, height//4
    rw, rh = width//2, height//2
    for y in range(ry, ry+rh):
        for x in range(rx, rx+rw):
            game_map[y][x] = Display.FLOOR
    rooms.append((rx, ry, rw, rh))
    # wreckage
    wx, wy = rx + rw//2 - 2, ry + rh//2 - 1
    for y in range(wy, wy+3):
        for x in range(wx, wx+5):
            if 0 <= x < width and 0 <= y < height:
                game_map[y][x] = Display.WRECKAGE
    # tomb markers
    game_map[ry+2][rx+rw-1] = '1'
    game_map[ry+rh//2][rx+rw-1] = '2'
    game_map[ry+rh-3][rx+rw-1] = '3'
    return game_map, rooms