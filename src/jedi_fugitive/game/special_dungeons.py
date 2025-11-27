"""
Special Dungeons - Randomly generated thematic areas with unique artifacts.
Each dungeon has a distinct theme, layout, and contains a powerful Sith artifact.
"""
import random
import math
from enum import Enum
from jedi_fugitive.game.level import Display


class DungeonType(Enum):
    MEMORY_VAULT = "memory_vault"
    CRYSTAL_GARDEN = "crystal_garden"
    SHADOWMAZE = "shadowmaze"
    BONE_CATHEDRAL = "bone_cathedral"
    ECHO_CHAMBERS = "echo_chambers"
    TWISTED_LIBRARY = "twisted_library"
    PAIN_FORGE = "pain_forge"
    DREAM_NEXUS = "dream_nexus"


class ArtifactType(Enum):
    HOLOCRON_OF_WHISPERS = "holocron_of_whispers"
    SOULSTONE_FRAGMENT = "soulstone_fragment"
    CRIMSON_CODEX = "crimson_codex"
    VOID_MIRROR = "void_mirror"
    TORMENT_CROWN = "torment_crown"
    ECHO_CRYSTAL = "echo_crystal"
    NIGHTMARE_ORB = "nightmare_orb"
    BONE_SCEPTER = "bone_scepter"


# Dungeon Templates - Now with multi-level structure and lore
DUNGEON_TEMPLATES = {
    DungeonType.MEMORY_VAULT: {
        'name': 'Vault of Lost Memories',
        'symbol': 'M',
        'size': (21, 21),
        'num_levels': 3,  # Multi-level dungeon
        'level_lore': {
            1: {
                'title': 'Chamber of Forgotten Names',
                'description': [
                    "The entrance chamber gleams with crystalline formations.",
                    "Memory fragments drift lazily through the air like snowflakes.",
                    "Names and faces of the forgotten echo through your mind."
                ],
                'atmosphere': "Faint whispers of those who were erased from history.",
            },
            2: {
                'title': 'Hall of Stolen Moments',
                'description': [
                    "The crystals grow larger here, containing entire scenes.",
                    "You witness moments of joy, terror, and betrayal frozen in time.",
                    "Some memories reach out, trying to replace your own."
                ],
                'atmosphere': "Memory fragments actively seek to overwrite your identity.",
            },
            3: {
                'title': 'Sanctum of the Erased',
                'description': [
                    "The deepest vault where memories go to die.",
                    "A massive crystal holds the consciousness of a forgotten Sith Lord.",
                    "This is where identities are unmade and reforged."
                ],
                'atmosphere': "The boundary between your memories and others' dissolves.",
            }
        },
        'description': [
            "A crystalline chamber filled with floating memory fragments.",
            "Ghostly images of the past flicker in the air around you.",
            "The walls pulse with psychic energy, showing glimpses of ancient events."
        ],
        'atmosphere': [
            "You hear whispers of forgotten conversations.",
            "A memory fragment shows a Sith Lord's final moments.",
            "The air shimmers with residual psychic imprints.",
            "Echoes of ancient pain resonate through the crystal walls.",
        ],
        'floor_tile': '◊',  # Crystal floor
        'wall_tile': '▓',   # Solid crystal walls
        'special_features': ['memory_pools', 'psychic_barriers'],
        'artifact': ArtifactType.HOLOCRON_OF_WHISPERS,
        'enemies': ['sith_ghost', 'memory_wraith'],
        'corruption_effect': 'psychic_drain'
    },
    
    DungeonType.CRYSTAL_GARDEN: {
        'name': 'Garden of Crimson Crystals',
        'symbol': 'G',
        'size': (25, 19),
        'num_levels': 4,  # Multi-level dungeon
        'level_lore': {
            1: {
                'title': 'The Outer Groves',
                'description': [
                    "Small crimson crystals sprout from the ground like deadly flowers.",
                    "Their soft humming creates an almost peaceful atmosphere.",
                    "But you sense hunger in their glow."
                ],
                'atmosphere': "The crystals feed on the life force of those who pass.",
            },
            2: {
                'title': 'The Singing Forest',
                'description': [
                    "Towering crystal formations create natural resonance chambers.",
                    "The harmonics they produce can shatter bone and mind alike.",
                    "Ancient Sith used this place for Force meditation rituals."
                ],
                'atmosphere': "The crystal song threatens to tear your consciousness apart.",
            },
            3: {
                'title': 'Heart of the Garden',
                'description': [
                    "Massive crystal pillars pulse with stolen life energy.",
                    "Thousands of souls are trapped within, fueling dark rituals.",
                    "The air itself feels thick with accumulated suffering."
                ],
                'atmosphere': "You hear the screams of the trapped echoing in every crystal.",
            },
            4: {
                'title': 'The Blood Crystal Throne',
                'description': [
                    "A throne room carved from a single colossal blood crystal.",
                    "This was where a Sith Lord achieved immortality through sacrifice.",
                    "The Soulstone Fragment lies waiting on the throne."
                ],
                'atmosphere': "Power beyond imagination... at a price beyond measure.",
            }
        },
        'description': [
            "A vast cavern filled with towering blood-red crystals.",
            "The crystals hum with dark side energy, casting eerie shadows.",
            "Narrow paths wind between the crystal formations."
        ],
        'atmosphere': [
            "The crystals sing a haunting melody as you pass.",
            "Red light pulses through the crystal formations.",
            "You feel the dark side energy growing stronger here.",
            "Crystal fragments crunch beneath your feet.",
        ],
        'floor_tile': '.',   # Rocky ground
        'wall_tile': '♦',    # Crystal walls
        'special_features': ['crystal_mazes', 'resonance_chambers'],
        'artifact': ArtifactType.SOULSTONE_FRAGMENT,
        'enemies': ['crystal_guardian', 'sith_warrior'],
        'corruption_effect': 'dark_resonance'
    },
    
    DungeonType.SHADOWMAZE: {
        'name': 'The Labyrinth of Shadows',
        'symbol': 'S',
        'size': (27, 27),
        'num_levels': 5,  # Multi-level dungeon - the most complex
        'level_lore': {
            1: {
                'title': 'Penumbral Entrance',
                'description': [
                    "The shadows here are merely thick, not yet alive.",
                    "You can still trust your eyes, mostly.",
                    "The maze begins to show its true nature."
                ],
                'atmosphere': "Your footsteps echo in ways that shouldn't be possible.",
            },
            2: {
                'title': 'Twilight Corridors',
                'description': [
                    "Darkness and light wage eternal war in these halls.",
                    "Shadows detach from their sources, moving with purpose.",
                    "Trust nothing you see in your peripheral vision."
                ],
                'atmosphere': "The shadows whisper lies that sound like truth.",
            },
            3: {
                'title': 'The Umbral Crossroads',
                'description': [
                    "All paths lead nowhere and everywhere simultaneously.",
                    "The maze has consumed so many that their despair lingers.",
                    "Even the shadows are lost here."
                ],
                'atmosphere': "Direction loses meaning. Up might be down. Forward might be back.",
            },
            4: {
                'title': 'Hall of Living Darkness',
                'description': [
                    "The shadows have achieved sentience in this place.",
                    "They hunger for light, for warmth, for life itself.",
                    "Your own shadow may turn against you here."
                ],
                'atmosphere': "The darkness drinks in your light and grows stronger.",
            },
            5: {
                'title': 'The Void Mirror Chamber',
                'description': [
                    "At the maze's heart, a mirror that shows no reflection.",
                    "Instead, it reveals the shadow-self within all beings.",
                    "Here, you must confront what you could become."
                ],
                'atmosphere': "The mirror shows you at your darkest. It looks hungry.",
            }
        },
        'description': [
            "An ever-shifting maze where shadows seem to have a life of their own.",
            "The walls appear to move when you're not looking directly at them.",
            "Darkness clings to everything, defying your light sources."
        ],
        'atmosphere': [
            "Your shadow moves independently for a moment.",
            "The maze walls seem to shift when you're not looking.",
            "Whispers emerge from the darkness ahead.",
            "You catch glimpses of movement in your peripheral vision.",
        ],
        'floor_tile': '▪',   # Shadow floor
        'wall_tile': '█',    # Dense shadow walls
        'special_features': ['shifting_walls', 'shadow_traps'],
        'artifact': ArtifactType.VOID_MIRROR,
        'enemies': ['shadow_stalker', 'maze_phantom'],
        'corruption_effect': 'shadow_touch'
    },
    
    DungeonType.BONE_CATHEDRAL: {
        'name': 'Cathedral of Ancient Bones',
        'symbol': 'B',
        'size': (23, 29),
        'num_levels': 3,
        'level_lore': {
            1: {
                'title': 'Ossuary Entrance',
                'description': [
                    "The outer chambers are piled high with countless bones.",
                    "Each represents a warrior who fell in ancient conflicts.",
                    "Their deaths fuel the dark rituals performed deeper within."
                ],
                'atmosphere': "The dead outnumber the living by millions here.",
            },
            2: {
                'title': 'The Nave of Fallen Legions',
                'description': [
                    "Bone pillars tower overhead, each carved with death songs.",
                    "This cathedral was built by a Sith who conquered armies.",
                    "Every bone is a trophy, every skull a reminder of power."
                ],
                'atmosphere': "You feel the weight of countless deaths pressing down.",
            },
            3: {
                'title': 'The Throne of Bones',
                'description': [
                    "At the cathedral's heart sits a throne of skulls and femurs.",
                    "The Bone Scepter rests here, crafted from a defeated Jedi Master.",
                    "This is where death itself bows to power."
                ],
                'atmosphere': "Even death serves the Sith who commanded this place.",
            }
        },
        'description': [
            "A massive cathedral built entirely from the bones of fallen warriors.",
            "Towering bone pillars support a vaulted ceiling of ribcages.",
            "Skulls embedded in the walls watch your every move."
        ],
        'atmosphere': [
            "The bone walls creak ominously as you pass.",
            "You hear the faint sound of marching feet echoing from nowhere.",
            "Ancient skulls seem to track your movement with empty sockets.",
            "Bone fragments fall from the ceiling like macabre snow.",
        ],
        'floor_tile': '≈',   # Bone debris
        'wall_tile': '╬',    # Bone construction
        'special_features': ['bone_altars', 'skull_sentries'],
        'artifact': ArtifactType.BONE_SCEPTER,
        'enemies': ['bone_wraith', 'skeletal_champion'],
        'corruption_effect': 'necrotic_aura'
    },
    
    DungeonType.ECHO_CHAMBERS: {
        'name': 'Halls of Eternal Echo',
        'symbol': 'E',
        'size': (19, 25),
        'num_levels': 3,
        'level_lore': {
            1: {
                'title': 'The Whispering Gallery',
                'description': [
                    "Soft whispers travel impossible distances here.",
                    "Words spoken centuries ago still bounce between the walls.",
                    "You hear conversations from the living and the dead."
                ],
                'atmosphere': "Every sound you make will echo forever in this place.",
            },
            2: {
                'title': 'The Screaming Halls',
                'description': [
                    "The acoustics here amplify sound to painful levels.",
                    "Ancient torture chambers where screams were weaponized.",
                    "The echoes of past agonies layer upon each other endlessly."
                ],
                'atmosphere': "The accumulated screams of centuries assault your ears.",
            },
            3: {
                'title': 'The Silent Heart',
                'description': [
                    "Paradoxically, the deepest chamber is perfectly silent.",
                    "All echoes converge here and cancel each other out.",
                    "The Echo Crystal floats in absolute silence, containing all sound."
                ],
                'atmosphere': "The silence is so complete it feels like suffocation.",
            }
        },
        'description': [
            "Vast halls where every sound echoes infinitely.",
            "The acoustics are impossible - whispers become roars.",
            "Your footsteps create a cacophony that never fades."
        ],
        'atmosphere': [
            "Your breath echoes back as a scream.",
            "Distant conversations from centuries past overlap with your footsteps.",
            "The sound of your heartbeat reverberates through the halls.",
            "Ancient chants echo from empty chambers.",
        ],
        'floor_tile': '~',   # Resonant floor
        'wall_tile': '║',    # Acoustic walls
        'special_features': ['resonance_chambers', 'sound_traps'],
        'artifact': ArtifactType.ECHO_CRYSTAL,
        'enemies': ['banshee', 'echo_wraith'],
        'corruption_effect': 'sonic_madness'
    },
    
    DungeonType.TWISTED_LIBRARY: {
        'name': 'The Forbidden Archive',
        'symbol': 'L',
        'size': (25, 25),
        'num_levels': 4,
        'level_lore': {
            1: {
                'title': 'The Catalogue of Lesser Sins',
                'description': [
                    "The outer library contains forbidden but relatively safe knowledge.",
                    "Texts on minor Dark Side techniques and forgotten histories.",
                    "Already you feel the temptation to read further."
                ],
                'atmosphere': "Knowledge whispers from every shelf, promising power.",
            },
            2: {
                'title': 'The Stacks of Dangerous Truths',
                'description': [
                    "Deeper in, the books become more aggressive.",
                    "Some texts actually attack readers who aren't ready for their secrets.",
                    "The geometry of the shelves becomes impossible to navigate."
                ],
                'atmosphere': "The library doesn't want you to leave. There's always one more book.",
            },
            3: {
                'title': 'The Chamber of Forbidden Names',
                'description': [
                    "Here lie the true names of ancient Sith Lords and dark entities.",
                    "To speak these names is to invoke their power across time itself.",
                    "The knowledge here can shatter minds unprepared for its weight."
                ],
                'atmosphere': "You understand why some knowledge should remain buried.",
            },
            4: {
                'title': 'The Crimson Codex Vault',
                'description': [
                    "At the archive's heart sits the Codex that writes itself.",
                    "It contains every dark secret ever conceived.",
                    "Reading it grants ultimate knowledge at the cost of ultimate corruption."
                ],
                'atmosphere': "The Codex knows your darkest thoughts before you think them.",
            }
        },
        'description': [
            "A vast library of forbidden knowledge with impossible geometry.",
            "Shelves stretch infinitely upward, defying architectural logic.",
            "Books whisper secrets as you pass, their pages rustling without wind."
        ],
        'atmosphere': [
            "A book falls open, revealing text that hurts to read.",
            "You hear the sound of pages turning in empty rooms.",
            "Ink bleeds from the walls, forming forbidden symbols.",
            "Whispered secrets fill the air, tempting you to listen.",
        ],
        'floor_tile': '▫',   # Parchment floor
        'wall_tile': '▤',    # Bookshelf walls
        'special_features': ['knowledge_traps', 'text_mazes'],
        'artifact': ArtifactType.CRIMSON_CODEX,
        'enemies': ['knowledge_seeker', 'text_phantom'],
        'corruption_effect': 'forbidden_knowledge'
    },
    
    DungeonType.PAIN_FORGE: {
        'name': 'Forge of Eternal Torment',
        'symbol': 'F',
        'size': (21, 23),
        'num_levels': 3,
        'level_lore': {
            1: {
                'title': 'The Preparation Chambers',
                'description': [
                    "Where victims were brought to understand their fate.",
                    "Chains and manacles line every wall.",
                    "Fear was cultivated here before being harvested below."
                ],
                'atmosphere': "The walls remember every scream that echoed here.",
            },
            2: {
                'title': 'The Torture Forges',
                'description': [
                    "Active forges where pain was transformed into dark power.",
                    "Anvils stained with centuries of blood still glow faintly.",
                    "This is where the Sith learned to smith with suffering."
                ],
                'atmosphere': "The heat comes not from fire but from accumulated agony.",
            },
            3: {
                'title': 'The Crown Chamber',
                'description': [
                    "The forge master's throne room, where the greatest works were made.",
                    "The Torment Crown sits here, forged from the pain of thousands.",
                    "Wearing it grants power over suffering itself."
                ],
                'atmosphere': "You feel the weight of every tortured soul that powered this place.",
            }
        },
        'description': [
            "An ancient forge where suffering was weaponized into dark artifacts.",
            "Chains hang from the ceiling, still warm with residual anguish.",
            "The air itself seems to burn with concentrated pain."
        ],
        'atmosphere': [
            "The phantom scent of burning metal fills your nostrils.",
            "Chains rattle without wind, carrying echoes of torment.",
            "Heat radiates from cold stone, fueled by ancient suffering.",
            "You hear the distant sound of hammers striking in empty chambers.",
        ],
        'floor_tile': '▓',   # Forge floor
        'wall_tile': '▣',    # Metal-reinforced stone
        'special_features': ['torment_anvils', 'pain_conduits'],
        'artifact': ArtifactType.TORMENT_CROWN,
        'enemies': ['pain_wraith', 'forge_guardian'],
        'corruption_effect': 'anguish_aura'
    },
    
    DungeonType.DREAM_NEXUS: {
        'name': 'Nexus of Shattered Dreams',
        'symbol': 'Ӿ',
        'size': (23, 21),
        'num_levels': 4,
        'level_lore': {
            1: {
                'title': 'The Drowsy Threshold',
                'description': [
                    "The boundary between waking and sleeping grows thin.",
                    "You're not sure if you're awake or dreaming anymore.",
                    "Pleasant dreams mix with the first hints of nightmare."
                ],
                'atmosphere': "Is this real? Were you always here? Will you wake up?",
            },
            2: {
                'title': 'The Shifting Dreamscape',
                'description': [
                    "Reality becomes fluid and malleable here.",
                    "The dreams of countless beings overlap and merge.",
                    "You see your own dreams walking past as physical entities."
                ],
                'atmosphere': "Your thoughts become real before you can stop them.",
            },
            3: {
                'title': 'The Nightmare Deeps',
                'description': [
                    "Where pleasant dreams die and nightmares are born.",
                    "Every fear you've ever had takes form and stalks you.",
                    "The deeper you go, the harder it becomes to remember waking."
                ],
                'atmosphere': "You're not sure you want to wake up. Or if you even can.",
            },
            4: {
                'title': 'The Heart of Sleeping Madness',
                'description': [
                    "At the center, the Nightmare Orb pulses with captured dreams.",
                    "It contains the nightmares of an entire civilization.",
                    "To touch it is to risk never waking again."
                ],
                'atmosphere': "The Orb dreams of you as you dream of it. Which is real?",
            }
        },
        'description': [
            "A surreal space where dreams and nightmares take physical form.",
            "Reality bends and shifts like a lucid dream gone wrong.",
            "Impossible colors paint walls that shouldn't exist."
        ],
        'atmosphere': [
            "You remember a dream you never had.",
            "The ground beneath you feels like sleeping thoughts.",
            "Nightmare creatures flicker at the edge of your vision.",
            "Time moves strangely here, like REM sleep.",
        ],
        'floor_tile': '∞',   # Dream floor
        'wall_tile': '≋',    # Fluid dream walls
        'special_features': ['dream_pools', 'nightmare_gates'],
        'artifact': ArtifactType.NIGHTMARE_ORB,
        'enemies': ['dream_stalker', 'nightmare_herald'],
        'corruption_effect': 'dream_sickness'
    }
}

# Artifact Definitions
ARTIFACTS = {
    ArtifactType.HOLOCRON_OF_WHISPERS: {
        'name': 'Holocron of Whispers',
        'description': [
            "A crystalline holocron that whispers secrets of the past.",
            "The voices of ancient Sith Lords echo from within its faceted surface.",
            "It pulses with psychic energy, promising forbidden knowledge."
        ],
        'power_level': 'legendary',
        'effects': {
            'absorb': {
                'corruption_gain': 25,
                'psychic_power': True,
                'mind_read_ability': True,
                'description': "You absorb the holocron's whispers, gaining terrifying insight into others' thoughts."
            },
            'destroy': {
                'corruption_loss': 15,
                'mental_clarity': True,
                'willpower_boost': 10,
                'description': "You shatter the holocron, silencing the whispers and clearing your mind."
            }
        }
    },
    
    ArtifactType.SOULSTONE_FRAGMENT: {
        'name': 'Crimson Soulstone Fragment',
        'description': [
            "A shard of a greater soulstone, still pulsing with trapped life energy.",
            "Faces of the tormented appear within its crimson depths.",
            "It hungers to absorb more souls to become whole again."
        ],
        'power_level': 'artifact',
        'effects': {
            'absorb': {
                'corruption_gain': 30,
                'life_drain_ability': True,
                'max_hp_boost': 20,
                'description': "You merge with the fragment, gaining the ability to drain life from your enemies."
            },
            'destroy': {
                'corruption_loss': 20,
                'soul_freedom': True,
                'karma_boost': 15,
                'description': "You shatter the fragment, freeing the trapped souls within."
            }
        }
    },
    
    ArtifactType.CRIMSON_CODEX: {
        'name': 'The Crimson Codex',
        'description': [
            "A tome bound in red leather that writes itself with blood.",
            "New entries appear as you watch, documenting your darkest thoughts.",
            "The knowledge within could remake the galaxy... or destroy it."
        ],
        'power_level': 'legendary',
        'effects': {
            'absorb': {
                'corruption_gain': 35,
                'forbidden_knowledge': True,
                'force_mastery': True,
                'description': "You absorb the Codex's knowledge, understanding the deepest secrets of the Force."
            },
            'destroy': {
                'corruption_loss': 25,
                'knowledge_purge': True,
                'wisdom_boost': 15,
                'description': "You burn the Codex, choosing wisdom over power."
            }
        }
    },
    
    ArtifactType.VOID_MIRROR: {
        'name': 'Mirror of the Void',
        'description': [
            "A black mirror that shows not your reflection, but your shadow self.",
            "In its depths, you see what you could become if you embraced darkness.",
            "It whispers of power beyond imagination."
        ],
        'power_level': 'artifact',
        'effects': {
            'absorb': {
                'corruption_gain': 28,
                'shadow_mastery': True,
                'stealth_bonus': 20,
                'description': "You embrace your shadow self, gaining mastery over darkness and deception."
            },
            'destroy': {
                'corruption_loss': 18,
                'self_acceptance': True,
                'inner_peace': True,
                'description': "You shatter the mirror, rejecting the temptation of your darker nature."
            }
        }
    },
    
    ArtifactType.TORMENT_CROWN: {
        'name': 'Crown of Eternal Torment',
        'description': [
            "A crown forged from suffering itself, twisted metal and crystallized pain.",
            "Those who wear it gain power through the agony of others.",
            "It throbs with the accumulated anguish of millennia."
        ],
        'power_level': 'legendary',
        'effects': {
            'absorb': {
                'corruption_gain': 40,
                'pain_mastery': True,
                'torture_expertise': True,
                'description': "You don the crown, becoming a conduit for suffering and pain."
            },
            'destroy': {
                'corruption_loss': 30,
                'compassion_awakening': True,
                'healing_power': True,
                'description': "You destroy the crown, transforming its pain into healing power."
            }
        }
    },
    
    ArtifactType.ECHO_CRYSTAL: {
        'name': 'Crystal of Infinite Echo',
        'description': [
            "A resonant crystal that captures and amplifies the last words of the dying.",
            "Voices of the past speak through its faceted surface.",
            "It could grant power over sound and memory."
        ],
        'power_level': 'artifact',
        'effects': {
            'absorb': {
                'corruption_gain': 22,
                'sonic_powers': True,
                'memory_manipulation': True,
                'description': "You absorb the crystal, gaining power over sound and the memories of others."
            },
            'destroy': {
                'corruption_loss': 12,
                'voice_of_peace': True,
                'calming_presence': True,
                'description': "You silence the crystal, bringing peace to the trapped voices."
            }
        }
    },
    
    ArtifactType.NIGHTMARE_ORB: {
        'name': 'Orb of Living Nightmares',
        'description': [
            "A sphere of crystallized fear that shows your worst nightmares.",
            "Within its swirling depths, all your terrors take shape.",
            "It offers power over dreams and the fears of others."
        ],
        'power_level': 'legendary',
        'effects': {
            'absorb': {
                'corruption_gain': 32,
                'fear_mastery': True,
                'nightmare_projection': True,
                'description': "You absorb the orb, becoming a living nightmare that can terrorize enemies."
            },
            'destroy': {
                'corruption_loss': 22,
                'fearlessness': True,
                'courage_inspiration': True,
                'description': "You destroy the orb, conquering your fears and gaining unshakeable courage."
            }
        }
    },
    
    ArtifactType.BONE_SCEPTER: {
        'name': 'Scepter of the Bone Throne',
        'description': [
            "A scepter carved from the spine of an ancient dragon.",
            "It commands the loyalty of the undead and grants dominion over death.",
            "Necromantic power flows through its calcified length."
        ],
        'power_level': 'artifact',
        'effects': {
            'absorb': {
                'corruption_gain': 26,
                'necromancy': True,
                'undead_command': True,
                'description': "You claim the scepter, gaining power over death and the undead."
            },
            'destroy': {
                'corruption_loss': 16,
                'death_resistance': True,
                'life_affinity': True,
                'description': "You destroy the scepter, gaining resistance to death magic and affinity for life."
            }
        }
    }
}


def generate_special_dungeon(dungeon_type: DungeonType):
    """Generate a complete special dungeon layout."""
    template = DUNGEON_TEMPLATES[dungeon_type]
    width, height = template['size']
    
    # Initialize with walls
    layout = [[template['wall_tile'] for _ in range(width)] for _ in range(height)]
    
    # Generate based on dungeon type
    if dungeon_type == DungeonType.MEMORY_VAULT:
        layout = _generate_memory_vault(layout, template)
    elif dungeon_type == DungeonType.CRYSTAL_GARDEN:
        layout = _generate_crystal_garden(layout, template)
    elif dungeon_type == DungeonType.SHADOWMAZE:
        layout = _generate_shadowmaze(layout, template)
    elif dungeon_type == DungeonType.BONE_CATHEDRAL:
        layout = _generate_bone_cathedral(layout, template)
    elif dungeon_type == DungeonType.ECHO_CHAMBERS:
        layout = _generate_echo_chambers(layout, template)
    elif dungeon_type == DungeonType.TWISTED_LIBRARY:
        layout = _generate_twisted_library(layout, template)
    elif dungeon_type == DungeonType.PAIN_FORGE:
        layout = _generate_pain_forge(layout, template)
    elif dungeon_type == DungeonType.DREAM_NEXUS:
        layout = _generate_dream_nexus(layout, template)
    
    # Find entrance and artifact positions
    entrance_pos = _find_entrance_position(layout, template)
    artifact_pos = _find_artifact_position(layout, template)

    # Place stairs: entrance gets STAIRS_UP, artifact gets STAIRS_DOWN
    from jedi_fugitive.game.level import Display as MainDisplay
    ex, ey = entrance_pos
    ax, ay = artifact_pos
    layout[ey][ex] = getattr(MainDisplay, 'STAIRS_UP', '<')
    layout[ay][ax] = getattr(MainDisplay, 'STAIRS_DOWN', '>')

    return layout, entrance_pos, artifact_pos, template['artifact']


def _generate_memory_vault(layout, template):
    """Generate crystalline chambers with memory pools."""
    height, width = len(layout), len(layout[0])
    floor = template['floor_tile']
    
    # Create central chamber
    for y in range(height // 3, 2 * height // 3):
        for x in range(width // 3, 2 * width // 3):
            layout[y][x] = floor
    
    # Create memory pool alcoves
    for i in range(4):
        alcove_x = width // 4 + (i % 2) * (width // 2)
        alcove_y = height // 4 + (i // 2) * (height // 2)
        
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if 0 <= alcove_y + dy < height and 0 <= alcove_x + dx < width:
                    if abs(dx) + abs(dy) <= 2:
                        layout[alcove_y + dy][alcove_x + dx] = floor
    
    # Create connecting corridors
    _create_corridor(layout, width // 2, height // 4, width // 2, 3 * height // 4, floor)
    _create_corridor(layout, width // 4, height // 2, 3 * width // 4, height // 2, floor)
    
    return layout


def _generate_crystal_garden(layout, template):
    """Generate winding paths through crystal formations."""
    height, width = len(layout), len(layout[0])
    floor = template['floor_tile']
    
    # Create main path
    current_x, current_y = width // 2, height - 2
    layout[current_y][current_x] = floor
    
    # Wind through the garden
    directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    current_dir = 0
    
    for _ in range(width * height // 4):
        # Change direction occasionally
        if random.random() < 0.3:
            current_dir = (current_dir + random.choice([-1, 1])) % 4
        
        dx, dy = directions[current_dir]
        new_x, new_y = current_x + dx, current_y + dy
        
        if (0 < new_x < width - 1 and 0 < new_y < height - 1):
            layout[new_y][new_x] = floor
            current_x, current_y = new_x, new_y
            
            # Create small side chambers
            if random.random() < 0.2:
                for side_dx in range(-1, 2):
                    for side_dy in range(-1, 2):
                        side_x, side_y = current_x + side_dx, current_y + side_dy
                        if (0 < side_x < width - 1 and 0 < side_y < height - 1):
                            layout[side_y][side_x] = floor
    
    return layout


def _generate_shadowmaze(layout, template):
    """Generate a complex shifting maze."""
    height, width = len(layout), len(layout[0])
    floor = template['floor_tile']
    
    # Start with a grid pattern
    for y in range(1, height - 1, 2):
        for x in range(1, width - 1, 2):
            layout[y][x] = floor
    
    # Create maze connections
    for y in range(1, height - 1, 2):
        for x in range(1, width - 1, 2):
            # Randomly connect to adjacent cells
            directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
            random.shuffle(directions)
            
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                wall_x, wall_y = x + dx // 2, y + dy // 2
                
                if (0 < new_x < width - 1 and 0 < new_y < height - 1 and
                    random.random() < 0.6):
                    layout[wall_y][wall_x] = floor
    
    return layout


def _generate_bone_cathedral(layout, template):
    """Generate cathedral-like structure with bone pillars."""
    height, width = len(layout), len(layout[0])
    floor = template['floor_tile']
    
    # Create nave (main hall)
    for y in range(2, height - 2):
        for x in range(width // 3, 2 * width // 3):
            layout[y][x] = floor
    
    # Create transept (cross section)
    for y in range(height // 3, 2 * height // 3):
        for x in range(2, width - 2):
            layout[y][x] = floor
    
    # Create apse (altar area)
    apse_center_x, apse_center_y = width // 2, 3
    for y in range(apse_center_y - 2, apse_center_y + 3):
        for x in range(apse_center_x - 3, apse_center_x + 4):
            if 0 <= y < height and 0 <= x < width:
                if (x - apse_center_x) ** 2 + (y - apse_center_y) ** 2 <= 9:
                    layout[y][x] = floor
    
    # Add bone pillars (keep as walls for structure)
    for i in range(4):
        pillar_x = width // 4 + (i % 2) * (width // 2)
        pillar_y = height // 4 + (i // 2) * (height // 2)
        if layout[pillar_y][pillar_x] == floor:
            layout[pillar_y][pillar_x] = '†'  # Bone pillar marker
    
    return layout


def _generate_echo_chambers(layout, template):
    """Generate resonant chambers with acoustic properties."""
    height, width = len(layout), len(layout[0])
    floor = template['floor_tile']
    
    # Create circular chambers
    chambers = [
        (width // 4, height // 4, 3),
        (3 * width // 4, height // 4, 4),
        (width // 2, height // 2, 5),
        (width // 4, 3 * height // 4, 3),
        (3 * width // 4, 3 * height // 4, 4)
    ]
    
    for cx, cy, radius in chambers:
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                if (0 <= y < height and 0 <= x < width and
                    (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2):
                    layout[y][x] = floor
    
    # Connect chambers with corridors
    _create_corridor(layout, width // 4, height // 4, 3 * width // 4, height // 4, floor)
    _create_corridor(layout, width // 2, height // 4, width // 2, 3 * height // 4, floor)
    _create_corridor(layout, width // 4, 3 * height // 4, 3 * width // 4, 3 * height // 4, floor)
    
    return layout


def _generate_twisted_library(layout, template):
    """Generate library with impossible geometry."""
    height, width = len(layout), len(layout[0])
    floor = template['floor_tile']
    
    # Create reading rooms in a grid
    for room_y in range(3):
        for room_x in range(3):
            start_x = 2 + room_x * (width // 3)
            start_y = 2 + room_y * (height // 3)
            end_x = start_x + width // 4
            end_y = start_y + height // 4
            
            for y in range(start_y, min(end_y, height - 1)):
                for x in range(start_x, min(end_x, width - 1)):
                    layout[y][x] = floor
    
    # Create connecting corridors in a cross pattern
    _create_corridor(layout, width // 2, 1, width // 2, height - 2, floor)
    _create_corridor(layout, 1, height // 2, width - 2, height // 2, floor)
    
    # Add some alcoves for books
    for i in range(6):
        alcove_x = random.randint(1, width - 3)
        alcove_y = random.randint(1, height - 3)
        if layout[alcove_y][alcove_x] == template['wall_tile']:
            layout[alcove_y][alcove_x] = floor
    
    return layout


def _generate_pain_forge(layout, template):
    """Generate forge with torture chambers."""
    height, width = len(layout), len(layout[0])
    floor = template['floor_tile']
    
    # Main forge chamber (central)
    for y in range(height // 3, 2 * height // 3):
        for x in range(width // 3, 2 * width // 3):
            layout[y][x] = floor
    
    # Torture chambers around the perimeter
    torture_rooms = [
        (width // 6, height // 6, width // 4, height // 4),
        (5 * width // 6 - width // 4, height // 6, width // 4, height // 4),
        (width // 6, 5 * height // 6 - height // 4, width // 4, height // 4),
        (5 * width // 6 - width // 4, 5 * height // 6 - height // 4, width // 4, height // 4)
    ]
    
    for start_x, start_y, room_width, room_height in torture_rooms:
        for y in range(start_y, start_y + room_height):
            for x in range(start_x, start_x + room_width):
                if 0 <= y < height and 0 <= x < width:
                    layout[y][x] = floor
        
        # Connect to main chamber
        _create_corridor(layout, start_x + room_width // 2, start_y + room_height // 2,
                        width // 2, height // 2, floor)
    
    return layout


def _generate_dream_nexus(layout, template):
    """Generate surreal dream-like structure."""
    height, width = len(layout), len(layout[0])
    floor = template['floor_tile']
    
    # Create organic, flowing chambers
    center_x, center_y = width // 2, height // 2
    
    # Spiral outward from center
    current_x, current_y = center_x, center_y
    angle = 0
    radius = 1
    
    for step in range(width * height // 6):
        # Calculate spiral position
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        
        if 0 < x < width - 1 and 0 < y < height - 1:
            # Create flowing chamber
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    if (0 < x + dx < width - 1 and 0 < y + dy < height - 1 and
                        abs(dx) + abs(dy) <= 2):
                        layout[y + dy][x + dx] = floor
        
        # Update spiral parameters
        angle += 0.3
        radius += 0.1
        
        if radius > min(width, height) // 3:
            radius = 1
            angle += 1
    
    return layout


def _create_corridor(layout, x1, y1, x2, y2, floor_tile):
    """Create a corridor between two points."""
    height, width = len(layout), len(layout[0])
    
    # L-shaped corridor
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 < x < width - 1 and 0 < y1 < height - 1:
            layout[y1][x] = floor_tile
    
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 < x2 < width - 1 and 0 < y < height - 1:
            layout[y][x2] = floor_tile


def _find_entrance_position(layout, template):
    """Find suitable entrance position (usually bottom center)."""
    height, width = len(layout), len(layout[0])
    floor = template['floor_tile']
    
    # Look for floor tiles near the bottom
    for y in range(height - 1, height - 5, -1):
        for x in range(width // 2 - 2, width // 2 + 3):
            if 0 <= y < height and 0 <= x < width and layout[y][x] == floor:
                return (x, y)
    
    # Fallback: create entrance at bottom center
    entrance_x, entrance_y = width // 2, height - 2
    layout[entrance_y][entrance_x] = floor
    return (entrance_x, entrance_y)


def _find_artifact_position(layout, template):
    """Find suitable position for artifact (usually deepest/most central)."""
    height, width = len(layout), len(layout[0])
    floor = template['floor_tile']
    
    # Look for floor tiles in the center area
    for y in range(height // 3, 2 * height // 3):
        for x in range(width // 3, 2 * width // 3):
            if layout[y][x] == floor:
                return (x, y)
    
    # Fallback: any floor tile
    for y in range(height):
        for x in range(width):
            if layout[y][x] == floor:
                return (x, y)
    
    return (width // 2, height // 2)


def get_random_dungeon_type():
    """Get a random dungeon type for spawning."""
    return random.choice(list(DungeonType))


def get_dungeon_atmosphere_message(dungeon_type: DungeonType):
    """Get a random atmosphere message for the dungeon."""
    template = DUNGEON_TEMPLATES[dungeon_type]
    return random.choice(template['atmosphere'])


def get_artifact_by_type(artifact_type: ArtifactType):
    """Get artifact data by type."""
    return ARTIFACTS[artifact_type]