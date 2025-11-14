class ForceAbility:
    def __init__(self, name: str, description: str, target_type: str, mana_cost: int, effect_func):
        self.name = name
        self.description = description
        self.target_type = target_type  # 'enemy' or 'self'
        self.mana_cost = mana_cost
        self.effect = effect_func

    def use(self, user, target, game_map, messages, player_rank=1):
        """Use the ability."""
        # For now, no mana system, just use the effect
        return self.effect(user, target, game_map, messages, player_rank)