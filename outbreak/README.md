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
* `extraction` - gather three parts, reach the extraction point before the way out closes on day 10.

Both end with a hold-out finale. Who shows up depends on your **humanity**: the Alpha if you stayed human,
armed people who have heard about you if you did not.

**Opening** (how the story starts): you do not begin in a vacuum. Pick, or let the game pick from who you are,
a scene: studying, preparing a meal, out hunting, on your rounds, standing watch, fixing things, at the market,
a funeral vigil. Each has its own text per era and small consequences (a ranged weapon and food for the hunter, a
bigger vocabulary for the student, armour for the guard, a steadier conscience at the vigil, the hour you
start at). A three-page briefing (the scene, the world and what the dead are, what you must do) plays before
the first turn; `B` re-reads it.

## How it plays

* **Noise is the game.** Every action makes noise; loud ones raise a *noise meter*. Fill it and a Stalker
  comes for you. Blades and bows are quiet; guns draw hordes. Sneak (`s`) halves what they notice.
* **Hordes are real.** Crowds roam the map, are drawn to noise, and become individual zombies when close.
  The game opens with a tide closing on the breach from every side but one.
* **Bitten?** Arm or leg: you have a short window to **cut it off** (`x`, needs a blade). Torso: suppressants
  only buy time. Spore presets infect through the air unless you wear a filter.
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
  you alone unless you attack them. Talk to one (`e`) for a tip, once, if you still look human. Only people
  near you are simulated, so a fight you are not close to does not happen.
* **Gore disguise** (`v`): smear yourself with a corpse to walk past mindless dead.

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
