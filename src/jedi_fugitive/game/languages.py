"""Ancient languages: inscriptions the Jedi cannot read until they learn the words.

Inspired by the language mechanic of No Man's Sky. Every Sith lore inscription on
the map is written in one of several dead languages. Text is shown with the words
the player has not learned replaced by alien script; words are picked up by

* **exposure**  - seeing an unknown word again and again in context,
* **study**     - deliberately decoding an inscription (better with tech and skills),
* **teachers**  - holocrons / sages / wreckage logs granting words directly,
* **fluency**   - as a language fills up, grammar and then rare words resolve on their own.

The module is pure logic (no curses): render_text() returns strings and learning
events, so it is easy to test and to reuse from any UI.
"""
import hashlib
import random
import re

# ---------------------------------------------------------------- vocabulary
# Core words: the concepts that recur in Sith lore. Learning them is the game.
CORE_WORDS = [
    "force", "power", "dark", "light", "death", "life", "fear", "peace", "war",
    "master", "apprentice", "lord", "knowledge", "truth", "strength", "weakness",
    "ancient", "forbidden", "ritual", "artifact", "tomb", "empire", "republic",
    "galaxy", "energy", "corruption", "passion", "rage", "love", "hate",
    "philosophy", "order", "fleet", "blade", "crystal", "temple",
    "sith", "jedi", "side", "darkness", "control", "fight", "victory", "weapon",
    "fate", "prophecy", "destruction", "ambition", "trials", "forge", "memory",
    "blood", "council", "hidden", "emotion", "fuel",
]
# Advanced words only become learnable once the language is partly understood.
ADVANCED_WORDS = [
    "sorcery", "essence", "dominion", "sacrifice", "betrayal", "legacy", "oath",
    "vengeance", "eternal", "shadow", "conquest", "destiny", "spirit", "holocron",
    "invocation", "dominate", "servant", "chosen", "abyss", "unity",
]
ALL_WORDS = CORE_WORDS + ADVANCED_WORDS

# Grammar particles: resolve automatically once fluency reaches FUNCTION_FLUENCY.
FUNCTION_WORDS = frozenset(
    "the a an and or but of to in on at by for from with as is are was be it its "
    "that this these those who what where when not only into through their his "
    "your you they them we our one all some every than while can will would have "
    "has had which".split()
)

FUNCTION_FLUENCY = 0.25   # grammar becomes readable
FULL_FLUENCY = 0.80       # everything else (names, rare words) becomes readable
EXPOSURE_TO_LEARN = 4     # times an unknown word is seen before it sinks in
STUDY_LIMIT = 3           # attempts per inscription
ADVANCED_FLUENCY = 0.30   # fluency needed before advanced words can be studied
FULL_TRANSLATION = 0.90   # share of content words known = "fully translated"

LANGUAGES = {
    "sith": {
        "name": "Old Sith",
        "blurb": "The harsh liturgical tongue of the first Sith Lords.",
        "syllables": ["ka", "ruk", "zar", "mor", "dra", "vek", "thul", "gor", "sha", "nak", "rul", "bar"],
        "glyphs": "ᛊᚱᛉᚦᛗᛞᚲᚷ",
    },
    "tythonian": {
        "name": "High Tythonian",
        "blurb": "The lyrical script of the earliest Force-sensitive scholars.",
        "syllables": ["ae", "li", "ori", "sel", "an", "ith", "el", "ura", "ven", "isa", "om", "yl"],
        "glyphs": "ᚠᚢᚨᚹᛟᛁᛃᛈ",
    },
    "rakatan": {
        "name": "Rakatan",
        "blurb": "The cold machine-tongue of the Infinite Empire. Key to its technology.",
        "syllables": ["xi", "tek", "qor", "zun", "pha", "ix", "ren", "kot", "ul", "vim", "syx", "dro"],
        "glyphs": "ᛜᛝᛠᛡᛢᛣᛤᛥ",
    },
    "mando": {
        "name": "Proto-Mandalorian",
        "blurb": "Blunt war-chants of the clans that once fought Jedi and Sith alike.",
        "syllables": ["ba", "ke", "or", "tor", "ad", "jet", "sol", "kar", "ne", "ru", "ha", "gar"],
        "glyphs": "ᚾᛅᛆᛐᛑᛒᛓᛔ",
    },
}

# which language each lore category is written in
CATEGORY_LANGUAGE = {
    "sith_lords": "sith",
    "sith_philosophy": "sith",
    "sith_sorcery": "sith",
    "sith_history": "tythonian",
    "sith_artifacts": "rakatan",
}
DEFAULT_MIX = ("sith", "tythonian", "rakatan", "mando")


def _rng(*parts):
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big"))


_native_cache = {}


def native_word(lang_id, meaning):
    """Deterministic native form of an English word in the given language."""
    key = (lang_id, meaning)
    if key in _native_cache:
        return _native_cache[key]
    lang = LANGUAGES[lang_id]
    r = _rng("word", lang_id, meaning)
    n = 2 if len(meaning) <= 5 else 3
    w = "".join(r.choice(lang["syllables"]) for _ in range(n))
    _native_cache[key] = w
    return w


def _native_lookup(lang_id):
    return {native_word(lang_id, m): m for m in ALL_WORDS}


def pseudo_word(lang_id, word):
    """Alien-looking stand-in for a word that has no dictionary entry."""
    lang = LANGUAGES[lang_id]
    r = _rng("pseudo", lang_id, word.lower())
    n = max(1, min(4, (len(word) + 2) // 3))
    out = "".join(r.choice(lang["syllables"]) for _ in range(n))
    return out


# ---------------------------------------------------------------- player state
def ensure_state(player):
    if not hasattr(player, "lexicon") or not isinstance(player.lexicon, dict):
        player.lexicon = {}
    for lid in LANGUAGES:
        st = player.lexicon.setdefault(lid, {})
        st.setdefault("known", set())
        st.setdefault("seen", {})
    if not hasattr(player, "inscriptions") or not isinstance(player.inscriptions, dict):
        player.inscriptions = {}
    if not hasattr(player, "translated_entries") or not isinstance(player.translated_entries, set):
        player.translated_entries = set()
    if not hasattr(player, "study_counts") or not isinstance(player.study_counts, dict):
        player.study_counts = {}
    return player.lexicon


def known_words(player, lang_id):
    return ensure_state(player)[lang_id]["known"]


def fluency(player, lang_id):
    """Share of the language's core+advanced vocabulary the player knows (0..1)."""
    return len(known_words(player, lang_id)) / float(len(ALL_WORDS))


def fluency_label(f):
    if f >= FULL_FLUENCY:
        return "Fluent"
    if f >= 0.5:
        return "Proficient"
    if f >= FUNCTION_FLUENCY:
        return "Conversational"
    if f > 0:
        return "Glimmers"
    return "Unknown"


def language_for(landmark, pos=None):
    """Language a landmark is inscribed in (decided once, then remembered)."""
    if "language" in landmark:
        return landmark["language"]
    cat = (landmark.get("sith_lore") or {}).get("category")
    lid = CATEGORY_LANGUAGE.get(cat)
    if lid is None:
        lid = _rng("lang", pos).choice(DEFAULT_MIX)
    landmark["language"] = lid
    return lid


# ---------------------------------------------------------------- learning
def learn_word(player, lang_id, meaning):
    """Add a word. Returns True when it was new."""
    known = known_words(player, lang_id)
    if meaning in known or meaning not in ALL_WORDS:
        return False
    known.add(meaning)
    return True


def unknown_words(player, lang_id, advanced=True):
    known = known_words(player, lang_id)
    pool = ALL_WORDS if advanced else CORE_WORDS
    return [w for w in pool if w not in known]


def grant_words(player, lang_id, n=3, rng=None):
    """Teacher/holocron: learn up to n random words. Returns the words learned."""
    rng = rng or random
    pool = unknown_words(player, lang_id, advanced=fluency(player, lang_id) >= ADVANCED_FLUENCY)
    rng.shuffle(pool)
    got = []
    for w in pool[:n]:
        if learn_word(player, lang_id, w):
            got.append(w)
    return got


_TOKEN = re.compile(r"[A-Za-z']+|[^A-Za-z']+")


def _stem(word):
    w = word.lower()
    if w.endswith("'s"):
        w = w[:-2]
    for suf in ("ies", "es", "s"):
        if w not in ALL_WORDS and w.endswith(suf) and w[: -len(suf)] in ALL_WORDS:
            return w[: -len(suf)], suf
    return w, ""


def render_text(player, lang_id, text, observe=True):
    """Render `text` as the player currently understands it.

    Returns (rendered, info). info = {
        'learned': [meanings picked up by exposure],
        'unknown': [dictionary meanings in the text the player still lacks],
        'content': number of dictionary words in the text,
        'known': how many of those the player knows,
    }
    """
    ensure_state(player)
    st = player.lexicon[lang_id]
    flu = fluency(player, lang_id)
    out = []
    unknown = []
    content = known_cnt = 0
    learned = []
    try:
        from jedi_fugitive.game import jedi_skills
        needed = max(2, EXPOSURE_TO_LEARN - int(jedi_skills.bonus(player, "exposure")))
    except Exception:
        needed = EXPOSURE_TO_LEARN
    for tok in _TOKEN.findall(text):
        if not re.match(r"[A-Za-z']", tok):
            out.append(tok)
            continue
        stem, suffix = _stem(tok)
        cap = tok[0].isupper()
        if stem in ALL_WORDS:
            content += 1
            if stem in st["known"]:
                known_cnt += 1
                out.append(tok)
            else:
                unknown.append(stem)
                nat = native_word(lang_id, stem) + (suffix and "s" or "")
                out.append(nat.capitalize() if cap else nat)
                if observe:
                    seen = st["seen"]
                    seen[stem] = seen.get(stem, 0) + 1
                    adv_ok = stem in CORE_WORDS or flu >= ADVANCED_FLUENCY
                    if adv_ok and seen[stem] >= needed and learn_word(player, lang_id, stem):
                        learned.append(stem)
        elif stem in FUNCTION_WORDS:
            out.append(tok if flu >= FUNCTION_FLUENCY else _particle(lang_id, stem))
        else:
            out.append(tok if flu >= FULL_FLUENCY else _fmt_pseudo(lang_id, tok, cap))
    info = {"learned": learned, "unknown": sorted(set(unknown)), "content": content, "known": known_cnt}
    if learned:
        # words just learned should already read in clear on this pass
        return render_text(player, lang_id, text, observe=False)[0], info
    return "".join(out), info


def _particle(lang_id, stem):
    w = pseudo_word(lang_id, "~" + stem)
    return w[:2] if len(w) > 2 else w


def _fmt_pseudo(lang_id, tok, cap):
    w = pseudo_word(lang_id, tok)
    return w.capitalize() if cap else w


def completion(player, lang_id, text):
    """Fraction of the text's dictionary words the player knows (1.0 if none)."""
    _, info = render_text(player, lang_id, text, observe=False)
    if info["content"] == 0:
        return 1.0
    return info["known"] / float(info["content"])


# ---------------------------------------------------------------- studying
def study_chance(player, lang_id):
    """Chance that one study attempt decodes a word."""
    base = 0.50
    try:
        from jedi_fugitive.game import jedi_skills, tech
        base += jedi_skills.bonus(player, "translate")
        base += tech.translator_bonus(player, lang_id)
    except Exception:
        pass
    base += 0.15 * fluency(player, lang_id)
    return max(0.10, min(0.95, base))


def study(player, lang_id, key, text, rng=None):
    """Try to decode words of an inscription. Returns (messages, spent_turn)."""
    rng = rng or random
    ensure_state(player)
    used = player.study_counts.get(key, 0)
    if used >= STUDY_LIMIT:
        return ["You have squeezed every insight you can from this inscription for now."], False
    player.study_counts[key] = used + 1
    _, info = render_text(player, lang_id, text, observe=False)
    flu = fluency(player, lang_id)
    cands = [w for w in info["unknown"] if w in CORE_WORDS or flu >= ADVANCED_FLUENCY]
    lname = LANGUAGES[lang_id]["name"]
    if not cands:
        if info["unknown"]:
            return [f"The remaining {lname} words are beyond you. Learn the basics first."], True
        return [f"There is nothing left to learn from this {lname} text."], True
    msgs = []
    tries = 1
    try:
        from jedi_fugitive.game import tech
        tries += tech.translator_extra_words(player)
        from jedi_fugitive.game import jedi_skills
        tries += int(jedi_skills.bonus(player, "study_words"))
    except Exception:
        pass
    rng.shuffle(cands)
    for w in cands[:tries]:
        if rng.random() <= study_chance(player, lang_id):
            learn_word(player, lang_id, w)
            msgs.append(f"You decode a {lname} word: {native_word(lang_id, w)} = '{w}'.")
        else:
            msgs.append(f"You puzzle over the strange {lname} glyphs but the meaning slips away.")
    return msgs, True


# ---------------------------------------------------------------- reading
def read_inscription(player, key, lang_id, title, text, observe=True):
    """Show an inscription. Returns (rendered, messages).

    Archives it so it can be re-read later with better vocabulary, and pays out a
    one-time reward the first time it is fully understood.
    """
    ensure_state(player)
    rendered, info = render_text(player, lang_id, text, observe=observe)
    msgs = []
    lname = LANGUAGES[lang_id]["name"]
    player.inscriptions[key] = {"lang": lang_id, "title": title, "text": text}
    for w in info["learned"]:
        msgs.append(f"[{lname}] Through repetition, '{native_word(lang_id, w)}' finally means '{w}'.")
    msgs.extend(check_full_translation(player, key, lang_id, title, text))
    return rendered, msgs


def check_full_translation(player, key, lang_id, title, text):
    ensure_state(player)
    if key in player.translated_entries:
        return []
    if completion(player, lang_id, text) < FULL_TRANSLATION:
        return []
    player.translated_entries.add(key)
    msgs = [f"** You have fully translated '{title}'! **"]
    try:
        player.gain_xp(40)
        msgs.append("The lost knowledge settles in your mind. +40 XP")
    except Exception:
        pass
    n = len(player.translated_entries)
    if n % 3 == 0:
        try:
            player.skill_points = getattr(player, "skill_points", 0) + 1
            msgs.append("Your scholarship deepens: +1 Skill Point (press O).")
        except Exception:
            pass
    return msgs


# ---------------------------------------------------------------- lexicon UI
def lexicon_rows(player):
    """[(language name, fluency, label, known, total, blurb)] for the lexicon screen."""
    ensure_state(player)
    rows = []
    for lid, lang in LANGUAGES.items():
        f = fluency(player, lid)
        rows.append((lid, lang["name"], f, fluency_label(f), len(known_words(player, lid)), len(ALL_WORDS), lang["blurb"]))
    return rows


def dictionary_lines(player, lang_id):
    lang = LANGUAGES[lang_id]
    known = known_words(player, lang_id)
    lines = [f"{lang['name']} - {fluency_label(fluency(player, lang_id))} "
             f"({len(known)}/{len(ALL_WORDS)} words)", ""]
    for w in ALL_WORDS:
        if w in known:
            lines.append(f"  {native_word(lang_id, w):<12} = {w}")
        else:
            lines.append(f"  {native_word(lang_id, w):<12} = ???")
    return lines
