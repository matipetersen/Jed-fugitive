#!/usr/bin/env python3
"""
Test reduced memory/atmosphere event frequency.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game import atmosphere

def test_atmosphere_frequency():
    """Test that atmosphere messages are spaced out more."""
    print("Testing atmosphere message frequency...")
    
    # Test that they don't trigger too early
    early_triggers = 0
    for _ in range(100):
        if atmosphere.should_trigger_atmosphere(30, 0):
            early_triggers += 1
    
    if early_triggers > 10:  # Should be very rare at 30 turns
        print(f"❌ FAILED: Too many early triggers ({early_triggers}/100 at 30 turns)")
        return False
    
    print(f"  ✓ Atmosphere messages properly delayed (only {early_triggers}/100 at 30 turns)")
    
    # Test that they do trigger after enough time
    late_triggers = 0
    for _ in range(100):
        if atmosphere.should_trigger_atmosphere(100, 0):
            late_triggers += 1
    
    if late_triggers < 80:  # Should trigger most of the time at 100 turns
        print(f"❌ FAILED: Not enough late triggers ({late_triggers}/100 at 100 turns)")
        return False
    
    print(f"  ✓ Atmosphere messages trigger reliably later ({late_triggers}/100 at 100 turns)")
    print("  ✓ New range: 50-80 turns (was 15-25)")
    return True

def test_memory_frequency():
    """Test that memories are spaced out more."""
    print("\nTesting memory frequency...")
    
    # Test that they don't trigger too early
    early_triggers = 0
    for _ in range(100):
        if atmosphere.should_trigger_memory(80, 0):
            early_triggers += 1
    
    if early_triggers > 5:  # Should be very rare at 80 turns
        print(f"❌ FAILED: Too many early triggers ({early_triggers}/100 at 80 turns)")
        return False
    
    print(f"  ✓ Memories properly delayed (only {early_triggers}/100 at 80 turns)")
    
    # Test that they do trigger after enough time
    late_triggers = 0
    for _ in range(100):
        if atmosphere.should_trigger_memory(300, 0):
            late_triggers += 1
    
    if late_triggers < 90:  # Should trigger almost always at 300 turns
        print(f"❌ FAILED: Not enough late triggers ({late_triggers}/100 at 300 turns)")
        return False
    
    print(f"  ✓ Memories trigger reliably later ({late_triggers}/100 at 300 turns)")
    print("  ✓ New range: 150-250 turns (was 40-60)")
    return True

def test_vision_frequency():
    """Test that visions are spaced out more."""
    print("\nTesting vision frequency...")
    
    # Test that they don't trigger too early
    early_triggers = 0
    for _ in range(100):
        if atmosphere.should_trigger_vision(100, 0):
            early_triggers += 1
    
    if early_triggers > 5:  # Should be very rare at 100 turns
        print(f"❌ FAILED: Too many early triggers ({early_triggers}/100 at 100 turns)")
        return False
    
    print(f"  ✓ Visions properly delayed (only {early_triggers}/100 at 100 turns)")
    
    # Test that they do trigger after enough time
    late_triggers = 0
    for _ in range(100):
        if atmosphere.should_trigger_vision(350, 0):
            late_triggers += 1
    
    if late_triggers < 90:  # Should trigger almost always at 350 turns
        print(f"❌ FAILED: Not enough late triggers ({late_triggers}/100 at 350 turns)")
        return False
    
    print(f"  ✓ Visions trigger reliably later ({late_triggers}/100 at 350 turns)")
    print("  ✓ New range: 200-300 turns (was 50-80)")
    return True

def show_comparison():
    """Show frequency comparison."""
    print("\n" + "=" * 70)
    print("MEMORY/ATMOSPHERE FREQUENCY COMPARISON")
    print("=" * 70)
    
    comparisons = [
        ("Atmosphere Messages", "15-25", "50-80", 3.3),
        ("Jedi Memories", "40-60", "150-250", 4.0),
        ("Force Visions", "50-80", "200-300", 4.0),
    ]
    
    print()
    for event_type, old_range, new_range, multiplier in comparisons:
        print(f"{event_type:25} {old_range:12} → {new_range:12} ({multiplier:.1f}x less frequent)")
    
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print("  • Atmosphere messages: 3.3x less frequent")
    print("  • Memories: 4x less frequent") 
    print("  • Visions: 4x less frequent")
    print("  • Much better spacing between atmospheric events")
    print("=" * 70)

def main():
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + "  MEMORY/ATMOSPHERE FREQUENCY REDUCTION TEST".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    tests = [
        test_atmosphere_frequency,
        test_memory_frequency,
        test_vision_frequency,
    ]
    
    results = []
    for test_func in tests:
        try:
            results.append(test_func())
        except Exception as e:
            print(f"❌ FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    show_comparison()
    
    print()
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed}/{total} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
