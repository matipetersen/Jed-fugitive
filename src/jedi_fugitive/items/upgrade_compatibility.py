"""
Weapon upgrade compatibility system.

This module defines which weapon upgrades are compatible with which weapon types,
preventing illogical combinations like sharpening energy weapons or adding ion
capacitors to melee weapons.
"""

from jedi_fugitive.items.weapons import WeaponType

# Define which weapon types each upgrade can be applied to
UPGRADE_COMPATIBILITY = {
    # Blade/Melee upgrades - only work on physical weapons
    "Sharpened Edge": [
        WeaponType.MELEE, 
        WeaponType.VIBROBLADE, 
        WeaponType.LIGHTSABER,
        WeaponType.DUAL_LIGHTSABER,
        WeaponType.LIGHTSABER_PIKE,
        WeaponType.COMBAT_KNIFE,
        WeaponType.CROSSBOW  # Add crossbow for blade/edge upgrades
    ],
    
    # Balance upgrades - work on most handheld weapons  
    "Balanced Grip": [
        WeaponType.MELEE,
        WeaponType.VIBROBLADE,
        WeaponType.LIGHTSABER,
        WeaponType.DUAL_LIGHTSABER,
        WeaponType.LIGHTSABER_PIKE,
        WeaponType.BLASTER_PISTOL,
        WeaponType.BLASTER_RIFLE,
        WeaponType.HEAVY_BLASTER,
        WeaponType.RANGED,
        WeaponType.COMBAT_KNIFE,
        WeaponType.WOOKIE_BOWCASTER,
        WeaponType.CROSSBOW,
        WeaponType.THERMAL_DETONATOR,
        WeaponType.ELECTROSTAFF
    ],
    
    # Structural reinforcement - works on all weapons
    "Reinforced Frame": "ALL",
    
    # Electronic/Energy upgrades - only energy weapons
    "Ion Capacitor": [
        WeaponType.BLASTER_PISTOL,
        WeaponType.BLASTER_RIFLE,
        WeaponType.HEAVY_BLASTER,
        WeaponType.RANGED,
        WeaponType.WOOKIE_BOWCASTER,
        WeaponType.THERMAL_DETONATOR,
        WeaponType.ELECTROSTAFF  # Electrostaffs are electronic weapons
    ],
    
    # Cortosis weave - works on weapons and armor
    "Cortosis Weave": "ALL",  # Can be woven into any weapon/armor
    
    # Power upgrades - only energy weapons
    "Power Cell Overcharge": [
        WeaponType.BLASTER_PISTOL,
        WeaponType.BLASTER_RIFLE,
        WeaponType.HEAVY_BLASTER,
        WeaponType.RANGED,
        WeaponType.LIGHTSABER,
        WeaponType.DUAL_LIGHTSABER,
        WeaponType.LIGHTSABER_PIKE,
        WeaponType.WOOKIE_BOWCASTER,
        WeaponType.THERMAL_DETONATOR,
        WeaponType.ELECTROSTAFF
    ],
    
    # Crystal focusing - only energy/Force weapons
    "Crystal Focus": [
        WeaponType.LIGHTSABER,
        WeaponType.DUAL_LIGHTSABER,
        WeaponType.LIGHTSABER_PIKE,
        WeaponType.BLASTER_PISTOL,
        WeaponType.BLASTER_RIFLE,
        WeaponType.HEAVY_BLASTER,
        WeaponType.RANGED,
        WeaponType.WOOKIE_BOWCASTER
    ],
    
    # Beskar - works on all weapons (legendary material)
    "Beskar Reinforcement": "ALL",
    
    # Kyber - only Force weapons
    "Kyber Attunement": [
        WeaponType.LIGHTSABER,
        WeaponType.DUAL_LIGHTSABER,
        WeaponType.LIGHTSABER_PIKE
    ],
    
    # Targeting computer - only ranged weapons
    "Targeting Computer": [
        WeaponType.BLASTER_PISTOL,
        WeaponType.BLASTER_RIFLE,
        WeaponType.HEAVY_BLASTER,
        WeaponType.RANGED,
        WeaponType.WOOKIE_BOWCASTER,
        WeaponType.CROSSBOW,
        WeaponType.THERMAL_DETONATOR
    ],
    
    # Vibro upgrades - only physical weapons that can vibrate
    "Vibro-Edge": [
        WeaponType.MELEE,
        WeaponType.VIBROBLADE,
        WeaponType.COMBAT_KNIFE,
        WeaponType.CROSSBOW  # Crossbow bolts can have vibro tips
    ],
}

def is_upgrade_compatible(recipe_name, weapon):
    """
    Check if a crafting recipe is compatible with a weapon.
    
    Args:
        recipe_name: Name of the crafting recipe
        weapon: Weapon object to check compatibility with
    
    Returns:
        tuple: (is_compatible: bool, reason: str)
    """
    if recipe_name not in UPGRADE_COMPATIBILITY:
        return True, "No restrictions defined for this upgrade"
    
    compatible_types = UPGRADE_COMPATIBILITY[recipe_name]
    
    # "ALL" means upgrade works on any weapon
    if compatible_types == "ALL":
        return True, "Universal upgrade"
    
    # Get weapon type
    weapon_type = getattr(weapon, 'weapon_type', None)
    if weapon_type is None:
        return False, "Weapon has no defined type"
    
    # Check if weapon type is in compatible list
    if weapon_type in compatible_types:
        return True, f"Compatible with {weapon_type.value}"
    
    # Generate helpful error message
    compatible_names = [wt.value for wt in compatible_types]
    return False, f"{recipe_name} only works on: {', '.join(compatible_names)}"

def get_compatible_upgrades(weapon):
    """
    Get list of upgrades that are compatible with a weapon.
    
    Args:
        weapon: Weapon object
    
    Returns:
        list: Recipe names that are compatible with this weapon
    """
    compatible_upgrades = []
    weapon_type = getattr(weapon, 'weapon_type', None)
    
    for recipe_name, compatible_types in UPGRADE_COMPATIBILITY.items():
        if compatible_types == "ALL" or (weapon_type and weapon_type in compatible_types):
            compatible_upgrades.append(recipe_name)
    
    return compatible_upgrades

def get_upgrade_description(recipe_name, weapon):
    """
    Get a description of why an upgrade is or isn't compatible.
    
    Args:
        recipe_name: Name of the crafting recipe
        weapon: Weapon object
    
    Returns:
        str: Human-readable description
    """
    is_compatible, reason = is_upgrade_compatible(recipe_name, weapon)
    
    if is_compatible:
        return f"✓ {recipe_name} - {reason}"
    else:
        return f"✗ {recipe_name} - {reason}"

# Special upgrade effects that apply only to specific weapon types
UPGRADE_SPECIAL_EFFECTS = {
    "Ion Capacitor": {
        "description": "Adds electrical damage effective against droids",
        "compatible_types": [WeaponType.BLASTER_PISTOL, WeaponType.BLASTER_RIFLE, WeaponType.RANGED]
    },
    
    "Kyber Attunement": {
        "description": "Channels Force energy through the weapon",
        "compatible_types": [WeaponType.LIGHTSABER, WeaponType.DUAL_LIGHTSABER, WeaponType.LIGHTSABER_PIKE],
        "force_required": True
    },
    
    "Vibro-Edge": {
        "description": "Creates ultrasonic vibrations that cut through armor",
        "compatible_types": [WeaponType.MELEE, WeaponType.VIBROBLADE, WeaponType.COMBAT_KNIFE]
    },
    
    "Crystal Focus": {
        "description": "Improves energy focusing and beam coherence",
        "compatible_types": [WeaponType.LIGHTSABER, WeaponType.BLASTER_PISTOL, WeaponType.BLASTER_RIFLE]
    }
}