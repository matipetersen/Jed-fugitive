#!/usr/bin/env python3
"""
Audit of all player controls in Jedi Fugitive.
Compares help screen documentation with actual implemented keys.
"""

IMPLEMENTED_KEYS = {
    # Movement (handled by curses)
    'Arrow Keys': 'Cardinal movement (↑↓←→)',
    'hjkl': 'Vi-style cardinal movement',
    'yubn': 'Vi-style diagonal',
    'Numpad': 'Numpad movement',
    
    # Actions
    'g': 'Pick up item',
    'e': 'Equip weapon/armor',
    'u': 'Use/consume item',
    'd': 'Drop item',
    'x': 'Inspect tile',
    'z': 'Unequip weapon',
    'o': 'Unequip armor',
    
    # Combat
    'Walk into enemy': 'Melee attack',
    't': 'Throw grenade (targeting)',
    'F': 'Fire ranged weapon (targeting)',
    
    # Force Abilities
    'f': 'Force powers menu',
    
    # Information
    'j': 'Journal/Travel Log',
    'i': 'Inventory',
    'v': 'Sith Codex (toggle)',
    
    # Crafting & Interaction
    'C': 'Crafting Bench',
    'T': 'Trade with merchant',
    'm': 'Meditate',
    
    # Artifact Interaction
    'a': 'ABSORB artifact (Dark Side)',
    'd': 'DESTROY artifact (Light Side) [conflicts with drop!]',
    'A': 'Absorb POI for power',
    'D': 'Destroy POI for XP',
    
    # System
    '?': 'Help screen',
    'S': 'Save game',
    'r': 'Reveal map (debug)',
    'p': 'Toggle popups',
    'q / ESC': 'Quit game',
}

HELP_SCREEN_CLAIMS = {
    'g': 'Pick up item',
    'e': 'Equip weapon/armor',
    'u': 'Use/consume item',
    'd': 'Drop item',
    'x': 'Inspect tile',
    't': 'Throw grenade',
    'F': 'Fire ranged weapon',
    'f': 'Force powers menu',
    'c': 'Scan/Compass (locate tombs)',  # NOT IMPLEMENTED!
    'j': 'Journal',
    'i': 'Inventory',
    '@': 'Character sheet',  # NOT IMPLEMENTED!
    'v': 'Sith Codex',
    'C': 'Crafting Bench',
    'm': 'Meditate',
    '?': 'Help screen',
    'S': 'Save game',
    'r': 'Reveal map',
    'q / ESC': 'Quit',
}

MISSING_FROM_HELP = {
    'z': 'Unequip weapon',
    'o': 'Unequip armor',
    'T': 'Trade with merchant',
    'p': 'Toggle popups',
    'A': 'Absorb POI',
    'D': 'Destroy POI',
}

NOT_IMPLEMENTED = {
    'c': 'Scan/Compass - mentioned in help but no implementation found',
    '@': 'Character sheet - mentioned in help but no implementation found',
}

CONFLICTS = {
    'd': ['Drop item', 'DESTROY artifact (in artifact menu context)'],
}

print("="*70)
print("JEDI FUGITIVE CONTROL AUDIT")
print("="*70)

print("\n❌ MENTIONED IN HELP BUT NOT IMPLEMENTED:")
for key, desc in NOT_IMPLEMENTED.items():
    print(f"  {key} - {desc}")

print("\n⚠️  IMPLEMENTED BUT NOT IN HELP SCREEN:")
for key, desc in MISSING_FROM_HELP.items():
    print(f"  {key} - {desc}")

print("\n⚠️  KEY CONFLICTS:")
for key, descriptions in CONFLICTS.items():
    print(f"  {key}:")
    for desc in descriptions:
        print(f"    - {desc}")

print("\n✅ RECOMMENDATIONS:")
print("  1. Remove 'c' (Scan/Compass) from help - not implemented")
print("  2. Remove '@' (Character sheet) from help - not implemented")
print("  3. Add 'z' (Unequip weapon) to help")
print("  4. Add 'o' (Unequip armor) to help")
print("  5. Add 'T' (Trade) to help")
print("  6. Add 'p' (Toggle popups) to help OR remove from code")
print("  7. Clarify 'd' context (inventory vs artifact menu)")
print("  8. Add 'A' and 'D' (POI actions) to help")
print("\n" + "="*70)
