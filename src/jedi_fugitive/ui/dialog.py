from time import strftime
import curses
from typing import List, Dict, Any

class DialogueSystem:
    def __init__(self):
        self.enemy_lines = {
            "STORMTROOPER": ["Stop right there!", "For the Empire!"],
            "SITH_GHOST": ["The dark side calls...", "You cannot hide!"]
        }

    def random_line(self, enemy_key: str) -> str:
        import random
        lines = self.enemy_lines.get(enemy_key, ["..."])
        return random.choice(lines)

class UIMessageBuffer:
    def __init__(self, max_messages: int = 200):
        self.messages: List[Dict[str, Any]] = []
        self.max_messages = max_messages

    def add(self, text: str, color: int = 0):
        # Deduplicate: don't add if the last message is identical (fixes Windows display issue)
        if self.messages and self.messages[-1].get("text") == text:
            return
        self.messages.append({"timestamp": strftime("%H:%M:%S"), "text": text, "color": color})
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]