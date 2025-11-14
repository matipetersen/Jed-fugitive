#!/usr/bin/env python3
"""Simulate game runs to test victory conditions."""

import sys
import os
import random
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game.player import Player
from jedi_fugitive.game.enemy import Enemy, EnemyType
from jedi_fugitive.game.enemies_sith import (
    create_sith_trooper, create_sith_acolyte, create_sith_warrior,
    create_sith_lord
)
from jedi_fugitive.items.weapons import WEAPONS
from jedi_fugitive.items.armor import ARMORS

class SimulationResult:
    def __init__(self):
        self.victories = 0
        self.deaths = 0
        self.death_causes = {}
        self.victory_corruption_levels = []
        self.avg_turns_to_victory = []
        self.avg_level_at_victory = []
        self.boss_defeats = 0
        self.boss_losses = 0
        
    def record_victory(self, turns, level, corruption):
        self.victories += 1
        self.avg_turns_to_victory.append(turns)
        self.avg_level_at_victory.append(level)
        self.victory_corruption_levels.append(corruption)
        
    def record_death(self, cause):
        self.deaths += 1
        self.death_causes[cause] = self.death_causes.get(cause, 0) + 1
        
    def record_boss_fight(self, won):
        if won:
            self.boss_defeats += 1
        else:
            self.boss_losses += 1
    
    def print_summary(self):
        total = self.victories + self.deaths
        print("\n" + "=" * 70)
        print("SIMULATION RESULTS")
        print("=" * 70)
        print(f"Total Runs: {total}")
        print(f"Victories: {self.victories} ({self.victories/total*100:.1f}%)")
        print(f"Deaths: {self.deaths} ({self.deaths/total*100:.1f}%)")
        print()
        
        if self.victories > 0:
            print("VICTORY STATISTICS:")
            print(f"  Average Turns: {sum(self.avg_turns_to_victory)/len(self.avg_turns_to_victory):.1f}")
            print(f"  Average Level: {sum(self.avg_level_at_victory)/len(self.avg_level_at_victory):.1f}")
            print(f"  Average Corruption: {sum(self.victory_corruption_levels)/len(self.victory_corruption_levels):.1f}")
            print(f"  Corruption Range: {min(self.victory_corruption_levels)} - {max(self.victory_corruption_levels)}")
            print()
            
            # Corruption distribution
            pure_light = sum(1 for c in self.victory_corruption_levels if c <= 20)
            light = sum(1 for c in self.victory_corruption_levels if 21 <= c <= 40)
            balanced = sum(1 for c in self.victory_corruption_levels if 41 <= c <= 59)
            dark = sum(1 for c in self.victory_corruption_levels if 60 <= c <= 79)
            pure_dark = sum(1 for c in self.victory_corruption_levels if c >= 80)
            
            print("  Victory Alignment Distribution:")
            print(f"    Pure Light (0-20): {pure_light} ({pure_light/self.victories*100:.1f}%)")
            print(f"    Light (21-40): {light} ({light/self.victories*100:.1f}%)")
            print(f"    Balanced (41-59): {balanced} ({balanced/self.victories*100:.1f}%)")
            print(f"    Dark (60-79): {dark} ({dark/self.victories*100:.1f}%)")
            print(f"    Pure Dark (80-100): {pure_dark} ({pure_dark/self.victories*100:.1f}%)")
            print()
        
        if self.boss_defeats + self.boss_losses > 0:
            print("BOSS FIGHT STATISTICS:")
            total_boss = self.boss_defeats + self.boss_losses
            print(f"  Boss Victories: {self.boss_defeats} ({self.boss_defeats/total_boss*100:.1f}%)")
            print(f"  Boss Defeats: {self.boss_losses} ({self.boss_losses/total_boss*100:.1f}%)")
            print()
        
        if self.death_causes:
            print("DEATH CAUSES:")
            for cause, count in sorted(self.death_causes.items(), key=lambda x: x[1], reverse=True):
                print(f"  {cause}: {count} ({count/self.deaths*100:.1f}%)")
        
        print("=" * 70)

def simulate_combat(player, enemy, max_turns=50):
    """Simulate combat between player and enemy."""
    turns = 0
    while turns < max_turns:
        turns += 1
        
        # Player attacks (with 20% crit chance for 2x damage)
        damage = max(1, player.attack - enemy.defense)
        if random.random() < 0.2:
            damage *= 2  # Critical hit
        enemy.hp -= damage
        
        if enemy.hp <= 0:
            return True, turns  # Player wins
        
        # Enemy attacks (with 10% miss chance)
        if random.random() < 0.1:
            # Miss
            pass
        else:
            damage = max(1, enemy.attack - player.defense)
            player.hp -= damage
        
        if player.hp <= 0:
            return False, turns  # Player loses
    
    # Timeout - consider it a draw/loss
    return False, turns

def simulate_tomb_run(player, tomb_depth=5):
    """Simulate a tomb run and return success/failure."""
    for level in range(1, tomb_depth + 1):
        # Fight 2-4 enemies per level
        num_enemies = random.randint(2, 4)
        for _ in range(num_enemies):
            # Scale enemies to level
            if level <= 2:
                enemy = create_sith_trooper(level=player.level)
            elif level <= 4:
                enemy = create_sith_acolyte(level=player.level + 1)
            else:
                enemy = create_sith_warrior(level=player.level + 2)
            
            won, _ = simulate_combat(player, enemy)
            if not won:
                return False, "tomb_combat"
            
            # Heal after each fight (simulate using healing items)
            player.hp = min(player.max_hp, player.hp + 40)
    
    # Found comms part!
    return True, "found_part"

def simulate_final_boss(player, corruption):
    """Simulate final boss fight."""
    # Create Sith Lord as final boss (both alignments fight Sith)
    boss = create_sith_lord(level=max(5, player.level))
    
    # Scale boss to be challenging but beatable
    boss.max_hp = int(player.max_hp * 1.3)
    boss.hp = boss.max_hp
    boss.attack = int(player.attack * 1.0)  # Equal attack
    boss.defense = max(0, player.defense - 2)  # Slightly lower defense
    
    won, turns = simulate_combat(player, boss, max_turns=100)
    return won, turns

def run_simulation(strategy="balanced", verbose=False):
    """
    Run a single game simulation.
    
    Strategy options:
    - "light": Focus on light side (low corruption)
    - "dark": Focus on dark side (high corruption)
    - "balanced": Mixed approach
    """
    if verbose:
        print(f"\n--- Starting simulation with '{strategy}' strategy ---")
    
    # Create player with boosted starting stats
    player = Player(x=0, y=0)
    
    # Boost starting stats for survivability
    player.max_hp = 100
    player.hp = 100
    player.attack = 8
    player.defense = 5
    
    # Equip starting gear
    try:
        vibroblade = next((w for w in WEAPONS if 'vibroblade' in w.name.lower()), None)
        if vibroblade:
            player.main_weapon = vibroblade
            player.attack += getattr(vibroblade, 'damage', 5)
    except:
        player.attack += 5  # Fallback weapon damage
    
    try:
        shield = next((a for a in ARMORS if 'shield' in a.name.lower()), None)
        if shield:
            player.armor = shield
            player.defense += getattr(shield, 'defense', 2)
    except:
        player.defense += 2  # Fallback armor
    
    # Simulate exploration and leveling
    turns = 0
    tombs_completed = 0
    comms_parts = 0
    
    # Early game: explore and level up
    for _ in range(random.randint(50, 100)):
        turns += 1
        
        # Random encounters
        if random.random() < 0.3:
            enemy = create_sith_trooper(level=player.level)
            won, _ = simulate_combat(player, enemy)
            if not won:
                if verbose:
                    print(f"  Died in early exploration at turn {turns}")
                return "death", "early_combat", turns, player.level, player.dark_corruption
            
            # Gain XP and level up more frequently
            player.hp = min(player.max_hp, player.hp + 20)
            if random.random() < 0.4:  # Higher level up chance
                player.level_up()
                player.hp = player.max_hp
                player.attack += 2
                player.defense += 1
                if verbose:
                    print(f"  Level up! Now level {player.level}")
        
        # Adjust corruption based on strategy
        if strategy == "dark" and random.random() < 0.1:
            player.dark_corruption = min(100, player.dark_corruption + random.randint(5, 10))
        elif strategy == "light" and random.random() < 0.1:
            player.dark_corruption = max(0, player.dark_corruption - random.randint(3, 7))
    
    # Mid game: tomb runs (need 3 comms parts from 3 tombs)
    for tomb_num in range(3):
        if verbose:
            print(f"  Entering tomb #{tomb_num + 1}")
        
        success, result = simulate_tomb_run(player, tomb_depth=random.randint(3, 5))
        if not success:
            if verbose:
                print(f"  Died in tomb #{tomb_num + 1}")
            return "death", result, turns, player.level, player.dark_corruption
        
        tombs_completed += 1
        comms_parts += 1
        turns += random.randint(20, 40)
        
        # Heal and level after tomb
        player.hp = player.max_hp
        player.level_up()  # Always level up after tomb
        player.attack += 3
        player.defense += 2
        if verbose:
            print(f"  Completed tomb #{tomb_num + 1}, level {player.level}")
    
    if verbose:
        print(f"  Collected {comms_parts} comms parts!")
    
    # Late game: activate comms and face final boss
    turns += 10
    
    if verbose:
        print(f"  Comms activated! Corruption: {player.dark_corruption}")
    
    # Final boss fight
    won, boss_turns = simulate_final_boss(player, player.dark_corruption)
    turns += boss_turns
    
    if won:
        if verbose:
            print(f"  VICTORY! Defeated final boss in {boss_turns} turns")
        return "victory", "final_boss_defeated", turns, player.level, player.dark_corruption
    else:
        if verbose:
            print(f"  Defeated by final boss")
        return "death", "final_boss", turns, player.level, player.dark_corruption

def main():
    """Run multiple simulations."""
    num_simulations = 100
    
    print("=" * 70)
    print("JEDI FUGITIVE - VICTORY SIMULATION")
    print("=" * 70)
    print(f"Running {num_simulations} simulations...")
    print()
    
    result = SimulationResult()
    
    # Run simulations with different strategies
    strategies = ["light", "balanced", "dark"]
    sims_per_strategy = num_simulations // len(strategies)
    
    for i in range(num_simulations):
        strategy = strategies[i % len(strategies)]
        
        outcome, cause, turns, level, corruption = run_simulation(strategy, verbose=False)
        
        if outcome == "victory":
            result.record_victory(turns, level, corruption)
            if cause == "final_boss_defeated":
                result.record_boss_fight(won=True)
        else:
            result.record_death(cause)
            if cause == "final_boss":
                result.record_boss_fight(won=False)
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  Completed {i + 1}/{num_simulations} simulations...")
    
    # Print results
    result.print_summary()
    
    # Analysis
    print("\nANALYSIS:")
    win_rate = result.victories / (result.victories + result.deaths) * 100
    
    if win_rate >= 50:
        print("✓ Victory is ACHIEVABLE - game is balanced for success")
    elif win_rate >= 25:
        print("⚠ Victory is DIFFICULT but possible - challenging game")
    elif win_rate >= 10:
        print("⚠ Victory is RARE - very difficult game")
    else:
        print("✗ Victory is NEARLY IMPOSSIBLE - game may be too hard")
    
    print()
    print("RECOMMENDATIONS:")
    if result.boss_defeats > 0 and result.boss_defeats < result.boss_losses:
        print("  - Final boss may be too strong, consider reducing HP/attack")
    if "tomb_combat" in result.death_causes and result.death_causes["tomb_combat"] > result.victories:
        print("  - Tomb enemies may be too difficult, consider scaling")
    if result.victories > 0:
        avg_level = sum(result.avg_level_at_victory) / len(result.avg_level_at_victory)
        if avg_level < 5:
            print("  - Players can win at lower levels - good progression")
        elif avg_level > 10:
            print("  - Players need high levels to win - consider more XP/easier leveling")

if __name__ == "__main__":
    main()
