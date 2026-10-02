"""How a run ends: a title, a paragraph, and a scorecard."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from outbreak.engine import cipher


@dataclass
class Ending:
    kind: str                       # won | dead | turned | left_behind
    title: str
    text: str
    summary: List[str] = field(default_factory=list)
    score: int = 0

    @property
    def victory(self) -> bool:
        return self.kind == "won"


def _band(humanity: int) -> str:
    if humanity >= 75:
        return "saint"
    if humanity >= 40:
        return "survivor"
    if humanity >= 15:
        return "cold"
    return "monster"


WIN = {
    ("cure", "saint"): ("The Cure - and the people who made it possible",
                        "The serum burns going in, then the fever breaks. You carry the formula back out to the "
                        "others. People you helped along the way are waiting. It is not the end of the dead, "
                        "but it is the beginning of the end of the fear."),
    ("cure", "survivor"): ("Cured",
                           "The fever breaks. You sit on the floor of the refuge and shake until the shaking stops. "
                           "You made hard choices to get here; you are alive, and so is the formula."),
    ("cure", "cold"): ("Cured, and cold",
                       "The cure works. The refuge keeps you at arm's length. You got what you came for, and you "
                       "paid in a currency nobody gives back."),
    ("cure", "monster"): ("The cure, and what it cost",
                          "You are alive. The formula is real. Nobody here will ever meet your eyes. You do not "
                          "blame them."),
    ("extraction", "saint"): ("Evacuated - with company",
                              "The pickup comes in low over the dead. You are not alone on the ramp: people you "
                              "helped are with you. You look down at the burning city and do not feel guilt."),
    ("extraction", "survivor"): ("Evacuated",
                                 "The pickup lifts. Below, the dead are a dark tide in the streets. You made it out."),
    ("extraction", "cold"): ("Evacuated, alone",
                             "You make the pickup. Nobody else does. You tell yourself it was the only way."),
    ("extraction", "monster"): ("Left a trail",
                                "You make it out alive. The crew who pull you aboard have heard the stories, and "
                                "they keep their rifles up the whole flight."),
}


def build(game, kind: str, cause: str = "") -> Ending:
    p, sc = game.player, game.scenario
    days = game.clock.day
    decoded = sum(1 for d in game.docs.values() if d.id in p.documents and cipher.is_decoded(d, game.know))
    score = (p.kills * 2 + days * 25 + p.humanity + decoded * 8 + p.level * 12 +
             (500 if kind == "won" else 0))
    summary = [
        f"Survived {days} day{'s' if days != 1 else ''} ({game.clock.turn} turns)",
        f"Zombies destroyed: {p.stats.get('zombies', 0)}   People killed: {p.stats.get('humans', 0)}",
        f"Level {p.level}   Humanity {p.humanity}   Fluency {int(game.know.fluency * 100)}%",
        f"Documents read: {len(p.documents)}   Words known: {len(game.know.known)}/{len(game.know.vocab)}",
    ]
    if p.lost:
        summary.append("You lost your " + " and your ".join(p.lost) + " to survive.")
    if kind == "won":
        title, text = WIN[(sc.id, _band(p.humanity))]
    elif kind == "turned":
        title = "You turned"
        text = ("The fever peaks and the world goes quiet. When you open your eyes again, you are hungry, and "
                "the sounds of the living are very loud.")
    elif kind == "left_behind":
        title = "Left behind"
        text = (f"Day {sc.deadline_days + 1} dawns. Somewhere far away, the last way out leaves without you. "
                "The dead are patient. You are not.")
    else:
        title = "You died"
        text = cause[:1].upper() + cause[1:] + "." if cause else "You did not make it."
    return Ending(kind, title, text, summary, score)
