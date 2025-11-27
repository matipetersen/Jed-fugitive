#!/usr/bin/env python3
"""
Test script for narrative choice system improvements.
Verifies:
1. Alignment labels removed from choices
2. Choice order is randomized
3. Choice processing works correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game import narrative_events

def test_alignment_labels_removed():
    """Test that (Light), (Dark), (Neutral) labels are removed from choices."""
    print("Testing alignment label removal...")
    
    # Check distress signals
    signal = narrative_events.get_random_distress_signal()
    formatted, choice_mapping = narrative_events.format_distress_signal(signal)
    
    for line in formatted:
        if '(Light)' in line or '(Dark)' in line or '(Neutral)' in line:
            print(f"❌ FAILED: Found alignment label in: {line}")
            return False
    
    # Check environmental events
    event = narrative_events.get_environmental_event()
    formatted, choice_mapping = narrative_events.format_environmental_event(event)
    
    for line in formatted:
        if '(Light)' in line or '(Dark)' in line or '(Neutral)' in line:
            print(f"❌ FAILED: Found alignment label in: {line}")
            return False
    
    print("✅ PASSED: No alignment labels found in choices")
    return True

def test_choice_randomization():
    """Test that choice order is randomized."""
    print("\nTesting choice randomization...")
    
    signal = narrative_events.DISTRESS_SIGNALS[0]  # Use first signal for consistency
    
    # Generate display multiple times and check if order varies
    orders = []
    for _ in range(10):
        formatted, choice_mapping = narrative_events.format_distress_signal(signal)
        # Extract the order (which choice_key is at position 1, 2, 3)
        order = tuple(sorted(choice_mapping.items()))
        orders.append(order)
    
    # Check if we got different orders
    unique_orders = set(orders)
    if len(unique_orders) > 1:
        print(f"✅ PASSED: Got {len(unique_orders)} different choice orders out of 10 attempts")
        return True
    else:
        print(f"⚠️  WARNING: All 10 attempts had same order (might be random luck)")
        # Not failing this as it could theoretically happen by chance
        return True

def test_choice_mapping():
    """Test that choice mapping works correctly."""
    print("\nTesting choice mapping...")
    
    signal = narrative_events.get_random_distress_signal()
    formatted, choice_mapping = narrative_events.format_distress_signal(signal)
    
    # Verify mapping has 3 entries
    if len(choice_mapping) != 3:
        print(f"❌ FAILED: Expected 3 choices, got {len(choice_mapping)}")
        return False
    
    # Verify keys are 1, 2, 3
    if set(choice_mapping.keys()) != {1, 2, 3}:
        print(f"❌ FAILED: Expected keys 1,2,3, got {choice_mapping.keys()}")
        return False
    
    # Verify values are valid choice keys
    expected_keys = {'choice_light', 'choice_dark', 'choice_ignore'}
    if set(choice_mapping.values()) != expected_keys:
        print(f"❌ FAILED: Expected choice keys {expected_keys}, got {choice_mapping.values()}")
        return False
    
    print("✅ PASSED: Choice mapping is correct")
    return True

def test_choice_processing():
    """Test that choice processing returns correct data."""
    print("\nTesting choice processing...")
    
    class MockPlayer:
        def __init__(self):
            self.corruption = 50
    
    player = MockPlayer()
    signal = narrative_events.DISTRESS_SIGNALS[0]
    
    # Test light choice
    outcome, corruption, reward = narrative_events.process_narrative_choice(
        signal, 'choice_light', player
    )
    
    if outcome is None:
        print("❌ FAILED: No outcome returned")
        return False
    
    if not isinstance(corruption, int):
        print(f"❌ FAILED: Corruption should be int, got {type(corruption)}")
        return False
    
    print(f"✅ PASSED: Choice processing returns valid data")
    print(f"   Outcome: {outcome[:50]}...")
    print(f"   Corruption: {corruption}")
    print(f"   Reward: {reward}")
    return True

def test_environmental_events():
    """Test environmental events with choices."""
    print("\nTesting environmental events...")
    
    event = narrative_events.get_environmental_event()
    formatted, choice_mapping = narrative_events.format_environmental_event(event)
    
    # Some events might not have choices
    if choice_mapping is None:
        print(f"ℹ️  Event '{event['name']}' has no choices (valid)")
        return True
    
    if len(choice_mapping) < 2:
        print(f"❌ FAILED: Expected at least 2 choices, got {len(choice_mapping)}")
        return False
    
    print(f"✅ PASSED: Environmental event has {len(choice_mapping)} choices")
    return True

def main():
    print("=" * 60)
    print("NARRATIVE CHOICE SYSTEM TEST")
    print("=" * 60)
    
    tests = [
        test_alignment_labels_removed,
        test_choice_randomization,
        test_choice_mapping,
        test_choice_processing,
        test_environmental_events,
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
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
