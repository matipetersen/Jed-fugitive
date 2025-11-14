from time import strftime
import random
from typing import List, Dict, Any

class DialogueSystem:
    def __init__(self):
        self.enemy_dialogues = {
            "STORMTROOPER": ["Stop right there!", "For the Empire!"],
            "SITH_GHOST": ["The dark side calls...", "You cannot hide!"],
            "INQUISITOR": ["Give in to the dark side!", "Your hope dies here!"]
        }

    def get_enemy_dialogue(self, enemy_key: str) -> str:
        lines = self.enemy_dialogues.get(enemy_key, ["..."])
        return random.choice(lines)

class UIMessageBuffer:
    def __init__(self, max_messages: int = 200):
        self.messages: List[Dict[str, Any]] = []
        self.max_messages = max_messages

    def add(self, text: str, color: int = 0):
        self.messages.append({"timestamp": strftime("%H:%M:%S"), "text": text, "color": color})
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]