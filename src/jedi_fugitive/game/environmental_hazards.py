"""
Environmental hazards system - lava pools, acid rain, radiation zones, etc.
"""
import random

# Hazard tile definitions
HAZARD_TILES = {
    'lava_pool': {
        'symbol': '~',
        'color': 'red',  # Will be mapped to color pair
        'damage_min': 10,
        'damage_max': 20,
        'effect': 'burning',
        'effect_duration': 3,
        'message_enter': "You step into molten lava! Your armor sizzles and burns!",
        'message_burning': "The burning continues! (-{damage} HP)",
        'spawn_biomes': ['volcanic', 'rocky'],
        'spawn_chance': 0.05,
    },
    'acid_pool': {
        'symbol': '≈',
        'color': 'green',
        'damage_min': 8,
        'damage_max': 15,
        'effect': 'corroding',
        'effect_duration': 4,
        'message_enter': "You splash through caustic acid! It burns through your equipment!",
        'message_corroding': "The acid continues to corrode! (-{damage} HP, -{armor} armor)",
        'spawn_biomes': ['wasteland', 'toxic'],
        'spawn_chance': 0.04,
    },
    'radiation_zone': {
        'symbol': '☢',
        'color': 'yellow',
        'damage_min': 3,
        'damage_max': 8,
        'effect': 'radiation_sickness',
        'effect_duration': 10,
        'max_hp_reduction': 1,
        'message_enter': "You feel sick from intense radiation exposure!",
        'message_radiation': "Radiation sickness worsens! (-{damage} HP, -{max_hp} max HP)",
        'spawn_biomes': ['wasteland', 'nuclear'],
        'spawn_chance': 0.03,
    },
    'ice_patch': {
        'symbol': '∴',
        'color': 'cyan',
        'damage_min': 2,
        'damage_max': 5,
        'effect': 'frozen',
        'effect_duration': 2,
        'evasion_penalty': 15,
        'message_enter': "You slip on ice! Your movements are hindered!",
        'message_frozen': "Still slowed by ice! (Evasion -{evasion}%)",
        'spawn_biomes': ['arctic', 'frozen'],
        'spawn_chance': 0.06,
    },
    'spike_trap': {
        'symbol': '^',
        'color': 'white',
        'damage_min': 15,
        'damage_max': 25,
        'effect': 'bleeding',
        'effect_duration': 5,
        'message_enter': "Hidden spikes pierce your legs!",
        'message_bleeding': "You're bleeding! (-{damage} HP per turn)",
        'spawn_biomes': ['tomb', 'ruins'],
        'spawn_chance': 0.02,
    },
}

# Atmospheric hazards (affect entire map region)
ATMOSPHERIC_HAZARDS = {
    'acid_rain': {
        'name': 'Acid Rain Storm',
        'damage_per_turn': 2,
        'duration_min': 30,
        'duration_max': 60,
        'message_start': "⚠ A storm of acid rain begins to fall! Seek shelter or suffer burns!",
        'message_ongoing': "Acid rain burns exposed skin! (-2 HP)",
        'message_end': "The acid rain storm passes.",
        'spawn_biomes': ['wasteland', 'toxic'],
        'spawn_chance': 0.01,  # 1% per turn
    },
    'dust_storm': {
        'name': 'Blinding Dust Storm',
        'visibility_reduction': 50,  # Reduce visibility radius by 50%
        'accuracy_penalty': 20,
        'duration_min': 40,
        'duration_max': 80,
        'message_start': "⚠ A massive dust storm engulfs the area! Visibility near zero!",
        'message_ongoing': "Dust obscures everything! (Accuracy -20%, Vision reduced)",
        'message_end': "The dust storm clears.",
        'spawn_biomes': ['desert', 'wasteland'],
        'spawn_chance': 0.015,
    },
    'radiation_storm': {
        'name': 'Radiation Storm',
        'damage_per_turn': 5,
        'force_drain': 3,
        'duration_min': 20,
        'duration_max': 40,
        'message_start': "⚠ WARNING: Intense radiation storm detected! Take cover immediately!",
        'message_ongoing': "Radiation sears through you! (-5 HP, -3 Force)",
        'message_end': "Radiation levels return to normal.",
        'spawn_biomes': ['wasteland', 'nuclear'],
        'spawn_chance': 0.008,
    },
}

class HazardManager:
    """Manages environmental hazards on the map."""
    
    def __init__(self, game):
        self.game = game
        self.hazard_tiles = {}  # (x, y) -> hazard_type
        self.active_atmospheric = []  # List of active atmospheric hazards
        self.player_effects = {}  # effect_type -> turns_remaining
    
    def spawn_hazards_on_map(self):
        """Spawn environmental hazards across the map based on biome."""
        try:
            map_h = len(self.game.game_map)
            map_w = len(self.game.game_map[0]) if map_h > 0 else 0
            biomes = getattr(self.game, 'map_biomes', None)
            
            if not biomes:
                return
            
            hazards_spawned = 0
            
            for y in range(map_h):
                for x in range(map_w):
                    # Don't spawn on player, enemies, or items
                    if (x, y) == (self.game.player.x, self.game.player.y):
                        continue
                    
                    # Check biome
                    try:
                        biome = biomes[y][x]
                    except:
                        continue
                    
                    # Try to spawn hazards based on biome
                    for hazard_type, hazard_data in HAZARD_TILES.items():
                        if biome in hazard_data.get('spawn_biomes', []):
                            if random.random() < hazard_data.get('spawn_chance', 0.01):
                                # Check if tile is empty floor
                                try:
                                    from jedi_fugitive.game.level import Display
                                    if self.game.game_map[y][x] == getattr(Display, 'FLOOR', '.'):
                                        self.hazard_tiles[(x, y)] = hazard_type
                                        hazards_spawned += 1
                                except:
                                    pass
            
            if hazards_spawned > 0:
                try:
                    self.game.ui.messages.add(f"⚠ {hazards_spawned} environmental hazards detected across the map!")
                except:
                    pass
        except Exception as e:
            print(f"Error spawning hazards: {e}")
    
    def check_player_hazard(self):
        """Check if player is standing on a hazard tile and apply effects."""
        px = self.game.player.x
        py = self.game.player.y
        
        if (px, py) in self.hazard_tiles:
            hazard_type = self.hazard_tiles[(px, py)]
            hazard_data = HAZARD_TILES.get(hazard_type, {})
            
            # Deal damage
            damage = random.randint(
                hazard_data.get('damage_min', 5),
                hazard_data.get('damage_max', 10)
            )
            self.game.player.hp = max(0, self.game.player.hp - damage)
            
            # Show message
            try:
                message = hazard_data.get('message_enter', f'Environmental hazard! -{damage} HP')
                self.game.ui.messages.add(message.format(damage=damage))
            except:
                pass
            
            # Apply ongoing effect
            effect = hazard_data.get('effect')
            if effect:
                duration = hazard_data.get('effect_duration', 3)
                self.player_effects[effect] = duration
    
    def tick_effects(self):
        """Process ongoing status effects on player."""
        effects_to_remove = []
        
        for effect_type, turns_remaining in list(self.player_effects.items()):
            if turns_remaining <= 0:
                effects_to_remove.append(effect_type)
                continue
            
            # Apply effect damage/penalties
            if effect_type == 'burning':
                damage = random.randint(3, 8)
                self.game.player.hp = max(0, self.game.player.hp - damage)
                try:
                    self.game.ui.messages.add(f"🔥 Still burning! (-{damage} HP)")
                except:
                    pass
            
            elif effect_type == 'radiation_sickness':
                damage = random.randint(2, 5)
                self.game.player.hp = max(0, self.game.player.hp - damage)
                # Reduce max HP
                if random.random() < 0.3:  # 30% chance per turn
                    self.game.player.max_hp = max(10, self.game.player.max_hp - 1)
                    try:
                        self.game.ui.messages.add(f"☢ Radiation sickness! (-{damage} HP, -1 max HP)")
                    except:
                        pass
                else:
                    try:
                        self.game.ui.messages.add(f"☢ Radiation sickness! (-{damage} HP)")
                    except:
                        pass
            
            elif effect_type == 'bleeding':
                damage = random.randint(2, 6)
                self.game.player.hp = max(0, self.game.player.hp - damage)
                try:
                    self.game.ui.messages.add(f"💉 Bleeding! (-{damage} HP)")
                except:
                    pass
            
            # Decrement duration
            self.player_effects[effect_type] = turns_remaining - 1
        
        # Remove expired effects
        for effect_type in effects_to_remove:
            del self.player_effects[effect_type]
            try:
                self.game.ui.messages.add(f"[{effect_type} effect has worn off]")
            except:
                pass
    
    def tick_atmospheric(self):
        """Process atmospheric hazards."""
        hazards_to_remove = []
        
        for hazard in self.active_atmospheric:
            hazard['turns_remaining'] -= 1
            
            if hazard['turns_remaining'] <= 0:
                hazards_to_remove.append(hazard)
                try:
                    self.game.ui.messages.add(hazard['data'].get('message_end', 'Hazard ends.'))
                except:
                    pass
                continue
            
            # Apply effects
            data = hazard['data']
            
            # Damage per turn
            if 'damage_per_turn' in data:
                self.game.player.hp = max(0, self.game.player.hp - data['damage_per_turn'])
            
            # Force drain
            if 'force_drain' in data and hasattr(self.game.player, 'force_energy'):
                self.game.player.force_energy = max(0, self.game.player.force_energy - data['force_drain'])
            
            # Show ongoing message occasionally
            if hazard['turns_remaining'] % 5 == 0:
                try:
                    self.game.ui.messages.add(data.get('message_ongoing', 'Hazard continues!'))
                except:
                    pass
        
        # Remove expired hazards
        for hazard in hazards_to_remove:
            self.active_atmospheric.remove(hazard)
