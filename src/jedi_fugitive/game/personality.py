from enum import Enum
import random

# Dynamic taunts based on player's dark side progression with environmental context
ENEMY_TAUNTS_BY_ALIGNMENT = {
    # Taunts for Light Side Player (dark_side_points <= 20)
    "light": {
        "attack": [
            "You will fall before the Sith!",
            "Feel the power of the dark side!",
            "Your Jedi tricks won't save you!",
            "The light makes you weak!",
            "I'll crush your pathetic hope!",
            "Your compassion is your weakness!",
            "Another Jedi falls to darkness!",
            "The Empire's vengeance is swift!",
            "Your lightsaber cannot protect you forever!",
            "The Force abandons the righteous!",
            "Hope dies with you, Jedi scum!",
            "Your Order is extinct - accept it!",
        ],
        "defend": [
            "I am one with the Force!",
            "You cannot break me!",
            "The dark side shields me!",
            "Your light cannot pierce my darkness!",
            "Hatred makes me stronger!",
        ],
        "low_hp": [
            "This isn't over!",
            "I will avenge my brothers!",
            "You... will... pay!",
            "The Sith are eternal!",
            "My death means nothing!",
        ],
    },
    
    # Taunts for Neutral Player (dark_side_points 21-60)
    "neutral": {
        "attack": [
            "You're not as pure as you pretend!",
            "I can sense the darkness growing in you!",
            "You're starting to understand true power!",
            "The conflict within you makes you strong!",
            "Neither light nor dark - just weak!",
            "Choose a side, coward!",
            "The grey path leads only to defeat!",
            "Indecision will be your downfall!",
            "I smell the fear in your wavering soul!",
            "Your uncertainty betrays your weakness!",
            "The Force responds to conviction - you have none!",
            "Fence-sitters die first in war!",
        ],
        "defend": [
            "Your uncertainty betrays you!",
            "I can feel your anger!",
            "The darkness calls to you!",
            "You're fighting what you truly are!",
            "Embrace your potential!",
        ],
        "low_hp": [
            "You're becoming one of us!",
            "The dark side has marked you!",
            "I see the Sith Lord you'll become!",
            "Your fall has already begun!",
            "Welcome to the darkness!",
        ],
    },
    
    # Taunts for Dark Side Player (dark_side_points > 60)
    "dark": {
        "attack": [
            "You dare challenge a true Sith?!",
            "I bow to no pretender!",
            "Your power is nothing compared to mine!",
            "There can be only one Dark Lord!",
            "I'll show you what real darkness looks like!",
            "You think you know the Sith way?",
            "Apprentice! You forget your place!",
            "Your arrogance will be your downfall!",
        ],
        "defend": [
            "You've learned well, but not well enough!",
            "The student challenges the master!",
            "Your hatred feeds me!",
            "We are the same, you and I!",
            "Feel the power of a true Sith!",
            "You cannot surpass your betters!",
        ],
        "low_hp": [
            "You... you have surpassed me...",
            "The apprentice becomes the master!",
            "I taught you too well!",
            "Kill me... complete your training!",
            "You are truly Sith now!",
            "The Rule of Two demands this!",
            "I die knowing I created a monster!",
            "My death will make you stronger!",
        ],
    },
}

ENEMY_TAUNTS = ENEMY_TAUNTS_BY_ALIGNMENT["light"]

# Animal/Fauna taunts (emotes only, no words)
FAUNA_TAUNTS = {
    "rock_lizard": {
        "attack": ["*hisses and lunges*", "*tail lashes the ground*", "*scales scrape on stone*"],
        "roam": ["*blends with the rocks*", "*tongue flicks out*", "*scurries between boulders*"],
        "death": ["*limbs twitch, then still*", "*stone-like hide cracks*", "*fades into the dust*"]
    },
    "crimson_leviathan": {
        "attack": ["*ROARS with blood-red fury*", "*massive jaws snap shut*", "*tail sweeps the sand*"],
        "roam": ["*prowls through red-stained wastes*", "*sand trembles with each step*"],
        "death": ["*collapses, shaking the dunes*", "*crimson eyes dim*", "*the desert falls silent*"]
    },
    "boulder_brute": {
        "attack": ["*hurls a massive rock*", "*snorts and charges*", "*lets out a guttural bellow*"],
        "roam": ["*grinds stone underfoot*", "*sniffs the air for prey*"],
        "death": ["*crashes to the ground*", "*dust billows up*", "*the earth shakes*"]
    },
    "plains_stalker": {
        "attack": ["*growls and circles*", "*leaps with claws extended*", "*snaps jaws*"],
        "roam": ["*moves swiftly through tall grass*", "*ears twitch, listening*"],
        "death": ["*body slumps in the grass*", "*final whimper fades*", "*pack howls in the distance*"]
    },
    # Add more fauna/creature types as needed
}

# Environmental and contextual taunts for enhanced immersion
ENVIRONMENTAL_TAUNTS = {
    "desert": {
        "attack": [
            "The desert sands will drink your blood!",
            "Like a mirage, your hope is an illusion!",
            "The sun beats down on your corpse!",
            "Even the vultures won't touch Jedi meat!",
            "The dunes will be your unmarked grave!",
            "This wasteland claims another fool!"
        ],
        "defend": [
            "I know every grain of sand here!",
            "The desert is my ally, not yours!",
            "Heat and hatred sustain me!",
            "You'll die of thirst before you defeat me!"
        ]
    },
    "forest": {
        "attack": [
            "The trees will watch you die!",
            "Nature itself rejects your presence!",
            "Your bones will feed these roots!",
            "The forest whispers of your doom!",
            "Even the wildlife flees from you!",
            "These ancient woods have seen empires fall!"
        ],
        "defend": [
            "The forest hides my movements!",
            "Every shadow conceals my blade!",
            "The wilderness knows no mercy!",
            "I am one with the predators here!"
        ]
    },
    "mountains": {
        "attack": [
            "From these heights, I'll cast you down!",
            "The mountains themselves reject you!",
            "An avalanche of steel and fury!",
            "Your screams will echo in these peaks!",
            "The thin air will be your last breath!",
            "Stone cold death awaits you here!"
        ],
        "defend": [
            "I stand firm as the mountain itself!",
            "These peaks have weathered worse than you!",
            "The high ground is mine!",
            "Altitude and attitude - both superior!"
        ]
    },
    "tomb": {
        "attack": [
            "Join the ancient dead in eternal torment!",
            "These tombs hunger for fresh souls!",
            "The Sith Lords demand your sacrifice!",
            "Darkness eternal awaits your spirit!",
            "You disturb the sleep of the damned!",
            "Ancient evil courses through my veins!"
        ],
        "defend": [
            "The dead rise to defend this place!",
            "Centuries of hatred empower me!",
            "This tomb is my fortress!",
            "The ancestors' fury shields me!"
        ]
    },
    "crash_site": {
        "attack": [
            "Your ship burns like your hope!",
            "Twisted metal, twisted fate!",
            "The wreckage foretells your doom!",
            "Another crash, another casualty!",
            "Technology fails, flesh fails, hope fails!",
            "The debris will make a fine funeral pyre!"
        ],
        "defend": [
            "I salvage victory from defeat!",
            "These ruins are my battlefield!",
            "Broken ships, broken enemies!",
            "From destruction comes my strength!"
        ]
    }
}

# Combat situation-specific taunts
COMBAT_SITUATION_TAUNTS = {
    "low_player_hp": [
        "I smell your blood on the wind!",
        "Death comes for you with each breath!",
        "Your weakness becomes more apparent!",
        "The end approaches - can you feel it?",
        "One more strike and it's over!",
        "Your life force ebbs away like sand!"
    ],
    "player_missed": [
        "Your aim falters with your courage!",
        "Even the Force abandons your strikes!",
        "Desperation makes you clumsy!",
        "Fear clouds your precision!",
        "Your technique crumbles under pressure!"
    ],
    "enemy_low_hp": [
        "I'll take you with me to the grave!",
        "My death will haunt your dreams!",
        "A Sith's final moments are the deadliest!",
        "Wounded beasts are the most dangerous!",
        "You may win, but at what cost?"
    ],
    "multiple_enemies": [
        "We have you surrounded!",
        "The pack closes in for the kill!",
        "You cannot face us all!",
        "Divided attention, certain death!",
        "Choose your target - it matters not!"
    ],
    "player_alone": [
        "No allies to save you now!",
        "Isolation breeds desperation!",
        "Where are your Jedi friends?",
        "Alone you came, alone you'll die!",
        "The galaxy has abandoned you!"
    ]
}

# Jedi/Light-aligned enemy taunts (also responsive to player alignment)
JEDI_MASTER_TAUNTS_BY_ALIGNMENT = {
    # Responses to Light Side Player
    "light": {
        "attack": [
            "The Force flows through me!",
            "I will bring you back to the light!",
            "Your dark path ends here!",
            "Let me show you the true way!",
            "The light will cleanse this darkness!",
        ],
        "defend": [
            "Peace is my ally!",
            "The light side protects me!",
            "Patience defeats aggression!",
            "I stand with the Force!",
            "Your anger gives you focus, but makes you predictable!",
        ],
        "low_hp": [
            "The Force will guide me!",
            "I sense conflict in you...",
            "There is still good in you!",
            "You have chosen a dark path!",
            "I failed to save you...",
        ],
    },
    
    # Responses to Neutral Player
    "neutral": {
        "attack": [
            "I can still save you from this path!",
            "Turn away from the darkness while you can!",
            "You walk a dangerous line!",
            "Choose the light before it's too late!",
            "I sense the conflict within you!",
        ],
        "defend": [
            "You're losing yourself to anger!",
            "This isn't who you're meant to be!",
            "Fight the darkness within!",
            "I can feel your struggle!",
            "The light still calls to you!",
        ],
        "low_hp": [
            "You're slipping away from the light!",
            "I can still sense good in you!",
            "Don't let the darkness win!",
            "There's still time to turn back!",
            "I... I couldn't reach you in time...",
        ],
    },
    
    # Responses to Dark Side Player  
    "dark": {
        "attack": [
            "What have you become?!",
            "You are lost to the darkness!",
            "I will stop this monster you've become!",
            "The Sith have consumed you completely!",
            "You are no longer the person I once knew!",
            "I should have stopped you sooner!",
        ],
        "defend": [
            "Your hatred burns through everything!",
            "The darkness has twisted you beyond recognition!",
            "I can no longer sense any light in you!",
            "You've become everything I fought against!",
            "The Sith have won... they have you now!",
        ],
        "low_hp": [
            "You are completely lost...",
            "I have failed you utterly!",
            "The darkness has won...",
            "You've become the very evil I swore to fight!",
            "May the Force... forgive us both...",
            "I die knowing I couldn't save you...",
            "You are Sith... truly Sith...",
        ],
    },
}

# Legacy taunts for backward compatibility
JEDI_MASTER_TAUNTS = JEDI_MASTER_TAUNTS_BY_ALIGNMENT["light"]

# Special contextual taunts
SPECIAL_TAUNTS = {
    "high_kill_count": [
        "Butcher! You leave only corpses in your wake!",
        "The blood of innocents stains your hands!",
        "Death follows wherever you go!",
        "You've become a monster!",
        "How many more must die by your hand?",
    ],
    "force_lightning_user": [
        "I can smell the ozone from your lightning!",
        "The Emperor would be proud!",
        "Your fingers crackle with pure hatred!",
        "Lightning betrays your Sith nature!",
        "The dark side flows through you like electricity!",
    ],
    "force_choke_user": [
        "You strangle the life from others like a true Sith!",
        "Your grip on the Force is choking us all!",
        "The throat-crusher! Your reputation precedes you!",
        "Death by your invisible hands!",
        "You've mastered the Sith's favorite technique!",
    ],
    "tomb_raider": [
        "Defiler of ancient tombs!",
        "You disturb the rest of the dead!",
        "Grave robber! You have no respect!",
        "The ancestors curse your name!",
        "You plunder what should remain buried!",
    ],
    "betrayer": [
        "Betrayer! You cannot be trusted!",
        "You turn on your allies like a true Sith!",
        "Trust dies wherever you walk!",
        "Treachery is your greatest weapon!",
        "You've betrayed everyone who helped you!",
    ],
}


def get_player_alignment_category(player):
    """Determine player alignment category based on dark side points."""
    try:
        dark_points = getattr(player, 'dark_side_points', 0)
        if dark_points <= 20:
            return "light"
        elif dark_points <= 60:
            return "neutral"
        else:
            return "dark"
    except:
        return "light"  # Default to light side


def get_contextual_taunt(player, situation="attack", game_context=None):
    """Get a taunt based on player's actions, reputation, and current environment."""
    try:
        taunts = []
        
        # Check for special behaviors
        kill_count = getattr(player, 'enemies_killed', 0)
        force_abilities = getattr(player, 'force_abilities', [])
        
        # High kill count (bloodthirsty player)
        if kill_count > 20:
            taunts.extend(SPECIAL_TAUNTS.get("high_kill_count", []))
        
        # Force Lightning user
        if any('lightning' in str(ability).lower() for ability in force_abilities):
            taunts.extend(SPECIAL_TAUNTS.get("force_lightning_user", []))
        
        # Force Choke user  
        if any('choke' in str(ability).lower() for ability in force_abilities):
            taunts.extend(SPECIAL_TAUNTS.get("force_choke_user", []))
        
        # Tomb raider (many tombs cleared)
        tombs_cleared = getattr(player, 'tombs_cleared', 0)
        if tombs_cleared > 3:
            taunts.extend(SPECIAL_TAUNTS.get("tomb_raider", []))
        
        # Environmental context taunts
        if game_context:
            current_biome = getattr(game_context, 'current_biome', None)
            in_tomb = getattr(game_context, 'in_tomb', False)
            
            if in_tomb:
                env_taunts = ENVIRONMENTAL_TAUNTS.get('tomb', {}).get(situation, [])
                taunts.extend(env_taunts)
            elif current_biome:
                env_taunts = ENVIRONMENTAL_TAUNTS.get(current_biome, {}).get(situation, [])
                taunts.extend(env_taunts)
            
            # Combat situation awareness
            player_hp = getattr(player, 'hp', 0)
            max_hp = getattr(player, 'max_hp', 1)
            
            if player_hp / max_hp < 0.3:  # Player low on health
                taunts.extend(COMBAT_SITUATION_TAUNTS.get('low_player_hp', []))
            
            # Check for multiple enemies nearby
            enemies_nearby = getattr(game_context, 'enemies', [])
            if len([e for e in enemies_nearby if getattr(e, 'is_alive', lambda: True)()]) > 2:
                taunts.extend(COMBAT_SITUATION_TAUNTS.get('multiple_enemies', []))
        
        return random.choice(taunts) if taunts else None
    except:
        return None


class EnemyPersonality:
    def __init__(self, is_jedi=False, enemy_type=None, personality_traits=None):
        self.is_jedi = is_jedi
        self.enemy_type = enemy_type
        self.personality_traits = personality_traits or []
        self.base_taunts = JEDI_MASTER_TAUNTS if is_jedi else ENEMY_TAUNTS
        self.combat_history = []  # Track combat interactions
        self.relationship_modifier = 0  # How enemy feels about player
        self.fear_level = 0  # 0-100, affects taunts when low HP

    def get_taunt(self, situation, player=None):
        """Get a taunt based on situation and player alignment/actions."""
        try:
            # Animal/creature types that should not speak
            animal_types = [
                'rock lizard', 'dust stalker', 'vine beast', 'canopy hunter', 'boulder brute', 'crystal spider',
                'grass runner', 'dewback', 'mire cat', 'force fish', 'storm hawk', 'sandworm spawn', 'plains stalker',
                'pack hunter', 'plains charger', 'rock burrower', 'nexu cub', 'corrupted vine cat', 'force firefly'
            ]
            # If enemy_type is animal/creature, return animal sound
            if self.enemy_type and self.enemy_type.lower() in animal_types:
                animal_sounds = [
                    "*hisses*", "*growls*", "*snarls*", "*scuttles*", "*chirps*", "*roars*", "*clicks*", "*howls*", "*screeches*", "*rattles*"
                ]
                return random.choice(animal_sounds)
            # If personality_traits indicate animal/creature, return animal sound
            if self.personality_traits and any(trait in ['animal', 'creature', 'beast', 'fauna'] for trait in self.personality_traits):
                animal_sounds = [
                    "*hisses*", "*growls*", "*snarls*", "*scuttles*", "*chirps*", "*roars*", "*clicks*", "*howls*", "*screeches*", "*rattles*"
                ]
                return random.choice(animal_sounds)
            # First try to get a contextual taunt based on player actions
            if player and random.random() < 0.3:  # 30% chance for contextual taunt
                contextual = get_contextual_taunt(player, situation)
                if contextual:
                    return contextual
            # Get alignment-based taunt
            if player:
                alignment = get_player_alignment_category(player)
                if self.is_jedi:
                    alignment_taunts = JEDI_MASTER_TAUNTS_BY_ALIGNMENT.get(alignment, JEDI_MASTER_TAUNTS_BY_ALIGNMENT["light"])
                else:
                    alignment_taunts = ENEMY_TAUNTS_BY_ALIGNMENT.get(alignment, ENEMY_TAUNTS_BY_ALIGNMENT["light"])
                taunt_list = alignment_taunts.get(situation, alignment_taunts.get("attack", ["..."]))
            else:
                # Fallback to base taunts
                taunt_list = self.base_taunts.get(situation, ["..."])
            return random.choice(taunt_list)
        except Exception:
            # Ultimate fallback
            return random.choice(["*hisses*", "*growls*", "*scuttles*", "*creature noises*"])


# ============ MASSIVE CREATURE PERSONALITIES ============

MASSIVE_CREATURE_TAUNTS = {
    "crimson_leviathan": {
        "attack": [
            "*ROARS with blood-red fury*",
            "The crimson sands shall drink your blood!",
            "*Massive crimson claws rake the air*",
            "I am death under the twin suns!",
            "*Scarlet eyes burn with ancient rage*",
            "Your bones will bleach in my domain!",
            "*Armored hide deflects your futile strikes*"
        ],
        "roam": [
            "*Prowls through red-stained wastes*",
            "*Ancient predator scans the dunes*",
            "*Moves like a living crimson mountain*"
        ],
        "death": [
            "*Falls like a crimson fortress*",
            "*Final roar echoes across blood-red sands*",
            "*The desert's apex predator is no more*"
        ]
    },
    "bone_crusher": {
        "attack": [
            "*BELLOWS with crushing might*",
            "*Massive fists pulverize stone*",
            "Your bones will join my collection!",
            "*Slavering jaws drip with hunger*",
            "*Eyes gleam with predatory malice*",
            "I smell your marrow!",
            "*Each step cracks the cavern floor*"
        ],
        "roam": [
            "*Sniffs for fresh prey*",
            "*Massive form stalks through darkness*",
            "*Claws scrape against tomb walls*"
        ],
        "death": [
            "*Collapses with earth-shaking impact*",
            "*Final bellow echoes through tombs*",
            "*The bone collector is silenced*"
        ]
    },
    "void_tendril": {
        "attack": [
            "*Void-touched tentacles writhe*",
            "The darkness hungers for you!",
            "*Force-corrupted appendages lash out*",
            "I am what the Sith made!",
            "*Dark energies crackle along my form*",
            "Feed the eternal void!",
            "*Reality tears where I touch*"
        ],
        "roam": [
            "*Phases in and out of existence*",
            "*Senses through Force disturbances*",
            "*Darkness follows in my wake*"
        ],
        "death": [
            "*Dissolves into shadow mist*",
            "*The void reclaims its child*",
            "*Dark corruption finally fades*"
        ]
    },
    "shadow_stalker": {
        "attack": [
            "*Emerges from living darkness*",
            "Death stalks on silent shadow!",
            "*Dark side enhancement flows through me*",
            "*Multiple shadow-forms confuse your eyes*",
            "The hunt ends now!",
            "*Darkness-cloaked claws strike*",
            "Fear feeds my power!"
        ],
        "roam": [
            "*Flows between shadows*",
            "*Dark energies mask my presence*",
            "*Stalks with supernatural grace*"
        ],
        "death": [
            "*Shadow form begins to fade*",
            "*The darkness releases its hold*",
            "*Returns to the shadow realm*"
        ]
    },
    "stone_titan": {
        "attack": [
            "*VOICE RESONATES like mountain thunder*",
            "This world's stone obeys my will!",
            "*Massive stone fists descend*",
            "I am guardian of ancient secrets!",
            "*Each step causes seismic tremors*",
            "Your flesh is weak against stone!",
            "*Mineral armor deflects your blows*"
        ],
        "roam": [
            "*Stone limbs grind with each movement*",
            "*Ancient guardian surveys the land*",
            "*Bedrock trembles at my passage*"
        ],
        "death": [
            "*Crumbles like an avalanche*",
            "*Stone returns to mountain's embrace*",
            "*The eternal guardian rests*"
        ]
    },
    "tomb_serpent": {
        "attack": [
            "*Ancient coils constrict reality*",
            "I guard these tombs since time began!",
            "*Millenia of tomb-dust in my scales*",
            "Your trespass ends in death!",
            "*Hypnotic patterns cloud your mind*",
            "The dead whisper your doom!",
            "*Fangs drip with ancient venom*"
        ],
        "roam": [
            "*Coils through burial chambers*",
            "*Tastes the air for intruders*",
            "*Serpentine form flows like liquid*"
        ],
        "death": [
            "*Ancient coils finally still*",
            "*Tomb guardian's vigil ends*",
            "*The serpent joins the eternal rest*"
        ]
    },
    "dark_weaver": {
        "attack": [
            "*Force-sensitive legs coordinate death*",
            "My web spans dimensions!",
            "*Dark side energy flows through silk*",
            "The pattern of your doom is woven!",
            "*Eight eyes see through the Force*",
            "Trapped in threads of destiny!",
            "*Venom carries Sith corruption*"
        ],
        "roam": [
            "*Scuttles across reality-warped webs*",
            "*Force sensitivity guides the hunt*",
            "*Dark patterns shift in the web*"
        ],
        "death": [
            "*Web trembles with final death-throes*",
            "*The dark pattern is broken*",
            "*Sith-touched weaver falls silent*"
        ]
    },
    "frost_behemoth": {
        "attack": [
            "*HOWLS with eternal winter's rage*",
            "This world's cold shall claim you!",
            "*Ice-encrusted claws tear flesh*",
            "I am winter made manifest!",
            "*Frozen breath creates ice crystals*",
            "Your warmth will be extinguished!",
            "*Permafrost follows my steps*"
        ],
        "roam": [
            "*Leaves trails of perpetual frost*",
            "*Cold radiates from massive form*",
            "*Ice forms in my footprints*"
        ],
        "death": [
            "*Falls with the sound of cracking glaciers*",
            "*Eternal winter's grip finally loosens*",
            "*The frost lord's reign ends*"
        ]
    }
}


def get_massive_creature_taunt(creature_type: str, situation: str = "attack") -> str:
    """Get a taunt for a massive creature."""
    try:
        creature_key = creature_type.lower().replace(" ", "_")
        taunts = MASSIVE_CREATURE_TAUNTS.get(creature_key, {})
        taunt_list = taunts.get(situation, taunts.get("attack", ["*Massive creature stirs*"]))
        return random.choice(taunt_list)
    except Exception:
        return "*The massive creature looms menacingly*"