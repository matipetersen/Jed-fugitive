import unittest

from tests import helpers
from outbreak import content
from outbreak.engine import ai, ambience, mutation
from outbreak.engine import tiles as T
from outbreak.engine.spawn import make_zombie, spawn_zombie


def world(era, zombies="classic", seed=3):
    g = helpers.make_game(era=era, zombies=zombies, seed=seed)
    helpers.empty_level_of_enemies(g.world.level)
    g.hordes.clear()
    g.ring = None
    g.player.hp = g.player.max_hp = 10 ** 6
    return g


def days(g, n):
    g.clock.turn = 240 * (n - 1)


class EraRulesTests(unittest.TestCase):
    def test_every_era_has_its_own_rules(self):
        rules = {e.id: e.rules for e in content.ERAS.values()}
        self.assertEqual(len({r.feel for r in rules.values()}), 4)
        self.assertEqual(rules["medieval"].alarm_chance, 0.0)
        self.assertGreater(rules["scifi"].lab, rules["modern"].lab, )
        for r in rules.values():
            self.assertTrue(r.ambient)
            for kind, _ in r.ambient:
                self.assertIn(kind, ambience.EVENTS)

    def test_medieval_worlds_are_quieter_and_darker_scifi_is_watched(self):
        med, sci, mod = world("medieval"), world("scifi"), world("modern")
        self.assertLess(med.era.rules.step_noise, mod.era.rules.step_noise)
        # the same dark night: you see less in the medieval one, more with a visor
        for g in (med, sci, mod):
            g.clock.turn = 240 * 3 + 215
        self.assertLess(med.vision_radius(), mod.vision_radius())
        self.assertGreater(sci.vision_radius(), mod.vision_radius())

    def test_a_torch_shows_you_further_in_the_medieval_night_than_cold_light_in_the_future(self):
        out = {}
        for era in ("medieval", "modern", "scifi"):
            g = world(era)
            g.clock.turn = 240 * 3 + 215
            z = spawn_zombie(g, g.world.level, g.world.level.free_spot_near(g.player.x + 9, g.player.y, 2), "walker", dormant=False)
            z.state = "idle"
            from outbreak.engine import combat
            from outbreak.engine.model import Item
            g.player.light = Item("torch", 1, 100)
            g.player.light_on = True
            out[era] = ai.sight_range(g, z) if combat.player_lit(g) else 0
        self.assertGreater(out["medieval"], out["modern"])
        self.assertGreater(out["modern"], out["scifi"])

    def test_the_dead_of_the_future_see_in_the_dark_and_through_brush(self):
        sci, mod = world("scifi"), world("modern")
        for g in (sci, mod):
            g.clock.turn = 240 * 3 + 215
        zs, zm = [spawn_zombie(g, g.world.level, g.world.level.free_spot_near(g.player.x + 9, g.player.y, 2), "walker",
                               dormant=False) for g in (sci, mod)]
        for g, z in ((sci, zs), (mod, zm)):
            g.player.light = None
        self.assertGreater(ai.sight_range(sci, zs), ai.sight_range(mod, zm) * 1.3)
        for g in (sci, mod):
            g.world.level.set_tile(g.player.x, g.player.y, T.BRUSH)
        self.assertGreater(ai.sight_range(sci, zs) / ai.sight_range(mod, zm), 1.3)

    def test_the_world_makes_the_noises_of_its_era(self):
        for era, banned in (("medieval", {"car_alarm", "siren", "klaxon", "phone", "helicopter", "drone", "surge"}),
                            ("modern", {"bell", "klaxon", "drone"}), ("scifi", {"bell", "car_alarm", "phone"})):
            g = world(era, seed=5)
            kinds = set()
            for i in range(1, 3000):
                g.clock.turn = 100 + i * 20
                before = len(g.sources)
                ambience.world_tick(g)
                kinds.update(s["kind"] for s in g.sources)
                g.sources.clear()
            self.assertFalse(kinds & banned, (era, kinds & banned))
            self.assertTrue(kinds, era)

    def test_medieval_buildings_have_no_alarms(self):
        g = world("medieval")
        for poi in [q for q in g.pois.values() if q.kind in ("market", "guard", "military", "lab")]:
            ambience.building_alarm(g, poi)
        self.assertEqual(g.sources, [])

    def test_a_drone_drifts_and_scans_you_unless_you_creep(self):
        g = world("scifi")
        pos = (g.player.x + 6, g.player.y)
        g.sources.append({"pos": pos, "radius": 10, "every": 2, "left": 40, "kind": "drone", "drift": (-1, 0)})
        n = len(g.pings)
        for _ in range(8):
            g.clock.turn += 1
            ambience.world_tick(g)
        self.assertNotEqual(g.sources[0]["pos"], pos)
        self.assertTrue(g.sources[0].get("scanned"))
        g2 = world("scifi")
        g2.player.sneaking = True
        g2.sources.append({"pos": (g2.player.x + 4, g2.player.y), "radius": 10, "every": 2, "left": 40, "kind": "drone", "drift": (-1, 0)})
        for _ in range(8):
            g2.clock.turn += 1
            ambience.world_tick(g2)
        self.assertFalse(g2.sources[0].get("scanned"))


class MutationTests(unittest.TestCase):
    def test_strength_is_plague_times_science_and_ramps_up(self):
        a, b, c = world("scifi", "bio"), world("medieval", "classic"), world("modern", "bio")
        for g in (a, b, c):
            days(g, 30)
        self.assertGreater(mutation.strength(a), mutation.strength(c))
        self.assertGreater(mutation.strength(c), mutation.strength(b) * 10)
        days(a, 1)
        self.assertEqual(mutation.strength(a), 0.0)

    def test_an_engineered_plague_in_a_world_of_labs_changes_a_lot_a_quiet_one_does_not(self):
        hot, cold = world("scifi", "bio", seed=7), world("medieval", "classic", seed=7)
        for g in (hot, cold):
            for day in range(2, 40):
                days(g, day)
                mutation.daily(g)
        self.assertGreaterEqual(len(hot.mutations), 4)
        self.assertLessEqual(len(cold.mutations), 1)

    def test_traits_reach_old_and_new_zombies(self):
        g = world("scifi", "bio")
        old = spawn_zombie(g, g.world.level, g.world.level.free_spot_near(g.player.x + 8, g.player.y, 2), "walker", dormant=False)
        hp, speed, hearing, dmg = old.max_hp, old.speed, old.hearing, old.dmg
        days(g, 20)
        for _ in range(60):
            mutation.daily(g)
        self.assertTrue(g.mutations)
        self.assertTrue(old.max_hp > hp or old.speed > speed or old.hearing > hearing or old.dmg != dmg)
        z = make_zombie(g, "walker", 5, 5, True)
        base = make_zombie(world("scifi", "bio"), "walker", 5, 5, True)
        self.assertTrue(z.max_hp >= base.max_hp)

    def test_the_briefing_says_how_it_plays(self):
        g = world("modern", "bio")
        text = "\n".join(t for _, t in g.intro_pages)
        self.assertIn(g.era.rules.feel, text)
        self.assertIn("mutates fast", text)
        q = world("medieval", "classic")
        self.assertIn("hardly changes", "\n".join(t for _, t in q.intro_pages))


if __name__ == "__main__":
    unittest.main()
