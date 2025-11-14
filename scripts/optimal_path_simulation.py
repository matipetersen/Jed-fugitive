#!/usr/bin/env python3
"""
Optimal Path to Victory Simulation
Tracks the shortest path through the game with detailed phase timing.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game.player import Player
from jedi_fugitive.items.tokens import TOKEN_MAP
import time

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

class OptimalPathSimulator:
    """Simulates optimal speedrun path through the game."""
    
    def __init__(self):
        dummy_screen = DummyStdScr()
        self.gm = GameManager(dummy_screen)
        self.phase_timings = {}
        self.total_turns = 0
        self.artifacts_collected = 0
        self.tombs_completed = 0
        
    def log_phase(self, phase_name, turns_taken, details=""):
        """Log timing for a game phase."""
        self.phase_timings[phase_name] = {
            'turns': turns_taken,
            'total_turns': self.total_turns,
            'details': details
        }
        print(f"\n{'='*70}")
        print(f"PHASE: {phase_name}")
        print(f"Turns taken: {turns_taken}")
        print(f"Total turns elapsed: {self.total_turns}")
        if details:
            print(f"Details: {details}")
        print(f"{'='*70}")
        
    def find_nearest_poi(self):
        """Find nearest Point of Interest for Force power."""
        player_pos = (self.gm.player.x, self.gm.player.y)
        nearest_poi = None
        min_dist = float('inf')
        
        # POIs are stored in game.map_landmarks
        for (px, py), landmark_data in getattr(self.gm, 'map_landmarks', {}).items():
            dist = abs(px - player_pos[0]) + abs(py - player_pos[1])
            if dist < min_dist:
                min_dist = dist
                nearest_poi = {'x': px, 'y': py, 'data': landmark_data}
                    
        return nearest_poi, min_dist
        
    def find_nearest_tomb(self):
        """Find nearest uncleared tomb entrance."""
        player_pos = (self.gm.player.x, self.gm.player.y)
        nearest_tomb = None
        min_dist = float('inf')
        
        for tx, ty in self.gm.tomb_entrances:
            # Check if we've already gotten artifact from this tomb
            tomb_key = f"tomb_{tx}_{ty}"
            if tomb_key not in getattr(self, 'cleared_tombs', set()):
                dist = abs(tx - player_pos[0]) + abs(ty - player_pos[1])
                if dist < min_dist:
                    min_dist = dist
                    nearest_tomb = (tx, ty)
                    
        return nearest_tomb, min_dist
        
    def move_towards(self, target_x, target_y):
        """Move one step towards target. Returns True if moved, False if arrived."""
        px, py = self.gm.player.x, self.gm.player.y
        
        if px == target_x and py == target_y:
            return False  # Already there
            
        # Simple pathfinding: move in direction that reduces distance
        dx = 0 if px == target_x else (1 if target_x > px else -1)
        dy = 0 if py == target_y else (1 if target_y > py else -1)
        
        # Try diagonal first, then cardinal directions
        if dx != 0 and dy != 0:
            new_x, new_y = px + dx, py + dy
            if self.gm.is_walkable(new_x, new_y):
                self.gm.player.move(dx, dy, self.gm)
                self.total_turns += 1
                return True
                
        # Try horizontal
        if dx != 0:
            new_x = px + dx
            if self.gm.is_walkable(new_x, py):
                self.gm.player.move(dx, 0, self.gm)
                self.total_turns += 1
                return True
                
        # Try vertical
        if dy != 0:
            new_y = py + dy
            if self.gm.is_walkable(px, new_y):
                self.gm.player.move(0, dy, self.gm)
                self.total_turns += 1
                return True
                
        # Stuck, try any adjacent walkable tile
        for test_dx, test_dy in [(1,0), (-1,0), (0,1), (0,-1)]:
            new_x, new_y = px + test_dx, py + test_dy
            if self.gm.is_walkable(new_x, new_y):
                self.gm.player.move(test_dx, test_dy, self.gm)
                self.total_turns += 1
                return True
                
        return False  # Really stuck
        
    def fight_enemies_in_room(self):
        """Fight all enemies in current room."""
        fights = 0
        while True:
            # Check for adjacent enemies
            adjacent_enemy = None
            px, py = self.gm.player.x, self.gm.player.y
            
            for enemy in self.gm.enemies:
                if not enemy.is_alive:
                    continue
                dist = abs(enemy.x - px) + abs(enemy.y - py)
                if dist <= 1:
                    adjacent_enemy = enemy
                    break
                    
            if not adjacent_enemy:
                break  # No more adjacent enemies
                
            # Fight this enemy
            self.gm.player_attack(adjacent_enemy)
            fights += 1
            self.total_turns += 1
            
            # Enemy counterattack if still alive
            if adjacent_enemy.is_alive:
                adjacent_enemy.attack(self.gm.player, self.gm)
                
            # Heal if needed
            if self.gm.player.hp < self.gm.player.max_hp * 0.3:
                healing_items = [item for item in self.gm.player.inventory 
                               if 'medkit' in item['name'].lower() or 'food' in item['name'].lower()]
                if healing_items:
                    self.gm.player.use_item(healing_items[0], self.gm)
                    self.total_turns += 1
                    
        return fights
        
    def clear_tomb_level(self):
        """Clear current tomb level of enemies and find stairs."""
        turns_start = self.total_turns
        
        # Fight enemies on this level
        enemies_killed = 0
        max_hunt_turns = 50  # Don't spend forever hunting
        hunt_turns = 0
        
        while hunt_turns < max_hunt_turns:
            # Find nearest enemy
            px, py = self.gm.player.x, self.gm.player.y
            nearest_enemy = None
            min_dist = float('inf')
            
            for enemy in self.gm.enemies:
                if not enemy.is_alive:
                    continue
                dist = abs(enemy.x - px) + abs(enemy.y - py)
                if dist < min_dist:
                    min_dist = dist
                    nearest_enemy = enemy
                    
            if not nearest_enemy or min_dist > 20:
                break  # No more nearby enemies
                
            # Move towards enemy
            if min_dist > 1:
                self.move_towards(nearest_enemy.x, nearest_enemy.y)
                hunt_turns += 1
            else:
                # Fight
                self.gm.player_attack(nearest_enemy)
                self.total_turns += 1
                if nearest_enemy.is_alive:
                    nearest_enemy.attack(self.gm.player, self.gm)
                else:
                    enemies_killed += 1
                    
                # Heal if low
                if self.gm.player.hp < self.gm.player.max_hp * 0.4:
                    healing_items = [item for item in self.gm.player.inventory 
                                   if 'medkit' in item['name'].lower() or 'food' in item['name'].lower()]
                    if healing_items:
                        self.gm.player.use_item(healing_items[0], self.gm)
                        self.total_turns += 1
                        
        return self.total_turns - turns_start, enemies_killed
        
    def descend_to_artifact(self):
        """Descend tomb to final level and get artifact."""
        turns_start = self.total_turns
        levels_descended = 0
        total_enemies = 0
        
        # Keep going down until we find artifact
        while self.artifacts_collected < self.tombs_completed + 1:
            # Clear this level
            turns_taken, enemies = self.clear_tomb_level()
            total_enemies += enemies
            
            # Look for artifact on this level
            px, py = self.gm.player.x, self.gm.player.y
            for item in self.gm.items:
                if item['char'] == 'Q':  # Artifact token
                    # Move to it
                    while self.gm.player.x != item['x'] or self.gm.player.y != item['y']:
                        self.move_towards(item['x'], item['y'])
                    # Pick it up
                    self.gm.player_pickup()
                    self.artifacts_collected += 1
                    turns_taken = self.total_turns - turns_start
                    return turns_taken, levels_descended + 1, total_enemies
                    
            # Find down stairs
            down_stairs = None
            for feat in self.gm.features:
                if feat['char'] == '>' and abs(feat['x'] - px) < 30 and abs(feat['y'] - py) < 30:
                    down_stairs = feat
                    break
                    
            if down_stairs:
                # Move to stairs
                while self.gm.player.x != down_stairs['x'] or self.gm.player.y != down_stairs['y']:
                    self.move_towards(down_stairs['x'], down_stairs['y'])
                # Go down
                self.gm.enter_tomb()
                self.total_turns += 1
                levels_descended += 1
            else:
                # Can't find stairs, search more
                for _ in range(10):
                    import random
                    dx = random.choice([-1, 0, 1])
                    dy = random.choice([-1, 0, 1])
                    new_x = px + dx
                    new_y = py + dy
                    if self.gm.is_walkable(new_x, new_y):
                        self.gm.player.move(dx, dy, self.gm)
                        self.total_turns += 1
                        
        return self.total_turns - turns_start, levels_descended, total_enemies
        
    def ascend_to_surface(self):
        """Return to surface from tomb."""
        turns_start = self.total_turns
        levels_ascended = 0
        
        while self.gm.current_biome == 'tomb':
            # Find up stairs
            px, py = self.gm.player.x, self.gm.player.y
            up_stairs = None
            
            for feat in self.gm.features:
                if feat['char'] == '<':
                    up_stairs = feat
                    break
                    
            if up_stairs:
                # Move to stairs
                while self.gm.player.x != up_stairs['x'] or self.gm.player.y != up_stairs['y']:
                    self.move_towards(up_stairs['x'], up_stairs['y'])
                # Go up
                self.gm.exit_tomb()
                self.total_turns += 1
                levels_ascended += 1
            else:
                # Emergency: just teleport out
                self.gm.current_biome = 'crash_site'
                break
                
        return self.total_turns - turns_start, levels_ascended
        
    def run_optimal_simulation(self):
        """Run a complete optimal path simulation."""
        print("\n" + "="*70)
        print("OPTIMAL PATH TO VICTORY SIMULATION")
        print("Tracking shortest viable route through the game")
        print("="*70)
        
        # Initialize game
        start_time = time.time()
        self.gm.initialize()
        self.gm.generate_world()
        self.cleared_tombs = set()
        
        phase_start = self.total_turns
        
        # PHASE 1: Initial setup - skip POIs for speed, head straight to tombs
        print("\n[PHASE 1: INITIAL PREPARATION]")
        print(f"  → Starting position: ({self.gm.player.x}, {self.gm.player.y})")
        print(f"  → Player level: {self.gm.player.level}, HP: {self.gm.player.hp}/{self.gm.player.max_hp}")
        print(f"  → Corruption: {self.gm.player.corruption}")
        print(f"  → Skipping POI exploration for optimal speed")
            
        self.log_phase(
            "Phase 1: Initial Preparation",
            self.total_turns - phase_start,
            f"Ready for tomb raids. Level {self.gm.player.level}, HP {self.gm.player.hp}/{self.gm.player.max_hp}"
        )
        
        # PHASE 2-4: Clear three tombs
        for tomb_num in range(1, 4):
            phase_start = self.total_turns
            
            print(f"\n[PHASE {tomb_num + 1}: TOMB {tomb_num} INFILTRATION]")
            
            # Find nearest tomb
            tomb, dist = self.find_nearest_tomb()
            if not tomb:
                print("  ⚠ No more tombs found!")
                break
                
            print(f"  → Navigating to tomb at ({tomb[0]}, {tomb[1]}), distance: {dist}")
            
            # Navigate to tomb entrance
            travel_start = self.total_turns
            while self.gm.player.x != tomb[0] or self.gm.player.y != tomb[1]:
                self.move_towards(tomb[0], tomb[1])
                # Fight surface enemies if encountered
                self.fight_enemies_in_room()
                
            travel_turns = self.total_turns - travel_start
            print(f"  → Reached tomb entrance in {travel_turns} turns")
            
            # Enter tomb
            self.gm.enter_tomb()
            self.total_turns += 1
            descent_start = self.total_turns
            
            # Descend to artifact
            print(f"  → Descending to artifact...")
            descent_turns, levels, enemies = self.descend_to_artifact()
            print(f"  → Cleared {levels} levels, defeated {enemies} enemies in {descent_turns} turns")
            print(f"  → ARTIFACT ACQUIRED ({self.artifacts_collected}/3)")
            
            # Ascend back to surface
            ascent_start = self.total_turns
            ascent_turns, levels_up = self.ascend_to_surface()
            print(f"  → Returned to surface in {ascent_turns} turns")
            
            # Mark tomb as cleared
            tomb_key = f"tomb_{tomb[0]}_{tomb[1]}"
            self.cleared_tombs.add(tomb_key)
            self.tombs_completed += 1
            
            total_tomb_turns = self.total_turns - phase_start
            self.log_phase(
                f"Phase {tomb_num + 1}: Tomb {tomb_num} Complete",
                total_tomb_turns,
                f"Travel: {travel_turns}t, Descent: {descent_turns}t ({levels} levels, {enemies} kills), Ascent: {ascent_turns}t. Artifacts: {self.artifacts_collected}/3"
            )
            
        # PHASE 5: Return to ship
        phase_start = self.total_turns
        print(f"\n[PHASE 5: RETURN TO SHIP]")
        
        # Find ship location
        ship_pos = None
        for feat in self.gm.features:
            if feat['char'] == 'S':
                ship_pos = (feat['x'], feat['y'])
                break
                
        if ship_pos:
            print(f"  → Navigating to ship at ({ship_pos[0]}, {ship_pos[1]})")
            while self.gm.player.x != ship_pos[0] or self.gm.player.y != ship_pos[1]:
                self.move_towards(ship_pos[0], ship_pos[1])
                self.fight_enemies_in_room()
                
        return_turns = self.total_turns - phase_start
        self.log_phase(
            "Phase 5: Return to Ship",
            return_turns,
            f"Navigated back to extraction point"
        )
        
        # PHASE 6: Power comms terminal
        phase_start = self.total_turns
        print(f"\n[PHASE 6: POWER COMMUNICATIONS]")
        
        # Find comms terminal
        comms_pos = None
        for feat in self.gm.features:
            if feat['char'] == 'C':
                comms_pos = (feat['x'], feat['y'])
                break
                
        if comms_pos:
            print(f"  → Moving to comms terminal at ({comms_pos[0]}, {comms_pos[1]})")
            while self.gm.player.x != comms_pos[0] or self.gm.player.y != comms_pos[1]:
                self.move_towards(comms_pos[0], comms_pos[1])
                
            # Interact with terminal
            print(f"  → Inserting {self.artifacts_collected} Jedi Artifacts into terminal")
            self.gm.interact_comms_terminal()
            self.total_turns += 1
            
        comms_turns = self.total_turns - phase_start
        self.log_phase(
            "Phase 6: Power Communications",
            comms_turns,
            f"Activated comms with {self.artifacts_collected} artifacts. Distress beacon sent!"
        )
        
        # PHASE 7: Final boss fight
        phase_start = self.total_turns
        print(f"\n[PHASE 7: FINAL CONFRONTATION]")
        print(f"  → Player corruption level: {self.gm.player.corruption}")
        
        # Boss should spawn near ship
        boss = None
        for enemy in self.gm.enemies:
            if 'Sith Lord' in enemy.name or 'Jedi Master' in enemy.name:
                boss = enemy
                break
                
        if boss:
            boss_name = boss.name
            print(f"  → {boss_name} has arrived!")
            print(f"  → Boss stats: HP={boss.max_hp}, ATK={boss.attack}, DEF={boss.defense}")
            
            # Move to boss and fight
            fight_turns = 0
            while boss.is_alive and self.gm.player.is_alive:
                # Move towards boss
                px, py = self.gm.player.x, self.gm.player.y
                dist = abs(boss.x - px) + abs(boss.y - py)
                
                if dist > 1:
                    self.move_towards(boss.x, boss.y)
                else:
                    # Attack boss
                    self.gm.player_attack(boss)
                    self.total_turns += 1
                    fight_turns += 1
                    
                    # Boss counterattack
                    if boss.is_alive:
                        boss.attack(self.gm.player, self.gm)
                        
                    # Heal if critical
                    if self.gm.player.hp < self.gm.player.max_hp * 0.3:
                        healing_items = [item for item in self.gm.player.inventory 
                                       if 'medkit' in item['name'].lower() or 'food' in item['name'].lower()]
                        if healing_items:
                            self.gm.player.use_item(healing_items[0], self.gm)
                            self.total_turns += 1
                            
            if boss.is_alive:
                print(f"  ⚠ DEFEAT - Player died in boss fight after {fight_turns} turns")
                final_turns = self.total_turns - phase_start
                self.log_phase(
                    "Phase 7: Final Boss - DEFEAT",
                    final_turns,
                    f"Died fighting {boss_name}. Fight lasted {fight_turns} turns."
                )
                self.print_summary(False, time.time() - start_time)
                return False
            else:
                print(f"  ✓ VICTORY - {boss_name} defeated in {fight_turns} turns!")
                
        final_turns = self.total_turns - phase_start
        self.log_phase(
            "Phase 7: Final Boss - VICTORY",
            final_turns,
            f"Defeated {boss_name if boss else 'final boss'} in {fight_turns} combat turns"
        )
        
        # PHASE 8: Board ship and ending
        phase_start = self.total_turns
        print(f"\n[PHASE 8: EXTRACTION & EPILOGUE]")
        
        # Move to ship if not already there
        if ship_pos:
            while self.gm.player.x != ship_pos[0] or self.gm.player.y != ship_pos[1]:
                self.move_towards(ship_pos[0], ship_pos[1])
                
        print(f"  → Boarding ship...")
        self.gm.victory = True
        self.total_turns += 1
        
        ending_turns = self.total_turns - phase_start
        self.log_phase(
            "Phase 8: Extraction Complete",
            ending_turns,
            f"Boarded ship. Jedi Council ending: {self.get_corruption_tier()}"
        )
        
        self.print_summary(True, time.time() - start_time)
        return True
        
    def get_corruption_tier(self):
        """Get corruption tier name."""
        c = self.gm.player.corruption
        if c <= 20:
            return "Pure Light (0-20)"
        elif c <= 40:
            return "Light (21-40)"
        elif c <= 59:
            return "Balanced (41-59)"
        elif c <= 79:
            return "Dark (60-79)"
        else:
            return "Pure Dark (80-100)"
            
    def print_summary(self, victory, real_time):
        """Print final summary of the run."""
        print("\n" + "="*70)
        print("SIMULATION COMPLETE - FINAL SUMMARY")
        print("="*70)
        print(f"Result: {'✓ VICTORY' if victory else '✗ DEFEAT'}")
        print(f"Total turns: {self.total_turns}")
        print(f"Real time: {real_time:.2f} seconds")
        print(f"Final level: {self.gm.player.level}")
        print(f"Final HP: {self.gm.player.hp}/{self.gm.player.max_hp}")
        print(f"Corruption: {self.gm.player.corruption} ({self.get_corruption_tier()})")
        print(f"Artifacts collected: {self.artifacts_collected}/3")
        print(f"Tombs cleared: {self.tombs_completed}/3")
        
        print(f"\n{'─'*70}")
        print("PHASE BREAKDOWN:")
        print(f"{'─'*70}")
        for phase, data in self.phase_timings.items():
            print(f"\n{phase}:")
            print(f"  Duration: {data['turns']} turns")
            print(f"  Completed at: Turn {data['total_turns']}")
            if data['details']:
                print(f"  {data['details']}")
                
        print(f"\n{'─'*70}")
        print("CRITICAL PATH ANALYSIS:")
        print(f"{'─'*70}")
        
        # Calculate percentages
        if self.total_turns > 0:
            exploration_turns = self.phase_timings.get('Phase 1: Initial Exploration', {}).get('turns', 0)
            tomb_turns = sum(self.phase_timings.get(f'Phase {i}: Tomb {i-1} Complete', {}).get('turns', 0) for i in range(2, 5))
            return_turns = self.phase_timings.get('Phase 5: Return to Ship', {}).get('turns', 0)
            comms_turns = self.phase_timings.get('Phase 6: Power Communications', {}).get('turns', 0)
            boss_turns = max(
                self.phase_timings.get('Phase 7: Final Boss - VICTORY', {}).get('turns', 0),
                self.phase_timings.get('Phase 7: Final Boss - DEFEAT', {}).get('turns', 0)
            )
            extraction_turns = self.phase_timings.get('Phase 8: Extraction Complete', {}).get('turns', 0)
            
            print(f"Initial exploration: {exploration_turns} turns ({exploration_turns/self.total_turns*100:.1f}%)")
            print(f"Three tomb raids: {tomb_turns} turns ({tomb_turns/self.total_turns*100:.1f}%)")
            print(f"Return to ship: {return_turns} turns ({return_turns/self.total_turns*100:.1f}%)")
            print(f"Power comms: {comms_turns} turns ({comms_turns/self.total_turns*100:.1f}%)")
            print(f"Final boss fight: {boss_turns} turns ({boss_turns/self.total_turns*100:.1f}%)")
            print(f"Extraction: {extraction_turns} turns ({extraction_turns/self.total_turns*100:.1f}%)")
            
        print(f"\n{'='*70}")
        print("SHORTEST PATH TO VICTORY ESTIMATE:")
        print(f"{'='*70}")
        print(f"Optimal completion time: {self.total_turns} turns")
        print(f"Average turn duration: ~2-3 seconds")
        print(f"Estimated real-time speedrun: {self.total_turns * 2.5 / 60:.1f} minutes")
        print("="*70 + "\n")


def main():
    """Run the optimal path simulation."""
    print("\n" + "="*70)
    print("JEDI FUGITIVE - OPTIMAL PATH ANALYSIS")
    print("Simulating the shortest viable route to victory")
    print("="*70 + "\n")
    
    sim = OptimalPathSimulator()
    success = sim.run_optimal_simulation()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
