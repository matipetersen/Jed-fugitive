"""
Detailed character sheet system showing complete player information.
"""

def show_character_sheet(game):
    """Display comprehensive character sheet with all player stats, abilities, and progress."""
    p = game.player
    lines = []
    
    # Header with player alignment
    try:
        alignment = p.get_alignment() if hasattr(p, 'get_alignment') else 'Unknown'
    except:
        alignment = 'Unknown'
    
    lines.append("╔════════════════════════════════════════════════════════════╗")
    lines.append("║          JEDI FUGITIVE - CHARACTER SHEET                   ║")
    lines.append("╚════════════════════════════════════════════════════════════╝")
    lines.append("")
    
    # Identity & Alignment
    lines.append(f"═══ IDENTITY ═══")
    lines.append(f"Alignment: {alignment.upper()}")
    corruption = getattr(p, 'dark_corruption', 0)
    lines.append(f"Corruption: {corruption}% {'[Pure Light]' if corruption <= 20 else '[Balanced]' if corruption <= 70 else '[Deep Dark]'}")
    lines.append(f"Overall Level: {getattr(p, 'level', 1)}")
    lines.append(f"  Light Side Level: {getattr(p, 'light_level', 1)} ({getattr(p, 'light_xp', 0)}/{getattr(p, 'xp_to_next_light', 100)} XP)")
    lines.append(f"  Dark Side Level: {getattr(p, 'dark_level', 1)} ({getattr(p, 'dark_xp', 0)}/{getattr(p, 'xp_to_next_dark', 100)} XP)")
    lines.append("")
    
    # Combat Stats
    lines.append(f"═══ COMBAT STATS ═══")
    lines.append(f"HP: {getattr(p, 'hp', 0)}/{getattr(p, 'max_hp', 0)}")
    
    # Attack with breakdown
    base_atk = getattr(p, '_base_stats', {}).get('attack', getattr(p, 'attack', 0))
    current_atk = getattr(p, 'attack', 0)
    atk_bonus = current_atk - base_atk
    if atk_bonus > 0:
        lines.append(f"Attack: {base_atk} +{atk_bonus} equipment = {current_atk}")
    else:
        lines.append(f"Attack: {current_atk}")
    
    # Defense with breakdown
    base_def = getattr(p, '_base_stats', {}).get('defense', getattr(p, 'defense', 0))
    current_def = getattr(p, 'defense', 0)
    def_bonus = current_def - base_def
    if def_bonus > 0:
        lines.append(f"Defense: {base_def} +{def_bonus} equipment = {current_def}")
    else:
        lines.append(f"Defense: {current_def}")
    
    lines.append(f"Accuracy: {getattr(p, 'accuracy', 0)}%")
    lines.append(f"Evasion: {getattr(p, 'evasion', 0)}%")
    lines.append(f"Crit Chance: {getattr(p, 'critical_chance', 5)}%")
    lines.append("")
    
    # Force Stats
    lines.append(f"═══ FORCE CONNECTION ═══")
    force_energy = getattr(p, 'force_energy', 0)
    max_force = getattr(p, 'max_force_energy', 100)
    lines.append(f"Force Energy: {force_energy}/{max_force}")
    lines.append(f"Force Points (Legacy): {getattr(p, 'force_points', 0)}")
    
    # Stress (if in tomb)
    try:
        if getattr(p, '_stress_system_active', False):
            stress = getattr(p, 'stress', 0)
            max_stress = getattr(p, 'max_stress', 100)
            desc, _ = p.get_stress_description() if hasattr(p, 'get_stress_description') else ("Unknown", 4)
            lines.append(f"Stress: {stress}/{max_stress} [{desc}]")
    except:
        pass
    lines.append("")
    
    # Force Abilities
    lines.append(f"═══ FORCE ABILITIES ═══")
    abilities = p.get_available_abilities() if hasattr(p, 'get_available_abilities') else []
    if abilities:
        for ability in abilities:
            name = getattr(ability, 'name', str(ability))
            cost = getattr(ability, 'base_cost', getattr(ability, 'cost', '?'))
            lines.append(f"  • {name} (Cost: {cost})")
    else:
        lines.append("  No abilities unlocked yet")
    lines.append("")
    
    # Combat Masteries
    lines.append(f"═══ COMBAT MASTERIES ═══")
    melee_m = getattr(p, 'melee_mastery', 0)
    ranged_m = getattr(p, 'ranged_mastery', 0)
    shield_m = getattr(p, 'shield_mastery', 0)
    dual_m = getattr(p, 'dual_wield_mastery', 0)
    force_m = getattr(p, 'force_mastery', 0)
    
    if any([melee_m, ranged_m, shield_m, dual_m, force_m]):
        if melee_m > 0:
            lines.append(f"  Melee Mastery: Rank {melee_m} (+{melee_m} damage)")
        if ranged_m > 0:
            lines.append(f"  Ranged Mastery: Rank {ranged_m} (+{ranged_m} damage)")
        if shield_m > 0:
            lines.append(f"  Shield Mastery: Rank {shield_m} (+{shield_m} defense)")
        if dual_m > 0:
            lines.append(f"  Dual Wield Mastery: Rank {dual_m} (+{dual_m} damage/hand)")
        if force_m > 0:
            lines.append(f"  Force Mastery: Rank {force_m} (-{force_m * 5}% cost)")
    else:
        lines.append("  No masteries developed yet")
    lines.append("")
    
    # Lightsaber Forms
    lines.append(f"═══ LIGHTSABER FORMS ═══")
    known_forms = getattr(p, 'known_forms', ["Shii-Cho"])
    active_form = getattr(p, 'active_form', "Shii-Cho")
    for form in known_forms:
        marker = "[ACTIVE]" if form == active_form else ""
        lines.append(f"  • {form} {marker}")
    lines.append("")
    
    # Crafting
    lines.append(f"═══ CRAFTING ═══")
    craft_lvl = getattr(p, 'craft_level', 1)
    craft_xp = getattr(p, 'craft_xp', 0)
    craft_next = getattr(p, 'craft_xp_to_next', 100)
    lines.append(f"Crafting Level: {craft_lvl} ({craft_xp}/{craft_next} XP)")
    lines.append(f"Unlocked Recipes: {craft_lvl * 2}")
    lines.append("")
    
    # Equipment
    lines.append(f"═══ EQUIPPED GEAR ═══")
    weapon = getattr(p, 'equipped_weapon', None)
    offhand = getattr(p, 'equipped_offhand', None)
    armor = getattr(p, 'equipped_armor', None)
    
    def _get_name(item):
        if item is None:
            return "None"
        if isinstance(item, dict):
            return item.get('name', 'Unknown')
        return getattr(item, 'name', str(item))
    
    lines.append(f"  Main Hand: {_get_name(weapon)}")
    lines.append(f"  Off Hand: {_get_name(offhand)}")
    lines.append(f"  Armor: {_get_name(armor)}")
    lines.append("")
    
    # Journey Progress
    lines.append(f"═══ JOURNEY PROGRESS ═══")
    lines.append(f"Enemies Defeated: {getattr(p, 'kills_count', 0)}")
    lines.append(f"Tombs Explored: {getattr(p, 'tombs_explored', 0)}")
    lines.append(f"Lore Discovered: {getattr(p, 'lore_discovered', 0)}")
    lines.append(f"Gold Collected: {getattr(p, 'gold_collected', 0)}")
    lines.append(f"Artifacts Consumed: {getattr(p, 'artifacts_consumed', 0)}")
    lines.append("")
    
    # Inventory Count (with armor capacity bonus)
    inv_count = len(getattr(p, 'inventory', []))
    inv_max = p.get_max_inventory() if hasattr(p, 'get_max_inventory') else 30
    
    # Show bonus if any
    armor = getattr(p, 'equipped_armor', None)
    if armor:
        bonus = int(getattr(armor, 'capacity_bonus', 0))
        if bonus != 0:
            lines.append(f"Inventory: {inv_count}/{inv_max} slots ({'+' if bonus > 0 else ''}{bonus} from armor)")
        else:
            lines.append(f"Inventory: {inv_count}/{inv_max} slots used")
    else:
        lines.append(f"Inventory: {inv_count}/{inv_max} slots used")
    lines.append("")
    lines.append("Press any key to close...")
    
    # Display using UI system
    try:
        if hasattr(game.ui, 'centered_dialog'):
            game.ui.centered_dialog(lines, title="Character Sheet")
        else:
            for line in lines:
                game.ui.messages.add(line)
    except:
        for line in lines:
            try:
                game.ui.messages.add(line)
            except:
                pass
