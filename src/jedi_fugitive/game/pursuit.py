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

    def check_predator_spawn(self, game):
        """Check if predator should spawn and spawn it if necessary."""
        if self.detection_level >= 100 and not self.sith_predator_active:
            self.sith_predator_active = True
            
            # Spawn Sith Predator
            try:
                from jedi_fugitive.game.enemy import Enemy, EnemyType
                
                # Find spawn position near player but not on top
                px, py = game.player.x, game.player.y
                spawn_x, spawn_y = px, py
                
                # Try to find a valid spot
                import random
                for _ in range(10):
                    dx = random.randint(-5, 5)
                    dy = random.randint(-5, 5)
                    tx, ty = px + dx, py + dy
                    if (0 <= ty < len(game.game_map) and 0 <= tx < len(game.game_map[0]) and
                        game.game_map[ty][tx] == '.'):
                        spawn_x, spawn_y = tx, ty
                        break
                
                # Create the predator
                predator = Enemy(spawn_x, spawn_y, EnemyType.SITH_ACOLYTE) # Placeholder type
                predator.name = "Sith Predator"
                predator.char = "S" # Sith symbol
                predator.hp = 150
                predator.max_hp = 150
                predator.attack = 25
                predator.defense = 10
                predator.xp_value = 500
                
                game.enemies.append(predator)
                
                if hasattr(game.ui, 'messages'):
                    game.ui.messages.add("⚠️ A SITH PREDATOR HAS FOUND YOU! RUN!", color='red')
                    
                return True
            except Exception as e:
                print(f"Error spawning predator: {e}")
                return False
                
        return False

    def decay_detection(self):
        # Detection decays over time
        if self.detection_level > 0:
            self.detection_level -= 1

# Usage: Attach PursuitSystem to player or game manager
