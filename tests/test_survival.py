"""Wounds the Force cannot mend, and camps that cost exposure."""
import random

from jedi_fugitive.game import survival, combat
from tests.test_world_and_story import make_game


def _fresh(seed):
    gm = make_game(seed=seed)
    gm.enemies = []  # a quiet world, so only what we do matters
    gm._world_tick()
    return gm


def test_brutal_hit_wounds_and_light_hit_does_not():
    gm = _fresh(21)
    p = gm.player
    p.hp = p.max_hp
    gm._world_tick()
    p.hp -= int(p.max_hp * 0.10)
    gm._world_tick()
    assert survival.wounds(p) == {}
    p.hp -= int(p.max_hp * 0.60) + 1
    gm._world_tick()
    assert len(survival.wounds(p)) == 1


def test_wound_chance_curve():
    c = survival.wound_chance
    assert c(2, 15) == 0.0            # a scratch
    assert 0.0 < c(5, 15) < 0.2       # a trooper's hit at level 1
    assert 0.35 < c(8, 15) <= 0.5     # a Sith warrior's
    assert c(9, 15) == 1.0            # 60%: always


def test_wound_effects_apply_and_revert():
    gm = _fresh(22)
    p = gm.player
    acc, eva, dmg = p.accuracy, p.evasion, combat.attack_bonus(p)
    survival.inflict(gm, 'arm')
    survival.inflict(gm, 'leg')
    assert p.accuracy == acc - 8
    assert p.evasion == eva - 6
    assert combat.attack_bonus(p) == dmg - 1
    survival.treat(gm, 'arm')
    survival.treat(gm, 'leg')
    assert (p.accuracy, p.evasion, combat.attack_bonus(p)) == (acc, eva, dmg)
    assert survival.wounds(p) == {}


def test_bleeding_never_kills():
    gm = _fresh(23)
    p = gm.player
    survival.inflict(gm, 'torso')
    p.hp = 3
    gm._last_hp_seen = p.hp
    # only the wound acts (a full world tick would let the cordon hit you too)
    for _ in range(100):
        gm.turn_count += 1
        survival.on_hp_change(gm)
    assert p.hp == 1


def test_force_heal_does_not_close_wounds_but_a_medkit_does():
    gm = _fresh(24)
    p = gm.player
    survival.inflict(gm, 'arm')
    p.hp = p.max_hp // 2
    p.force_energy = 100
    heal = next((a for a in p.force_abilities.values() if getattr(a, 'name', '') == 'Heal'), None)
    if heal is not None:
        try:
            heal.use(p, p, gm.ui.messages)
        except TypeError:
            heal.use(p, p)
        assert 'arm' in survival.wounds(p)
    p.inventory.append({'id': 'medkit_small', 'name': 'Small Medkit', 'type': 'consumable', 'effect': {'heal': 10}})
    assert survival.is_medkit(p.inventory[-1])
    survival.treat(gm)
    assert survival.wounds(p) == {}


def test_leg_wound_makes_you_stumble():
    gm = _fresh(25)
    survival.inflict(gm, 'leg')
    random.seed(0)
    for _ in range(200):
        survival.on_player_moved(gm)
    n = survival.pop_stumble(gm)
    assert 30 <= n <= 90  # ~30%
    assert survival.pop_stumble(gm) == 0


def test_undisturbed_camp_heals_a_wound():
    gm = _fresh(26)
    p = gm.player
    survival.inflict(gm, 'torso')
    p.hp = p.max_hp // 3
    gm._last_hp_seen = p.hp  # (setting HP here is not a hit)
    p.stress = 50
    random.seed(1)
    orig = survival.camp_risk
    survival.camp_risk = lambda game: 0.0
    gm._in_combat = lambda radius=8: False  # nothing wanders by
    try:
        t0 = gm.turn_count
        assert survival.make_camp(gm)
    finally:
        survival.camp_risk = orig
    assert gm.turn_count - t0 == survival.CAMP_TICKS
    assert survival.wounds(p) == {}
    assert p.hp > p.max_hp // 3


def test_camp_can_be_ambushed_and_risk_grows_with_heat_and_wounds():
    gm = _fresh(27)
    base = survival.camp_risk(gm)
    gm.pursuit_system.detection_level = 80
    survival.inflict(gm, 'leg')
    assert survival.camp_risk(gm) > base + 0.4
    survival.inflict(gm, 'arm')
    random.seed(2)
    orig = survival.camp_risk
    survival.camp_risk = lambda game: 1.0
    try:
        n_enemies = len(gm.enemies)
        survival.make_camp(gm)
    finally:
        survival.camp_risk = orig
    assert len(gm.enemies) > n_enemies
    assert survival.wounds(gm.player)  # an interrupted camp treats nothing


def test_no_camp_next_to_enemies():
    gm = _fresh(28)
    from jedi_fugitive.game import enemies_sith as sith
    e = sith.create_sith_trooper(level=1)
    e.x, e.y = gm.player.x + 2, gm.player.y
    gm.enemies.append(e)
    t0 = gm.turn_count
    assert not survival.make_camp(gm)
    assert gm.turn_count == t0


def test_wounds_and_lord_progress_survive_save_and_load():
    import json
    from jedi_fugitive.game import save_system
    gm = _fresh(29)
    p = gm.player
    survival.inflict(gm, 'arm')
    p.lord_fragments = {'naga_sadow': {0, 2}}
    p.lord_masteries = {'tulak_hord'}
    acc = p.accuracy
    data = json.loads(json.dumps(save_system.serialize_game_state(gm)))
    gm2 = _fresh(30)
    assert save_system.apply_save_data(gm2, data)
    p2 = gm2.player
    assert 'arm' in survival.wounds(p2) and p2.accuracy == acc
    assert p2.lord_fragments == {'naga_sadow': {0, 2}} and p2.lord_masteries == {'tulak_hord'}
    survival.treat(gm2, 'arm')
    assert p2.accuracy == acc + 8
