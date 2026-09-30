from jedi_fugitive.game import logger
log = getattr(logger, 'log', None)
"""
Compass and scanning system to reveal nearby Points of Interest, enemies, and objectives.
"""
import math

def show_compass_scan(game):
    """Display compass showing nearby enemies, POIs, tombs, and NPCs."""
    try:
        px = getattr(game.player, 'x', 0)
        py = getattr(game.player, 'y', 0)
        scan_radius = 15  # Tiles to scan
        
        lines = []
        lines.append("╔════════════════════════════════════════════════════════════╗")
        lines.append("║          FORCE SENSE - COMPASS SCAN                        ║")
        lines.append("╚════════════════════════════════════════════════════════════╝")
        lines.append("")
        lines.append(f"Scanning from position ({px}, {py})...")
        lines.append(f"Scan radius: {scan_radius} tiles")
        lines.append("")
        
        # Scan for enemies
        enemies_found = []
        for enemy in getattr(game, 'enemies', []):
            if not getattr(enemy, 'is_alive', lambda: True)():
                continue
            ex = getattr(enemy, 'x', -999)
            ey = getattr(enemy, 'y', -999)
            dist = abs(ex - px) + abs(ey - py)  # Manhattan distance
            
            if dist <= scan_radius:
                dx = ex - px
                dy = ey - py
                direction = get_direction_string(dx, dy)
                enemy_name = getattr(enemy, 'name', 'Enemy')
                enemy_level = getattr(enemy, 'level', '?')
                enemies_found.append((dist, direction, enemy_name, enemy_level))
        
        if enemies_found:
            lines.append("═══ HOSTILE FORCES ═══")
            enemies_found.sort(key=lambda x: x[0])  # Sort by distance
            for dist, direction, name, level in enemies_found[:10]:  # Show max 10
                lines.append(f"  ⚔ {name} (Lv.{level}) - {dist} tiles {direction}")
            if len(enemies_found) > 10:
                lines.append(f"  ... and {len(enemies_found) - 10} more enemies")
            lines.append("")
        else:
            lines.append("═══ HOSTILE FORCES ═══")
            lines.append("  [No enemies detected in range]")
            lines.append("")
        
        # Scan for Sith tombs
        tombs_found = []
        tomb_entrances = getattr(game, 'tomb_entrances', set())
        for (tx, ty) in tomb_entrances:
            dist = abs(tx - px) + abs(ty - py)
            if dist <= scan_radius * 2:  # Tombs have longer range
                dx = tx - px
                dy = ty - py
                direction = get_direction_string(dx, dy)
                tombs_found.append((dist, direction, tx, ty))
        
        if tombs_found:
            lines.append("═══ SITH TOMBS ═══")
            tombs_found.sort(key=lambda x: x[0])
            for dist, direction, tx, ty in tombs_found[:3]:  # Show nearest 3
                lines.append(f"  ⚱ Tomb Entrance - {dist} tiles {direction} at ({tx},{ty})")
            lines.append("")
        
        # Scan for NPCs
        npcs_found = []
        npcs_on_map = getattr(game, 'npcs_on_map', {})
        for (npc_x, npc_y), npc in npcs_on_map.items():
            dist = abs(npc_x - px) + abs(npc_y - py)
            if dist <= scan_radius:
                dx = npc_x - px
                dy = npc_y - py
                direction = get_direction_string(dx, dy)
                npc_name = getattr(npc, 'name', 'Survivor')
                npcs_found.append((dist, direction, npc_name))
        
        if npcs_found:
            lines.append("═══ SURVIVORS & TRAVELERS ═══")
            npcs_found.sort(key=lambda x: x[0])
            for dist, direction, name in npcs_found:
                lines.append(f"  👤 {name} - {dist} tiles {direction}")
            lines.append("")
        
        # Scan for landmarks
        landmarks_found = []
        landmarks = getattr(game, 'map_landmarks', {})
        for (lx, ly), landmark in landmarks.items():
            dist = abs(lx - px) + abs(ly - py)
            if dist <= scan_radius:
                dx = lx - px
                dy = ly - py
                direction = get_direction_string(dx, dy)
                landmark_name = landmark.get('name', 'Point of Interest')
                landmarks_found.append((dist, direction, landmark_name))
        
        if landmarks_found:
            lines.append("═══ POINTS OF INTEREST ═══")
            landmarks_found.sort(key=lambda x: x[0])
            for dist, direction, name in landmarks_found[:5]:  # Show nearest 5
                lines.append(f"  ⭐ {name} - {dist} tiles {direction}")
            lines.append("")
        
        # Show scan cost
        lines.append("")
        lines.append("[This scan consumed 5 Force Energy]")
        lines.append("")
        lines.append("Press any key to close...")
        
        # Consume Force energy for scan
        if hasattr(game.player, 'force_energy'):
            game.player.force_energy = max(0, game.player.force_energy - 5)
        
        # Display
        try:
            if hasattr(game.ui, 'centered_dialog'):
                game.ui.centered_dialog(lines, title="Compass Scan")
            else:
                for line in lines:
                    game.ui.messages.add(line)
        except:
            for line in lines:
                try:
                    game.ui.messages.add(line)
                except:
                    pass
        
        return True
    except Exception as e:
        if log:
            log.exception("Compass scan failed", exc_info=e)
        try:
            game.ui.messages.add(f"Compass scan failed: {e}")
        except Exception as e2:
            if log:
                log.exception("Compass scan failed to add UI message", exc_info=e2)
        return False

def get_direction_string(dx, dy):
    """Convert dx, dy offsets to compass direction string."""
    if dx == 0 and dy == 0:
        return "here"
    
    # Calculate angle
    angle = math.degrees(math.atan2(-dy, dx))
    angle = (angle + 360) % 360
    
    # Convert to 8-direction compass
    if angle < 22.5 or angle >= 337.5:
        return "to the EAST"
    elif 22.5 <= angle < 67.5:
        return "to the NORTHEAST"
    elif 67.5 <= angle < 112.5:
        return "to the NORTH"
    elif 112.5 <= angle < 157.5:
        return "to the NORTHWEST"
    elif 157.5 <= angle < 202.5:
        return "to the WEST"
    elif 202.5 <= angle < 247.5:
        return "to the SOUTHWEST"
    elif 247.5 <= angle < 292.5:
        return "to the SOUTH"
    else:  # 292.5 to 337.5
        return "to the SOUTHEAST"
