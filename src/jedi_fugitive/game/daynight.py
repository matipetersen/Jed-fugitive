"""
Day and night on the surface, derived from the world clock (turn_count).

One day lasts DAY_TICKS world ticks; the crash happens in the late afternoon.
Underground (tombs) there is no sky: everything here is neutral there.

  phase   sight      hiding    camp risk
  dawn    -1         +5%       +0
  day      0          0        -5%
  dusk    -1         +5%       +0
  night   -2         +15%      +15%  (a fire is visible from far away)

Night is the fugitive's friend and enemy: harder to be seen, harder to see,
and a dangerous time to stop and rest.
"""
DAY_TICKS = 480
START_OFFSET = 240          # the crash: late afternoon
PHASES = (                  # (start, name) as a fraction of the day
    (0.00, 'dawn'),
    (0.10, 'day'),
    (0.60, 'dusk'),
    (0.70, 'night'),
)
SIGHT = {'dawn': -1, 'day': 0, 'dusk': -1, 'night': -2}
HIDE = {'dawn': 5, 'day': 0, 'dusk': 5, 'night': 15}
CAMP = {'dawn': 0.0, 'day': -0.05, 'dusk': 0.0, 'night': 0.15}
# how dark the graphical map gets (0 = none, 1 = black)
DARKNESS = {'dawn': 0.25, 'day': 0.0, 'dusk': 0.3, 'night': 0.55}


def underground(game):
    return bool(getattr(game, 'tomb_levels', None)) and hasattr(game, 'tomb_floor')


def time_of_day(game):
    """Fraction of the current day elapsed, 0.0-1.0."""
    t = int(getattr(game, 'turn_count', 0) or 0) + START_OFFSET
    return (t % DAY_TICKS) / DAY_TICKS


def phase(game):
    f = time_of_day(game)
    name = PHASES[0][1]
    for start, n in PHASES:
        if f >= start:
            name = n
    return name


def sight_modifier(game):
    return 0 if underground(game) else SIGHT[phase(game)]


def hide_bonus(game):
    return 0 if underground(game) else HIDE[phase(game)]


def camp_risk_modifier(game):
    return 0.0 if underground(game) else CAMP[phase(game)]


def darkness(game):
    return 0.0 if underground(game) else DARKNESS[phase(game)]


def clock_label(game):
    """'Dusk 18:40' style label (a 24h clock spread over DAY_TICKS)."""
    minutes = int(time_of_day(game) * 24 * 60)
    # the day fraction starts at dawn (~05:00)
    minutes = (minutes + 5 * 60) % (24 * 60)
    return f"{phase(game).title()} {minutes // 60:02d}:{minutes % 60:02d}"


_ANNOUNCE = {
    'dawn': "#3#The sky pales. Dawn is coming.#0#",
    'day': "The sun is up. You are easier to see, and so is everything else.",
    'dusk': "#3#The light is failing. Dusk settles over the ruins.#0#",
    'night': "#5#Night falls. Harder to see, harder to be seen. A campfire now would be a beacon.#0#",
}


def tick(game):
    """Announce phase changes on the surface."""
    if underground(game):
        return
    now = phase(game)
    last = getattr(game, '_daynight_phase', None)
    game._daynight_phase = now
    if last is not None and last != now:
        try:
            game.add_message(_ANNOUNCE[now])
        except Exception:
            pass
