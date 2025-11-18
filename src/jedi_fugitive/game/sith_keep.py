"""
Sith Keep - A challenging labyrinth with puzzles, guards, and a final boss.
Located on the main map, requires Force Push/Pull to navigate.
"""
import random
from jedi_fugitive.game.level import Display


def generate_sith_keep_layout(keep_size=15):
    """
    Generate a Sith Keep labyrinth with chambers and corridors.
    Returns (map, entrance, chambers, puzzle_positions, boss_chamber)
    """
    width = keep_size * 2 + 1
    height = keep_size * 2 + 1
    
    # Initialize with walls
    layout = [[Display.WALL for _ in range(width)] for _ in range(height)]
    
    # Create central hub
    hub_x, hub_y = width // 2, height // 2
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            layout[hub_y + dy][hub_x + dx] = Display.FLOOR
    
    # Define chamber positions (north, east, south, west wings)
    chambers = []
    
    # North wing - Puzzle chambers
    north_chamber = _create_chamber(layout, hub_x, hub_y - 8, 5, 5)
    chambers.append(('puzzle_north', north_chamber))
    _create_corridor(layout, hub_x, hub_y - 2, hub_x, hub_y - 8)
    
    # East wing - Guard chambers
    east_chamber = _create_chamber(layout, hub_x + 8, hub_y, 5, 5)
    chambers.append(('guards_east', east_chamber))
    _create_corridor(layout, hub_x + 2, hub_y, hub_x + 8, hub_y)
    
    # South wing - Puzzle chambers
    south_chamber = _create_chamber(layout, hub_x, hub_y + 8, 5, 5)
    chambers.append(('puzzle_south', south_chamber))
    _create_corridor(layout, hub_x, hub_y + 2, hub_x, hub_y + 8)
    
    # West wing - Guard chambers
    west_chamber = _create_chamber(layout, hub_x - 8, hub_y, 5, 5)
    chambers.append(('guards_west', west_chamber))
    _create_corridor(layout, hub_x - 2, hub_y, hub_x - 8, hub_y)
    
    # Boss chamber - North of north wing
    boss_chamber = _create_chamber(layout, hub_x, hub_y - 16, 7, 7)
    _create_corridor(layout, hub_x, hub_y - 13, hub_x, hub_y - 16)
    
    # Entrance at south
    entrance_x, entrance_y = hub_x, height - 2
    layout[entrance_y][entrance_x] = Display.FLOOR
    _create_corridor(layout, hub_x, hub_y + 13, hub_x, entrance_y)
    
    return layout, (entrance_x, entrance_y), chambers, boss_chamber


def _create_chamber(layout, cx, cy, width, height):
    """Create a rectangular chamber centered at cx, cy."""
    x1 = cx - width // 2
    y1 = cy - height // 2
    x2 = x1 + width
    y2 = y1 + height
    
    for y in range(y1, y2):
        for x in range(x1, x2):
            if 0 <= y < len(layout) and 0 <= x < len(layout[0]):
                layout[y][x] = Display.FLOOR
    
    return (cx, cy, width, height)


def _create_corridor(layout, x1, y1, x2, y2):
    """Create a straight corridor between two points."""
    if x1 == x2:  # Vertical corridor
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= y < len(layout):
                layout[y][x1] = Display.FLOOR
    else:  # Horizontal corridor
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < len(layout[0]):
                layout[y1][x] = Display.FLOOR


def setup_sith_keep_puzzles(game, keep_center_x, keep_center_y, chambers):
    """
    Setup Force Push/Pull puzzles in the keep.
    Puzzle: Move boulders to pressure plates to open doors.
    """
    if not hasattr(game, 'sith_keep_puzzles'):
        game.sith_keep_puzzles = {}
    
    puzzle_chambers = [c for c in chambers if 'puzzle' in c[0]]
    
    for chamber_name, (cx, cy, width, height) in puzzle_chambers:
        # Calculate world coordinates
        world_cx = keep_center_x + cx - 15  # Offset from keep origin
        world_cy = keep_center_y + cy - 15
        
        # Place boulders (rocks that can be pushed)
        boulder_positions = []
        for i in range(2):
            bx = world_cx + random.randint(-2, 2)
            by = world_cy + random.randint(-2, 2)
            
            # Check if position is valid
            if (0 <= by < len(game.game_map) and 0 <= bx < len(game.game_map[0]) and
                game.game_map[by][bx] == Display.FLOOR):
                game.game_map[by][bx] = 'O'  # Boulder symbol
                boulder_positions.append((bx, by))
        
        # Place pressure plates
        plate_positions = []
        for i in range(2):
            px = world_cx + random.randint(-1, 1)
            py = world_cy + random.randint(-1, 1)
            
            if (0 <= py < len(game.game_map) and 0 <= bx < len(game.game_map[0]) and
                game.game_map[py][px] == Display.FLOOR and
                (px, py) not in boulder_positions):
                # Mark pressure plate (will be invisible until player discovers)
                plate_positions.append((px, py))
        
        # Store puzzle state
        puzzle_id = f"keep_puzzle_{chamber_name}"
        game.sith_keep_puzzles[puzzle_id] = {
            'boulders': boulder_positions,
            'plates': plate_positions,
            'solved': False,
            'door_position': (world_cx, world_cy - 3)  # Door to boss chamber
        }


def setup_sith_keep_guards(game, keep_center_x, keep_center_y, chambers):
    """Spawn elite guards in the guard chambers."""
    from jedi_fugitive.game import enemies_sith as sith
    
    guard_chambers = [c for c in chambers if 'guards' in c[0]]
    player_level = getattr(game.player, 'level', 1)
    
    for chamber_name, (cx, cy, width, height) in guard_chambers:
        # Calculate world coordinates
        world_cx = keep_center_x + cx - 15
        world_cy = keep_center_y + cy - 15
        
        # Spawn 2-3 elite guards per chamber
        num_guards = random.randint(2, 3)
        for i in range(num_guards):
            gx = world_cx + random.randint(-2, 2)
            gy = world_cy + random.randint(-2, 2)
            
            if (0 <= gy < len(game.game_map) and 0 <= gx < len(game.game_map[0]) and
                game.game_map[gy][gx] == Display.FLOOR):
                
                # Create elite guard (higher level than player)
                guard_level = player_level + random.randint(2, 4)
                guard = sith.create_sith_warrior(level=guard_level, x=gx, y=gy)
                guard.name = f"Sith Keep Guard (Lvl {guard_level})"
                guard.hp = int(guard.hp * 1.5)  # Tougher
                guard.max_hp = guard.hp
                
                # Patrol within chamber
                patrol = []
                for _ in range(3):
                    patrol.append((
                        world_cx + random.randint(-2, 2),
                        world_cy + random.randint(-2, 2)
                    ))
                guard.patrol_points = patrol
                guard._patrol_index = 0
                
                game.enemies.append(guard)


def setup_sith_keep_boss(game, keep_center_x, keep_center_y, boss_chamber):
    """
    Spawn a random canon Sith Lord boss in the final chamber.
    This boss is significantly stronger than any other enemy.
    """
    from jedi_fugitive.game import enemies_sith as sith
    from jedi_fugitive.items.weapons import WEAPONS
    
    cx, cy, width, height = boss_chamber
    world_cx = keep_center_x + cx - 15
    world_cy = keep_center_y + cy - 15
    
    # Place legendary weapon on pedestal (end of chamber)
    weapon_x = world_cx
    weapon_y = world_cy - 3
    
    # Find rarest weapon
    legendary_weapons = [w for w in WEAPONS if getattr(w, 'rarity', '').lower() == 'legendary']
    if legendary_weapons:
        # Place the most powerful legendary weapon
        best_weapon = max(legendary_weapons, key=lambda w: getattr(w, 'base_damage', 0))
    else:
        # Fallback to highest damage weapon
        best_weapon = max(WEAPONS, key=lambda w: getattr(w, 'base_damage', 0))
    
    # Add to items on map
    game.items_on_map.append({
        'x': weapon_x,
        'y': weapon_y,
        'item': best_weapon
    })
    
    # Mark on map
    if (0 <= weapon_y < len(game.game_map) and 0 <= weapon_x < len(game.game_map[0])):
        game.game_map[weapon_y][weapon_x] = '†'  # Legendary weapon marker
    
    # Create Sith Lord boss (randomly named from canon Sith Lords)
    player_level = getattr(game.player, 'level', 1)
    boss_level = max(10, player_level + 5)
    
    boss = sith.create_sith_inquisitor(level=boss_level, x=world_cx, y=world_cy)
    # Name is already set randomly in create_sith_inquisitor, just add level
    boss.name = f"{boss.name} (Lvl {boss_level})"
    boss.hp = int(boss.hp * 2.5)  # Boss HP
    boss.max_hp = boss.hp
    boss.attack = int(boss.attack * 1.5)  # Boss damage
    
    # Store as boss for special handling
    if not hasattr(game, 'sith_keep_boss'):
        game.sith_keep_boss = boss
    
    game.enemies.append(boss)
    
    # Add dramatic message when player gets close
    if not hasattr(game, 'sith_keep_discovered'):
        game.sith_keep_discovered = False


def place_sith_keep_on_map(game):
    """
    Place the Sith Keep entrance on the main map.
    The keep is a separate area accessed through a portal.
    """
    mh = len(game.game_map)
    mw = len(game.game_map[0]) if mh else 0
    floor = getattr(Display, 'FLOOR', '.')
    
    # Find suitable location (far from player spawn, avoid merchants/caches)
    player_x = getattr(game.player, 'x', 0)
    player_y = getattr(game.player, 'y', 0)
    
    # Get merchant and cache positions to avoid
    merchant_positions = []
    if hasattr(game, 'merchant_positions'):
        merchant_positions = game.merchant_positions
    
    cache_positions = []
    if hasattr(game, 'loot_cache_positions'):
        cache_positions = game.loot_cache_positions
    
    best_distance = 0
    best_position = None
    min_distance = max(150, min(mw, mh) // 3)  # Minimum 150 tiles or 1/3 map size
    
    # Try to find position far from everything
    for attempt in range(1000):
        # Randomize quadrant first to ensure distribution
        quadrant = attempt % 4
        if quadrant == 0:  # Top-left
            x = random.randint(20, mw // 2 - 20)
            y = random.randint(20, mh // 2 - 20)
        elif quadrant == 1:  # Top-right
            x = random.randint(mw // 2 + 20, mw - 20)
            y = random.randint(20, mh // 2 - 20)
        elif quadrant == 2:  # Bottom-left
            x = random.randint(20, mw // 2 - 20)
            y = random.randint(mh // 2 + 20, mh - 20)
        else:  # Bottom-right
            x = random.randint(mw // 2 + 20, mw - 20)
            y = random.randint(mh // 2 + 20, mh - 20)
        
        distance = abs(x - player_x) + abs(y - player_y)
        
        # Must be far from spawn
        if distance < min_distance:
            continue
        
        # Check if floor
        if game.game_map[y][x] != floor:
            continue
        
        # Check distance from merchants and caches (avoid overlap)
        too_close = False
        for mx, my in merchant_positions:
            if abs(x - mx) + abs(y - my) < 80:
                too_close = True
                break
        if too_close:
            continue
        
        for cx, cy in cache_positions:
            if abs(x - cx) + abs(y - cy) < 80:
                too_close = True
                break
        if too_close:
            continue
        
        # Check if we can place the keep structure (32x32 area)
        can_place = True
        for dy in range(-16, 17):
            for dx in range(-16, 17):
                ny, nx = y + dy, x + dx
                if (ny < 0 or nx < 0 or ny >= mh or nx >= mw or
                    game.game_map[ny][nx] != floor):
                    can_place = False
                    break
            if not can_place:
                break
        
        if can_place and distance > best_distance:
            best_position = (x, y)
            best_distance = distance
            
            # If we found a really good spot (very far), take it
            if best_distance > min_distance * 1.5:
                break
    
    if not best_position:
        # Fallback: place in corner farthest from player
        corners = [
            (50, 50),
            (mw - 50, 50),
            (50, mh - 50),
            (mw - 50, mh - 50)
        ]
        best_position = max(corners, key=lambda p: abs(p[0] - player_x) + abs(p[1] - player_y))
    
    keep_x, keep_y = best_position
    
    # Generate the keep structure directly on the map
    layout, entrance, chambers, boss_chamber = generate_sith_keep_layout(keep_size=15)
    
    # Place keep walls on map
    keep_height = len(layout)
    keep_width = len(layout[0]) if keep_height > 0 else 0
    
    offset_x = keep_x - keep_width // 2
    offset_y = keep_y - keep_height // 2
    
    # Draw the keep structure
    for y in range(keep_height):
        for x in range(keep_width):
            map_y = offset_y + y
            map_x = offset_x + x
            
            if 0 <= map_y < mh and 0 <= map_x < mw:
                if layout[y][x] == Display.WALL:
                    game.game_map[map_y][map_x] = '█'  # Keep wall (solid block)
                elif layout[y][x] == Display.FLOOR:
                    game.game_map[map_y][map_x] = Display.FLOOR
    
    # Mark entrance with special symbol
    entrance_world_x = offset_x + entrance[0]
    entrance_world_y = offset_y + entrance[1]
    game.game_map[entrance_world_y][entrance_world_x] = '▓'  # Keep entrance
    
    # Setup puzzles, guards, and boss
    setup_sith_keep_puzzles(game, offset_x, offset_y, chambers)
    setup_sith_keep_guards(game, offset_x, offset_y, chambers)
    setup_sith_keep_boss(game, offset_x, offset_y, boss_chamber)
    
    # Store keep data
    game.sith_keep_entrance = (entrance_world_x, entrance_world_y)
    game.sith_keep_center = (keep_x, keep_y)
    game.sith_keep_bounds = (offset_x, offset_y, keep_width, keep_height)
    
    # Add landmark
    if hasattr(game, 'map_landmarks'):
        game.map_landmarks[(entrance_world_x, entrance_world_y)] = {
            'glyph': '▓',
            'name': 'Ancient Sith Keep',
            'description': 'A foreboding fortress radiating dark side energy. The entrance beckons.',
            'is_sith_keep': True
        }
    
    try:
        if hasattr(game, 'ui') and hasattr(game.ui, 'messages'):
            game.ui.messages.add("⚔ An ancient Sith Keep materializes on the horizon...")
            game.ui.messages.add("  Dark power emanates from within. Only the strongest may enter.")
    except:
        pass
    
    print(f"[DEBUG] Sith Keep placed at ({entrance_world_x}, {entrance_world_y}), distance from spawn: {best_distance} tiles")
    
    return (entrance_world_x, entrance_world_y)


def get_direction_to_keep(game, from_x, from_y):
    """
    Get a directional hint to the Sith Keep from a given position.
    Used by merchants/landmarks to guide player.
    """
    if not hasattr(game, 'sith_keep_entrance'):
        return "somewhere in the unknown regions"
    
    keep_x, keep_y = game.sith_keep_entrance
    
    dx = keep_x - from_x
    dy = keep_y - from_y
    distance = abs(dx) + abs(dy)
    
    # Determine cardinal direction
    if abs(dx) > abs(dy):
        direction = "to the east" if dx > 0 else "to the west"
    else:
        direction = "to the north" if dy < 0 else "to the south"
    
    # Add secondary direction for diagonals
    if abs(dx) > 20 and abs(dy) > 20:
        if dy < 0:
            direction += "-north" if "north" not in direction else ""
        else:
            direction += "-south" if "south" not in direction else ""
    
    # Distance description
    if distance < 100:
        distance_desc = "nearby"
    elif distance < 200:
        distance_desc = "a moderate distance"
    elif distance < 300:
        distance_desc = "far"
    else:
        distance_desc = "very far"
    
    return f"{direction}, {distance_desc} from here"


def check_puzzle_solution(game, puzzle_id):
    """Check if a puzzle has been solved (all boulders on plates)."""
    if not hasattr(game, 'sith_keep_puzzles'):
        return False
    
    puzzle = game.sith_keep_puzzles.get(puzzle_id)
    if not puzzle or puzzle.get('solved'):
        return puzzle.get('solved', False)
    
    boulders = puzzle['boulders']
    plates = puzzle['plates']
    
    # Check if all plates have boulders
    plates_covered = 0
    for plate_pos in plates:
        if plate_pos in boulders:
            plates_covered += 1
    
    if plates_covered >= len(plates):
        puzzle['solved'] = True
        return True
    
    return False


def move_boulder(game, boulder_x, boulder_y, dx, dy):
    """
    Move a boulder using Force Push/Pull.
    Returns True if moved successfully.
    """
    mh = len(game.game_map)
    mw = len(game.game_map[0]) if mh else 0
    
    # Calculate new position
    new_x = boulder_x + dx
    new_y = boulder_y + dy
    
    # Check if new position is valid
    if (new_x < 0 or new_y < 0 or new_y >= mh or new_x >= mw):
        return False
    
    target_cell = game.game_map[new_y][new_x]
    
    # Can only move to floor
    if target_cell != Display.FLOOR and target_cell not in ['.', '_']:
        try:
            if hasattr(game, 'ui'):
                game.ui.messages.add("The boulder cannot be moved there.")
        except:
            pass
        return False
    
    # Move the boulder
    game.game_map[boulder_y][boulder_x] = Display.FLOOR
    game.game_map[new_y][new_x] = 'O'
    
    # Update puzzle state
    if hasattr(game, 'sith_keep_puzzles'):
        for puzzle_id, puzzle in game.sith_keep_puzzles.items():
            if (boulder_x, boulder_y) in puzzle['boulders']:
                puzzle['boulders'].remove((boulder_x, boulder_y))
                puzzle['boulders'].append((new_x, new_y))
                
                # Check if puzzle is solved
                if check_puzzle_solution(game, puzzle_id):
                    try:
                        if hasattr(game, 'ui'):
                            game.ui.messages.add("★ PUZZLE SOLVED! A distant door opens...")
                    except:
                        pass
                break
    
    try:
        if hasattr(game, 'ui'):
            game.ui.messages.add(f"Boulder moved to ({new_x}, {new_y})")
    except:
        pass
    
    return True
