#!/usr/bin/env python3
"""Test save/load system without running full game."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jedi_fugitive.game.save_manager import SaveManager
from jedi_fugitive.game.player import Player

def test_save_manager():
    """Test SaveManager basic functionality."""
    print("Testing SaveManager...")
    
    # Create save manager
    sm = SaveManager()
    print(f"✓ Save directory: {sm.save_dir}")
    print(f"✓ Save file: {sm.save_file}")
    print(f"✓ Autosave file: {sm.autosave_file}")
    
    # Test has_save
    has_save = sm.has_save()
    has_autosave = sm.has_save(check_autosave=True)
    print(f"✓ Has save: {has_save}")
    print(f"✓ Has autosave: {has_autosave}")
    
    # Test get_save_info
    if has_save:
        info = sm.get_save_info()
        print(f"✓ Save info: {info}")
    
    if has_autosave:
        info = sm.get_save_info(check_autosave=True)
        print(f"✓ Autosave info: {info}")
    
    # Test serialization
    print("\nTesting player serialization...")
    player = Player(5, 10)
    player.hp = 80
    player.max_hp = 100
    player.level = 3
    player.xp = 150
    player.force_alignment = 45
    
    player_data = sm._serialize_player(player)
    print(f"✓ Serialized player: {player_data['hp']}/{player_data['max_hp']} HP, Level {player_data['level']}")
    
    # Test deserialization
    new_player = Player(0, 0)
    sm._deserialize_player(new_player, player_data)
    print(f"✓ Deserialized player: {new_player.hp}/{new_player.max_hp} HP, Level {new_player.level}")
    
    # Verify values match
    assert new_player.x == 5
    assert new_player.y == 10
    assert new_player.hp == 80
    assert new_player.level == 3
    print("✓ All values match!")
    
    print("\n✅ All save manager tests passed!")

if __name__ == "__main__":
    test_save_manager()
