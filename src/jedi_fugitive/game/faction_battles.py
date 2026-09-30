"""
Dynamic Faction Battle System
Spawns faction vs faction battles on the map that player can observe or join.
"""

import random
from typing import List, Tuple, Optional
from enum import Enum


class BattleState(Enum):
    SETUP = "setup"
    ACTIVE = "active"
    ENDING = "ending"
    FINISHED = "finished"


class FactionBattle:
    """Represents an ongoing battle between two factions."""
    
    def __init__(self, faction_a: str, faction_b: str, location: Tuple[int, int], size: int):
        self.faction_a = faction_a
        self.faction_b = faction_b
        self.center_x, self.center_y = location
        self.size = size  # Battle radius
        self.state = BattleState.SETUP
        self.turn_count = 0
        self.max_turns = random.randint(20, 40)
        
        self.faction_a_units = []  # List of enemies
        self.faction_b_units = []  # List of enemies
        
        self.faction_a_casualties = 0
        self.faction_b_casualties = 0
        
        self.player_joined = None  # None, 'a', or 'b'
        
    def is_near_battle(self, x: int, y: int, radius: int = 15) -> bool:
        """Check if position is near the battle."""
        dist = abs(x - self.center_x) + abs(y - self.center_y)
        return dist <= radius
    
    def is_inside_battle(self, x: int, y: int) -> bool:
        """Check if position is inside the battle zone."""
        dist = abs(x - self.center_x) + abs(y - self.center_y)
        return dist <= self.size
    
    def update(self, game) -> List[str]:
        """Update battle state. Returns list of messages."""
        messages = []
        
        if self.state == BattleState.FINISHED:
            return messages
        
        self.turn_count += 1
        
        # Check if battle should end
        faction_a_alive = sum(1 for u in self.faction_a_units if getattr(u, 'hp', 0) > 0)
        faction_b_alive = sum(1 for u in self.faction_b_units if getattr(u, 'hp', 0) > 0)
        
        if faction_a_alive == 0 or faction_b_alive == 0 or self.turn_count >= self.max_turns:
            self.state = BattleState.ENDING
            
            if faction_a_alive > faction_b_alive:
                messages.append(f"#2#{self.faction_a} forces have won the battle!#0#")
            elif faction_b_alive > faction_a_alive:
                messages.append(f"#1#{self.faction_b} forces have won the battle!#0#")
            else:
                messages.append(f"#3#The battle ends in a stalemate.#0#")
            
            self.state = BattleState.FINISHED
            return messages
        
        # Units fight each other
        if self.state == BattleState.ACTIVE:
            # Occasionally show battle updates
            if self.turn_count % 5 == 0 and random.random() < 0.3:
                messages.append(f"#3#Fierce fighting between {self.faction_a} and {self.faction_b}!#0#")
        
        return messages
    
    def get_winner(self) -> Optional[str]:
        """Return winning faction name, or None if not finished."""
        if self.state != BattleState.FINISHED:
            return None
        
        faction_a_alive = sum(1 for u in self.faction_a_units if getattr(u, 'hp', 0) > 0)
        faction_b_alive = sum(1 for u in self.faction_b_units if getattr(u, 'hp', 0) > 0)
        
        if faction_a_alive > faction_b_alive:
            return self.faction_a
        elif faction_b_alive > faction_a_alive:
            return self.faction_b
        return None


class FactionBattleManager:
    """Manages spawning and updating faction battles."""
    
    def __init__(self):
        self.active_battles: List[FactionBattle] = []
        self.battle_cooldown = 0
        self.min_cooldown = 100  # Turns between battles
        
        # Faction conflict rules
        self.faction_conflicts = {
            'Sith Empire': ['Republic', 'Mandalorian'],
            'Republic': ['Sith Empire', 'Hutt'],
            'Hutt': ['Republic', 'Settlers', 'Mandalorian'],
            'Settlers': ['Sith Empire', 'Hutt'],
            'Mandalorian': ['Sith Empire', 'Hutt'],
        }
    
    def can_spawn_battle(self, game) -> bool:
        """Check if conditions allow spawning a new battle."""
        # Don't spawn too many battles at once
        if len(self.active_battles) >= 2:
            return False
        
        # Cooldown check
        if self.battle_cooldown > 0:
            return False
        
        # Don't spawn battles too close to player
        px, py = game.player.x, game.player.y
        for battle in self.active_battles:
            if battle.is_near_battle(px, py, radius=30):
                return False
        
        return True
    
    def spawn_battle(self, game) -> Optional[FactionBattle]:
        """Attempt to spawn a new faction battle."""
        if not self.can_spawn_battle(game):
            return None
        
        # Choose two conflicting factions
        faction_a = random.choice(list(self.faction_conflicts.keys()))
        possible_enemies = self.faction_conflicts[faction_a]
        faction_b = random.choice(possible_enemies)
        
        # Find a suitable location (away from player, on walkable terrain)
        px, py = game.player.x, game.player.y
        map_h = len(game.game_map)
        map_w = len(game.game_map[0]) if map_h > 0 else 0
        
        for attempt in range(50):
            # Random location far from player
            bx = random.randint(10, map_w - 10)
            by = random.randint(10, map_h - 10)
            
            # Check distance from player (must be 40+ tiles away)
            dist_from_player = abs(bx - px) + abs(by - py)
            if dist_from_player < 40:
                continue
            
            # Check if location is walkable
            from jedi_fugitive.game.level import Display
            if game.game_map[by][bx] != Display.FLOOR:
                continue
            
            # Valid location found
            battle_size = random.randint(8, 15)
            battle = FactionBattle(faction_a, faction_b, (bx, by), battle_size)
            
            # Spawn units for both sides
            self._spawn_battle_units(game, battle, faction_a, faction_b, bx, by, battle_size)
            
            battle.state = BattleState.ACTIVE
            self.active_battles.append(battle)
            self.battle_cooldown = self.min_cooldown
            
            # Notify if close enough
            if dist_from_player < 50:
                if hasattr(game, 'ui') and hasattr(game.ui, 'messages'):
                    game.ui.messages.add(f"#3#Battle erupts between {faction_a} and {faction_b} forces!#0#")
            
            return battle
        
        return None
    
    def _spawn_battle_units(self, game, battle: FactionBattle, faction_a: str, faction_b: str, 
                           center_x: int, center_y: int, radius: int):
        """Spawn enemy units for both factions in the battle."""
        from jedi_fugitive.game.enemy import Enemy
        from jedi_fugitive.game.personality import EnemyPersonality
        
        # Number of units per side
        unit_count = random.randint(3, 6)
        player_level = getattr(game.player, 'level', 1)
        
        # Spawn faction A units
        for i in range(unit_count):
            enemy = self._create_faction_unit(faction_a, player_level)
            if enemy:
                # Position around center
                angle = (i / unit_count) * 6.28  # 2*pi
                offset = radius // 2
                ex = int(center_x + offset * (1 if i % 2 == 0 else -1))
                ey = int(center_y + offset * (1 if i < unit_count // 2 else -1))
                
                # Ensure valid position
                map_h = len(game.game_map)
                map_w = len(game.game_map[0]) if map_h > 0 else 0
                ex = max(1, min(map_w - 2, ex))
                ey = max(1, min(map_h - 2, ey))
                
                enemy.x = ex
                enemy.y = ey
                enemy.faction = faction_a
                enemy.in_faction_battle = True
                enemy.battle_target_faction = faction_b
                
                battle.faction_a_units.append(enemy)
                game.enemies.append(enemy)
        
        # Spawn faction B units
        for i in range(unit_count):
            enemy = self._create_faction_unit(faction_b, player_level)
            if enemy:
                # Position on opposite side
                angle = (i / unit_count) * 6.28
                offset = radius // 2
                ex = int(center_x - offset * (1 if i % 2 == 0 else -1))
                ey = int(center_y - offset * (1 if i < unit_count // 2 else -1))
                
                # Ensure valid position
                map_h = len(game.game_map)
                map_w = len(game.game_map[0]) if map_h > 0 else 0
                ex = max(1, min(map_w - 2, ex))
                ey = max(1, min(map_h - 2, ey))
                
                enemy.x = ex
                enemy.y = ey
                enemy.faction = faction_b
                enemy.in_faction_battle = True
                enemy.battle_target_faction = faction_a
                
                battle.faction_b_units.append(enemy)
                game.enemies.append(enemy)
    
    def _create_faction_unit(self, faction: str, level: int):
        """Create an appropriate enemy unit for the faction."""
        from jedi_fugitive.game import enemies_sith as sith
        
        if faction == 'Sith Empire':
            choices = [sith.create_sith_trooper, sith.create_sith_acolyte, sith.create_sith_warrior]
            creator = random.choice(choices)
            return creator(level=level)
        
        elif faction == 'Republic':
            from jedi_fugitive.game.enemy import Enemy
            from jedi_fugitive.game.personality import EnemyPersonality
            enemy = Enemy("Republic Soldier", 18 + level * 3, 8 + level, 4 + level//2, 5, EnemyPersonality(), 25, 0, 0, level=level)
            enemy.symbol = 'R'
            enemy.color = 4  # Blue
            return enemy
        
        elif faction == 'Mandalorian':
            from jedi_fugitive.game.enemy import Enemy
            from jedi_fugitive.game.personality import EnemyPersonality
            enemy = Enemy("Mandalorian Warrior", 22 + level * 4, 10 + level, 6 + level//2, 7, EnemyPersonality(), 40, 0, 0, level=level)
            enemy.symbol = 'M'
            enemy.color = 6  # Cyan
            return enemy
        
        elif faction == 'Hutt':
            from jedi_fugitive.game.enemy import Enemy
            from jedi_fugitive.game.personality import EnemyPersonality
            enemy = Enemy("Hutt Enforcer", 16 + level * 3, 7 + level, 3 + level//3, 6, EnemyPersonality(), 20, 0, 0, level=level)
            enemy.symbol = 'H'
            enemy.color = 3  # Yellow
            return enemy
        
        elif faction == 'Settlers':
            from jedi_fugitive.game.enemy import Enemy
            from jedi_fugitive.game.personality import EnemyPersonality
            enemy = Enemy("Armed Settler", 12 + level * 2, 5 + level//2, 2 + level//4, 8, EnemyPersonality(), 10, 0, 0, level=level)
            enemy.symbol = 'C'  # Civilian
            enemy.color = 7  # White
            return enemy
        
        return None
    
    def update_battles(self, game) -> List[str]:
        """Update all active battles. Returns list of messages."""
        messages = []
        
        # Decrement cooldown
        if self.battle_cooldown > 0:
            self.battle_cooldown -= 1
        
        # Try to spawn new battle occasionally
        if random.random() < 0.02:  # 2% chance per turn
            new_battle = self.spawn_battle(game)
            if new_battle:
                pass  # Message already sent in spawn_battle
        
        # Update existing battles
        finished_battles = []
        for battle in self.active_battles:
            battle_messages = battle.update(game)
            messages.extend(battle_messages)
            
            if battle.state == BattleState.FINISHED:
                finished_battles.append(battle)
                
                # Clean up dead units
                for unit in battle.faction_a_units + battle.faction_b_units:
                    if getattr(unit, 'hp', 0) <= 0 and unit in game.enemies:
                        game.enemies.remove(unit)
        
        # Remove finished battles
        for battle in finished_battles:
            self.active_battles.remove(battle)
        
        return messages
    
    def cleanup_dead_units(self, game, enemy):
        """Called when an enemy dies to update battle stats."""
        for battle in self.active_battles:
            if enemy in battle.faction_a_units:
                battle.faction_a_casualties += 1
            elif enemy in battle.faction_b_units:
                battle.faction_b_casualties += 1
