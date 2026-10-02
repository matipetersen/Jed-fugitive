"""Day and night: shorter sight, easier hiding, riskier camps; nothing underground."""
from jedi_fugitive.game import daynight, survival
from tests.test_world_and_story import make_game


def _at(gm, phase):
    for t in range(daynight.DAY_TICKS):
        gm.turn_count = t
        if daynight.phase(gm) == phase:
            return t
    raise AssertionError(phase)


def test_a_day_has_every_phase_in_order():
    gm = make_game(seed=2)
    seen = []
    for t in range(daynight.DAY_TICKS):
        gm.turn_count = t
        p = daynight.phase(gm)
        if not seen or seen[-1] != p:
            seen.append(p)
    # the crash happens by day; then dusk, night, dawn
    assert seen[:4] == ['day', 'dusk', 'night', 'dawn']


def test_night_shortens_sight_on_the_surface_only():
    gm = make_game(seed=2)
    gm.enemies = []
    _at(gm, 'day')
    gm.compute_visibility()
    day = len(gm.visible)
    _at(gm, 'night')
    gm.compute_visibility()
    assert len(gm.visible) < day
    # underground there is no night
    gm.player.x, gm.player.y = sorted(gm.tomb_entrances)[0]
    assert gm.enter_tomb()
    assert daynight.sight_modifier(gm) == 0 and daynight.camp_risk_modifier(gm) == 0


def test_camping_at_night_is_riskier():
    gm = make_game(seed=2)
    _at(gm, 'day')
    day = survival.camp_risk(gm)
    _at(gm, 'night')
    assert survival.camp_risk(gm) > day + 0.15


def test_phase_changes_are_announced():
    gm = make_game(seed=2)
    msgs = []
    gm.add_message = msgs.append
    t = _at(gm, 'dusk') - 1
    gm.turn_count = t
    daynight.tick(gm)
    gm.turn_count = t + 1
    daynight.tick(gm)
    assert any('Dusk' in m for m in msgs)
