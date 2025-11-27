# Trading System Improvements

## Issues Fixed

### 1. **All Selling Prices Were Identical**
**Problem**: Every item was selling for nearly the same price (12-17 gold) regardless of type, quality, or rarity.

**Root Cause**: The `calculate_sell_price()` function in `merchants.py` had a simple fallback that defaulted all items without explicit values to 25 gold base value.

**Solution**: Completely rewrote the pricing calculation to:

#### For Weapons:
- Base value calculated from: `30 + (damage * 15) + (accuracy * 2) + (crit * 3)`
- Lightsabers get 1.5x multiplier
- Rarity multipliers applied:
  - Common: 1x
  - Uncommon: 2x
  - Rare: 4x
  - Epic: 8x
  - Legendary: 15x

#### For Armor:
- Base value calculated from: `30 + (defense * 12) + (max(0, evasion) * 5) + (hp_bonus * 2)`
- Rarity multipliers applied same as weapons

#### For Consumables (Dict Items):
- Healing items: `heal_amount * 3` gold
- Stress reduction: `stress_reduction * 2` gold
- Area damage items: `damage * 4` gold (worth more)
- Utility items (compass): 40g base
- Ammo: `ammo_count * 2` gold

### 2. **Faction Differences Now Meaningful**
Different factions now have notably different buyback rates:
- **Scavenger Looters**: 50% (cheapest - they're greedy)
- **Mandalorian Scouts**: 60% (fair traders)
- **Neutral Traders**: 60% (standard rate)
- **Jedi Refugee**: 65% (generous)
- **Republic Survivors**: 70% (best rate for most)
- **Black Market**: 70% (pays well for rare goods)

### 3. **Improved Merchant Inventory Variety**

#### Level-Based Rarity Scaling:
Merchants now stock better items as player level increases:
- Low level (1-5): Mostly common items
- Mid level (6-15): Mix of common/uncommon with rare items appearing
- High level (16+): Rare and epic items common, legendary items possible

#### Faction-Specific Inventories:
- **Mandalorian Scouts**: Melee weapons, medium/heavy armor, shields
- **Republic Survivors**: Ranged weapons, light/medium armor, consumables
- **Scavenger Looters**: Everything at cheap prices, but random quality
- **Neutral Traders**: Balanced selection of all item types
- **Black Market**: Rare/epic items, expensive but powerful
- **Jedi Refugee**: Melee weapons, light armor, Force-related consumables

#### Anti-Duplicate System:
- Merchants no longer stock duplicate items
- Each visit shows unique inventory
- Inventory size scales with player level

## Test Results

Running `scripts/test_trading_prices.py` shows:

### Weapon Pricing Examples:
- Common Combat Knife (2 dmg): 4-6g
- Uncommon Vibroblade (5 dmg): 142-198g
- Legendary weapons: 2000+ gold

### Armor Pricing Examples:
- Common Cloth Robes (1 def): 40-46g
- Uncommon Jedi Robes (2 def, 10 HP): 124-145g
- Rare Light Combat Suit (3 def, 15 HP): 249-324g

### Consumable Pricing Examples:
- Water Canteen (5 HP heal): 9g
- Small Medkit (10 HP heal): 18g
- Calming Tea (25 stress reduction): 30g
- Jedi Meditation Focus (40 stress): 48g
- Thermal Grenade (24 area damage): 57g

### Faction Comparison (Training Saber example):
- Scavenger Boss: 4g (50% buyback)
- Mandalorian Scout: 5g (60% buyback)
- Republic Officer: 6g (70% buyback)

## Files Modified

1. **src/jedi_fugitive/game/merchants.py**:
   - Line 376-446: Rewrote `calculate_sell_price()` function
   - Line 198-365: Enhanced `get_faction_inventory()` with:
     - Level-based rarity weighting
     - Anti-duplicate system
     - Better value calculation
     - Scaling inventory size

2. **scripts/test_trading_prices.py** (NEW):
   - Comprehensive test suite for pricing system
   - Tests weapons, armor, consumables
   - Verifies faction differences
   - Checks rarity scaling

## Gameplay Impact

### Before:
- All items sell for ~12-17 gold regardless of quality
- No incentive to find rare items for selling
- No reason to choose specific merchants
- Trading felt flat and unrewarding

### After:
- Common items: 5-20 gold
- Uncommon items: 20-200 gold
- Rare items: 100-500 gold
- Epic items: 500-2000 gold
- Legendary items: 2000+ gold
- Clear progression and value distinction
- Strategic merchant choice matters
- Finding rare loot is rewarding

## How to Test

Run the test script:
```bash
cd jedi-fugitive
python scripts/test_trading_prices.py
```

In-game testing:
1. Collect various items (weapons, armor, consumables)
2. Visit different merchant factions
3. Compare sell prices - should vary significantly based on:
   - Item type (weapon/armor/consumable)
   - Item stats (damage, defense, effects)
   - Item rarity (common through legendary)
   - Merchant faction (50% to 70% buyback rates)

## Future Enhancements (Optional)

Consider adding:
- Player reputation system affecting prices
- Bulk sale discounts/bonuses
- Merchant inventory refresh mechanics
- Special merchant quests for better prices
- Item condition affecting value (damaged items worth less)
- Bartering skill system
