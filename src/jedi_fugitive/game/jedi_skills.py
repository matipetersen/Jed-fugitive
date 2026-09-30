"""Jedi skill trees: depth beyond level-ups.

Three trees - Way of the Blade, Force Mastery and Lorekeeper - made of ranked
nodes with prerequisites, level gates and light/dark alignment gates. Skill
points come from level-ups, from fully translating ancient inscriptions and from
milestones. Nodes grant

* static stat bonuses (applied through apply_stats, kept in sync with equipment),
* dynamic bonuses read by other systems through bonus(player, key), and
* Force abilities (unlock).
"""
import copy

STAT_KEYS = ("attack", "defense", "accuracy", "evasion", "max_hp")

LIGHT_MAX = 35   # dark_corruption at or below this counts as the Light path
DARK_MIN = 45    # at or above this counts as the Dark path


class Node:
    def __init__(self, id, name, tree, desc, max_rank=1, cost=1, requires=(), min_level=1,
                 alignment=None, effect=None, unlock=None):
        self.id = id
        self.name = name
        self.tree = tree
        self.desc = desc
        self.max_rank = max_rank
        self.cost = cost
        self.requires = tuple(requires)     # ((node_id, rank), ...)
        self.min_level = min_level
        self.alignment = alignment          # None / 'light' / 'dark'
        self.effect = effect or {}          # per-rank bonuses
        self.unlock = unlock                # Force ability name granted at rank 1


TREES = {
    "blade": "Way of the Blade",
    "force": "Force Mastery",
    "sage": "Lorekeeper",
    "artificer": "Artificer",
}

_NODES = [
    # ---------------------------------------------------------- Way of the Blade
    Node("soresu", "Soresu Guard", "blade", "Patient defensive form. +1 defense per rank.", 3,
         effect={"defense": 1}),
    Node("makashi", "Makashi Precision", "blade", "Elegant dueling form. +3 accuracy per rank.", 3,
         effect={"accuracy": 3}),
    Node("ataru", "Ataru Fury", "blade", "Acrobatic aggression. +1 attack per rank.", 3,
         requires=(("makashi", 1),), effect={"attack": 1}),
    Node("shien", "Shien Deflection", "blade", "Turn blaster fire aside. +2 evasion per rank.", 3,
         requires=(("soresu", 2),), effect={"evasion": 2}),
    Node("niman", "Niman Harmony", "blade", "Balanced form of the Light. +1 defense, +4 HP per rank.", 2,
         requires=(("soresu", 2),), alignment="light", effect={"defense": 1, "max_hp": 4}),
    Node("juyo", "Juyo Ferocity", "blade", "Raw fury of the Dark. +2 attack per rank.", 2,
         requires=(("ataru", 2),), alignment="dark", effect={"attack": 2}),
    Node("form_mastery", "Form Mastery", "blade", "Every form flows into the next. +2 attack, +5 accuracy.", 1,
         cost=2, requires=(("ataru", 3),), min_level=8, effect={"attack": 2, "accuracy": 5}),

    Node("precision", "Precision Strike", "blade", "Find the gap in any guard. +3% critical chance per rank.", 3,
         requires=(("makashi", 1),), effect={"crit": 0.03}),
    Node("riposte", "Riposte", "blade", "Turn a missed blow into a counter. +8% counter chance per rank.", 3,
         requires=(("shien", 1),), effect={"counter": 0.08}),

    # ---------------------------------------------------------- Force Mastery
    Node("reserve", "Force Reserve", "force", "A deeper well of the Force. +10 max Force energy per rank.", 4,
         effect={"max_force": 10}),
    Node("attune", "Attunement", "force", "Recover Force energy faster. +4 regeneration per rank.", 3,
         effect={"force_regen": 4}),
    Node("efficiency", "Efficiency", "force", "Waste nothing. -7% Force costs per rank.", 3,
         requires=(("reserve", 1),), effect={"force_cost": 0.07}),
    Node("speed", "Kinetic Discipline", "force", "Unlocks Force Speed.", 1,
         requires=(("reserve", 1),), unlock="Force Speed"),
    Node("sight", "Farsight", "force", "Unlocks Force Sight.", 1,
         requires=(("attune", 1),), unlock="Force Sight"),
    Node("blink", "Sudden Step", "force", "Unlocks Force Blink.", 1,
         requires=(("efficiency", 1),), min_level=6, unlock="Force Blink"),
    Node("burst", "Shockwave", "force", "Unlocks Force Burst.", 1,
         requires=(("reserve", 3),), min_level=8, unlock="Force Burst"),
    Node("ward", "Serene Warding", "force", "Unlocks Protect and Force Stun.", 1,
         requires=(("attune", 2),), alignment="light", unlock="Force Stun"),
    Node("choke", "Grasping Dark", "force", "Unlocks Force Choke.", 1,
         requires=(("reserve", 2),), alignment="dark", unlock="Choke"),
    Node("drain", "Hollow Hunger", "force", "Unlocks Force Drain.", 1,
         requires=(("choke", 1),), min_level=7, alignment="dark", unlock="Drain"),

    # ---------------------------------------------------------- Lorekeeper
    Node("tongues", "Ancient Tongues", "sage", "Decode dead languages. +8% study success per rank.", 4,
         effect={"translate": 0.08}),
    Node("ear", "Linguist's Ear", "sage", "Unknown words sink in one sighting sooner per rank.", 2,
         requires=(("tongues", 1),), effect={"exposure": 1}),
    Node("attunement_holo", "Holocron Attunement", "sage", "Each study attempt can decode one extra word.", 1,
         cost=2, requires=(("tongues", 2),), min_level=4, effect={"study_words": 1}),
    Node("serenity", "Serenity", "sage", "Stress washes off you. -5% stress gain per rank.", 4,
         effect={"stress_resist": 0.05}),
    Node("insight", "Insight", "sage", "See further. +1 sight radius per rank.", 2,
         requires=(("serenity", 1),), effect={"sight": 1}),
    Node("trance", "Healing Trance", "sage", "Mend the body with the Force. +5 max HP per rank.", 3,
         effect={"max_hp": 5}),

    # ---------------------------------------------------------- Artificer
    Node("salvage", "Efficient Assembly", "artificer", "Devices need 1 less of each multi-unit material per rank.", 2,
         effect={"tech_discount": 1}),
    Node("rakatan_insight", "Rakatan Insight", "artificer", "Machine-tongue comes easier: +5% effective Rakatan fluency for building, per rank.", 3,
         effect={"tech_fluency": 0.05}),
    Node("overclock", "Overclock", "artificer", "Active devices recharge 15% faster per rank.", 3,
         requires=(("salvage", 1),), effect={"cooldown": 0.15}),
    Node("field_medic", "Field Medic", "artificer", "Med-Unit heals +8 HP per rank.", 3,
         effect={"med": 8}),
    Node("deep_scan", "Deep Scan", "artificer", "Scanner range +15 tiles per rank.", 3,
         requires=(("rakatan_insight", 1),), effect={"scan": 15}),
    Node("plating", "Composite Plating", "artificer", "Reinforce your gear. +1 defense, +3 HP per rank.", 2,
         requires=(("salvage", 1),), effect={"defense": 1, "max_hp": 3}),
]
NODES = {n.id: n for n in _NODES}


# ---------------------------------------------------------------- state
def ensure_state(player):
    if not hasattr(player, "skills") or not isinstance(player.skills, dict):
        player.skills = {}
    if not hasattr(player, "skill_points") or not isinstance(player.skill_points, int):
        player.skill_points = 2  # a starting pair so the tree is usable immediately
    if not hasattr(player, "_skill_applied"):
        player._skill_applied = {}
    return player.skills


def rank(player, node_id):
    return ensure_state(player).get(node_id, 0)


def alignment_of(player):
    c = getattr(player, "dark_corruption", 0) or 0
    if c <= LIGHT_MAX:
        return "light"
    if c >= DARK_MIN:
        return "dark"
    return "neutral"


def bonus(player, key):
    """Total dynamic bonus for a key across all learned nodes."""
    total = 0
    skills = ensure_state(player)
    for nid, r in skills.items():
        n = NODES.get(nid)
        if n and key in n.effect:
            total += n.effect[key] * r
    return total


def can_learn(player, node_id):
    """(ok, reason)."""
    n = NODES.get(node_id)
    if n is None:
        return False, "Unknown skill."
    ensure_state(player)
    r = rank(player, node_id)
    if r >= n.max_rank:
        return False, "Already mastered."
    if getattr(player, "level", 1) < n.min_level:
        return False, f"Requires level {n.min_level}."
    for rid, rr in n.requires:
        if rank(player, rid) < rr:
            return False, f"Requires {NODES[rid].name} rank {rr}."
    if n.alignment and alignment_of(player) != n.alignment:
        want = "Light" if n.alignment == "light" else "Dark"
        return False, f"Requires a {want} Side path."
    if player.skill_points < n.cost:
        return False, f"Needs {n.cost} skill point(s)."
    return True, ""


def learn(player, node_id, game=None):
    """Spend points on a node. Returns (ok, message)."""
    ok, why = can_learn(player, node_id)
    if not ok:
        return False, why
    n = NODES[node_id]
    player.skill_points -= n.cost
    player.skills[node_id] = rank(player, node_id) + 1
    msg = f"Learned {n.name} (rank {player.skills[node_id]}/{n.max_rank})."
    if n.unlock and player.skills[node_id] == 1:
        if _unlock_ability(player, n.unlock):
            msg += f" You can now use {n.unlock}."
    apply_stats(player)
    return True, msg


def _unlock_ability(player, name):
    try:
        from jedi_fugitive.game.force_abilities import FORCE_ABILITIES
        abilities = getattr(player, "force_abilities", None)
        if abilities is None:
            player.force_abilities = abilities = {}
        names = [name]
        if name == "Force Stun":
            names.append("Protect")
        got = False
        for want in names:
            for a in FORCE_ABILITIES or []:
                if getattr(a, "name", None) == want and want not in abilities:
                    pa = copy.deepcopy(a)
                    pa.unlocked = True
                    abilities[want] = pa
                    got = True
        return got
    except Exception:
        return False


def grant_points(player, n=1, reason=None):
    ensure_state(player)
    player.skill_points += n
    return f"+{n} Skill Point{'s' if n != 1 else ''}" + (f" ({reason})" if reason else "") + ". Press O to spend."


# ---------------------------------------------------------------- effects
def apply_stats(player):
    """Idempotently apply static stat bonuses (also folded into _base_stats)."""
    ensure_state(player)
    new = {k: 0 for k in STAT_KEYS}
    new["max_force"] = int(bonus(player, "max_force"))
    new["sight"] = int(bonus(player, "sight"))
    for k in STAT_KEYS:
        new[k] = int(bonus(player, k))
    old = player._skill_applied
    for k in STAT_KEYS:
        d = new[k] - old.get(k, 0)
        if not d:
            continue
        setattr(player, k, getattr(player, k, 0) + d)
        bs = getattr(player, "_base_stats", None)
        if isinstance(bs, dict) and k in bs:
            bs[k] = bs[k] + d
        if k == "max_hp":
            player.hp = min(player.max_hp, getattr(player, "hp", 0) + max(0, d))
    d = new["max_force"] - old.get("max_force", 0)
    if d:
        player.max_force_energy = getattr(player, "max_force_energy", 100) + d
        player.force_energy = min(player.max_force_energy, getattr(player, "force_energy", 0) + max(0, d))
    d = new["sight"] - old.get("sight", 0)
    if d:
        player.los_radius = getattr(player, "los_radius", 6) + d
    player._skill_applied = new


def force_cost_multiplier(player):
    return max(0.5, 1.0 - bonus(player, "force_cost"))


def stress_multiplier(player):
    return max(0.4, 1.0 - bonus(player, "stress_resist"))


def on_level_up(player):
    ensure_state(player)
    player.skill_points += 1
    return "You gain a Skill Point. Press O to spend it."


# ---------------------------------------------------------------- UI helpers
def tree_nodes(tree):
    return [n for n in _NODES if n.tree == tree]


def node_line(player, n):
    r = rank(player, n.id)
    ok, why = can_learn(player, n.id)
    mark = "*" if r >= n.max_rank else ("+" if ok else "-")
    tag = f" [{n.alignment}]" if n.alignment else ""
    return f"{mark} {n.name}{tag} {r}/{n.max_rank}", (n.desc + ("" if ok or r >= n.max_rank else f"  ({why})"))


def mark_applied(player):
    """After loading a save: stats already contain the bonuses; just record them
    (and fold them into _base_stats so equipment recalculation keeps them)."""
    ensure_state(player)
    new = {k: int(bonus(player, k)) for k in STAT_KEYS}
    new["max_force"] = int(bonus(player, "max_force"))
    new["sight"] = int(bonus(player, "sight"))
    bs = getattr(player, "_base_stats", None)
    if isinstance(bs, dict):
        for k in STAT_KEYS:
            if k in bs:
                bs[k] += new[k]
    player._skill_applied = new
