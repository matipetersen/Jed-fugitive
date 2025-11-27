"""
Progression Milestones for Dark Meridian.
Achievement ceremonies triggered by player progress: combat victories, discoveries, corruption thresholds, level-ups.
"""
import random

# ═══════════════════════════════════════════════════════════════════════════
# FIRST SITH DEFEATED
# ═══════════════════════════════════════════════════════════════════════════

FIRST_SITH_DEFEATED = {
    'title': 'First Blood',
    'messages': {
        'light': [
            "You stand over your fallen enemy, lightsaber still humming.",
            "The Sith trooper lies motionless. Your first kill.",
            "It had to be done. You defend yourself, nothing more.",
            "But a voice whispers: This is only the beginning."
        ],
        'balanced': [
            "The Sith falls. You feel neither triumph nor remorse.",
            "One enemy down. How many more will follow?",
            "You've crossed a threshold - from fugitive to fighter.",
            "Survival demands action. This was necessary."
        ],
        'dark': [
            "The Sith collapses, and you feel... powerful.",
            "Their fear fed you in those final moments.",
            "You could have shown mercy. You chose strength instead.",
            "The dark side whispers approval."
        ]
    },
    'journal_entry': {
        'light': "I took my first life today. A Sith trooper, hunting me. I had no choice - it was them or me. But I feel the weight of it. Every life matters, even an enemy's. The Force teaches compassion, yet here I am, a killer. I pray this doesn't become easier.",
        'balanced': "First Sith down. I'm past the point of peaceful escape now. They're hunting me, and I have to fight back. It's kill or be killed out here. The Jedi taught restraint, but survival demands action. I'll do what I must.",
        'dark': "I killed my first Sith today, and it felt... right. Their fear, their pain - I could sense it all through the Force. Power flows from conflict. The old teachings held me back, but out here, strength is all that matters. More will fall."
    },
    'effect': 'confidence_boost'
}

# ═══════════════════════════════════════════════════════════════════════════
# FIRST TOMB DISCOVERED
# ═══════════════════════════════════════════════════════════════════════════

FIRST_TOMB_DISCOVERED = {
    'title': 'The Threshold',
    'messages': {
        'light': [
            "You stand before the tomb entrance, ancient and foreboding.",
            "Dark energy radiates from within. Your instincts scream danger.",
            "The Jedi Masters warned of places like this - nexuses of the dark side.",
            "But inside may lie answers... or your doom."
        ],
        'balanced': [
            "An ancient Sith tomb. Forbidden knowledge within.",
            "Risk and reward. Power and peril.",
            "The dark side is strong here, but so is your curiosity.",
            "You'll tread carefully, but you will tread."
        ],
        'dark': [
            "A Sith tomb! The dark side calls to you from its depths.",
            "This is what you've been searching for - real power.",
            "The Jedi feared these places. You embrace them.",
            "Descend. Claim what waits below."
        ]
    },
    'journal_entry': {
        'light': "Found my first Sith tomb. The darkness emanating from it is palpable - I can feel corruption trying to claw its way into my mind. Every instinct tells me to run, but I need what's inside. Artifacts, knowledge, maybe a way off this world. I must stay vigilant. The dark side is strongest in places like this.",
        'balanced': "A Sith tomb. Dangerous, but necessary. I'm not here for power - I'm here for survival. If there are artifacts, weapons, or a way to communicate with the Republic, they're in places like this. I'll take what I need and get out. Simple.",
        'dark': "I found it. A Sith tomb, untouched for millennia. The power inside calls to me - I can feel it resonating with something deep within. The Jedi would call this corruption. I call it potential. I'm going in, and I'm not coming out the same person."
    },
    'effect': 'tomb_sense'
}

# ═══════════════════════════════════════════════════════════════════════════
# CORRUPTION THRESHOLD CEREMONIES
# ═══════════════════════════════════════════════════════════════════════════

CORRUPTION_MILESTONE_25 = {
    'title': 'The First Compromise',
    'threshold': 25,
    'messages': [
        "You notice it in small ways. Anger comes easier now.",
        "The Jedi Code feels... distant. Like a half-remembered dream.",
        "You justified it all - survival, necessity, pragmatism.",
        "But deep down, you know: you've changed.",
        "The dark side has taken root."
    ],
    'journal_entry': "I'm not the same Jedi I was when I crashed here. I can feel myself changing - darker thoughts come easier, violence feels more natural. I told myself it was survival, but it's more than that. The dark side is seeping in, and I'm... letting it. Not fighting as hard as I should. Am I weak, or just practical? I don't know anymore.",
    'effect': 'dark_whispers'
}

CORRUPTION_MILESTONE_50 = {
    'title': 'The Tipping Point',
    'threshold': 50,
    'messages': [
        "You stand at the edge of an abyss.",
        "Half your soul belongs to the dark side now.",
        "You feel powerful. Decisive. Unrestrained.",
        "The Jedi Masters would call you fallen.",
        "You call yourself free."
    ],
    'journal_entry': "I'm past the point of no return. The light and dark wage war inside me constantly. I've done things that would horrify my old teachers - killed without hesitation, embraced anger, drawn on the dark side deliberately. But I'm still alive. Survival demands sacrifice. Even if that sacrifice is my own soul.",
    'effect': 'inner_conflict'
}

CORRUPTION_MILESTONE_75 = {
    'title': 'The Embrace',
    'threshold': 75,
    'messages': [
        "The dark side is no longer your enemy. It's your ally.",
        "You wield it like a weapon, channeling hatred and fear into power.",
        "The Jedi teachings? Chains that held you back.",
        "You're stronger now than you ever were as a Jedi.",
        "And you're just getting started."
    ],
    'journal_entry': "The dark side flows through me like lightning. I don't fear it anymore - I command it. Every kill makes me stronger. Every act of cruelty feeds my power. The Jedi were fools to deny this potential. I'm not fallen - I'm ascended. Let the Sith come. I'll show them what true power looks like.",
    'effect': 'dark_mastery'
}

# ═══════════════════════════════════════════════════════════════════════════
# LEVEL MILESTONE CEREMONIES
# ═══════════════════════════════════════════════════════════════════════════

LEVEL_MILESTONES = {
    5: {
        'title': 'Survivor',
        'messages': {
            'light': [
                "You've endured where many would have fallen.",
                "Five levels of growth. Five steps from death.",
                "The Force guided you, even in darkness.",
                "You remain true to the light."
            ],
            'balanced': [
                "Level 5. You're adapting, learning, surviving.",
                "Neither hero nor villain - just a survivor.",
                "The path ahead is long, but you've proven you can walk it."
            ],
            'dark': [
                "Level 5. Power accumulates with every battle.",
                "You're no longer prey - you're the predator.",
                "Fear you. Respect you. Or die."
            ]
        },
        'reward': 'skill_point'
    },
    10: {
        'title': 'Warrior',
        'messages': {
            'light': [
                "Ten levels. A true Jedi Knight in power, if not in title.",
                "You've protected the innocent and resisted corruption.",
                "The Order would be proud."
            ],
            'balanced': [
                "Level 10. You've mastered combat and survived impossible odds.",
                "Neither Jedi nor Sith define you - you forge your own path."
            ],
            'dark': [
                "Level 10. Lesser beings cower before you.",
                "You've embraced power without apology.",
                "The Sith Lords will take notice."
            ]
        },
        'reward': 'ability_unlock'
    },
    15: {
        'title': 'Master',
        'messages': {
            'light': [
                "Fifteen levels of discipline and growth.",
                "You've become what the Order hoped: a beacon of light in darkness.",
                "May the Force be with you, always."
            ],
            'balanced': [
                "Level 15. You've transcended simple labels.",
                "Light and dark are tools. You wield both with wisdom."
            ],
            'dark': [
                "Level 15. You rival the ancient Sith Lords in power.",
                "None can stand against you. All will kneel."
            ]
        },
        'reward': 'force_mastery'
    },
    20: {
        'title': 'Legend',
        'messages': {
            'light': [
                "Twenty levels. You've achieved what few Jedi ever do.",
                "A living legend, even in exile.",
                "Your name will echo through the Force itself."
            ],
            'balanced': [
                "Level 20. You've become myth.",
                "Gray Jedi, Shadow Walker, Force Incarnate.",
                "You are beyond Light and Dark - you ARE the Force."
            ],
            'dark': [
                "Level 20. You've surpassed even your Sith pursuers.",
                "Dark Lord is not a title - it's a destiny.",
                "The galaxy will tremble at your name."
            ]
        },
        'reward': 'legendary_status'
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# TOMB DEPTH MILESTONES
# ═══════════════════════════════════════════════════════════════════════════

TOMB_DEPTH_MILESTONES = {
    3: {
        'title': 'Into the Deep',
        'message': "Three levels into the tomb. The air grows colder. The darkness, heavier.",
        'effect': 'pressure_mounting'
    },
    5: {
        'title': 'The Abyss',
        'message': "Five levels down. You've descended farther than most dare. Ancient evil awakens.",
        'effect': 'sith_awareness'
    },
    10: {
        'title': 'Heart of Darkness',
        'message': "Ten levels. The tomb's core. Something waits here. Something old. Something hungry.",
        'effect': 'final_guardian'
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# KILL COUNT MILESTONES
# ═══════════════════════════════════════════════════════════════════════════

KILL_MILESTONES = {
    10: {
        'title': 'Blooded',
        'messages': {
            'light': "Ten lives taken. Ten souls on your conscience. The burden weighs heavy.",
            'balanced': "Ten confirmed kills. You're a soldier now, not a diplomat.",
            'dark': "Ten enemies crushed. Their fear fuels you. More will follow."
        }
    },
    25: {
        'title': 'Veteran',
        'messages': {
            'light': "Twenty-five dead by your hand. How many more before this ends?",
            'balanced': "Twenty-five kills. You've become efficient. Professional.",
            'dark': "Twenty-five corpses in your wake. Magnificent."
        }
    },
    50: {
        'title': 'Executioner',
        'messages': {
            'light': "Fifty lives extinguished. Their faces haunt your dreams.",
            'balanced': "Fifty enemies eliminated. The body count is staggering.",
            'dark': "Fifty souls offered to the dark side. Your power grows exponentially."
        }
    },
    100: {
        'title': 'Death Incarnate',
        'messages': {
            'light': "One hundred dead. You're a walking massacre. What have you become?",
            'balanced': "One hundred kills. You're a legend. And a cautionary tale.",
            'dark': "One hundred sacrifices. The dark side crowns you its champion."
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# ARTIFACT COLLECTION MILESTONES
# ═══════════════════════════════════════════════════════════════════════════

ARTIFACT_MILESTONES = {
    5: {
        'title': 'Collector',
        'message': "Five Sith artifacts recovered. Each one pulses with dark power.",
        'effect': 'artifact_resonance'
    },
    10: {
        'title': 'Hoarder',
        'message': "Ten artifacts. Your collection rivals ancient Sith Lords.",
        'effect': 'dark_enlightenment'
    },
    20: {
        'title': 'Dark Archivist',
        'message': "Twenty artifacts. You've assembled forbidden knowledge the Jedi tried to erase.",
        'effect': 'sith_mastery'
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_alignment_category(corruption):
    """Determine player's alignment category based on corruption."""
    if corruption <= 35:
        return 'light'
    elif corruption <= 65:
        return 'balanced'
    else:
        return 'dark'

def format_milestone_display(milestone_data, corruption=50):
    """Format a milestone event for display."""
    lines = []
    lines.append("═" * 60)
    lines.append(f"  ★ {milestone_data['title'].upper()} ★  ".center(60))
    lines.append("═" * 60)
    lines.append("")
    
    # Get appropriate messages
    if 'messages' in milestone_data:
        alignment = get_alignment_category(corruption)
        if isinstance(milestone_data['messages'], dict):
            messages = milestone_data['messages'].get(alignment, [])
            if isinstance(messages, list):
                for msg in messages:
                    lines.append(msg)
                    lines.append("")
            else:
                lines.append(messages)
                lines.append("")
        else:
            lines.append(milestone_data['messages'])
            lines.append("")
    
    elif 'message' in milestone_data:
        lines.append(milestone_data['message'])
        lines.append("")
    
    # Reward info
    if 'reward' in milestone_data:
        lines.append("─" * 60)
        reward = milestone_data['reward'].replace('_', ' ').title()
        lines.append(f"Reward: {reward}")
        lines.append("")
    
    # Effect info
    if 'effect' in milestone_data:
        effect = milestone_data['effect'].replace('_', ' ').title()
        lines.append(f"Effect: {effect}")
    
    return lines

def get_journal_entry_for_milestone(milestone_data, corruption=50):
    """Get the journal entry text for a milestone."""
    if 'journal_entry' in milestone_data:
        if isinstance(milestone_data['journal_entry'], dict):
            alignment = get_alignment_category(corruption)
            return milestone_data['journal_entry'].get(alignment, "")
        else:
            return milestone_data['journal_entry']
    return None

def check_milestone_trigger(player, milestone_type, value):
    """Check if a milestone should trigger based on player stats."""
    # Track which milestones have been triggered
    if not hasattr(player, '_triggered_milestones'):
        player._triggered_milestones = set()
    
    milestone_key = f"{milestone_type}_{value}"
    
    if milestone_key in player._triggered_milestones:
        return False  # Already triggered
    
    # Check if conditions are met
    if milestone_type == 'level':
        if player.level >= value:
            player._triggered_milestones.add(milestone_key)
            return True
    
    elif milestone_type == 'corruption':
        if player.corruption >= value:
            player._triggered_milestones.add(milestone_key)
            return True
    
    elif milestone_type == 'kills':
        kills = getattr(player, 'total_kills', 0)
        if kills >= value:
            player._triggered_milestones.add(milestone_key)
            return True
    
    elif milestone_type == 'artifacts':
        artifacts = len(getattr(player, 'artifacts_collected', []))
        if artifacts >= value:
            player._triggered_milestones.add(milestone_key)
            return True
    
    elif milestone_type == 'tomb_depth':
        depth = getattr(player, 'max_tomb_depth', 0)
        if depth >= value:
            player._triggered_milestones.add(milestone_key)
            return True
    
    elif milestone_type == 'first_sith':
        # Check if this is the first kill
        if not hasattr(player, '_first_kill_triggered'):
            kills = getattr(player, 'total_kills', 0)
            if kills >= 1:
                player._first_kill_triggered = True
                player._triggered_milestones.add('first_sith_1')
                return True
    
    elif milestone_type == 'first_tomb':
        # Check if player has discovered their first tomb
        if not hasattr(player, '_first_tomb_triggered'):
            discovered = getattr(player, 'tombs_discovered', 0)
            if discovered >= 1:
                player._first_tomb_triggered = True
                player._triggered_milestones.add('first_tomb_1')
                return True
    
    return False

def process_milestone_effects(player, effect_type):
    """Apply effects from milestone achievements."""
    if effect_type == 'confidence_boost':
        # Slight corruption decrease for first kill (remorse)
        player.corruption = max(0, player.corruption - 2)
    
    elif effect_type == 'tomb_sense':
        # Player gains ability to sense nearby tombs
        if not hasattr(player, 'tomb_sense'):
            player.tomb_sense = True
    
    elif effect_type == 'dark_whispers':
        # Corruption milestone effects
        pass
    
    elif effect_type == 'inner_conflict':
        # Major corruption milestone
        pass
    
    elif effect_type == 'dark_mastery':
        # Near-full corruption
        pass
    
    elif effect_type == 'skill_point':
        # Award bonus skill point
        if hasattr(player, 'skill_points'):
            player.skill_points += 1
    
    elif effect_type == 'ability_unlock':
        # Unlock special ability
        pass
    
    elif effect_type == 'force_mastery':
        # Increase Force power
        player.max_force = getattr(player, 'max_force', 100) + 20
        player.force = player.max_force
    
    elif effect_type == 'legendary_status':
        # Permanent stat boost
        player.max_hp = getattr(player, 'max_hp', 100) + 50
        player.hp = player.max_hp

def get_all_pending_milestones(player):
    """Get all milestones that should trigger for the current player state."""
    pending = []
    
    # Check first kill
    if check_milestone_trigger(player, 'first_sith', 1):
        pending.append(('first_sith', FIRST_SITH_DEFEATED))
    
    # Check first tomb
    if check_milestone_trigger(player, 'first_tomb', 1):
        pending.append(('first_tomb', FIRST_TOMB_DISCOVERED))
    
    # Check corruption milestones
    for threshold in [25, 50, 75]:
        if check_milestone_trigger(player, 'corruption', threshold):
            milestone = eval(f"CORRUPTION_MILESTONE_{threshold}")
            pending.append((f'corruption_{threshold}', milestone))
    
    # Check level milestones
    for level, milestone in LEVEL_MILESTONES.items():
        if check_milestone_trigger(player, 'level', level):
            pending.append((f'level_{level}', milestone))
    
    # Check kill count milestones
    for count, milestone in KILL_MILESTONES.items():
        if check_milestone_trigger(player, 'kills', count):
            pending.append((f'kills_{count}', milestone))
    
    # Check tomb depth milestones
    for depth, milestone in TOMB_DEPTH_MILESTONES.items():
        if check_milestone_trigger(player, 'tomb_depth', depth):
            pending.append((f'tomb_depth_{depth}', milestone))
    
    # Check artifact milestones
    for count, milestone in ARTIFACT_MILESTONES.items():
        if check_milestone_trigger(player, 'artifacts', count):
            pending.append((f'artifacts_{count}', milestone))
    
    return pending
