"""
Canonical Lightsaber Combat Forms (Fighting Stances)
Based on Star Wars lore - 7 traditional forms plus specialized variants.
"""

class LightsaberForm:
    """Base class for lightsaber combat forms."""
    def __init__(self):
        self.name = "Unknown Form"
        self.number = 0  # Form I through VII
        self.philosophy = ""
        self.focus = ""  # e.g., "Offense", "Defense", "Balance"
        self.alignment_preference = "neutral"  # light, dark, or neutral
        
        # Stat bonuses when this form is active
        self.attack_bonus = 0
        self.defense_bonus = 0
        self.evasion_bonus = 0
        self.crit_chance_bonus = 0
        self.force_cost_reduction = 0  # Reduces Force ability costs
        
        # Special abilities or effects
        self.special_effects = []
        
        # Requirements to learn
        self.min_level = 1
        self.required_forms = []  # Must know these forms first
        
    def get_description(self):
        """Get full description for display."""
        lines = [
            f"═══ FORM {self.number}: {self.name.upper()} ═══",
            f"Focus: {self.focus}",
            f"Philosophy: {self.philosophy}",
            "",
            "Bonuses:",
        ]
        
        if self.attack_bonus:
            lines.append(f"  +{self.attack_bonus} Attack")
        if self.defense_bonus:
            lines.append(f"  +{self.defense_bonus} Defense")
        if self.evasion_bonus:
            lines.append(f"  +{self.evasion_bonus} Evasion")
        if self.crit_chance_bonus:
            lines.append(f"  +{self.crit_chance_bonus}% Critical Chance")
        if self.force_cost_reduction:
            lines.append(f"  -{self.force_cost_reduction}% Force Power Cost")
        
        if self.special_effects:
            lines.append("")
            lines.append("Special Effects:")
            for effect in self.special_effects:
                lines.append(f"  • {effect}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# THE SEVEN TRADITIONAL FORMS
# ═══════════════════════════════════════════════════════════════════════

class FormI_Shii_Cho(LightsaberForm):
    """Form I: Shii-Cho - The Way of the Sarlacc"""
    def __init__(self):
        super().__init__()
        self.name = "Shii-Cho"
        self.number = 1
        self.philosophy = "The simplest and oldest form. Wide, sweeping strikes. The foundation all Jedi learn."
        self.focus = "Fundamentals"
        self.alignment_preference = "neutral"
        
        # Basic, balanced bonuses
        self.attack_bonus = 1
        self.defense_bonus = 1
        
        self.special_effects = [
            "Guaranteed to disarm enemies on critical hits",
            "Wide attacks can hit multiple adjacent enemies"
        ]
        
        self.min_level = 1  # Starting form


class FormII_Makashi(LightsaberForm):
    """Form II: Makashi - The Way of the Ysalamiri"""
    def __init__(self):
        super().__init__()
        self.name = "Makashi"
        self.number = 2
        self.philosophy = "Elegant dueling form. Precise thrusts and parries. Count Dooku's signature style."
        self.focus = "Dueling"
        self.alignment_preference = "neutral"
        
        # High attack, moderate defense, bonus crit
        self.attack_bonus = 3
        self.defense_bonus = 1
        self.crit_chance_bonus = 10
        
        self.special_effects = [
            "Bonus damage against single opponents",
            "Increased critical damage",
            "Less effective against multiple enemies or blasters"
        ]
        
        self.min_level = 3
        self.required_forms = ["Shii-Cho"]


class FormIII_Soresu(LightsaberForm):
    """Form III: Soresu - The Way of the Mynock"""
    def __init__(self):
        super().__init__()
        self.name = "Soresu"
        self.number = 3
        self.philosophy = "Ultimate defensive form. Tight economy of motion. Obi-Wan Kenobi's mastery."
        self.focus = "Defense"
        self.alignment_preference = "light"
        
        # Maximum defense and evasion
        self.attack_bonus = -1  # Sacrifice offense
        self.defense_bonus = 4
        self.evasion_bonus = 3
        
        self.special_effects = [
            "Excellent against blaster fire",
            "Can deflect projectiles back at attackers",
            "Minimizes exposed targets",
            "Outlasts opponents through perfect defense"
        ]
        
        self.min_level = 4
        self.required_forms = ["Shii-Cho"]


class FormIV_Ataru(LightsaberForm):
    """Form IV: Ataru - The Way of the Hawk-Bat"""
    def __init__(self):
        super().__init__()
        self.name = "Ataru"
        self.number = 4
        self.philosophy = "Acrobatic aggression. Force-enhanced jumps and strikes. Favored by smaller, agile Jedi Masters."
        self.focus = "Aggressive Acrobatics"
        self.alignment_preference = "light"
        
        # High attack and evasion, lower defense
        self.attack_bonus = 3
        self.defense_bonus = 0
        self.evasion_bonus = 4
        self.force_cost_reduction = 10
        
        self.special_effects = [
            "Can leap to distant enemies",
            "Multiple rapid strikes",
            "Draining in prolonged combat",
            "Ineffective in confined spaces"
        ]
        
        self.min_level = 5
        self.required_forms = ["Shii-Cho"]


class FormV_Shien_Djem_So(LightsaberForm):
    """Form V: Shien/Djem So - The Way of the Krayt Dragon"""
    def __init__(self):
        super().__init__()
        self.name = "Shien / Djem So"
        self.number = 5
        self.philosophy = "Power and dominance. Deflect then counter-attack. Favored by aggressive duelists."
        self.focus = "Power Attack"
        self.alignment_preference = "neutral"  # Can trend dark
        
        # Maximum attack, decent defense
        self.attack_bonus = 4
        self.defense_bonus = 2
        self.crit_chance_bonus = 5
        
        self.special_effects = [
            "Counter-attacks after successful blocks",
            "Overpowers opponents through strength",
            "Excels against single strong enemies",
            "Can tend toward aggression and dark side"
        ]
        
        self.min_level = 6
        self.required_forms = ["Shii-Cho"]


class FormVI_Niman(LightsaberForm):
    """Form VI: Niman - The Way of the Rancor"""
    def __init__(self):
        super().__init__()
        self.name = "Niman"
        self.number = 6
        self.philosophy = "The diplomat's form. Balanced integration of Force powers with combat."
        self.focus = "Force Integration"
        self.alignment_preference = "neutral"
        
        # Moderate all-around, emphasizes Force use
        self.attack_bonus = 2
        self.defense_bonus = 2
        self.evasion_bonus = 1
        self.force_cost_reduction = 20
        
        self.special_effects = [
            "Seamlessly mix Force powers with attacks",
            "Reduced Force ability cooldowns",
            "Jack-of-all-trades, master of none",
            "Preferred by Jedi Consulars"
        ]
        
        self.min_level = 7
        self.required_forms = ["Shii-Cho"]


class FormVII_Juyo_Vaapad(LightsaberForm):
    """Form VII: Juyo/Vaapad - The Way of the Vornskr"""
    def __init__(self):
        super().__init__()
        self.name = "Juyo / Vaapad"
        self.number = 7
        self.philosophy = "Ferocious unpredictability. Channels inner darkness. Mace Windu's Vaapad variant."
        self.focus = "Ferocity"
        self.alignment_preference = "dark"  # Vaapad channels darkness
        
        # Extreme offense, risky
        self.attack_bonus = 5
        self.defense_bonus = 0
        self.evasion_bonus = 2
        self.crit_chance_bonus = 15
        
        self.special_effects = [
            "Unpredictable attack patterns confuse enemies",
            "Feeds on opponent's dark side energy",
            "Risk of falling to dark side",
            "Banned by Jedi Council (except Mace Windu)",
            "Bonus damage proportional to corruption level"
        ]
        
        self.min_level = 10
        self.required_forms = ["Shii-Cho", "Shien / Djem So"]


# ═══════════════════════════════════════════════════════════════════════
# SPECIALIZED VARIANTS
# ═══════════════════════════════════════════════════════════════════════

class FormJarKai(LightsaberForm):
    """Jar'Kai - Dual-Blade Combat"""
    def __init__(self):
        super().__init__()
        self.name = "Jar'Kai"
        self.number = 0  # Not a numbered form
        self.philosophy = "Ancient dual-wielding technique. Two blades in perfect synchronization. Ahsoka's specialty."
        self.focus = "Dual-Wielding"
        self.alignment_preference = "neutral"
        
        # Bonuses only apply when dual-wielding
        self.attack_bonus = 2
        self.defense_bonus = 1
        self.evasion_bonus = 2
        
        self.special_effects = [
            "Only active when wielding two lightsabers",
            "Enables dual-wielding mastery",
            "Extra attack per turn when dual-wielding",
            "Slightly reduced individual strike power"
        ]
        
        self.min_level = 5
        self.required_forms = ["Shii-Cho", "Ataru"]


class FormDoubleBladed(LightsaberForm):
    """Saberstaff Form - Double-Bladed Combat"""
    def __init__(self):
        super().__init__()
        self.name = "Saberstaff Mastery"
        self.number = 0
        self.philosophy = "Exotic double-bladed technique. Spinning death. Ancient Sith assassin signature style."
        self.focus = "Double-Bladed"
        self.alignment_preference = "dark"
        
        # Bonuses only apply with double-bladed saber
        self.attack_bonus = 3
        self.defense_bonus = 2
        self.evasion_bonus = 1
        
        self.special_effects = [
            "Only active with double-bladed lightsaber",
            "Spinning attacks hit multiple enemies",
            "Intimidating presence",
            "Difficult to master"
        ]
        
        self.min_level = 6
        self.required_forms = ["Shii-Cho", "Ataru"]


# ═══════════════════════════════════════════════════════════════════════
# FORM REGISTRY
# ═══════════════════════════════════════════════════════════════════════

ALL_FORMS = [
    FormI_Shii_Cho(),
    FormII_Makashi(),
    FormIII_Soresu(),
    FormIV_Ataru(),
    FormV_Shien_Djem_So(),
    FormVI_Niman(),
    FormVII_Juyo_Vaapad(),
    FormJarKai(),
    FormDoubleBladed(),
]

# Create lookup dictionaries
FORMS_BY_NAME = {form.name: form for form in ALL_FORMS}
FORMS_BY_NUMBER = {form.number: form for form in ALL_FORMS if form.number > 0}


def get_available_forms(player):
    """
    Get list of forms the player can learn.
    
    Args:
        player: Player object with level and known_forms
    
    Returns:
        List of available LightsaberForm objects
    """
    known = getattr(player, 'known_forms', [])
    level = getattr(player, 'level', 1)
    
    available = []
    for form in ALL_FORMS:
        # Skip if already known
        if form.name in known:
            continue
        
        # Check level requirement
        if level < form.min_level:
            continue
        
        # Check form prerequisites
        if form.required_forms:
            has_prereqs = all(req in known for req in form.required_forms)
            if not has_prereqs:
                continue
        
        available.append(form)
    
    return available


def get_form_bonuses(player):
    """
    Calculate total bonuses from active stance.
    
    Args:
        player: Player object
    
    Returns:
        dict with bonus values
    """
    active_form_name = getattr(player, 'active_form', None)
    if not active_form_name or active_form_name not in FORMS_BY_NAME:
        return {
            'attack': 0,
            'defense': 0,
            'evasion': 0,
            'crit_chance': 0,
            'force_cost_reduction': 0
        }
    
    form = FORMS_BY_NAME[active_form_name]
    
    return {
        'attack': form.attack_bonus,
        'defense': form.defense_bonus,
        'evasion': form.evasion_bonus,
        'crit_chance': form.crit_chance_bonus,
        'force_cost_reduction': form.force_cost_reduction
    }
