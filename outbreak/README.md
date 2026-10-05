# OUTBREAK

A zombie survival roguelike for the terminal. You choose **when** the collapse happens (the era),
**what** the dead are (the zombie type) and **what you are trying to do** (the scenario).

It is a standalone game: it shares nothing with the Jedi Fugitive game in the parent directory
except the repository. Pure Python, standard library only (curses).

```
python3 play.py                      # title screen -> new game form
python3 play.py --new --era medieval --zombies swarm --scenario extraction --seed 7
python3 play.py --continue           # resume the autosave
python3 play.py --list               # every era, zombie preset, scenario and origin
```
On Windows install `windows-curses` first (`pip install windows-curses`). Needs a terminal of at least 80x24.

## The three choices

**Era** (what you have): Medieval 1348, 1986, Modern, Far-future station. Each is a data pack: its own
weapons, armour, lights, place names, factions, medicines, and the vocabulary of the cipher you learn to read.
No guns in 1348; bows are quiet, mail is heavy. In 2026 a shot is loud and ammunition is the real currency.

**The dead** (what hunts you) are built from parameters, not hard-coded classes:
speed, senses, how the infection spreads, intelligence, decay over the days, and how you kill them.

| preset | feel | inspired by |
|---|---|---|
| `classic` | slow, noise-driven, head shots only; everyone who dies rises | Romero |
| `rot` | slow, track your scent, rot over weeks; people are the real danger | The Walking Dead |
| `rage` | sprinters, near-instant infection, they starve after a few weeks | 28 Days Later |
| `spore` | spore clouds in closed rooms (carry filters), blind brutes hunt by sound | The Last of Us |
| `bio` | the longer it spreads the worse the mutations; a hunter that never stops | Resident Evil |
| `swarm` | frail but huge hordes that pile over fences; go quiet or die | World War Z |
| `night` | clever pack hunters that burn in sunlight; deadly by night and indoors | I Am Legend |

**Scenario** (your goal):
* `cure` - you start bitten with a slow strain. Find three components in locked vaults, decipher the formula,
  and synthesise a cure at the refuge before the fever turns you.
* `extraction` - gather three parts, reach the extraction point before the way out closes and hold out until the pickup.
  The deadline is computed from the route (the farther the parts and the extraction point are, the longer you get: about 96
  tiles of real progress a day, plus time for every vault), never less than 10 days.
* `dash` - no parts, only the road: get to the extraction point before the way closes and hold out. A shorter, more
  physical run, with five incidents on the way.
* `endless` - no exit and no clock. Live as long as you can, or gather the three components and the formula
  and make the cure at the refuge, which ends it with a win. Nobody starts bitten. Every day past the third the
  world gets worse, without limit: the dead get +6% a day of health and damage (up to x3), hordes and ambient
  spawns grow with it, and in hardcore the enemy level cap rises with the calendar (up to 40, not 15). To keep
  a long life possible, vaults and containers you emptied refill (about half of them) every 4 days. Dying
  is a survival result ("Survived 23 days") with a bigger score per day. Combined with `living` it is the eternal
  hardcore world.

On the road to the extraction point (`extraction` and `dash`) things happen: wrecked convoys, an abandoned checkpoint, a
bridge that is out, a column of refugees, an ambush, the dead crossing the road. Each is placed on the route when the world
is created and fires once when you get close. Choices cost items, health, humanity or time; time lost does not simulate the world
(nothing hunts you while you lose it) but counts against the deadline.

All three end with a hold-out finale. Who shows up depends on your **humanity**: the Alpha if you stayed human,
armed people who have heard about you if you did not.

**Raiders are a squad, not a target.** Camps are no longer a clearing with some men standing in it:
* *Ambushes.* Half of a camp's raiders lie hidden in cover 4-9 tiles round it. They are not drawn, not targeted and not
  counted as enemies in sight until they spring: when you come within 3 tiles (2 if you creep), when one of their squad
  starts hunting you, or when you bump into one. They all spring together (`Raiders burst out of cover!`). A creeping player
  can spot one first (25% a turn within 3 tiles): it has not seen you and you can avoid it or strike first.
* *Snares.* Five hidden snares are laid on the approaches of every camp. Stepping on one costs 8 health and a bleed, makes
  a clatter (noise 12) and alerts every raider within 14 tiles. You may spot one as you walk next to it (35%; 70% and from
  2 tiles if you creep): it shows as a red X. A spotted snare will not let you step on it unless you creep, in which case
  you disarm it and keep a scrap. The dead trip them too, so camps thin out zombie hordes.
* *Fire discipline.* Gunmen and archers carry a magazine (6 shots, 5 arrows) and must reload (3 turns, from cover if
  they can), they back off to range when you close in instead of standing still, and take cover between bursts a third of
  the time. In pairs one side works round to your flank instead of walking into the barrel.
* *Morale.* Raiders no longer run on contact. They run when below 30% health or when their morale breaks: each friend
  killed near them costs 25. Out of sight it recovers 2 a turn, and they come back.
* *Everywhere.* Ambushes are not only for camps: raider road events and the Dash finale spring the same hidden squad
  (half in cover, three hidden snares round you), and lone tripwires are scattered along the far roads.

**Food: hunting, foraging, cooking.** Rations are no longer the only meal.
* *Game.* Rabbits (`r`), deer (`d`) and boar (`b`) graze on grass and brush, away from the start. They notice you from 5, 7 and
  4 tiles (3 tiles less if you creep, and then only 40% of the time per turn), and bolt on two of every three turns, so a chase
  can end. A creeping hunter can walk up and stab an unaware animal for **triple damage**. A boar does not run: it charges and
  gores (3-7). Walk into game to attack (melee only for now: they are not shot at). A kill drops 1-3 **raw meat**.
* *Raw meat* feeds 24 but has a 35% chance of cramps (-4 health, hungrier). **Cook** it (craft menu, `cook`: raw meat + a plank)
  for **cooked meat**, which feeds 58.
* *Foraging.* Terminal `F`, web **Forage** button (key `z`): 5 turns on grass (50%) or brush (80%) for 1-3 wild greens
  (feed 12); +10% in rain or fog, -25% at night. A patch (radius 2) stays picked for 800 turns. Something hunting you stops it.
* *Gather* is one key for living off the land (terminal `F`, web **Gather** button or `z`; the button names what it will do):
  - **Chop**: with a blade (6 turns) or something heavy (9) next to a tree. 2-4 planks, a stump-free clearing where it stood
    (it opens sightlines), and noise 8 every third turn. Not on the rim of the map, not bare-handed.
  - **Fish**: next to water with a **rod** (wood + cloth + scrap; 8 turns, 55%, one fish, 4% to snap) or a **net**
    (3 cloth + wood; 12 turns, 70%, up to 3 fish, 35% to tear). Quiet. Raw fish feeds 20 (12% cramps); cook it with a plank
    (`cook_fish`) for grilled fish (46). +10% in rain or fog, -20% at night.
  - **Forage** otherwise, as above.
* *Nail bomb* (chem + 2 scrap + cloth, no workshop; throw it): 11-18 to everything in radius 2 with line of sight, loud (16),
  and it hurts you too if you are inside the radius. All of these recipes are known from the start.
* Checkpoints take only the most valuable **three stacks** of contraband, not your whole kit.

**Checkpoints and corrupt soldiers.** The far roads (at least 35 tiles from the start) have military checkpoints: three
soldiers holding the highway (two on the small map, more on a big one). Come within 7 tiles in sight of one (3 if you are
creeping) and it stops you, once per 500 turns. Roaming military patrols do the same, but only half the time and at most
once per 300 turns. They are looking for **contraband**: medicine (medkit, suppressant, painkiller), thrown explosives and
in the firearm eras every gun and bullet (in 1348, crossbows). Quest items are never taken. If you carry nothing they
wave you on; a corrupt one may stop you for a road tax instead. A bite you cannot hide (40% chance per stop) is the worst
thing they can find. You choose:
* *Submit* - they take it all. An honest soldier means to hand it in; a corrupt one pockets it. Either way the **leader
  carries it**: kill him and it drops. If you are infected, they shoot.
* *Bribe* - 4 + 2 per contraband item (+8 if sick; sick pays double). A corrupt soldier takes it 90% of the time (75% if
  you are sick); an honest one 15% (never if sick), and when it fails he keeps the money and takes the goods.
* *Talk* - 22% + humanity/220 + military reputation/250 (less if sick). Failing it is a search.
* *Draw* - the whole crew turns on you and military reputation drops 40. At -50 every checkpoint shoots on sight.
About 38% of soldiers are corrupt (decided by their id, so it is the same on every run of a seed). Hostile soldiers fight like
raider squads: magazines, reloads, cover.

**Push and run.** The web controls have a **PUSH** button (keyboard V; terminal `P`) next to **SNEAK** and a new **RUN** button
(keyboard X; terminal `R`; sneak is H on the web). Push shoves the nearest hostile within reach: it staggers back a tile (two if
you are level 4 or more and it is not a brute), loses two turns, and wakes up hunting you. A wall or a solid thing behind it
costs it 2-4 health and a third lost turn. Brutes resist (45% less likely to move), the Alpha and other bosses never budge, a
missing arm makes your shove 30% less likely to work, it costs 8 stamina and is quiet (noise 3). Use it to make room, to
break off, or to steer the dead onto a spike trap or into a fire. The button lights up and names the target when something is
within reach.

**Learning the language.** Everything written (research notes, vault codes, the formula, crafting manuals, diary pages)
is in the era's cipher. Where it comes from:
* *Pages* lie in the crates and on the floors of buildings, houses above all (a loose page shows as a teal mark; crates must
  be searched). Reading a page exposes you to its unknown words (a word sinks in after four exposures); *studying* it
  (three tries per page) decodes words on purpose. A page is *deciphered* once about 60% of its key words are known, and
  only then does it act (marks a vault, gives a code, teaches a recipe).
* The *diary pages* are the practice material. They scale with the world (about one for every five buildings: ~50 on the web
  map, 9 on the terminal one) and the first quarter are placed within about 30 tiles of where you start, the next quarter
  within the nearest third of the map, so the language can be picked up from the first day.
* Stepping into a building that still holds pages you have not read tells you so (`You glimpse written pages somewhere in
  here.`).
* The **Archivist** at the refuge teaches 3 words for 5 coins, and for 4 more marks the two nearest buildings that still hold
  unread pages (*papers rumoured* in the places list).
* Your origin and your opening scene start you with a few words, and some road events teach more.

**Crafting.** You start knowing the five basics (bandage, splint, fire bomb, noisemaker, barricade kit). The
rest (spike trap, repair kit, filter, medkit, suppressant, ammunition) are learned from a **manual**: one
written page per recipe, hidden in buildings like any other document, in the era's cipher. Read and decipher it
and you know the recipe for good (a new survivor in hardcore keeps what you learned). Using a recipe still
needs the materials and, for the advanced ones, enough fluency in the cipher. The craft screen lists only
what you know and says how many are still to find.

**Weapons are made at a workshop.** Standing beside a workshop (you build one in your base) you can make a
nail-studded club (known from the start), and, from manuals, a ground-down blade, a reinforced spear, a scrap bow
and improvised arrows for it. They are never found in loot; they are the reason to have a base.

**A base of your own** (`o` in the terminal game, *Base* in the web menu). Step into a building with nothing
hostile left in it and claim it. Inside it you can build, on the clear floor beside you, a **workshop**, up to two
**cots** (sleep there to heal; a raid or a wound wakes you early), a **locker** (a stash: what you store there
stays, and in hardcore the next survivor wakes up in your base with the locker still full) and **barricades**
(braced gates of 40 hp the dead must batter down; you cannot wall yourself in). At night, while you are in it, the
dead find your base: a raid of several zombies comes in at the entrance, and the base stops being safe until
they are dead. Only one base at a time; claiming another leaves the old one to the dead.

**The world plays its part** (`ambience.py` / `ambience.js`). Noise is no longer only yours:
* *Ground and places.* Stairs, open doors and, inside buildings, the kind of place make every step louder: broken
  glass in markets and labs, loose metal in industrial sites, echoing platforms and halls, creaking house floors.
  Sneaking is silent on all of it. On an open road or splashing through shallows you are also easier to see.
* *Weather* (outdoors; rolled every half day): **rain** muffles noise (x0.7), washes your scent trail away and shortens
  sight; **fog** halves what the dead see and shortens your own view; **storms** do all of that, harder, and add
  thunder claps that pull the dead toward wherever they landed. Indoors weather does not matter. The weather
  shows in the clock line.
* *Things that go off on their own.* Now and then a car alarm starts to wail somewhere out of sight, or something
  collapses in the distance; the dead go to see. The first time you enter a market, guard post, military site or lab
  its alarm may still have power (30%) and shriek for a while, loud enough for the street to hear it. Pushing through
  brush by day can flush a flock of crows.
  All of these can be used: a distant alarm pulls zombies away from you, a storm covers a run, and a mistake in a
  glass-strewn market brings the street in.

**Eras play differently** (`EraRules` in `content/eras.py`; every number is data):
| | medieval | eighties | modern | sci-fi |
|---|---|---|---|---|
| the world makes noise | bells, livestock, collapses | car alarms, sirens | car alarms, phones, helicopters | klaxons, patrol drones, power surges |
| building alarms | none | 20% | 30% | 45% |
| your footsteps | x0.8 (soft ground) | x1 | x1.1 (hard floors) | x1.15 |
| your own night view | -1 | 0 | +1 | +2 (visor) |
| a carried light shows you | x2.2 (a beacon) | x1.8 | x1.7 | x1.3 |
| the dead in the dark | as usual | as usual | as usual | no penalty (they sense heat) |
| brush hides you | x0.45 | x0.5 | x0.5 | x0.65 |
| how much the plague can mutate | x0.3 | x0.7 | x1.0 | x1.4 |

Patrol drones drift across the map and, if they get near you while you are not creeping, scan you and call the dead.

**The strain changes, district by district.** Each plague has a `mutates` rate (Biohazard 1.0, Spore 0.6, Rage 0.35,
Swarm 0.3, Slow rot 0.2, Classic and Nightstalkers 0.1); times the era's science and ramped over the first 12 days, it is
the daily chance that a district's dead gain a trait. The map is cut into districts (about 6 on the terminal map, up to 30
on the big web one), named for their compass position and what stands in them ("North-East Garrison", "South Labs"). Labs,
bases, hospitals and ground zero are **hot** and breed it up to 1.7x faster; each district runs its own dice, so they
diverge. Eight traits exist, at most four per district, and not all are improvements: *faster, tougher, keener senses,
harder hitting, hulking (big, slower), brittle but quick, howling (hears everything), swifter*. A trait applies to the
dead already walking in that district and to every zombie born there afterwards; it also raises the share of the strange
ones. Crossing into a district tells you what its dead are like (`You enter the South Labs. The dead here are faster,
tougher.`), the status line and the web header show it, and the web menu has a **Strain map** listing every district with
its direction, distance and what you know of it (only districts you have entered, or heard of, are known). So the same
Classic dead in a medieval world hardly change in a month, while Biohazard in a sci-fi world has districts with four
traits by day 20, and the road you choose is a choice of which mutations you meet. The briefing says which of these you
are playing. (A horde that wanders between districts keeps the traits of where it was born.)

**The records.** Every finished run (won, dead, turned, left behind) is kept on your machine
(`records.json` next to the saves, or the browser's storage) and compared with your earlier runs of the same
objective and mode: days survived first, points second. The end screen says whether it is a new record, and
the title screen has a *Records* page with the best of each and the latest runs.

**The siege.** The hold-out is not a countdown you stand through. The final site has a main entrance and three
side doors. Waves arrive at a random one of them, get bigger, and come faster as the clock runs down. A side
door that is not barricaded breaks on the first wave; a barricaded one (barricade kit, 40 hp) batters for a few
waves and then everything that piled up behind it comes through at once. The first time you use the console
the game tells you which doors are open and lets you prepare; the second time it starts for good. Prepare with
barricade kits, **spike traps** (craftable from wood and scrap; set where you stand, they wound the first of the
dead to step on them), fire bombs and noisemakers, and re-barricade a door that still stands while you hold.

**Opening** (how the story starts): you do not begin in a vacuum. Pick, or let the game pick from who you are,
a scene: studying, preparing a meal, out hunting, on your rounds, standing watch, fixing things, at the market,
a funeral vigil. Each has its own text per era and small consequences (a ranged weapon and food for the hunter, a
bigger vocabulary for the student, armour for the guard, a steadier conscience at the vigil, the hour you
start at). A three-page briefing (the scene, the world and what the dead are, what you must do) plays before
the first turn; `B` re-reads it.

**Mode**:
* `normal` - one survivor, one life; permadeath deletes the save.
* `living` ("Hardcore - the world goes on", `--mode living`) - your death is not the end. A new survivor
  (another origin) walks out of the refuge into the *same* world at the same hour: the dead, the vaults, the
  patrols and the clock are untouched. Your gear lies where you fell and your body rises as a named, levelled
  zombie. Whatever killed you levels up, takes a name ("Killer of Paramedic #1") and stays. The new survivor
  keeps your documents and half your cipher knowledge and starts at half your level. Infinite lives: the run
  ends only by winning or, in `extraction`, when the way out closes. The cure is for the world: nobody starts bitten.
  Enemies (zombies, raiders, patrols) gain levels by killing, capped by the calendar (level 3 on day 1, +1 per day,
  maximum 15). Big hordes keep every zombie instead of dropping the ones that do not fit on screen.

The web build also has a much larger map (360x240) planned whole and painted by chunks as you approach (see
`web/README.md`); the terminal game keeps its fixed 120x76 map. In the web build the hardcore modes run in **real time** (no turns), and there is a third mode, a **shared world** with seasons
that the keeper resets; see `web/README.md`. Those are web only (real time and the artifact database).

**Random**: era, the dead, objective, who you are and mode can each be set to `random` (the new-game screen has a Random
option on each choice and a "random everything" entry; `--era random` ... or `--random` on the command line). It is drawn when
the game starts, reproducibly if you also give a seed, and the log says what came up. The shared world is never drawn.

## How it plays

* **Sneaking up on them.** A zombie that has not noticed you has an awareness meter and a facing (the pale wedge on
  it in the web build). While you are in its sight the meter fills: fast if you are close, in front of it, running or
  making noise; slowly if you are sneaking (`s`) or behind it (it sees about 60% as well over its shoulder, 80% at its
  side). At 100 it hunts you (a red `!`); at 40 it turns to look; a `?` means it is on edge. Hit one that has not noticed
  you (meter under 70) and you cannot miss: a double-damage head blow that kills most. Sneaking on soft ground makes no
  noise, walking is always noticed, and walking straight at one's face is too. Idle zombies keep going the way they face,
  so wait, pick a side, and come in behind or beside it.
  Sneaking costs you: half speed (two ticks a step), no running, and it ends as soon as you fight a zombie that
  has noticed you or get hit. Fighting is never quiet: a blow carries 1.5x the weapon's noise (1.3x more for blunt
  weapons: a mace is heard from about 12 tiles), halved for a stealth strike. Everything within earshot goes to look
  (more rattled the closer it is, never past "about to notice you" without seeing you). The web build has a SNEAK button and a "Strike" action for this.
* **Stamina and the march.** Every step costs stamina (1.5 walking, 3 running, 0.4 creeping, half as much again in shallow
  water); standing still, resting and creeping win it back faster than they spend it. Marching nonstop empties the tank in about
  130 steps: below 20 you are winded (every other step takes two ticks), at zero you are exhausted (every step takes two) and
  cannot run. Running burns out in about 30 steps. Fast dead will catch a tired walker; stop, creep or rest to recover.
* **Noise is the game.** Every action makes noise; loud ones raise a *noise meter*. Fill it and a Stalker
  comes for you. Blades and bows are quiet; guns draw hordes. Sneak (`s`) halves what they notice.
* **Hordes are real.** Crowds roam the map, are drawn to noise, and become individual zombies when close.
  The game opens with a tide closing on the breach from every side but one.
* **Bitten?** Arm or leg: you have a short window to **cut it off** (`x`, needs a blade). It is not a free cure:
  it costs about 30 health (the first limb; the second costs nearly twice as much and will kill you unless you are
  nearly whole), permanently lowers your maximum health and stamina, and leaves a stump that bleeds until you bind
  it (a bandage only slows it, a medkit closes it). A lost leg halves your speed, stops you running and wrecks your
  evasion; a lost arm cuts your accuracy and melee damage, carries less, and rules out bows, polearms and rifles.
  Torso: suppressants only buy time. Spore presets infect through the air unless you wear a filter.
* **Injuries**: bleeding, broken legs, lost limbs. **Panic** wrecks your aim and can freeze you.
* **Day and night**: you see less in the dark, lights make you visible, some dead change at night.
* **Documents are written in a cipher.** Unknown words show as glyphs. You learn them by exposure, by
  studying, and from teachers. Deciphered documents reveal where components are, give vault codes and the
  formula; better recipes need fluency too.
* **Choices**: the road throws moral encounters at you. Humanity changes who will trade with you, how you are
  remembered, and who you face at the end.
* **Everyone fights everyone.** Zombies attack any living person they see, not just you: a patrol that
  meets a horde loses people, and what it loses gets up again (even on presets where the dead normally do not
  turn). Raiders and patrols shoot each other on sight. Gunfire draws the dead whoever fires.
* **Patrols**: enclave scouts and military soldiers walk between buildings and the raider camps. They leave
  you alone unless you attack them. Talk to one (`e`) for a tip, once, if you still look human.
* **Calls for help**: a patrol under attack shouts, and you hear it ("a call for help to the north-east").
  Kill something near them while they are in trouble and they remember: next time they thank you with a
  medical item and a lead, and trust you.
* **Companions**: ask a patrol member to come with you (`e` > ask) once they trust you (answered a call, or
  enough reputation). Up to two. They follow, fight what you fight, wait outside when you go indoors, and
  leave if you become inhuman. Tell them to go their way from the same menu.
* **Far away, in the abstract**: patrols you cannot see still walk their routes and still fight, resolved
  coarsely every 20 turns (they kill or lose to nearby dead, raiders and hordes). Over a long game the
  patrols thin out.
* **Gore disguise** (`v`): smear yourself with a corpse to walk past mindless dead.
* **The record**: when a run ends (won, dead, turned, left behind) a second page retells how it went: a
  chronicle of the moments that mattered (bites, amputations, documents deciphered, event choices, first
  visits, level-ups, hordes, boss kills, every 25th kill, survivors lost) and the last ten log lines before
  the end. Routine hits and idle chatter are left out; a long run keeps its opening and its latest events.

## Keys (press `?` in game)

`arrows/hjkl/yubn` move or attack, `.` wait, `r` rest, `g` pick up, `e` interact (crates, people, beds, bench),
`i` inventory, `c` craft, `d` documents, `p` skills, `m` places, `f` fire, `t` throw, `x` amputate,
`s` sneak, `R` run, `L` light, `v` gore, `B` briefing, `Q` save and quit.

## Layout

```
src/outbreak/
  content/   data packs: eras, zombie presets, scenarios, items, perks, recipes
  engine/    game rules; deterministic for a given seed; no I/O except save.py
  ui/        render.py (state -> drawable view, no curses) and the curses front-end
  bot.py     a simple autonomous player used for fuzzing and balance checks
tests/       unittest suite (no dependencies)
```

Adding an era or a zombie preset is a data change: add a function to `content/eras.py` or an entry in
`content/zombies.py`. Both are validated at import time, and the test suite iterates over every pack.

```
python3 -m unittest discover -s tests -t .      # ~30 s
python3 play.py --bot 1500 --era scifi --zombies spore --seed 3      # headless bot run
python3 play.py --show --seed 4                  # print the opening view
```

Saves live in `$OUTBREAK_HOME` or `~/.local/share/outbreak/`. They are Python pickles of your own game:
do not load save files from people you do not trust.

## Art credits

The web build draws with pixel sprites from **Kenney** (www.kenney.nl): *Roguelike Modern City* and
*Roguelike Characters* for every era but the medieval one, *Tiny Town* and *Tiny Dungeon* for the medieval one (its
dead are villagers gone green, plus the dungeon pack's spiders, slimes, bats and ghosts). All are **CC0** (public domain; the licence files are in `web/art/src/`). A small atlas is built
from them by `web/art/build_atlas.py` (Pillow; the result, `atlas.png` + `atlas.json`, is committed and inlined by
`web/build.py`). The zombies are the packs' green body in a torn shirt, recoloured per kind. *Settings > Pixel
sprites* turns them off and draws plain shapes instead, which is also what happens if the atlas is missing.
