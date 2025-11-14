"""Diverse enemy types with unique behaviors and tactics."""

from jedi_fugitive.game.enemy import Enemy


def create_sith_sniper(level=1):
    """Long-range enemy that stays back and shoots."""
    enemy = Enemy(
        name="Sith Marksman",
        hp=15 + level * 3,
        attack=10 + level * 2,
        defense=1,
        evasion=15,
        personality=None,
        xp_value=30,
        level=level
    )
    enemy.symbol = 'M'
    enemy.enemy_behavior = 'sniper'
    enemy.preferred_range = 6
    enemy.alert_range = 10
    enemy.description = "A deadly sharpshooter who prefers distance"
    return enemy


def create_sith_brawler(level=1):
    """Aggressive melee fighter that always charges."""
    enemy = Enemy(
        name="Sith Berserker",
        hp=30 + level * 6,
        attack=14 + level * 3,
        defense=3,
        evasion=5,
        personality=None,
        xp_value=40,
        level=level
    )
    enemy.symbol = 'B'
    enemy.enemy_behavior = 'aggressive'
    enemy.alert_range = 8
    enemy.description = "A fearsome warrior who charges without hesitation"
    return enemy


def create_sith_assassin(level=1):
    """Stealthy flanker that attacks from sides."""
    enemy = Enemy(
        name="Sith Assassin",
        hp=18 + level * 3,
        attack=12 + level * 2,
        defense=2,
        evasion=25,
        personality=None,
        xp_value=45,
        level=level
    )
    enemy.symbol = 'A'
    enemy.enemy_behavior = 'flanker'
    enemy.alert_range = 7
    enemy.description = "A cunning killer who strikes from the shadows"
    return enemy


def create_sith_trooper(level=1):
    """Standard balanced soldier with ranged capability."""
    enemy = Enemy(
        name="Sith Trooper",
        hp=20 + level * 4,
        attack=11 + level * 2,
        defense=4,
        evasion=10,
        personality=None,
        xp_value=35,
        level=level
    )
    enemy.symbol = 'T'
    enemy.enemy_behavior = 'ranged'
    enemy.preferred_range = 4
    enemy.alert_range = 6
    enemy.description = "A disciplined soldier with tactical training"
    return enemy


def create_sith_scout(level=1):
    """Fast-moving flanker with high evasion."""
    enemy = Enemy(
        name="Sith Scout",
        hp=16 + level * 3,
        attack=9 + level * 2,
        defense=1,
        evasion=20,
        personality=None,
        xp_value=30,
        level=level
    )
    enemy.symbol = 'S'
    enemy.enemy_behavior = 'flanker'
    enemy.alert_range = 9
    enemy.description = "An agile scout who circles to find weaknesses"
    return enemy


def create_sith_guardian(level=1):
    """Tanky defender with high HP and defense."""
    enemy = Enemy(
        name="Sith Guardian",
        hp=40 + level * 8,
        attack=10 + level * 2,
        defense=6,
        evasion=5,
        personality=None,
        xp_value=50,
        level=level
    )
    enemy.symbol = 'G'
    enemy.enemy_behavior = 'aggressive'
    enemy.alert_range = 5
    enemy.description = "A heavily armored defender built like a fortress"
    return enemy


def create_dark_acolyte(level=1):
    """Force-sensitive enemy with moderate stats."""
    enemy = Enemy(
        name="Dark Acolyte",
        hp=22 + level * 4,
        attack=13 + level * 2,
        defense=2,
        evasion=15,
        personality=None,
        xp_value=55,
        level=level
    )
    enemy.symbol = 'D'
    enemy.enemy_behavior = 'standard'
    enemy.alert_range = 7
    enemy.description = "A Force-sensitive apprentice of the dark side"
    return enemy


# Collection of all enemy factory functions
ENEMY_TYPES = {
    'sniper': create_sith_sniper,
    'brawler': create_sith_brawler,
    'assassin': create_sith_assassin,
    'trooper': create_sith_trooper,
    'scout': create_sith_scout,
    'guardian': create_sith_guardian,
    'acolyte': create_dark_acolyte,
}


def create_random_enemy(level=1):
    """Create a random enemy from the available types."""
    import random
    enemy_type = random.choice(list(ENEMY_TYPES.keys()))
    return ENEMY_TYPES[enemy_type](level)


def create_mixed_group(count=3, level=1):
    """Create a diverse group of enemies with complementary tactics."""
    import random
    group = []
    
    # Ensure variety
    types_pool = list(ENEMY_TYPES.keys())
    random.shuffle(types_pool)
    
    for i in range(count):
        enemy_type = types_pool[i % len(types_pool)]
        enemy = ENEMY_TYPES[enemy_type](level)
        group.append(enemy)
    
    return group
