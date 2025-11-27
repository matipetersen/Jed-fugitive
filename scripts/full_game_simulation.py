#!/usr/bin/env python3
"""
Complete Game Simulation: Test all systems, Sith Keep, victory paths, equipment, levels.
Simulates 3 playthroughs: Light Side, Dark Side, and Balanced paths.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game.player import Player
from jedi_fugitive.game.level import Display
from jedi_fugitive.items.weapons import WEAPONS
from jedi_fugitive.items.armor import ARMORS
import random

class DummyStdScr:
    """Dummy curses screen for headless simulation."""
    def __init__(self, h=24, w=80):
        self._h = h
        self._w = w
    def getmaxyx(self):
        return (self._h, self._w)
    def subwin(self, h, w, y, x):
        return self
    def clear(self): pass
    def erase(self): pass
    def border(self): pass
    def addstr(self, *a, **k): pass
    def addnstr(self, *a, **k): pass
    def refresh(self): pass
    def noutrefresh(self): pass
    def resize(self, h, w): 
        self._h, self._w = h, w
    def mvwin(self, y, x): pass
    def move(self, y, x): pass
    def clrtoeol(self): pass
    def getch(self): 
        return -1

class GameSimulator:
    """Complete game simulation with detailed tracking."""
    
    def __init__(self, alignment_path="balanced"):
        self.alignment_path = alignment_path  # "light", "dark", or "balanced"
        dummy_screen = DummyStdScr()
        self.gm = GameManager(dummy_screen)
        self.gm.new_game()
        
        self.stats = {
            'turns': 0,
            'combat_encounters': 0,
            'kills': 0,
            'tombs_cleared': 0,
            'artifacts_collected': 0,
            'equipment_found': [],
            'max_level': 1,
            'max_hp': self.gm.player.max_hp,
            'sith_keep_spawned': False,
            'final_boss_faced': False,
            'victory': False,
            'death_cause': None,
        }
        self.cleared_tombs = set()
        
    def log(self, message):
        """Print timestamped log message."""
        print(f"[Turn {self.stats['turns']:4d}] {message}")
        
    def find_nearest_target(self, target_type):
        """Find nearest target of given type (tomb, comms, ship, etc)."""
        px, py = self.gm.player.x, self.gm.player.y
        nearest = None
        min_dist = float('inf')
        
        if target_type == 'tomb':
            for tx, ty in getattr(self.gm, 'tomb_entrances', []):
                tomb_key = f"tomb_{tx}_{ty}"
                if tomb_key not in self.cleared_tombs:
                    dist = abs(tx - px) + abs(ty - py)
                    if dist < min_dist:
                        min_dist = dist
                        nearest = (tx, ty)
        
        elif target_type == 'comms':
            comms_pos = getattr(self.gm, 'comms_pos', None)
            if comms_pos:
                dist = abs(comms_pos[0] - px) + abs(comms_pos[1] - py)
                nearest = comms_pos
                min_dist = dist
        
        elif target_type == 'ship':
            ship_pos = getattr(self.gm, 'ship_pos', None)
            if ship_pos:
                dist = abs(ship_pos[0] - px) + abs(ship_pos[1] - py)
                nearest = ship_pos
                min_dist = dist
                
        return nearest, min_dist
    
    def move_towards(self, target_x, target_y):
        """Move one step towards target."""
        px, py = self.gm.player.x, self.gm.player.y
        
        if px == target_x and py == target_y:
            return True  # Arrived
        
        # Simple pathfinding: move in cardinal directions
        dx = target_x - px
        dy = target_y - py
        
        # Try horizontal first if further
        if abs(dx) > abs(dy):
            new_x = px + (1 if dx > 0 else -1)
            if self.try_move(new_x, py):
                return False
        
        # Try vertical
        new_y = py + (1 if dy > 0 else -1)
        if self.try_move(px, new_y):
            return False
        
        # Try horizontal as fallback
        new_x = px + (1 if dx > 0 else -1)
        if self.try_move(new_x, py):
            return False
            
        # Stuck or arrived
        return True
    
    def try_move(self, new_x, new_y):
        """Attempt to move to position."""
        # Check bounds
        if not (0 <= new_y < len(self.gm.game_map) and 
                0 <= new_x < len(self.gm.game_map[0])):
            return False
        
        tile = self.gm.game_map[new_y][new_x]
        
        # Check if walkable
        if tile == Display.WALL:
            return False
        
        # Check for enemy
        for enemy in getattr(self.gm, 'enemies', []):
            if enemy.x == new_x and enemy.y == new_y and enemy.hp > 0:
                self.combat(enemy)
                return False  # Don't move into enemy space
        
        # Move player
        self.gm.player.x = new_x
        self.gm.player.y = new_y
        self.stats['turns'] += 1
        
        # Check for pickups
        self.check_pickups(new_x, new_y)
        
        return True
    
    def check_pickups(self, x, y):
        """Check for items at position."""
        tile = self.gm.game_map[y][x]
        
        # Check for Jedi Artifact (Q token)
        if tile == 'Q':
            self.stats['artifacts_collected'] += 1
            self.log(f"✓ JEDI ARTIFACT collected ({self.stats['artifacts_collected']}/3)")
            self.gm.game_map[y][x] = Display.FLOOR
            
            # Add to inventory
            jedi_artifact = {
                'name': 'Jedi Artifact',
                'type': 'quest_item',
                'quest': True
            }
            self.gm.player.inventory.append(jedi_artifact)
        
        # Check for other items
        elif tile in [Display.POTION, Display.GOLD, Display.ARTIFACT]:
            self.log(f"  Picked up item: {tile}")
            self.gm.game_map[y][x] = Display.FLOOR
    
    def combat(self, enemy):
        """Simulate combat with enemy."""
        self.stats['combat_encounters'] += 1
        
        player_dmg = self.calculate_player_damage()
        enemy_dmg = getattr(enemy, 'attack', 5)
        
        # Fight until one dies
        while enemy.hp > 0 and self.gm.player.hp > 0:
            # Player attacks
            enemy.hp -= player_dmg
            self.stats['turns'] += 1
            
            if enemy.hp <= 0:
                self.stats['kills'] += 1
                # Alignment choice simulation
                if self.alignment_path == "light":
                    self.gm.player.light_side_points += 1
                elif self.alignment_path == "dark":
                    self.gm.player.dark_corruption += 2
                break
            
            # Enemy attacks
            self.gm.player.hp -= enemy_dmg
            
        if self.gm.player.hp <= 0:
            self.stats['death_cause'] = f"Killed by {getattr(enemy, 'name', 'enemy')}"
            return False
        
        # Level up check
        if self.stats['kills'] % 5 == 0:
            self.level_up()
        
        return True
    
    def calculate_player_damage(self):
        """Calculate player damage output."""
        base_dmg = 2  # Training Saber
        
        # Check equipped weapon
        equipped_weapon = getattr(self.gm.player, 'equipped_weapon', None)
        if equipped_weapon:
            base_dmg = getattr(equipped_weapon, 'base_damage', base_dmg)
        
        # Add level bonus
        level_bonus = (self.gm.player.level - 1) * 2
        
        return base_dmg + level_bonus
    
    def level_up(self):
        """Level up the player."""
        self.gm.player.level += 1
        self.gm.player.max_hp += 10
        self.gm.player.hp = self.gm.player.max_hp
        self.stats['max_level'] = self.gm.player.level
        self.stats['max_hp'] = self.gm.player.max_hp
        self.log(f"⬆ LEVEL UP to {self.gm.player.level}! HP: {self.gm.player.max_hp}")
    
    def explore_tomb(self, entrance_x, entrance_y):
        """Simulate exploring a tomb to get artifact."""
        tomb_key = f"tomb_{entrance_x}_{entrance_y}"
        self.log(f"→ Entering tomb at ({entrance_x}, {entrance_y})")
        
        # Simulate descent (5-7 levels, 2-4 enemies per level)
        num_levels = random.randint(5, 7)
        total_enemies = 0
        
        for level in range(1, num_levels + 1):
            enemies_on_level = random.randint(2, 4)
            total_enemies += enemies_on_level
            
            # Simulate combat
            for _ in range(enemies_on_level):
                # Create mock enemy
                class MockEnemy:
                    def __init__(self, level):
                        self.name = f"Sith Acolyte (L{level})"
                        self.hp = 20 + (level * 5)
                        self.attack = 5 + level
                        self.x = 0
                        self.y = 0
                
                enemy = MockEnemy(level)
                if not self.combat(enemy):
                    self.log(f"✗ DIED in tomb at level {level}")
                    return False
        
        # Reached artifact
        self.stats['artifacts_collected'] += 1
        self.log(f"✓ ARTIFACT acquired from tomb! ({self.stats['artifacts_collected']}/3)")
        
        # Add to inventory
        jedi_artifact = {
            'name': 'Jedi Artifact',
            'type': 'quest_item',
            'quest': True
        }
        self.gm.player.inventory.append(jedi_artifact)
        
        # Simulate ascent (faster)
        ascent_turns = num_levels * 3
        self.stats['turns'] += ascent_turns
        
        self.cleared_tombs.add(tomb_key)
        self.stats['tombs_cleared'] += 1
        
        self.log(f"← Exited tomb. Total enemies: {total_enemies}, Turns: ~{num_levels * enemies_on_level * 2 + ascent_turns}")
        return True
    
    def activate_comms(self):
        """Try to activate comms terminal."""
        # Check if we have 3 artifacts
        artifact_count = sum(1 for item in self.gm.player.inventory 
                           if isinstance(item, dict) and 
                           item.get('type') == 'quest_item' and 
                           'artifact' in item.get('name', '').lower())
        
        if artifact_count >= 3:
            self.log("✓ COMMS ACTIVATED! Distress beacon sent.")
            self.gm.comms_established = True
            
            # Check for Sith Keep spawn
            if hasattr(self.gm, 'sith_keep_pos') or 'Sith Keep' in str(getattr(self.gm, 'map_landmarks', {})):
                self.stats['sith_keep_spawned'] = True
                self.log("⚠ SITH KEEP has spawned on the map!")
            
            return True
        else:
            self.log(f"✗ Need {3 - artifact_count} more artifacts to activate comms")
            return False
    
    def face_final_boss(self):
        """Simulate final boss fight."""
        self.stats['final_boss_faced'] = True
        self.log("⚔ FINAL BOSS SPAWNED!")
        
        # Boss stats based on alignment
        boss_hp = 100 + (self.gm.player.level * 10)
        boss_dmg = 15 + self.gm.player.level
        
        if self.alignment_path == "dark":
            boss_name = "Jedi Council Enforcer"
        elif self.alignment_path == "light":
            boss_name = "Sith Inquisitor"
        else:
            boss_name = "Dark Jedi Hunter"
        
        self.log(f"  Boss: {boss_name} (HP: {boss_hp}, DMG: {boss_dmg})")
        
        # Simulate boss fight
        player_dmg = self.calculate_player_damage()
        turns_in_combat = 0
        
        while boss_hp > 0 and self.gm.player.hp > 0:
            boss_hp -= player_dmg
            turns_in_combat += 1
            self.stats['turns'] += 1
            
            if boss_hp <= 0:
                break
            
            self.gm.player.hp -= boss_dmg
        
        if self.gm.player.hp <= 0:
            self.stats['death_cause'] = f"Defeated by {boss_name}"
            self.log(f"✗ DEFEATED by {boss_name} after {turns_in_combat} turns")
            return False
        
        self.log(f"✓ BOSS DEFEATED after {turns_in_combat} turns!")
        return True
    
    def run_simulation(self):
        """Run complete game simulation."""
        print("\n" + "="*80)
        print(f"FULL GAME SIMULATION - {self.alignment_path.upper()} PATH")
        print("="*80)
        
        self.log(f"Starting game with {self.alignment_path} alignment path")
        self.log(f"Player: Level {self.gm.player.level}, HP {self.gm.player.hp}/{self.gm.player.max_hp}")
        
        # Check starting inventory
        starting_items = [item.name if hasattr(item, 'name') else item.get('name', 'item') 
                         for item in self.gm.player.inventory]
        self.log(f"Starting inventory: {', '.join(starting_items)}")
        
        # Phase 1: Collect 3 Jedi Artifacts from tombs
        self.log("\n--- PHASE 1: Artifact Collection ---")
        
        while self.stats['artifacts_collected'] < 3:
            # Find nearest tomb
            tomb_pos, dist = self.find_nearest_target('tomb')
            
            if not tomb_pos:
                self.log("✗ No more tombs available!")
                break
            
            self.log(f"Traveling to tomb at {tomb_pos} (distance: {dist})")
            
            # Travel to tomb
            for _ in range(dist):
                if not self.move_towards(tomb_pos[0], tomb_pos[1]):
                    break
            
            # Explore tomb
            if not self.explore_tomb(tomb_pos[0], tomb_pos[1]):
                break  # Died in tomb
        
        if self.gm.player.hp <= 0:
            self.print_summary()
            return False
        
        # Phase 2: Activate comms terminal
        self.log("\n--- PHASE 2: Comms Activation ---")
        
        comms_pos, dist = self.find_nearest_target('comms')
        if comms_pos:
            self.log(f"Traveling to comms terminal at {comms_pos} (distance: {dist})")
            
            # Travel to comms
            for _ in range(dist):
                if not self.move_towards(comms_pos[0], comms_pos[1]):
                    break
            
            # Activate comms
            self.activate_comms()
        
        # Phase 3: Face final boss at ship
        self.log("\n--- PHASE 3: Final Boss & Victory ---")
        
        ship_pos, dist = self.find_nearest_target('ship')
        if ship_pos:
            self.log(f"Returning to ship at {ship_pos} (distance: {dist})")
            
            # Travel to ship
            for _ in range(dist):
                if not self.move_towards(ship_pos[0], ship_pos[1]):
                    break
            
            # Face final boss
            if self.face_final_boss():
                self.log("\n🎉 VICTORY! Game completed successfully!")
                self.stats['victory'] = True
        
        self.print_summary()
        return self.stats['victory']
    
    def print_summary(self):
        """Print detailed game summary."""
        print("\n" + "="*80)
        print("GAME SUMMARY")
        print("="*80)
        
        print(f"\nAlignment Path: {self.alignment_path.upper()}")
        print(f"Result: {'✓ VICTORY' if self.stats['victory'] else '✗ DEFEAT'}")
        if self.stats['death_cause']:
            print(f"Death Cause: {self.stats['death_cause']}")
        
        print(f"\n--- Stats ---")
        print(f"Total Turns: {self.stats['turns']}")
        print(f"Final Level: {self.stats['max_level']}")
        print(f"Final HP: {self.gm.player.hp}/{self.stats['max_hp']}")
        print(f"Light Side Points: {self.gm.player.light_side_points}")
        print(f"Dark Corruption: {self.gm.player.dark_corruption}")
        
        print(f"\n--- Progress ---")
        print(f"Tombs Cleared: {self.stats['tombs_cleared']}")
        print(f"Artifacts Collected: {self.stats['artifacts_collected']}/3")
        print(f"Combat Encounters: {self.stats['combat_encounters']}")
        print(f"Total Kills: {self.stats['kills']}")
        print(f"Sith Keep Spawned: {'Yes' if self.stats['sith_keep_spawned'] else 'No'}")
        print(f"Final Boss Faced: {'Yes' if self.stats['final_boss_faced'] else 'No'}")
        
        print(f"\n--- Equipment ---")
        equipped_weapon = getattr(self.gm.player, 'equipped_weapon', None)
        if equipped_weapon:
            weapon_name = getattr(equipped_weapon, 'name', 'Unknown')
            weapon_dmg = getattr(equipped_weapon, 'base_damage', 0)
            print(f"Weapon: {weapon_name} ({weapon_dmg} damage)")
        else:
            print(f"Weapon: Training Saber (2 damage)")
        
        equipped_armor = getattr(self.gm.player, 'equipped_armor', None)
        if equipped_armor:
            armor_name = getattr(equipped_armor, 'name', 'Unknown')
            armor_def = getattr(equipped_armor, 'defense', 0)
            print(f"Armor: {armor_name} ({armor_def} defense)")
        else:
            print(f"Armor: None")
        
        print("\n" + "="*80)


def main():
    """Run simulations for all three alignment paths."""
    
    print("\n" + "█"*80)
    print("JEDI FUGITIVE - COMPREHENSIVE GAME SIMULATION")
    print("█"*80)
    
    results = {}
    
    for alignment in ["light", "balanced", "dark"]:
        sim = GameSimulator(alignment_path=alignment)
        success = sim.run_simulation()
        results[alignment] = {
            'success': success,
            'turns': sim.stats['turns'],
            'level': sim.stats['max_level'],
            'kills': sim.stats['kills']
        }
        
        print("\n" + "─"*80 + "\n")
    
    # Final comparison
    print("\n" + "█"*80)
    print("FINAL COMPARISON")
    print("█"*80)
    
    for alignment, data in results.items():
        status = "✓ WIN" if data['success'] else "✗ LOSS"
        print(f"{alignment.upper():10s} {status:8s} | Turns: {data['turns']:4d} | Level: {data['level']:2d} | Kills: {data['kills']:3d}")
    
    print("█"*80)


if __name__ == "__main__":
    main()
