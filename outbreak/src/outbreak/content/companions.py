"""The people who travel with you: archetypes with a strength, a flaw and a voice.

Every non-hostile person can become your companion (a trader, a healer, a patrol member, a stranger you saved), and
whoever they are they get a personal name and one of these profiles, fixed by their id.  One companion at a time; when
they die, they stay dead.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class Archetype:
    id: str
    label: str                    # "veteran"
    strength: str
    flaw: str
    hp: int
    dmg: Tuple[int, int]
    acc: int
    intro: str                    # what they say when they fall in beside you
    idle: Tuple[str, ...]
    kill: Tuple[str, ...]
    hurt: Tuple[str, ...]
    farewell: str                 # said when they leave, or what you remember them saying
    backstory: Tuple[str, str, str]


STRENGTHS: Dict[str, str] = {
    "fighter": "hits hard and shoots straight",
    "medic": "patches you up when you are hurt",
    "scavenger": "finds something useful whenever you come back out of a building",
    "scout": "spots ambushes and snares before you walk into them",
    "calm": "steadies your nerves",
    "tinker": "keeps your weapon in repair",
    "tough": "can take a beating",
    "lucky": "has a way of coming back with something",
}

FLAWS: Dict[str, str] = {
    "coward": "runs when it gets bad",
    "loud": "cannot keep quiet, and noise draws the dead",
    "hungry": "eats from your pack",
    "frail": "will not survive much",
    "pacifist": "will not fight people, and judges you if you do",
    "reckless": "charges in and will not break off",
}

ARCHETYPES: Tuple[Archetype, ...] = (
    Archetype("veteran", "veteran", "fighter", "reckless", 40, (5, 9), 68,
              "\"You look like you know where you are going. I know how to hit things. Seems fair.\"",
              ("\"Keep your head down and your feet moving. That is all I ever learned.\"",
               "\"I have walked into worse. I just do not remember when.\"",
               "\"Quiet is good. Quiet means nothing is hunting us yet.\""),
              ("\"One less.\"", "\"Stay down.\""),
              ("\"Scratch. Keep going.\"",),
              "\"Do not wait for me. Never wait for me.\"",
              ("\"I was somebody's sergeant once. They are all dead now. I count them when I cannot sleep.\"",
               "\"I charge because stopping is when I remember. You can hate that about me.\"",
               "\"I am not afraid of dying out here. I am afraid of being the only one left again.\"")),
    Archetype("medic", "medic", "medic", "frail", 16, (2, 4), 45,
              "\"I can keep you alive if you can keep me alive. That is the whole arrangement.\"",
              ("\"Drink something. Please. I am tired of watching people forget.\"",
               "\"Every one of these buildings had a clinic once.\"",
               "\"Tell me if anything hurts. Anything.\""),
              ("\"I... did that?\"",),
              ("\"I am fine. I am fine. I am not fine.\"",),
              "\"You did everything right. Remember that.\"",
              ("\"I was three weeks from finishing my residency. I still sign things with the wrong title.\"",
               "\"I counted the ones I could not save. I stopped counting at forty.\"",
               "\"If it comes to a choice, save the one who can walk. I have already decided that about myself.\"")),
    Archetype("scavenger", "scavenger", "scavenger", "loud", 24, (3, 6), 52,
              "\"Mina. I find things. Do not ask me to be quiet, I get nervous.\"",
              ("\"Heh. Heh. Did you see that shelf? We should have taken the shelf.\"",
               "\"Nothing is ever really empty. People just do not look under things.\"",
               "\"I talk when I am scared. Did I mention I talk when I am scared?\""),
              ("\"Whoa! Okay. Okay!\"", "\"Did I do that? I did that.\""),
              ("\"Ow ow ow ow.\"",),
              "\"Take the red bag. It has the good stuff. Go.\"",
              ("\"I ran a stall at the night market. Fourteen years. Everything has a price, and I know all of them.\"",
               "\"The first thing I stole out here was a stranger's shoes. They did not need them anymore.\"",
               "\"You are the first person who did not ask me to shut up. I will remember that.\"")),
    Archetype("hunter", "hunter", "scout", "hungry", 28, (3, 7), 55,
              "\"I walk quiet and I eat a lot. Both are true. You will see.\"",
              ("\"Wind has changed. Smell that? Rain by evening.\"",
               "\"I would trade my whole kit for one hot meal.\"",
               "\"Tracks over there. Old. Do not worry about them.\""),
              ("\"Clean.\"", "\"Dinner.\""),
              ("\"That is nothing. I have been bitten by worse.\"",),
              "\"Keep to the trees. They hide a person better than a wall.\"",
              ("\"I grew up on a farm that ate us all in a hard year. I never trusted full pantries after.\"",
               "\"There was a dog. I will not talk about the dog.\"",
               "\"I leave food out for the strays. I know it makes noise. I do it anyway.\"")),
    Archetype("mechanic", "mechanic", "tinker", "coward", 26, (3, 6), 50,
              "\"If it has moving parts, I can make it keep moving. Please do not make me go first.\"",
              ("\"Your weapon is balanced wrong. I will fix it when we stop. If we stop.\"",
               "\"There is always a way to make it work. There is rarely a good way.\"",
               "\"Do you hear that? Probably nothing. Probably.\""),
              ("\"I did NOT want to do that.\"",),
              ("\"Can we go? Can we please go?\"",),
              "\"I left the toolbox. It was heavy. Sorry. Sorry.\"",
              ("\"I fixed elevators for twenty years. I got stuck in one for two days when it started.\"",
               "\"Fear is just information. Mine says run, mostly.\"",
               "\"The only time I was not scared was fixing something. Thank you for letting me.\"")),
    Archetype("preacher", "preacher", "calm", "pacifist", 24, (2, 4), 40,
              "\"I will walk with you. I will not hurt anyone. If that is a problem, say so now.\"",
              ("\"We are not the first to walk this road, and we will not be the last.\"",
               "\"Breathe. Count to four. Again.\"",
               "\"Everyone out here is somebody's something.\""),
              ("\"Forgive me.\"",),
              ("\"It is only the body.\"",),
              "\"Let it go. You are lighter without it. Go on.\"",
              ("\"I took vows I do not believe anymore. I keep the habit because people need to see it.\"",
               "\"I prayed over a hundred of them. None of them were mine.\"",
               "\"I will hurt someone to save you, one day. I would rather you do not ask me to say that out loud.\"")),
    Archetype("brute", "brute", "tough", "loud", 52, (4, 8), 58,
              "\"Dag. I carry things and I hit things. Where to?\"",
              ("\"HA. Did you see that one go?\"", "\"Is there food? I am always asking about food.\"",
               "\"I am quiet! I am being quiet!\""),
              ("\"Another!\"", "\"Next!\""),
              ("\"Pfft. Feels like a bee.\"",),
              "\"Keep walking. I will hold the door. I always hold the door.\"",
              ("\"I was a bouncer. Then a roofer. I am good at standing in doorways.\"",
               "\"My brother was bigger than me. That is what everyone says about him now.\"",
               "\"People are afraid of me. I wish they were not. You are not. Thank you.\"")),
    Archetype("gambler", "gambler", "lucky", "coward", 26, (3, 6), 54,
              "\"Name is not important. Luck is. Stay close and some of it might rub off.\"",
              ("\"Odds are odds. Never fight a bad one.\"", "\"I once drew three aces in a row. Then the world ended. Coincidence?\"",
               "\"Nothing is certain. That is what makes it fun. And terrifying.\""),
              ("\"Beginner's luck.\"",),
              ("\"The house always wins, huh.\"",),
              "\"I bet you make it. I have never been right about anything, but I bet you make it.\"",
              ("\"I owe money to people who are probably dead. It does not feel like freedom.\"",
               "\"I bluff. I always bluff. Right now I am bluffing that I am not afraid.\"",
               "\"You are the only bet I have ever hoped to lose to.\"")),
)

BY_ID: Dict[str, Archetype] = {a.id: a for a in ARCHETYPES}

# Who a person is when you only know their trade or what they do for a living
ROLE_ARCHETYPE: Dict[str, str] = {"healer": "medic", "trader": "scavenger", "scholar": "mechanic", "scout": "hunter",
                                  "soldier": "veteran", "raider": "brute"}

NAMES: Tuple[str, ...] = ("Ruiz", "Okafor", "Mina", "Tomas", "Joon", "Lena", "Dag", "Vesper", "Kaito", "Ada", "Marek", "Sol",
                          "Imani", "Bruno", "Nadia", "Pip", "Ines", "Haruto", "Cass", "Oren", "Talia", "Wren", "Yusuf", "Greta",
                          "Beck", "Sasha", "Ravi", "Noor", "Dmitri", "Lucia", "Fenn", "Odile")

# What they shout when it turns violent
COMBAT_LINES: Dict[str, Tuple[str, ...]] = {
    "engage": ("\"Contact!\"", "\"On me!\"", "\"I see it. I have got it.\"", "\"Here they come!\""),
    "regroup": ("\"Wait! Do not leave me here!\"", "\"Where are you going? Wait for me!\"", "\"I am coming! Keep moving!\""),
    "player_hurt": ("\"You are hit! Get back!\"", "\"Behind you!\"", "\"Stay with me, I have got you!\""),
    "flee": ("\"I cannot do this! Fall back!\"", "\"Back! Everybody back!\"", "\"Run!\""),
}

# What they say about the world, whoever they are
SITUATION_LINES: Dict[str, Tuple[str, ...]] = {
    "night": ("\"I do not like the dark. Nobody should.\"", "\"Let us find somewhere with walls.\""),
    "rain": ("\"At least the rain covers the sound.\"", "\"Rain again. My boots have given up.\""),
    "fog": ("\"I can barely see you. Stay close.\"",),
    "storm": ("\"Thunder. Everything hears thunder. Be careful.\"",),
    "forest": ("\"Too many trees. I do not trust a place that quiet.\"", "\"Listen. Even the birds went silent.\""),
    "cave": ("\"I will wait here. I am not going down there. Take the light.\"",),
    "hungry": ("\"Are we eating soon? I can hear my stomach arguing.\"",),
    "hurt": ("\"You are bleeding. Do something about it.\"", "\"You do not look good. Rest.\""),
    "refuge": ("\"Walls. Real walls. I forgot what that feels like.\"",),
    "warning": ("\"Contact!\"", "\"Something is moving.\""),
}
