# OUTBREAK for phones and browsers

`dist/outbreak.html` is the whole game in one file: no install, no network needed once the page is open
(the three web fonts are optional and fall back to system fonts). Open it in any modern mobile browser.

```
python3 web/build.py          # builds dist/outbreak.html (and dist/outbreak.fragment.html)
node web/test/run_all.js      # engine tests: world, interiors, full playthroughs, rules, save/load
```

## How it relates to the terminal game

The JavaScript engine in `src/*.js` is a port of the Python engine in `src/outbreak/engine`, with the same
function and field names so the two stay easy to compare. Game data (eras, zombie presets, scenarios, items,
perks, recipes, moral encounters, endings) is **exported from the Python packs by `build.py`**, so adding an era
or a zombie preset in Python shows up here after a rebuild. The two engines use different random number
generators, so the same seed does not give the same world in both.

The story briefing (three pages) opens when a new game starts; the menu has a **Briefing** tile to read it again.
The new-game screen has a *How it starts* choice (or *Surprise me*).

## Touch controls

* **Pad** (bottom left): hold to keep moving. The centre dot waits; hold it to rest.
* **Tap a tile** to walk there; you stop when an enemy appears. Tap an adjacent enemy to hit it, a far enemy to
  shoot it (ranged weapon equipped). Long-press a tile to see what it is. Pinch to zoom.
* **ACT** changes with context: pick up, search, talk, sleep, unlock, rest.
* **FIRE**, **BAG**, **MENU**. The menu holds craft, documents, skills, places, throw, sneak, run, light, settings.
* A red **CUT IT OFF** button appears when an arm or leg bite can still be amputated.
* Settings: left-handed layout, zoom, tap-to-travel, vibration.

The run autosaves to the browser's local storage (every 100 turns, when the page is hidden, and from the
menu). If the browser blocks storage the game tells you and plays without saving.
