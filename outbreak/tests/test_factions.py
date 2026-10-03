import unittest

from tests.helpers import make_game
from outbreak import content
from outbreak.engine import combat, services
from outbreak.engine.model import Human, Zombie
from outbreak.engine.spawn import make_patrol, make_raider, spawn_zombie
from outbreak.engine import ai


def clear(game):
    lv = game.world.level
    for a in list(lv.actors):
        if not a.is_player:
            lv.remove_actor(a)
    game.hordes.clear()
    return lv


def open_spot(game, lv, away=20):
    p = game.player
    for r in range(away, 40):
        for dx in range(-r, r + 1, 3):
            pos = (p.x + dx, p.y + r)
            if lv.in_bounds(*pos) and all(lv.free(pos[0] + i, pos[1]) for i in range(-3, 4)):
                return pos
    raise AssertionError("no open ground")


def tick(game, n):
    for _ in range(n):
        game._spend(1)


class FactionCombat(unittest.TestCase):
    def setUp(self):
        self.g = make_game(era="modern", zombies="classic", seed=3)
        self.lv = clear(self.g)
        self.base = open_spot(self.g, self.lv)

    def _put(self, actor, dx=0):
        spot = self.lv.free_spot_near(self.base[0] + dx, self.base[1], 2)
        if actor not in self.lv.actors:
            self.lv.add_actor(actor)
        self.lv.move_actor(actor, *spot)
        return actor

    def test_zombie_attacks_distant_human_when_player_is_away(self):
        z = self._put(spawn_zombie(self.g, self.lv, self.base, "walker", dormant=False))
        h = self._put(make_patrol(self.g, "scout", 0, 0, 1), dx=2)
        h.reach = 1
        h.hp = h.max_hp = 400
        z.state = "idle"
        before = h.hp
        tick(self.g, 30)
        self.assertLess(h.hp, before, "the zombie never touched the patrol")

    def test_patrol_kills_zombie(self):
        z = self._put(spawn_zombie(self.g, self.lv, self.base, "walker", dormant=False))
        h = self._put(make_patrol(self.g, "soldier", 0, 0, 1), dx=3)
        h.hp = h.max_hp = 500
        tick(self.g, 80)
        self.assertLessEqual(z.hp, 0)
        self.assertNotIn(z, self.lv.actors)

    def test_raiders_and_patrol_fight(self):
        r = self._put(make_raider(self.g, 0, 0))
        r.state = "idle"
        h = self._put(make_patrol(self.g, "soldier", 0, 0, 1), dx=4)
        tick(self.g, 80)
        self.assertTrue(r.hp < r.max_hp or h.hp < h.max_hp or r not in self.lv.actors or h not in self.lv.actors)

    def test_human_killed_by_zombie_rises_even_if_preset_does_not_turn_the_dead(self):
        g = make_game(era="modern", zombies="rage", seed=3)
        lv = clear(g)
        base = open_spot(g, lv)
        self.assertFalse(g.profile.turn_on_death)
        z = spawn_zombie(g, lv, base, "walker", dormant=False)
        h = make_patrol(g, "scout", 0, 0, 1)
        spot = lv.free_spot_near(base[0] + 1, base[1], 2)
        lv.add_actor(h)
        lv.move_actor(h, *spot)
        h.hp = 1
        combat.kill_human_other(g, h, z)
        self.assertEqual(lv.corpses[spot][1], 2)
        lv.remove_actor(z)
        g.clock.turn += 60
        g._rising_dead()
        self.assertTrue(any(isinstance(a, Zombie) and a.pos == spot for a in lv.actors))

    def test_player_kill_of_human_does_not_rise_on_rage(self):
        g = make_game(era="modern", zombies="rage", seed=3)
        lv = clear(g)
        h = make_raider(g, 0, 0)
        spot = lv.free_spot_near(*open_spot(g, lv), 2)
        lv.add_actor(h)
        lv.move_actor(h, *spot)
        combat.kill_human(g, h)
        self.assertEqual(lv.corpses[spot][1], True)

    def test_patrols_are_spawned_and_walk(self):
        g = make_game(era="modern", zombies="classic", seed=7)
        patrols = [a for a in g.world.level.actors if isinstance(a, Human) and a.role in ("scout", "soldier")]
        self.assertGreaterEqual(len(patrols), 4)
        self.assertTrue(all(not a.hostile for a in patrols))
        self.assertEqual({a.faction for a in patrols}, {"enclave", "military"})

    def test_patrol_walks_toward_waypoint(self):
        h = self._put(make_patrol(self.g, "scout", 0, 0, 9))
        goal = (h.x + 14, h.y)
        self.g.patrol_goals[9] = goal
        start = ai.cheb(h.pos, goal)
        tick(self.g, 20)
        self.assertLess(ai.cheb(h.pos, goal), start)

    def test_talking_to_patrol_gives_one_lead(self):
        h = self._put(make_patrol(self.g, "scout", 0, 0, 1))
        leads = lambda: sum(1 for q in self.g.pois.values() if q.lead)
        before = leads()
        first = services.talk_patrol(self.g, h)
        self.assertEqual(leads(), before + 1)
        second = services.talk_patrol(self.g, h)
        self.assertEqual(leads(), before + 1)
        self.assertNotEqual(first, second)

    def test_patrol_refuses_the_inhuman(self):
        h = self._put(make_patrol(self.g, "soldier", 0, 0, 1))
        self.g.player.humanity = 5
        before = sum(1 for q in self.g.pois.values() if q.lead)
        services.talk_patrol(self.g, h)
        self.assertEqual(sum(1 for q in self.g.pois.values() if q.lead), before)

    def test_gunfight_noise_attracts_zombies(self):
        g = make_game(era="modern", zombies="classic", seed=3)
        lv = clear(g)
        base = open_spot(g, lv)
        z = spawn_zombie(g, lv, (base[0], base[1]), "walker", dormant=False)
        z.state = "idle"
        shooter = make_patrol(g, "soldier", 0, 0, 1)
        spot = lv.free_spot_near(base[0] + 6, base[1], 2)
        lv.add_actor(shooter)
        lv.move_actor(shooter, *spot)
        victim = make_raider(g, 0, 0)
        spot2 = lv.free_spot_near(base[0] + 8, base[1], 2)
        lv.add_actor(victim)
        lv.move_actor(victim, *spot2)
        for _ in range(5):
            combat.attack_actor(g, shooter, victim, ranged=True)
            if victim.hp <= 0:
                break
        self.assertEqual(z.state, "investigate")


class Openings(unittest.TestCase):
    def test_every_opening_every_era_builds(self):
        for era in content.ERAS:
            for oid in content.OPENINGS:
                g = make_game(era=era, opening=oid, seed=4, zombies="night" if oid == "vigil" else "classic")
                self.assertEqual(g.opening_id, oid)
                self.assertEqual(len(g.intro_pages), 3)
                self.assertTrue(all(len(t) > 40 for _, t in g.intro_pages))
                self.assertLess(g.clock.hour, 19 if g.profile.sun_burn else 24)

    def test_random_opening_is_stable_per_seed_and_does_not_change_the_world(self):
        a = make_game(seed=11, opening="random")
        b = make_game(seed=11, opening="random")
        self.assertEqual(a.opening_id, b.opening_id)
        c = make_game(seed=11, opening="market")
        self.assertEqual([q.name for q in a.pois.values()], [q.name for q in c.pois.values()])

    def test_opening_effects(self):
        base = make_game(seed=5, opening="rounds", origin="scholar")
        study = make_game(seed=5, opening="study", origin="scholar")
        self.assertGreater(study.know.known_count() if hasattr(study.know, "known_count") else len(study.know.known),
                           base.know.known_count() if hasattr(base.know, "known_count") else len(base.know.known))
        market = make_game(seed=5, opening="market")
        plain = make_game(seed=5, opening="meal")
        self.assertEqual(market.player.coins, plain.player.coins + 14)
        hunt = make_game(seed=5, opening="hunt", origin="scholar")
        ids = [i.id for i in hunt.player.inventory]
        self.assertIn(hunt.era.defaults["ranged"], ids)
        self.assertIn(hunt.item_def(hunt.era.defaults["ranged"]).ammo, ids)
        vigil = make_game(seed=5, opening="vigil", origin="scholar", zombies="classic")
        self.assertGreater(vigil.player.humanity, plain.player.humanity)
        watch = make_game(seed=5, opening="watch", origin="scholar")
        self.assertIsNotNone(watch.player.armor)

    def test_unknown_opening_rejected(self):
        with self.assertRaises(KeyError):
            make_game(opening="nope")

    def test_scene_texts_exist_for_every_era(self):
        for o in content.OPENINGS.values():
            self.assertEqual(set(o.scenes), set(content.ERAS))

    def test_origin_affinity_biases_choice(self):
        from collections import Counter
        picks = Counter(make_game(seed=s, origin="medic").opening_id for s in range(60, 120))
        self.assertGreater(picks["rounds"], picks["watch"])


if __name__ == "__main__":
    unittest.main()
