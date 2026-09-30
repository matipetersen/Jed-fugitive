"""
Enhanced NPC Quest System for Jedi Fugitive
Provides immersive storytelling, rescue missions, and peaceful progression alternatives.
"""

import random
import math
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


class NPCType(Enum):
    """Types of NPCs that can be encountered"""
    REFUGEE = "refugee"
    MERCHANT = "merchant" 
    JEDI_SURVIVOR = "jedi_survivor"
    REPUBLIC = "republic"
    CIVILIAN = "civilian"
    INJURED_PILOT = "injured_pilot"
    RESEARCHER = "researcher"
    CHILD = "child"


class QuestType(Enum):
    """Categories of quests available"""
    RESCUE = "rescue"
    ESCORT = "escort"
    MEDICAL = "medical"
    INFORMATION = "information"
    SUPPLY = "supply"
    PROTECTION = "protection"
    RECOVERY = "recovery"


class QuestState(Enum):
    """Current state of a quest"""
    AVAILABLE = "available"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class QuestNPC:
    """Represents an NPC with quest potential"""
    
    def __init__(self, npc_type: NPCType, name: str, location: Tuple[int, int]):
        self.npc_type = npc_type
        self.name = name
        self.x, self.y = location
        self.dialogue_tree = {}
        self.quest_data = {}
        self.state = "alive"
        self.alignment_preference = "neutral"  # light, neutral, dark
        self.relationship_level = 0  # -100 to 100
        self.first_meeting = True
        self.backstory = ""
        self.current_need = ""
        self.personality_traits = []
        self.rewards = {}
        self.spawn_turn = 0
        
    def get_greeting(self, player) -> str:
        """Generate contextual greeting based on player alignment and relationship"""
        try:
            alignment = self._get_player_alignment(player)
            
            if self.first_meeting:
                return self._get_first_meeting_dialogue(alignment)
            else:
                return self._get_return_dialogue(alignment)
                
        except Exception:
            return f"{self.name}: Hello, traveler."
    
    def _get_player_alignment(self, player) -> str:
        """Determine player alignment category"""
        try:
            dark_points = getattr(player, 'dark_side_points', 0)
            if dark_points <= 20:
                return "light"
            elif dark_points <= 60:
                return "neutral"
            else:
                return "dark"
        except Exception:
            return "neutral"
    
    def _get_first_meeting_dialogue(self, alignment: str) -> str:
        """Generate first meeting dialogue based on NPC type and player alignment"""
        
        base_dialogues = {
            NPCType.REFUGEE: {
                "light": [
                    f"{self.name}: Thank the stars! A Jedi? We thought we were abandoned.",
                    f"{self.name}: Please, help us. The Sith Empire took everything.",
                    f"{self.name}: You have a kind face. Are you here to save us?"
                ],
                "neutral": [
                    f"{self.name}: Keep your distance. We've been burned by strangers before.", 
                    f"{self.name}: We don't have credits, if that's what you want.",
                    f"{self.name}: Just passing through? Don't bring the Sith down on us."
                ],
                "dark": [
                    f"{self.name}: *trembling* Take what you want, just leave us be!",
                    f"{self.name}: *eyes wide with fear* A Sith... please, mercy!",
                    f"{self.name}: We have nothing! Why do you torment us?"
                ]
            },
            
            NPCType.MERCHANT: {
                "light": [
                    f"{self.name}: Ah, a guardian of peace! I have special discounts for the Order.",
                    f"{self.name}: Dangerous times for trade, but I'm happy to help a Jedi.",
                    f"{self.name}: Supplies for the righteous cause? I have just the thing."
                ],
                "neutral": [
                    f"{self.name}: Credits are the only language I speak fluently.",
                    f"{self.name}: Buy or move on, time is money.", 
                    f"{self.name}: I don't ask questions, I just sell goods."
                ],
                "dark": [
                    f"{self.name}: *nervously* My Lord... everything is free for you, of course.",
                    f"{self.name}: I have... illicit goods that might interest someone of your... power.",
                    f"{self.name}: Please, take it all! Just don't hurt me!"
                ]
            },
            
            NPCType.JEDI_SURVIVOR: {
                "light": [
                    f"{self.name}: The Force is strong with you. We are not the last.",
                    f"{self.name}: I felt your presence. It is good to see a friendly face.",
                    f"{self.name}: The Order may be fallen, but we are still Jedi."
                ],
                "neutral": [
                    f"{self.name}: Your path is uncertain. Be careful, the dark side is seductive.",
                    f"{self.name}: You walk the line between light and dark. A dangerous game.",
                    f"{self.name}: I sense conflict. Do not let your emotions rule you."
                ],
                "dark": [
                    f"{self.name}: *ignites lightsaber* You have fallen. I will do what I must.",
                    f"{self.name}: Another brother lost to the shadow. I will end your suffering.",
                    f"{self.name}: The dark side has consumed you. There is no return."
                ]
            },
            
            NPCType.CHILD: {
                "light": [
                    f"{self.name}: Wow! A real Jedi? Can you lift rocks with your mind?",
                    f"{self.name}: My dad said the Jedi were gone. I knew he was wrong!",
                    f"{self.name}: Are you going to beat the bad guys?"
                ],
                "neutral": [
                    f"{self.name}: *peeking out* You look scary... but not like the Sith troopers.",
                    f"{self.name}: Do you have any food? I'm hungry.",
                    f"{self.name}: Are you a bounty hunter? Like in the stories?"
                ],
                "dark": [
                    f"{self.name}: *crying* You look like the monsters in my dreams!",
                    f"{self.name}: *running away* Mommy! Help!",
                    f"{self.name}: *shaking* Please don't hurt me..."
                ]
            },

            NPCType.REPUBLIC: {
                "light": [
                    f"{self.name}: Commander? No... but you're with us, aren't you?",
                    f"{self.name}: The Republic needs people like you. We're fighting a losing war.",
                    f"{self.name}: Good to see a friendly face. The Sith are everywhere."
                ],
                "neutral": [
                    f"{self.name}: Keep your head down. The Sith are watching.",
                    f"{self.name}: If you're not with us, stay out of our way.",
                    f"{self.name}: Information is worth more than credits these days."
                ],
                "dark": [
                    f"{self.name}: *reaching for blaster* Sith spy! You won't take me alive!",
                    f"{self.name}: You reek of the dark side. Stay back!",
                    f"{self.name}: We'll never surrender to your kind!"
                ]
            },

            NPCType.INJURED_PILOT: {
                "light": [
                    f"{self.name}: *coughing* My ship... I tried to evade them... help me...",
                    f"{self.name}: Thank the Force... I thought I was done for.",
                    f"{self.name}: Can you get me to a med-center? I have vital intel."
                ],
                "neutral": [
                    f"{self.name}: *groaning* I can pay... just get me out of here.",
                    f"{self.name}: Don't leave me here to die... I have credits.",
                    f"{self.name}: Look, I don't care who you are. Just help me."
                ],
                "dark": [
                    f"{self.name}: *gasping* You... you're one of them...",
                    f"{self.name}: Just finish it... I won't talk...",
                    f"{self.name}: *spits blood* The Republic will... win..."
                ]
            },

            NPCType.RESEARCHER: {
                "light": [
                    f"{self.name}: Fascinating! A Force user? I have so many questions!",
                    f"{self.name}: These ruins predate the Republic! We must preserve them.",
                    f"{self.name}: Please, protect my findings. This knowledge is precious."
                ],
                "neutral": [
                    f"{self.name}: Careful! Don't touch anything. This site is unstable.",
                    f"{self.name}: I'm here for the history, not the war.",
                    f"{self.name}: If you find any artifacts, I'll pay well for them."
                ],
                "dark": [
                    f"{self.name}: *backing away* You seek the forbidden texts? I... I can show you.",
                    f"{self.name}: Such power... you must be drawn to the dark energy here.",
                    f"{self.name}: Don't destroy this place! The knowledge belongs to everyone!"
                ]
            },

            NPCType.CIVILIAN: {
                "light": [
                    f"{self.name}: Bless you, master Jedi. We live in fear.",
                    f"{self.name}: Is it true? Is the Republic coming back?",
                    f"{self.name}: We just want to live in peace."
                ],
                "neutral": [
                    f"{self.name}: I didn't see anything. I don't know anything.",
                    f"{self.name}: Just passing through. Don't mind me.",
                    f"{self.name}: Hard times for everyone, eh?"
                ],
                "dark": [
                    f"{self.name}: *averting eyes* I obey! I obey!",
                    f"{self.name}: Please, I'm a loyal citizen!",
                    f"{self.name}: *frozen in fear*"
                ]
            }
        }
        try:
            dialogues = base_dialogues.get(self.npc_type, {})
            alignment_dialogues = dialogues.get(alignment, [f"{self.name}: Hello there."])
            return random.choice(alignment_dialogues)
        except Exception:
            return f"{self.name}: Greetings, traveler."
    
    def _get_return_dialogue(self, alignment: str) -> str:
        """Generate return meeting dialogue"""
        if self.relationship_level > 50:
            return f"{self.name}: Good to see you again, friend!"
        elif self.relationship_level > 0:
            return f"{self.name}: Hello again, {self._get_player_title(alignment)}."
        elif self.relationship_level < -50:
            return f"{self.name}: *warily* You again..."
        else:
            return f"{self.name}: We meet again."
    
    def _get_player_title(self, alignment: str) -> str:
        """Get appropriate title for player based on alignment"""
        titles = {
            "light": ["hero", "savior", "Jedi", "friend"],
            "neutral": ["traveler", "wanderer", "stranger", "fighter"],
            "dark": ["dark one", "Sith", "lord", "master"]
        }
        return random.choice(titles.get(alignment, ["traveler"]))


class Quest:
    """Represents an individual quest"""
    
    def __init__(self, quest_id: str, quest_type: QuestType, npc: QuestNPC, description: str):
        self.quest_id = quest_id
        self.quest_type = quest_type
        self.npc = npc
        self.title = ""
        self.description = description
        self.objectives = []
        self.state = QuestState.AVAILABLE
        self.progress = {}
        self.rewards = {}
        self.time_limit = None
        self.alignment_bonus = ""
        self.xp_reward = 0
        self.created_turn = 0
        
    def check_completion(self, game) -> bool:
        """Check if quest objectives are completed"""
        try:
            for obj in self.objectives:
                if not self._check_objective(obj, game):
                    return False
            return True
        except Exception:
            return False
    
    def _check_objective(self, objective: Dict, game) -> bool:
        """Check individual objective completion"""
        obj_type = objective.get('type')
        
        if obj_type == 'escort':
            # Check if NPC reached destination
            target_x, target_y = objective.get('destination', (0, 0))
            return abs(self.npc.x - target_x) <= 1 and abs(self.npc.y - target_y) <= 1
            
        elif obj_type == 'deliver':
            # Check if player has delivered item
            return objective.get('delivered', False)
            
        elif obj_type == 'protect':
            # Check if NPC is still alive and safe
            return self.npc.state == "alive" and objective.get('threats_cleared', False)
            
        elif obj_type == 'gather':
            # Check if required items collected
            required = objective.get('required_amount', 1)
            collected = objective.get('collected_amount', 0)
            return collected >= required
            
        return False


class QuestManager:
    """Manages all NPC quests and interactions"""
    
    def __init__(self):
        self.active_quests = {}
        self.completed_quests = []
        self.available_npcs = []
        self.quest_log = []
        self.next_quest_id = 1
        
    def spawn_contextual_npc(self, game, location: Tuple[int, int]) -> Optional[QuestNPC]:
        """Spawn an NPC appropriate to the current location and game state"""
        try:
            biome = getattr(game, 'current_biome', 'unknown')
            in_tomb = getattr(game, 'in_tomb', False)
            player_level = getattr(game.player, 'level', 1)
            
            # Don't spawn NPCs in tombs unless it's a researcher
            if in_tomb and random.random() > 0.1:
                return None
                
            # Determine appropriate NPC type based on context
            npc_type = self._choose_npc_type(biome, in_tomb, player_level)
            if not npc_type:
                return None
                
            # Generate NPC
            npc = self._create_npc(npc_type, location, game)
            if npc:
                self.available_npcs.append(npc)
                return npc
                
        except Exception:
            pass
        return None
    
    def _choose_npc_type(self, biome: str, in_tomb: bool, player_level: int) -> Optional[NPCType]:
        """Choose appropriate NPC type for context"""
        
        if in_tomb:
            # Researchers and injured explorers in tombs
            return random.choice([NPCType.RESEARCHER, NPCType.REFUGEE])
        
        biome_npcs = {
            'desert': [NPCType.REFUGEE, NPCType.MERCHANT, NPCType.CIVILIAN],
            'forest': [NPCType.REFUGEE, NPCType.JEDI_SURVIVOR, NPCType.CHILD, NPCType.CIVILIAN],
            'mountains': [NPCType.REFUGEE, NPCType.REPUBLIC, NPCType.CIVILIAN],
            'crash_site': [NPCType.INJURED_PILOT, NPCType.REFUGEE, NPCType.RESEARCHER],
        }
        
        possible_types = biome_npcs.get(biome, [NPCType.REFUGEE, NPCType.CIVILIAN])
        
        # Higher level players more likely to meet important NPCs
        if player_level >= 5 and random.random() < 0.3:
            possible_types.append(NPCType.JEDI_SURVIVOR)
        if player_level >= 3 and random.random() < 0.4:
            possible_types.append(NPCType.REPUBLIC)
            
        return random.choice(possible_types) if possible_types else None
    
    def _create_npc(self, npc_type: NPCType, location: Tuple[int, int], game) -> QuestNPC:
        """Create NPC with contextual details"""
        
        name_pools = {
            NPCType.REFUGEE: ["Kira Thorne", "Marcus Vale", "Elena Skyborn", "David Cross", "Sarah Vex"],
            NPCType.MERCHANT: ["Josto the Trader", "Mira Coinwright", "Bren Goodseller", "Nala Markup"],
            NPCType.JEDI_SURVIVOR: ["Master Kellan", "Knight Bastila", "Knight Sera", "Padawan Jex"],
            NPCType.REPUBLIC: ["Captain Rex", "Lieutenant Maya", "Sergeant Korr", "Agent Blackwood"],
            NPCType.CHILD: ["Little Timmy", "Young Vette", "Small Ben", "Tiny Sara"],
            NPCType.INJURED_PILOT: ["Pilot Voss", "Commander Ash", "Flight Leader Tano", "Captain Solo"],
            NPCType.RESEARCHER: ["Dr. Aphra", "Scholar Voss", "Archaeologist Ming", "Professor Kell"]
        }
        
        names = name_pools.get(npc_type, ["Unknown Traveler"])
        name = random.choice(names)
        
        npc = QuestNPC(npc_type, name, location)
        npc.spawn_turn = getattr(game, 'turn_count', 0)
        
        # Set contextual details
        self._set_npc_backstory(npc, game)
        self._generate_quest_for_npc(npc, game)
        
        return npc
    
    def _set_npc_backstory(self, npc: QuestNPC, game):
        """Generate contextual backstory and personality"""
        
        biome = getattr(game, 'current_biome', 'unknown')
        
        backstories = {
            NPCType.REFUGEE: [
                f"Fled when the Sith attacked their settlement in the {biome}.",
                f"Lost everything in a recent Sith raid.",
                f"Searching for family members separated during the evacuation.",
                f"Former civilian now struggling to survive in the wilderness."
            ],
            NPCType.JEDI_SURVIVOR: [
                f"Went into hiding during Order 66, living as a hermit.",
                f"Former Padawan who escaped the Great Purge.",
                f"Aging Jedi Master protecting the last remnants of the Order.",
                f"Knight who lost their lightsaber but not their connection to the Force."
            ],
            NPCType.CHILD: [
                f"Orphaned by the war, trying to find surviving relatives.",
                f"Lost and scared, separated from parents during an attack.",
                f"Hiding in the {biome} after their home was destroyed.",
                f"Too young to understand the war, just wants to go home."
            ]
        }
        
        stories = backstories.get(npc.npc_type, [f"A {npc.npc_type.value} trying to survive."])
        npc.backstory = random.choice(stories)
        
        # Set personality traits
        trait_pools = {
            NPCType.REFUGEE: ["desperate", "hopeful", "grateful", "fearful", "determined"],
            NPCType.MERCHANT: ["greedy", "shrewd", "friendly", "cautious", "opportunistic"],
            NPCType.JEDI_SURVIVOR: ["wise", "melancholy", "protective", "patient", "haunted"],
            NPCType.CHILD: ["innocent", "scared", "curious", "trusting", "lonely"]
        }
        
        traits = trait_pools.get(npc.npc_type, ["neutral"])
        npc.personality_traits = random.sample(traits, min(2, len(traits)))
    
    def _generate_quest_for_npc(self, npc: QuestNPC, game):
        """Generate appropriate quest based on NPC type and context"""
        
        quest_templates = {
            NPCType.REFUGEE: [
                {
                    'type': QuestType.ESCORT,
                    'title': 'Safe Passage',
                    'description': f'Escort {npc.name} to safety',
                    'xp_reward': 75,
                    'objectives': [{'type': 'escort', 'destination': None}]
                },
                {
                    'type': QuestType.MEDICAL,
                    'title': 'Medical Aid', 
                    'description': f'Provide healing to {npc.name}',
                    'xp_reward': 50,
                    'objectives': [{'type': 'deliver', 'item': 'medkit'}]
                }
            ],
            NPCType.JEDI_SURVIVOR: [
                {
                    'type': QuestType.INFORMATION,
                    'title': 'Lost Knowledge',
                    'description': f'Help {npc.name} recover Jedi artifacts',
                    'xp_reward': 100,
                    'objectives': [{'type': 'gather', 'item': 'jedi_artifact', 'required_amount': 1}]
                }
            ],
            NPCType.CHILD: [
                {
                    'type': QuestType.PROTECTION,
                    'title': 'Find Family',
                    'description': f'Help {npc.name} find their family',
                    'xp_reward': 80,
                    'objectives': [{'type': 'escort', 'destination': None}]
                }
            ]
        }
        
        templates = quest_templates.get(npc.npc_type, [])
        if templates:
            template = random.choice(templates)
            
            quest_id = f"quest_{self.next_quest_id}"
            self.next_quest_id += 1
            
            quest = Quest(quest_id, template['type'], npc, template['description'])
            quest.title = template['title']
            quest.xp_reward = template['xp_reward']
            quest.objectives = template['objectives']
            quest.created_turn = getattr(game, 'turn_count', 0)
            
            npc.quest_data = quest
    
    def update_quests(self, game):
        """Update all active quests based on game state"""
        try:
            for quest_id, quest in list(self.active_quests.items()):
                if quest.check_completion(game):
                    self._complete_quest(quest, game, success=True)
                elif self._check_quest_failure(quest, game):
                    self._complete_quest(quest, game, success=False)
        except Exception:
            pass
    
    def _complete_quest(self, quest: Quest, game, success: bool):
        """Complete quest and give rewards"""
        try:
            if success:
                # Award XP
                if hasattr(game.player, 'add_experience'):
                    game.player.add_experience(quest.xp_reward)
                    
                # Award items/rewards
                for reward_type, amount in quest.rewards.items():
                    self._give_reward(game.player, reward_type, amount)
                
                # Update relationship
                quest.npc.relationship_level += 25
                
                quest.state = QuestState.COMPLETED
                self.completed_quests.append(quest)
                
                # Message
                if hasattr(game.ui, 'messages'):
                    game.ui.messages.add(f"✓ Quest completed: {quest.title} (+{quest.xp_reward} XP)")
                    
            else:
                quest.state = QuestState.FAILED
                quest.npc.relationship_level -= 10
                
                if hasattr(game.ui, 'messages'):
                    game.ui.messages.add(f"✗ Quest failed: {quest.title}")
            
            # Remove from active quests
            if quest.quest_id in self.active_quests:
                del self.active_quests[quest.quest_id]
                
        except Exception:
            pass
    
    def _give_reward(self, player, reward_type: str, amount: int):
        """Give quest reward to player"""
        try:
            if reward_type == 'credits' and hasattr(player, 'credits'):
                player.credits += amount
            elif reward_type == 'experience' and hasattr(player, 'add_experience'):
                player.add_experience(amount)
            # Add more reward types as needed
        except Exception:
            pass
    
    def _check_quest_failure(self, quest: Quest, game) -> bool:
        """Check if quest has failed"""
        try:
            # NPC died
            if quest.npc.state == "dead":
                return True
            
            # Time limit exceeded
            if quest.time_limit:
                current_turn = getattr(game, 'turn_count', 0)
                if current_turn - quest.created_turn > quest.time_limit:
                    return True
                    
            return False
        except Exception:
            return False
    
    def get_nearest_npc(self, player_x: int, player_y: int, max_distance: int = 1) -> Optional[QuestNPC]:
        """Find nearest interactable NPC"""
        try:
            nearest = None
            min_dist = float('inf')
            
            for npc in self.available_npcs:
                if npc.state != "alive":
                    continue
                    
                dist = abs(npc.x - player_x) + abs(npc.y - player_y)
                if dist <= max_distance and dist < min_dist:
                    min_dist = dist
                    nearest = npc
                    
            return nearest
        except Exception:
            return None
    
    def create_random_npc(self, x: int, y: int, level: int = 1, biome: str = 'forest') -> Optional[QuestNPC]:
        """Create a random NPC with quest at specified location"""
        try:
            # Create a mock game object for context
            class MockGame:
                def __init__(self, biome, level):
                    self.current_biome = biome
                    self.in_tomb = False
                    self.turn_count = 0
                    self.player = MockPlayer(level)
                    
            class MockPlayer:
                def __init__(self, level):
                    self.level = level
            
            mock_game = MockGame(biome, level)
            npc = self.spawn_contextual_npc(mock_game, (x, y))
            
            if npc:
                # Generate a quest for this NPC
                quest = self._generate_quest_for_npc(npc, mock_game)
                if quest:
                    npc.current_quest = quest
                    self.active_quests[quest.id] = quest
                
            return npc
            
        except Exception:
            return None
            
    def start_conversation(self, npc: QuestNPC, player) -> Optional[Dict[str, Any]]:
        """Start a conversation with an NPC"""
        try:
            if not npc or not player:
                return None
                
            # Check if NPC has an active quest
            if hasattr(npc, 'current_quest') and npc.current_quest:
                quest = npc.current_quest
                
                # Check quest state
                if quest.state == QuestState.AVAILABLE:
                    return {
                        'message': self._get_quest_offer_dialogue(npc, quest),
                        'quest_offered': True,
                        'quest': quest
                    }
                elif quest.state == QuestState.ACTIVE:
                    # Check if quest can be completed
                    if self._can_complete_quest(quest, player):
                        return {
                            'message': self._get_quest_completion_dialogue(npc, quest),
                            'quest_complete': True,
                            'quest': quest
                        }
                    else:
                        return {
                            'message': self._get_quest_progress_dialogue(npc, quest),
                            'quest_active': True,
                            'quest': quest
                        }
                elif quest.state == QuestState.COMPLETED:
                    return {
                        'message': self._get_post_quest_dialogue(npc),
                        'quest_completed': True
                    }
            
            # Default conversation if no quest
            return {
                'message': self._get_default_dialogue(npc),
                'greeting': True
            }
            
        except Exception:
            return None
    
    def _get_quest_offer_dialogue(self, npc: QuestNPC, quest) -> str:
        """Generate quest offer dialogue"""
        greetings = {
            NPCType.REFUGEE: f"Please, you must help me! {quest.description}",
            NPCType.MERCHANT: f"I have a business proposition: {quest.description}",
            NPCType.JEDI_SURVIVOR: f"The Force led you to me. {quest.description}",
            NPCType.REPUBLIC: f"We need your assistance, friend. {quest.description}",
            NPCType.CHILD: f"Mister, can you help me? {quest.description}",
            NPCType.INJURED_PILOT: f"My ship crashed... {quest.description}",
            NPCType.RESEARCHER: f"My research depends on this: {quest.description}"
        }
        
        return greetings.get(npc.npc_type, f"I need your help. {quest.description}")
    
    def _get_quest_completion_dialogue(self, npc: QuestNPC, quest) -> str:
        """Generate quest completion dialogue"""
        return f"You've done it! {quest.completion_text or 'Thank you for your help!'}"
    
    def _get_quest_progress_dialogue(self, npc: QuestNPC, quest) -> str:
        """Generate dialogue for active quest"""
        return f"Have you made progress on {quest.title}? {quest.description}"
    
    def _get_post_quest_dialogue(self, npc: QuestNPC) -> str:
        """Generate dialogue after quest completion"""
        return "Thank you again for all your help. I won't forget your kindness."
    
    def _get_default_dialogue(self, npc: QuestNPC) -> str:
        """Generate default NPC dialogue"""
        defaults = {
            NPCType.REFUGEE: "This world is so dangerous... I'm just trying to survive.",
            NPCType.MERCHANT: "Looking for supplies? I might have something useful.",
            NPCType.JEDI_SURVIVOR: "The Force is strong in this place, but so is the darkness.",
            NPCType.REPUBLIC: "Keep fighting the good fight, friend.",
            NPCType.CHILD: "Are you a Jedi? You look brave!",
            NPCType.INJURED_PILOT: "My ship's in bad shape, but I'll manage.",
            NPCType.RESEARCHER: "This planet holds many secrets..."
        }
        
        return defaults.get(npc.npc_type, "Hello there, traveler.")
    
    def _can_complete_quest(self, quest, player) -> bool:
        """Check if quest objectives are met"""
        try:
            if quest.quest_type == QuestType.RESCUE:
                # Simple completion check - could be enhanced with actual objectives
                return True
            elif quest.quest_type == QuestType.SUPPLY:
                # Check if player has required items (simplified)
                return True
            elif quest.quest_type == QuestType.INFORMATION:
                # Information quests auto-complete when returned to
                return True
            else:
                return True  # Simplified - all quests can be completed
        except Exception:
            return False
    
    def accept_quest(self, quest, player) -> bool:
        """Accept a quest"""
        try:
            if quest and quest.state == QuestState.AVAILABLE:
                quest.state = QuestState.ACTIVE
                quest.start_turn = getattr(player, 'turn_count', 0)
                self.quest_log.append(quest)
                return True
        except Exception:
            pass
        return False
    
    def complete_quest(self, quest, player) -> Dict[str, int]:
        """Complete a quest and return rewards"""
        try:
            if quest and quest.state == QuestState.ACTIVE:
                quest.state = QuestState.COMPLETED
                self.completed_quests.append(quest)
                
                # Remove from active quests
                if quest.id in self.active_quests:
                    del self.active_quests[quest.id]
                
                # Calculate rewards
                rewards = {}
                if hasattr(quest, 'experience_reward') and quest.experience_reward:
                    rewards['experience'] = quest.experience_reward
                if hasattr(quest, 'credits_reward') and quest.credits_reward:
                    rewards['credits'] = quest.credits_reward
                
                return rewards
        except Exception:
            pass
        return {}