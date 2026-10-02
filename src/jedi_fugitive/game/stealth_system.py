"""
Stealth and Hiding System
Allows players to hide, sneak, and use stealth mechanics to avoid detection.
"""

import random
from typing import Optional, Tuple


class StealthSystem:
    """Manages player stealth state and detection mechanics."""
    
    def __init__(self):
        self.is_hidden = False
        self.stealth_bonus = 0  # From equipment/abilities
        self.noise_level = 0  # 0-100, affects detection chance
        self.last_movement_turn = 0
        
    def attempt_hide(self, player, game) -> Tuple[bool, str]:
        """
        Attempt to hide in current position.
        Returns: (success: bool, message: str)
        """
        # Check if terrain allows hiding
        px, py = player.x, player.y
        terrain = game.game_map[py][px] if 0 <= py < len(game.game_map) and 0 <= px < len(game.game_map[0]) else '.'
        
        # Trees, ruins, wreckage provide hiding spots
        from jedi_fugitive.game.level import Display
        hiding_spots = {
            Display.TREE, 'T', '🌲',
            Display.WRECKAGE, 'x', '💥',
            'R',  # Ruins
            '⌂',  # Buildings
        }
        
        # Check adjacent tiles for hiding spots
        has_cover = False
        for dx, dy in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = px + dx, py + dy
            if 0 <= ny < len(game.game_map) and 0 <= nx < len(game.game_map[0]):
                if game.game_map[ny][nx] in hiding_spots:
                    has_cover = True
                    break
        
        if not has_cover:
            return False, "No suitable cover nearby to hide."
        
        # Base hide chance: 60%
        hide_chance = 60
        
        # Stealth bonuses
        hide_chance += self.stealth_bonus
        hide_chance += getattr(player, 'evasion', 0) // 2
        
        # Disguise bonus
        if getattr(player, 'disguise', None):
            hide_chance += 15
        
        # darkness hides you
        try:
            from jedi_fugitive.game import daynight
            hide_chance += daynight.hide_bonus(game)
        except Exception:
            pass

        # Penalti for nearby enemies
        nearby_enemies = self._count_nearby_enemies(player, game, radius=5)
        hide_chance -= nearby_enemies * 10
        
        # Check for Force detection (enemies with Force powers see through stealth better)
        force_aware_enemies = self._count_force_aware_enemies(player, game, radius=8)
        hide_chance -= force_aware_enemies * 5
        
        # Roll for success
        if random.randint(1, 100) <= hide_chance:
            self.is_hidden = True
            self.noise_level = 0
            return True, f"#2#You hide in the shadows...#0# (Stealth: {hide_chance}%)"
        else:
            self.noise_level += 20
            return False, f"#3#Failed to hide!#0# Enemies may have noticed."
    
    def break_stealth(self, reason: str = "movement") -> str:
        """Break stealth state and return notification message."""
        if not self.is_hidden:
            return ""
        
        self.is_hidden = False
        self.noise_level = min(100, self.noise_level + 30)
        
        messages = {
            "movement": "You emerge from hiding.",
            "attack": "#1#Stealth broken by attack!#0#",
            "force_power": "#3#Using Force powers reveals your location!#0#",
            "detected": "#3#You've been spotted!#0#",
        }
        return messages.get(reason, "Stealth broken.")
    
    def update_stealth(self, player, game, action_type: str = "idle") -> Optional[str]:
        """
        Update stealth state based on player actions.
        Returns message if stealth changes.
        """
        if not self.is_hidden:
            return None
        
        # Actions that break stealth
        if action_type in ["attack", "force_power", "pickup", "throw"]:
            return self.break_stealth(action_type)
        
        # Movement increases noise
        if action_type == "move":
            self.noise_level += 5
            self.last_movement_turn = getattr(game, 'turn_count', 0)
        
        # Check detection by nearby enemies
        if self._check_detection(player, game):
            return self.break_stealth("detected")
        
        # Reduce noise over time when idle
        if action_type == "idle":
            self.noise_level = max(0, self.noise_level - 3)
        
        return None
    
    def _check_detection(self, player, game) -> bool:
        """Check if any nearby enemy detects the hidden player."""
        if not self.is_hidden:
            return False
        
        px, py = player.x, player.y
        
        for enemy in getattr(game, 'enemies', []):
            ex, ey = getattr(enemy, 'x', 0), getattr(enemy, 'y', 0)
            dist = abs(ex - px) + abs(ey - py)
            
            # Base detection chance based on distance
            if dist > 6:
                continue  # Too far to detect
            
            detection_chance = 100 - dist * 15  # Closer = higher chance
            detection_chance += self.noise_level // 2
            detection_chance -= self.stealth_bonus
            detection_chance -= getattr(player, 'evasion', 0) // 2
            
            # Elite enemies are better at detection
            if getattr(enemy, 'is_boss', False) or 'inquisitor' in getattr(enemy, 'name', '').lower():
                detection_chance += 20
            
            # Force-sensitive enemies detect better
            if hasattr(enemy, 'force_abilities') and enemy.force_abilities:
                detection_chance += 15
            
            if random.randint(1, 100) <= detection_chance:
                return True
        
        return False
    
    def _count_nearby_enemies(self, player, game, radius: int = 5) -> int:
        """Count enemies within radius of player."""
        px, py = player.x, player.y
        count = 0
        
        for enemy in getattr(game, 'enemies', []):
            ex, ey = getattr(enemy, 'x', 0), getattr(enemy, 'y', 0)
            dist = abs(ex - px) + abs(ey - py)
            if dist <= radius:
                count += 1
        
        return count
    
    def _count_force_aware_enemies(self, player, game, radius: int = 8) -> int:
        """Count Force-sensitive enemies within radius."""
        px, py = player.x, player.y
        count = 0
        
        for enemy in getattr(game, 'enemies', []):
            if not hasattr(enemy, 'force_abilities') or not enemy.force_abilities:
                continue
            
            ex, ey = getattr(enemy, 'x', 0), getattr(enemy, 'y', 0)
            dist = abs(ex - px) + abs(ey - py)
            if dist <= radius:
                count += 1
        
        return count
    
    def get_detection_range_modifier(self) -> int:
        """Return modifier to enemy alert/detection ranges while hidden."""
        if not self.is_hidden:
            return 0
        
        # Hidden players are detected at shorter range
        return -3 - (self.stealth_bonus // 10)
    
    def apply_stealth_bonus(self, bonus: int, duration: int = 0):
        """Apply temporary or permanent stealth bonus."""
        self.stealth_bonus += bonus
