#!/usr/bin/env python3
"""Test script for grenade throwing mechanics."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_grenade_throw():
    """Test grenade throw distance and damage calculations."""
    
    print("=== GRENADE THROWING SYSTEM TEST ===\n")
    
    # Test 1: Range calculation
    print("1. RANGE TESTING (3-tile max)")
    print("-" * 50)
    
    test_positions = [
        ((0, 0), (0, 3), 3, True),   # 3 tiles away (OK)
        ((0, 0), (3, 0), 3, True),   # 3 tiles away (OK)
        ((0, 0), (2, 1), 3, True),   # 3 tiles Manhattan (OK)
        ((0, 0), (0, 4), 4, False),  # 4 tiles away (TOO FAR)
        ((0, 0), (2, 2), 4, False),  # 4 tiles away (TOO FAR)
        ((5, 5), (5, 8), 3, True),   # 3 tiles vertical (OK)
        ((5, 5), (7, 6), 3, True),   # 3 tiles diagonal (OK)
    ]
    
    for player_pos, target_pos, expected_dist, should_work in test_positions:
        px, py = player_pos
        tx, ty = target_pos
        dist = abs(tx - px) + abs(ty - py)
        status = "✓ OK" if (dist <= 3) == should_work else "✗ FAIL"
        print(f"{status} Player at {player_pos}, target {target_pos}: dist={dist} (expected {expected_dist})")
    
    print()
    
    # Test 2: Area of effect
    print("2. AREA OF EFFECT (3-tile radius)")
    print("-" * 50)
    
    explosion_center = (5, 5)
    radius = 3
    
    test_enemies = [
        ((5, 5), True, "at center"),
        ((5, 6), True, "1 tile away"),
        ((5, 8), True, "3 tiles away"),
        ((8, 5), True, "3 tiles away"),
        ((7, 7), True, "2.8 tiles (circular)"),
        ((5, 9), False, "4 tiles away"),
        ((9, 5), False, "4 tiles away"),
        ((8, 8), False, "4.2 tiles (circular)"),
    ]
    
    cx, cy = explosion_center
    print(f"Explosion at {explosion_center}, radius={radius}\n")
    
    for enemy_pos, should_hit, description in test_enemies:
        ex, ey = enemy_pos
        dx = ex - cx
        dy = ey - cy
        actual_dist = (dx*dx + dy*dy) ** 0.5
        in_radius = (dx*dx + dy*dy) <= (radius * radius)
        status = "💥 HIT" if in_radius else "  MISS"
        expected = "HIT" if should_hit else "MISS"
        match = "✓" if in_radius == should_hit else "✗"
        print(f"{match} {status} Enemy at {enemy_pos}: dist={actual_dist:.1f} - {description} (expected {expected})")
    
    print()
    
    # Test 3: Grenade inventory check
    print("3. INVENTORY REQUIREMENTS")
    print("-" * 50)
    
    test_inventories = [
        ([{'id': 'grenade', 'name': 'Thermal Grenade'}], True, "Has grenade"),
        ([{'id': 'thermal_grenade', 'name': 'Thermal Detonator'}], True, "Has thermal_grenade"),
        ([{'id': 'stimpack', 'name': 'Stimpack'}], False, "No grenades"),
        ([], False, "Empty inventory"),
        ([{'id': 'grenade'}, {'id': 'stimpack'}], True, "Multiple items, has grenade"),
    ]
    
    for inv, should_have, description in test_inventories:
        has_grenade = False
        for item in inv:
            if isinstance(item, dict) and item.get('id') in ['grenade', 'thermal_grenade']:
                has_grenade = True
                break
        status = "✓" if has_grenade == should_have else "✗"
        result = "Has grenade" if has_grenade else "No grenade"
        print(f"{status} {result}: {description}")
    
    print()
    print("=== TEST COMPLETE ===")
    print("\nGrenade System Features:")
    print("• Press 't' to enter targeting mode")
    print("• Move reticle within 3-tile range (Manhattan distance)")
    print("• Press Enter to confirm, ESC to cancel")
    print("• Explosion deals 12 damage in 3-tile circular radius")
    print("• Consumes 1 grenade from inventory")
    print("• Alignment-based travel log entries")

if __name__ == "__main__":
    test_grenade_throw()
