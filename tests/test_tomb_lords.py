"""Tombs with identity: a Sith Lord per tomb, holocron fragments as progression."""
from jedi_fugitive.game import tomb_lords
from jedi_fugitive.game.level import Display

from tests.test_world_and_story import make_game


def _enter(gm, entrance):
    gm.player.x, gm.player.y = entrance
    assert gm.enter_tomb()


def test_each_tomb_has_a_lord_fragments_and_guardian():
    gm = make_game(seed=5)
    entrances = sorted(gm.tomb_entrances)
    _enter(gm, entrances[0])
    rec = tomb_lords.current_record(gm)
    assert rec['lord'] in tomb_lords.LORDS
    # one fragment on each of the first three floors, drawn on the map
    floors = sorted(k[0] for k in rec['fragments'])
    assert floors == [0, 1, 2]
    for (f, x, y) in rec['fragments']:
        assert gm.tomb_levels[f][y][x] == tomb_lords.FRAGMENT_GLYPH
    # the guardian waits on the last floor, next to the relic
    last = gm.tomb_enemies[-1]
    guardians = [e for e in last if getattr(e, 'tomb_boss', False)]
    assert len(guardians) == 1 and guardians[0] is gm.tomb_guardian
    assert tomb_lords.LORDS[rec['lord']]['boss'][1] == guardians[0].name


def test_distinct_lords_until_all_used():
    gm = make_game(seed=5)
    lords = [tomb_lords.lord_for(gm, (i, i))['lord'] for i in range(len(tomb_lords.LORDS))]
    assert sorted(lords) == sorted(tomb_lords.LORDS)
    # binding is stable
    assert tomb_lords.lord_for(gm, (0, 0))['lord'] == lords[0]


def test_collecting_all_fragments_grants_the_lords_legacy():
    gm = make_game(seed=7)
    _enter(gm, sorted(gm.tomb_entrances)[0])
    rec = tomb_lords.current_record(gm)
    lord_id = rec['lord']
    reward = tomb_lords.LORDS[lord_id]['reward']
    p = gm.player
    before = {'max_hp': p.max_hp, 'attack': p.attack, 'defense': p.defense, 'accuracy': p.accuracy,
              'max_force': p.max_force_energy}
    for (f, x, y) in sorted(rec['fragments']):
        gm.tomb_floor = f
        gm.game_map = gm.tomb_levels[f]
        p.x, p.y = x, y
        assert tomb_lords.on_step(gm)
        assert gm.game_map[y][x] == Display.FLOOR
    assert rec['fragments'] == {}
    assert p.lord_fragments[lord_id] == {0, 1, 2}
    assert lord_id in p.lord_masteries
    if reward.get('ability'):
        assert reward['ability'] in p.force_abilities
    if reward.get('form'):
        assert reward['form'] in p.known_forms
    if reward.get('max_hp'):
        assert p.max_hp == before['max_hp'] + reward['max_hp']
    for stat in ('attack', 'defense', 'accuracy'):
        if reward.get(stat):
            assert getattr(p, stat) == before[stat] + reward[stat]
    if reward.get('max_force'):
        assert p.max_force_energy == before['max_force'] + reward['max_force']
    # the codex records every fragment
    found = {e for (c, e) in gm.sith_codex.discovered_entries if c == 'tomb_lords'}
    assert found == {f"{lord_id}_{i}" for i in range(3)}
    # the legacy is granted once
    assert not tomb_lords.grant_mastery(gm, lord_id)


def test_guardian_death_and_relic_story_and_persistence():
    gm = make_game(seed=9)
    entrance = sorted(gm.tomb_entrances)[0]
    _enter(gm, entrance)
    rec = tomb_lords.current_record(gm)
    gm.tomb_guardian.hp = 0
    gm._world_tick()
    assert rec['boss_defeated']
    assert tomb_lords.on_relic_recovered(gm)
    assert not tomb_lords.on_relic_recovered(gm)
    # leave and come back: same Lord, guardian stays dead
    gm.tomb_floor = 0
    gm.game_map = gm.tomb_levels[0]
    assert gm.change_floor(-1)
    assert gm.current_tomb is None
    _enter(gm, entrance)
    assert tomb_lords.current_record(gm) is rec
    assert gm.tomb_guardian is None


def test_illusions_dissolve_when_struck():
    gm = make_game(seed=11)
    from jedi_fugitive.game import enemies_sith as sith
    e = tomb_lords.make_illusion(sith.create_sith_acolyte(level=2))
    e.x, e.y = gm.player.x + 1, gm.player.y
    gm.enemies.append(e)
    stress = gm.player.stress
    from jedi_fugitive.game.input_handler import perform_player_attack
    perform_player_attack(gm, e)
    assert e not in gm.enemies
    assert gm.player.stress >= stress


def test_a_swing_is_resolved_once():
    """perform_player_attack used to add a second 'fallback' hit whenever the enemy survived."""
    import random
    gm = make_game(seed=13)
    from jedi_fugitive.game import enemies_sith as sith
    from jedi_fugitive.game.input_handler import perform_player_attack
    from jedi_fugitive.game import combat
    random.seed(1)
    calls = []
    real = combat.player_attack

    def spy(player, enemy, messages=None, game=None):
        before = enemy.hp
        res = real(player, enemy, messages=messages, game=game)
        calls.append(before - enemy.hp)
        return res
    combat.player_attack = spy
    try:
        e = sith.create_sith_warrior(level=8)
        e.hp = e.max_hp = 10_000
        gm.enemies.append(e)
        for _ in range(20):
            hp0 = e.hp
            perform_player_attack(gm, e)
            assert hp0 - e.hp == calls[-1]
    finally:
        combat.player_attack = real
