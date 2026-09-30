import random

from jedi_fugitive.game import form_combat, jedi_skills, languages, tech
from jedi_fugitive.game.combat import player_attack
from jedi_fugitive.game.npc_encounters import NPC
from jedi_fugitive.game.player import Player
from jedi_fugitive.items.weapons import WEAPONS


class Msgs:
    def __init__(self): self.lines = []
    def add(self, m, *a, **k): self.lines.append(m)


class UI:
    def __init__(self): self.messages = Msgs()


class Foe:
    def __init__(self, x, y, hp=100):
        self.x, self.y, self.hp, self.name, self.evasion = x, y, hp, "Foe", 0


class G:
    def __init__(self, player, enemies):
        self.player, self.enemies, self.ui = player, enemies, UI()


def saber_player(form):
    p = Player(5, 5)
    saber = next(w for w in WEAPONS if "lightsaber" in w.name.lower())
    p.equipped_weapon = saber
    p.active_form = form
    p.accuracy = 999
    return p


def test_form_bonuses_only_with_lightsaber():
    p = saber_player("Soresu")
    assert form_combat.defense_bonus(p) == 4 and form_combat.evasion_bonus(p) == 3
    p.equipped_weapon = None
    assert form_combat.defense_bonus(p) == 0 and form_combat.total_defense(p) == p.defense


def test_shien_name_is_normalised():
    assert form_combat.form_key(saber_player("Shien / Djem So")) == "Shien"
    assert form_combat.form_key(saber_player("Juyo / Vaapad")) == "Juyo"


def test_makashi_duelist_beats_crowd():
    random.seed(1)
    p = saber_player("Makashi")
    lone = Foe(6, 5)
    d1, _ = form_combat.modify_player_attack(p, lone, 20, G(p, [lone]), rng=random.Random(9))
    crowd = [Foe(6, 5), Foe(6, 6), Foe(5, 6), Foe(4, 5)]
    d2, _ = form_combat.modify_player_attack(p, crowd[0], 20, G(p, crowd), rng=random.Random(9))
    assert d1 > d2


def test_shii_cho_cleave_hits_second_enemy():
    p = saber_player("Shii-Cho")
    a, b = Foe(6, 5), Foe(6, 6)
    g = G(p, [a, b])
    victim = form_combat.cleave(p, a, 10, g, g.ui.messages)
    assert victim is b and b.hp == 95


def test_juyo_scales_with_corruption_and_feeds_dark_on_crit():
    p = saber_player("Juyo / Vaapad")
    p.dark_corruption = 0
    low, _ = form_combat.modify_player_attack(p, Foe(6, 5), 10, None, rng=random.Random(5))
    p.dark_corruption = 90
    high, _ = form_combat.modify_player_attack(p, Foe(6, 5), 10, None, rng=random.Random(5))
    assert high > low


def test_shien_counters_a_miss():
    p = saber_player("Shien / Djem So")
    foe = Foe(6, 5)
    g = G(p, [foe])
    class Always:  # rng that always rolls low
        def random(self): return 0.0
    assert form_combat.on_enemy_miss(g, foe, rng=Always()) and foe.hp < 100


def test_player_attack_uses_form_mechanics():
    random.seed(2)
    p = saber_player("Ataru")
    foe = Foe(6, 5)
    g = G(p, [foe])
    hit, dmg = player_attack(p, foe, g.ui.messages, g)
    assert hit and foe.hp == 100 - dmg


def test_artificer_tree_discounts_and_tech_boosts():
    p = Player(0, 0)
    p.skill_points = 10
    assert jedi_skills.learn(p, "salvage")[0] and jedi_skills.learn(p, "field_medic")[0]
    cost = tech.effective_cost(p, {"Scrap Metal": 2, "Power Cell": 1})
    assert cost == {"Scrap Metal": 1, "Power Cell": 1}
    p.tech = {"medunit": 1}
    p.hp, p.max_hp = 1, 100

    class GG: turn_count = 0
    ok, msgs = tech.use(p, GG(), "medunit")
    assert ok and p.hp == 1 + 15 + 8
    assert tech.cooldown_left(p, GG(), "medunit") > 0


def test_teachers_teach_and_consult_archive():
    p = Player(0, 0)
    npc = NPC("archivist", 10, 10)
    opts = npc.get_available_interactions(p)
    assert opts[0].startswith("Ask to be taught")
    before = len(languages.known_words(p, npc.teaches))
    npc.handle_interaction(0, p)
    assert len(languages.known_words(p, npc.teaches)) > before
    npc.handle_interaction(0, p)
    assert "all I can" in npc.handle_interaction(0, p)  # third lesson refused
    # consult: archive an inscription in that language, then ask
    q = Player(0, 0)
    languages.read_inscription(q, (1, 1), npc.teaches, "T", "Power and fear in the dark.")
    got = languages.consult_archive(q, npc.teaches, 3, random.Random(1))
    assert got and set(got) <= {"power", "fear", "dark"}


def test_tinker_barter_and_advice():
    p = Player(0, 0)
    npc = NPC("rakatan_tinker", 3, 3)
    assert npc.teaches == "rakatan"
    assert "Bring me" in npc.handle_interaction(2, p)
    p.inventory = [{"name": "Scrap Metal", "type": "material"}, {"name": "Fused Wire", "type": "material"}]
    before = len(languages.known_words(p, "rakatan"))
    npc.handle_interaction(2, p)
    assert len(languages.known_words(p, "rakatan")) > before and p.inventory == []
    assert "Press I" in npc.handle_interaction(3, p)
