from time import strftime
import curses
from typing import List, Dict, Any, Tuple
import re

_COLOR_CODE = re.compile(r'#(\d{1,2})#')


def parse_color_codes(text: str, default: int = 3) -> List[Tuple[str, int]]:
    """Split "#N#text#0#" markup into (segment, colour_pair) runs. #0# restores the default."""
    out = []
    pair = default
    pos = 0
    for m in _COLOR_CODE.finditer(text):
        if m.start() > pos:
            out.append((text[pos:m.start()], pair))
        n = int(m.group(1))
        pair = default if n == 0 else n
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], pair))
    return out


def strip_color_codes(text: str) -> str:
    return _COLOR_CODE.sub('', str(text))

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
        # Deduplicate FIRST for performance (early exit)
        if self.messages and self.messages[-1].get("text") == text:
            return
            
        # Parse color tags like #3#[EVENT]#0# message text (OPTIMIZED)
        if text.startswith('#') and '#0#' in text:
            import re
            color_match = re.match(r'^#(\d+)#(.+?)#0#(.*)$', text)
            if color_match:
                color = int(color_match.group(1))
                highlighted_part = color_match.group(2)
                rest_of_message = color_match.group(3)
                text = highlighted_part + rest_of_message
        self.messages.append({"timestamp": strftime("%H:%M:%S"), "text": text, "color": color})
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]