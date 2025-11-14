from enum import Enum
from typing import Tuple, List
import random

class WeaponType(Enum):
    BLASTER_PISTOL = "Blaster Pistol"
    BLASTER_RIFLE = "Blaster Rifle"
    HEAVY_BLASTER = "Heavy Blaster"
    WOOKIE_BOWCASTER = "Wookiee Bowcaster"
    CROSSBOW = "Crossbow"
    THERMAL_DETONATOR = "Thermal Detonator"
    VIBROBLADE = "Vibroblade"
    LIGHTSABER = "Lightsaber"
    DUAL_LIGHTSABER = "Dual Lightsaber"
    LIGHTSABER_PIKE = "Lightsaber Pike"
    MELEE = "Melee"
    RANGED = "Ranged"

class HandRequirement(Enum):
    ONE_HAND = "1H"       # Can be used with one hand (pistol, blade, shield)
    TWO_HAND = "2H"       # Requires both hands (rifle, pike, two-handed sword)
    DUAL_WIELD = "Dual"   # Paired weapons (dual lightsabers, dual blades)

class Weapon:
    def __init__(self, name: str, weapon_type: WeaponType, damage_range: Tuple[int, int] = (0, 0), accuracy: int = 0, weight: int = 0, value: int = 0, special: List[str] = None, base_damage: int = 0, accuracy_mod: int = 0, crit_mod: int = 0, rarity: str = "", description: str = "", hands: HandRequirement = HandRequirement.ONE_HAND, ammo: int = 0, range: int = 1):
        self.name = name
        self.weapon_type = weapon_type
        self.damage_range = damage_range
        self.accuracy = accuracy
        self.weight = weight
        self.value = value
        self.special = special if special is not None else []
        self.base_damage = base_damage
        self.accuracy_mod = accuracy_mod
        self.crit_mod = crit_mod
        self.rarity = rarity
        self.description = description
        self.hands = hands  # Hand requirement
        self.ammo = ammo  # Current ammo count
        self.max_ammo = ammo  # Starting/max ammo capacity (0 = melee/unlimited)
        self.range = range  # Attack range in tiles (1 = melee, 5+ = ranged)
        self.type = "weapon"  # For inventory system

    def get_damage(self) -> int:
        return random.randint(*self.damage_range)
    
    def get_hand_requirement(self) -> str:
        """Return hand requirement as display string."""
        return self.hands.value

# Rebalanced weapon list: More melee, fewer guns
# Note: base_damage is bonus to player Attack stat, accuracy_mod affects hit chance
WEAPONS = [
    # === MELEE WEAPONS (70% of arsenal) ===
    
    # Common Melee (6 weapons)
    Weapon("Training Saber", WeaponType.LIGHTSABER, (3, 6), 85, 1, 9, ["Practice Weapon", "Non-Lethal"],
           base_damage=2, accuracy_mod=10, crit_mod=2, rarity="Common",
           description="Low-power training lightsaber. Good for learning, weak in combat. +2 Attack",
           hands=HandRequirement.ONE_HAND),
    Weapon("Electrostaff", WeaponType.MELEE, (9, 14), 75, 3, 5, ["Shock", "Defensive"],
           base_damage=3, accuracy_mod=4, crit_mod=7, rarity="Common",
           description="Electrified staff effective against lightsabers. +3 Attack",
           hands=HandRequirement.TWO_HAND),
    Weapon("Vibrodagger", WeaponType.MELEE, (5, 9), 88, 1, 8, ["Quick", "Concealable"],
           base_damage=2, accuracy_mod=12, crit_mod=8, rarity="Common",
           description="Small vibrating blade. Fast and accurate. +2 Attack, +12 Accuracy",
           hands=HandRequirement.ONE_HAND),
    Weapon("Riot Baton", WeaponType.MELEE, (7, 11), 78, 2, 6, ["Stun", "Guard Weapon"],
           base_damage=3, accuracy_mod=5, crit_mod=4, rarity="Common",
           description="Standard issue crowd control weapon. +3 Attack",
           hands=HandRequirement.ONE_HAND),
    Weapon("Vibro-Knuckler", WeaponType.MELEE, (6, 10), 82, 1, 7, ["Brawler", "Quick Strikes"],
           base_damage=4, accuracy_mod=8, crit_mod=6, rarity="Common",
           description="Vibro-enhanced gauntlets. Fast melee attacks. +4 Attack",
           hands=HandRequirement.ONE_HAND),
    Weapon("Combat Knife", WeaponType.MELEE, (5, 8), 85, 1, 9, ["Precise", "Stealth"],
           base_damage=2, accuracy_mod=10, crit_mod=9, rarity="Common",
           description="Sharp and reliable. Good for surprise attacks. +2 Attack",
           hands=HandRequirement.ONE_HAND),
    
    # Uncommon Melee (7 weapons)
    Weapon("Vibroblade", WeaponType.VIBROBLADE, (8, 12), 85, 2, 0, ["Armor Penetration", "Quick Strikes"],
           base_damage=5, accuracy_mod=8, crit_mod=7, rarity="Uncommon",
           description="Vibrating blade cuts through armor. Fast and reliable. +5 Attack",
           hands=HandRequirement.ONE_HAND),
    Weapon("Force Pike", WeaponType.MELEE, (10, 16), 80, 3, 6, ["Stun", "Reach", "Guard Weapon"],
           base_damage=6, accuracy_mod=6, crit_mod=6, rarity="Uncommon",
           description="Electrified staff used by elite guards. Can stun. +6 Attack",
           hands=HandRequirement.TWO_HAND),
    Weapon("Vibro-Axe", WeaponType.MELEE, (13, 19), 70, 5, 6, ["Heavy Strike", "Cleave"],
           base_damage=8, accuracy_mod=2, crit_mod=10, rarity="Uncommon",
           description="Massive vibro-weapon. Devastating but slow. +8 Attack",
           hands=HandRequirement.TWO_HAND),
    Weapon("Electro-Sword", WeaponType.MELEE, (9, 15), 83, 3, 5, ["Shock", "Duelist"],
           base_damage=6, accuracy_mod=7, crit_mod=7, rarity="Uncommon",
           description="Charged blade favored by duelists. +6 Attack, +7 Accuracy",
           hands=HandRequirement.ONE_HAND),
    Weapon("Vibro-Lance", WeaponType.MELEE, (11, 17), 78, 4, 6, ["Reach", "Mounted"],
           base_damage=7, accuracy_mod=5, crit_mod=8, rarity="Uncommon",
           description="Long reach spear with vibro-tip. Great range. +7 Attack",
           hands=HandRequirement.TWO_HAND),
    Weapon("Sith Warblade", WeaponType.MELEE, (10, 16), 80, 3, 7, ["Dark Energy", "Fear"],
           base_damage=7, accuracy_mod=6, crit_mod=9, rarity="Uncommon",
           description="Curved blade radiating dark side energy. +7 Attack",
           hands=HandRequirement.ONE_HAND),
    Weapon("Techblade", WeaponType.MELEE, (8, 14), 85, 2, 7, ["Mono-Molecular", "Precise"],
           base_damage=5, accuracy_mod=9, crit_mod=8, rarity="Uncommon",
           description="Ultra-sharp molecular blade. Cuts anything. +5 Attack, +9 Accuracy",
           hands=HandRequirement.ONE_HAND),
    
    # Rare Melee (5 weapons)
    Weapon("Sith War Sword", WeaponType.MELEE, (12, 18), 85, 4, 8, ["Dark Side Infused", "Armor Pierce"],
           base_damage=9, accuracy_mod=7, crit_mod=9, rarity="Rare",
           description="Ancient blade infused with dark side energy. +9 Attack"),
    Weapon("Cortosis Blade", WeaponType.MELEE, (8, 13), 82, 2, 7, ["Lightsaber Resist", "Quick"],
           base_damage=6, accuracy_mod=9, crit_mod=5, rarity="Rare",
           description="Cortosis ore can short out lightsabers. +6 Attack, +9 Accuracy"),
    Weapon("Mandalorian Darksaber", WeaponType.MELEE, (14, 20), 88, 3, 5, ["Ancient", "Leadership"],
           base_damage=10, accuracy_mod=10, crit_mod=12, rarity="Rare",
           description="Legendary black-bladed lightsaber. Symbol of power. +10 Attack"),
    Weapon("Phrik Alloy Sword", WeaponType.MELEE, (11, 17), 86, 3, 7, ["Lightsaber-Proof", "Durable"],
           base_damage=8, accuracy_mod=8, crit_mod=7, rarity="Rare",
           description="Rare phrik metal resists lightsabers. +8 Attack"),
    Weapon("Sith Tremor Sword", WeaponType.MELEE, (13, 19), 80, 5, 6, ["Sonic Burst", "Heavy"],
           base_damage=9, accuracy_mod=4, crit_mod=11, rarity="Rare",
           description="Blade emits sonic shockwaves on impact. +9 Attack"),
    
    # Legendary Melee (3 weapons)
    Weapon("Single Lightsaber", WeaponType.LIGHTSABER, (15, 20), 90, 2, 0, ["Deflect Blasters", "Ignores Armor", "Force Focus"],
           base_damage=12, accuracy_mod=12, crit_mod=10, rarity="Legendary",
           description="Elegant weapon for a civilized age. +12 Attack, +12 Accuracy",
           hands=HandRequirement.ONE_HAND),
    Weapon("Dual Lightsaber", WeaponType.DUAL_LIGHTSABER, (18, 25), 85, 3, 0, ["Dual Wield", "High Risk", "Force Surge"],
           base_damage=15, accuracy_mod=10, crit_mod=15, rarity="Legendary",
           description="Double-bladed lightsaber. Aggressive offense. +15 Attack",
           hands=HandRequirement.DUAL_WIELD),
    Weapon("Lightsaber Pike", WeaponType.LIGHTSABER_PIKE, (16, 22), 80, 4, 1, ["Reach", "Defensive Stance"],
           base_damage=13, accuracy_mod=8, crit_mod=12, rarity="Legendary",
           description="Long-reach lightsaber. Balanced offense/defense. +13 Attack",
           hands=HandRequirement.TWO_HAND),
    
    # === RANGED WEAPONS (30% of arsenal) ===
    
    # Common Ranged (3 weapons)
    Weapon("DL-44 Blaster Pistol", WeaponType.BLASTER_PISTOL, (4, 8), 75, 2, 5, ["Quick Draw", "Reliable"],
           base_damage=3, accuracy_mod=5, crit_mod=3, rarity="Common",
           description="Han Solo's favorite. Reliable sidearm. +3 Attack",
           hands=HandRequirement.ONE_HAND, ammo=12, range=5),
    Weapon("Ion Blaster", WeaponType.RANGED, (5, 9), 80, 2, 6, ["Droid Killer", "EMP"],
           base_damage=4, accuracy_mod=6, crit_mod=3, rarity="Common",
           description="Specialized for disabling droids. +4 Attack",
           hands=HandRequirement.ONE_HAND, ammo=10, range=5),
    Weapon("Holdout Blaster", WeaponType.RANGED, (3, 6), 78, 1, 8, ["Concealable", "Backup"],
           base_damage=2, accuracy_mod=8, crit_mod=4, rarity="Common",
           description="Small backup blaster. Easy to conceal. +2 Attack",
           hands=HandRequirement.ONE_HAND, ammo=8, range=4),
    
    # Uncommon Ranged (3 weapons)
    Weapon("E-11 Blaster Rifle", WeaponType.BLASTER_RIFLE, (6, 10), 80, 3, 7, ["Stunning Shot", "Precision"],
           base_damage=5, accuracy_mod=7, crit_mod=4, rarity="Uncommon",
           description="Standard Imperial rifle. Good accuracy. +5 Attack, +7 Accuracy",
           hands=HandRequirement.TWO_HAND, ammo=30, range=7),
    Weapon("Bowcaster", WeaponType.WOOKIE_BOWCASTER, (12, 18), 65, 5, 4, ["Explosive Quarrels", "Knockback"],
           base_damage=8, accuracy_mod=2, crit_mod=8, rarity="Uncommon",
           description="Chewbacca's weapon. Explosive bolts. +8 Attack",
           hands=HandRequirement.TWO_HAND, ammo=6, range=6),
    Weapon("Sonic Blaster", WeaponType.RANGED, (7, 12), 75, 3, 7, ["Stun", "Area Effect"],
           base_damage=5, accuracy_mod=5, crit_mod=4, rarity="Uncommon",
           description="Projects sonic waves that stun. +5 Attack",
           hands=HandRequirement.ONE_HAND, ammo=15, range=5),
    
    # Rare Ranged (1 weapon)
    Weapon("Disruptor Pistol", WeaponType.RANGED, (11, 17), 65, 2, 4, ["Disintegrate", "Illegal"],
           base_damage=7, accuracy_mod=3, crit_mod=12, rarity="Rare",
           description="Banned disintegration weapon. +7 Attack",
           hands=HandRequirement.ONE_HAND, ammo=5, range=6),
]

# ensure WEAPONS exists, then normalize and provide safe defaults (non-destructive)
try:
    WEAPONS
except NameError:
    WEAPONS = []

# Normalize weapon objects so UI/combat always sees certain attributes
def _normalize_weapons():
    normalized = []
    for i, w in enumerate(WEAPONS):
        try:
            # if plain dict provided, convert to simple object
            if isinstance(w, dict):
                class _W:
                    pass
                obj = _W()
                for k, v in w.items():
                    setattr(obj, k, v)
                w = obj
            # ensure name
            if not hasattr(w, "name"):
                try:
                    setattr(w, "name", getattr(w, "title", f"weapon_{i}"))
                except Exception:
                    setattr(w, "name", f"weapon_{i}")
            # ensure base_damage (fallback to damage or 1)
            if not hasattr(w, "base_damage"):
                bd = getattr(w, "damage", None)
                try:
                    setattr(w, "base_damage", int(bd) if bd is not None else 1)
                except Exception:
                    setattr(w, "base_damage", 1)
            # ensure accuracy_mod and other expected attrs
            if not hasattr(w, "accuracy_mod"):
                setattr(w, "accuracy_mod", getattr(w, "acc", 0))
            if not hasattr(w, "crit_mod"):
                setattr(w, "crit_mod", getattr(w, "crit", 0))
            normalized.append(w)
        except Exception:
            # skip broken entries
            continue
    # If normalized ended up empty, create safe defaults
    if not normalized:
        class _W:
            def __init__(self, name, base_damage, accuracy_mod=0, crit_mod=0):
                self.name = name
                self.base_damage = base_damage
                self.accuracy_mod = accuracy_mod
                self.crit_mod = crit_mod
            def __str__(self):
                return self.name
        defaults = [
            _W("Training Baton", 1, 0, 0),
            _W("Training Saber", 4, 5, 2),
            _W("Vibroblade", 7, 4, 5),
            _W("Shock Baton", 5, 2, 1),
            _W("Blaster Pistol", 6, 5, 4),
            _W("Blaster Rifle", 9, 3, 5),
            _W("Light Saber", 8, 10, 6),
            _W("Wrist Launcher", 5, 0, 2),
            _W("Sonic Knife", 3, 6, 3),
            _W("Ion Staff", 10, -1, 8),
        ]
        normalized = defaults
    # replace global WEAPONS with normalized list (non-destructive to original objects)
    globals()["WEAPONS"] = normalized

_normalize_weapons()

class WeaponProficiency(Enum):
    NOVICE = 1
    TRAINED = 2
    EXPERT = 3
    MASTER = 4