"""Moral encounters on the road.  Pure data plus a small effect interpreter.

Effects are dicts: ``humanity``, ``panic``, ``hp``, ``coins``, ``xp``, ``words``,
``heat`` (ints); ``items`` ({id: +/-qty}); ``rep`` ({faction role: delta});
``horde`` / ``raiders`` (spawn); ``reveal`` (a lead on a building).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from outbreak.engine.model import Item
from outbreak.util import weighted_choice


@dataclass(frozen=True)
class Outcome:
    weight: float
    text: str
    fx: Dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Choice:
    label: str
    outcomes: Tuple[Outcome, ...]
    needs: Dict[str, object] = field(default_factory=dict)       # {"items": {id: qty}, "coins": n}


@dataclass(frozen=True)
class EventDef:
    id: str
    title: str
    text: str
    choices: Tuple[Choice, ...]
    weight: float = 1.0
    min_day: int = 1


def _o(text, weight=1.0, **fx) -> Outcome:
    return Outcome(weight, text, fx)


def _c(label, *outcomes, **needs) -> Choice:
    return Choice(label, tuple(outcomes), needs)


EVENTS: Tuple[EventDef, ...] = (
    EventDef("hungry", "A thin stranger",
             "A thin stranger steps out of the ruins with empty hands up. 'Please. Anything to eat?'",
             (_c("Share your food", _o("They weep and press a few {coin} into your hand.", humanity=6, coins=3, xp=5,
                                       items={"food": -1}, rep={"enclave": 3}), items={"food": 1}),
              _c("Send them away", _o("They watch you go without a word.", humanity=-3, panic=3)),
              _c("Take what they carry", _o("They had little. You feel worse than you expected.", humanity=-14,
                                            coins=2, items={"food": 1}, rep={"enclave": -5})))),
    EventDef("bitten", "A bitten survivor",
             "A survivor sits against a wall, a fresh bite on their forearm. 'Don't leave me. Please. I can feel it.'",
             (_c("Bandage them and stay", _o("It was only a scratch. They give you what they can.", 0.55, humanity=6,
                                            coins=3, words=2, items={"bandage": -1}),
                 _o("They were bitten after all. They turn while you work.", 0.45, humanity=2, hp=-6, panic=12,
                    horde=False, items={"bandage": -1}), items={"bandage": 1}),
              _c("End it quickly", _o("A mercy. Your hands shake for a long time.", humanity=0, panic=10, xp=4)),
              _c("Walk away", _o("Their pleading follows you down the street.", humanity=-6, panic=6)))),
    EventDef("toll", "A roadblock",
             "Three {raiders} stand across the road. 'Toll's five {coin}. Or you can leave it all behind.'",
             (_c("Pay the toll", _o("They wave you through, laughing.", humanity=0, coins=-5, rep={"raiders": 3}),
                 coins=5),
              _c("Fight", _o("They go for their weapons.", raiders=3)),
              _c("Slip around", _o("You circle through the ruins unseen.", 0.55, xp=6),
                 _o("A shout goes up: you were seen.", 0.45, raiders=2, heat=8)))),
    EventDef("radio", "A call for help",
             "{radio} carries a faint, repeating call for help from a building nearby.",
             (_c("Go and help", _o("A grateful family gives you supplies and a lead.", 0.5, humanity=8, items={"food": 2},
                                   coins=4, reveal=True, xp=10),
                 _o("It was bait. The dead are already moving toward you.", 0.5, humanity=2, horde=True, panic=10)),
              _c("Ignore it", _o("You keep walking. The signal goes on for a long time.", humanity=-2)))),
    EventDef("scholar", "A dying researcher",
             "A researcher lies in a doorway, clutching a folder. 'Take it... please. Read the last page.'",
             (_c("Stay with them", _o("You stay until the end. The notes are meticulous.", humanity=5, words=4, xp=8)),
              _c("Take the notes and go", _o("You do not look back.", humanity=-3, words=2)),
              ), min_day=1),
    EventDef("preacher", "A preacher",
             "A {cult} preacher offers you a blessing: 'The dead are only the beginning. Kneel and be unafraid.'",
             (_c("Accept the blessing", _o("A strange calm settles on you.", panic=-30, humanity=-2, rep={"cult": 8})),
              _c("Argue with them", _o("They are unmoved. You feel a little steadier for having said it.", humanity=2,
                                       panic=-5)),
              _c("Walk on", _o("You leave them preaching to the empty street.")))),
    EventDef("trapped", "Trapped under rubble",
             "Someone is pinned under a fallen beam, groaning. Freeing them will be loud.",
             (_c("Free them", _o("They limp away, grateful. You hear the dead stirring.", 0.7, humanity=7, xp=8,
                                 items={"bandage": 1}, heat=15),
                 _o("The beam shifts. It was worse than it looked.", 0.3, humanity=3, hp=-8, heat=20)),
              _c("Leave them", _o("The groaning fades behind you.", humanity=-5, panic=4)))),
    EventDef("cache", "A supply cache",
             "A tidy stash of supplies sits behind a doorway. A wire runs across the threshold.",
             (_c("Disarm the wire", _o("Click. Everything inside is yours.", 0.6, items={"food": 2, "bandage": 2},
                                       coins=3, xp=8),
                 _o("The wire was connected to something loud.", 0.4, heat=22, panic=8)),
              _c("Smash the door", _o("It works, but half the street heard.", items={"food": 1, "bandage": 1}, heat=18)),
              _c("Leave it", _o("Nothing is ever free.", xp=1)))),
    EventDef("soldier", "A wounded soldier",
             "A wounded {military} soldier waves you over. 'Got intel. Got ammo. Can't walk.'",
             (_c("Treat their wounds", _o("They give you everything they have left, and a location.", humanity=5, reveal=True,
                                         coins=5, xp=10, items={"bandage": -1}, rep={"military": 8}),
                 items={"bandage": 1}),
              _c("Rob them", _o("They are in no state to stop you.", humanity=-10, coins=6,
                                rep={"military": -10})),
              _c("Keep walking", _o("They call after you, then stop.", humanity=-3)))),
    EventDef("prisoner", "A prisoner",
             "A {raiders} prisoner is chained to a post in a yard. Two guards watch from a porch.",
             (_c("Free them", _o("The guards open fire.", raiders=2, humanity=8, rep={"enclave": 5})),
              _c("Ignore it", _o("You pass by quietly.", humanity=-4)))),
    EventDef("bait", "A horde in the street",
             "A horde fills the end of the street, drifting your way. A stranger crouches beside you, shaking.",
             (_c("Push the stranger out as bait", _o("The horde follows the screaming. You slip away. You will remember it.",
                                                   humanity=-25, heat=-30, panic=15)),
              _c("Pull them to cover and hide", _o("Silence, held for minutes. The horde passes.", 0.6, humanity=4, xp=8),
                 _o("A cough. They are on you.", 0.4, horde=True, humanity=2, panic=10)),
              _c("Draw them off yourself", _o("You run, loud and desperate. It works, barely.", hp=-5, panic=10,
                                              humanity=5, heat=15)))),
    EventDef("trader", "A wandering trader",
             "A wiry trader with a hand-cart whispers: 'Medicine, cheap. Ask no questions.'",
             (_c("Buy bandages (4 {coin})", _o("A fair deal.", items={"bandage": 3}, coins=-4), coins=4),
              _c("Buy a medkit (12 {coin})", _o("Wrapped in a clean cloth.", items={"medkit": 1}, coins=-12), coins=12),
              _c("Move on", _o("They shrug and push their cart on.")))),
)
BY_ID: Dict[str, EventDef] = {e.id: e for e in EVENTS}


@dataclass
class ActiveEvent:
    event_id: str
    text: str
    result: str = ""
    resolved: bool = False

    @property
    def definition(self) -> EventDef:
        return BY_ID[self.event_id]


def context(game) -> Dict[str, str]:
    f = game.era.factions
    return {"coin": game.era.coin, "radio": game.era.radio.capitalize(),
            "raiders": f["raiders"][0], "cult": f["cult"][0], "military": f["military"][0],
            "enclave": f["enclave"][0], "science": f["science"][0]}


def can_afford(game, choice: Choice) -> bool:
    p = game.player
    need = choice.needs
    if p.coins < int(need.get("coins", 0)):
        return False
    return all(p.count(i) >= q for i, q in dict(need.get("items", {})).items())


def pick(game) -> Optional[EventDef]:
    pairs = []
    for ev in EVENTS:
        if game.clock.day < ev.min_day or game.recent_events.get(ev.id, -999) > game.clock.turn - 600:
            continue
        w = ev.weight * game.profile.human_threat if ev.id in ("toll", "prisoner", "bait") else ev.weight
        if ev.id == "radio" and not game.era.electricity and game.era.tech > 0:
            continue
        pairs.append((ev, w))
    return weighted_choice(game.rng, pairs) if pairs else None


def start(game, ev: EventDef) -> ActiveEvent:
    game.recent_events[ev.id] = game.clock.turn
    return ActiveEvent(ev.id, ev.text.format(**context(game)))


def resolve(game, active: ActiveEvent, index: int) -> str:
    choice = active.definition.choices[index]
    if not can_afford(game, choice):
        return "You cannot afford that."
    outcome = weighted_choice(game.rng, [(o, o.weight) for o in choice.outcomes])
    text = outcome.text.format(**context(game))
    apply_fx(game, outcome.fx)
    active.result, active.resolved = text, True
    game.msg(text, "lore")
    return text


def apply_fx(game, fx: Dict[str, object]) -> None:
    p = game.player
    if "humanity" in fx:
        game.adjust_humanity(int(fx["humanity"]), "")
    if "panic" in fx:
        game.add_panic(float(fx["panic"]), raw=True)
    if "hp" in fx:
        p.hp = max(1, min(p.max_hp, p.hp + int(fx["hp"])))
    if "coins" in fx:
        p.coins = max(0, p.coins + int(fx["coins"]))
    if "xp" in fx and int(fx["xp"]) > 0:
        p.gain_xp(int(fx["xp"]))
    if "words" in fx:
        learned = game.know.learn_random(game.rng, int(fx["words"]))
        if learned:
            game.msg(f"You pick up the meaning of: {', '.join(learned)}.", "good")
    if "heat" in fx:
        game.add_heat(float(fx["heat"]), raw=True)
    for item_id, qty in dict(fx.get("items", {})).items():
        if qty > 0:
            game.give_item(Item(item_id, qty))
        elif qty < 0:
            p.take(item_id, -qty)
    for role, delta in dict(fx.get("rep", {})).items():
        game.rep[role] = max(-100, min(100, game.rep.get(role, 0) + int(delta)))
    if fx.get("horde"):
        game.spawn_horde_near_player()
    if fx.get("raiders"):
        game.spawn_raiders_near_player(int(fx["raiders"]))
    if fx.get("reveal"):
        game.reveal_random_lead()
