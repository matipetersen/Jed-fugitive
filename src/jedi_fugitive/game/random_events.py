"""
Random Events Generator
Creates dynamic, contextual events that respond to player actions and game state.
"""

import random
from typing import List, Dict, Any, Tuple


class RandomEvent:
    def __init__(self, name: str, description: str, event_type: str, 
                 condition_func=None, effect_func=None, choices=None):
        self.name = name
        self.description = description
        self.event_type = event_type  # 'beneficial', 'neutral', 'hostile', 'choice'
        self.condition_func = condition_func  # Function to check if event can trigger
        self.effect_func = effect_func  # Function to apply event effects
        self.choices = choices or []  # List of choice options for choice events


# Event condition functions
def condition_low_health(game) -> bool:
    """Trigger when player has low health."""
    try:
        return game.player.hp < (game.player.max_hp * 0.3)
    except:
        return False


def condition_many_enemies(game) -> bool:
    """Trigger when many enemies are nearby."""
    try:
        player_x, player_y = game.player.x, game.player.y
        nearby_enemies = 0
        for enemy in game.enemies:
            distance = abs(enemy.x - player_x) + abs(enemy.y - player_y)
            if distance <= 8:
                nearby_enemies += 1
        return nearby_enemies >= 3
    except:
        return False


def condition_high_level(game) -> bool:
    """Trigger for high-level players."""
    try:
        return getattr(game.player, 'level', 1) >= 5
    except:
        return False


def condition_has_materials(game) -> bool:
    """Trigger when player has crafting materials."""
    try:
        material_count = 0
        for item in game.player.inventory:
            if isinstance(item, dict) and item.get('type') == 'material':
                material_count += 1
            elif hasattr(item, 'type') and item.type == 'material':
                material_count += 1
        return material_count >= 3
    except:
        return False


def condition_force_abilities(game) -> bool:
    """Trigger when player has Force abilities."""
    try:
        return len(getattr(game.player, 'force_abilities', [])) >= 2
    except:
        return False


# Event effect functions
def effect_heal_player(game) -> str:
    """Heal the player."""
    try:
        heal_amount = random.randint(15, 30)
        old_hp = game.player.hp
        game.player.hp = min(game.player.max_hp, game.player.hp + heal_amount)
        actual_heal = game.player.hp - old_hp
        return f"Restored {actual_heal} health points."
    except:
        return "Health restoration failed."


def effect_add_materials(game) -> str:
    """Give player random crafting materials."""
    try:
        from jedi_fugitive.items.crafting import MATERIALS
        common_materials = [m for m in MATERIALS if m.rarity in ['Common', 'Uncommon']]
        
        if common_materials:
            material = random.choice(common_materials)
            material_item = {
                'name': material.name,
                'type': 'material',
                'description': material.description,
                'rarity': material.rarity
            }
            game.player.inventory.append(material_item)
            return f"Found {material.name}!"
        return "Found some useful materials."
    except:
        return "Material discovery failed."


def effect_force_vision(game) -> str:
    """Give player a Force vision with helpful info."""
    try:
        visions = [
            "You sense a powerful presence to the north...",
            "The Force whispers of hidden dangers ahead.",
            "Ancient echoes guide you toward valuable secrets.",
            "You feel the pull of a Sith tomb in the distance.",
            "Dark energy emanates from the eastern regions.",
            "The Force reveals the location of nearby enemies.",
            "Whispers of the past warn of impending conflict."
        ]
        return random.choice(visions)
    except:
        return "The Force remains silent."


def effect_enemy_ambush(game) -> str:
    """Spawn enemies near player."""
    try:
        from jedi_fugitive.game import enemies_sith as sith
        
        # Spawn 1-2 enemies nearby
        num_enemies = random.randint(1, 2)
        spawned = 0
        
        for _ in range(num_enemies):
            # Find nearby spawn location (at least 3 tiles away for fairness)
            for attempt in range(20):
                # Generate spawn offset ensuring minimum distance of 3 tiles
                # Use simple grid-based approach instead of trigonometry
                dx = random.randint(-7, 7)
                dy = random.randint(-7, 7)
                
                # Ensure minimum distance of 3 tiles
                if abs(dx) + abs(dy) < 3:
                    continue
                
                spawn_x = game.player.x + dx
                spawn_y = game.player.y + dy
                
                # Check bounds and floor
                if (0 <= spawn_x < len(game.game_map[0]) and 
                    0 <= spawn_y < len(game.game_map) and
                    game.game_map[spawn_y][spawn_x] == '.'):
                    
                    enemy_level = max(1, getattr(game.player, 'level', 1) + random.randint(-1, 1))
                    enemy = sith.create_sith_warrior(level=enemy_level, x=spawn_x, y=spawn_y)
                    enemy.name += " (Ambusher)"
                    game.enemies.append(enemy)
                    spawned += 1
                    break
        
        return f"{spawned} hostile(s) emerge from hiding!" if spawned else "Something stirs in the shadows..."
    except:
        return "You sense movement in the darkness."


def effect_equipment_boost(game) -> str:
    """Temporarily boost player stats."""
    try:
        # Apply temporary bonuses (these would need to be tracked separately)
        boost_type = random.choice(['attack', 'defense', 'accuracy'])
        boost_amount = random.randint(2, 5)
        
        if boost_type == 'attack':
            game.player.attack += boost_amount
            return f"The Force enhances your combat prowess! (+{boost_amount} Attack)"
        elif boost_type == 'defense':
            game.player.defense += boost_amount
            return f"Dark energy hardens your resolve! (+{boost_amount} Defense)"
        else:
            game.player.accuracy += boost_amount
            return f"Your focus sharpens dramatically! (+{boost_amount} Accuracy)"
    except:
        return "You feel a surge of power."


# Define random events
RANDOM_EVENTS = [
    # Beneficial Events
    RandomEvent(
        "Abandoned Med-Kit",
        "You discover an emergency medical kit left behind by previous crash survivors.",
        "beneficial",
        condition_low_health,
        effect_heal_player
    ),
    
    RandomEvent(
        "Salvage Discovery",
        "Hidden among the debris, you find useful crafting materials.",
        "beneficial",
        condition_has_materials,
        effect_add_materials
    ),
    
    RandomEvent(
        "Force Nexus",
        "You step into a location strong with the Force. Visions flood your mind.",
        "beneficial",
        condition_force_abilities,
        effect_force_vision
    ),
    
    RandomEvent(
        "Ancient Cache",
        "An old Sith cache yields valuable materials and equipment enhancements.",
        "beneficial",
        condition_high_level,
        effect_equipment_boost
    ),
    
    # Hostile Events
    RandomEvent(
        "Sith Patrol",
        "A Sith patrol has been tracking your movements. They attack without warning!",
        "hostile",
        condition_many_enemies,
        effect_enemy_ambush
    ),
    
    RandomEvent(
        "Disturbed Nest",
        "Your presence has awakened something that should have stayed sleeping...",
        "hostile",
        lambda game: len(getattr(game, 'enemies', [])) < 15,  # Only when not overwhelmed
        effect_enemy_ambush
    ),
    
    # Neutral/Atmospheric Events
    RandomEvent(
        "Eerie Silence",
        "An unnatural quiet settles over the area. Even the wind holds its breath.",
        "neutral",
        lambda game: True,  # Can always trigger
        lambda game: "The silence is broken only by your own footsteps."
    ),
    
    RandomEvent(
        "Crashed Speeder",
        "You find the wreckage of a speeder bike, its rider long gone.",
        "neutral",
        lambda game: True,
        lambda game: "You search the wreckage but find nothing of immediate use."
    ),
    
    RandomEvent(
        "Force Echo",
        "The Force shows you glimpses of what happened here before the crash.",
        "neutral",
        condition_force_abilities,
        lambda game: "Images of panic and desperation flash through your mind."
    ),
]


# Choice-based events
CHOICE_EVENTS = [
    {
        "name": "Mysterious Container",
        "description": "You discover a sealed container with Sith markings. It might contain valuable items, but opening it could be dangerous.",
        "choices": {
            "Open carefully": {
                "description": "Use the Force to sense for traps before opening.",
                "effect": lambda game: effect_add_materials(game) if random.random() < 0.7 else "The container was empty, but you avoided any traps."
            },
            "Force it open": {
                "description": "Ignore caution and break it open immediately.",
                "effect": lambda game: effect_add_materials(game) if random.random() < 0.9 else effect_enemy_ambush(game)
            },
            "Leave it alone": {
                "description": "Better safe than sorry. Continue without investigating.",
                "effect": lambda game: "Sometimes discretion is the better part of valor."
            }
        }
    },
    
    {
        "name": "Wounded Creature",
        "description": "A native creature lies wounded near some wreckage. It's not hostile, but approaches you warily.",
        "choices": {
            "Heal with Force": {
                "description": "Use Force healing to help the creature.",
                "effect": lambda game: "The creature chirps gratefully and bounds away, leaving you with a sense of peace." if random.random() < 0.8 else effect_heal_player(game)
            },
            "Share supplies": {
                "description": "Give it some of your medical supplies.",
                "effect": lambda game: "The creature recovers and leads you to a hidden cache!" if random.random() < 0.5 else "You feel good about helping, though it costs you supplies."
            },
            "Ignore it": {
                "description": "Focus on your mission. Time is precious.",
                "effect": lambda game: "You continue on your path, leaving the creature behind."
            }
        }
    },
]


def get_random_event(game) -> RandomEvent:
    """Get a random event that can trigger based on current conditions."""
    available_events = []
    used_events = getattr(game, 'used_random_events', set())
    
    for event in RANDOM_EVENTS:
        try:
            # Skip if already used
            if event.name in used_events:
                continue
            # Check if event condition is met
            if event.condition_func is None or event.condition_func(game):
                available_events.append(event)
        except:
            continue  # Skip events with broken conditions
    
    if not available_events:
        # Fallback neutral event
        return RandomEvent(
            "Moment of Reflection",
            "You pause for a moment to gather your thoughts and assess your situation.",
            "neutral",
            lambda game: True,
            lambda game: "The brief rest helps you focus on the challenges ahead."
        )
    
    selected = random.choice(available_events)
    # Mark as used
    if not hasattr(game, 'used_random_events'):
        game.used_random_events = set()
    game.used_random_events.add(selected.name)
    
    return selected


def get_choice_event(game) -> Dict[str, Any]:
    """Get a choice-based event."""
    if not CHOICE_EVENTS:
        return None
    
    return random.choice(CHOICE_EVENTS)


def trigger_random_event(game) -> bool:
    """Main function to potentially trigger a random event."""
    try:
        # Check if in tomb/dungeon - no random events there
        if getattr(game, 'in_special_dungeon', False) or getattr(game, 'in_tomb', False):
            return False
        
        # Random chance to trigger event (adjustable)
        if random.random() > 0.05:  # 5% chance per turn
            return False
        
        # Choose between simple event or choice event
        if random.random() < 0.7:  # 70% chance for simple event
            event = get_random_event(game)
            
            # Apply event using popup menu
            try:
                # Build popup content
                popup_content = [event.description, ""]
                
                if event.effect_func:
                    result = event.effect_func(game)
                    if result:
                        popup_content.append(f"→ {result}")
                        popup_content.append("")
                        
                        # Check if this was a beneficial event that should grant additional rewards
                        if event.event_type == 'beneficial' and 'found' in result.lower():
                            try:
                                from jedi_fugitive.game.reward_system import apply_random_event_reward
                                # Give small additional benefit for finding things
                                bonus_reward = apply_random_event_reward(game, 'materials')
                                if 'crafting material' in bonus_reward.lower():
                                    popup_content.append(f"→ {bonus_reward}")
                                    popup_content.append("")
                            except:
                                pass
                
                popup_content.append("Press any key to continue...")
                
                # Show in popup menu
                if hasattr(game.ui, 'centered_menu'):
                    game.ui.centered_menu(popup_content, f"Event: {event.name}")
                    # Brief confirmation message
                    game.ui.messages.add(f"#3#[EVENT]#0# {event.name}")
                else:
                    # Fallback to messages if no UI
                    game.ui.messages.add(f"#3#[EVENT]#0# {event.name}")
                    for line in popup_content[:-1]:  # Skip "Press any key" line
                        if line:
                            game.ui.messages.add(line)
                        
                return True
            except:
                return False
        else:
            # Choice event with interactive popup
            choice_event = get_choice_event(game)
            if choice_event:
                try:
                    # Build menu options from choices
                    choices = choice_event.get('choices', {})
                    if not choices:
                        return False
                    
                    # Create menu items
                    menu_items = [choice_event['description'], ""]  # Description + separator
                    choice_keys = list(choices.keys())
                    
                    for choice_key in choice_keys:
                        choice_data = choices[choice_key]
                        menu_items.append(f"{choice_key}: {choice_data['description']}")
                    
                    # Show popup menu
                    if hasattr(game.ui, 'centered_menu'):
                        selection = game.ui.centered_menu(menu_items, title=f"Event: {choice_event['name']}")
                        
                        # Handle selection (adjust for description lines)
                        if selection is not None and selection >= 2 and selection < len(menu_items):
                            selected_choice = choice_keys[selection - 2]  # -2 for description and separator
                            choice_data = choices[selected_choice]
                            
                            # Apply effect
                            game.ui.messages.add(f"#3#[EVENT]#0# {choice_event['name']}")
                            game.ui.messages.add(f"You chose: {selected_choice}")
                            
                            if 'effect' in choice_data and callable(choice_data['effect']):
                                result = choice_data['effect'](game)
                                if result:
                                    game.ui.messages.add(f"→ {result}")
                            
                            return True
                        else:
                            # No selection made
                            game.ui.messages.add(f"#3#[EVENT]#0# {choice_event['name']}")
                            game.ui.messages.add("You decide to move on without acting.")
                            return True
                    else:
                        # Fallback if no UI menu available
                        game.ui.messages.add(f"#3#[EVENT]#0# {choice_event['name']}")
                        game.ui.messages.add(choice_event['description'])
                        game.ui.messages.add("(Interactive menu not available)")
                        return True
                except Exception as e:
                    # Debug: Log the error
                    try:
                        game.ui.messages.add(f"Event error: {e}")
                    except:
                        pass
                    return False
        
        return False
    except:
        return False


def should_trigger_random_event(turn_count: int) -> bool:
    """Determine if random events should be checked this turn."""
    # Much less frequent to reduce spam
    base_chance = 0.005  # 0.5% base chance (reduced from 2%)
    turn_bonus = min(0.01, turn_count * 0.00005)  # Up to 1% bonus over time (reduced)
    total_chance = base_chance + turn_bonus
    
    return random.random() < total_chance