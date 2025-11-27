"""
Biome-Specific Encounters for Dark Meridian.
Unique events, POIs, and encounters tailored to each biome type.
"""
import random

# Biome-specific encounters
BIOME_ENCOUNTERS = {
    'crash_site': {
        'name': 'Ship Graveyard',
        'encounters': [
            {
                'name': 'Escape Pod',
                'description': [
                    "An intact escape pod lies half-buried in the debris.",
                    "The hatch is sealed, but you hear movement inside.",
                    "Someone survived the crash. Or something.",
                ],
                'discovery': {
                    'light': "You force open the hatch. Inside, a terrified survivor collapses in relief.",
                    'dark': "You breach the pod, ready for threat. Just a survivor. Pathetic.",
                    'balanced': "You carefully open the hatch. A survivor emerges, wary but grateful.",
                },
                'corruption_range': (0, 100),
            },
            {
                'name': 'Black Box Recovery',
                'description': [
                    "You locate the ship's flight recorder among the wreckage.",
                    "Its data could reveal what brought the vessel down.",
                    "But accessing it requires technical skill - or brute force.",
                ],
                'discovery': {
                    'light': "You carefully extract the data, preserving evidence of what happened.",
                    'dark': "You rip out the recorder. The past doesn't matter. Only survival.",
                    'balanced': "You recover the black box. Knowledge is power.",
                },
                'corruption_range': (0, 100),
            },
            {
                'name': 'Fuel Cache',
                'description': [
                    "Emergency fuel cells lie scattered near a broken cargo hold.",
                    "Still viable after all this time. Valuable for trade or repairs.",
                ],
                'reward': 'fuel_cells',
                'corruption_range': (0, 100),
            },
        ],
    },
    'forest': {
        'name': 'Ancient Woods',
        'encounters': [
            {
                'name': 'Force-Sensitive Tree',
                'description': [
                    "At the forest's heart stands an impossibly ancient tree.",
                    "The Force flows through it like a living current.",
                    "Jedi of old meditated beneath its branches.",
                ],
                'discovery': {
                    'light': "You sit in meditation. The tree shares visions of peace and growth.",
                    'dark': "The tree recoils from your darkness. Its wisdom is lost to you.",
                    'balanced': "You touch the bark. Past and present flow together in harmony.",
                },
                'corruption_range': (0, 70),
                'effect': 'force_wisdom',
            },
            {
                'name': 'Hunter Camp',
                'description': [
                    "You find a makeshift camp. Hunters, tracking something.",
                    "Traps surround the area. Beware.",
                ],
                'discovery': {
                    'light': "You announce yourself. They're wary, but accept your help against predators.",
                    'dark': "You eliminate them before they see you. Fewer witnesses.",
                    'balanced': "You bypass the camp unseen. Their hunt is not your concern.",
                },
                'corruption_range': (0, 100),
            },
            {
                'name': 'Hidden Grove',
                'description': [
                    "Through dense undergrowth, you discover a tranquil grove.",
                    "Medicinal plants grow here in abundance.",
                    "This place feels... safe.",
                ],
                'reward': 'healing_herbs',
                'corruption_range': (0, 60),
            },
        ],
    },
    'desert': {
        'name': 'Endless Dunes',
        'encounters': [
            {
                'name': 'Oasis',
                'description': [
                    "Against all odds, you find water. An oasis, green and alive.",
                    "Others have been here. Recently.",
                ],
                'discovery': {
                    'light': "You share the water with travelers you encounter. Generosity brings allies.",
                    'dark': "You claim the oasis for yourself. Drive off anyone who approaches.",
                    'balanced': "You fill your containers and move on. Resources are survival.",
                },
                'corruption_range': (0, 100),
                'reward': 'water_supply',
            },
            {
                'name': 'Sand People Ruins',
                'description': [
                    "Ancient dwellings carved into rock. Long abandoned.",
                    "The Tusken Raiders who lived here left artifacts behind.",
                ],
                'discovery': {
                    'light': "You respectfully examine their culture. Understanding brings wisdom.",
                    'dark': "You loot everything of value. The dead have no need of possessions.",
                    'balanced': "You take what's useful, leave the rest. Practical.",
                },
                'corruption_range': (0, 100),
                'reward': 'ancient_artifacts',
            },
            {
                'name': 'Sandstorm Shelter',
                'description': [
                    "A massive sandstorm approaches. You spot a cave.",
                    "Inside, ancient carvings depict a Jedi's journey through trials.",
                ],
                'discovery': {
                    'light': "You study the carvings during the storm. Patience rewards understanding.",
                    'dark': "You ignore the murals. Storms pass. Power endures.",
                    'balanced': "You wait out the storm. The carvings tell of balance.",
                },
                'corruption_range': (0, 100),
                'effect': 'knowledge',
            },
        ],
    },
    'mountain_pass': {
        'name': 'Treacherous Heights',
        'encounters': [
            {
                'name': 'Hermit Cave',
                'description': [
                    "High in the mountains, a cave shows signs of habitation.",
                    "Someone lives here, far from civilization.",
                ],
                'discovery': {
                    'light': "An old Jedi hermit greets you. They offer wisdom and rest.",
                    'dark': "A fallen Jedi dwells here, consumed by bitterness. They attack.",
                    'balanced': "A Gray Jedi makes this their home. They're neither friend nor foe.",
                },
                'corruption_range': (0, 100),
                'npc_trigger': True,
            },
            {
                'name': 'Ancient Shrine',
                'description': [
                    "A meditation platform built into the mountainside.",
                    "The Force is strong here. Light and dark in balance.",
                ],
                'discovery': {
                    'light': "You meditate on the light side. Clarity fills you.",
                    'dark': "You draw on dark power. The abyss stares back.",
                    'balanced': "You achieve perfect balance. For a moment, you understand everything.",
                },
                'corruption_range': (0, 100),
                'effect': 'meditation_bonus',
            },
            {
                'name': 'Frozen Battlefield',
                'description': [
                    "Ancient warriors fell here millennia ago.",
                    "Their weapons and armor, preserved by ice.",
                ],
                'reward': 'ancient_equipment',
                'corruption_range': (0, 100),
            },
        ],
    },
    'rocky': {
        'name': 'Barren Wastes',
        'encounters': [
            {
                'name': 'Mining Operation',
                'description': [
                    "An abandoned mining facility. Equipment still functional.",
                    "Valuable ores remain in the tunnels.",
                ],
                'reward': 'rare_minerals',
                'corruption_range': (0, 100),
            },
            {
                'name': 'Sith Monument',
                'description': [
                    "A towering statue of a Sith Lord, weathered but intact.",
                    "Dark energy pulses from the stone.",
                ],
                'discovery': {
                    'light': "You sense evil in the monument. You should destroy it.",
                    'dark': "The monument calls to you. Power awaits those who listen.",
                    'balanced': "It's just stone. But the Force remembers.",
                },
                'corruption_range': (0, 100),
                'effect': 'dark_presence',
            },
            {
                'name': 'Crystal Cave',
                'description': [
                    "Natural crystal formations fill this cavern.",
                    "Some resonate with the Force. Kyber crystals?",
                ],
                'reward': 'force_crystals',
                'corruption_range': (0, 80),
            },
        ],
    },
    'river': {
        'name': 'Flowing Waters',
        'encounters': [
            {
                'name': 'Fishing Village',
                'description': [
                    "A small settlement by the water. Simple people, wary of strangers.",
                ],
                'discovery': {
                    'light': "You help them with their troubles. They welcome you.",
                    'dark': "You intimidate them into giving you supplies. Fear works.",
                    'balanced': "You trade fairly. Business is business.",
                },
                'corruption_range': (0, 100),
                'npc_trigger': True,
            },
            {
                'name': 'Underwater Temple',
                'description': [
                    "Ruins extend beneath the water's surface.",
                    "Ancient Force users built temples in strange places.",
                ],
                'discovery': {
                    'light': "You dive deep, finding preserved Jedi texts.",
                    'dark': "You sense Sith artifacts below. The depths call.",
                    'balanced': "You explore carefully. Knowledge lies beneath.",
                },
                'corruption_range': (0, 100),
                'reward': 'ancient_texts',
            },
            {
                'name': 'Bridge Ambush',
                'description': [
                    "The only bridge across the river. Perfect ambush site.",
                    "Bandits wait on the far side.",
                ],
                'corruption_range': (30, 100),
                'combat_trigger': True,
            },
        ],
    },
    'plains': {
        'name': 'Open Grasslands',
        'encounters': [
            {
                'name': 'Caravan',
                'description': [
                    "Traders moving between settlements. Safety in numbers.",
                ],
                'discovery': {
                    'light': "You offer protection. They share news and supplies.",
                    'dark': "You rob them. They had more than they needed.",
                    'balanced': "You trade. Fair exchange.",
                },
                'corruption_range': (0, 100),
                'trade_trigger': True,
            },
            {
                'name': 'Battlefield Memorial',
                'description': [
                    "Markers honor fallen soldiers. Republic and Sith alike.",
                    "The war consumed them all.",
                ],
                'discovery': {
                    'light': "You pay respects to all who fell. No side claims righteousness.",
                    'dark': "The weak died. The strong survived. It's that simple.",
                    'balanced': "You acknowledge their sacrifice. War wastes potential.",
                },
                'corruption_range': (0, 100),
            },
            {
                'name': 'Herd Migration',
                'description': [
                    "Massive beasts migrate across the plains.",
                    "Their path offers cover and concealment.",
                ],
                'reward': 'safe_passage',
                'corruption_range': (0, 100),
            },
        ],
    },
    'tomb': {
        'name': 'Sith Necropolis',
        'encounters': [
            {
                'name': 'Trapped Corridor',
                'description': [
                    "Ancient Sith trap mechanisms still function.",
                    "One wrong step...",
                ],
                'corruption_range': (0, 100),
                'hazard': 'traps',
            },
            {
                'name': 'Meditation Chamber',
                'description': [
                    "A Sith Lord meditated here for decades.",
                    "Their presence lingers, watching, judging.",
                ],
                'discovery': {
                    'light': "You resist the dark presence. It weakens.",
                    'dark': "You embrace the Sith teachings. Power flows.",
                    'balanced': "You acknowledge both light and dark. Neither owns you.",
                },
                'corruption_range': (0, 100),
                'effect': 'force_test',
            },
            {
                'name': 'Treasury',
                'description': [
                    "Ancient Sith hoarded wealth beyond measure.",
                    "Gold, artifacts, forbidden knowledge.",
                ],
                'reward': 'sith_treasure',
                'corruption_range': (0, 100),
            },
        ],
    },
}

def get_biome_encounter(biome_type):
    """Get a random encounter for the specified biome."""
    if biome_type not in BIOME_ENCOUNTERS:
        return None
    
    biome_data = BIOME_ENCOUNTERS[biome_type]
    return random.choice(biome_data['encounters'])

def check_encounter_availability(encounter, player_corruption):
    """Check if encounter is available based on player's corruption level."""
    if 'corruption_range' not in encounter:
        return True
    
    min_corrupt, max_corrupt = encounter['corruption_range']
    return min_corrupt <= player_corruption <= max_corrupt

def get_discovery_text(encounter, player_corruption):
    """Get appropriate discovery text based on player's alignment."""
    if 'discovery' not in encounter:
        return None
    
    if player_corruption <= 35:
        return encounter['discovery'].get('light')
    elif player_corruption <= 65:
        return encounter['discovery'].get('balanced')
    else:
        return encounter['discovery'].get('dark')

def format_encounter_display(biome_type, encounter, player_corruption):
    """Format an encounter for display to the player."""
    lines = []
    biome_name = BIOME_ENCOUNTERS[biome_type]['name']
    lines.append("═" * 60)
    lines.append(f"  {biome_name.upper()}  ".center(60))
    lines.append("═" * 60)
    lines.append("")
    lines.append(f"You discover: {encounter['name']}")
    lines.append("")
    
    for line in encounter['description']:
        lines.append(line)
        lines.append("")
    
    discovery = get_discovery_text(encounter, player_corruption)
    if discovery:
        lines.append("─" * 60)
        lines.append(discovery)
    
    if 'reward' in encounter:
        lines.append("")
        lines.append(f"Reward: {encounter['reward'].replace('_', ' ').title()}")
    
    if 'effect' in encounter:
        lines.append("")
        lines.append(f"Effect: {encounter['effect'].replace('_', ' ').title()}")
    
    return lines

def should_spawn_encounter(biome_type, turns_since_last, player_corruption=50, visited_before=False):
    """Determine if an encounter should spawn in this biome.
    
    Args:
        biome_type: The type of biome
        turns_since_last: Number of turns since last encounter
        player_corruption: Player's corruption level (0-100)
        visited_before: Whether player has visited this biome type before
    
    Returns:
        bool: True if encounter should spawn
    """
    if biome_type not in BIOME_ENCOUNTERS:
        return False
    
    # Require minimum turns between encounters (200-300 turns for proper spacing)
    min_turns = 200
    max_turns = 300
    
    if turns_since_last < min_turns:
        return False
    
    # Gradually increase spawn chance as more turns pass
    if turns_since_last >= max_turns:
        return True
    
    # Calculate chance based on turns elapsed
    turn_progress = (turns_since_last - min_turns) / (max_turns - min_turns)
    base_chance = turn_progress * 0.5  # Max 50% chance before forced spawn
    
    # Modify chance based on biome type
    modifiers = {
        'crash_site': 1.2,  # More encounters near crash
        'tomb': 1.5,  # Sith tombs are rich with encounters
        'forest': 1.0,
        'desert': 0.8,  # Sparse
        'mountain_pass': 1.1,
        'rocky': 0.9,
        'river': 1.0,
        'plains': 0.85,
    }
    
    final_chance = base_chance * modifiers.get(biome_type, 1.0)
    return random.random() < final_chance

# Statistics
def get_encounter_statistics():
    """Get statistics about biome encounters."""
    stats = {
        'total_biomes': len(BIOME_ENCOUNTERS),
        'total_encounters': 0,
        'by_biome': {},
        'with_rewards': 0,
        'with_effects': 0,
        'with_combat': 0,
        'with_npcs': 0,
    }
    
    for biome_type, biome_data in BIOME_ENCOUNTERS.items():
        encounter_count = len(biome_data['encounters'])
        stats['total_encounters'] += encounter_count
        stats['by_biome'][biome_type] = encounter_count
        
        for encounter in biome_data['encounters']:
            if 'reward' in encounter:
                stats['with_rewards'] += 1
            if 'effect' in encounter:
                stats['with_effects'] += 1
            if encounter.get('combat_trigger'):
                stats['with_combat'] += 1
            if encounter.get('npc_trigger'):
                stats['with_npcs'] += 1
    
    return stats
