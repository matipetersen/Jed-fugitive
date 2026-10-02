"""Save v2: the whole run survives a save/load, not just a few player numbers."""
import json

import pytest

from jedi_fugitive.game import save_codec, save_system, survival, tomb_lords
from jedi_fugitive.game.equipment import _grant_ability
from jedi_fugitive.game.game_manager import GameManager
from tests.test_world_and_story import DummyStdScr, make_game


def _roundtrip(gm, tmp_path):
    data = json.loads(json.dumps(save_system.serialize_game_state(gm)))
    path = tmp_path / 'save.json'
    path.write_text(json.dumps(data))
    gm2 = GameManager(DummyStdScr())
    gm2.world_size = gm.world_size
    assert save_system.continue_game(gm2, path)
    return gm2


def _names(inv):
    return sorted((getattr(i, 'name', None) or i.get('name')) for i in inv)


def test_world_regenerates_identically_from_its_seed():
    a = make_game(seed=8)
    b = GameManager(DummyStdScr())
    b.initialize()
    b.world_size = a.world_size
    b.world_seed = a.world_seed
    b.generate_world()
    assert a.game_map == b.game_map
    assert a.tomb_entrances == b.tomb_entrances


def test_full_roundtrip(tmp_path):
    gm = make_game(seed=4)
    for _ in range(10):
        gm._world_tick()
    p = gm.player
    survival.inflict(gm, 'arm')
    _grant_ability(gm, 'Lightning')
    p.known_forms.append('Makashi')
    p.inventory.append({'id': 'medkit_small', 'name': 'Small Medkit', 'type': 'consumable', 'effect': {'heal': 10}})
    accepted = None
    for npc in gm.quest_manager.available_npcs:
        conv = gm.quest_manager.start_conversation(npc, p, game=gm)
        if conv.get('quest') is not None and gm.accept_npc_quest(conv['quest']):
            accepted = conv['quest']
            break
    gm.pursuit_system.detection_level = 42
    gm.sith_codex.discovered_entries.add(('sith_history', 'ancient_orders'))

    gm2 = _roundtrip(gm, tmp_path)
    p2 = gm2.player
    assert gm2.game_map == gm.game_map
    assert (p2.x, p2.y, p2.hp, p2.max_hp, p2.level) == (p.x, p.y, p.hp, p.max_hp, p.level)
    assert _names(p2.inventory) == _names(p.inventory)
    assert p2.equipped_weapon.name == p.equipped_weapon.name
    assert sorted(p2.force_abilities) == sorted(p.force_abilities)
    assert p2.known_forms == p.known_forms
    assert p2.wounds == p.wounds and p2.accuracy == p.accuracy
    assert p2.travel_log == p.travel_log and p2.skills == p.skills
    assert gm2.turn_count == gm.turn_count
    assert gm2.pursuit_system.detection_level == 42 and gm2.pursuit_system.player is p2
    assert ('sith_history', 'ancient_orders') in gm2.sith_codex.discovered_entries
    if accepted is not None:
        (q2,) = gm2.quest_manager.active_quests.values()
        assert q2.title == accepted.title
        # quest and map share the same NPC object again
        assert any(q2.npc is n for n in gm2.npcs_on_map.values())
    # and the game keeps running
    for _ in range(20):
        gm2._try_move_player(1, 0)
        gm2._world_tick()
        gm2.running = True


def test_saving_inside_a_tomb_resumes_at_its_entrance_without_exploits(tmp_path):
    gm = make_game(seed=6)
    entrance = sorted(gm.tomb_entrances)[0]
    gm.player.x, gm.player.y = entrance
    assert gm.enter_tomb()
    rec = tomb_lords.current_record(gm)
    rec['boss_defeated'] = True
    rec['relic_recovered'] = True
    gm.player.lord_fragments = {rec['lord']: {0}}

    gm2 = _roundtrip(gm, tmp_path)
    assert (gm2.player.x, gm2.player.y) == entrance
    assert not getattr(gm2, 'tomb_levels', None)
    assert gm2.enter_tomb()
    rec2 = tomb_lords.current_record(gm2)
    assert rec2['lord'] == rec['lord']
    # the slain guardian, the carried-out relic and the read fragment do not come back
    assert gm2.tomb_guardian is None
    assert not any(getattr(e, 'tomb_boss', False) for fl in gm2.tomb_enemies for e in fl)
    assert not any(i.get('token') == 'Q' for fl in gm2.tomb_items for i in fl if isinstance(i, dict))
    assert sorted(k[0] for k in rec2['fragments']) == [1, 2]


def test_codec_keeps_shared_references_and_exact_types():
    class_obj = survival  # any module object is dropped
    shared = {'k': 1}
    data = save_codec.encode({'a': [shared, shared], 't': (1, 2), 's': {3}, 'p': {(1, 2): 'x'}, 'm': class_obj})
    back = save_codec.decode(json.loads(json.dumps(data)))
    assert back['t'] == (1, 2) and back['s'] == {3} and back['p'] == {(1, 2): 'x'}
    assert 'm' not in back


def test_codec_refuses_classes_outside_the_game():
    evil = {'__obj__': 'os:system', '__id__': 1, 'state': {}}
    with pytest.raises(ValueError):
        save_codec.decode(evil)
