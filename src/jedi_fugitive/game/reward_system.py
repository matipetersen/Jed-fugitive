"""
Reward Application System
Handles applying rewards from various game events (environmental, random, fauna, etc.)
"""

def apply_narrative_reward(game, reward_type):
    """Apply a narrative event reward to the player."""
    if not reward_type:
        return "No reward applied."
    
    try:
        player = game.player
        
        if reward_type == 'force_insight':
            # Grant Force points and temporary vision
            force_gain = 3
            player.force_points = min(
                getattr(player, 'max_force_points', 20), 
                getattr(player, 'force_points', 0) + force_gain
            )
            
            # Add insight to journal
            try:
                if hasattr(player, 'add_log_entry'):
                    player.add_log_entry(
                        "A moment of clarity revealed hidden truths about this world. "
                        "The Force flows more freely through me now.", 
                        getattr(game, 'turn_count', 0)
                    )
            except:
                pass
                
            return f"Gained {force_gain} Force points and valuable insight!"
            
        elif reward_type == 'force_power':
            # Grant temporary attack boost and Force points
            attack_boost = 2
            force_gain = 2
            
            player.attack = getattr(player, 'attack', 10) + attack_boost
            player.force_points = min(
                getattr(player, 'max_force_points', 20),
                getattr(player, 'force_points', 0) + force_gain
            )
            
            # Mark as temporary boost (for tracking)
            if not hasattr(player, 'temporary_boosts'):
                player.temporary_boosts = {}
            player.temporary_boosts['dark_power'] = {
                'attack': attack_boost,
                'duration': 50  # turns
            }
            
            return f"Dark power surges through you! (+{attack_boost} Attack, +{force_gain} Force)"
            
        elif reward_type == 'cave_location':
            # Reveal nearby tomb or hidden cache location
            try:
                if hasattr(game, 'tomb_entrances') and game.tomb_entrances:
                    # Find nearest tomb
                    px, py = player.x, player.y
                    nearest_tomb = None
                    min_distance = float('inf')
                    
                    for tx, ty in game.tomb_entrances:
                        distance = abs(tx - px) + abs(ty - py)
                        if distance < min_distance:
                            min_distance = distance
                            nearest_tomb = (tx, ty)
                    
                    if nearest_tomb:
                        tx, ty = nearest_tomb
                        # Add direction hint
                        dx = tx - px
                        dy = ty - py
                        
                        if abs(dx) > abs(dy):
                            direction = "east" if dx > 0 else "west"
                        else:
                            direction = "north" if dy < 0 else "south"
                            
                        return f"You sense a hidden tomb entrance to the {direction}!"
                        
            except:
                pass
            return "You gain knowledge of hidden places in this area."
            
        elif reward_type == 'healing_herbs':
            # Add healing items to inventory
            try:
                herb_item = {
                    'name': 'Healing Herbs',
                    'type': 'consumable',
                    'description': 'Natural herbs with restorative properties.',
                    'effect': {'heal': 15},
                    'value': 25
                }
                player.inventory.append(herb_item)
                return "Found medicinal herbs! (Heals 15 HP when used)"
            except:
                return "Found some useful healing supplies."
                
        elif reward_type == 'materials':
            # Add crafting materials
            try:
                from jedi_fugitive.items.crafting import MATERIALS
                common_materials = [m for m in MATERIALS if m.rarity == 'Common']
                
                if common_materials:
                    import random
                    material = random.choice(common_materials)
                    material_item = {
                        'name': material.name,
                        'type': 'material',
                        'description': material.description,
                        'rarity': material.rarity,
                        'value': 20
                    }
                    player.inventory.append(material_item)
                    return f"Found crafting material: {material.name}!"
            except:
                pass
            return "Found some useful crafting materials."
            
        elif reward_type == 'weapon_upgrade':
            # Temporarily boost equipped weapon
            try:
                equipped_weapon = getattr(player, 'equipped_weapon', None)
                if equipped_weapon:
                    if not hasattr(player, 'weapon_enhancements'):
                        player.weapon_enhancements = {}
                    
                    enhancement_key = f"battlefield_blessing_{getattr(game, 'turn_count', 0)}"
                    player.weapon_enhancements[enhancement_key] = {
                        'attack_bonus': 3,
                        'duration': 30
                    }
                    
                    # Apply immediately
                    player.attack += 3
                    return "Your weapon gleams with enhanced power! (+3 Attack for 30 turns)"
            except:
                pass
            return "You feel your combat skills sharpened by experience."
            
        elif reward_type == 'force_vision':
            # Grant temporary enhanced perception
            try:
                if not hasattr(player, 'active_effects'):
                    player.active_effects = {}
                    
                player.active_effects['force_vision'] = {
                    'evasion_bonus': 2,
                    'accuracy_bonus': 5,
                    'duration': 25
                }
                
                player.evasion = getattr(player, 'evasion', 10) + 2
                player.accuracy = getattr(player, 'accuracy', 75) + 5
                
                return "The Force grants you enhanced perception! (+2 Evasion, +5 Accuracy for 25 turns)"
            except:
                pass
            return "Visions of the future guide your steps."
            
        elif reward_type == 'energy_boost':
            # Restore Force and reduce stress
            try:
                force_restore = 5
                stress_reduce = 15
                
                player.force_points = min(
                    getattr(player, 'max_force_points', 20),
                    getattr(player, 'force_points', 0) + force_restore
                )
                
                if hasattr(player, 'reduce_stress'):
                    player.reduce_stress(stress_reduce)
                else:
                    player.stress = max(0, getattr(player, 'stress', 0) - stress_reduce)
                    
                return f"You feel refreshed and energized! (+{force_restore} Force, -{stress_reduce} Stress)"
            except:
                pass
            return "You feel reinvigorated by your experience."
            
        elif reward_type in ['scrap_metal', 'energy_cell', 'durasteel']:
            # Specific material rewards
            try:
                material_names = {
                    'scrap_metal': 'Scrap Metal',
                    'energy_cell': 'Power Cell', 
                    'durasteel': 'Durasteel Plate'
                }
                
                material_item = {
                    'name': material_names.get(reward_type, reward_type.replace('_', ' ').title()),
                    'type': 'material',
                    'description': f'{material_names.get(reward_type, reward_type)} for crafting.',
                    'rarity': 'Common',
                    'value': 15
                }
                player.inventory.append(material_item)
                return f"Salvaged {material_item['name']}!"
            except:
                pass
            return f"Found {reward_type.replace('_', ' ')}."
            
        else:
            # Generic reward - small benefit
            try:
                # Small HP heal as fallback
                heal_amount = 5
                old_hp = player.hp
                player.hp = min(
                    getattr(player, 'max_hp', 100), 
                    getattr(player, 'hp', 0) + heal_amount
                )
                actual_heal = player.hp - old_hp
                
                if actual_heal > 0:
                    return f"You feel slightly better. (+{actual_heal} HP)"
                else:
                    return "You gain a small benefit from your experience."
            except:
                pass
            return f"Gained: {reward_type.replace('_', ' ').title()}"
            
    except Exception as e:
        try:
            game.ui.messages.add(f"Reward application error: {e}")
        except:
            pass
        return "Reward could not be applied."


def apply_random_event_reward(game, reward_type):
    """Apply rewards from random events."""
    # Most random event rewards are handled by their effect functions
    # This is for any additional processing needed
    return apply_narrative_reward(game, reward_type)


def apply_fauna_reward(game, reward_type):
    """Apply rewards from fauna encounters."""
    # Fauna rewards are mostly handled in the fauna system
    # But we can add some special cases here
    if reward_type == 'creature_blessing':
        try:
            player = game.player
            # Temporary evasion boost
            evasion_boost = 3
            player.evasion = getattr(player, 'evasion', 10) + evasion_boost
            
            if not hasattr(player, 'active_effects'):
                player.active_effects = {}
            player.active_effects['creature_blessing'] = {
                'evasion_bonus': evasion_boost,
                'duration': 40
            }
            
            return f"The grateful creature's blessing enhances your agility! (+{evasion_boost} Evasion for 40 turns)"
        except:
            pass
        return "A creature's blessing protects you."
    
    return apply_narrative_reward(game, reward_type)


def tick_temporary_effects(game):
    """Process temporary effects each turn (call from game loop)."""
    try:
        player = game.player
        
        # Process temporary boosts
        if hasattr(player, 'temporary_boosts'):
            expired_boosts = []
            for boost_name, boost_data in player.temporary_boosts.items():
                boost_data['duration'] -= 1
                if boost_data['duration'] <= 0:
                    expired_boosts.append(boost_name)
                    # Remove the boost effect
                    if 'attack' in boost_data:
                        player.attack = max(1, player.attack - boost_data['attack'])
                        try:
                            game.ui.messages.add(f"Your {boost_name.replace('_', ' ')} fades away.")
                        except:
                            pass
            
            for boost_name in expired_boosts:
                del player.temporary_boosts[boost_name]
        
        # Process active effects
        if hasattr(player, 'active_effects'):
            expired_effects = []
            for effect_name, effect_data in player.active_effects.items():
                effect_data['duration'] -= 1
                if effect_data['duration'] <= 0:
                    expired_effects.append(effect_name)
                    # Remove effect bonuses
                    if 'evasion_bonus' in effect_data:
                        player.evasion = max(0, player.evasion - effect_data['evasion_bonus'])
                    if 'accuracy_bonus' in effect_data:
                        player.accuracy = max(0, player.accuracy - effect_data['accuracy_bonus'])
                        
                    try:
                        game.ui.messages.add(f"The {effect_name.replace('_', ' ')} effect wears off.")
                    except:
                        pass
            
            for effect_name in expired_effects:
                del player.active_effects[effect_name]
        
        # Process weapon enhancements
        if hasattr(player, 'weapon_enhancements'):
            expired_enhancements = []
            for enhancement_name, enhancement_data in player.weapon_enhancements.items():
                enhancement_data['duration'] -= 1
                if enhancement_data['duration'] <= 0:
                    expired_enhancements.append(enhancement_name)
                    if 'attack_bonus' in enhancement_data:
                        player.attack = max(1, player.attack - enhancement_data['attack_bonus'])
                        try:
                            game.ui.messages.add("Your weapon's enhancement fades.")
                        except:
                            pass
            
            for enhancement_name in expired_enhancements:
                del player.weapon_enhancements[enhancement_name]
                
    except Exception as e:
        # Don't break the game if effect processing fails
        try:
            game.ui.messages.add(f"Effect processing error: {e}")
        except:
            pass


def apply_environmental_reward(player, event, ui, inventory):
    """Apply rewards from environmental events based on event content"""
    try:
        import random
        
        # Parse environmental event for reward keywords
        event_text = ' '.join(event.get('description', []) + [event.get('title', '')]).lower()
        
        # Force insight rewards
        if any(word in event_text for word in ['ancient', 'wisdom', 'knowledge', 'understanding', 'insight', 'meditation']):
            player.force_points += 3
            ui.messages.add("#3#[INSIGHT]#0# Ancient wisdom flows through you! (+3 Force Points)")
            # Add journal entry
            if hasattr(player, 'journal'):
                player.journal.append(f"Discovered ancient wisdom at coordinates ({player.x}, {player.y})")
        
        # Healing rewards
        if any(word in event_text for word in ['spring', 'pool', 'water', 'refreshing', 'healing', 'restore']):
            heal_amount = min(20, getattr(player, 'max_health', 100) - getattr(player, 'health', 50))
            if heal_amount > 0:
                player.health = getattr(player, 'health', 50) + heal_amount
                ui.messages.add(f"#2#[HEALING]#0# The waters restore you! (+{heal_amount} Health)")
            
            # Add healing herbs to inventory
            try:
                from jedi_fugitive.items.consumables import create_consumable
                herbs = create_consumable('healing_herb')
                if inventory.add_item(herbs):
                    ui.messages.add("#2#[DISCOVERY]#0# Gathered healing herbs!")
            except:
                # Fallback: add to crafting materials
                if not hasattr(inventory, 'crafting_materials'):
                    inventory.crafting_materials = {}
                if 'herbs' not in inventory.crafting_materials:
                    inventory.crafting_materials['herbs'] = 0
                inventory.crafting_materials['herbs'] += 1
                ui.messages.add("#2#[DISCOVERY]#0# Gathered healing herbs!")
        
        # Material rewards
        if any(word in event_text for word in ['crystal', 'mineral', 'ore', 'metal', 'resource', 'cache']):
            materials = ['crystal', 'durasteel', 'cortosis']
            material = random.choice(materials)
            if not hasattr(inventory, 'crafting_materials'):
                inventory.crafting_materials = {}
            if material not in inventory.crafting_materials:
                inventory.crafting_materials[material] = 0
            amount = random.randint(1, 3)
            inventory.crafting_materials[material] += amount
            ui.messages.add(f"#2#[MATERIALS]#0# Found {amount} {material}!")
        
        # Force power enhancement
        if any(word in event_text for word in ['power', 'energy', 'nexus', 'connection', 'strong', 'amplify']):
            if not hasattr(player, 'temporary_effects'):
                player.temporary_effects = {}
            player.temporary_effects['force_nexus'] = {'duration': 25, 'force_regen': 1, 'accuracy': 5}
            ui.messages.add("#3#[NEXUS]#0# Force nexus enhances your abilities! (+1 Force regen, +5 Accuracy for 25 turns)")
        
        # Vision/perception enhancement
        if any(word in event_text for word in ['vision', 'sight', 'see', 'reveal', 'clarity', 'perception']):
            if not hasattr(player, 'temporary_effects'):
                player.temporary_effects = {}
            player.temporary_effects['enhanced_sight'] = {'duration': 30, 'evasion': 2, 'accuracy': 3}
            # Apply immediate bonuses
            player.evasion = getattr(player, 'evasion', 10) + 2
            player.accuracy = getattr(player, 'accuracy', 75) + 3
            ui.messages.add("#3#[VISION]#0# Your perception sharpens! (+2 Evasion, +3 Accuracy for 30 turns)")
            
    except Exception as e:
        ui.messages.add(f"Error processing environmental reward: {e}")
        pass