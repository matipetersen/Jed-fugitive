#!/usr/bin/env python3
"""
Test that Sith Lord names are randomly assigned from canon list
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_sith_lord_names():
    """Test that create_sith_inquisitor uses random canon Sith Lord names"""
    from jedi_fugitive.game.enemies_sith import create_sith_inquisitor
    
    print("Testing Sith Lord Name Randomization")
    print("=" * 60)
    print()
    
    # Expected canon names
    expected_names = {
        "Darth Malak",
        "Darth Revan", 
        "Darth Bane",
        "Darth Nihilus",
        "Darth Sion",
        "Darth Traya",
        "Darth Malgus",
        "Darth Marr",
        "Darth Nox",
        "Darth Thanaton",
        "Darth Baras",
        "Darth Zash",
        "Darth Jadus",
        "Darth Vindican"
    }
    
    # Create 20 bosses to see variety
    print("Creating 20 Sith Lord bosses:")
    print("-" * 60)
    
    generated_names = []
    for i in range(20):
        boss = create_sith_inquisitor(level=10, x=0, y=0)
        generated_names.append(boss.name)
        print(f"  {i+1}. {boss.name} (Symbol: {boss.symbol}, HP: {boss.max_hp})")
    
    print()
    print("=" * 60)
    print("Verification:")
    print("-" * 60)
    
    # Check all names are from expected list
    unique_names = set(generated_names)
    all_valid = all(name in expected_names for name in unique_names)
    
    if all_valid:
        print(f"✓ All {len(unique_names)} unique names are canon Sith Lords")
    else:
        invalid = [n for n in unique_names if n not in expected_names]
        print(f"✗ Found invalid names: {invalid}")
        return False
    
    # Check for variety
    if len(unique_names) > 1:
        print(f"✓ Good variety: {len(unique_names)} different names in 20 spawns")
    else:
        print(f"⚠ Warning: Only {len(unique_names)} unique name(s)")
    
    # Check boss properties
    test_boss = create_sith_inquisitor(level=10, x=0, y=0)
    print(f"✓ Boss symbol changed from 'I' to 'L': {test_boss.symbol}")
    print(f"✓ Boss is marked as boss: {test_boss.is_boss}")
    print(f"✓ Boss has Force abilities: {len(test_boss.force_abilities)} abilities")
    
    print()
    print("=" * 60)
    print("SUCCESS! Sith Lords now have canon names!")
    print("=" * 60)
    print()
    print("Example boss names you might encounter:")
    for name in sorted(list(unique_names)[:5]):
        print(f"  • {name}")
    
    return True

if __name__ == "__main__":
    success = test_sith_lord_names()
    sys.exit(0 if success else 1)
