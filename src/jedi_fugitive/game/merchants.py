"""
Merchant system for Jedi Fugitive.
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
    from jedi_fugitive.items.consumables import CONSUMABLES
    
    faction_data = FACTION_DATA.get(faction, FACTION_DATA[MerchantFaction.NEUTRAL_TRADERS])
    inventory_types = faction_data["inventory_types"]
    inventory = []
    
    # Filter weapons by type
    available_weapons = []
    for weapon in WEAPONS:
        weapon_rarity = getattr(weapon, 'rarity', 'common').lower()
        
        # Faction filtering
        if "weapons_melee" in inventory_types:
            weapon_type = str(getattr(weapon, 'weapon_type', ''))
            if any(melee in weapon_type for melee in ['VIBROBLADE', 'MELEE', 'LIGHTSABER', 'KNIFE', 'STAFF']):
                available_weapons.append(weapon)
        
        if "weapons_ranged" in inventory_types:
            weapon_type = str(getattr(weapon, 'weapon_type', ''))
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
    
    # Select random items based on player level
    num_weapons = random.randint(3, 6)
    num_armor = random.randint(2, 4)
    num_consumables = random.randint(3, 5) if "consumables" in inventory_types else 0
    
    # Add weapons
    if available_weapons:
        for _ in range(min(num_weapons, len(available_weapons))):
            weapon = random.choice(available_weapons)
            base_value = getattr(weapon, 'value', 100)
            if base_value == 0:  # Items with 0 value
                base_value = 50 + player_level * 10
            inventory.append({
                'item': weapon,
                'type': 'weapon',
                'price': int(base_value * faction_data['markup']),
                'quantity': 1
            })
    
    # Add armor
    if available_armor:
        for _ in range(min(num_armor, len(available_armor))):
            armor = random.choice(available_armor)
            base_value = 50 + getattr(armor, 'defense', 0) * 10 + getattr(armor, 'hp_bonus', 0) * 2
            inventory.append({
                'item': armor,
                'type': 'armor',
                'price': int(base_value * faction_data['markup']),
                'quantity': 1
            })
    
    # Add consumables
    if num_consumables > 0:
        try:
            for _ in range(num_consumables):
                consumable = random.choice(CONSUMABLES)
                base_value = getattr(consumable, 'value', 20)
                inventory.append({
                    'item': consumable,
                    'type': 'consumable',
                    'price': int(base_value * faction_data['markup']),
                    'quantity': random.randint(1, 3)
                })
        except:
            pass  # CONSUMABLES might not exist yet
    
    return inventory


def get_merchant_dialogue(faction: str, dialogue_type: str) -> str:
    """Get a random dialogue line for a faction."""
    faction_data = FACTION_DATA.get(faction, FACTION_DATA[MerchantFaction.NEUTRAL_TRADERS])
    dialogues = faction_data.get(dialogue_type, ["..."])
    return random.choice(dialogues)


def calculate_sell_price(item, faction: str) -> int:
    """Calculate how much a merchant will pay for an item."""
    faction_data = FACTION_DATA.get(faction, FACTION_DATA[MerchantFaction.NEUTRAL_TRADERS])
    
    # Determine base value
    base_value = getattr(item, 'value', 0)
    if base_value == 0:
        # Estimate value based on stats
        if hasattr(item, 'base_damage'):
            base_value = 50 + getattr(item, 'base_damage', 0) * 10
        elif hasattr(item, 'defense'):
            base_value = 50 + getattr(item, 'defense', 0) * 10
        else:
            base_value = 25
    
    return int(base_value * faction_data['buyback'])
