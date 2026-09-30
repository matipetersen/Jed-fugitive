"""
Faction System
Defines factions, player reputation, and dynamic world logic.
"""

class Faction:
    def __init__(self, name, icon, description):
        self.name = name
        self.icon = icon
        self.description = description
        self.relationships = {}  # {faction_name: value}

class FactionManager:
    def __init__(self):
        self.factions = {}
        self.player_reputation = {}  # {faction_name: -100 (hostile) to 100 (allied)}
        self._init_factions()

    def _init_factions(self):
        self.factions = {
            'Sith Empire': Faction('Sith Empire', '⚡', 'Sith military and dark side agents'),
            'Republic': Faction('Republic', '⭐', 'Galactic Republic and Jedi allies'),
            'Hutt': Faction('Hutt', '💰', 'Hutt Cartel and criminal underworld'),
            'Settlers': Faction('Settlers', '🏚️', 'Civilians and outcasts'),
            'Mandalorian': Faction('Mandalorian', '🛡️', 'Mandalorian clans and mercenaries'),
        }
        
        # Set up inter-faction relationships (-100 hostile, 0 neutral, 100 allied)
        sith = self.factions['Sith Empire']
        sith.relationships = {
            'Republic': -80,      # Mortal enemies
            'Hutt': -20,          # Distrustful
            'Settlers': -40,      # Oppressive
            'Mandalorian': -30,   # Rivals
        }
        
        republic = self.factions['Republic']
        republic.relationships = {
            'Sith Empire': -80,   # Mortal enemies
            'Hutt': -30,          # Fight against crime
            'Settlers': 40,       # Protect civilians
            'Mandalorian': 10,    # Uneasy allies
        }
        
        hutt = self.factions['Hutt']
        hutt.relationships = {
            'Sith Empire': -20,   # Business rivals
            'Republic': -30,      # Opposed by law
            'Settlers': -10,      # Exploit them
            'Mandalorian': 20,    # Sometimes hire them
        }
        
        settlers = self.factions['Settlers']
        settlers.relationships = {
            'Sith Empire': -40,   # Oppressed by
            'Republic': 40,       # Protected by
            'Hutt': -10,          # Exploited by
            'Mandalorian': -20,   # Fear them
        }
        
        mandalorian = self.factions['Mandalorian']
        mandalorian.relationships = {
            'Sith Empire': -30,   # Ancient enemies
            'Republic': 10,       # Sometimes work with
            'Hutt': 20,           # Mercenary contracts
            'Settlers': -20,      # Raid settlements
        }
        
        # Initialize reputation - Jedi should start with positive Republic standing
        for name in self.factions:
            if name == 'Republic':
                self.player_reputation[name] = 30  # Jedi are allies of the Republic
            elif name == 'Sith Empire':
                self.player_reputation[name] = -30  # Sith are enemies of the Jedi
            else:
                self.player_reputation[name] = 0  # Neutral with others

    def adjust_reputation(self, faction, amount):
        if faction in self.player_reputation:
            self.player_reputation[faction] = max(-100, min(100, self.player_reputation[faction] + amount))

    def get_reputation(self, faction):
        return self.player_reputation.get(faction, 0)

    def are_factions_hostile(self, faction_a, faction_b):
        """Check if two factions are hostile to each other."""
        if not faction_a or not faction_b:
            return False
        if faction_a == faction_b:
            return False  # Same faction, not hostile
        
        faction_obj = self.factions.get(faction_a)
        if faction_obj and faction_b in faction_obj.relationships:
            return faction_obj.relationships[faction_b] < -20  # Hostile threshold
        return False
    
    def is_player_hostile_to_faction(self, faction_name):
        """Check if player has hostile reputation with a faction."""
        rep = self.get_reputation(faction_name)
        return rep < -20
    
    def is_player_friendly_to_faction(self, faction_name):
        """Check if player has friendly reputation with a faction."""
        rep = self.get_reputation(faction_name)
        return rep > 20
    
    def get_faction_greeting(self, faction_name):
        """Get a greeting based on reputation with the faction."""
        rep = self.get_reputation(faction_name)
        
        if faction_name == 'Sith Empire':
            if rep < -50: return "Jedi filth! Die!"
            if rep < -10: return "Halt! State your business."
            if rep > 50: return "Glory to the Empire. Report any Jedi sightings."
            return "Move along, citizen."
            
        elif faction_name == 'Republic':
            if rep < -50: return "Sith spy! Open fire!"
            if rep < -10: return "This is a restricted area."
            if rep > 50: return "For the Republic! Good to see you."
            return "Stay safe. The Sith are everywhere."
            
        elif faction_name == 'Hutt':
            if rep < -50: return "The Hutt has a price on your head!"
            if rep < -10: return "Pay the toll or pay with your life."
            if rep > 50: return "Welcome! Your credits are always good here."
            return "You looking for work? Or trouble?"
            
        elif faction_name == 'Settlers':
            if rep < -50: return "Get away from us! We're armed!"
            if rep < -10: return "We don't want any trouble."
            if rep > 50: return "Welcome to our home. Stay as long as you like."
            return "Hello traveler. We have little to share."
            
        elif faction_name == 'Mandalorian':
            if rep < -50: return "You have no honor. Die!"
            if rep < -10: return "Walk away, outsider."
            if rep > 50: return "Su cuy'gar! Join us in the hunt?"
            return "This is Mandalorian business."
            
        return "Greetings."
