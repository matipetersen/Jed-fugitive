#!/usr/bin/env python3
"""Test items_on_map initialization fix."""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

def test_items_on_map_initialization():
    """Test that items_on_map is properly initialized."""
    print("="*60)
    print("TESTING ITEMS_ON_MAP INITIALIZATION")
    print("="*60)
    
    try:
        print("\n1. Creating mock stdscr...")
        class DummyStdScr:
            def __init__(self, h=24, w=80):
                self._h = h; self._w = w
            def getmaxyx(self): return (self._h, self._w)
            def subwin(self, h, w, y, x): return self
            def clear(self): pass
            def erase(self): pass
            def border(self): pass
            def addstr(self, *args, **kwargs): pass
            def addnstr(self, *args, **kwargs): pass
            def refresh(self): pass
            def noutrefresh(self): pass
            def resize(self, h, w): self._h = h; self._w = w
            def mvwin(self, y, x): pass
            def move(self, y, x): pass
            def clrtoeol(self): pass
            def getch(self): return -1
        
        dummy = DummyStdScr()
        print("   ✓ Mock stdscr created")
        
        print("\n2. Importing GameManager...")
        from jedi_fugitive.game.game_manager import GameManager
        print("   ✓ GameManager imported")
        
        print("\n3. Creating GameManager instance...")
        gm = GameManager(dummy)
        print("   ✓ GameManager instance created")
        
        print("\n4. Checking items_on_map attribute...")
        if hasattr(gm, 'items_on_map'):
            print("   ✓ items_on_map attribute exists")
        else:
            print("   ✗ items_on_map attribute missing!")
            return False
        
        print("\n5. Checking items_on_map type...")
        if isinstance(gm.items_on_map, list):
            print("   ✓ items_on_map is a list")
        else:
            print(f"   ✗ items_on_map is {type(gm.items_on_map)}, expected list")
            return False
        
        print("\n6. Checking items_on_map initial value...")
        if gm.items_on_map == []:
            print("   ✓ items_on_map initialized to empty list")
        else:
            print(f"   ✗ items_on_map is {gm.items_on_map}, expected []")
            return False
        
        print("\n7. Testing append operation...")
        gm.items_on_map.append({'x': 10, 'y': 20, 'name': 'test_item'})
        if len(gm.items_on_map) == 1:
            print("   ✓ Append operation successful")
        else:
            print("   ✗ Append operation failed")
            return False
        
        print("\n8. Testing remove operation...")
        item = gm.items_on_map[0]
        gm.items_on_map.remove(item)
        if len(gm.items_on_map) == 0:
            print("   ✓ Remove operation successful")
        else:
            print("   ✗ Remove operation failed")
            return False
        
        print("\n9. Testing list comprehension...")
        gm.items_on_map = [
            {'x': 10, 'y': 20},
            {'x': 30, 'y': 40},
            {'x': 50, 'y': 60}
        ]
        gm.items_on_map = [it for it in gm.items_on_map if it.get('x') != 30]
        if len(gm.items_on_map) == 2:
            print("   ✓ List comprehension successful")
        else:
            print(f"   ✗ List comprehension failed: {len(gm.items_on_map)} items")
            return False
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
        print("\nitems_on_map is now properly initialized in GameManager.__init__")
        print("This prevents 'GameManager has no attribute items_on_map' errors.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_items_on_map_initialization()
    sys.exit(0 if success else 1)
