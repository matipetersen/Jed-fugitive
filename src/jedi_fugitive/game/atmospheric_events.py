"""
Enhanced atmospheric events that affect gameplay mechanics.
Reduces visibility, affects movement, and adds environmental hazards.
"""
import random

# Atmospheric events that affect gameplay
ATMOSPHERIC_EVENTS = [
    {
        'name': 'Dark Side Storm',
        'description': 'Sith energy crackles through the air, distorting your vision.',
        'sith_description': 'The dark side flows through you like lightning in your veins.',
        'duration': 8,  # turns
        'effects': {
            'visibility_range': -2,
            'movement_cost': 1.2,
            'force_regen': -1,
            'dark_side_bonus': 2  # bonus for dark side players
        },
        'trigger_chance': 0.02,
        'biomes': ['tomb', 'mountain_pass', 'rocky']
    },
    {
        'name': 'Blinding Sandstorm',
        'description': 'Whirling sand reduces visibility to mere steps ahead.',
        'sith_description': 'The desert\'s fury masks your presence from prying eyes.',
        'duration': 6,
        'effects': {
            'visibility_range': -3,
            'movement_cost': 1.5,
            'accuracy': -15
        },
        'trigger_chance': 0.03,
        'biomes': ['desert']
    },
    {
        'name': 'Force Fog',
        'description': 'An ethereal mist fills with Force energy, clouding both sight and mind.',
        'sith_description': 'The mist whispers secrets of power to those who listen.',
        'duration': 10,
        'effects': {
            'visibility_range': -1,
            'force_regen': +2,
            'enemy_detection': -20  # enemies less likely to spot you
        },
        'trigger_chance': 0.015,
        'biomes': ['forest', 'river', 'plains']
    },
    {
        'name': 'Crushing Darkness',
        'description': 'Oppressive shadows weigh down your movements.',
        'sith_description': 'The darkness embraces you, lending weight to your presence.',
        'duration': 5,
        'effects': {
            'visibility_range': -2,
            'movement_cost': 1.3,
            'intimidation': +25,  # enemies more likely to flee
            'dark_side_protection': +10
        },
        'trigger_chance': 0.02,
        'biomes': ['tomb', 'rocky', 'mountain_pass']
    },
    {
        'name': 'Electrical Storm',
        'description': 'Lightning splits the sky, making electronics unreliable.',
        'sith_description': 'The storm\'s power resonates with your Force Lightning mastery.',
        'duration': 4,
        'effects': {
            'visibility_range': +1,  # lightning illuminates
            'blaster_malfunction': 0.15,  # chance for weapons to fail
            'force_lightning_boost': +20
        },
        'trigger_chance': 0.01,
        'biomes': ['plains', 'mountain_pass']
    },
    {
        'name': 'Temporal Flux',
        'description': 'Reality seems to shift and waver around you.',
        'sith_description': 'Time bends to your will as the dark side distorts reality.',
        'duration': 3,
        'effects': {
            'visibility_range': 0,  # surreal but clear
            'movement_cost': 0.8,  # easier movement through time flux
            'force_cost_reduction': 0.2,
            'confusion_chance': 0.1  # chance to move randomly
        },
        'trigger_chance': 0.008,
        'biomes': ['tomb']
    }
]

# Environmental hazards that can occur
ENVIRONMENTAL_HAZARDS = [
    {
        'name': 'Sith Wraiths',
        'description': 'Ghostly apparitions of ancient Sith materialize around you.',
        'effect': 'spawn_hostile_spirits',
        'trigger_alignment': 'light',  # more likely for light side players in tombs
        'trigger_chance': 0.03,
        'biomes': ['tomb']
    },
    {
        'name': 'Cave-in',
        'description': 'The ground trembles and debris falls from above.',
        'effect': 'block_passages',
        'damage_range': (5, 15),
        'trigger_chance': 0.015,
        'biomes': ['tomb', 'mountain_pass']
    },
    {
        'name': 'Quicksand',
        'description': 'The ground beneath your feet gives way.',
        'effect': 'movement_trap',
        'duration': 3,
        'trigger_chance': 0.02,
        'biomes': ['desert', 'river']
    },
    {
        'name': 'Force Nexus Overload',
        'description': 'Intense Force energy erupts from the ground.',
        'effect': 'force_drain_or_boost',
        'trigger_chance': 0.01,
        'biomes': ['tomb', 'forest']
    }
]

class AtmosphericEventManager:
    def __init__(self, game):
        self.game = game
        self.active_events = []
        self.last_event_turn = 0
        
    def update(self):
        """Update active atmospheric events and potentially trigger new ones."""
        # Update existing events
        self.update_active_events()
        
        # Check for new events
        self.check_new_events()
    
    def update_active_events(self):
        """Update duration of active events and remove expired ones."""
        for event in self.active_events[:]:  # copy list to avoid modification issues
            event['remaining_duration'] -= 1
            if event['remaining_duration'] <= 0:
                self.end_event(event)
                self.active_events.remove(event)
    
    def check_new_events(self):
        """Check if new atmospheric events should trigger."""
        current_biome = getattr(self.game, 'current_biome', 'crash_site')
        
        # Don't trigger events too frequently
        if self.game.turn_count - self.last_event_turn < 120:
            return
            
        # Check each potential event
        for event_template in ATMOSPHERIC_EVENTS:
            if current_biome not in event_template['biomes']:
                continue
                
            if random.random() < event_template['trigger_chance']:
                self.trigger_event(event_template)
                self.last_event_turn = self.game.turn_count
                break  # Only one event at a time
    
    def trigger_event(self, event_template):
        """Start a new atmospheric event."""
        event = event_template.copy()
        event['remaining_duration'] = event['duration']
        
        # Choose description based on player alignment
        player_alignment = getattr(self.game.player, 'alignment_score', 0)
        if player_alignment < -10 and 'sith_description' in event:
            description = event['sith_description']
            prefix = "#2#[DARK OMEN]#0#"
        else:
            description = event['description']
            prefix = "#5#[ATMOSPHERIC]#0#"
        
        self.active_events.append(event)
        
        try:
            self.game.ui.messages.add(f"{prefix} {event['name']}")
            self.game.ui.messages.add(f"   {description}")
            self.game.ui.messages.add(f"   Duration: {event['duration']} turns")
        except:
            pass
        
        self.apply_event_effects(event)
    
    def end_event(self, event):
        """End an atmospheric event and restore normal conditions."""
        try:
            self.game.ui.messages.add(f"🌤️ The {event['name']} subsides.")
        except:
            pass
        
        self.remove_event_effects(event)
    
    def apply_event_effects(self, event):
        """Apply the effects of an atmospheric event."""
        effects = event.get('effects', {})
        
        # Apply temporary modifiers to the game state
        if not hasattr(self.game, 'atmospheric_modifiers'):
            self.game.atmospheric_modifiers = {}
        
        for effect, value in effects.items():
            if effect not in self.game.atmospheric_modifiers:
                self.game.atmospheric_modifiers[effect] = 0
            self.game.atmospheric_modifiers[effect] += value
    
    def remove_event_effects(self, event):
        """Remove the effects of an atmospheric event."""
        effects = event.get('effects', {})
        
        if not hasattr(self.game, 'atmospheric_modifiers'):
            return
        
        for effect, value in effects.items():
            if effect in self.game.atmospheric_modifiers:
                self.game.atmospheric_modifiers[effect] -= value
                if self.game.atmospheric_modifiers[effect] == 0:
                    del self.game.atmospheric_modifiers[effect]
    
    def get_visibility_modifier(self):
        """Get the current visibility range modifier from atmospheric events."""
        if not hasattr(self.game, 'atmospheric_modifiers'):
            return 0
        return self.game.atmospheric_modifiers.get('visibility_range', 0)
    
    def get_movement_cost_modifier(self):
        """Get the current movement cost modifier from atmospheric events."""
        if not hasattr(self.game, 'atmospheric_modifiers'):
            return 1.0
        return self.game.atmospheric_modifiers.get('movement_cost', 1.0)
    
    def get_active_event_info(self):
        """Get information about currently active atmospheric events."""
        info = []
        for event in self.active_events:
            info.append({
                'name': event['name'],
                'remaining': event['remaining_duration'],
                'effects': event.get('effects', {})
            })
        return info

def should_trigger_environmental_hazard(game):
    """Check if an environmental hazard should trigger."""
    current_biome = getattr(game, 'current_biome', 'crash_site')
    
    for hazard in ENVIRONMENTAL_HAZARDS:
        if current_biome not in hazard['biomes']:
            continue
            
        # Check alignment-specific triggers
        if 'trigger_alignment' in hazard:
            player_alignment = getattr(game.player, 'alignment_score', 0)
            if hazard['trigger_alignment'] == 'light' and player_alignment < 5:
                continue
            elif hazard['trigger_alignment'] == 'dark' and player_alignment > -5:
                continue
        
        if random.random() < hazard['trigger_chance']:
            return hazard
    
    return None

def trigger_environmental_hazard(game, hazard):
    """Trigger an environmental hazard."""
    try:
        game.ui.messages.add(f"⚠️ [Hazard] {hazard['name']}")
        game.ui.messages.add(f"   {hazard['description']}")
        
        effect = hazard['effect']
        
        if effect == 'spawn_hostile_spirits':
            # Spawn wraith enemies near the player
            _spawn_sith_wraiths(game)
        elif effect == 'block_passages':
            # Cause cave-in damage and potentially block paths
            _trigger_cave_in(game, hazard)
        elif effect == 'movement_trap':
            # Trap player in quicksand/similar
            _trigger_movement_trap(game, hazard)
        elif effect == 'force_drain_or_boost':
            # Force nexus effect based on alignment
            _trigger_force_nexus(game)
            
    except:
        pass

def _spawn_sith_wraiths(game):
    """Spawn ghostly Sith enemies near the player."""
    # Implementation would spawn 1-2 wraith enemies
    try:
        game.ui.messages.add("   Ancient Sith spirits rise to challenge you!")
    except:
        pass

def _trigger_cave_in(game, hazard):
    """Trigger cave-in damage and effects."""
    damage_range = hazard.get('damage_range', (5, 15))
    damage = random.randint(*damage_range)
    
    try:
        game.ui.messages.add(f"   You take {damage} damage from falling debris!")
        game.player.hp = max(0, game.player.hp - damage)
    except:
        pass

def _trigger_movement_trap(game, hazard):
    """Trigger movement-restricting trap."""
    duration = hazard.get('duration', 3)
    try:
        game.ui.messages.add(f"   You're trapped for {duration} turns!")
        # Implementation would add movement restriction status effect
    except:
        pass

def _trigger_force_nexus(game):
    """Trigger Force nexus effects based on player alignment."""
    try:
        player_alignment = getattr(game.player, 'alignment_score', 0)
        
        if player_alignment > 10:  # Light side
            # Boost Force regeneration
            game.ui.messages.add("   Light side energy flows through you!")
            if hasattr(game.player, 'force') and hasattr(game.player.force, 'current_force_points'):
                game.player.force.current_force_points = min(
                    game.player.force.max_force_points,
                    game.player.force.current_force_points + 20
                )
        elif player_alignment < -10:  # Dark side
            # Boost dark powers but drain health
            game.ui.messages.add("   Dark side power surges, but at a cost!")
            game.player.hp = max(1, game.player.hp - 10)
            # Could add temporary dark side bonuses
        else:  # Neutral
            # Balanced effect
            game.ui.messages.add("   The Force flows through you in perfect balance.")
            
    except:
        pass