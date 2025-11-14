from jedi_fugitive.game.enemy import Enemy
from typing import Tuple, List
# fixed import: Display lives in game.level, not jedi_fugitive.display
from jedi_fugitive.game.level import Display
from jedi_fugitive.items.weapons import WeaponType, Weapon
import random

def calculate_hit(accuracy: int, evasion: int) -> bool:
    """Calculate if an attack hits based on accuracy and evasion."""
    hit_chance = max(5, min(95, accuracy - evasion + 50))
    return random.randint(1, 100) <= hit_chance

def player_attack(player, enemy, messages=None, game=None):
    """Player attacks enemy. Accepts optional messages buffer and game for compatibility."""
    try:
        # prefer player's effective accuracy which accounts for stress/equipment
        try:
            acc = int(player.get_effective_accuracy())
        except Exception:
            acc = getattr(player, "accuracy", 0)
        ev = getattr(enemy, "evasion", 0)
        if calculate_hit(acc, ev):
            if getattr(player, "equipped_weapon", None):
                try:
                    dmg = player.equipped_weapon.get_damage()
                except Exception:
                    dmg = getattr(player, "attack", 1)
            else:
                dmg = getattr(player, "attack", 1)
            try:
                enemy.hp = getattr(enemy, "hp", 0) - int(dmg)
            except Exception:
                try: setattr(enemy, "hp", getattr(enemy, "hp", 0) - int(dmg))
                except Exception: pass
            
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
                    elif dmg >= 8:
                        # High damage critical hits with emphasis
                        crit_messages = [
                            f"⚡ CRITICAL! ⚡ You brutally slash {enemy_name}'s {random.choice(body_parts)}! [{dmg} damage]",
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
                except Exception: 
                    messages.add(f"You hit {getattr(enemy,'name','the enemy')} for {dmg}.")
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
                except Exception: 
                    messages.add("You miss.")
            return False, 0
    except Exception:
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
