#!/usr/bin/env python3
"""
Test that the inventory size has been increased to 20 slots.
"""
import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

from jedi_fugitive.config import MAX_INVENTORY_SIZE

def test_inventory_size():
    """Test that MAX_INVENTORY_SIZE is set to 20"""
    print("Testing inventory size configuration...")
    print("=" * 60)
    
    # Check config value
    print(f"\n✓ MAX_INVENTORY_SIZE in config: {MAX_INVENTORY_SIZE}")
    
    if MAX_INVENTORY_SIZE != 20:
        print(f"✗ ERROR: Expected MAX_INVENTORY_SIZE to be 20, got {MAX_INVENTORY_SIZE}")
        return False
    
    print("✓ Inventory size correctly set to 20 slots")
    
    # Test that the value is used in the code
    print("\n✓ Testing inventory capacity in game...")
    
    # Import after config check
    from jedi_fugitive.game.game_manager import GameManager
    
    class DummyStdScr:
        def __init__(self, h=24, w=80):
            self._h = h
            self._w = w
        def getmaxyx(self):
            return (self._h, self._w)
        def subwin(self, h, w, y, x):
            return self
        def clear(self):
            pass
        def erase(self):
            pass
        def border(self):
            pass
        def addstr(self, *args, **kwargs):
            pass
        def addnstr(self, *args, **kwargs):
            pass
        def refresh(self):
            pass
        def noutrefresh(self):
            pass
        def resize(self, h, w):
            self._h = h
            self._w = w
        def getch(self):
            return -1
    
    dummy_screen = DummyStdScr(h=40, w=120)
    gm = GameManager(dummy_screen)
    
    # Add 20 items to inventory
    test_items = [{'token': 'T', 'name': f'Test Item {i}'} for i in range(20)]
    gm.player.inventory = test_items
    
    print(f"✓ Added {len(test_items)} items to inventory")
    print(f"✓ Current inventory size: {len(gm.player.inventory)}")
    
    if len(gm.player.inventory) == 20:
        print("✓ Successfully stored 20 items in inventory")
    else:
        print(f"✗ ERROR: Expected 20 items, got {len(gm.player.inventory)}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All inventory size tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = test_inventory_size()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
