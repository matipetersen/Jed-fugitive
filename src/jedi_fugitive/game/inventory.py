from typing import List, Any

class Inventory:
    def __init__(self):
        self.items: List[Any] = []

    def add(self, item: Any):
        self.items.append(item)

    def remove(self, index: int):
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None

    def list_items(self):
        return list(self.items)