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
            dark_points = getattr(player, 'dark_corruption', getattr(player, 'dark_side_points', 0)) or 0
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
    """A quest with objectives the game actually updates.

    kinds:
      deliver  - hand the NPC a healing item (checked when you talk to them)
      recover  - pick up a quest item placed somewhere on the map, bring it back
      hunt     - kill a named Sith that was spawned for this quest, then report
      escort   - the NPC follows you to a destination
      scout    - reach a location (usually a tomb entrance), then report
    """

    def __init__(self, quest_id: str, quest_type: QuestType, npc: QuestNPC, description: str):
        self.quest_id = quest_id
        self.id = quest_id
        self.quest_type = quest_type
        self.npc = npc
        self.title = ""
        self.description = description
        self.kind = "deliver"
        self.objectives = []
        self.state = QuestState.AVAILABLE
        self.target = None          # (x, y) for recover/escort/scout
        self.target_enemy = None    # Enemy for hunt
        self.item_name = ""
        self.done = False           # objective met; reward on return (or on arrival for escort)
        self.xp_reward = 0
        self.experience_reward = 0
        self.rewards = {}
        self.created_turn = 0
        self.start_turn = 0
        self.time_limit = None
        self.completion_text = ""

    def status_line(self, game=None) -> str:
        where = ""
        if game is not None:
            tgt = self.current_target(game)
            if tgt:
                dx, dy = tgt[0] - game.player.x, tgt[1] - game.player.y
                where = f" [{_direction(dx, dy)} {abs(dx) + abs(dy)}m]"
        state = "report back" if self.done and self.kind != "escort" else "in progress"
        return f"{self.title}: {self.description}{where} ({state})"

    def current_target(self, game):
        if self.state != QuestState.ACTIVE:
            return None
        if self.done or self.kind == "deliver":
            return (self.npc.x, self.npc.y)
        if self.kind == "hunt" and self.target_enemy is not None:
            return (self.target_enemy.x, self.target_enemy.y)
        return self.target

    # kept for compatibility with older callers
    def check_completion(self, game) -> bool:
        return self.done


def _direction(dx, dy):
    ns = "N" if dy < 0 else ("S" if dy > 0 else "")
    ew = "W" if dx < 0 else ("E" if dx > 0 else "")
    return (ns + ew) or "here"


HEALING_IDS = ('medkit_small', 'stimpack', 'ration', 'water_canteen', 'nutrient_paste')

# (kind, title, description, item, xp)
QUEST_TEMPLATES = {
    NPCType.REFUGEE: [
        ("escort", "Safe Passage", "Escort {name} to the hidden camp", "", 80),
        ("deliver", "Medical Aid", "Bring {name} something to treat their wounds", "", 50),
    ],
    NPCType.CIVILIAN: [
        ("recover", "Lost Heirloom", "Recover {name}'s family heirloom from the ruins", "Family Heirloom", 60),
        ("deliver", "Hunger", "Bring {name} food or water", "", 45),
    ],
    NPCType.CHILD: [
        ("escort", "Find Family", "Take {name} back to their family's shelter", "", 90),
    ],
    NPCType.MERCHANT: [
        ("recover", "Stolen Cargo", "Recover the cargo crate the Sith seized from {name}", "Cargo Crate", 70),
    ],
    NPCType.JEDI_SURVIVOR: [
        ("scout", "Echoes in the Dark", "Find the Sith tomb {name} sensed in a vision", "", 110),
        ("recover", "Lost Knowledge", "Recover the Jedi holocron {name} hid before the purge", "Jedi Holocron", 120),
    ],
    NPCType.REPUBLIC: [
        ("hunt", "Cut the Head", "Eliminate the Sith patrol leader hunting {name}'s unit", "", 120),
    ],
    NPCType.INJURED_PILOT: [
        ("recover", "Flight Recorder", "Recover the flight recorder from {name}'s wreck", "Flight Recorder", 80),
        ("deliver", "Field Dressing", "Bring {name} a medkit or stimpack", "", 50),
    ],
    NPCType.RESEARCHER: [
        ("scout", "Survey", "Survey the tomb entrance {name} has been studying", "", 90),
    ],
}

QUEST_FACTION = {
    NPCType.REFUGEE: 'Settlers', NPCType.CIVILIAN: 'Settlers', NPCType.CHILD: 'Settlers',
    NPCType.MERCHANT: 'Hutt', NPCType.REPUBLIC: 'Republic', NPCType.INJURED_PILOT: 'Republic',
    NPCType.JEDI_SURVIVOR: 'Republic', NPCType.RESEARCHER: 'Settlers',
}


class QuestManager:
    """Manages NPC quests: offers, objectives, progress each tick, rewards."""

    def __init__(self):
        self.active_quests = {}       # quest_id -> Quest (accepted)
        self.completed_quests = []
        self.available_npcs = []
        self.quest_log = []
        self.next_quest_id = 1

    # ------------------------------------------------------------ spawning
    def _choose_npc_type(self, biome: str, in_tomb: bool, player_level: int) -> Optional[NPCType]:
        if in_tomb:
            return random.choice([NPCType.RESEARCHER, NPCType.REFUGEE])
        biome_npcs = {
            'desert': [NPCType.REFUGEE, NPCType.MERCHANT, NPCType.CIVILIAN, NPCType.INJURED_PILOT],
            'forest': [NPCType.REFUGEE, NPCType.JEDI_SURVIVOR, NPCType.CHILD, NPCType.CIVILIAN],
            'rocky': [NPCType.REFUGEE, NPCType.REPUBLIC, NPCType.RESEARCHER],
            'mountain_pass': [NPCType.REPUBLIC, NPCType.JEDI_SURVIVOR, NPCType.RESEARCHER],
            'river': [NPCType.CIVILIAN, NPCType.CHILD, NPCType.MERCHANT],
            'plains': [NPCType.REFUGEE, NPCType.CIVILIAN, NPCType.INJURED_PILOT, NPCType.REPUBLIC],
        }
        return random.choice(biome_npcs.get(biome, [NPCType.REFUGEE, NPCType.CIVILIAN]))

    def _create_npc(self, npc_type: NPCType, location: Tuple[int, int], game) -> QuestNPC:
        name_pools = {
            NPCType.REFUGEE: ["Kira Thorne", "Marcus Vale", "Elena Skyborn", "David Cross", "Sarah Vex"],
            NPCType.MERCHANT: ["Josto the Trader", "Mira Coinwright", "Bren Goodseller", "Nala Markup"],
            NPCType.JEDI_SURVIVOR: ["Master Kellan", "Knight Bastila", "Knight Sera", "Padawan Jex"],
            NPCType.REPUBLIC: ["Captain Rex", "Lieutenant Maya", "Sergeant Korr", "Agent Blackwood"],
            NPCType.CHILD: ["Little Timmy", "Young Vette", "Small Ben", "Tiny Sara"],
            NPCType.INJURED_PILOT: ["Pilot Voss", "Commander Ash", "Flight Leader Tano", "Captain Solo"],
            NPCType.RESEARCHER: ["Dr. Aphra", "Scholar Voss", "Archaeologist Ming", "Professor Kell"],
            NPCType.CIVILIAN: ["Old Jorrin", "Tessa Marr", "Fenn Rook", "Ama Dorran"],
        }
        npc = QuestNPC(npc_type, random.choice(name_pools.get(npc_type, ["Unknown Traveler"])), location)
        npc.spawn_turn = getattr(game, 'turn_count', 0)
        self._set_npc_backstory(npc, game)
        return npc

    def _set_npc_backstory(self, npc: QuestNPC, game):
        biome = getattr(game, 'current_biome', 'unknown')
        backstories = {
            NPCType.REFUGEE: [
                f"Fled when the Sith attacked their settlement in the {biome}.",
                "Lost everything in a recent Sith raid.",
                "Searching for family members separated during the evacuation.",
                "Former civilian now struggling to survive in the wilderness.",
            ],
            NPCType.JEDI_SURVIVOR: [
                "Survived the purge by living as a hermit.",
                "Former Padawan who escaped the massacre at the enclave.",
                "Aging Jedi Master protecting the last remnants of the Order.",
                "Knight who lost their lightsaber but not their connection to the Force.",
            ],
            NPCType.CHILD: [
                "Orphaned by the war, trying to find surviving relatives.",
                "Lost and scared, separated from parents during an attack.",
                f"Hiding in the {biome} after their home was destroyed.",
                "Too young to understand the war, just wants to go home.",
            ],
        }
        stories = backstories.get(npc.npc_type, [f"A {npc.npc_type.value} trying to survive."])
        npc.backstory = random.choice(stories)
        trait_pools = {
            NPCType.REFUGEE: ["desperate", "hopeful", "grateful", "fearful", "determined"],
            NPCType.MERCHANT: ["greedy", "shrewd", "friendly", "cautious", "opportunistic"],
            NPCType.JEDI_SURVIVOR: ["wise", "melancholy", "protective", "patient", "haunted"],
            NPCType.CHILD: ["innocent", "scared", "curious", "trusting", "lonely"],
        }
        traits = trait_pools.get(npc.npc_type, ["neutral"])
        npc.personality_traits = random.sample(traits, min(2, len(traits)))

    def _make_quest(self, npc: QuestNPC, game) -> Optional[Quest]:
        templates = QUEST_TEMPLATES.get(npc.npc_type)
        if not templates:
            return None
        kind, title, desc, item, xp = random.choice(templates)
        q = Quest(f"quest_{self.next_quest_id}", QuestType.RECOVERY, npc, desc.format(name=npc.name))
        self.next_quest_id += 1
        q.kind = kind
        q.title = title
        q.item_name = item
        q.xp_reward = q.experience_reward = xp
        q.created_turn = getattr(game, 'turn_count', 0)
        q.objectives = [{'type': kind}]
        q.completion_text = {
            'escort': "We made it. I don't know how to thank you.",
            'deliver': "This will keep me going. Thank you.",
            'recover': "You found it! I thought it was lost forever.",
            'hunt': "With that monster gone we can breathe again.",
            'scout': "So the vision was true. The Force guided you.",
        }[kind]
        return q

    def create_random_npc(self, x: int, y: int, level: int = 1, biome: str = 'forest', game=None) -> Optional[QuestNPC]:
        """Create an NPC with a quest offer at (x, y)."""
        try:
            class _Ctx:
                pass
            ctx = game if game is not None else _Ctx()
            if game is None:
                ctx.current_biome = biome
                ctx.turn_count = 0
            npc_type = self._choose_npc_type(biome, False, level)
            npc = self._create_npc(npc_type, (x, y), ctx)
            npc.current_quest = self._make_quest(npc, ctx)
            npc.quest_data = npc.current_quest
            self.available_npcs.append(npc)
            return npc
        except Exception:
            return None

    # --------------------------------------------------------- conversation
    def start_conversation(self, npc: QuestNPC, player, game=None) -> Optional[Dict[str, Any]]:
        """Talk to an NPC. Completes deliver/report quests on the spot when possible."""
        try:
            quest = getattr(npc, 'current_quest', None)
            greeting = npc.get_greeting(player) if hasattr(npc, 'get_greeting') else f"{npc.name}: Hello."
            npc.first_meeting = False
            if quest is None:
                return {'message': greeting, 'greeting': True}
            if quest.state == QuestState.AVAILABLE:
                return {'message': f"{greeting} {self._get_quest_offer_dialogue(npc, quest)}",
                        'quest_offered': True, 'quest': quest}
            if quest.state == QuestState.ACTIVE:
                if quest.kind == 'deliver' and game is not None and self._take_delivery(quest, game):
                    quest.done = True
                if quest.done and quest.kind != 'escort':
                    return {'message': f"{npc.name}: {quest.completion_text}", 'quest_complete': True, 'quest': quest}
                return {'message': f"{npc.name}: {self._get_quest_progress_dialogue(npc, quest)}",
                        'quest_active': True, 'quest': quest}
            return {'message': f"{npc.name}: {self._get_post_quest_dialogue(npc)}", 'quest_completed': True}
        except Exception:
            return None

    def _get_quest_offer_dialogue(self, npc: QuestNPC, quest) -> str:
        greetings = {
            NPCType.REFUGEE: f"Please, you must help me! {quest.description}.",
            NPCType.MERCHANT: f"I have a business proposition: {quest.description}.",
            NPCType.JEDI_SURVIVOR: f"The Force led you to me. {quest.description}.",
            NPCType.REPUBLIC: f"We need your assistance, friend. {quest.description}.",
            NPCType.CHILD: f"Can you help me? {quest.description}.",
            NPCType.INJURED_PILOT: f"My ship went down too... {quest.description}.",
            NPCType.RESEARCHER: f"My research depends on this: {quest.description}.",
        }
        return greetings.get(npc.npc_type, f"I need your help. {quest.description}.")

    def _get_quest_progress_dialogue(self, npc: QuestNPC, quest) -> str:
        if quest.kind == 'deliver':
            return "Do you have anything that could help? (a medkit, stimpack, ration or water)"
        return f"Any news? {quest.description}."

    def _get_post_quest_dialogue(self, npc: QuestNPC) -> str:
        return "Thank you again for all your help. I won't forget your kindness."

    def _get_default_dialogue(self, npc: QuestNPC) -> str:
        defaults = {
            NPCType.REFUGEE: "This world is so dangerous... I'm just trying to survive.",
            NPCType.MERCHANT: "Looking for supplies? I might have something useful.",
            NPCType.JEDI_SURVIVOR: "The Force is strong in this place, but so is the darkness.",
            NPCType.REPUBLIC: "Keep fighting the good fight, friend.",
            NPCType.CHILD: "Are you a Jedi? You look brave!",
            NPCType.INJURED_PILOT: "My ship's in bad shape, but I'll manage.",
            NPCType.RESEARCHER: "This planet holds many secrets...",
        }
        return defaults.get(npc.npc_type, "Hello there, traveler.")

    # ------------------------------------------------------------ lifecycle
    def accept_quest(self, quest, player, game=None) -> bool:
        if not quest or quest.state != QuestState.AVAILABLE:
            return False
        quest.state = QuestState.ACTIVE
        quest.start_turn = getattr(game, 'turn_count', 0) if game is not None else 0
        self.active_quests[quest.id] = quest
        self.quest_log.append(quest)
        if game is not None:
            self._setup_objective(quest, game)
        return True

    def _random_spot(self, game, origin, rmin, rmax):
        from jedi_fugitive.game.level import Display
        gm = game.game_map
        mh, mw = len(gm), len(gm[0]) if gm else 0
        floor = getattr(Display, 'FLOOR', '.')
        for _ in range(600):
            ang = random.random() * math.tau
            r = random.randint(rmin, rmax)
            x = int(origin[0] + math.cos(ang) * r)
            y = int(origin[1] + math.sin(ang) * r)
            if 2 <= x < mw - 2 and 2 <= y < mh - 2 and gm[y][x] == floor:
                return (x, y)
        return None

    def _setup_objective(self, quest, game):
        npc = quest.npc
        origin = (npc.x, npc.y)
        if quest.kind == 'recover':
            spot = self._random_spot(game, origin, 18, 45)
            if spot:
                quest.target = spot
                game.game_map[spot[1]][spot[0]] = 'E'
                game.items_on_map.append({'x': spot[0], 'y': spot[1], 'token': 'E', 'name': quest.item_name,
                                          'type': 'quest_token', 'quest_id': quest.id,
                                          'description': f"The {quest.item_name.lower()} {npc.name} asked you to find."})
        elif quest.kind == 'escort':
            quest.target = self._random_spot(game, origin, 20, 40)
            npc.following = True
        elif quest.kind == 'scout':
            tombs = list(getattr(game, 'tomb_entrances', []) or [])
            if tombs:
                quest.target = min(tombs, key=lambda t: abs(t[0] - npc.x) + abs(t[1] - npc.y))
            else:
                quest.target = self._random_spot(game, origin, 20, 40)
        elif quest.kind == 'hunt':
            from jedi_fugitive.game import enemies_sith as sith
            spot = self._random_spot(game, origin, 20, 45)
            if spot:
                e = sith.create_sith_warrior(level=max(1, getattr(game.player, 'level', 1) + 1))
                e.name = random.choice(["Patrol Leader Vex", "Lieutenant Karsh", "Hunter Dral"])
                e.x, e.y = spot
                e.quest_target = quest.id
                game.enemies.append(e)
                quest.target_enemy = e
                quest.target = spot
        try:
            from jedi_fugitive.game.map_features import ensure_reachable
            if quest.target:
                ensure_reachable(game, [quest.target])
        except Exception:
            pass

    def _take_delivery(self, quest, game) -> bool:
        inv = getattr(game.player, 'inventory', []) or []
        for it in list(inv):
            iid = it.get('id') if isinstance(it, dict) else getattr(it, 'id', None)
            if iid in HEALING_IDS:
                inv.remove(it)
                game.add_message(f"You give {quest.npc.name} your {it.get('name', 'supplies') if isinstance(it, dict) else 'supplies'}.")
                return True
        return False

    def update_quests(self, game):
        """Advance objectives once per world tick."""
        for quest in list(self.active_quests.values()):
            try:
                self._update_one(quest, game)
            except Exception:
                continue

    def _update_one(self, quest, game):
        npc = quest.npc
        px, py = game.player.x, game.player.y
        if quest.kind == 'hunt' and not quest.done:
            e = quest.target_enemy
            if e is None or getattr(e, 'hp', 0) <= 0 or e not in game.enemies:
                quest.done = True
                game.add_message(f"#6#Quest: {quest.title}#0# - target eliminated. Report to {npc.name}.")
        elif quest.kind == 'recover' and not quest.done:
            inv = getattr(game.player, 'inventory', []) or []
            if any(isinstance(i, dict) and i.get('quest_id') == quest.id for i in inv):
                quest.done = True
                game.add_message(f"#6#Quest: {quest.title}#0# - you have the {quest.item_name.lower()}. Return to {npc.name}.")
        elif quest.kind == 'scout' and not quest.done and quest.target:
            if abs(px - quest.target[0]) + abs(py - quest.target[1]) <= 3:
                quest.done = True
                game.add_message(f"#6#Quest: {quest.title}#0# - location surveyed. Report to {npc.name}.")
        elif quest.kind == 'escort' and getattr(npc, 'following', False):
            self._follow(npc, game)
            if quest.target and max(abs(npc.x - quest.target[0]), abs(npc.y - quest.target[1])) <= 2:
                npc.following = False
                quest.done = True
                game.add_message(f"{npc.name}: {quest.completion_text}")
                self.finish(quest, game)

    def _follow(self, npc, game):
        """Escorted NPCs path towards you (short BFS around walls); if they fall far
        behind they catch up next to you. Keeps npcs_on_map in sync."""
        from collections import deque
        from jedi_fugitive.game.level import BLOCKING_TILES
        px, py = game.player.x, game.player.y
        if max(abs(npc.x - px), abs(npc.y - py)) <= 1:
            npc._lag = 0
            return
        gm = game.game_map
        mh, mw = len(gm), len(gm[0])
        occupied = {(getattr(e, 'x', None), getattr(e, 'y', None)) for e in game.enemies}
        start = (npc.x, npc.y)
        prev = {start: None}
        q = deque([start])
        goal = None
        while q:
            c = q.popleft()
            if max(abs(c[0] - px), abs(c[1] - py)) <= 1 and c != (px, py):
                goal = c
                break
            if abs(c[0] - start[0]) + abs(c[1] - start[1]) > 40:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                n = (c[0] + dx, c[1] + dy)
                if 0 <= n[0] < mw and 0 <= n[1] < mh and n not in prev and gm[n[1]][n[0]] not in BLOCKING_TILES \
                        and n not in occupied and n != (px, py) and (n not in game.npcs_on_map or n == start):
                    prev[n] = c
                    q.append(n)
        step = None
        if goal is not None:
            c = goal
            while prev[c] is not None and prev[c] != start:
                c = prev[c]
            step = c if prev[c] is not None else None
        npc._lag = getattr(npc, '_lag', 0) + (0 if step else 1)
        if step is None and npc._lag >= 3:
            # lost you: catch up on a free tile next to you
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                n = (px + dx, py + dy)
                if 0 <= n[0] < mw and 0 <= n[1] < mh and gm[n[1]][n[0]] not in BLOCKING_TILES \
                        and n not in occupied and n not in game.npcs_on_map:
                    step = n
                    break
        if step:
            game.npcs_on_map.pop((npc.x, npc.y), None)
            npc.x, npc.y = step
            game.npcs_on_map[step] = npc

    def finish(self, quest, game) -> Dict[str, int]:
        """Pay out rewards and close the quest."""
        if quest.state != QuestState.ACTIVE:
            return {}
        quest.state = QuestState.COMPLETED
        self.active_quests.pop(quest.id, None)
        self.completed_quests.append(quest)
        p = game.player
        rewards = {'experience': quest.xp_reward}
        try:
            p.gain_xp(quest.xp_reward)
        except Exception:
            pass
        # remove the quest token from the pack
        try:
            p.inventory[:] = [i for i in p.inventory if not (isinstance(i, dict) and i.get('quest_id') == quest.id)]
        except Exception:
            pass
        # a useful item, from the registry
        try:
            from jedi_fugitive.items import registry
            from jedi_fugitive.items.tokens import TOKEN_MAP
            tok = random.choice(['+', '+', '!', 'c', 'f', 'h', 'i', 'l'])
            item = registry.materialize(TOKEN_MAP[tok])
            if len(p.inventory) < int(getattr(game, 'max_inventory', 9) or 9):
                p.inventory.append(item)
                game.add_message(f"{quest.npc.name} gives you: {registry.item_name(item)}.")
        except Exception:
            pass
        faction = QUEST_FACTION.get(quest.npc.npc_type)
        fm = getattr(p, 'faction_manager', None)
        if faction and fm is not None:
            try:
                fm.adjust_reputation(faction, 10)
                rewards['reputation'] = 10
            except Exception:
                pass
        # helping people pulls you towards the light
        try:
            p.dark_corruption = max(0, int(getattr(p, 'dark_corruption', 0) or 0) - 2)
        except Exception:
            pass
        # Jedi survivors share what they know: codex entries
        if quest.npc.npc_type == NPCType.JEDI_SURVIVOR and getattr(game, 'sith_codex', None) is not None:
            try:
                cx = game.sith_codex
                pool = [(c, e) for c, es in cx.categories.items() for e in es if (c, e) not in cx.discovered_entries]
                for c, e in random.sample(pool, min(2, len(pool))):
                    game._register_codex_discovery(p, c, e)
            except Exception:
                pass
        game.add_message(f"#6#Quest complete: {quest.title}#0# (+{quest.xp_reward} XP)")
        try:
            p.add_to_travel_log(f"[QUEST] {quest.title}: I helped {quest.npc.name}. {quest.completion_text}")
        except Exception:
            pass
        quest.npc.relationship_level = min(100, quest.npc.relationship_level + 40)
        return rewards

    # compatibility wrapper
    def complete_quest(self, quest, player, game=None) -> Dict[str, int]:
        if game is None:
            return {}
        return self.finish(quest, game)

    def get_nearest_npc(self, player_x: int, player_y: int, max_distance: int = 1) -> Optional[QuestNPC]:
        best = None
        for npc in self.available_npcs:
            d = max(abs(npc.x - player_x), abs(npc.y - player_y))
            if d <= max_distance and (best is None or d < best[0]):
                best = (d, npc)
        return best[1] if best else None
