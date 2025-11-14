# Small config constants used by the UI and game
TARGET_WIDTH = 140
TARGET_HEIGHT = 40

# default layout proportions (used as base; UI computes dynamically)
MAP_RATIO_W = 0.68
MAP_RATIO_H = 0.65
STATS_RATIO_W = 0.16

SAVE_FILE = "jedi_fugitive_save.pkl"

# Global tuning knobs (added; non-destructive)
# Multiply enemy stat growth and difficulty by this factor (1.0 = default)
DIFFICULTY_MULTIPLIER = 1.0

# How strongly depth increases enemy difficulty per depth level (fractional)
DEPTH_DIFFICULTY_RATE = 0.20  # 20% depth-ish influence per depth step (tweak as needed)

# Map scaling: how much bigger maps should be compared to the generator's base.
# Setting to 10 will produce maps ~10x larger (both width and height scaled).
MAP_SCALE = 4