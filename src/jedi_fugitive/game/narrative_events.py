"""
Dynamic Narrative Events system for Jedi Fugitive.
Random discoveries, holocron messages, distress signals, and environmental storytelling.
"""
import random

# Survivor journals - found scattered across the map
SURVIVOR_JOURNALS = [
    {
        'title': 'Jedi Padawan Journal',
        'author': 'Padawan Kira Voss',
        'entries': [
            "Day 47: Master Jorin is dead. The Sith came in the night.",
            "I managed to escape into the wilderness. I'm alone now.",
            "The Force feels... different here. Darker. Am I falling?",
            "I found a cave. It's cold, but it's shelter. For now.",
        ],
        'corruption_effect': 0,
        'discovery_message': "You find a tattered journal, its pages stained with dirt and moisture."
    },
    {
        'title': 'Republic Soldier Log',
        'author': 'Captain Dane Korr',
        'entries': [
            "Ship went down over uncharted territory. Most crew didn't make it.",
            "We're being hunted. Something out there... not human.",
            "Found ruins. Old Sith tombs maybe. Jenkins went inside. Came back different.",
            "Last entry: If you find this, don't follow us into the tombs.",
        ],
        'corruption_effect': -5,
        'discovery_message': "A military logbook lies wedged between rocks, weathered but readable."
    },
    {
        'title': 'Dark Side Cultist Diary',
        'author': 'Acolyte Zash',
        'entries': [
            "The power here is intoxicating. I can feel it coursing through me.",
            "The Master says I'm progressing quickly. Too quickly, perhaps.",
            "I don't care what the cost is anymore. I WILL have this power.",
            "The others fear me now. Good. Fear is the beginning of respect.",
        ],
        'corruption_effect': 10,
        'discovery_message': "A leather-bound diary, its pages crackling with residual dark energy."
    },
    {
        'title': 'Jedi Master Notes',
        'author': 'Master Ven Torra',
        'entries': [
            "I came here seeking the source of the darkness. I found it.",
            "Ancient Sith Lords are entombed here. Their presence corrupts everything.",
            "I've sealed three tombs, but there are more. Too many.",
            "To whoever reads this: You cannot destroy them. Only contain them.",
        ],
        'corruption_effect': -8,
        'discovery_message': "Carefully preserved notes written in the elegant script of a Jedi Master."
    },
    {
        'title': 'Smuggler Captain Log',
        'author': 'Captain Rax Vane',
        'entries': [
            "This job was supposed to be easy. Find artifacts, sell them, retire rich.",
            "Half my crew is dead. The other half has gone mad from the Force echoes.",
            "Whatever's in those tombs, it's worth more than money. But I'm done.",
            "I'm leaving the planet. If I make it out, I'm never dealing with Force stuff again.",
        ],
        'corruption_effect': 0,
        'discovery_message': "A datapad with a captain's log, its screen cracked but still functional."
    },
    {
        'title': 'Researcher Field Notes',
        'author': 'Dr. Saresh Lann',
        'entries': [
            "This planet is a nexus of Force energy. Both light and dark converge here.",
            "The ruins predate the Galactic Republic by millennia. Rakata? Sith?",
            "My instruments can't explain the energy readings. They fluctuate with emotion.",
            "Final note: Leaving before I become part of the research. Some things shouldn't be studied.",
        ],
        'corruption_effect': 0,
        'discovery_message': "Scientific field notes in a weatherproof case, meticulously detailed."
    }
]

# Holocron messages - Force echoes from long-dead Jedi/Sith
HOLOCRON_MESSAGES = {
    'light_side': [
        {
            'speaker': 'Jedi Master Satele Shan',
            'message': [
                "If you're hearing this, the Order has fallen. I foresaw this possibility.",
                "Remember: The Force is not a weapon. It is a guide, a companion.",
                "Dark times lie ahead, but do not lose hope. The light will endure.",
                "Trust in the Force, and trust in yourself. You are not alone.",
            ],
            'corruption_effect': -12,
            'force_wisdom': True
        },
        {
            'speaker': 'Jedi Knight Revan (Redeemed)',
            'message': [
                "I walked both paths - light and dark. I know their costs.",
                "The dark side offers power, but it is a hollow victory.",
                "Every time you choose darkness, you lose a piece of yourself.",
                "There is always a way back. Always. No matter how far you've fallen.",
            ],
            'corruption_effect': -15,
            'force_wisdom': True
        },
        {
            'speaker': 'Master Yoda',
            'message': [
                "Difficult to see, the future is. Always in motion.",
                "Fear leads to anger. Anger leads to hate. Hate leads to suffering.",
                "Wars not make one great. Peace, knowledge, serenity - these are the Jedi way.",
                "The greatest teacher, failure is. Learn from it, you must.",
            ],
            'corruption_effect': -10,
            'force_wisdom': True
        },
    ],
    'dark_side': [
        {
            'speaker': 'Darth Revan (Sith Lord)',
            'message': [
                "Power. True power comes from embracing what you are.",
                "The Jedi teach weakness disguised as virtue. Reject their lies.",
                "Your anger, your hatred - these are tools. Wield them without apology.",
                "The strong rule. The weak serve. Which will you be?",
            ],
            'corruption_effect': 18,
            'force_wisdom': True
        },
        {
            'speaker': 'Darth Bane',
            'message': [
                "Two there should be. No more, no less. One to embody power, the other to crave it.",
                "Betrayal is the way of the Sith. Embrace it or become its victim.",
                "Every moment of peace is wasted. Train. Grow stronger. Or die.",
                "The dark side serves those strong enough to master it. Are you strong enough?",
            ],
            'corruption_effect': 20,
            'force_wisdom': True
        },
        {
            'speaker': 'Darth Traya',
            'message': [
                "The Force binds us, controls us, uses us. Are we truly free?",
                "Light and dark are both prisons. True power lies in independence.",
                "Every choice you make echoes across the galaxy. Choose wisely - or boldly.",
                "Perhaps the greatest wisdom is knowing when to let go of wisdom itself.",
            ],
            'corruption_effect': 5,
            'force_wisdom': True
        },
    ],
    'neutral': [
        {
            'speaker': 'Gray Jedi Jolee Bindo',
            'message': [
                "The Jedi say 'no emotion.' The Sith say 'embrace it.' Both are fools.",
                "I've lived 300 years. Know what I learned? Balance, not extremes.",
                "The Force doesn't care about your philosophy. It just is.",
                "Do what you think is right. But think carefully about what 'right' means.",
            ],
            'corruption_effect': 0,
            'force_wisdom': True
        },
        {
            'speaker': 'The Exile (Meetra Surik)',
            'message': [
                "I severed my connection to the Force. Then rebuilt it. Changed by both.",
                "You don't need the Force to be strong. But it helps to understand it.",
                "Every person you meet, every choice you make, shapes who you become.",
                "The Force will always be there. The question is: what will you do with it?",
            ],
            'corruption_effect': 0,
            'force_wisdom': True
        },
    ]
}

# Distress signals - lead to moral dilemmas
DISTRESS_SIGNALS = [
    {
        'signal_type': 'emergency_beacon',
        'transmission': "This is transport vessel Starlight. Under attack. Requesting immediate assistance!",
        'location_description': "Following the beacon leads you to crash wreckage. Smoke still rises from the ruins.",
        'scenario': {
            'description': [
                "You arrive to find the wreckage of a small transport.",
                "Scavengers are picking through the debris, ignoring the bodies.",
                "One survivor crawls from the wreckage, badly wounded.",
                "The scavengers notice you. They draw weapons.",
            ],
            'choice_light': {
                'text': "Defend the survivor and drive off the scavengers (Light)",
                'outcome': "You protect the wounded survivor. The scavengers flee. You tend to their injuries with what supplies you have.",
                'corruption': -8,
                'reward': 'survivor_gratitude'
            },
            'choice_dark': {
                'text': "Kill the scavengers and take everything (Dark)",
                'outcome': "You strike without mercy. The scavengers and the survivor all die. Their supplies are yours.",
                'corruption': 20,
                'reward': 'scavenger_loot'
            },
            'choice_ignore': {
                'text': "Leave - this isn't your problem (Neutral)",
                'outcome': "You turn away. The screams fade behind you. Survival requires hard choices.",
                'corruption': 5,
                'reward': None
            }
        }
    },
    {
        'signal_type': 'automated_warning',
        'transmission': "WARNING: Quarantine zone. Rakghoul infection detected. Do not approach.",
        'location_description': "The signal comes from a sealed medical facility, its doors barricaded.",
        'scenario': {
            'description': [
                "Through the facility's viewport, you see dozens of infected creatures.",
                "Among them, a handful of survivors huddle in a sealed room.",
                "They've spotted you. They're begging for help through the glass.",
                "The facility's power is failing. The seals won't hold much longer.",
            ],
            'choice_light': {
                'text': "Risk infection to save the survivors (Light)",
                'outcome': "You fight through the infected, rescue the survivors. One becomes infected during the escape. A calculated risk.",
                'corruption': -10,
                'reward': 'medical_supplies'
            },
            'choice_dark': {
                'text': "Seal the facility permanently, ending the threat (Dark)",
                'outcome': "You override the doors, sealing everyone inside. Infected and survivors alike. The threat is contained. Screams echo, then silence.",
                'corruption': 25,
                'reward': 'security_codes'
            },
            'choice_ignore': {
                'text': "Walk away - they're already dead (Neutral)",
                'outcome': "You leave them to their fate. Sometimes there are no good choices.",
                'corruption': 8,
                'reward': None
            }
        }
    },
    {
        'signal_type': 'jedi_beacon',
        'transmission': "Emergency Jedi frequency. Temple destroyed. Rally point compromised. This may be my last transmission.",
        'location_description': "The signal leads to an ancient meditation circle. Someone is meditating there.",
        'scenario': {
            'description': [
                "A lone Jedi sits in meditation, surrounded by battle damage.",
                "Bodies of Sith assassins lie nearby. The Jedi is gravely wounded.",
                "They sense your presence. 'Another survivor. Or another hunter?'",
                "You sense their distrust. They're on the edge of the dark side.",
            ],
            'choice_light': {
                'text': "Offer help and guidance back to the light (Light)",
                'outcome': "You spend hours in meditation with them, sharing your burden. Together you find peace. They join you as a temporary companion.",
                'corruption': -12,
                'reward': 'jedi_ally'
            },
            'choice_dark': {
                'text': "Finish what the assassins started (Dark)",
                'outcome': "They're weak, broken. You end their suffering - and take their lightsaber crystal. The strong survive.",
                'corruption': 22,
                'reward': 'lightsaber_crystal'
            },
            'choice_ignore': {
                'text': "Leave them to their fate (Neutral)",
                'outcome': "You depart without a word. Everyone must choose their own path.",
                'corruption': 3,
                'reward': None
            }
        }
    },
    {
        'signal_type': 'sith_lure',
        'transmission': "Power... knowledge... secrets of the ancient Sith await those brave enough to claim them...",
        'location_description': "The signal emanates from a dark cave entrance carved with Sith runes.",
        'scenario': {
            'description': [
                "The cave pulses with dark side energy. It's clearly a trap.",
                "But you also sense genuine Sith artifacts inside. Ancient knowledge.",
                "A Sith spirit guards the entrance. 'Enter if you dare, Jedi.'",
                "This is a test. Pass, and power is yours. Fail, and you join the dead.",
            ],
            'choice_light': {
                'text': "Refuse the trap and seal the cave (Light)",
                'outcome': "You use the Force to collapse the cave entrance. The Sith spirit shrieks in rage, then fades. The artifacts are buried forever.",
                'corruption': -15,
                'reward': 'force_wisdom'
            },
            'choice_dark': {
                'text': "Accept the challenge and claim the power (Dark)",
                'outcome': "You enter and face the spirit in combat. Victorious, you claim the Sith artifacts. Power flows through you.",
                'corruption': 30,
                'reward': 'sith_artifacts'
            },
            'choice_ignore': {
                'text': "Ignore the trap entirely (Neutral)",
                'outcome': "You mark the location and move on. Perhaps you'll return when stronger.",
                'corruption': 0,
                'reward': 'cave_location'
            }
        }
    }
]

# Random environmental discoveries
ENVIRONMENTAL_EVENTS = [
    {
        'name': 'Ancient Battlefield',
        'description': [
            "You stumble upon an ancient battlefield. Lightsabers and armor lie half-buried.",
            "Thousands died here in some long-forgotten war between Jedi and Sith.",
            "The Force echoes with their final moments - rage, fear, determination.",
            "Do you absorb these echoes, or let the dead rest in peace?",
        ],
        'choices': {
            'meditate': {
                'text': "Meditate and honor the fallen (Light)",
                'corruption': -6,
                'reward': 'force_insight'
            },
            'absorb': {
                'text': "Absorb the residual Force energy (Dark)",
                'corruption': 12,
                'reward': 'force_power'
            }
        }
    },
    {
        'name': 'Crashed Starship',
        'description': [
            "A starship lies half-buried in the ground. Republic design, but ancient.",
            "The distress beacon is still transmitting after all these centuries.",
            "Inside, you find the crew - skeletal remains at their stations.",
            "The ship's computer core might still contain valuable data.",
        ],
        'choices': {
            'data': {
                'text': "Access the ship's computer",
                'corruption': 0,
                'reward': 'navigation_data'
            },
            'salvage': {
                'text': "Salvage the ship for parts",
                'corruption': 2,
                'reward': 'ship_parts'
            }
        }
    },
    {
        'name': 'Force Nexus',
        'description': [
            "You've discovered a Force nexus - a place where the Force converges powerfully.",
            "The air shimmers. Time seems to flow differently here.",
            "This place could amplify your abilities... or expose your inner darkness.",
            "Many have sought such places. Few left unchanged.",
        ],
        'choices': {
            'meditate': {
                'text': "Meditate at the nexus",
                'corruption': 0,  # Varies based on player alignment
                'reward': 'force_vision'
            },
            'leave': {
                'text': "Leave this place undisturbed",
                'corruption': 0,
                'reward': None
            }
        }
    }
]

def get_random_journal():
    """Get a random survivor journal."""
    return random.choice(SURVIVOR_JOURNALS)

def get_holocron_message(corruption_level):
    """Get a holocron message appropriate for player's corruption level."""
    if corruption_level <= 35:
        # Light side player gets light side holocrons
        return random.choice(HOLOCRON_MESSAGES['light_side'])
    elif corruption_level <= 65:
        # Balanced player can get any
        category = random.choice(['light_side', 'dark_side', 'neutral'])
        return random.choice(HOLOCRON_MESSAGES[category])
    else:
        # Dark side player gets dark side holocrons
        return random.choice(HOLOCRON_MESSAGES['dark_side'])

def get_random_distress_signal():
    """Get a random distress signal scenario."""
    return random.choice(DISTRESS_SIGNALS)

def get_environmental_event():
    """Get a random environmental event."""
    return random.choice(ENVIRONMENTAL_EVENTS)

def format_journal_display(journal):
    """Format a journal for display to player."""
    lines = []
    lines.append("═" * 60)
    lines.append(f"║ {journal['title'].center(56)} ║")
    lines.append(f"║ By: {journal['author'].center(52)} ║")
    lines.append("═" * 60)
    lines.append("")
    lines.append(journal['discovery_message'])
    lines.append("")
    
    for i, entry in enumerate(journal['entries'], 1):
        lines.append(f"Entry {i}: {entry}")
        if i < len(journal['entries']):
            lines.append("")
    
    return lines

def format_holocron_display(holocron):
    """Format a holocron message for display."""
    lines = []
    lines.append("═" * 60)
    lines.append("  HOLOCRON ACTIVATED  ".center(60))
    lines.append("═" * 60)
    lines.append("")
    lines.append(f"Speaker: {holocron['speaker']}")
    lines.append("")
    
    for line in holocron['message']:
        lines.append(f"  \"{line}\"")
        lines.append("")
    
    lines.append("═" * 60)
    return lines

def format_distress_signal(signal):
    """Format a distress signal scenario for display."""
    lines = []
    lines.append("═" * 60)
    lines.append(f"  {signal['signal_type'].upper().replace('_', ' ')}  ".center(60))
    lines.append("═" * 60)
    lines.append("")
    lines.append(f"Transmission: \"{signal['transmission']}\"")
    lines.append("")
    lines.append(signal['location_description'])
    lines.append("")
    
    for line in signal['scenario']['description']:
        lines.append(line)
        lines.append("")
    
    lines.append("What will you do?")
    lines.append("")
    lines.append(f"1. {signal['scenario']['choice_light']['text']}")
    lines.append(f"2. {signal['scenario']['choice_dark']['text']}")
    lines.append(f"3. {signal['scenario']['choice_ignore']['text']}")
    
    return lines

def should_trigger_narrative_event(turns_since_last, event_type='journal'):
    """
    Determine if a narrative event should trigger.
    
    Args:
        turns_since_last: Number of turns since last event of this type
        event_type: 'journal', 'holocron', 'distress', or 'environmental'
    
    Returns:
        Boolean indicating if event should trigger
    """
    thresholds = {
        'journal': (80, 120),  # Every 80-120 turns
        'holocron': (100, 150),  # Every 100-150 turns
        'distress': (150, 200),  # Every 150-200 turns
        'environmental': (60, 100),  # Every 60-100 turns
    }
    
    min_turns, max_turns = thresholds.get(event_type, (100, 150))
    
    if turns_since_last < min_turns:
        return False
    
    if turns_since_last >= max_turns:
        return True
    
    # Gradual increase in probability
    chance = (turns_since_last - min_turns) / (max_turns - min_turns)
    return random.random() < chance
