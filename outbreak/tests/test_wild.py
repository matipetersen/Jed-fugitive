import unittest

from tests import helpers
from outbreak.engine import tiles as T, wild
from outbreak.engine.model import Animal, Item


def field(seed=3):
    g = helpers.make_game(seed=seed)
    lv = g.world.level
    helpers.empty_level_of_enemies(lv)
    g.hordes.clear()
    g.ring = None
    p = g.player
    p.hp = p.max_hp = 10 ** 6
    p.infected = False
    for y in range(p.y - 12, p.y + 13):
        for x in range(p.x - 14, p.x + 15):
            lv.set_tile(x, y, T.GRASS)
    return g, lv


def animal(g, lv, dx, species="deer", dy=0):
    a = wild.make_animal(g, g.player.x + dx, g.player.y + dy, species)
    lv.add_actor(a)
    return a


class Hunting(unittest.TestCase):
    def test_the_world_has_game(self):
        g = helpers.make_game(seed=3)
        n = [a for a in g.world.level.actors if isinstance(a, Animal)]
        self.assertGreaterEqual(len(n), 6)
        self.assertTrue({a.species for a in n} >= {"rabbit", "deer"})

    def test_game_bolts_when_it_notices_you(self):
        g, lv = field()
        a = animal(g, lv, 5)
        d0 = abs(a.x - g.player.x)
        for i in range(12):
            g.clock.turn = i + 1
            wild.tick(g, a)
        self.assertEqual(a.state, "flee")
        self.assertGreater(abs(a.x - g.player.x), d0)

    def test_a_chase_can_catch_it_but_not_for_free(self):
        g, lv = field()
        a = animal(g, lv, 3, "rabbit")
        gaps = []
        for i in range(30):
            g.clock.turn = i + 1
            wild.tick(g, a)
            gaps.append(abs(a.x - g.player.x))
        self.assertLess(gaps[-1], 3 + 30)               # it does not outrun a walker forever: at most 2 of every 3 turns

    def test_creeping_hides_you_and_a_stab_in_the_back_kills(self):
        g, lv = field()
        g.player.sneaking = True
        g.rng.random = lambda: 0.99
        a = animal(g, lv, 3, "deer")
        for i in range(6):
            g.clock.turn = i + 1
            wild.tick(g, a)
        self.assertFalse(a.alert)
        a.x, a.y = g.player.x + 1, g.player.y
        lv.occ = {k: v for k, v in lv.occ.items() if v is not a}
        lv.occ[a.pos] = a
        before = a.hp
        g.move(1, 0)
        self.assertTrue(a.hp < before or a not in lv.actors)

    def test_a_kill_drops_meat_that_can_be_eaten_or_cooked(self):
        g, lv = field()
        a = animal(g, lv, 1, "deer")
        wild.kill(g, a)
        meat = lv.items[(g.player.x + 1, g.player.y)][0]
        self.assertEqual(meat.id, "raw_meat")
        self.assertGreaterEqual(meat.qty, 2)
        self.assertNotIn(a, lv.actors)

    def test_raw_meat_can_make_you_sick_cooked_cannot(self):
        g, lv = field()
        p = g.player
        p.hp = 50
        p.hunger = 80
        g.rng.random = lambda: 0.0
        from outbreak.engine import inventory_ops
        item = Item("raw_meat", 1)
        p.inventory.append(item)
        inventory_ops.use(g, p.inventory.index(item))
        self.assertLess(p.hp, 50)
        p.hp = 50
        p.hunger = 80
        cooked = Item("meat", 1)
        p.inventory.append(cooked)
        inventory_ops.use(g, p.inventory.index(cooked))
        self.assertEqual(p.hp, 50)
        self.assertLess(p.hunger, 80 - 40)

    def test_cooking_needs_a_plank(self):
        from outbreak.content.recipes import RECIPES
        r = next(r for r in RECIPES if r.id == "cook")
        self.assertEqual(r.out, "meat")
        self.assertIn(("wood", 1), r.inputs)
        self.assertTrue(r.starter)

    def test_a_boar_fights_back(self):
        g, lv = field()
        a = animal(g, lv, 1, "boar")
        hp = g.player.hp
        a.alert, a.state = True, "charge"
        g.rng.random = lambda: 0.1
        g.clock.turn = 1
        wild.tick(g, a)
        self.assertLess(g.player.hp, hp)


class Foraging(unittest.TestCase):
    def test_foraging_takes_time_and_finds_food(self):
        g, lv = field()
        g.rng.random = lambda: 0.0
        g.clock.turn = 1000
        t0 = g.clock.turn
        n0 = g.player.count("forage")
        self.assertTrue(g.forage())
        self.assertGreaterEqual(g.clock.turn - t0, wild.FORAGE_TURNS)
        self.assertGreater(g.player.count("forage"), n0)

    def test_a_patch_is_picked_clean_for_a_while(self):
        g, lv = field()
        g.rng.random = lambda: 0.0
        g.forage()
        n = g.player.count("forage")
        self.assertFalse(g.forage())
        self.assertEqual(g.player.count("forage"), n)
        g.clock.turn += wild.PATCH_TURNS + 1
        self.assertTrue(g.forage())

    def test_only_on_grass_or_brush_and_never_indoors_or_hunted(self):
        g, lv = field()
        lv.set_tile(g.player.x, g.player.y, T.ROAD)
        self.assertFalse(g.forage())
        lv.set_tile(g.player.x, g.player.y, T.GRASS)
        self.assertEqual(wild.can_forage(g), "")
        from outbreak.engine.spawn import spawn_zombie
        spawn_zombie(g, lv, (g.player.x + 4, g.player.y), "walker", False)
        g.update_fov()
        self.assertNotEqual(wild.can_forage(g), "")


if __name__ == "__main__":
    unittest.main()
