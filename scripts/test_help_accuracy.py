#!/usr/bin/env python3
"""
Test that all controls mentioned in help screen are actually implemented.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def extract_keys_from_help():
    """Extract all key bindings mentioned in help screen."""
    from jedi_fugitive.game import input_handler
    
    # Read the source file to get help text
    with open(os.path.join(os.path.dirname(__file__), '..', 'src', 'jedi_fugitive', 'game', 'input_handler.py'), 'r') as f:
        content = f.read()
    
    # Find help_lines definition
    help_start = content.find('help_lines = [')
    help_end = content.find('Press any key to close..."', help_start) + 30
    help_section = content[help_start:help_end]
    
    # Extract single-letter keys
    import re
    keys = set()
    
    # Pattern: "  X =" where X is the key
    pattern = r'"  ([a-zA-Z?@]) = '
    matches = re.findall(pattern, help_section)
    keys.update(matches)
    
    # Special keys
    if 'Arrow Keys' in help_section:
        keys.add('arrows')
    if 'hjkl' in help_section:
        keys.add('hjkl')
    if 'ESC' in help_section or 'q ' in help_section:
        keys.add('q')
    
    return keys

def check_implementation(key):
    """Check if a key is implemented in input_handler.py."""
    with open(os.path.join(os.path.dirname(__file__), '..', 'src', 'jedi_fugitive', 'game', 'input_handler.py'), 'r') as f:
        content = f.read()
    
    if key == 'arrows' or key == 'hjkl' or key == 'q':
        return True  # Handled by curses/special cases
    
    # Check for key implementation
    patterns = [
        f"if key == ord('{key}')",
        f"if key == ord('{key.upper()}')",
        f"if key == ord('{key.lower()}')",
    ]
    
    for pattern in patterns:
        if pattern in content:
            return True
    
    return False

def main():
    print("="*70)
    print("HELP SCREEN ACCURACY TEST")
    print("="*70)
    
    print("\nExtracting keys from help screen...")
    help_keys = extract_keys_from_help()
    
    print(f"Found {len(help_keys)} key bindings in help screen:")
    for key in sorted(help_keys):
        print(f"  {key}")
    
    print("\nChecking implementation...")
    not_implemented = []
    implemented = []
    
    for key in sorted(help_keys):
        if check_implementation(key):
            implemented.append(key)
            print(f"  ✓ {key} - implemented")
        else:
            not_implemented.append(key)
            print(f"  ✗ {key} - NOT FOUND")
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"✓ Implemented: {len(implemented)}/{len(help_keys)}")
    print(f"✗ Not found: {len(not_implemented)}/{len(help_keys)}")
    
    if not_implemented:
        print("\n⚠️  Keys mentioned in help but not implemented:")
        for key in not_implemented:
            print(f"  - {key}")
        return 1
    else:
        print("\n🎉 All help screen keys are implemented!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
