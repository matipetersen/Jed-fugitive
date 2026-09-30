"""Colour palette and sizing for the pygame front-end.

The game code still speaks in curses colour pairs (1..15) built from the eight
ANSI colours. Here those ANSI colours are remapped to a modern dark palette so
every existing ``curses.color_pair(n)`` call picks up the new look for free.
"""

# ANSI colour index -> RGB (curses.COLOR_BLACK .. COLOR_WHITE)
ANSI = {
    0: (14, 16, 26),      # black  -> deep space
    1: (255, 92, 112),    # red    -> sith crimson
    2: (110, 224, 150),   # green  -> vital green
    3: (255, 198, 92),    # yellow -> warm amber
    4: (104, 146, 255),   # blue   -> steel blue
    5: (196, 128, 255),   # magenta-> force violet
    6: (86, 214, 255),    # cyan   -> jedi cyan
    7: (214, 222, 242),   # white  -> soft white
}

# Default text colour when a pair uses -1 (terminal default)
DEFAULT_FG = (200, 208, 230)

# Window chrome
BG_TOP = (9, 11, 20)
BG_BOTTOM = (18, 14, 30)
PANEL_BG = (17, 20, 33, 238)
DIALOG_BG = (24, 28, 46, 250)
PANEL_BORDER = (58, 68, 104)
DIALOG_BORDER = (96, 168, 255)
TITLE_BG = (30, 36, 60, 255)
PANEL_RADIUS = 10

# World palette -------------------------------------------------------------
FLOOR = {
    'plains': (86, 82, 88),
    'forest': (50, 90, 62),
    'desert': (156, 128, 82),
    'rocky': (98, 92, 102),
    'river': (64, 98, 80),      # riverbank grass; the water itself is '~'
    'mountain_pass': (104, 92, 84),
    'tomb': (62, 52, 78),
}
WALL = (78, 88, 120)
WALL_TOMB = (70, 52, 84)
TREE_CANOPY = (46, 120, 70)
TREE_LIGHT = (92, 170, 104)
ROCK = (118, 112, 122)
MEMORY_TINT = (40, 56, 96)      # explored-but-not-visible tiles fade towards this
VOID = (6, 7, 12)

PLAYER_BY_CORRUPTION = [
    (0, (86, 214, 255)),    # pure light: cyan
    (25, (140, 170, 255)),  # tinted
    (50, (255, 198, 92)),   # wavering: amber
    (75, (255, 70, 90)),    # fallen: crimson
]

SABER_BY_CORRUPTION = [
    (0, (90, 200, 255)),
    (25, (120, 255, 150)),
    (50, (210, 120, 255)),
    (75, (255, 40, 60)),
]

ENEMY = (235, 70, 90)
ENEMY_SITH = (200, 40, 80)
ENEMY_HALLUCINATION = (150, 120, 200)

TOKEN_COLORS = {
    '$': (255, 206, 84),     # gold
    '!': (255, 110, 150),    # potion / stim
    ':': (140, 220, 120),    # food
    '&': (200, 120, 255),    # artifact
    '>': (255, 186, 90),     # stairs down
    '<': (110, 210, 255),    # stairs up
}
POI_COLOR = (220, 180, 120)
MATERIAL_COLOR = (150, 200, 220)
DANGER_COLOR = (255, 70, 90)

RETICLE = {
    'force': (196, 128, 255),
    'gun': (255, 92, 112),
    'grenade': (255, 198, 92),
}

BAR_HP = ((255, 92, 112), (255, 150, 110))
BAR_FORCE = ((96, 150, 255), (150, 110, 255))
BAR_STRESS = ((255, 170, 60), (255, 80, 60))
BAR_XP = ((110, 224, 150), (86, 214, 255))


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def scale(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


def by_threshold(table, value):
    col = table[0][1]
    for threshold, c in table:
        if value >= threshold:
            col = c
    return col
