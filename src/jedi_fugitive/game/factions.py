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
            'Imperial': Faction('Imperial', '🛡️', 'Empire military and Sith agents'),
            'Rebel': Faction('Rebel', '✊', 'Rebel Alliance and sympathizers'),
            'Hutt': Faction('Hutt', '💰', 'Hutt Cartel and criminal underworld'),
            'Settlers': Faction('Settlers', '🏚️', 'Civilians and outcasts'),
        }
        for name in self.factions:
            self.player_reputation[name] = 0

    def adjust_reputation(self, faction, amount):
        if faction in self.player_reputation:
            self.player_reputation[faction] = max(-100, min(100, self.player_reputation[faction] + amount))

    def get_reputation(self, faction):
        return self.player_reputation.get(faction, 0)

# Usage: Attach FactionManager to game manager or player
