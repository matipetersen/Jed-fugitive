#!/usr/bin/env python3
"""Test biome-specific encounters."""
import sys
sys.path.insert(0, '/Users/matiaspetersen/Documents/Spider/ScholarsOf/jedi-fugitive/src')

from jedi_fugitive.game.biome_encounters import (
    BIOME_ENCOUNTERS,
    get_biome_encounter,
    check_encounter_availability,
    get_discovery_text,
    format_encounter_display,
    should_spawn_encounter,
    get_encounter_statistics,
)

def test_biome_coverage():
    """Test that all expected biomes have encounters."""
    print("Testing biome coverage...")
    expected_biomes = ['crash_site', 'forest', 'desert', 'mountain_pass', 'rocky', 'river', 'plains', 'tomb']
    
    for biome in expected_biomes:
        if biome not in BIOME_ENCOUNTERS:
            print(f"❌ Missing biome: {biome}")
            return False
        
        encounters = BIOME_ENCOUNTERS[biome]['encounters']
        if len(encounters) < 3:
            print(f"❌ {biome} has only {len(encounters)} encounters (expected at least 3)")
            return False
    
    print("✅ All 8 biomes have at least 3 encounters each")
    return True

def test_encounter_retrieval():
    """Test getting random encounters from biomes."""
    print("\nTesting encounter retrieval...")
    
    for biome in BIOME_ENCOUNTERS:
        encounter = get_biome_encounter(biome)
        if not encounter:
            print(f"❌ Failed to get encounter from {biome}")
            return False
        
        if 'name' not in encounter or 'description' not in encounter:
            print(f"❌ Encounter in {biome} missing required fields")
            return False
    
    print("✅ All biomes return valid encounters")
    return True

def test_corruption_filtering():
    """Test corruption-based encounter filtering."""
    print("\nTesting corruption filtering...")
    
    # Create a test encounter with specific corruption range
    test_encounter = {
        'name': 'Test',
        'description': ['Test'],
        'corruption_range': (30, 70),
    }
    
    # Should be unavailable at 0 corruption
    if check_encounter_availability(test_encounter, 0):
        print(f"❌ Encounter available at 0 corruption (should require 30-70)")
        return False
    
    # Should be available at 50 corruption
    if not check_encounter_availability(test_encounter, 50):
        print(f"❌ Encounter unavailable at 50 corruption (should be available)")
        return False
    
    # Should be unavailable at 100 corruption
    if check_encounter_availability(test_encounter, 100):
        print(f"❌ Encounter available at 100 corruption (should require 30-70)")
        return False
    
    print("✅ Corruption filtering works correctly")
    return True

def test_discovery_alignment():
    """Test that discovery text changes based on corruption."""
    print("\nTesting alignment-based discovery text...")
    
    test_encounter = {
        'name': 'Test',
        'description': ['Test'],
        'discovery': {
            'light': 'Light side text',
            'balanced': 'Balanced text',
            'dark': 'Dark side text',
        }
    }
    
    # Low corruption = light side
    text = get_discovery_text(test_encounter, 20)
    if text != 'Light side text':
        print(f"❌ Expected light text at 20 corruption, got: {text}")
        return False
    
    # Mid corruption = balanced
    text = get_discovery_text(test_encounter, 50)
    if text != 'Balanced text':
        print(f"❌ Expected balanced text at 50 corruption, got: {text}")
        return False
    
    # High corruption = dark side
    text = get_discovery_text(test_encounter, 80)
    if text != 'Dark side text':
        print(f"❌ Expected dark text at 80 corruption, got: {text}")
        return False
    
    print("✅ Discovery text changes based on alignment")
    return True

def test_encounter_formatting():
    """Test encounter display formatting."""
    print("\nTesting encounter formatting...")
    
    encounter = get_biome_encounter('forest')
    formatted = format_encounter_display('forest', encounter, 50)
    
    if not formatted:
        print("❌ Formatting returned empty result")
        return False
    
    # Check for biome name (case insensitive)
    biome_name_found = any('ANCIENT WOODS' in line.upper() for line in formatted)
    if not biome_name_found:
        print("❌ Formatted text missing biome name")
        print(f"   Lines: {formatted[:5]}")  # Debug: show first 5 lines
        return False
    
    if not any(encounter['name'] in line for line in formatted):
        print("❌ Formatted text missing encounter name")
        return False
    
    print("✅ Encounter formatting works correctly")
    return True

def test_spawn_probabilities():
    """Test encounter spawn probabilities."""
    print("\nTesting spawn probabilities...")
    
    # Test multiple times to get probability distribution
    spawn_counts = {}
    iterations = 1000
    
    for _ in range(iterations):
        for biome in BIOME_ENCOUNTERS:
            if should_spawn_encounter(biome, 50, visited_before=False):
                spawn_counts[biome] = spawn_counts.get(biome, 0) + 1
    
    # Check that crash_site and tomb have higher spawn rates
    if spawn_counts.get('crash_site', 0) < spawn_counts.get('desert', 0):
        print(f"❌ Crash site spawn rate ({spawn_counts.get('crash_site', 0)}) lower than desert ({spawn_counts.get('desert', 0)})")
        print("   Expected crash_site to have higher rate (modifier 1.2)")
        return False
    
    if spawn_counts.get('tomb', 0) < spawn_counts.get('plains', 0):
        print(f"❌ Tomb spawn rate ({spawn_counts.get('tomb', 0)}) lower than plains ({spawn_counts.get('plains', 0)})")
        print("   Expected tomb to have higher rate (modifier 1.5)")
        return False
    
    print("✅ Spawn probabilities favor encounter-rich biomes")
    return True

def test_statistics():
    """Test encounter statistics collection."""
    print("\nTesting statistics...")
    
    stats = get_encounter_statistics()
    
    if stats['total_biomes'] != 8:
        print(f"❌ Expected 8 biomes, found {stats['total_biomes']}")
        return False
    
    if stats['total_encounters'] < 24:  # 8 biomes * 3 encounters minimum
        print(f"❌ Expected at least 24 encounters, found {stats['total_encounters']}")
        return False
    
    print(f"✅ Statistics: {stats['total_encounters']} encounters across {stats['total_biomes']} biomes")
    print(f"   - {stats['with_rewards']} have rewards")
    print(f"   - {stats['with_effects']} have Force effects")
    print(f"   - {stats['with_combat']} trigger combat")
    print(f"   - {stats['with_npcs']} involve NPCs")
    return True

def main():
    print("="*60)
    print("BIOME ENCOUNTERS TEST SUITE".center(60))
    print("="*60)
    
    tests = [
        test_biome_coverage,
        test_encounter_retrieval,
        test_corruption_filtering,
        test_discovery_alignment,
        test_encounter_formatting,
        test_spawn_probabilities,
        test_statistics,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
