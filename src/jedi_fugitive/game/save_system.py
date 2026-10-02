from jedi_fugitive.game import logger as game_logger
log = getattr(game_logger, 'get_logger', lambda name=None: None)("save_system")
"""Save and load game state system."""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


def get_save_directory() -> Path:
    """Get the save directory path, creating it if needed."""
    # Use user's home directory for cross-platform compatibility
    # (JEDI_FUGITIVE_SAVE_DIR overrides it: tests, portable installs, the web build's
    # persistent storage mount)
    if os.environ.get('JEDI_FUGITIVE_SAVE_DIR'):
        save_dir = Path(os.environ['JEDI_FUGITIVE_SAVE_DIR'])
    elif os.name == 'nt':  # Windows
        save_dir = Path(os.environ.get('APPDATA', '~')) / 'DarkMeridian' / 'saves'
    else:  # Mac/Linux
        save_dir = Path.home() / '.dark_meridian' / 'saves'
    
    save_dir.mkdir(parents=True, exist_ok=True)
    return save_dir


def get_autosave_path() -> Path:
    """Get the autosave file path."""
    return get_save_directory() / 'autosave.json'


def get_manual_save_path(slot: int = 1) -> Path:
    """Get a manual save slot path."""
    return get_save_directory() / f'save_slot_{slot}.json'


def _is_json_serializable(obj) -> bool:
    """Check if an object is JSON serializable."""
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError) as e:
        if log:
            log.exception("Object not JSON serializable", exc_info=e)
        return False


def _serialize_value(val):
    """Convert a value to a JSON-serializable format."""
    if val is None:
        return None
    
    # Handle basic types
    if isinstance(val, (int, float, str, bool)):
        return val
    
    # Handle lists and tuples
    if isinstance(val, (list, tuple)):
        return [_serialize_value(v) for v in val]
    
    # Handle dicts
    if isinstance(val, dict):
        return {k: _serialize_value(v) for k, v in val.items()}
    
    # Handle enums (like HandRequirement)
    if hasattr(val, 'value'):
        return val.value
    
    # Handle enums with name attribute
    if hasattr(val, 'name') and isinstance(val.name, str):
        return val.name
    
    # Try to convert to string as last resort
    try:
        return str(val)
    except Exception:
        return None


def _serialize_item(item) -> Optional[Dict[str, Any]]:
    """Convert an item object to a serializable dictionary."""
    if item is None:
        return None
    
    if isinstance(item, dict):
        # Still need to serialize dict values that might not be JSON-safe
        safe_dict = {}
        for k, v in item.items():
            serialized = _serialize_value(v)
            if serialized is not None or v is None:
                safe_dict[k] = serialized
        return safe_dict
    
    try:
        item_data = {
            'name': str(getattr(item, 'name', 'Unknown')),
            'type': type(item).__name__,
        }
        
        # Try to capture common item attributes
        for attr in ['damage', 'defense', 'evasion_bonus', 'accuracy_bonus', 
                     'value', 'description', 'quantity', 'slot', 'hands',
                     'damage_bonus', 'defense_bonus', 'range', 'weapon_type']:
            if hasattr(item, attr):
                val = getattr(item, attr)
                serialized = _serialize_value(val)
                if serialized is not None or val is None:
                    item_data[attr] = serialized
        
        return item_data
    except Exception as e:
        # Fallback to minimal data
        try:
            return {
                'name': str(item) if hasattr(item, '__str__') else 'Unknown',
                'type': type(item).__name__
            }
        except Exception:
            return {'name': 'Unknown', 'type': 'Unknown'}


def _pos_key(k):
    return f"{k[0]},{k[1]}" if isinstance(k, (tuple, list)) else str(k)


def _pos_from_key(k):
    try:
        x, y = str(k).split(',')
        return (int(x), int(y))
    except Exception:
        return k


def _mastery_to_dict(player):
    from jedi_fugitive.game import languages, jedi_skills, tech
    languages.ensure_state(player)
    jedi_skills.ensure_state(player)
    tech.ensure_state(player)
    return {
        'skills': dict(player.skills),
        'skill_points': player.skill_points,
        'tech': dict(player.tech),
        'lexicon': {lid: {'known': sorted(st['known']), 'seen': dict(st['seen'])}
                    for lid, st in player.lexicon.items()},
        'inscriptions': {_pos_key(k): v for k, v in player.inscriptions.items()},
        'translated_entries': [_pos_key(k) for k in player.translated_entries],
        'study_counts': {_pos_key(k): v for k, v in player.study_counts.items()},
    }


def _mastery_from_dict(player, data):
    if not data:
        return
    from jedi_fugitive.game import languages, jedi_skills, tech
    languages.ensure_state(player)
    jedi_skills.ensure_state(player)
    tech.ensure_state(player)
    player.skills = dict(data.get('skills', {}))
    player.skill_points = int(data.get('skill_points', 0))
    player.tech = dict(data.get('tech', {}))
    for lid, st in (data.get('lexicon') or {}).items():
        if lid in player.lexicon:
            player.lexicon[lid]['known'] = set(st.get('known', []))
            player.lexicon[lid]['seen'] = dict(st.get('seen', {}))
    player.inscriptions = {_pos_from_key(k): v for k, v in (data.get('inscriptions') or {}).items()}
    player.translated_entries = {_pos_from_key(k) for k in data.get('translated_entries', [])}
    player.study_counts = {_pos_from_key(k): v for k, v in (data.get('study_counts') or {}).items()}
    jedi_skills.mark_applied(player)
    tech.mark_applied(player)


def _serialize_game_state_v1(game) -> Dict[str, Any]:
    """Legacy (v1) save: a hand-picked subset of player fields. Kept to read old saves."""
    try:
        # Player state
        player_data = {
            'x': getattr(game.player, 'x', 0),
            'y': getattr(game.player, 'y', 0),
            'hp': getattr(game.player, 'hp', 10),
            'max_hp': getattr(game.player, 'max_hp', 10),
            'attack': getattr(game.player, 'attack', 10),
            'defense': getattr(game.player, 'defense', 5),
            'evasion': getattr(game.player, 'evasion', 10),
            'accuracy': getattr(game.player, 'accuracy', 80),
            'stress': getattr(game.player, 'stress', 0),
            'max_stress': getattr(game.player, 'max_stress', 100),
            'level': getattr(game.player, 'level', 1),
            'xp': getattr(game.player, 'xp', 0),
            'xp_to_next': getattr(game.player, 'xp_to_next', 100),
            'light_xp': getattr(game.player, 'light_xp', 0),
            'dark_xp': getattr(game.player, 'dark_xp', 0),
            'light_level': getattr(game.player, 'light_level', 1),
            'dark_level': getattr(game.player, 'dark_level', 1),
            'dark_corruption': getattr(game.player, 'dark_corruption', 0),
            'alignment_score': getattr(game.player, 'alignment_score', 50),
            'force_energy': getattr(game.player, 'force_energy', 100),
            'max_force_energy': getattr(game.player, 'max_force_energy', 100),
            'force_points': getattr(game.player, 'force_points', 2),
            'kills_count': getattr(game.player, 'kills_count', 0),
            'tombs_explored': getattr(game.player, 'tombs_explored', 0),
            'artifacts_consumed': getattr(game.player, 'artifacts_consumed', 0),
            'gold_collected': getattr(game.player, 'gold_collected', 0),
            '_stress_system_active': getattr(game.player, '_stress_system_active', False),
            'facing': list(getattr(game.player, 'facing', (1, 0))),  # Convert tuple to list for JSON
            'melee_mastery': getattr(game.player, 'melee_mastery', 0),
            'ranged_mastery': getattr(game.player, 'ranged_mastery', 0),
            'shield_mastery': getattr(game.player, 'shield_mastery', 0),
            'dual_wield_mastery': getattr(game.player, 'dual_wield_mastery', 0),
            # saved accuracy/evasion include wound penalties, so the wounds must travel with them
            'wounds': dict(getattr(game.player, 'wounds', {}) or {}),
            'lord_fragments': {k: sorted(v) for k, v in (getattr(game.player, 'lord_fragments', {}) or {}).items()},
            'lord_masteries': sorted(getattr(game.player, 'lord_masteries', set()) or set()),
        }
        
        # Inventory - serialize each item properly
        inventory = []
        for item in getattr(game.player, 'inventory', []):
            serialized = _serialize_item(item)
            if serialized:
                inventory.append(serialized)
        player_data['inventory'] = inventory
        
        # Equipped items
        player_data['equipped_weapon'] = _serialize_item(getattr(game.player, 'equipped_weapon', None))
        player_data['equipped_armor'] = _serialize_item(getattr(game.player, 'equipped_armor', None))
        player_data['offhand'] = _serialize_item(getattr(game.player, 'offhand', None))
        
        # Travel log - ensure it's a list of strings
        travel_log = getattr(game.player, 'travel_log', [])
        player_data['travel_log'] = [str(entry) for entry in travel_log]
        
        # Mastery systems: skills, languages, technology
        try:
            player_data_mastery = _mastery_to_dict(game.player)
        except Exception:
            player_data_mastery = {}

        # Game state
        game_data = {
            'turn_count': getattr(game, 'turn_count', 0),
            'current_biome': getattr(game, 'current_biome', 'crash_site'),
            'in_tomb': getattr(game, 'in_tomb', False),
            'tomb_floor': getattr(game, 'tomb_floor', 0),
            'has_codex': getattr(game, 'has_codex', False),
            'has_artifact': getattr(game, 'has_artifact', False),
            'victory': getattr(game, 'victory', False),
        }
        
        # Combine everything
        save_data = {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'player': player_data,
            'mastery': player_data_mastery,
            'game': game_data,
        }
        
        return save_data
    
    except Exception as e:
        print(f"Error serializing game state: {e}")
        return {}


def save_game(game, path: Optional[Path] = None, is_autosave: bool = True) -> bool:
    """Save the game state to a file."""
    try:
        if path is None:
            path = get_autosave_path() if is_autosave else get_manual_save_path()
        
        save_data = serialize_game_state(game)
        if not save_data:
            return False
        
        # Test that the data is actually JSON serializable before writing
        try:
            json.dumps(save_data)
        except (TypeError, ValueError) as e:
            print(f"Save data is not JSON serializable: {e}")
            try:
                if hasattr(game, 'ui') and hasattr(game.ui, 'messages'):
                    game.ui.messages.add(f"Save failed: Data not serializable")
            except Exception:
                pass
            return False
        
        # Write to file
        with open(path, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        # Notify user
        if not is_autosave:
            try:
                if hasattr(game, 'ui') and hasattr(game.ui, 'messages'):
                    game.ui.messages.add(f"Game saved to {path.name}")
            except Exception:
                pass
        
        return True
    
    except Exception as e:
        import traceback
        print(f"Error saving game: {e}")
        print(traceback.format_exc())
        try:
            if hasattr(game, 'ui') and hasattr(game.ui, 'messages'):
                game.ui.messages.add(f"Save failed - check console")
        except Exception:
            pass
        return False


def load_game(path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Load game state from a file."""
    try:
        if path is None:
            path = get_autosave_path()
        
        if not path.exists():
            return None
        
        with open(path, 'r') as f:
            save_data = json.load(f)
        
        return save_data
    
    except Exception as e:
        print(f"Error loading game: {e}")
        return None


def _apply_save_data_v1(game, save_data: Dict[str, Any]) -> bool:
    """Apply a legacy (v1) save: player fields only."""
    try:
        if not save_data:
            return False
        
        player_data = save_data.get('player', {})
        game_data = save_data.get('game', {})
        
        # Restore player state
        for key, value in player_data.items():
            if key not in ['inventory', 'equipped_weapon', 'equipped_armor', 'travel_log', 'facing', 'offhand']:
                setattr(game.player, key, value)
        
        game.player.lord_fragments = {k: set(v) for k, v in (player_data.get('lord_fragments') or {}).items()}
        game.player.lord_masteries = set(player_data.get('lord_masteries') or [])
        game.player.wounds = dict(player_data.get('wounds') or {})
        game._last_hp_seen = getattr(game.player, 'hp', None)

        # Restore facing tuple
        if 'facing' in player_data:
            facing = player_data['facing']
            if isinstance(facing, list):
                game.player.facing = tuple(facing)
            else:
                game.player.facing = facing
        
        # Restore travel log
        if 'travel_log' in player_data:
            game.player.travel_log = player_data['travel_log']
        
        # Restore mastery systems (skills, languages, technology)
        try:
            _mastery_from_dict(game.player, save_data.get('mastery') or {})
        except Exception as e:
            print(f"Could not restore mastery data: {e}")

        # Restore game state
        for key, value in game_data.items():
            setattr(game, key, value)
        
        # Note: Full inventory/equipment restoration would need item reconstruction
        # For now, this saves core progress - items can be re-obtained
        
        return True
    
    except Exception as e:
        print(f"Error applying save data: {e}")
        return False


def list_saves() -> list:
    """List all available save files."""
    try:
        save_dir = get_save_directory()
        saves = []
        
        # Check autosave
        autosave = get_autosave_path()
        if autosave.exists():
            try:
                with open(autosave, 'r') as f:
                    data = json.load(f)
                saves.append({
                    'name': 'Autosave',
                    'path': autosave,
                    'timestamp': data.get('timestamp', 'Unknown'),
                    'level': data.get('player', {}).get('level', 1),
                    'turn': data.get('game', {}).get('turn_count', 0),
                })
            except Exception:
                pass
        
        # Check manual saves
        for i in range(1, 4):  # Support 3 manual save slots
            save_path = get_manual_save_path(i)
            if save_path.exists():
                try:
                    with open(save_path, 'r') as f:
                        data = json.load(f)
                    saves.append({
                        'name': f'Save Slot {i}',
                        'path': save_path,
                        'timestamp': data.get('timestamp', 'Unknown'),
                        'level': data.get('player', {}).get('level', 1),
                        'turn': data.get('game', {}).get('turn_count', 0),
                    })
                except Exception:
                    pass
        
        return saves
    
    except Exception as e:
        print(f"Error listing saves: {e}")
        return []


# --------------------------------------------------------------------------- v2
# A v2 save holds the world seed (the surface is regenerated identically from
# it), the current surface map, and the whole object graph of the player and
# of every system that carries progress, encoded by save_codec in one pass so
# shared references (quest <-> NPC <-> player, faction manager) survive.

SAVE_VERSION = '2.0'

# GameManager attributes that carry progress (everything else is regenerated)
GAME_STATE_ATTRS = (
    'turn_count', 'turns', 'artifacts_collected', 'artifacts_needed', 'comms_established',
    'explored', 'items_on_map', 'map_landmarks', 'map_lore', 'merchants', 'npcs_on_map',
    'quest_manager', 'faction_manager', 'pursuit_system', 'tomb_records', 'loot_caches',
    'current_biome', 'last_respawn_turn', 'used_holocrons', 'last_holocron_turn',
    '_handled_breaking_point', 'final_boss_spawned', 'completed_special_dungeons',
)
# links into the running session or into enemies that are regenerated on load
_SKIP = {'game', 'ui', 'stdscr', 'gfx', 'messages', '_cached_stats',
         'last_attacking_enemy', 'predator', 'stealth_system'}


def _surface_view(game):
    """(map, items, player position) of the surface, even when saved inside a tomb."""
    in_tomb = bool(getattr(game, 'tomb_levels', None)) and getattr(game, 'surface_map', None) is not None
    if in_tomb:
        return (game.surface_map, list(getattr(game, 'surface_items_on_map', []) or []),
                tuple(getattr(game, 'surface_player_pos', (game.player.x, game.player.y))), True)
    return game.game_map, list(getattr(game, 'items_on_map', []) or []), (game.player.x, game.player.y), False


def serialize_game_state(game) -> Dict[str, Any]:
    """Everything needed to continue this run (see GAME_STATE_ATTRS)."""
    from jedi_fugitive.game import save_codec
    try:
        from jedi_fugitive.game.game_manager import GameManager
        stop = (GameManager,)
    except Exception:
        stop = ()
    try:
        surface_map, surface_items, pos, in_tomb = _surface_view(game)
        state = {k: getattr(game, k) for k in GAME_STATE_ATTRS if hasattr(game, k)}
        state['items_on_map'] = surface_items
        state['codex_discovered'] = set(getattr(getattr(game, 'sith_codex', None), 'discovered_entries', set()) or set())
        cordon = getattr(game, 'cordon', None)
        state['cordon'] = {'active': bool(getattr(cordon, 'active', False)),
                           'escaped': bool(getattr(cordon, 'escaped', False))} if cordon is not None else None
        blob = save_codec.encode({'player': game.player, 'game': state}, skip=_SKIP, stop_types=stop)
        player = game.player
        return {
            'version': SAVE_VERSION,
            'timestamp': datetime.now().isoformat(),
            'world_seed': getattr(game, 'world_seed', None),
            'world_size': getattr(game, 'world_size', 'normal'),
            'position': list(pos),
            'saved_in_tomb': in_tomb,
            'map': [''.join(row) for row in surface_map],
            'state': blob,
            # summary for the load menu
            'summary': {'level': getattr(player, 'level', 1), 'turn': getattr(game, 'turn_count', 0),
                        'hp': getattr(player, 'hp', 0), 'max_hp': getattr(player, 'max_hp', 0)},
            # kept so list_saves() and old tools keep working
            'player': {'level': getattr(player, 'level', 1)},
            'game': {'turn_count': getattr(game, 'turn_count', 0)},
        }
    except Exception as e:
        print(f"Error serializing game state: {e}")
        return {}


def apply_save_data(game, save_data: Dict[str, Any]) -> bool:
    """Restore a save into `game`, regenerating its world from the saved seed if needed."""
    if not save_data:
        return False
    if save_data.get('version') != SAVE_VERSION:
        return _apply_save_data_v1(game, save_data)
    from jedi_fugitive.game import save_codec
    try:
        seed = save_data.get('world_seed')
        if seed is not None and (getattr(game, 'world_seed', None) != seed or not getattr(game, 'game_map', None)):
            game.world_seed = seed
            game.world_size = save_data.get('world_size', getattr(game, 'world_size', 'normal'))
            game.generate_world()
        blob = save_codec.decode(save_data['state'])
        fresh, player = game.player, blob['player']
        # re-attach the session links the codec dropped
        for k in _SKIP:
            if hasattr(fresh, k) and k not in vars(player):
                try:
                    object.__setattr__(player, k, getattr(fresh, k))
                except Exception:
                    pass
        if getattr(game, 'stealth_system', None) is not None:
            player.stealth_system = game.stealth_system
        game.player = player
        for k, v in blob['game'].items():
            if k in ('codex_discovered', 'cordon'):
                continue
            setattr(game, k, v)
        # systems that point at the player now point at the restored one
        for obj in list(vars(game).values()):
            try:
                if getattr(obj, 'player', None) is fresh:
                    obj.player = player
            except Exception:
                pass
        ps = getattr(game, 'pursuit_system', None)
        if ps is not None:
            ps.predator = None
            ps.sith_predator_active = False
        try:
            if getattr(player, 'faction_manager', None) is not None:
                game.faction_manager = player.faction_manager
        except Exception:
            pass
        codex = getattr(game, 'sith_codex', None)
        if codex is not None:
            try:
                from jedi_fugitive.game import tomb_lords
                tomb_lords._ensure_codex(game)
            except Exception:
                pass
            codex.discovered_entries = set(blob['game'].get('codex_discovered') or set())
        # the surface as it was
        if save_data.get('map'):
            game.game_map = [list(row) for row in save_data['map']]
        for attr in ('tomb_levels', 'tomb_rooms', 'tomb_enemies', 'tomb_items', 'tomb_stairs',
                     'tomb_floor', 'surface_map', 'surface_items_on_map'):
            if hasattr(game, attr):
                try:
                    delattr(game, attr)
                except Exception:
                    pass
        game.current_tomb = None
        game.tomb_guardian = None
        game.current_depth = 1
        x, y = save_data.get('position') or (player.x, player.y)
        player.x, player.y = int(x), int(y)
        if save_data.get('saved_in_tomb'):
            player.los_radius = max(6, int(getattr(player, 'los_radius', 6) or 6))
        # the cordon does not come back once you broke out of it
        cordon_state = blob['game'].get('cordon') or {}
        cordon = getattr(game, 'cordon', None)
        if cordon is not None and (cordon_state.get('escaped') or not cordon_state.get('active', True)):
            units = set(id(u) for u in getattr(cordon, 'units', []) or [])
            game.enemies = [e for e in game.enemies if id(e) not in units]
            cordon.active = False
            cordon.escaped = bool(cordon_state.get('escaped'))
            cordon.units = []
        # quest hunt targets live in the quest: put them back into the world
        try:
            for q in (getattr(game.quest_manager, 'active_quests', {}) or {}).values():
                e = getattr(q, 'target_enemy', None)
                if e is not None and getattr(e, 'hp', 0) > 0 and e not in game.enemies:
                    game.enemies.append(e)
        except Exception:
            pass
        # nothing regenerated gets to stand on top of you
        game.enemies = [e for e in game.enemies
                        if abs(getattr(e, 'x', 0) - player.x) + abs(getattr(e, 'y', 0) - player.y) > 14
                        or getattr(e, 'is_boss', False) or getattr(e, 'quest_target', False)]
        game._last_hp_seen = getattr(player, 'hp', None)
        game.death = False
        game.running = True
        try:
            player._stats_cache_dirty = True
        except Exception:
            pass
        try:
            game.compute_visibility()
        except Exception:
            pass
        if save_data.get('saved_in_tomb'):
            try:
                game.add_message("You wake at the tomb's entrance; the halls below have shifted in the dark.")
            except Exception:
                pass
        return True
    except Exception as e:
        import traceback
        print(f"Error applying save data: {e}")
        traceback.print_exc()
        return False


def latest_save_path() -> Optional[Path]:
    """The most recently written save (autosave or a manual slot), or None."""
    paths = [get_autosave_path()] + [get_manual_save_path(i) for i in range(1, 4)]
    existing = [p for p in paths if p.exists()]
    return max(existing, key=lambda p: p.stat().st_mtime) if existing else None


def continue_game(game, path: Optional[Path] = None) -> bool:
    """Initialize `game` from a save file (instead of initialize() + generate_world())."""
    path = path or latest_save_path()
    if path is None:
        return False
    data = load_game(path)
    if not data:
        return False
    game.initialize()
    if data.get('version') == SAVE_VERSION:
        game.world_seed = data.get('world_seed')
        game.world_size = data.get('world_size', getattr(game, 'world_size', 'normal'))
        game.generate_world()
    else:
        game.generate_world()
    return apply_save_data(game, data)
