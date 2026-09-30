"""Technology: devices built from salvage and upgraded with Rakatan know-how.

Devices have three tiers. Tier 1 needs only materials; higher tiers also need
fluency in Rakatan (the Infinite Empire's machine-language), so language and
technology feed each other: the more of their tongue you read, the better the
gadgets you can build.

Passive devices apply stat bonuses; active devices are used from the Tech screen
(or their hotkeys) and run on cooldowns measured in world ticks.
"""
from jedi_fugitive.game import languages

# fluency in Rakatan required per tier
TIER_FLUENCY = {1: 0.0, 2: 0.15, 3: 0.30}


class Device:
    def __init__(self, id, name, desc, costs, kind="passive", cooldown=0):
        self.id = id
        self.name = name
        self.desc = desc
        self.costs = costs          # {tier: {material name: count}}
        self.kind = kind            # 'passive' | 'active'
        self.cooldown = cooldown    # ticks (active devices)


DEVICES = {
    "translator": Device(
        "translator", "Holo-Translator",
        "Cross-references glyphs against every text you have seen. T1 +10%, T2 +20%, T3 +30% study "
        "success; T2 lets each study decode a second word; T3 adds a third.",
        {1: {"Fused Wire": 2, "Focusing Lens": 1},
         2: {"Advanced Circuitry": 2, "Power Cell": 1, "Focusing Lens": 1},
         3: {"Quantum Processor": 1, "Neural Interface": 1, "Advanced Circuitry": 1}}),
    "scanner": Device(
        "scanner", "Signal Scanner",
        "Pings for ancient inscriptions. Range 40 / 70 / 110 tiles. Active (cooldown 25 ticks).",
        {1: {"Scrap Metal": 2, "Fused Wire": 1, "Power Cell": 1},
         2: {"Sensor Array": 1, "Advanced Circuitry": 1},
         3: {"Sensor Array": 1, "Quantum Processor": 1, "Compact Power Core": 1}},
        kind="active", cooldown=25),
    "emitter": Device(
        "emitter", "Kinetic Shield Emitter",
        "A belt-mounted barrier. +1 / +2 / +3 defense.",
        {1: {"Scrap Metal": 2, "Power Cell": 1},
         2: {"Plasteel Composite": 2, "Advanced Circuitry": 1},
         3: {"Phrik Alloy": 1, "Compact Power Core": 1, "Reflective Coating": 1}}),
    "medunit": Device(
        "medunit", "Field Med-Unit",
        "Injects stimulants and sealants. Heals 15 / 30 / 50 HP. Active (cooldown 60 ticks).",
        {1: {"Scrap Metal": 1, "Fused Wire": 1},
         2: {"Advanced Circuitry": 1, "Power Cell": 1},
         3: {"Synthetic Crystal": 1, "Stabilized Plasma": 1}},
        kind="active", cooldown=60),
    "focus": Device(
        "focus", "Kyber Focus Lattice",
        "A resonance lattice worn at the wrist. +10 / +20 / +30 max Force energy and +5 regeneration at T2+.",
        {1: {"Focusing Lens": 1, "Fused Wire": 1},
         2: {"Synthetic Crystal": 1, "Power Cell": 1},
         3: {"Kyber Crystal": 1, "Compact Power Core": 1}}),
}

SCAN_RANGE = {1: 40, 2: 70, 3: 110}
MED_HEAL = {1: 15, 2: 30, 3: 50}


# ---------------------------------------------------------------- state
def ensure_state(player):
    if not hasattr(player, "tech") or not isinstance(player.tech, dict):
        player.tech = {}
    if not hasattr(player, "tech_cooldowns") or not isinstance(player.tech_cooldowns, dict):
        player.tech_cooldowns = {}
    if not hasattr(player, "_tech_applied"):
        player._tech_applied = {}
    return player.tech


def tier(player, device_id):
    return ensure_state(player).get(device_id, 0)


def translator_bonus(player, lang_id=None):
    return 0.10 * tier(player, "translator")


def translator_extra_words(player):
    return max(0, tier(player, "translator") - 1)


def apply_stats(player):
    """Fold passive device bonuses into the player's stats (idempotent)."""
    ensure_state(player)
    t = tier(player, "emitter")
    f = tier(player, "focus")
    new = {"defense": t, "max_force": 10 * f, "force_regen": 5 if f >= 2 else 0}
    old = player._tech_applied
    d = new["defense"] - old.get("defense", 0)
    if d:
        player.defense = getattr(player, "defense", 0) + d
        bs = getattr(player, "_base_stats", None)
        if isinstance(bs, dict) and "defense" in bs:
            bs["defense"] += d
    d = new["max_force"] - old.get("max_force", 0)
    if d:
        player.max_force_energy = getattr(player, "max_force_energy", 100) + d
        player.force_energy = min(player.max_force_energy, getattr(player, "force_energy", 0) + max(0, d))
    d = new["force_regen"] - old.get("force_regen", 0)
    if d:
        player.force_regen_peaceful = getattr(player, "force_regen_peaceful", 1) + d
    player._tech_applied = new


# ---------------------------------------------------------------- building
def next_cost(player, device_id):
    dev = DEVICES[device_id]
    t = tier(player, device_id) + 1
    return dev.costs.get(t), t


def can_build(player, device_id):
    """(ok, reason)."""
    from jedi_fugitive.items.crafting import check_materials
    dev = DEVICES.get(device_id)
    if dev is None:
        return False, "Unknown device."
    cost, t = next_cost(player, device_id)
    if cost is None:
        return False, "Fully upgraded."
    need = TIER_FLUENCY[t]
    have = languages.fluency(player, "rakatan")
    if have + 1e-9 < need:
        return False, f"Needs Rakatan fluency {int(need * 100)}% (you have {int(have * 100)}%)."
    inv = getattr(player, "inventory", None) or []
    if not check_materials(inv, cost):
        return False, "Missing: " + ", ".join(f"{c}x {n}" for n, c in cost.items())
    return True, ""


def build(player, device_id):
    """Consume materials and raise the device one tier. Returns (ok, message)."""
    from jedi_fugitive.items.crafting import consume_materials
    ok, why = can_build(player, device_id)
    if not ok:
        return False, why
    cost, t = next_cost(player, device_id)
    player.inventory = consume_materials(player.inventory, cost)
    player.tech[device_id] = t
    apply_stats(player)
    return True, f"{DEVICES[device_id].name} is now Tier {t}."


# ---------------------------------------------------------------- active use
def _now(game):
    return int(getattr(game, "turn_count", 0) or 0)


def cooldown_left(player, game, device_id):
    ensure_state(player)
    return max(0, player.tech_cooldowns.get(device_id, 0) - _now(game))


def use(player, game, device_id):
    """Use an active device. Returns (ok, [messages])."""
    ensure_state(player)
    t = tier(player, device_id)
    dev = DEVICES.get(device_id)
    if dev is None or t == 0:
        return False, ["You have not built that device."]
    if dev.kind != "active":
        return False, [f"{dev.name} works on its own."]
    left = cooldown_left(player, game, device_id)
    if left:
        return False, [f"{dev.name} is recharging ({left} ticks)."]
    if device_id == "medunit":
        heal = MED_HEAL[t]
        before = player.hp
        player.hp = min(player.max_hp, player.hp + heal)
        player.tech_cooldowns[device_id] = _now(game) + dev.cooldown
        return True, [f"The Med-Unit hisses. +{player.hp - before} HP."]
    if device_id == "scanner":
        msgs = scan_inscriptions(player, game, SCAN_RANGE[t])
        player.tech_cooldowns[device_id] = _now(game) + dev.cooldown
        return True, msgs
    return False, ["Nothing happens."]


def scan_inscriptions(player, game, radius):
    """Report the nearest unread / untranslated inscriptions within radius."""
    px, py = int(player.x), int(player.y)
    found = []
    for (x, y), info in (getattr(game, "map_landmarks", {}) or {}).items():
        if "sith_lore" not in info:
            continue
        d = abs(x - px) + abs(y - py)
        if d > radius:
            continue
        key = (x, y)
        if key in getattr(player, "translated_entries", set()):
            continue
        found.append((d, x, y, languages.language_for(info, key)))
    if not found:
        return ["The scanner finds no untranslated inscriptions in range."]
    found.sort()
    msgs = [f"Scanner: {len(found)} untranslated inscription(s) within {radius} tiles."]
    for d, x, y, lid in found[:3]:
        ns = ("north" if y < py else "south") if abs(y - py) > 2 else ""
        ew = ("west" if x < px else "east") if abs(x - px) > 2 else ""
        direction = (ns + ("-" if ns and ew else "") + ew) or "here"
        msgs.append(f"  {languages.LANGUAGES[lid]['name']} inscription, {d} tiles {direction}.")
    # remember them on the map so the player can navigate back (reuses explored marks if present)
    return msgs


def device_rows(player):
    """[(id, name, tier, description, status text)] for the tech screen."""
    ensure_state(player)
    rows = []
    for did, dev in DEVICES.items():
        t = tier(player, did)
        ok, why = can_build(player, did)
        cost, nt = next_cost(player, did)
        if cost is None:
            status = "MAX"
        elif ok:
            status = f"Build T{nt}: " + ", ".join(f"{c}x {n}" for n, c in cost.items())
        else:
            status = f"T{nt}: {why}"
        rows.append((did, dev.name, t, dev.desc, status))
    return rows


def mark_applied(player):
    """After loading a save: stats already contain the device bonuses."""
    ensure_state(player)
    t = tier(player, "emitter")
    f = tier(player, "focus")
    bs = getattr(player, "_base_stats", None)
    if isinstance(bs, dict) and "defense" in bs:
        bs["defense"] += t
    player._tech_applied = {"defense": t, "max_force": 10 * f, "force_regen": 5 if f >= 2 else 0}
