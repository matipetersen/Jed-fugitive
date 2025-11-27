"""
Corruption & Moral Choices System
Tracks corruption from dark side actions and locks/unlocks powers.
"""

class CorruptionSystem:
    def __init__(self, player):
        self.player = player

    def adjust_corruption(self, amount):
        self.player.dark_corruption = max(0, min(100, self.player.dark_corruption + amount))
        # Effects at thresholds
        if self.player.dark_corruption >= 80:
            self.lock_light_side_powers()
            self.strengthen_dark_side_powers()
        elif self.player.dark_corruption >= 50:
            self.warn_animals_avoid()
        elif self.player.dark_corruption >= 20:
            self.warn_npcs_wary()

    def lock_light_side_powers(self):
        # Lock light side powers (example: set unlocked=False)
        for ab in getattr(self.player, 'force_abilities', {}).values():
            if getattr(ab, 'alignment', None) == 'light':
                ab.unlocked = False

    def strengthen_dark_side_powers(self):
        # Strengthen dark side powers (example: reduce cost)
        for ab in getattr(self.player, 'force_abilities', {}).values():
            if getattr(ab, 'alignment', None) == 'dark':
                ab.base_cost = max(1, ab.base_cost // 2)

    def warn_animals_avoid(self):
        # Placeholder: animals avoid player
        pass

    def warn_npcs_wary(self):
        # Placeholder: NPCs become wary
        pass

# Usage: Attach CorruptionSystem to player or game manager
