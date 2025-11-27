"""
Dynamic Lightsaber Building System
Allows player to collect and combine saber parts for custom sabers.
"""

class SaberPart:
    def __init__(self, part_type, name, stat_bonus, description):
        self.part_type = part_type  # 'crystal', 'hilt', 'emitter'
        self.name = name
        self.stat_bonus = stat_bonus  # Dict of stat changes
        self.description = description

class Lightsaber:
    def __init__(self, crystal, hilt, emitter):
        self.crystal = crystal
        self.hilt = hilt
        self.emitter = emitter
        self.stats = self.combine_stats()
        self.style = self.determine_style()

    def combine_stats(self):
        stats = {}
        for part in [self.crystal, self.hilt, self.emitter]:
            for k, v in part.stat_bonus.items():
                stats[k] = stats.get(k, 0) + v
        return stats

    def determine_style(self):
        # Example: double-bladed, shoto, standard
        if self.hilt.name.lower().startswith('double'):
            return 'double-bladed'
        elif self.hilt.name.lower().startswith('shoto'):
            return 'shoto'
        return 'standard'

# Example saber parts
SABER_PARTS = {
    'crystal_kyber': SaberPart('crystal', 'Kyber Crystal', {'attack': 5}, 'Standard Jedi crystal.'),
    'crystal_sith': SaberPart('crystal', 'Sith Crystal', {'attack': 7, 'corruption': 10}, 'Dark side attuned.'),
    'hilt_standard': SaberPart('hilt', 'Standard Hilt', {'defense': 2}, 'Balanced hilt.'),
    'hilt_double': SaberPart('hilt', 'Double Hilt', {'attack': 3}, 'Allows double-bladed style.'),
    'hilt_shoto': SaberPart('hilt', 'Shoto Hilt', {'evasion': 3}, 'Short hilt for defense.'),
    'emitter_basic': SaberPart('emitter', 'Basic Emitter', {'accuracy': 2}, 'Standard emitter.'),
    'emitter_stable': SaberPart('emitter', 'Stable Emitter', {'attack': 1, 'defense': 1}, 'Stabilizes blade.'),
}

# Usage: Collect parts, then create Lightsaber(crystal, hilt, emitter)
