import random

from jedi_fugitive.game import languages, jedi_skills, tech
from jedi_fugitive.game.player import Player
from jedi_fugitive.items.crafting import MATERIALS

TEXT = "The Sith seek power in the dark, and fear is their master."


def mat(name):
    for m in MATERIALS:
        if m.name == name:
            return {"name": name, "type": "material"}
    raise KeyError(name)


def fresh():
    p = Player(0, 0)
    p.game = None
    return p


def test_unknown_words_are_alien_and_deterministic():
    p = fresh()
    a, info = languages.render_text(p, "sith", TEXT, observe=False)
    b, _ = languages.render_text(p, "sith", TEXT, observe=False)
    assert a == b and "power" not in a.lower() and "dark" not in a.lower()
    assert "power" in info["unknown"] and "dark" in info["unknown"]


def test_learned_word_shows_in_clear_and_languages_differ():
    p = fresh()
    assert languages.learn_word(p, "sith", "power")
    a, _ = languages.render_text(p, "sith", TEXT, observe=False)
    assert "power" in a and "dark" not in a
    b, _ = languages.render_text(p, "rakatan", TEXT, observe=False)
    assert languages.native_word("sith", "dark") != languages.native_word("rakatan", "dark")
    assert "power" not in b


def test_exposure_teaches_words():
    p = fresh()
    learned = []
    for _ in range(languages.EXPOSURE_TO_LEARN):
        _, info = languages.render_text(p, "sith", "power power", observe=True)
        learned += info["learned"]
    assert "power" in learned and "power" in languages.known_words(p, "sith")


def test_grammar_and_fluency_unlock():
    p = fresh()
    assert "the" not in languages.render_text(p, "sith", "the ", observe=False)[0].split()
    for w in languages.ALL_WORDS[:int(len(languages.ALL_WORDS) * 0.3)]:
        languages.learn_word(p, "sith", w)
    assert languages.render_text(p, "sith", "the ", observe=False)[0].strip() == "the"


def test_study_and_full_translation_rewards():
    p = fresh()
    rng = random.Random(1)
    for w in ("power", "dark", "fear", "master", "sith"):
        languages.learn_word(p, "sith", w)
    xp = p.xp
    for w in languages.CORE_WORDS:
        languages.learn_word(p, "sith", w)
    _, msgs = languages.read_inscription(p, (1, 1), "sith", "Test", TEXT)
    assert (1, 1) in p.translated_entries and any("fully translated" in m for m in msgs)
    assert p.xp >= xp
    # study limit
    for _ in range(languages.STUDY_LIMIT):
        languages.study(p, "sith", (2, 2), TEXT, rng)
    assert "squeezed" in languages.study(p, "sith", (2, 2), TEXT, rng)[0][0]


def test_study_learns_words_with_high_chance():
    p = fresh()
    rng = random.Random(3)
    tech.ensure_state(p)
    p.tech["translator"] = 3
    before = len(languages.known_words(p, "sith"))
    for _ in range(3):
        languages.study(p, "sith", (5, 5), TEXT, rng)
    assert len(languages.known_words(p, "sith")) > before


def test_skill_prereqs_gates_and_stats_are_idempotent():
    p = fresh()
    jedi_skills.ensure_state(p)
    p.skill_points = 10
    assert not jedi_skills.can_learn(p, "ataru")[0]          # needs makashi
    assert jedi_skills.learn(p, "makashi")[0] and jedi_skills.learn(p, "ataru")[0]
    atk, acc = p.attack, p.accuracy
    jedi_skills.apply_stats(p)
    jedi_skills.apply_stats(p)
    assert (p.attack, p.accuracy) == (atk, acc)
    p.dark_corruption = 0
    assert not jedi_skills.can_learn(p, "juyo")[0]           # dark-only
    assert not jedi_skills.can_learn(p, "choke")[0]
    p.dark_corruption = 80
    assert not jedi_skills.can_learn(p, "niman")[0]          # light-only


def test_skill_unlocks_ability_and_force_bonuses():
    p = fresh()
    p.skill_points = 10
    base_max = p.max_force_energy
    assert jedi_skills.learn(p, "reserve")[0] and jedi_skills.learn(p, "speed")[0]
    assert p.max_force_energy == base_max + 10
    assert "Force Speed" in p.force_abilities and p.force_abilities["Force Speed"].unlocked
    ab = p.force_abilities["Force Speed"]
    before = ab.get_actual_cost(p)
    jedi_skills.learn(p, "efficiency")
    assert ab.get_actual_cost(p) < before


def test_tech_needs_materials_and_rakatan_fluency():
    p = fresh()
    assert not tech.can_build(p, "translator")[0]
    p.inventory = [mat("Fused Wire"), mat("Fused Wire"), mat("Focusing Lens")]
    assert tech.build(p, "translator")[0] and tech.tier(p, "translator") == 1
    assert p.inventory == []
    p.inventory = [mat("Advanced Circuitry"), mat("Advanced Circuitry"), mat("Power Cell"), mat("Focusing Lens")]
    ok, why = tech.can_build(p, "translator")
    assert not ok and "Rakatan" in why
    for w in languages.ALL_WORDS[:int(0.16 * len(languages.ALL_WORDS)) + 1]:
        languages.learn_word(p, "rakatan", w)
    assert tech.build(p, "translator")[0] and tech.tier(p, "translator") == 2


def test_passive_tech_stats():
    p = fresh()
    d = p.defense
    p.inventory = [mat("Scrap Metal"), mat("Scrap Metal"), mat("Power Cell")]
    assert tech.build(p, "emitter")[0]
    assert p.defense == d + 1
    tech.apply_stats(p)
    assert p.defense == d + 1


def test_save_roundtrip():
    from jedi_fugitive.game.save_system import _mastery_to_dict, _mastery_from_dict
    import json
    p = fresh()
    p.skill_points = 5
    jedi_skills.learn(p, "soresu")
    languages.learn_word(p, "sith", "power")
    languages.read_inscription(p, (3, 4), "sith", "T", TEXT)
    data = json.loads(json.dumps(_mastery_to_dict(p)))
    q = fresh()
    _mastery_from_dict(q, data)
    assert q.skills == {"soresu": 1} and "power" in languages.known_words(q, "sith")
    assert (3, 4) in q.inscriptions
