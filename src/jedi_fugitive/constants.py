from enum import Enum

class GameState(Enum):
    EXPLORING = 1
    IN_COMBAT = 2
    GAME_OVER = 3
    VICTORY = 4

class UIPanel(Enum):
    MAP = 1
    STATS = 2
    ABILITIES = 3
    MESSAGES = 4
    COMMANDS = 5

class ForceAbilityTier(Enum):
    BASIC = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    MASTER = 4

class ForceSchool(Enum):
    TELEKINESIS = 1
    BODY = 2
    MIND = 3
    ENERGY = 4

class LevelUpOption(Enum):
    MAX_HP = 1
    FORCE_POWER = 2
    ACCURACY = 3
    EVASION = 4
    CRITICAL_CHANCE = 5