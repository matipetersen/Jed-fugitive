from enum import Enum
import random

ENEMY_TAUNTS = {
    "attack": [
        "You will fall before the Sith!",
        "Feel the power of the dark side!",
        "Your Jedi tricks won't save you!",
    ],
    "defend": [
        "I am one with the Force!",
        "You cannot break me!",
        "The dark side shields me!",
    ],
    "low_hp": [
        "This isn't over!",
        "I will avenge my brothers!",
        "You... will... pay!",
    ],
}

JEDI_MASTER_TAUNTS = {
    "attack": [
        "The Force flows through me!",
        "I will bring you back to the light!",
        "Your dark path ends here!",
    ],
    "defend": [
        "Peace is my ally!",
        "The light side protects me!",
        "Patience defeats aggression!",
    ],
    "low_hp": [
        "The Force will guide me!",
        "I sense conflict in you...",
        "There is still good in you!",
    ],
}

class EnemyPersonality:
    def __init__(self, is_jedi=False):
        self.taunts = JEDI_MASTER_TAUNTS if is_jedi else ENEMY_TAUNTS

    def get_taunt(self, situation):
        import random
        return random.choice(self.taunts.get(situation, ["..."]))