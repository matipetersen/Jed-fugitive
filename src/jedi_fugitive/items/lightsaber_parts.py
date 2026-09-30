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

class BladeType:
    """Blade configuration types inspired by Jedi Survivor"""
    SINGLE = "single"           # Standard single blade
    DOUBLE = "double"           # Double-bladed (Sith assassin style)
    CROSSGUARD = "crossguard"   # Crossguard (Kylo Ren style)
    DUAL_WIELD = "dual_wield"   # Two separate sabers
    
class Lightsaber:
    def __init__(self, crystal, hilt, emitter, blade_type="single", player_corruption=50):
        self.crystal = crystal
        self.hilt = hilt
        self.emitter = emitter
        self.blade_type = blade_type
        self.player_corruption = player_corruption
        self.stats = self.combine_stats()
        self.style = self.determine_style()
        self.blade_color = self.get_blade_color()
        self.blade_display = self.get_blade_display()

    def combine_stats(self):
        stats = {}
        for part in [self.crystal, self.hilt, self.emitter]:
            for k, v in part.stat_bonus.items():
                stats[k] = stats.get(k, 0) + v
        
        # Blade type modifiers
        if self.blade_type == BladeType.DOUBLE:
            stats['attack'] = stats.get('attack', 0) + 5
            stats['defense'] = stats.get('defense', 0) - 2
        elif self.blade_type == BladeType.CROSSGUARD:
            stats['attack'] = stats.get('attack', 0) + 3
            stats['defense'] = stats.get('defense', 0) + 3
        elif self.blade_type == BladeType.DUAL_WIELD:
            stats['attack'] = stats.get('attack', 0) + 4
            stats['evasion'] = stats.get('evasion', 0) + 2
        
        return stats

    def determine_style(self):
        """Determine fighting style based on blade type and hilt"""
        if self.blade_type == BladeType.DOUBLE:
            return 'double-bladed saberstaff'
        elif self.blade_type == BladeType.CROSSGUARD:
            return 'crossguard broadsaber'
        elif self.blade_type == BladeType.DUAL_WIELD:
            return 'dual-wielding'
        elif self.hilt.name.lower().startswith('shoto'):
            return 'shoto defensive'
        return 'standard single-blade'
    
    def get_blade_color(self):
        """Dynamic blade color based on player corruption and alignment"""
        corruption = self.player_corruption
        
        # Pure Dark Side (80-100 corruption) - Red variations
        if corruption >= 80:
            return "Crimson Red" if corruption >= 90 else "Blood Red"
        
        # Dark Leaning (60-79) - Orange to Red
        elif corruption >= 60:
            return "Dark Orange" if corruption >= 70 else "Amber Orange"
        
        # Gray/Balanced (40-59) - Yellow to Purple
        elif corruption >= 50:
            return "Gold Yellow"  # Balanced gray Jedi
        elif corruption >= 40:
            return "Violet Purple"  # Force sensitive, questioning
        
        # Light Leaning (20-39) - Green variations
        elif corruption >= 20:
            return "Emerald Green" if corruption >= 30 else "Verdant Green"
        
        # Pure Light Side (0-19) - Blue variations  
        else:
            return "Azure Blue" if corruption >= 10 else "Crystal Blue"
    
    def get_blade_display(self):
        """ASCII representation of blade based on type"""
        if self.blade_type == BladeType.DOUBLE:
            return "═══╪═══"  # Double blade
        elif self.blade_type == BladeType.CROSSGUARD:
            return "═╪═"      # Crossguard
        elif self.blade_type == BladeType.DUAL_WIELD:
            return "═══ ═══" # Two blades
        else:
            return "═══"      # Single blade
    
    def update_corruption(self, new_corruption):
        """Update blade color when corruption changes"""
        self.player_corruption = new_corruption
        self.blade_color = self.get_blade_color()

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
