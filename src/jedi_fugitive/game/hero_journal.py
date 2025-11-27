"""
Enhanced Hero's Journey Journal System
Transforms the simple travel log into a compelling narrative tracking the player's path
from Jedi padawan to their ultimate destiny - light, dark, or balanced.
"""

import random
from datetime import datetime

class JourneyPhase:
    """Represents different phases of the hero's journey."""
    DEPARTURE = "departure"           # Crash, initial survival
    INITIATION = "initiation"         # Trials, conflicts, growth
    TRANSFORMATION = "transformation" # Major alignment shifts
    RETURN = "return"                 # Victory or defeat, completion

class JournalEntryType:
    """Categories of journal entries for better organization."""
    MILESTONE = "milestone"       # Major story beats
    COMBAT = "combat"            # Battle encounters
    DISCOVERY = "discovery"      # Items, locations, lore
    REFLECTION = "reflection"    # Character development
    ATMOSPHERE = "atmosphere"    # Environmental storytelling
    FAUNA = "fauna"             # Creature encounters
    CORRUPTION = "corruption"   # Alignment changes
    DEATH = "death"             # Final entry
    VICTORY = "victory"         # Successful completion

class HeroJournalManager:
    """Enhanced journal system that creates a hero's journey narrative."""
    
    def __init__(self, player):
        self.player = player
        
        # Journey phases tracking
        self.current_phase = JourneyPhase.DEPARTURE
        self.phase_entry_count = 0
        self.major_milestones = []
        
        # Entry categorization
        self.entries_by_type = {entry_type: [] for entry_type in vars(JournalEntryType).values() if not entry_type.startswith('__')}
        
        # Hero's journey progression
        self.trials_faced = 0
        self.companions_met = 0
        self.powers_gained = 0
        self.enemies_defeated = 0
        self.corruption_events = 0
        
        # Narrative arc tracking
        self.story_threads = {
            'master_memory': False,    # Remembering the fallen master
            'first_kill': False,       # First enemy defeated
            'dark_temptation': False,  # First dark side choice
            'light_choice': False,     # First light side choice
            'tomb_entered': False,     # Entering Sith tomb
            'artifact_found': False,   # First Sith artifact
            'breaking_point': False,   # Major corruption event
            'redemption': False,       # Major light side turn
            'final_trial': False       # End-game challenge
        }
    
    def add_enhanced_entry(self, text, turn, entry_type=JournalEntryType.REFLECTION, 
                          corruption_level=None, phase_override=None):
        """Add an entry with enhanced metadata and narrative context."""
        
        # Get current corruption if not provided
        if corruption_level is None:
            corruption_level = getattr(self.player, 'corruption', 50)
        
        # Determine current journey phase
        phase = phase_override or self.get_current_phase(turn, corruption_level)
        
        # Enhance the entry with narrative context
        enhanced_text = self.enhance_entry_text(text, entry_type, corruption_level, phase)
        
        # Create rich journal entry
        entry = {
            'text': enhanced_text,
            'turn': turn,
            'type': entry_type,
            'phase': phase,
            'corruption': corruption_level,
            'alignment': self.get_alignment_description(corruption_level),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'chapter': self.get_chapter_number(phase)
        }
        
        # Add to appropriate category
        self.entries_by_type[entry_type].append(entry)
        
        # Add to main travel log
        if not hasattr(self.player, 'travel_log'):
            self.player.travel_log = []
        self.player.travel_log.append(entry)
        
        # Update journey tracking
        self.update_journey_progress(entry_type, enhanced_text)
        
        # Check for phase transitions
        self.check_phase_transition(turn, corruption_level)
        
        return entry
    
    def get_current_phase(self, turn, corruption_level):
        """Determine the current phase of the hero's journey."""
        if turn < 100:
            return JourneyPhase.DEPARTURE
        elif turn < 500 or not self.story_threads['tomb_entered']:
            return JourneyPhase.INITIATION
        elif self.trials_faced >= 3 or abs(corruption_level - 50) > 30:
            return JourneyPhase.TRANSFORMATION
        else:
            return JourneyPhase.RETURN
    
    def get_alignment_description(self, corruption_level):
        """Get descriptive alignment text."""
        if corruption_level <= 20:
            return "Pure Light"
        elif corruption_level <= 35:
            return "Light Side"
        elif corruption_level <= 65:
            return "Balanced"
        elif corruption_level <= 80:
            return "Dark Side"
        else:
            return "Pure Darkness"
    
    def get_chapter_number(self, phase):
        """Get chapter number based on journey phase."""
        phase_chapters = {
            JourneyPhase.DEPARTURE: 1,
            JourneyPhase.INITIATION: 2,
            JourneyPhase.TRANSFORMATION: 3,
            JourneyPhase.RETURN: 4
        }
        return phase_chapters.get(phase, 1)
    
    def enhance_entry_text(self, text, entry_type, corruption_level, phase):
        """Enhance entry text with narrative flair based on context."""
        
        # Add phase-appropriate prefixes
        phase_prefixes = {
            JourneyPhase.DEPARTURE: ["Survival Log", "Initial Entry", "Crash Report"],
            JourneyPhase.INITIATION: ["Trial Record", "Learning", "Challenge"],
            JourneyPhase.TRANSFORMATION: ["Revelation", "Turning Point", "Metamorphosis"],
            JourneyPhase.RETURN: ["Final Path", "Destiny", "Conclusion"]
        }
        
        # Add corruption-influenced tone
        if corruption_level > 70:
            tone_indicators = ["The power flows through me...", "Weakness disgusts me.", "They will all kneel."]
        elif corruption_level < 30:
            tone_indicators = ["The Force guides me still.", "I must stay true to the light.", "Compassion remains my strength."]
        else:
            tone_indicators = ["Balance is the key.", "Neither fully light nor dark.", "I walk my own path."]
        
        # Sometimes add atmospheric enhancement
        if entry_type == JournalEntryType.REFLECTION and random.random() < 0.3:
            prefix = random.choice(phase_prefixes.get(phase, ["Entry"]))
            tone = random.choice(tone_indicators)
            return f"[{prefix}] {text} {tone}"
        
        return text
    
    def update_journey_progress(self, entry_type, text):
        """Update journey progression trackers."""
        
        # Count different types of experiences
        if entry_type == JournalEntryType.COMBAT:
            self.enemies_defeated += 1
            if not self.story_threads['first_kill'] and self.enemies_defeated == 1:
                self.story_threads['first_kill'] = True
                self.trials_faced += 1
        
        elif entry_type == JournalEntryType.CORRUPTION:
            self.corruption_events += 1
        
        elif entry_type == JournalEntryType.DISCOVERY:
            if 'tomb' in text.lower():
                self.story_threads['tomb_entered'] = True
            if 'artifact' in text.lower() or 'holocron' in text.lower():
                self.story_threads['artifact_found'] = True
                self.trials_faced += 1
        
        # Track major story moments
        if 'dark side' in text.lower() or 'ABSORB' in text:
            if not self.story_threads['dark_temptation']:
                self.story_threads['dark_temptation'] = True
                self.trials_faced += 1
        
        if 'light side' in text.lower() or 'DESTROY' in text:
            if not self.story_threads['light_choice']:
                self.story_threads['light_choice'] = True
                self.trials_faced += 1
    
    def check_phase_transition(self, turn, corruption_level):
        """Check if we should transition to a new journey phase."""
        old_phase = self.current_phase
        new_phase = self.get_current_phase(turn, corruption_level)
        
        if old_phase != new_phase:
            self.current_phase = new_phase
            self.phase_entry_count = 0
            
            # Add phase transition entry
            transition_text = self.get_phase_transition_text(old_phase, new_phase, corruption_level)
            self.add_milestone_entry(transition_text, turn, corruption_level)
    
    def get_phase_transition_text(self, old_phase, new_phase, corruption_level):
        """Generate narrative text for phase transitions."""
        
        transitions = {
            (JourneyPhase.DEPARTURE, JourneyPhase.INITIATION): {
                'light': "I've learned to survive in this harsh world. Now begins the true test of my Jedi training.",
                'balanced': "Survival is only the beginning. The real journey starts now.",
                'dark': "The weak die quickly here. I have proven I am not among them. Time to claim what is mine."
            },
            (JourneyPhase.INITIATION, JourneyPhase.TRANSFORMATION): {
                'light': "Each trial has tested my resolve. I feel the Force changing me, but I hold to the light.",
                'balanced': "The path becomes clearer. Neither pure light nor darkness, but something new.",
                'dark': "The power grows within me. I am no longer the frightened padawan who crashed here."
            },
            (JourneyPhase.TRANSFORMATION, JourneyPhase.RETURN): {
                'light': "I have faced the darkness and emerged purified. The final path reveals itself.",
                'balanced': "Transformed by trials, I see the way forward with clear eyes.",
                'dark': "Reborn in shadow and lightning. Let all who oppose me tremble. My destiny awaits."
            }
        }
        
        alignment = 'light' if corruption_level < 35 else 'dark' if corruption_level > 65 else 'balanced'
        transition_key = (old_phase, new_phase)
        
        return transitions.get(transition_key, {}).get(alignment, "The journey continues...")
    
    def add_milestone_entry(self, text, turn, corruption_level):
        """Add a major milestone entry."""
        self.major_milestones.append(turn)
        return self.add_enhanced_entry(text, turn, JournalEntryType.MILESTONE, corruption_level)
    
    def generate_journey_summary(self):
        """Generate a hero's journey summary for the journal display."""
        
        summary = {
            'title': self.get_story_title(),
            'chapters': self.organize_entries_by_chapter(),
            'statistics': self.get_journey_statistics(),
            'character_arc': self.get_character_arc_summary(),
            'epilogue': self.generate_epilogue()
        }
        
        return summary
    
    def get_story_title(self):
        """Generate a dynamic story title based on player's journey."""
        corruption = getattr(self.player, 'corruption', 50)
        
        if corruption <= 20:
            return "Chronicles of a Jedi Purifier"
        elif corruption <= 35:
            return "Path of the Light Bearer"
        elif corruption <= 65:
            return "Journey of the Gray Walker"
        elif corruption <= 80:
            return "Rise of a Dark Apprentice"
        else:
            return "Birth of a Sith Lord"
    
    def organize_entries_by_chapter(self):
        """Organize entries into narrative chapters."""
        chapters = {}
        
        for entry in getattr(self.player, 'travel_log', []):
            chapter = entry.get('chapter', 1)
            if chapter not in chapters:
                chapters[chapter] = []
            chapters[chapter].append(entry)
        
        return chapters
    
    def get_journey_statistics(self):
        """Get meaningful journey statistics."""
        return {
            'trials_faced': self.trials_faced,
            'enemies_defeated': self.enemies_defeated,
            'corruption_events': self.corruption_events,
            'major_milestones': len(self.major_milestones),
            'story_threads_completed': sum(1 for thread in self.story_threads.values() if thread)
        }
    
    def get_character_arc_summary(self):
        """Generate a character development summary."""
        corruption = getattr(self.player, 'corruption', 50)
        level = getattr(self.player, 'level', 1)
        
        arc_templates = {
            'light': f"From the ashes of tragedy, a beacon of hope emerged. Despite facing darkness at every turn, this Jedi remained true to the light, growing from level 1 to {level} while maintaining their compassion and wisdom.",
            'balanced': f"Neither purely light nor dark, this Force user carved their own path. Rising to level {level}, they learned that true strength comes from balance, not extremism.",
            'dark': f"Power corrupted, but perhaps that was always the destiny. From fallen Jedi to Sith apprentice, this journey to level {level} reveals how quickly light can become shadow."
        }
        
        alignment = 'light' if corruption < 35 else 'dark' if corruption > 65 else 'balanced'
        return arc_templates[alignment]
    
    def generate_epilogue(self):
        """Generate an epilogue based on current state."""
        corruption = getattr(self.player, 'corruption', 50)
        
        if hasattr(self.player, 'hp') and getattr(self.player, 'hp', 1) <= 0:
            return "Here ends the tale of one who dared to face the darkness... and was consumed by it."
        elif getattr(self.player, 'artifacts_collected', 0) >= 3:
            if corruption < 35:
                return "The artifacts purified, the beacon activated. This Jedi's journey ends in light and hope."
            elif corruption > 65:
                return "The artifacts claimed, power absolute. This Sith's rise has only just begun."
            else:
                return "Balance achieved, wisdom gained. This Force user's path continues beyond light and dark."
        else:
            return "The journey continues, destiny yet unwritten..."

def enhance_existing_journal_system(player):
    """Enhance an existing player's journal system."""
    if not hasattr(player, 'hero_journal'):
        player.hero_journal = HeroJournalManager(player)
    
    # Migrate existing travel log entries
    if hasattr(player, 'travel_log') and player.travel_log:
        for entry in player.travel_log:
            if isinstance(entry, dict) and 'type' not in entry:
                # Enhance old format entries
                entry['type'] = JournalEntryType.REFLECTION
                entry['phase'] = JourneyPhase.INITIATION
                entry['alignment'] = player.hero_journal.get_alignment_description(
                    getattr(player, 'corruption', 50)
                )
                entry['chapter'] = 2
    
    return player.hero_journal

# Enhanced journal entry functions for different events
def create_combat_victory_entry(enemy_name, player, biome="wasteland", weapon_type=None):
    """Create an enhanced combat victory journal entry."""
    corruption = getattr(player, 'corruption', 50)
    journal = enhance_existing_journal_system(player)
    
    # Import existing journal entries for base text
    try:
        from jedi_fugitive.game.journal_entries import get_combat_victory_entry
        base_text = get_combat_victory_entry(enemy_name, 
                                           player.get_alignment() if hasattr(player, 'get_alignment') else 'balanced',
                                           biome, weapon_type)
    except ImportError:
        base_text = f"Defeated {enemy_name} in combat."
    
    return journal.add_enhanced_entry(base_text, getattr(player, 'turn_count', 0), 
                                    JournalEntryType.COMBAT, corruption)

def create_discovery_entry(discovery_text, player, turn_count=0):
    """Create an enhanced discovery journal entry."""
    corruption = getattr(player, 'corruption', 50)
    journal = enhance_existing_journal_system(player)
    
    return journal.add_enhanced_entry(discovery_text, turn_count, 
                                    JournalEntryType.DISCOVERY, corruption)

def create_fauna_entry(creature_name, interaction, result, player, turn_count=0):
    """Create an enhanced fauna encounter journal entry."""
    corruption = getattr(player, 'corruption', 50)
    journal = enhance_existing_journal_system(player)
    
    text = f"Encountered {creature_name}. Chose to {interaction}. {result}"
    
    return journal.add_enhanced_entry(text, turn_count, 
                                    JournalEntryType.FAUNA, corruption)

def create_corruption_event_entry(event_text, corruption_change, player, turn_count=0):
    """Create an enhanced corruption/alignment change entry."""
    corruption = getattr(player, 'corruption', 50)
    journal = enhance_existing_journal_system(player)
    
    if corruption_change > 0:
        enhanced_text = f"{event_text} I feel the darkness seeping deeper into my soul. (+{corruption_change} corruption)"
    else:
        enhanced_text = f"{event_text} The light within grows stronger, pushing back the shadows. ({corruption_change} corruption)"
    
    return journal.add_enhanced_entry(enhanced_text, turn_count, 
                                    JournalEntryType.CORRUPTION, corruption)