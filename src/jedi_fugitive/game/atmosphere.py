"""
Atmospheric descriptions and immersive elements for Jedi Fugitive.
Provides biome-specific ambient descriptions, Force visions, and environmental storytelling.
"""
import random

# Biome atmospheric descriptions
BIOME_ATMOSPHERES = {
    'forest': [
        "Ancient trees loom overhead, their bark scarred by old lightsaber burns.",
        "The forest whispers with the echoes of long-forgotten battles.",
        "Moss-covered ruins peek through the undergrowth, remnants of a Jedi temple.",
        "The canopy above filters the light into shifting patterns of shadow.",
        "Strange bird calls echo through the trees - or are they Force-sensitive warnings?",
        "Vines hang like silent witnesses to countless years of solitude.",
        "The air here is thick with the scent of decay and new growth intertwined.",
    ],
    'desert': [
        "The desert wind howls, carrying whispers of the past across the dunes.",
        "Sand shifts beneath your feet, revealing ancient debris from the Old Republic.",
        "Heat mirages dance on the horizon - or are they Force visions?",
        "The sun beats down mercilessly, testing your connection to the living Force.",
        "Bleached bones half-buried in sand mark where others failed to survive.",
        "The endless expanse makes you feel both infinitely small and deeply connected.",
        "Sandstorms on the horizon promise change - for better or worse.",
    ],
    'rocky': [
        "The rocky terrain echoes with distant sounds - battle cries from another era.",
        "Jagged spires of stone reach skyward like accusing fingers.",
        "Ancient cave paintings depict robed figures locked in eternal conflict.",
        "The stones themselves seem to remember the weight of countless footsteps.",
        "Wind-carved formations create haunting shapes in the twilight.",
        "Every crevice could hide danger, or perhaps salvation.",
        "The harsh landscape has forged many warriors - will it forge you?",
    ],
    'plains': [
        "Tall grass waves in an endless sea, concealing what lies beneath.",
        "The open expanse offers nowhere to hide - from enemies or yourself.",
        "Wildflowers bloom where blood was once spilled, nature reclaiming its own.",
        "The horizon stretches forever, promising both freedom and isolation.",
        "Ancient stone markers dot the plains - guideposts or grave markers?",
        "The Force flows freely here, unimpeded by walls or shadows.",
        "You can see for miles, yet the most important things remain hidden.",
    ],
    'river': [
        "The river's current mirrors the flow of the Force itself - constant, inevitable.",
        "Mist rises from the water, concealing the world in mystery.",
        "The sound of flowing water soothes your troubled mind.",
        "Ancient bridges, half-collapsed, speak of civilizations long gone.",
        "Fish leap from the water, defying gravity as you might defy fate.",
        "The river has witnessed countless journeys - where will yours lead?",
        "Water-smoothed stones hold the memories of centuries.",
    ],
    'mountain_pass': [
        "Narrow passages between towering cliffs create an oppressive atmosphere.",
        "The mountains loom like ancient sentinels, guarding long-forgotten secrets.",
        "Wind howls through the passes, carrying Sith chants from distant ages.",
        "Every shadow could conceal a threat or reveal a path forward.",
        "The thin air makes breathing difficult - or is it the dark side's presence?",
        "Stone walls bear carved inscriptions in languages you barely recognize.",
        "These mountains have seen empires rise and fall like the tides.",
    ],
    'crash_site': [
        "The wreckage of your ship stands as a monument to your survival.",
        "Scorched earth and twisted metal mark the beginning of your journey.",
        "The crash site feels both alien and strangely like home.",
        "Emergency beacons blink uselessly - no one is coming to save you.",
        "Every piece of debris holds a memory of your life before.",
        "The Force led you here - or did it crash you here on purpose?",
        "This place of destruction may become the foundation of your rebirth.",
    ],
    'tomb': [
        "Ancient darkness permeates every stone of this Sith tomb.",
        "The walls themselves seem to breathe with malevolent purpose.",
        "Whispers in the dark promise power - at a terrible price.",
        "The air is thick with centuries of hatred and ambition.",
        "Every step deeper feels like a descent into your own soul.",
        "Dark side energy pulses through the corridors like a heartbeat.",
        "The tombs of the Sith remember all who enter - and most who never leave.",
    ],
}

# Jedi Master memories (triggered periodically)
JEDI_MASTER_MEMORIES = {
    'light': [  # For light-aligned players
        'You remember your Master\'s words: "The Force flows through all things. Never forget compassion."',
        'A memory surfaces: Your Master smiling as you completed your first mind trick. "Gentle persuasion, not domination."',
        'You recall training sessions in the temple gardens. "Balance in all things, my young Padawan."',
        'Your Master\'s final lesson echoes: "If I fall, remember - the Force is stronger than any darkness."',
        'You remember Master\'s meditation teachings: "Peace is not the absence of struggle, but mastery of self."',
        'A warm memory: Your Master placing a hand on your shoulder. "I am proud of who you\'re becoming."',
        'You hear your Master\'s voice: "The light side is not about suppressing emotion, but channeling it wisely."',
    ],
    'balanced': [  # For gray/balanced players
        'You remember your Master\'s warning: "Beware certainty. Both light and dark have their truths."',
        'A memory stirs: "Power without wisdom is destruction. Wisdom without power is futility."',
        'Your Master once said: "The Force cares nothing for our labels of light and dark."',
        'You recall a difficult lesson: "Sometimes the right path lies between the extremes."',
        'Your Master\'s ambiguous smile returns to you: "Find your own way, not mine."',
        'A memory surfaces: "The Jedi Order had wisdom, but also blindness. Learn from both."',
        'You remember: "In the end, the Force judges us not by our code, but by our choices."',
    ],
    'dark': [  # For dark-aligned players
        'You remember your Master\'s fear when you first tasted the dark side\'s power.',
        'A painful memory: Your Master\'s disappointment in your eyes. Were they wrong about you?',
        'Your Master warned: "The dark side is seductive. Once you start down that path..." Were they afraid of your potential?',
        'You recall your Master holding you back. They feared your strength, didn\'t they?',
        'A bitter memory: "Control your anger," they said. But anger gives you strength they could never understand.',
        'Your Master\'s final words haunt you: "Don\'t let me have trained a Sith." But what if that\'s exactly what was needed?',
        'You remember their weakness masquerading as wisdom. You\'ve surpassed them now.',
    ],
}

# Visions of transformation based on corruption
TRANSFORMATION_VISIONS = {
    'becoming_dark': [  # For players descending into darkness
        'Vision: You see yourself, eyes burning yellow, power crackling from your fingertips.',
        'Vision: A glimpse of your future - feared across the galaxy, unstoppable.',
        'Vision: You stand atop a mountain of defeated enemies. This is your destiny.',
        'Vision: The Force shows you ruling through strength. Compassion is weakness.',
        'Vision: You see yourself breaking chains - the Jedi code was always a cage.',
        'Vision: Dark side energy transforms you into something beyond Jedi, beyond human.',
        'Vision: You walk among shadows, and the shadows bow to you.',
    ],
    'becoming_light': [  # For players staying in the light
        'Vision: You see yourself bringing peace to war-torn systems, a beacon of hope.',
        'Vision: A glimpse of your future - teaching younglings, the Jedi Order reborn.',
        'Vision: You stand as the last guardian of the light in a darkening galaxy.',
        'Vision: The Force shows you healing the wounds of the Clone Wars.',
        'Vision: You see yourself at peace, having found balance between power and compassion.',
        'Vision: Light side energy fills you with warmth and purpose.',
        'Vision: You walk a path few can see, guided by the Force itself.',
    ],
    'becoming_balanced': [  # For gray jedi
        'Vision: You see yourself as neither Jedi nor Sith, but something new.',
        'Vision: A glimpse of your future - free from dogma, wielding both light and dark.',
        'Vision: You stand at the center, light in one hand, darkness in the other, in perfect balance.',
        'Vision: The Force shows you a path the Order never imagined.',
        'Vision: You see yourself breaking the cycle that destroyed the Jedi.',
        'Vision: Neither constrained nor corrupted, you forge your own destiny.',
        'Vision: You walk between worlds, understanding both but bound by neither.',
    ],
}

def get_biome_atmosphere(biome_type):
    """Get a random atmospheric description for the current biome."""
    atmospheres = BIOME_ATMOSPHERES.get(biome_type, BIOME_ATMOSPHERES.get('crash_site'))
    return random.choice(atmospheres)

def get_master_memory(corruption_level):
    """Get a Jedi Master memory based on player's current alignment."""
    if corruption_level <= 35:
        return random.choice(JEDI_MASTER_MEMORIES['light'])
    elif corruption_level <= 65:
        return random.choice(JEDI_MASTER_MEMORIES['balanced'])
    else:
        return random.choice(JEDI_MASTER_MEMORIES['dark'])

def get_transformation_vision(corruption_level):
    """Get a vision of what the player is becoming based on their path."""
    if corruption_level <= 35:
        return random.choice(TRANSFORMATION_VISIONS['becoming_light'])
    elif corruption_level <= 65:
        return random.choice(TRANSFORMATION_VISIONS['becoming_balanced'])
    else:
        return random.choice(TRANSFORMATION_VISIONS['becoming_dark'])

def should_trigger_atmosphere(turn_count, last_atmosphere_turn):
    """Check if we should show an atmospheric description this turn."""
    # Show atmosphere every 15-25 turns
    turns_since_last = turn_count - last_atmosphere_turn
    return turns_since_last >= random.randint(15, 25)

def should_trigger_memory(turn_count, last_memory_turn):
    """Check if we should show a Jedi Master memory this turn."""
    # Show memories every 40-60 turns
    turns_since_last = turn_count - last_memory_turn
    return turns_since_last >= random.randint(40, 60)

def should_trigger_vision(turn_count, last_vision_turn):
    """Check if we should show a transformation vision this turn."""
    # Show visions every 50-80 turns
    turns_since_last = turn_count - last_vision_turn
    return turns_since_last >= random.randint(50, 80)
