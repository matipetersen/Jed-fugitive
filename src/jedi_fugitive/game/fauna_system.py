from .personality import FAUNA_TAUNTS
"""
Fauna System for Dark Meridian - Biome-specific creatures and interactions.
Adds living ecosystems to each biome with creatures the player can interact with.
All encounters are logged in the player's journal for immersive storytelling.
"""
import random

# Fauna types and their characteristics
class FaunaType:
    PASSIVE = "passive"          # Harmless creatures (banthas, dewbacks)
    NEUTRAL = "neutral"         # May defend themselves if threatened
    AGGRESSIVE = "aggressive"   # Will attack on sight
    FORCE_SENSITIVE = "force_sensitive"  # Reacts to player's alignment
    CORRUPTED = "corrupted"     # Twisted by dark side energy

class FaunaSize:
    TINY = "tiny"           # Insects, small birds
    SMALL = "small"         # Rodents, small reptiles  
    MEDIUM = "medium"       # Human-sized creatures
    LARGE = "large"         # Horse-sized creatures
    MASSIVE = "massive"     # Rancor-sized creatures

# Biome-specific fauna definitions
BIOME_FAUNA = {
    'forest': [
        {
            'name': 'Nexu Cub',
            'type': FaunaType.NEUTRAL,
            'size': FaunaSize.SMALL,
            'rarity': 0.06,  # 6% chance to encounter
            'description': 'A young nexu with spotted fur, cautiously watching you.',
            'force_reaction': {
                'light': 'The cub approaches curiously, sensing your peaceful intent.',
                'balanced': 'The cub maintains its distance, neither fleeing nor approaching.',
                'dark': 'The cub hisses and retreats, sensing the darkness within you.'
            },
            'interactions': {
                'observe': 'You watch the nexu cub as it explores the undergrowth.',
                'feed': 'You offer some rations. The cub accepts warily, then bounds away.',
                'capture': 'You attempt to catch the cub, but it escapes into the trees.',
                'ignore': 'You leave the creature in peace and continue on your path.'
            },
            'loot_chance': 0.1,  # Small chance of finding something
            'loot_items': ['nexu_fur_scraps', 'small_bones']
        },
        {
            'name': 'Force Firefly',
            'type': FaunaType.FORCE_SENSITIVE,
            'size': FaunaSize.TINY,
            'rarity': 0.04,
            'description': 'Glowing insects that pulse with Force energy.',
            'force_reaction': {
                'light': 'The fireflies swirl around you in beautiful patterns, drawn to your light.',
                'balanced': 'The fireflies flicker in neutral colors, reflecting your balanced nature.',
                'dark': 'The fireflies glow deep red, their light corrupted by your dark presence.'
            },
            'interactions': {
                'meditate': 'You meditate among the fireflies, feeling the Force flow through them.',
                'capture': 'You carefully capture some fireflies in a container.',
                'follow': 'You follow the fireflies deeper into the forest.',
                'ignore': 'You continue past the dancing lights.'
            },
            'force_bonus': 5,  # Restores Force points if treated well
            'loot_items': ['force_essence', 'glowing_dust']
        },
        {
            'name': 'Corrupted Vine Cat',
            'type': FaunaType.CORRUPTED,
            'size': FaunaSize.MEDIUM,
            'rarity': 0.03,
            'description': 'Once a graceful forest predator, now twisted by dark side energy.',
            'force_reaction': {
                'light': 'The creature writhes in pain at your presence, the light causing it agony.',
                'balanced': 'The creature regards you with confusion, as if trying to remember something.',
                'dark': 'The creature recognizes a kindred darkness and approaches submissively.'
            },
            'interactions': {
                'heal': 'You attempt to cleanse the dark side corruption with Force healing.',
                'dominate': 'You use the dark side to command the corrupted creature.',
                'fight': 'You engage the twisted creature in combat.',
                'flee': 'You retreat from the dangerous predator.'
            },
            'combat_stats': {'hp': 45, 'attack': 12, 'defense': 8},
            'loot_items': ['corrupted_claws', 'dark_crystal_shard', 'tainted_fur']
        }
    ],
    'desert': [
        {
            'name': 'Dewback',
            'type': FaunaType.PASSIVE,
            'size': FaunaSize.LARGE,
            'rarity': 0.12,
            'description': 'A massive, slow-moving reptile adapted to desert life.',
            'force_reaction': {
                'light': 'The dewback seems calm and trusting in your presence.',
                'balanced': 'The dewback ignores you, focused on foraging.',
                'dark': 'The dewback becomes agitated and moves away from you.'
            },
            'interactions': {
                'ride': 'You attempt to mount the dewback for faster desert travel.',
                'follow': 'You follow the dewback, hoping it knows where to find water.',
                'harvest': 'You collect dewback scales and other useful materials.',
                'rest': 'You rest in the shade provided by the massive creature.'
            },
            'travel_bonus': True,  # Can provide faster movement
            'loot_items': ['dewback_scales', 'desert_moss', 'water_sac']
        },
        {
            'name': 'Sand Wraith',
            'type': FaunaType.FORCE_SENSITIVE,
            'size': FaunaSize.MEDIUM,
            'rarity': 0.02,
            'description': 'A ghostly creature born from the desert\'s Force energy.',
            'force_reaction': {
                'light': 'The wraith glows with silver light, offering cryptic guidance.',
                'balanced': 'The wraith flickers between light and shadow, watching silently.',
                'dark': 'The wraith turns blood red, whispering of power and conquest.'
            },
            'interactions': {
                'communicate': 'You reach out through the Force to understand the wraith.',
                'banish': 'You attempt to dispel the Force apparition.',
                'absorb': 'You try to drain the wraith\'s energy for your own power.',
                'learn': 'You ask the wraith to share ancient desert wisdom.'
            },
            'force_bonus': 10,
            'knowledge_reward': True,  # Can teach Force abilities
            'loot_items': ['force_echo', 'ancient_knowledge', 'spirit_essence']
        }
    ],
    'rocky': [
        {
            'name': 'Crystal Spider',
            'type': FaunaType.NEUTRAL,
            'size': FaunaSize.SMALL,
            'rarity': 0.07,
            'description': 'Arachnids that have evolved crystalline exoskeletons.',
            'force_reaction': {
                'light': 'The spider\'s crystals glow warmly, creating beautiful light patterns.',
                'balanced': 'The spider\'s crystals remain clear and neutral.',
                'dark': 'The spider\'s crystals turn dark purple, pulsing with malevolent energy.'
            },
            'interactions': {
                'harvest': 'You carefully collect shed crystal fragments.',
                'study': 'You observe how the crystals focus Force energy.',
                'disturb': 'You provoke the spider to see how it reacts.',
                'protect': 'You shield the spider from other predators.'
            },
            'loot_items': ['crystal_fragments', 'force_focusing_crystal', 'spider_silk']
        },
        {
            'name': 'Rock Burrower',
            'type': FaunaType.PASSIVE,
            'size': FaunaSize.MEDIUM,
            'rarity': 0.10,
            'description': 'A heavily armored creature that tunnels through solid rock.',
            'force_reaction': {
                'light': 'The burrower emerges peacefully, trusting your intentions.',
                'balanced': 'The burrower watches you cautiously from its tunnel.',
                'dark': 'The burrower retreats deep underground, sensing danger.'
            },
            'interactions': {
                'follow': 'You follow the burrower\'s tunnels, hoping to find shelter.',
                'trade': 'You offer the burrower metal scraps in exchange for passage.',
                'mine': 'You help the burrower excavate, sharing what you find.',
                'block': 'You seal the tunnel to trap the creature.'
            },
            'shelter_bonus': True,  # Can provide protection from storms
            'loot_items': ['rare_minerals', 'tunnel_moss', 'stone_tools']
        }
    ],
    'plains': [
        {
            'name': 'Grass Runner',
            'type': FaunaType.PASSIVE,
            'size': FaunaSize.SMALL,
            'rarity': 0.22,
            'description': 'Swift herbivores that move in herds across the grasslands.',
            'force_reaction': {
                'light': 'The herd approaches without fear, sensing your peaceful nature.',
                'balanced': 'The herd maintains distance but doesn\'t flee.',
                'dark': 'The herd scatters in terror at your dark presence.'
            },
            'interactions': {
                'hunt': 'You attempt to catch one of the grass runners for food.',
                'herd': 'You use Force persuasion to guide the herd\'s movement.',
                'protect': 'You defend the herd from predators.',
                'study': 'You observe their behavior patterns.'
            },
            'food_value': 15,  # Can provide sustenance
            'loot_items': ['fresh_meat', 'hide_scraps', 'bone_tools']
        },
        {
            'name': 'Storm Hawk',
            'type': FaunaType.NEUTRAL,
            'size': FaunaSize.SMALL,
            'rarity': 0.14,
            'description': 'Majestic birds that can predict weather changes.',
            'force_reaction': {
                'light': 'The hawk circles overhead, its cries seeming to offer guidance.',
                'balanced': 'The hawk observes you from afar, neither hostile nor friendly.',
                'dark': 'The hawk\'s cries become harsh and threatening.'
            },
            'interactions': {
                'tame': 'You attempt to befriend the storm hawk.',
                'follow': 'You track the hawk to learn about weather patterns.',
                'message': 'You try to send a message with the hawk.',
                'hunt': 'You attempt to bring down the bird.'
            },
            'weather_prediction': True,  # Warns of incoming atmospheric events
            'loot_items': ['storm_feathers', 'weather_crystals', 'wind_essence']
        }
    ],
    'river': [
        {
            'name': 'Force Fish',
            'type': FaunaType.FORCE_SENSITIVE,
            'size': FaunaSize.SMALL,
            'rarity': 0.20,
            'description': 'Luminescent fish that glow with Force sensitivity.',
            'force_reaction': {
                'light': 'The fish swim in harmonious patterns around you.',
                'balanced': 'The fish glow with steady, peaceful light.',
                'dark': 'The fish pulse with angry red light and flee downstream.'
            },
            'interactions': {
                'fish': 'You attempt to catch some of the Force fish.',
                'commune': 'You reach out through the Force to connect with the fish.',
                'purify': 'You cleanse the water to help the fish thrive.',
                'corrupt': 'You taint the water with dark side energy.'
            },
            'force_bonus': 8,
            'loot_items': ['force_fish_scales', 'pure_water', 'aquatic_plants']
        },
        {
            'name': 'Mire Cat',
            'type': FaunaType.NEUTRAL,
            'size': FaunaSize.MEDIUM,
            'rarity': 0.11,
            'description': 'Amphibious predators that hunt along riverbanks.',
            'force_reaction': {
                'light': 'The mire cat approaches cautiously, sensing no threat.',
                'balanced': 'The mire cat watches you warily from the water.',
                'dark': 'The mire cat hisses and prepares to attack.'
            },
            'interactions': {
                'avoid': 'You give the predator a wide berth.',
                'intimidate': 'You use the Force to frighten the mire cat away.',
                'befriend': 'You attempt to gain the creature\'s trust.',
                'challenge': 'You face the mire cat in direct combat.'
            },
            'combat_stats': {'hp': 35, 'attack': 10, 'defense': 6},
            'loot_items': ['mire_cat_claws', 'waterproof_hide', 'river_stones']
        }
    ],
    'mountain_pass': [
        {
            'name': 'Ice Crawler',
            'type': FaunaType.AGGRESSIVE,
            'size': FaunaSize.MEDIUM,
            'rarity': 0.09,
            'description': 'Insectoid creatures adapted to high-altitude cold.',
            'force_reaction': {
                'light': 'The crawler\'s aggression lessens slightly in your calming presence.',
                'balanced': 'The crawler regards you as a potential threat.',
                'dark': 'The crawler becomes even more vicious, feeding on your darkness.'
            },
            'interactions': {
                'fight': 'You engage the ice crawler in combat.',
                'evade': 'You attempt to sneak past the territorial creature.',
                'dominate': 'You use dark side powers to control the crawler.',
                'reason': 'You try to communicate using the Force.'
            },
            'combat_stats': {'hp': 40, 'attack': 14, 'defense': 10},
            'loot_items': ['ice_crawler_chitin', 'frost_crystals', 'alpine_herbs']
        },
        {
            'name': 'Wind Spirit',
            'type': FaunaType.FORCE_SENSITIVE,
            'size': FaunaSize.TINY,
            'rarity': 0.07,
            'description': 'Ethereal beings made of mountain wind and Force energy.',
            'force_reaction': {
                'light': 'The spirit dances joyfully around you, creating gentle breezes.',
                'balanced': 'The spirit hovers nearby, curious but cautious.',
                'dark': 'The spirit becomes a howling gale, expressing its distress.'
            },
            'interactions': {
                'meditate': 'You meditate with the wind spirit to understand its nature.',
                'bind': 'You attempt to trap the spirit for your own purposes.',
                'release': 'You help the spirit find peace and move on.',
                'learn': 'You ask the spirit to teach you about the mountains.'
            },
            'force_bonus': 12,
            'altitude_adaptation': True,  # Helps with mountain travel
            'loot_items': ['wind_essence', 'mountain_wisdom', 'spiritual_energy']
        }
    ],
    'tomb': [
        {
            'name': 'Sith Wraith',
            'type': FaunaType.CORRUPTED,
            'size': FaunaSize.MEDIUM,
            'rarity': 0.12,
            'description': 'The tortured soul of an ancient Sith apprentice.',
            'force_reaction': {
                'light': 'The wraith writhes in agony, your light causing it great pain.',
                'balanced': 'The wraith regards you with confusion and longing.',
                'dark': 'The wraith bows before you, recognizing your dark power.'
            },
            'interactions': {
                'banish': 'You attempt to send the wraith to the afterlife.',
                'communicate': 'You try to speak with the ancient spirit.',
                'dominate': 'You bind the wraith to serve your will.',
                'learn': 'You seek ancient Sith knowledge from the wraith.'
            },
            'combat_stats': {'hp': 30, 'attack': 8, 'defense': 12},  # Hard to hit
            'knowledge_reward': True,
            'loot_items': ['sith_essence', 'ancient_holocron_fragment', 'spectral_energy']
        },
        {
            'name': 'Tomb Bat Swarm',
            'type': FaunaType.NEUTRAL,
            'size': FaunaSize.SMALL,
            'rarity': 0.16,
            'description': 'Colonies of bats that have lived in the tombs for centuries.',
            'force_reaction': {
                'light': 'The bats remain calm, your peaceful aura not disturbing them.',
                'balanced': 'The bats chittle nervously but don\'t attack.',
                'dark': 'The bats become agitated and aggressive.'
            },
            'interactions': {
                'calm': 'You use the Force to soothe the bat colony.',
                'follow': 'You follow the bats to find hidden passages.',
                'disturb': 'You provoke the bats into a frenzy.',
                'study': 'You observe how the bats navigate in complete darkness.'
            },
            'navigation_bonus': True,  # Can reveal secret passages
            'loot_items': ['bat_guano', 'echo_crystals', 'darkness_essence']
        },
        {
            'name': 'Dark Side Manifestation',
            'type': FaunaType.FORCE_SENSITIVE,
            'size': FaunaSize.MASSIVE,
            'rarity': 0.03,  # Very rare
            'description': 'A terrifying embodiment of pure dark side energy.',
            'force_reaction': {
                'light': 'The manifestation recoils from your light, but grows more aggressive.',
                'balanced': 'The manifestation tests your resolve, seeking weakness.',
                'dark': 'The manifestation merges partially with your darkness.'
            },
            'interactions': {
                'resist': 'You fight against the manifestation\'s corruption.',
                'embrace': 'You allow the manifestation to merge with you.',
                'banish': 'You attempt to destroy the dark side entity.',
                'negotiate': 'You try to bargain with the manifestation.'
            },
            'corruption_risk': 20,  # High chance to corrupt player
            'power_reward': 25,    # But offers great power if embraced
            'combat_stats': {'hp': 100, 'attack': 20, 'defense': 5},
            'loot_items': ['pure_dark_crystal', 'sith_holocron', 'power_essence']
        }
    ]
}


class FaunaEncounter:
    def __init__(self, fauna_data, biome):
        self.fauna_data = fauna_data
        self.biome = biome
        self.name = fauna_data['name']
        self.type = fauna_data['type']
        self.size = fauna_data['size']
        self.description = fauna_data['description']

    def get_taunt(self, event):
        """Return an animalistic emote/sound for this fauna, based on event (attack, roam, death, etc)."""
        taunt_bank = FAUNA_TAUNTS.get(self.name.lower().replace(' ', '_'), {})
        event_taunts = taunt_bank.get(event, [])
        if event_taunts:
            return random.choice(event_taunts)
        return "*the creature makes an unrecognizable sound*"

    def get_force_reaction(self, player_alignment):
        """Get the creature's reaction based on player's Force alignment."""
        reactions = self.fauna_data.get('force_reaction', {})
        if player_alignment <= -15:
            return reactions.get('dark', 'The creature senses your dark presence.')
        elif player_alignment >= 15:
            return reactions.get('light', 'The creature is calmed by your light.')
        else:
            return reactions.get('balanced', 'The creature regards you neutrally.')

    def get_available_interactions(self):
        """Return list of possible interactions with this creature."""
        return list(self.fauna_data.get('interactions', {}).keys())

    def perform_interaction(self, interaction_type, game):
        """Execute an interaction and return the result."""
        interactions = self.fauna_data.get('interactions', {})
        if interaction_type not in interactions:
            return "You cannot perform that interaction with this creature."
        result = interactions[interaction_type]
        # Apply any special effects based on interaction
        self._apply_interaction_effects(interaction_type, game)
        return result

    def _apply_interaction_effects(self, interaction_type, game):
        """Apply game effects based on the interaction chosen."""
        player = game.player
        # Hostile interactions spawn the creature as an enemy
        if interaction_type in ['fight', 'hunt', 'challenge', 'disturb', 'attack', 'provoke']:
            combat_stats = self.fauna_data.get('combat_stats')
            if combat_stats:
                self._spawn_fauna_enemy(game, combat_stats)
                return  # Enemy will provide loot on defeat
        
        # Force bonuses for positive interactions
        if interaction_type in ['meditate', 'commune', 'heal', 'protect', 'learn', 'follow']:
            force_bonus = self.fauna_data.get('force_bonus', 0)
            if hasattr(player, 'force_energy') and force_bonus > 0:
                player.force_energy = min(
                    player.max_force_energy,
                    player.force_energy + force_bonus
                )
                game.ui.messages.add(f"Force energy restored! (+{force_bonus})")
        
        # Corruption effects for dark interactions
        if interaction_type in ['dominate', 'corrupt', 'absorb', 'embrace', 'bind']:
            corruption_risk = self.fauna_data.get('corruption_risk', 5)
            if hasattr(player, 'dark_corruption'):
                player.dark_corruption = min(100, player.dark_corruption + corruption_risk)
                game.ui.messages.add(f"The dark side's grip tightens... (+{corruption_risk} corruption)")
            # Grant dark XP for dark interactions
            if hasattr(player, 'dark_xp'):
                player.dark_xp += 5
                game.ui.messages.add("Dark XP gained! (+5)")
        
        # Light side XP for compassionate interactions
        if interaction_type in ['heal', 'release', 'purify', 'protect', 'befriend', 'calm']:
            if hasattr(player, 'light_xp'):
                player.light_xp += 5
                game.ui.messages.add("Light XP gained! (+5)")
        
        # Loot rewards for non-hostile gathering
        if interaction_type in ['harvest', 'fish', 'gather', 'collect']:
            self._grant_loot(game)
        
        # Knowledge rewards
        if interaction_type == 'learn' and self.fauna_data.get('knowledge_reward'):
            self._grant_knowledge(game)
    
    def _spawn_fauna_enemy(self, game, combat_stats):
        """Spawn the fauna creature as an enemy for combat."""
        try:
            from jedi_fugitive.game.enemy import Enemy, EnemyType
            
            # Create enemy near player
            spawn_x = game.player.x + random.randint(-2, 2)
            spawn_y = game.player.y + random.randint(-2, 2)
            
            # Ensure spawn location is valid
            if (0 <= spawn_x < len(game.game_map[0]) and
                0 <= spawn_y < len(game.game_map) and
                game.game_map[spawn_y][spawn_x] == '.'):
                
                # Create enemy with fauna stats
                enemy = Enemy(
                    name=self.name,
                    hp=combat_stats.get('hp', 30),
                    attack=combat_stats.get('attack', 10),
                    defense=combat_stats.get('defense', 5),
                    enemy_type=EnemyType.FAUNA,
                    x=spawn_x,
                    y=spawn_y
                )
                
                # Set loot drops
                if hasattr(enemy, 'loot_table'):
                    enemy.loot_table = self.fauna_data.get('loot_items', [])
                
                game.enemies.append(enemy)
                game.ui.messages.add(f"#1#The {self.name} attacks!#0#")
            else:
                # Fallback: spawn at player location + 1
                enemy = Enemy(
                    name=self.name,
                    hp=combat_stats.get('hp', 30),
                    attack=combat_stats.get('attack', 10),
                    defense=combat_stats.get('defense', 5),
                    enemy_type=EnemyType.FAUNA,
                    x=game.player.x + 1,
                    y=game.player.y
                )
                game.enemies.append(enemy)
                game.ui.messages.add(f"#1#The {self.name} attacks!#0#")
        except Exception as e:
            game.ui.messages.add(f"Combat with {self.name} initiated! (spawn failed: {e})")
    
    def _grant_loot(self, game):
        """Grant loot items from the creature."""
        loot_chance = self.fauna_data.get('loot_chance', 0.3)
        if random.random() < loot_chance:
            loot_items = self.fauna_data.get('loot_items', [])
            if loot_items:
                item_name = random.choice(loot_items)
                # Create proper item object for crafting material
                item_obj = self._create_fauna_item(item_name)
                
                # Add to player inventory
                try:
                    if hasattr(game.player, 'inventory'):
                        game.player.inventory.append(item_obj)
                        game.ui.messages.add(f"You found: {item_obj['name']}")
                    else:
                        game.ui.messages.add(f"You found: {item_name.replace('_', ' ').title()}")
                except Exception as e:
                    try:
                        game.ui.messages.add(f"You found: {item_name.replace('_', ' ').title()}")
                    except:
                        pass
    
    def _grant_knowledge(self, game):
        """Grant player knowledge/information from interacting with creature."""
        try:
            knowledge_messages = [
                f"The {self.name} shares ancient wisdom through the Force.",
                f"You learn secrets about navigating this region from the {self.name}.",
                f"The creature reveals hidden paths and dangers through Force communion.",
                f"Through the Force, you understand the {self.name}'s perspective on this place."
            ]
            game.ui.messages.add(f"#3#{random.choice(knowledge_messages)}#0#")
            
            # Small light XP bonus for learning
            if hasattr(game.player, 'light_xp'):
                game.player.light_xp += 10
                game.ui.messages.add("Wisdom gained! (+10 Light XP)")
        except Exception:
            pass
    
    def _create_fauna_item(self, item_name):
        """Create a fauna material item for the inventory."""
        # Mapping of fauna items to proper materials
        fauna_materials = {
            'nexu_fur_scraps': {
                'name': 'Nexu Fur Scraps',
                'type': 'material',
                'material_type': 'Common Organic',
                'rarity': 'Common',
                'description': 'Tough fur from a nexu. Useful for crafting.',
                'value': 15
            },
            'small_bones': {
                'name': 'Small Bones',
                'type': 'material',
                'material_type': 'Common Organic',
                'rarity': 'Common',
                'description': 'Small animal bones. Can be carved into tools.',
                'value': 10
            },
            'force_essence': {
                'name': 'Force Essence',
                'type': 'material',
                'material_type': 'Force Crystal',
                'rarity': 'Rare',
                'description': 'Crystallized Force energy. Valuable for Force items.',
                'value': 50
            },
            'glowing_dust': {
                'name': 'Glowing Dust',
                'type': 'material',
                'material_type': 'Force Crystal',
                'rarity': 'Uncommon',
                'description': 'Luminescent particles infused with Force energy.',
                'value': 25
            },
            'corrupted_claws': {
                'name': 'Corrupted Claws',
                'type': 'material',
                'material_type': 'Dark Side Material',
                'rarity': 'Rare',
                'description': 'Claws twisted by dark side energy. Dangerous to handle.',
                'value': 40
            },
            'dark_crystal_shard': {
                'name': 'Dark Crystal Shard',
                'type': 'material',
                'material_type': 'Dark Side Crystal',
                'rarity': 'Rare',
                'description': 'A shard of dark side crystal. Pulses with malevolent energy.',
                'value': 60
            },
            'tainted_fur': {
                'name': 'Tainted Fur',
                'type': 'material',
                'material_type': 'Dark Side Material',
                'rarity': 'Uncommon',
                'description': 'Fur corrupted by dark side exposure. Still has uses.',
                'value': 30
            },
            'dewback_scales': {
                'name': 'Dewback Scales',
                'type': 'material',
                'material_type': 'Common Organic',
                'rarity': 'Common',
                'description': 'Tough scales from a dewback. Good for armor crafting.',
                'value': 20
            },
            'desert_moss': {
                'name': 'Desert Moss',
                'type': 'material',
                'material_type': 'Common Organic',
                'rarity': 'Common',
                'description': 'Hardy moss that survives in harsh conditions.',
                'value': 5
            },
            'water_sac': {
                'name': 'Water Sac',
                'type': 'material',
                'material_type': 'Common Organic',
                'rarity': 'Common',
                'description': 'Natural water storage organ. Can be processed.',
                'value': 12
            }
        }
        
        # Get material data or create generic item
        material_data = fauna_materials.get(item_name, {
            'name': item_name.replace('_', ' ').title(),
            'type': 'material',
            'material_type': 'Unknown Organic',
            'rarity': 'Common',
            'description': 'An organic material from local fauna.',
            'value': 10
        })
        
        return material_data
    
    def _grant_knowledge(self, game):
        """Grant Force knowledge or abilities."""
        try:
            game.ui.messages.add("The creature shares ancient wisdom with you!")
            # Could unlock new Force abilities or provide permanent bonuses
        except:
            pass

class FaunaManager:
    def __init__(self, game):
        self.game = game
        self.active_encounters = {}  # Track ongoing encounters
        self.last_encounter_turn = 0
    
    def check_fauna_encounter(self, biome):
        """Check if a fauna encounter should occur in the current biome."""
        # Don't trigger encounters too frequently
        if self.game.turn_count - self.last_encounter_turn < 150:
            return None
        
        fauna_list = BIOME_FAUNA.get(biome, [])
        if not fauna_list:
            return None
        
        # Roll for encounter with heavily reduced overall frequency
        for fauna_data in fauna_list:
            # Apply global 0.2x multiplier to make all fauna encounters much less frequent
            if random.random() < (fauna_data['rarity'] * 0.2):
                self.last_encounter_turn = self.game.turn_count
                return FaunaEncounter(fauna_data, biome)
        
        return None
    
    def trigger_fauna_encounter(self, encounter):
        """Initiate a fauna encounter."""
        try:
            # Get player's alignment for creature reaction
            player_alignment = getattr(self.game.player, 'alignment_score', 0)
            
            # Set encounter location near player
            encounter.location_x = getattr(self.game.player, 'x', 0)
            encounter.location_y = getattr(self.game.player, 'y', 0)
            
            # Use popup menu for fauna encounter
            self._show_fauna_encounter_popup(encounter, player_alignment)
            
            # Log encounter in journal
            self._log_fauna_encounter(encounter, player_alignment)
            
            # Store encounter for interaction handling
            encounter_key = f"{encounter.name}_{self.game.turn_count}"
            self.active_encounters[encounter_key] = encounter
            
        except Exception as e:
            pass  # Silent fail to avoid breaking game flow
    
    def handle_fauna_interaction(self, interaction_type, encounter_key):
        """Handle player interaction with a fauna encounter."""
        if encounter_key not in self.active_encounters:
            return "No active fauna encounter found."
        
        encounter = self.active_encounters[encounter_key]
        result = encounter.perform_interaction(interaction_type, self.game)
        
        # Log interaction in journal
        self._log_fauna_interaction(encounter, interaction_type, result)
        
        # Remove encounter after interaction
        del self.active_encounters[encounter_key]
        
        return result
    
    def _log_fauna_encounter(self, encounter, player_alignment):
        """Log fauna encounter in enhanced journal."""
        try:
            from jedi_fugitive.game.hero_journal import create_fauna_entry
            
            biome = getattr(self.game, 'current_biome', 'unknown')
            alignment_desc = "light" if player_alignment > 15 else "dark" if player_alignment < -15 else "balanced"
            
            # Create enhanced entry text with alignment perspective
            encounter_text = f"Discovered {encounter.name} in the {biome}. {encounter.description}"
            
            if alignment_desc == "light":
                reflection = "The Force flows through all living things. Even here, life finds a way to flourish."
            elif alignment_desc == "dark":
                reflection = "Another piece on the board. Every creature serves its purpose in the grand design."
            else:
                reflection = "In this harsh world, we all struggle to survive. I wonder what stories this creature could tell."
            
            full_entry = f"{encounter_text} {reflection}"
            
            # Use enhanced journal system
            create_fauna_entry(encounter.name, "observe", full_entry, 
                             self.game.player, self.game.turn_count)
        except Exception:
            # Fallback to simple entry
            try:
                entry = f"[FAUNA] Encountered {encounter.name} in the {getattr(self.game, 'current_biome', 'unknown')}."
                self.game.player.add_log_entry(entry, self.game.turn_count)
            except Exception:
                pass
    
    def _log_fauna_interaction(self, encounter, interaction_type, result):
        """Log fauna interaction result in enhanced journal."""
        try:
            from jedi_fugitive.game.hero_journal import create_fauna_entry
            
            # Create enhanced interaction entry
            create_fauna_entry(encounter.name, interaction_type, result, 
                             self.game.player, self.game.turn_count)
        except Exception:
            # Fallback to simple entry
            try:
                entry = f"[FAUNA] {interaction_type.title()} with {encounter.name}: {result}"
                self.game.player.add_log_entry(entry, self.game.turn_count)
            except Exception:
                pass

    def _show_fauna_encounter_popup(self, encounter, player_alignment):
        """Show fauna encounter in a popup menu with clear action options."""
        try:
            # Check if UI menu is available
            if not hasattr(self.game.ui, 'centered_menu') or not callable(self.game.ui.centered_menu):
                # Fallback to message system
                self.game.ui.messages.add(f"#6#[FAUNA]#0# You encounter: {encounter.name} (popup menu not available)")
                return
            
            # Get Force reaction
            reaction = encounter.get_force_reaction(player_alignment)
            
            # First, show the encounter description in a simple popup
            description_popup = [
                encounter.description,
                "",
                reaction,
                "",
                "Press any key to choose your action..."
            ]
            
            # Show description popup
            self.game.ui.centered_menu(
                description_popup,
                f"Fauna Encounter: {encounter.name}"
            )
            
            # Now show ONLY the action choices in a clean menu
            interactions = encounter.get_available_interactions()
            action_menu = []
            
            # Build clean action menu with only selectable options
            for i, interaction in enumerate(interactions[:5]):  # Max 5 interactions
                action_name = interaction.title().replace('_', ' ')
                action_menu.append(f"{action_name}")
            
            action_menu.append("Back away quietly")
            
            # Show action selection menu
            choice = self.game.ui.centered_menu(
                action_menu, 
                "Choose Your Action"
            )
            
            # Handle the choice - now choice index directly corresponds to actions
            if choice is not None:
                if 0 <= choice < len(interactions):
                    # User chose a specific interaction
                    interaction_type = list(interactions)[choice]
                    encounter_key = f"{encounter.name}_{self.game.turn_count}"
                    self.active_encounters[encounter_key] = encounter
                    
                    try:
                        result = self.handle_fauna_interaction(interaction_type, encounter_key)
                        self.game.ui.messages.add(f"#6#[FAUNA]#0# {result}")
                    except Exception as e:
                        self.game.ui.messages.add(f"Fauna interaction failed: {e}")
                elif choice == len(interactions):
                    # User chose to back away
                    self.game.ui.messages.add(f"#6#[FAUNA]#0# You quietly back away from the {encounter.name}.")
                else:
                    # Invalid choice
                    self.game.ui.messages.add(f"#6#[FAUNA]#0# You decide not to interact with the {encounter.name}.")
            else:
                # No choice made or cancelled
                self.game.ui.messages.add(f"#6#[FAUNA]#0# You observe the {encounter.name} from a distance.")
                
        except Exception as e:
            # Enhanced fallback with error info
            try:
                self.game.ui.messages.add(f"#6#[FAUNA]#0# You encounter: {encounter.name}")
                self.game.ui.messages.add(f"Fauna popup error: {e}")
            except:
                pass

def get_fauna_for_biome(biome):
    """Get all possible fauna for a specific biome."""
    return BIOME_FAUNA.get(biome, [])

def get_fauna_interaction_description(fauna_name, interaction):
    """Get descriptive text for a specific fauna interaction."""
    for biome_fauna in BIOME_FAUNA.values():
        for fauna_data in biome_fauna:
            if fauna_data['name'] == fauna_name:
                return fauna_data.get('interactions', {}).get(interaction, "Unknown interaction.")
    return "Fauna not found."