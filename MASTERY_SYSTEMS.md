# Mastery systems: languages, Jedi skills, technology

Keys: **N** Lexicon, **O** Jedi skills, **I** Technology.

## Ancient languages (`game/languages.py`)
Every Sith lore stone is written in one of four dead languages (Old Sith, High Tythonian, Rakatan,
Proto-Mandalorian; chosen by lore category). Unknown words show as alien script.
Words are learned by:
- **Exposure** - seeing an unknown word 4 times (Linguist's Ear skill lowers this).
- **Study (N on a stone)** - up to 3 attempts per stone; success rises with the Holo-Translator and the
  Ancient Tongues skill.
- **Absorbing** a lore stone (Dark choice) grants 3 words of its language.
- **Fluency** - at 25% grammar words resolve; at 80% names and rare words do too.
Fully translating a stone (90% of its key words) gives XP, and every 3rd one gives a Skill Point.
All found inscriptions are archived and can be re-read as your vocabulary grows.

## Jedi skills (`game/jedi_skills.py`)
Three trees (Blade, Force Mastery, Lorekeeper) of ranked nodes with prerequisites, level gates and
Light/Dark gates. Points: 2 at start, +1 per level-up, +1 per 3 translated stones. Nodes grant stats,
Force energy/regeneration, cheaper Force costs, stress resistance, sight, translation bonuses and unlock
Force abilities (Speed, Sight, Blink, Burst, Stun/Protect, Choke, Drain).

## Technology (`game/tech.py`)
Five devices with three tiers each, built from crafting materials: Holo-Translator, Signal Scanner
(finds untranslated stones), Kinetic Shield Emitter, Field Med-Unit and Kyber Focus Lattice.
Tier 2 and 3 require Rakatan fluency (15% / 30%), tying language to technology.

State (skills, lexicon, archive, tech) is written to saves under `mastery`.
