"""Menus for the mastery systems: Lexicon (N), Jedi skills (O) and Technology (I).

Each open_* function returns True when the action should consume a turn.
"""
import textwrap

from jedi_fugitive.game import languages, jedi_skills, tech


def _say(game, text):
    try:
        game.ui.messages.add(text)
    except Exception:
        pass


def _say_wrapped(game, text, width=68, prefix=""):
    for i, ln in enumerate(textwrap.wrap(text, width) or [""]):
        _say(game, (prefix if i == 0 else " " * len(prefix)) + ln)


def _show_text(game, lines, title=""):
    """Blocking text dialog when interactive, else the message log."""
    ui = getattr(game, "ui", None)
    try:
        if ui is not None and hasattr(ui, "centered_dialog"):
            res = ui.centered_dialog(list(lines) + ["", "Press any key..."], title=title)
            if res is not None:
                return
    except Exception:
        pass
    for ln in lines:
        _say(game, ln)


def _menu(game, items, title):
    try:
        return game.ui.popup_dialogue(items, title=title)
    except Exception:
        return None


# ---------------------------------------------------------------- inscriptions
def landmark_here(game):
    pos = (int(game.player.x), int(game.player.y))
    info = (getattr(game, "map_landmarks", {}) or {}).get(pos)
    if info and "sith_lore" in info:
        return pos, info
    return None, None


def read_landmark(game, pos, info):
    """Called when the player steps on an inscription. Shows it as currently understood."""
    p = game.player
    lore = info.get("sith_lore") or {}
    text = lore.get("content") or " ".join(info.get("lore", []))
    lid = languages.language_for(info, pos)
    lname = languages.LANGUAGES[lid]["name"]
    title = lore.get("title", "Inscription")
    rendered, msgs = languages.read_inscription(p, pos, lid, title, text)
    _say(game, f"[{lname} inscription] {title}")
    _say_wrapped(game, rendered, prefix="  ")
    _, stats = languages.render_text(p, lid, text, observe=False)
    if stats["unknown"]:
        _say(game, f"  ({stats['known']}/{stats['content']} key words understood - press N to study it)")
    for m in msgs:
        _say(game, m)


def study_here(game):
    pos, info = landmark_here(game)
    if info is None:
        _say(game, "There is no inscription here to study. Find a glowing lore stone.")
        return False
    p = game.player
    lore = info["sith_lore"]
    lid = languages.language_for(info, pos)
    text = lore.get("content", "")
    msgs, spent = languages.study(p, lid, pos, text)
    for m in msgs:
        _say(game, m)
    rendered, more = languages.read_inscription(p, pos, lid, lore.get("title", "Inscription"), text, observe=False)
    for m in more:
        _say(game, m)
    _say_wrapped(game, rendered, prefix="  ")
    return spent


def open_lexicon(game):
    p = game.player
    while True:
        items = [
            ("Study the inscription here", "Spend a turn decoding words of the lore stone you stand on.", {}),
            ("Archived inscriptions", "Re-read every inscription you have found with what you know now.", {}),
        ]
        for lid, name, f, label, k, total, blurb in languages.lexicon_rows(p):
            items.append((f"{name}: {label} ({k}/{total})", blurb, {}))
        choice = _menu(game, items, "LEXICON")
        if choice is None:
            return False
        if choice == 0:
            return study_here(game)
        if choice == 1:
            _open_archive(game)
        else:
            lid = list(languages.LANGUAGES)[choice - 2]
            _show_text(game, languages.dictionary_lines(p, lid), title=languages.LANGUAGES[lid]["name"])


def _open_archive(game):
    p = game.player
    ins = getattr(p, "inscriptions", {}) or {}
    if not ins:
        _say(game, "You have not found any inscriptions yet.")
        return
    keys = list(ins)
    items = []
    for k in keys:
        rec = ins[k]
        f = languages.completion(p, rec["lang"], rec["text"])
        items.append((rec["title"], f"{languages.LANGUAGES[rec['lang']]['name']} - {int(f * 100)}% understood", {}))
    choice = _menu(game, items, "ARCHIVED INSCRIPTIONS")
    if choice is None or not (0 <= choice < len(keys)):
        return
    rec = ins[keys[choice]]
    rendered, _ = languages.render_text(p, rec["lang"], rec["text"], observe=False)
    _show_text(game, textwrap.wrap(rendered, 66), title=rec["title"])


# ---------------------------------------------------------------- skills
def open_skills(game):
    p = game.player
    jedi_skills.ensure_state(p)
    while True:
        items = []
        nodes = []
        for tid, tname in jedi_skills.TREES.items():
            for n in jedi_skills.tree_nodes(tid):
                name, desc = jedi_skills.node_line(p, n)
                items.append((f"{tname[:6]:<6} | {name}", desc, {}))
                nodes.append(n)
        title = f"JEDI SKILLS  (points: {p.skill_points})"
        choice = _menu(game, items, title)
        if choice is None or not (0 <= choice < len(nodes)):
            return False
        ok, msg = jedi_skills.learn(p, nodes[choice].id, game)
        _say(game, msg if ok else f"Cannot learn {nodes[choice].name}: {msg}")


# ---------------------------------------------------------------- technology
def open_tech(game):
    p = game.player
    tech.ensure_state(p)
    while True:
        rows = tech.device_rows(p)
        items = []
        for did, name, t, desc, status in rows:
            cd = tech.cooldown_left(p, game, did) if tech.DEVICES[did].kind == "active" and t else 0
            extra = f"  [recharging {cd}]" if cd else ""
            items.append((f"{name}  T{t}{extra}", f"{desc}\n{status}", {}))
        choice = _menu(game, items, "TECHNOLOGY")
        if choice is None or not (0 <= choice < len(rows)):
            return False
        did = rows[choice][0]
        ok, why = tech.can_build(p, did)
        if ok:
            _ok, msg = tech.build(p, did)
            _say(game, msg)
            continue
        dev = tech.DEVICES[did]
        if dev.kind == "active" and tech.tier(p, did):
            used, msgs = tech.use(p, game, did)
            for m in msgs:
                _say(game, m)
            if used:
                return True
            continue
        _say(game, why)


def use_device(game, device_id):
    """Hotkey path for active devices."""
    used, msgs = tech.use(game.player, game, device_id)
    for m in msgs:
        _say(game, m)
    return used
