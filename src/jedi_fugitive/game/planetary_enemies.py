"""Planetary local enemies that vary by biome/terrain type."""

from jedi_fugitive.game.enemy import Enemy
import random


# ============ DESERT BIOME ENEMIES ============

def create_desert_raider(level=1):
    """Wasteland scavenger adapted to desert heat."""
    enemy = Enemy(
        name="Desert Raider",
        hp=18 + level * 3,
        attack=11 + level * 2,
        defense=2,
        evasion=18,
        personality=None,
        xp_value=32,
        level=level
    )
    enemy.symbol = 'r'
    enemy.enemy_behavior = 'flanker'
    enemy.alert_range = 9
    enemy.description = "Sun-scorched nomad who knows every dune"
    enemy.biome = 'desert'
    return enemy


def create_sandworm_spawn(level=1):
    """Small sandworm that emerges from dunes."""
    enemy = Enemy(
        name="Sandworm Spawn",
        hp=25 + level * 5,
        attack=13 + level * 2,
        defense=4,
        evasion=8,
        personality=None,
        xp_value=40,
        level=level
    )
    enemy.symbol = 'w'
    enemy.enemy_behavior = 'aggressive'
    enemy.alert_range = 6
    enemy.description = "Young sandworm hunting in the dunes"
    enemy.biome = 'desert'
    return enemy


def create_dust_stalker(level=1):
    """Predator that uses sandstorms for cover."""
    enemy = Enemy(
        name="Dust Stalker",
        hp=20 + level * 4,
        attack=12 + level * 2,
        defense=1,
        evasion=22,
        personality=None,
        xp_value=38,
        level=level
    )
    enemy.symbol = 'd'
    enemy.enemy_behavior = 'flanker'
    enemy.alert_range = 8
    enemy.description = "Creature that moves like a mirage through sandstorms"
    enemy.biome = 'desert'
    return enemy


# ============ FOREST BIOME ENEMIES ============

def create_forest_ambusher(level=1):
    """Stealthy predator that hides in dense foliage."""
    enemy = Enemy(
        name="Forest Ambusher",
        hp=16 + level * 3,
        attack=13 + level * 2,
        defense=2,
        evasion=25,
        personality=None,
        xp_value=35,
        level=level
    )
    enemy.symbol = 'a'
    enemy.enemy_behavior = 'flanker'
    enemy.alert_range = 7
    enemy.description = "Silent hunter that strikes from the shadows of trees"
    enemy.biome = 'forest'
    return enemy


def create_vine_beast(level=1):
    """Territorial creature covered in living vines."""
    enemy = Enemy(
        name="Vine Beast",
        hp=28 + level * 6,
        attack=10 + level * 2,
        defense=5,
        evasion=10,
        personality=None,
        xp_value=42,
        level=level
    )
    enemy.symbol = 'v'
    enemy.enemy_behavior = 'aggressive'
    enemy.alert_range = 5
    enemy.description = "Massive creature tangled with aggressive plant life"
    enemy.biome = 'forest'
    return enemy


def create_canopy_hunter(level=1):
    """Agile predator that drops from trees."""
    enemy = Enemy(
        name="Canopy Hunter",
        hp=15 + level * 3,
        attack=11 + level * 2,
        defense=1,
        evasion=20,
        personality=None,
        xp_value=33,
        level=level
    )
    enemy.symbol = 'h'
    enemy.enemy_behavior = 'flanker'
    enemy.alert_range = 8
    enemy.description = "Tree-dwelling predator with incredible reflexes"
    enemy.biome = 'forest'
    return enemy


# ============ ROCKY/MOUNTAIN BIOME ENEMIES ============

def create_rock_lizard(level=1):
    """Camouflaged reptile that blends with stone."""
    enemy = Enemy(
        name="Rock Lizard",
        hp=22 + level * 4,
        attack=10 + level * 2,
        defense=6,
        evasion=12,
        personality=None,
        xp_value=36,
        level=level
    )
    enemy.symbol = 'l'
    enemy.enemy_behavior = 'standard'
    enemy.alert_range = 6
    enemy.description = "Stone-skinned reptile that waits motionless for prey"
    enemy.biome = 'rocky'
    return enemy


def create_cliff_raider(level=1):
    """Mountain bandit who knows every outcrop."""
    enemy = Enemy(
        name="Cliff Raider",
        hp=19 + level * 3,
        attack=12 + level * 2,
        defense=3,
        evasion=16,
        personality=None,
        xp_value=34,
        level=level
    )
    enemy.symbol = 'c'
    enemy.enemy_behavior = 'ranged'
    enemy.preferred_range = 5
    enemy.alert_range = 10
    enemy.description = "Mountain scavenger who strikes from high ground"
    enemy.biome = 'rocky'
    return enemy


def create_boulder_brute(level=1):
    """Massive creature that hurls rocks."""
    enemy = Enemy(
        name="Boulder Brute",
        hp=35 + level * 7,
        attack=14 + level * 3,
        defense=7,
        evasion=5,
        personality=None,
        xp_value=50,
        level=level
    )
    enemy.symbol = 'B'
    enemy.enemy_behavior = 'aggressive'
    enemy.alert_range = 6
    enemy.description = "Enormous beast covered in stone-like hide"
    enemy.biome = 'rocky'
    return enemy


# ============ PLAINS BIOME ENEMIES ============

def create_plains_stalker(level=1):
    """Swift predator that hunts in open grassland."""
    enemy = Enemy(
        name="Plains Stalker",
        hp=17 + level * 3,
        attack=11 + level * 2,
        defense=1,
        evasion=20,
        personality=None,
        xp_value=30,
        level=level
    )
    enemy.symbol = 'p'
    enemy.enemy_behavior = 'flanker'
    enemy.alert_range = 10
    enemy.description = "Fast-moving hunter that circles prey in open terrain"
    enemy.biome = 'plains'
    return enemy


def create_grassland_pack_hunter(level=1):
    """Social predator that coordinates with others."""
    enemy = Enemy(
        name="Pack Hunter",
        hp=14 + level * 3,
        attack=10 + level * 2,
        defense=2,
        evasion=18,
        personality=None,
        xp_value=28,
        level=level
    )
    enemy.symbol = 'k'
    enemy.enemy_behavior = 'flanker'
    enemy.alert_range = 9
    enemy.description = "Cunning predator that hunts in coordinated groups"
    enemy.biome = 'plains'
    return enemy


def create_plains_charger(level=1):
    """Large beast that charges at threats."""
    enemy = Enemy(
        name="Plains Charger",
        hp=30 + level * 6,
        attack=13 + level * 3,
        defense=4,
        evasion=8,
        personality=None,
        xp_value=44,
        level=level
    )
    enemy.symbol = 'C'
    enemy.enemy_behavior = 'aggressive'
    enemy.alert_range = 7
    enemy.description = "Massive herd animal that tramples intruders"
    enemy.biome = 'plains'
    return enemy


# ============ RIVER BIOME ENEMIES ============

def create_river_lurker(level=1):
    """Amphibious predator that hunts near water."""
    enemy = Enemy(
        name="River Lurker",
        hp=20 + level * 4,
        attack=11 + level * 2,
        defense=3,
        evasion=15,
        personality=None,
        xp_value=35,
        level=level
    )
    enemy.symbol = 'u'
    enemy.enemy_behavior = 'standard'
    enemy.alert_range = 6
    enemy.description = "Amphibious creature that drags prey into water"
    enemy.biome = 'river'
    return enemy


def create_swamp_crawler(level=1):
    """Toxic creature adapted to wetlands."""
    enemy = Enemy(
        name="Swamp Crawler",
        hp=18 + level * 4,
        attack=10 + level * 2,
        defense=4,
        evasion=12,
        personality=None,
        xp_value=37,
        level=level
    )
    enemy.symbol = 's'
    enemy.enemy_behavior = 'standard'
    enemy.alert_range = 5
    enemy.description = "Toxic marsh dweller with venomous bite"
    enemy.biome = 'river'
    return enemy


def create_water_serpent(level=1):
    """Large aquatic predator."""
    enemy = Enemy(
        name="Water Serpent",
        hp=26 + level * 5,
        attack=12 + level * 2,
        defense=3,
        evasion=16,
        personality=None,
        xp_value=40,
        level=level
    )
    enemy.symbol = 'S'
    enemy.enemy_behavior = 'aggressive'
    enemy.alert_range = 8
    enemy.description = "Massive serpent that strikes from beneath the surface"
    enemy.biome = 'river'
    return enemy


# ============ CRASH SITE BIOME ENEMIES ============

def create_scrap_scavenger(level=1):
    """Creature attracted to wreckage and technology."""
    enemy = Enemy(
        name="Scrap Scavenger",
        hp=16 + level * 3,
        attack=10 + level * 2,
        defense=3,
        evasion=14,
        personality=None,
        xp_value=30,
        level=level
    )
    enemy.symbol = 'x'
    enemy.enemy_behavior = 'standard'
    enemy.alert_range = 7
    enemy.description = "Opportunistic creature drawn to metal and debris"
    enemy.biome = 'crash_site'
    return enemy


def create_radiation_mutant(level=1):
    """Creature warped by leaking fuel cells."""
    enemy = Enemy(
        name="Radiation Mutant",
        hp=24 + level * 5,
        attack=13 + level * 3,
        defense=2,
        evasion=10,
        personality=None,
        xp_value=42,
        level=level
    )
    enemy.symbol = 'm'
    enemy.enemy_behavior = 'aggressive'
    enemy.alert_range = 6
    enemy.description = "Twisted creature mutated by toxic wreckage"
    enemy.biome = 'crash_site'
    return enemy


# ============ BIOME ENEMY COLLECTIONS ============

BIOME_ENEMIES = {
    'desert': [
        create_desert_raider,
        create_sandworm_spawn,
        create_dust_stalker,
    ],
    'forest': [
        create_forest_ambusher,
        create_vine_beast,
        create_canopy_hunter,
    ],
    'rocky': [
        create_rock_lizard,
        create_cliff_raider,
        create_boulder_brute,
    ],
    'plains': [
        create_plains_stalker,
        create_grassland_pack_hunter,
        create_plains_charger,
    ],
    'river': [
        create_river_lurker,
        create_swamp_crawler,
        create_water_serpent,
    ],
    'crash_site': [
        create_scrap_scavenger,
        create_radiation_mutant,
    ],
    'mountain_pass': [
        # Mountain pass uses rocky enemies
        create_rock_lizard,
        create_cliff_raider,
    ]
}


def create_biome_enemy(biome, level=1):
    """Create a random enemy appropriate for the given biome."""
    enemy_factories = BIOME_ENEMIES.get(biome, BIOME_ENEMIES.get('plains', []))
    
    if not enemy_factories:
        # Fallback to plains if biome not found
        enemy_factories = BIOME_ENEMIES['plains']
    
    factory = random.choice(enemy_factories)
    return factory(level)


def get_biome_enemy_types(biome):
    """Get list of enemy factory functions for a specific biome."""
    return BIOME_ENEMIES.get(biome, BIOME_ENEMIES.get('plains', []))


def create_mixed_biome_group(biome, count=3, level=1):
    """Create a diverse group of enemies from the same biome."""
    enemy_factories = BIOME_ENEMIES.get(biome, BIOME_ENEMIES.get('plains', []))
    
    if not enemy_factories:
        enemy_factories = BIOME_ENEMIES['plains']
    
    group = []
    # Shuffle to ensure variety
    factories_pool = list(enemy_factories)
    random.shuffle(factories_pool)
    
    for i in range(count):
        factory = factories_pool[i % len(factories_pool)]
        enemy = factory(level)
        group.append(enemy)
    
    return group


def get_all_biomes():
    """Get list of all available biomes."""
    return list(BIOME_ENEMIES.keys())
