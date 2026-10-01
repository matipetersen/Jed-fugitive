
from jedi_fugitive.game.enemy import Enemy
from typing import Tuple, List
# fixed import: Display lives in game.level, not jedi_fugitive.display
from jedi_fugitive.game.level import Display
from jedi_fugitive.items.weapons import WeaponType, Weapon
import random
from jedi_fugitive.utils.logger import get_logger

logger = get_logger("combat")

def calculate_hit(accuracy: int, evasion: int) -> bool:
    """Calculate if an attack hits based on accuracy and evasion."""
    hit_chance = max(5, min(95, accuracy - evasion + 50))
    return random.randint(1, 100) <= hit_chance

MELEE_TYPES = tuple(t for t in (getattr(WeaponType, n, None) for n in (
    'VIBROBLADE', 'COMBAT_KNIFE', 'ELECTROSTAFF', 'MELEE')) if t is not None)
RANGED_TYPES = tuple(t for t in (getattr(WeaponType, n, None) for n in (
    'BLASTER_PISTOL', 'BLASTER_RIFLE', 'HEAVY_BLASTER', 'RANGED', 'WOOKIE_BOWCASTER', 'CROSSBOW')) if t is not None)
ARMOR_IGNORING = ('Ignores Armor',)
ARMOR_PIERCING = ('Armor Penetration', 'Armor Pierce', 'Mono-Molecular', 'Disintegrate')


def weapon_roll(weapon, rng=random):
    """Damage roll of a weapon. Unarmed: 1-4.

    Weapons built without a damage_range (e.g. the starting vibroblade used to be
    created with only base_damage, so it rolled (0, 0) = 0 damage) derive one
    from base_damage instead.
    """
    if not weapon:
        return rng.randint(1, 4)
    if isinstance(weapon, dict):
        rng_pair = weapon.get('damage_range')
        base = int(weapon.get('base_damage', weapon.get('attack', 3)) or 3)
    else:
        rng_pair = getattr(weapon, 'damage_range', None)
        base = int(getattr(weapon, 'base_damage', 3) or 3)
    try:
        lo, hi = int(rng_pair[0]), int(rng_pair[1])
    except Exception:
        lo = hi = 0
    if hi <= 0:
        lo, hi = max(1, base - 2), max(2, base + 2)
    upgrade = int(getattr(weapon, 'upgrade_damage', 0) or 0) if not isinstance(weapon, dict) else 0
    return rng.randint(min(lo, hi), max(lo, hi)) + upgrade


def attack_bonus(player):
    """+1 damage per 2 points of the character's own Attack above 10.

    Uses the base stats (without equipment) so weapon stats are not counted
    twice; levels, level-up choices and skills feed into it.
    """
    base = getattr(player, '_base_stats', None) or {}
    atk = base.get('attack', getattr(player, 'attack', 10))
    try:
        return (int(atk) - 10) // 2
    except Exception:
        return 0


def generic_crit_chance(player, weapon):
    crit_mod = int(getattr(weapon, 'crit_mod', 0) or 0) if weapon is not None and not isinstance(weapon, dict) else 0
    bonus = float(getattr(player, 'crit_chance_bonus', 0) or 0)
    return min(0.5, 0.05 + crit_mod / 100.0 + bonus / 100.0)


def _specials(weapon):
    if weapon is None:
        return ()
    sp = weapon.get('special', ()) if isinstance(weapon, dict) else getattr(weapon, 'special', ())
    return tuple(sp or ())


def apply_armor(dmg, enemy, weapon):
    """Enemy defense absorbs half its value; piercing weapons a quarter; 'Ignores Armor' none."""
    defense = int(getattr(enemy, 'defense', 0) or 0)
    sp = _specials(weapon)
    if any(s in sp for s in ARMOR_IGNORING):
        absorbed = 0
    elif any(s in sp for s in ARMOR_PIERCING):
        absorbed = defense // 4
    else:
        absorbed = defense // 2
    return max(1, int(dmg) - absorbed)


def player_attack(player, enemy, messages=None, game=None):
    """Player attacks enemy. Accepts optional messages buffer and game for compatibility."""
    try:
        # Update pursuit system if available
        if game and hasattr(game, 'pursuit_system'):
            game.pursuit_system.update_detection('combat')

        # prefer player's effective accuracy which accounts for stress/equipment
        try:
            acc = int(player.get_effective_accuracy())
        except Exception as e:
            logger.exception(f"Exception getting player effective accuracy: {e}")
            acc = getattr(player, "accuracy", 0)
        ev = getattr(enemy, "evasion", 0)
        if calculate_hit(acc, ev):
            weapon = getattr(player, "equipped_weapon", None)
            offhand = getattr(player, "offhand", None)
            # damage = weapon roll + character attack bonus (+ masteries), crit, then enemy armour
            dmg = weapon_roll(weapon) + attack_bonus(player)

            if weapon:
                try:
                    weapon_type = getattr(weapon, 'weapon_type', None)
                    # Apply melee/ranged mastery
                    if weapon_type in MELEE_TYPES:
                        dmg += getattr(player, 'melee_mastery', 0)
                    elif weapon_type in RANGED_TYPES:
                        dmg += getattr(player, 'ranged_mastery', 0)
                    # Apply dual wield mastery if both hands have weapons
                    if offhand and hasattr(offhand, 'weapon_type'):
                        dmg += getattr(player, 'dual_wield_mastery', 0)
                except Exception as e:
                    logger.exception(f"Exception applying mastery bonuses: {e}")

            crit = False
            # Lightsaber form mechanics (stance bonuses, crits, cleave, ...)
            form_notes = []
            try:
                from jedi_fugitive.game import form_combat
                if form_combat.has_lightsaber(player) and form_combat._form(player) is not None:
                    dmg, form_notes = form_combat.modify_player_attack(player, enemy, int(dmg), game)
                    crit = any('CRITICAL' in n for n in form_notes)
                elif random.random() < generic_crit_chance(player, weapon):
                    # weapons without a lightsaber form crit through their own crit_mod
                    dmg = int(dmg * 1.5)
                    crit = True
            except Exception as e:
                logger.exception(f"Exception applying form mechanics: {e}")
            dmg = apply_armor(int(dmg), enemy, weapon)
            try:
                enemy.hp = getattr(enemy, "hp", 0) - int(dmg)
            except Exception as e:
                logger.exception(f"Exception setting enemy.hp: {e}")
                try:
                    setattr(enemy, "hp", getattr(enemy, "hp", 0) - int(dmg))
                except Exception as e2:
                    logger.exception(f"Exception using setattr for enemy.hp: {e2}")
            
            try:
                from jedi_fugitive.game import form_combat
                form_combat.cleave(player, enemy, int(dmg), game, messages)
            except Exception as e:
                logger.exception(f"Exception applying cleave: {e}")

            # Generate descriptive combat message
            if messages is not None:
                try:
                    enemy_name = getattr(enemy, 'name', 'the enemy')
                    enemy_hp = getattr(enemy, 'hp', 0)
                    # Select body part and action based on damage and enemy HP
                    body_parts = ['head', 'torso', 'arm', 'leg', 'chest', 'shoulder']
                    if enemy_hp <= 0:
                        # Death blow descriptions with ASCII art
                        death_messages = [
                            f"☠ FATAL BLOW ☠ You strike {enemy_name}'s {random.choice(body_parts)} - {dmg} damage!",
                            f"✖ SLAIN ✖ Your attack cleaves through {enemy_name}'s {random.choice(body_parts)} - {dmg} damage!",
                            f"† DEFEATED † You cut open {enemy_name}'s {random.choice(body_parts)} and they collapse! [{dmg} dmg]",
                            f"⚔ VICTORY ⚔ {enemy_name} falls as your blade pierces their {random.choice(body_parts)}! [{dmg} dmg]",
                            f"★ KILLING BLOW ★ Devastating strike to {enemy_name}'s {random.choice(body_parts)}! [{dmg} dmg]"
                        ]
                        messages.add(random.choice(death_messages))
                    elif crit:
                        # real critical hits (form crit or weapon crit_mod)
                        crit_messages = [
                            f"#2#CRITICAL!#0# You brutally slash {enemy_name}'s {random.choice(body_parts)}! [{dmg} damage]",
                            f"★ POWER STRIKE! ★ Your weapon tears through {enemy_name}'s {random.choice(body_parts)}! [{dmg} dmg]",
                            f"◆ BRUTAL HIT! ◆ Vicious strike to {enemy_name}'s {random.choice(body_parts)}! [{dmg} damage]",
                            f"⚔ HEAVY BLOW! ⚔ You cut deep into {enemy_name}'s {random.choice(body_parts)}! [{dmg} damage]"
                        ]
                        messages.add(random.choice(crit_messages))
                    else:
                        # Normal hits
                        hit_messages = [
                            f"You strike {enemy_name}'s {random.choice(body_parts)}. [{dmg} damage]",
                            f"Your attack hits {enemy_name} in the {random.choice(body_parts)}. [{dmg} damage]",
                            f"You wound {enemy_name}'s {random.choice(body_parts)}. [{dmg} damage]",
                            f"Your blade finds {enemy_name}'s {random.choice(body_parts)}! [{dmg} damage]"
                        ]
                        messages.add(random.choice(hit_messages))
                except Exception as e:
                    logger.exception(f"Exception generating combat message: {e}")
                    messages.add(f"You hit {getattr(enemy,'name','the enemy')} for {dmg}.")
            if messages is not None:
                for _n in form_notes:
                    try: messages.add(_n)
                    except Exception: pass
            return True, int(dmg)
        else:
            if messages is not None:
                try:
                    miss_messages = [
                        "Your attack misses!",
                        "You swing but miss!",
                        "Your strike goes wide!",
                        "The enemy dodges your attack!"
                    ]
                    messages.add(random.choice(miss_messages))
                except Exception as e:
                    logger.exception(f"Exception generating miss message: {e}")
                    messages.add("You miss.")
            return False, 0
    except Exception as e:
        logger.exception(f"Attack failed: {e}")
        if messages is not None:
            try: messages.add("Attack failed (internal).")
            except Exception: pass
        return False, 0

ATTACK_DESCRIPTIONS = {
    WeaponType.BLASTER_PISTOL: [
        "You fire a precise shot with your blaster pistol.",
        "A quick draw and fire from your blaster pistol.",
        "You squeeze the trigger on your blaster pistol.",
    ],
    WeaponType.BLASTER_RIFLE: [
        "You unleash a burst from your blaster rifle.",
        "A steady aim and fire from your blaster rifle.",
        "You pull the trigger on your blaster rifle.",
    ],
    WeaponType.HEAVY_BLASTER: [
        "You blast away with your heavy blaster.",
        "A powerful shot from your heavy blaster.",
        "You fire a devastating blast from your heavy blaster.",
    ],
    WeaponType.WOOKIE_BOWCASTER: [
        "You loose a quarrel from your bowcaster.",
        "A mighty twang from your bowcaster.",
        "You fire an explosive quarrel from your bowcaster.",
    ],
    WeaponType.CROSSBOW: [
        "You release a bolt from your crossbow.",
        "A silent shot from your crossbow.",
        "You fire a piercing bolt from your crossbow.",
    ],
    WeaponType.THERMAL_DETONATOR: [
        "You hurl a thermal detonator.",
        "A thrown explosive from your thermal detonator.",
        "You toss a thermal detonator at the enemy.",
    ],
    WeaponType.VIBROBLADE: [
        "You slash with your vibroblade.",
        "A quick strike with your vibroblade.",
        "You thrust your vibroblade forward.",
    ],
    WeaponType.LIGHTSABER: [
        "You swing your lightsaber in a graceful arc.",
        "A humming slash from your lightsaber.",
        "You deflect and counter with your lightsaber.",
    ],
    WeaponType.DUAL_LIGHTSABER: [
        "You whirl your dual lightsabers in a deadly dance.",
        "A spinning attack with your dual lightsabers.",
        "You cross your dual lightsabers for a powerful strike.",
    ],
    WeaponType.LIGHTSABER_PIKE: [
        "You thrust with your lightsaber pike.",
        "A sweeping strike from your lightsaber pike.",
        "You jab forward with your lightsaber pike.",
    ],
}

def get_combat_description(weapon_type: WeaponType) -> str:
    """Get a random combat description for the weapon type."""
    descriptions = ATTACK_DESCRIPTIONS.get(weapon_type, ["You attack with your weapon."])
    return random.choice(descriptions)
