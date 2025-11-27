"""
Merchant system for Dark Meridian.
Merchants spawn across biomes with faction-based inventories and dialogues.
"""
import random
from typing import List, Dict, Tuple, Optional


class MerchantFaction:
    """Merchant faction definitions with unique inventories and dialogues."""
    
    MANDALORIAN_SCOUTS = "mandalorian_scouts"
    REPUBLIC_SURVIVORS = "republic_survivors"
    SCAVENGER_LOOTERS = "scavenger_looters"
    NEUTRAL_TRADERS = "neutral_traders"
    BLACK_MARKET = "black_market"
    JEDI_REFUGEE = "jedi_refugee"
    

FACTION_DATA = {
    MerchantFaction.MANDALORIAN_SCOUTS: {
        "name": "Mandalorian Scout",
        "camp_name": "Mandalorian Outpost",
        "greeting": [
            "This is the Way. You looking to trade, traveler?",
            "Our clan has surplus gear. Make me an offer.",
            "Credits or barter - Mandalorians deal in both.",
            "I've seen worse-looking fugitives. What do you need?"
        ],
        "buy": [
            "A fair trade. The clan will be pleased.",
            "This will serve you well in battle.",
            "Beskar-quality merchandise. You won't regret it."
        ],
        "sell": [
            "I can use this. Here's your payment.",
            "Scavenged goods? I'll take it off your hands.",
            "Fair price. The clan appreciates good trade."
        ],
        "goodbye": [
            "Safe travels, dar'manda.",
            "May your armor hold against all foes.",
            "Watch your back out there."
        ],
        "inventory_types": ["weapons_melee", "armor_medium", "armor_heavy", "shields"],
        "markup": 1.3,  # 30% markup
        "buyback": 0.6,  # Buy items at 60% value
    },
    
    MerchantFaction.REPUBLIC_SURVIVORS: {
        "name": "Republic Officer",
        "camp_name": "Crashed Republic Ship",
        "greeting": [
            "Republic military surplus. We need to liquidate before evacuation.",
            "Soldier, we're stranded but well-supplied. Need anything?",
            "The Republic looks after its own. Let's deal.",
            "Our ship's grounded but our armory's intact. Interested?"
        ],
        "buy": [
            "Sold. For the Republic!",
            "Standard issue quality. You made the right choice.",
            "This gear served us well. May it serve you better."
        ],
        "sell": [
            "We can always use more supplies. Deal.",
            "I'll requisition this. Here's payment.",
            "The Republic thanks you for this contribution."
        ],
        "goodbye": [
            "May the Force be with you.",
            "Good luck out there, soldier.",
            "Stay sharp. The Sith are everywhere."
        ],
        "inventory_types": ["weapons_ranged", "armor_medium", "armor_light", "consumables"],
        "markup": 1.2,  # 20% markup
        "buyback": 0.7,  # Buy items at 70% value
    },
    
    MerchantFaction.SCAVENGER_LOOTERS: {
        "name": "Scavenger Boss",
        "camp_name": "Scavenger Camp",
        "greeting": [
            "Eh? You buy, you sell, you leave. Got it?",
            "I don't ask questions, you don't ask questions. Business is business.",
            "Found all this myself. Mostly. You interested or what?",
            "Credits talk, everything else walks. What'll it be?"
        ],
        "buy": [
            "It's yours. Now beat it.",
            "Pleasure doing business. Sort of.",
            "Take it and go before I change my mind."
        ],
        "sell": [
            "I'll take it off your hands. Here.",
            "This'll fetch a nice price. Deal.",
            "Not bad. Don't expect charity though."
        ],
        "goodbye": [
            "Yeah, yeah. Get lost.",
            "Watch yourself out there. Or don't. Whatever.",
            "Try not to die. Bad for repeat business."
        ],
        "inventory_types": ["weapons_all", "armor_light", "shields", "consumables"],
        "markup": 1.5,  # 50% markup (greedy)
        "buyback": 0.5,  # Buy items at 50% value
    },
    
    MerchantFaction.NEUTRAL_TRADERS: {
        "name": "Wandering Trader",
        "camp_name": "Trading Post",
        "greeting": [
            "Welcome, welcome! Best prices in the sector!",
            "A customer! Business has been slow. What can I get you?",
            "I trade with everyone - Sith, Jedi, doesn't matter. Credits are credits.",
            "You look like someone who appreciates quality goods."
        ],
        "buy": [
            "Excellent choice! You won't find better!",
            "Guaranteed quality. Come back anytime!",
            "A wise purchase. May it serve you well."
        ],
        "sell": [
            "I can work with this. Here's a fair offer.",
            "Interesting piece. I'll take it.",
            "You drive a hard bargain, but deal."
        ],
        "goodbye": [
            "Safe travels, friend!",
            "Come back soon! I restock frequently!",
            "May fortune smile upon you."
        ],
        "inventory_types": ["weapons_melee", "weapons_ranged", "armor_all", "shields", "consumables"],
        "markup": 1.4,  # 40% markup
        "buyback": 0.6,  # Buy items at 60% value
    },
    
    MerchantFaction.BLACK_MARKET: {
        "name": "Black Market Dealer",
        "camp_name": "Hidden Black Market",
        "greeting": [
            "Keep your voice down. You looking to buy or sell?",
            "No names, no records. Cash only. What do you need?",
            "I've got items the Sith don't want you to have.",
            "Dangerous goods for dangerous times. Interested?"
        ],
        "buy": [
            "This transaction never happened. Understand?",
            "Use it wisely. Or don't. Not my problem.",
            "You didn't get this from me."
        ],
        "sell": [
            "I know people who'll pay for this. Deal.",
            "No questions asked. Here's your cut.",
            "This'll move fast on the underground market."
        ],
        "goodbye": [
            "You were never here.",
            "Watch your six. Sith cultists are everywhere.",
            "Lose my location if you get caught."
        ],
        "inventory_types": ["weapons_rare", "armor_rare", "shields", "consumables"],
        "markup": 1.6,  # 60% markup (expensive but rare items)
        "buyback": 0.7,  # Buy items at 70% value (pays well)
    },
    
    MerchantFaction.JEDI_REFUGEE: {
        "name": "Former Jedi",
        "camp_name": "Jedi Refuge",
        "greeting": [
            "I sense... you're running too. The Force brought you here.",
            "Another survivor. I have supplies to share, for a price.",
            "The old ways are gone, but commerce remains. What do you seek?",
            "I feel your disturbance. Perhaps I can help lighten your burden."
        ],
        "buy": [
            "May the Force guide your path.",
            "Use this with wisdom, not vengeance.",
            "In these dark times, we must help each other."
        ],
        "sell": [
            "I'll make use of this. The Force provides.",
            "Thank you. Every resource helps us survive.",
            "Your generosity is noted. Here's fair payment."
        ],
        "goodbye": [
            "Trust in the Force.",
            "Stay hidden. The Inquisitors never stop hunting.",
            "May we both live to see better days."
        ],
        "inventory_types": ["weapons_melee", "armor_light", "consumables", "force_items"],
        "markup": 1.25,  # 25% markup (fair)
        "buyback": 0.65,  # Buy items at 65% value
    },
}


def get_faction_inventory(faction: str, player_level: int) -> List[Dict]:
    """Generate faction-specific inventory based on player level."""
    from jedi_fugitive.items.weapons import WEAPONS
    from jedi_fugitive.items.armor import ARMORS
    from jedi_fugitive.items.consumables import ITEM_DEFS
    
    faction_data = FACTION_DATA.get(faction, FACTION_DATA[MerchantFaction.NEUTRAL_TRADERS])
    inventory_types = faction_data["inventory_types"]
    inventory = []
    
    # Rarity weights based on player level
    rarity_weights = {
        'common': max(10, 80 - player_level * 3),
        'uncommon': min(40, 15 + player_level * 2),
        'rare': min(30, player_level * 2),
        'epic': min(15, max(0, player_level - 10)),
        'legendary': min(5, max(0, player_level - 20))
    }
    
    def should_include_rarity(rarity: str) -> bool:
        """Weighted chance to include an item based on rarity and player level."""
        weight = rarity_weights.get(rarity, 10)
        return random.randint(1, 100) <= weight
    
    # Filter weapons by type
    available_weapons = []
    for weapon in WEAPONS:
        weapon_rarity = getattr(weapon, 'rarity', 'common').lower()
        if not should_include_rarity(weapon_rarity):
            continue
            
        weapon_type = str(getattr(weapon, 'weapon_type', ''))
        
        # Faction filtering
        if "weapons_melee" in inventory_types:
            if any(melee in weapon_type for melee in ['VIBROBLADE', 'MELEE', 'LIGHTSABER', 'KNIFE', 'STAFF']):
                available_weapons.append(weapon)
        
        if "weapons_ranged" in inventory_types:
            if any(ranged in weapon_type for ranged in ['BLASTER', 'BOWCASTER', 'RANGED']):
                available_weapons.append(weapon)
        
        if "weapons_all" in inventory_types:
            available_weapons.append(weapon)
        
        if "weapons_rare" in inventory_types and weapon_rarity in ['rare', 'epic', 'legendary']:
            available_weapons.append(weapon)
    
    # Add shields
    if "shields" in inventory_types:
        for weapon in WEAPONS:
            weapon_type = str(getattr(weapon, 'weapon_type', ''))
            if 'SHIELD' in weapon_type:
                available_weapons.append(weapon)
    
    # Filter armor by type
    available_armor = []
    for armor in ARMORS:
        armor_rarity = getattr(armor, 'rarity', 'common').lower()
        if not should_include_rarity(armor_rarity):
            continue
            
        armor_weight = getattr(armor, 'weight', 0)
        
        if "armor_light" in inventory_types and armor_weight <= 1:
            available_armor.append(armor)
        
        if "armor_medium" in inventory_types and 2 <= armor_weight <= 3:
            available_armor.append(armor)
        
        if "armor_heavy" in inventory_types and armor_weight >= 4:
            available_armor.append(armor)
        
        if "armor_all" in inventory_types:
            available_armor.append(armor)
        
        if "armor_rare" in inventory_types and armor_rarity in ['rare', 'epic', 'legendary']:
            available_armor.append(armor)
    
    # Select random items based on player level (scale with level)
    num_weapons = random.randint(2 + player_level // 5, 5 + player_level // 3)
    num_armor = random.randint(1 + player_level // 6, 3 + player_level // 4)
    num_consumables = random.randint(2 + player_level // 8, 4 + player_level // 5) if "consumables" in inventory_types else 0
    
    # Add weapons (avoid duplicates)
    added_weapons = set()
    if available_weapons:
        for _ in range(min(num_weapons, len(available_weapons))):
            attempts = 0
            while attempts < 10:
                weapon = random.choice(available_weapons)
                weapon_name = getattr(weapon, 'name', '')
                if weapon_name not in added_weapons:
                    added_weapons.add(weapon_name)
                    
                    # Calculate value from stats if not set
                    base_value = getattr(weapon, 'value', 0)
                    if base_value == 0:
                        damage = getattr(weapon, 'base_damage', 0)
                        accuracy = getattr(weapon, 'accuracy_mod', 0)
                        crit = getattr(weapon, 'crit_mod', 0)
                        base_value = 30 + (damage * 15) + (accuracy * 2) + (crit * 3)
                        
                        # Apply rarity multiplier
                        rarity = getattr(weapon, 'rarity', 'common').lower()
                        rarity_mult = {'common': 1.0, 'uncommon': 2.0, 'rare': 4.0, 'epic': 8.0, 'legendary': 15.0}
                        base_value = int(base_value * rarity_mult.get(rarity, 1.0))
                    
                    inventory.append({
                        'item': weapon,
                        'type': 'weapon',
                        'price': int(base_value * faction_data['markup']),
                        'quantity': 1
                    })
                    break
                attempts += 1
    
    # Add armor (avoid duplicates)
    added_armor = set()
    if available_armor:
        for _ in range(min(num_armor, len(available_armor))):
            attempts = 0
            while attempts < 10:
                armor = random.choice(available_armor)
                armor_name = getattr(armor, 'name', '')
                if armor_name not in added_armor:
                    added_armor.add(armor_name)
                    
                    # Calculate value from stats
                    defense = getattr(armor, 'defense', 0)
                    evasion = getattr(armor, 'evasion_mod', 0)
                    hp_bonus = getattr(armor, 'hp_bonus', 0)
                    base_value = 30 + (defense * 12) + (max(0, evasion) * 5) + (hp_bonus * 2)
                    
                    # Apply rarity multiplier
                    rarity = getattr(armor, 'rarity', 'common').lower()
                    rarity_mult = {'common': 1.0, 'uncommon': 2.0, 'rare': 4.0, 'epic': 8.0, 'legendary': 15.0}
                    base_value = int(base_value * rarity_mult.get(rarity, 1.0))
                    
                    inventory.append({
                        'item': armor,
                        'type': 'armor',
                        'price': int(base_value * faction_data['markup']),
                        'quantity': 1
                    })
                    break
                attempts += 1
    
    # Add consumables
    if num_consumables > 0 and ITEM_DEFS:
        for _ in range(num_consumables):
            item_def = random.choice(ITEM_DEFS)
            
            # Calculate value from effect magnitude
            effect = item_def.get('effect', {})
            base_value = 15
            if 'heal' in effect:
                base_value = max(15, effect['heal'] * 3)
            elif 'stress_reduction' in effect:
                base_value = max(10, effect['stress_reduction'] * 2)
            elif 'area_damage' in effect:
                base_value = max(25, effect['area_damage'] * 2)
            
            inventory.append({
                'item': item_def,
                'type': 'consumable',
                'price': int(base_value * faction_data['markup']),
                'quantity': random.randint(1, 3)
            })
    
    return inventory


def get_merchant_dialogue(faction: str, dialogue_type: str) -> str:
    """Get a random dialogue line for a faction."""
    faction_data = FACTION_DATA.get(faction, FACTION_DATA[MerchantFaction.NEUTRAL_TRADERS])
    dialogues = faction_data.get(dialogue_type, ["..."])
    return random.choice(dialogues)


def calculate_sell_price(item, faction: str) -> int:
    """Calculate how much a merchant will pay for an item."""
    faction_data = FACTION_DATA.get(faction, FACTION_DATA[MerchantFaction.NEUTRAL_TRADERS])
    
    # Rarity multipliers
    rarity_multipliers = {
        'common': 1.0,
        'uncommon': 2.0,
        'rare': 4.0,
        'epic': 8.0,
        'legendary': 15.0
    }
    
    # Handle dict items (tokens/consumables)
    if isinstance(item, dict):
        base_value = item.get('value', 0)
        if base_value == 0:
            # Consumables: value based on effect magnitude
            effect = item.get('effect', {})
            if effect:
                magnitude = 0
                # Check for various effect types
                if 'heal' in effect:
                    magnitude = effect['heal'] * 3  # Healing worth 3 per HP
                elif 'hp_restore' in effect:
                    magnitude = effect['hp_restore'] * 3
                elif 'fp_restore' in effect:
                    magnitude = effect['fp_restore'] * 6  # Force points worth more
                elif 'stress_reduction' in effect:
                    magnitude = effect['stress_reduction'] * 2  # Stress reduction worth 2
                elif 'area_damage' in effect:
                    magnitude = effect['area_damage'] * 4  # AoE damage worth more
                elif 'damage' in effect:
                    magnitude = effect['damage'] * 4
                elif 'compass' in effect:
                    magnitude = 40  # Utility items
                elif 'ammo' in effect:
                    magnitude = effect['ammo'] * 2
                
                base_value = max(15, magnitude)
            else:
                base_value = 15  # Basic materials/tokens
        
        # Apply rarity if present
        rarity = item.get('rarity', 'common').lower()
        base_value = int(base_value * rarity_multipliers.get(rarity, 1.0))
    
    # Handle object items (weapons/armor)
    else:
        base_value = getattr(item, 'value', 0)
        
        # If no value set, calculate from stats
        if base_value == 0:
            # Weapons: value based on damage and special properties
            if hasattr(item, 'base_damage'):
                damage = getattr(item, 'base_damage', 0)
                accuracy = getattr(item, 'accuracy_mod', 0)
                crit = getattr(item, 'crit_mod', 0)
                base_value = 30 + (damage * 15) + (accuracy * 2) + (crit * 3)
                
                # Lightsabers worth more
                weapon_type = getattr(item, 'weapon_type', None)
                if weapon_type and 'lightsaber' in str(weapon_type).lower():
                    base_value = int(base_value * 1.5)
            
            # Armor: value based on defense, evasion, and HP bonus
            elif hasattr(item, 'defense'):
                defense = getattr(item, 'defense', 0)
                evasion = getattr(item, 'evasion_mod', 0)
                hp_bonus = getattr(item, 'hp_bonus', 0)
                base_value = 30 + (defense * 12) + (max(0, evasion) * 5) + (hp_bonus * 2)
            
            else:
                base_value = 20  # Minimal fallback
        
        # Apply rarity multiplier
        rarity = getattr(item, 'rarity', 'common').lower()
        base_value = int(base_value * rarity_multipliers.get(rarity, 1.0))
    
    # Apply faction buyback rate
    return max(1, int(base_value * faction_data['buyback']))
