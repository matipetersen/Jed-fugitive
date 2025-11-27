"""
Pursuit & Detection System
Tracks player detection level and manages Sith Predator AI.
"""

class PursuitSystem:
    def __init__(self, player):
        self.player = player
        self.detection_level = 0  # 0-100
        self.last_force_use_turn = None
        self.last_combat_turn = None
        self.sith_predator_active = False

    def update_detection(self, action_type, stealth=False, disguise_bonus=0):
        """
        Update detection based on player actions.
        action_type: 'force', 'combat', 'stealth', etc.
        """
        if action_type == 'force':
            self.detection_level += 20
            self.last_force_use_turn = self.player.turn_count
        elif action_type == 'combat':
            self.detection_level += 10
            self.last_combat_turn = self.player.turn_count
        elif action_type == 'stealth':
            self.detection_level = max(0, self.detection_level - 10)
        self.detection_level = max(0, min(100, self.detection_level - disguise_bonus))

    def check_predator_spawn(self):
        if self.detection_level >= 70 and not self.sith_predator_active:
            self.sith_predator_active = True
            # TODO: Spawn Sith Predator AI
            return True
        return False

    def decay_detection(self):
        # Detection decays over time
        if self.detection_level > 0:
            self.detection_level -= 1

# Usage: Attach PursuitSystem to player or game manager
