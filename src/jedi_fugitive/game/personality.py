from enum import Enum
import random

ENEMY_TAUNTS = {
    "attack": [
        "You will fall before the Empire!",
        "Feel the power of the dark side!",
        "Your Jedi tricks won't save you!",
    ],
    "defend": [
        "I am one with the Force!",
        "You cannot break me!",
        "Stand down, rebel!",
    ],
    "low_hp": [
        "This isn't over!",
        "I will avenge my brothers!",
        "You... will... pay!",
    ],
}

class EnemyPersonality:
    def __init__(self):
        self.taunts = ENEMY_TAUNTS

    def get_taunt(self, situation):
        import random
        return random.choice(self.taunts.get(situation, ["..."]))