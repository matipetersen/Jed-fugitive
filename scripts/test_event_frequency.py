#!/usr/bin/env python3
"""
Test reduced event frequency.
Verifies that narrative events trigger less frequently.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game import narrative_events

def test_new_intervals():
    """Test that new intervals are significantly larger."""
    print("Testing new event intervals...")
    print("=" * 60)
    
    # Check journals
    print("\nJOURNALS:")
    assert narrative_events.should_trigger_narrative_event(100, 'journal') == False
    print("  ✓ Don't trigger at 100 turns")
    assert narrative_events.should_trigger_narrative_event(200, 'journal') == False
    print("  ✓ Don't trigger at 200 turns (minimum)")
    assert narrative_events.should_trigger_narrative_event(300, 'journal') == True
    print("  ✓ Force trigger at 300 turns")
    
    # Check holocrons
    print("\nHOLOCRONS:")
    assert narrative_events.should_trigger_narrative_event(150, 'holocron') == False
    print("  ✓ Don't trigger at 150 turns")
    assert narrative_events.should_trigger_narrative_event(250, 'holocron') == False
    print("  ✓ Don't trigger at 250 turns (minimum)")
    assert narrative_events.should_trigger_narrative_event(350, 'holocron') == True
    print("  ✓ Force trigger at 350 turns")
    
    # Check distress signals
    print("\nDISTRESS SIGNALS:")
    assert narrative_events.should_trigger_narrative_event(200, 'distress') == False
    print("  ✓ Don't trigger at 200 turns")
    assert narrative_events.should_trigger_narrative_event(300, 'distress') == False
    print("  ✓ Don't trigger at 300 turns (minimum)")
    assert narrative_events.should_trigger_narrative_event(400, 'distress') == True
    print("  ✓ Force trigger at 400 turns")
    
    # Check environmental
    print("\nENVIRONMENTAL EVENTS:")
    assert narrative_events.should_trigger_narrative_event(100, 'environmental') == False
    print("  ✓ Don't trigger at 100 turns")
    assert narrative_events.should_trigger_narrative_event(150, 'environmental') == False
    print("  ✓ Don't trigger at 150 turns (minimum)")
    assert narrative_events.should_trigger_narrative_event(250, 'environmental') == True
    print("  ✓ Force trigger at 250 turns")
    
    print("\n" + "=" * 60)
    print("✅ All interval tests passed!")
    return True

def compare_old_vs_new():
    """Show comparison between old and new intervals."""
    print("\n" + "=" * 60)
    print("FREQUENCY COMPARISON (Old → New)")
    print("=" * 60)
    
    comparisons = [
        ("Journals", "80-120", "200-300", 2.5),
        ("Holocrons", "100-150", "250-350", 2.5),
        ("Distress Signals", "150-200", "300-400", 2.0),
        ("Environmental", "60-100", "150-250", 2.5),
        ("Biome Encounters", "200-300", "200-300", 1.0),
    ]
    
    print()
    for event_type, old_range, new_range, multiplier in comparisons:
        print(f"{event_type:20} {old_range:12} → {new_range:12} ({multiplier:.1f}x less frequent)")
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("  • Most events are now 2-2.5x less frequent")
    print("  • Biome encounters unchanged (already spaced well)")
    print("  • Players will see events roughly every 200-400 turns")
    print("  • Much less spam, more impactful when they occur")
    print("=" * 60)

def main():
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + "  EVENT FREQUENCY REDUCTION TEST".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    
    try:
        test_new_intervals()
        compare_old_vs_new()
        
        print("\n✅ Event frequency successfully reduced!")
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
