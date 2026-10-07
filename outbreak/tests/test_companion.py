import unittest

from tests import helpers
from outbreak.content.companions import ARCHETYPES, BY_ID
from outbreak.engine import combat, companion, services, tiles as T
from outbreak.engine.model import Human, Item, Zombie
from outbreak.engine.spawn import spawn_zombie


def field(seed=3, arch=None):
    g = helpers.make_game(seed=seed)
    lv = g.world.level
    c = companion.current(g)
    for a in list(lv.actors):
        if a is not c:
            lv.remove_actor(a)
    g.hordes.clear()
    g.ring = None
    p = g.player
    p.hp = p.max_hp = 10 ** 6
    p.infected = False
    for y in range(p.y - 10, p.y + 11):
        for x in range(p.x - 12, p.x + 13):
            lv.set_tile(x, y, T.GRASS)
    if arch:
        c.trait = ""
        companion.ensure_person(g, c, arch)
    return g, lv, c


class Profiles(unittest.TestCase):
    def test_you_start_with_one_companion_from_the_pool(self):
        seen = set()
        for seed in range(1, 25):
            g = helpers.make_game(seed=seed)
            c = companion.current(g)
            self.assertIsNotNone(c)
            self.assertEqual(c.state, "follow")
            self.assertIn(c.trait, BY_ID)
            self.assertTrue(c.name and c.name != "Survivor")
            seen.add(c.trait)
        self.assertGreaterEqual(len(seen), 5, "the pool is varied")

    def test_every_archetype_has_a_strength_a_flaw_and_a_voice(self):
        self.assertGreaterEqual(len(ARCHETYPES), 8)
        for a in ARCHETYPES:
            self.assertTrue(a.strength and a.flaw and a.intro and a.farewell)
            self.assertEqual(len(a.backstory), 3)
            self.assertTrue(a.idle and a.kill and a.hurt)

    def test_anyone_can_become_a_companion_with_a_profile_fixed_by_who_they_are(self):
        g, lv, c = field()
        g.companion_uid = 0
        c.state = "patrol"
        healer = Human(g.next_uid(), "Healer", "H", c.x + 2, c.y, 30, 30, role="healer", faction="enclave")
        lv.add_actor(healer)
        g.rep["enclave"] = 40
        self.assertEqual(services.ask_join(g, healer).split()[0], healer.name)
        self.assertEqual(healer.trait, "medic")
        self.assertEqual(g.companion_uid, healer.uid)
        self.assertEqual(healer.state, "follow")

    def test_only_one_at_a_time(self):
        g, lv, c = field()
        other = Human(g.next_uid(), "Trader", "T", c.x + 2, c.y, 30, 30, role="trader", faction="enclave")
        lv.add_actor(other)
        g.rep["enclave"] = 40
        self.assertIn("only one", services.ask_join(g, other).lower())


class Effects(unittest.TestCase):
    def test_a_medic_patches_you_up(self):
        g, lv, c = field(arch="medic")
        p = g.player
        p.max_hp, p.hp = 100, 30
        g.clock.turn = 1000
        companion.tick(g)
        self.assertGreater(p.hp, 30)
        self.assertTrue(any(t == "ally" for _, _, t in g.log))

    def test_a_scout_reveals_ambushers(self):
        g, lv, c = field(arch="hunter")
        from outbreak.engine.spawn import make_raider
        r = make_raider(g, c.x + 4, c.y)
        r.hidden, r.state = True, "idle"
        lv.add_actor(r)
        g.clock.turn = 1000
        companion.tick(g)
        self.assertFalse(r.hidden)

    def test_a_scavenger_comes_back_with_something(self):
        g, lv, c = field(arch="scavenger")
        g.rng.random = lambda: 0.0
        n = sum(i.qty for i in g.player.inventory)
        companion.on_return(g)
        self.assertGreater(sum(i.qty for i in g.player.inventory), n)

    def test_a_loud_companion_makes_noise(self):
        g, lv, c = field(arch="scavenger")
        g.rng.random = lambda: 0.0
        g.clock.turn = 50 * 25
        before = len(g.pings)
        companion.tick(g)
        self.assertGreater(len(g.pings), before)

    def test_a_hungry_companion_eats_your_food(self):
        g, lv, c = field(arch="hunter")
        g.player.inventory.append(Item("food", 3))
        c.since = 0
        g.clock.turn = 1000
        companion.tick(g)
        self.assertEqual(g.player.count("food"), 2)

    def test_a_coward_runs_early_and_a_pacifist_will_not_fight_people(self):
        g, lv, c = field(arch="mechanic")
        self.assertEqual(companion.flee_below(c), 0.6)
        g2, lv2, c2 = field(arch="preacher")
        raider = Human(g2.next_uid(), "Raider", "r", c2.x + 3, c2.y, 10, 10, role="raider", faction="raiders", hostile=True)
        self.assertTrue(companion.refuses_to_fight(c2, raider))
        z = Zombie(1, "Z", "z", 0, 0, 5, 5)
        self.assertFalse(companion.refuses_to_fight(c2, z))

    def test_a_fighter_fights_better_than_a_frail_medic(self):
        g, lv, c = field(arch="veteran")
        g2, lv2, m = field(arch="medic")
        self.assertGreater(c.max_hp, m.max_hp)
        self.assertGreater(sum(c.dmg), sum(m.dmg))


class Bond(unittest.TestCase):
    def test_time_and_gifts_raise_it_and_killing_innocents_lowers_it(self):
        g, lv, c = field(arch="preacher")
        b = c.bond
        g.clock.turn = 100
        companion.tick(g)
        self.assertGreater(c.bond, b)
        g.player.inventory.append(Item("food", 1))
        b = c.bond
        companion.give(g, c, len(g.player.inventory) - 1)
        self.assertGreater(c.bond, b)
        victim = Human(g.next_uid(), "Stranger", "S", c.x + 2, c.y, 5, 5, role="survivor", faction="enclave")
        b = c.bond
        companion.on_player_kills_human(g, victim)
        self.assertLess(c.bond, b - 10, "a pacifist cannot bear it")

    def test_a_broken_bond_makes_them_leave(self):
        g, lv, c = field()
        c.bond = 3
        g.clock.turn = 7
        companion.tick(g)
        self.assertIsNone(companion.current(g))
        self.assertEqual(c.state, "patrol")

    def test_what_you_have_become_matters(self):
        g, lv, c = field()
        g.player.humanity = 10
        companion.tick(g)
        self.assertIsNone(companion.current(g))

    def test_their_story_comes_out_as_the_bond_grows(self):
        g, lv, c = field(arch="veteran")
        c.bond = 40
        t1 = companion.talk(g, c)
        self.assertIn(BY_ID["veteran"].backstory[0][1:20], t1)
        self.assertEqual(c.story, 1)
        c.bond = 90
        companion.talk(g, c)
        companion.talk(g, c)
        self.assertEqual(c.story, 3)

    def test_advice_names_the_next_objective(self):
        g, lv, c = field()
        self.assertIn(c.name, companion.advice(g))


class Death(unittest.TestCase):
    def test_a_dead_companion_stays_dead_and_the_log_says_so(self):
        g, lv, c = field()
        c.hp = 1
        z = spawn_zombie(g, lv, (c.x + 1, c.y), "walker", False)
        combat.kill_human_other(g, c, z)
        self.assertIsNone(companion.current(g))
        self.assertEqual(g.companion_uid, 0)
        self.assertIn(c.name, g.fallen_allies[-1][0])
        self.assertTrue(any("is dead" in t and tag == "ally" for _, t, tag in g.story))
        self.assertNotIn(c, lv.actors)

    def test_anyone_else_can_take_their_place(self):
        g, lv, c = field()
        combat.kill_human_other(g, c, spawn_zombie(g, lv, (c.x + 2, c.y), "walker", False))
        other = Human(g.next_uid(), "Soldier", "f", g.player.x + 2, g.player.y, 20, 20, role="soldier", faction="military")
        lv.add_actor(other)
        g.rep["military"] = 30
        services.ask_join(g, other)
        self.assertEqual(g.companion_uid, other.uid)

    def test_the_ending_remembers_them(self):
        g, lv, c = field()
        name = c.name
        combat.kill_human_other(g, c, spawn_zombie(g, lv, (c.x + 2, c.y), "walker", False))
        from outbreak.engine import ending
        e = ending.build(g, "dead", "test")
        self.assertTrue(any(name in line for line in e.summary))


class Log(unittest.TestCase):
    def test_the_default_log_is_objectives_and_companion_not_noise(self):
        g, lv, c = field()
        g.msg("You swing at the thing and miss.", "combat")
        g.msg("Mina: \"hi\"", "ally")
        g.msg("Done: something.", "obj")
        g.msg("A horde appears!", "bad", key=True)
        tags = {t for _, _, t in g.story}
        self.assertIn("ally", tags)
        self.assertIn("obj", tags)
        self.assertNotIn("combat", tags)
        self.assertTrue(any("swing" in t for _, t, _ in g.log), "the full log keeps everything")

    def test_objective_changes_are_announced(self):
        g, lv, c = field()
        g.clock.turn = 10
        from outbreak.engine import objective
        objective.watch(g)
        n = len(g.story)
        g.formula_found = True
        for p in g.pois.values():
            if p.component:
                p.lead = True
                p.revealed = True
        g.clock.turn = 20
        objective.watch(g)
        self.assertTrue(any(t == "obj" for _, _, t in g.story[n - 1:]) or len(g.story) > n)

    def test_build_log_pins_the_goal(self):
        from outbreak.ui import render
        g, lv, c = field()
        g.msg("Day 1.", "obj")
        lines = render.build_log(g, 5, 80)
        self.assertTrue(lines[0][0].startswith("GOAL"))
        self.assertLessEqual(len(lines), 5)
        full = render.build_log(g, 5, 80, full=True)
        self.assertFalse(any(t.startswith("GOAL") for t, _ in full))


class Combat(unittest.TestCase):
    def test_the_dead_attack_a_companion_and_it_can_die(self):
        g, lv, c = field(arch="medic")
        c.hp = 6
        z = spawn_zombie(g, lv, (c.x + 1, c.y), "walker", False)
        z.hp = z.max_hp = 500
        z.dmg, z.acc = (6, 8), 95
        del lv.occ[g.player.pos]
        g.player.x, g.player.y = c.x - 7, c.y
        lv.occ[g.player.pos] = g.player
        for _ in range(80):
            if companion.current(g) is None:
                break
            g.clock.turn += 1
            from outbreak.engine import ai
            ai.run(g)
        self.assertIsNone(companion.current(g), "a companion is not invincible")
        self.assertTrue(any("is dead" in t for _, t, _ in g.story))

    def test_every_companion_role_is_a_target_not_just_fighters(self):
        g, lv, c = field(arch="medic")
        c.role = "survivor"
        z = spawn_zombie(g, lv, (c.x + 2, c.y), "walker", False)
        z.state, z.target = "hunt", c.pos
        z.hp = z.max_hp = 500
        z.dmg, z.acc = (4, 6), 95
        del lv.occ[g.player.pos]
        g.player.x, g.player.y = c.x + 8, c.y + 8
        lv.occ[g.player.pos] = g.player
        hp = c.hp
        from outbreak.engine import ai
        for _ in range(12):
            g.clock.turn += 1
            ai.run(g)
        self.assertLess(c.hp, hp)

    def test_they_do_not_leave_you_to_chase_a_fight_while_you_run(self):
        g, lv, c = field(arch="brute")
        z = spawn_zombie(g, lv, (c.x + 5, c.y + 3), "walker", False)
        z.state = "idle"
        del lv.occ[g.player.pos]
        g.player.x, g.player.y = c.x - 9, c.y
        lv.occ[g.player.pos] = g.player
        before = max(abs(c.x - g.player.x), abs(c.y - g.player.y))
        from outbreak.engine import ai
        for _ in range(6):
            g.clock.turn += 1
            ai.run(g)
        after = max(abs(c.x - g.player.x), abs(c.y - g.player.y))
        self.assertLess(after, before, "they come back to you")
        self.assertTrue(companion.should_hold_back(g, c, z) or after < before)

    def test_a_reckless_one_still_charges(self):
        g, lv, c = field(arch="veteran")
        self.assertEqual(companion.leash(c), companion.LEASH_RECKLESS)
        g2, lv2, m = field(arch="medic")
        self.assertEqual(companion.leash(m), companion.LEASH)

    def test_they_shout_when_a_fight_starts_when_you_are_hit_and_when_left_behind(self):
        g, lv, c = field(arch="veteran")
        z = spawn_zombie(g, lv, (c.x + 1, c.y), "walker", False)
        from outbreak.engine import ai
        g.clock.turn = 2000
        ai._human_fight(g, c, z)
        self.assertTrue(any(tag == "ally" and "Contact" in t or tag == "ally" and c.name in t for _, t, tag in g.story[-4:]))
        n = len(g.story)
        g.clock.turn = 3000
        combat.damage_player(g, 6, "test")
        self.assertGreater(len(g.story), n, "a shout when you are hit")
        g.clock.turn = 4000
        companion.on_regroup(g, c)
        self.assertIn("ally", [tag for _, _, tag in g.story[-2:]])

    def test_their_blows_show_in_the_story_log(self):
        g, lv, c = field(arch="veteran")
        z = spawn_zombie(g, lv, (c.x + 1, c.y), "walker", False)
        z.hp = z.max_hp = 100
        for _ in range(8):
            combat.attack_actor(g, c, z)
        self.assertTrue(any(tag == "ally" and ("hits" in t or "misses" in t) for _, t, tag in g.story))


if __name__ == "__main__":
    unittest.main()
