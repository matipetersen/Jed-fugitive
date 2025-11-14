from jedi_fugitive.game.force_abilities import ForceAbility, ForcePushPull, FORCE_ABILITIES

# Keep the old convenience names/helpers expected by other codebases.
ForceAbilities = FORCE_ABILITIES

def force_push_effect(*args, **kwargs):
    """Backward-compatible wrapper for push effect."""
    return ForcePushPull().use(*args, **kwargs)

__all__ = [
    "ForceAbility",
    "ForcePushPull",
    "FORCE_ABILITIES",
    "ForceAbilities",
    "force_push_effect",
]