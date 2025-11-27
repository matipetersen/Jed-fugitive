# Critical Feature Implementation Plan

## 🔴 CRITICAL FIXES (Immediate)

### 1. GUI Stat Block Not Appearing
**Issue**: `get_stats_display()` exists but stat panel may not be rendering properly
**Fix**: 
- Check if stat panel is being created correctly in UI initialization
- Verify draw_stats_panel is being called each frame
- Fix corruption property reference (should use `self.corruption` not `self.dark_corruption`)

### 2. Inspect Not Showing Full Information
**Issue**: Inspect only checks facing tile, not all adjacent tiles
**Fix**:
- Modify inspect to scan all 8 adjacent tiles + player tile (9 total)
- Show combined information for all items/enemies/NPCs nearby
- Add lore for each inspected item using inspection.py

### 3. Inspect Not Available in Inventory
**Issue**: Cannot inspect items in inventory before using
**Fix**:
- Add 'x' key handler in inventory menu to inspect selected item
- Show full lore, stats, and corruption effects before equipping/using

### 4. Missing Item Lore
**Issue**: Most items lack detailed lore descriptions
**Fix**:
- Expand inspection.py ITEM_LORE dictionary
- Add lore for all weapons, armor, consumables, artifacts
- Include alignment-specific perspectives

---

## 🟡 CRITICAL PRIORITY FEATURES

### 5. NPC System Integration ⚠️ CRITICAL
**Status**: Complete code exists but NPCs never spawn!
**Fix**:
- Verify `spawn_npcs_on_map()` is called during map generation
- Check if npcs_on_map dict is being populated
- Ensure NPC symbols render on map
- Test NPC interaction with 't' key

### 6. Ritual System Integration
**Status**: 19 ceremonies coded but not bound to gameplay
**Fix**:
- Wire ritual menu ('r' key) to actual ritual functions
- Implement ritual effects (buff player stats, summon allies, etc.)
- Add Force energy costs and cooldowns

### 7. Compass/Scan System
**Status**: Referenced in help but not implemented
**Fix**:
- Add 'c' key handler for compass
- Show nearby enemies, POIs, tomb locations within radius
- Display directional arrows and distances

---

## 🟢 HIGH-VALUE ADDITIONS

### 8. Character Sheet (@)
**Implementation**:
```python
def show_character_sheet(game):
    lines = []
    p = game.player
    
    # Header
    lines.append("╔═══════════════════════════════════════════╗")
    lines.append("║       JEDI FUGITIVE - CHARACTER SHEET      ║")
    lines.append("╚═══════════════════════════════════════════╝")
    
    # Identity & Alignment
    alignment = p.get_alignment()
    lines.append(f"Alignment: {alignment.upper()}")
    lines.append(f"Corruption: {p.dark_corruption}%")
    lines.append(f"Level: {p.level} (Light: {p.light_level}, Dark: {p.dark_level})")
    
    # Stats with bonuses breakdown
    lines.append("")
    lines.append("═══ COMBAT STATS ═══")
    lines.append(f"HP: {p.hp}/{p.max_hp}")
    lines.append(f"Attack: {p.attack} (Base + Equipment + Mastery)")
    lines.append(f"Defense: {p.defense}")
    lines.append(f"Accuracy: {p.accuracy}%")
    lines.append(f"Evasion: {p.evasion}%")
    
    # Force abilities
    lines.append("")
    lines.append("═══ FORCE ABILITIES ═══")
    for ability in p.get_available_abilities():
        lines.append(f"• {ability.name} (Cost: {ability.base_cost})")
    
    # Masteries
    lines.append("")
    lines.append("═══ COMBAT MASTERIES ═══")
    lines.append(f"Melee Mastery: Rank {p.melee_mastery}")
    lines.append(f"Ranged Mastery: Rank {p.ranged_mastery}")
    lines.append(f"Shield Mastery: Rank {p.shield_mastery}")
    lines.append(f"Dual Wield: Rank {p.dual_wield_mastery}")
    
    # Journey stats
    lines.append("")
    lines.append("═══ JOURNEY ═══")
    lines.append(f"Enemies Defeated: {p.kills_count}")
    lines.append(f"Tombs Explored: {p.tombs_explored}")
    lines.append(f"Lore Discovered: {p.lore_discovered}")
    lines.append(f"Gold Collected: {p.gold_collected}")
    
    return lines
```

### 9. Crafting Skill Progression
**Implementation**:
- Track crafting_xp gained from successful crafts
- Level up crafting skill (1-10)
- Unlock better recipes at higher levels
- Reduce material costs at higher levels

### 10. Environmental Hazards
**Implementation**:
```python
HAZARDS = {
    'lava_pool': {
        'symbol': '~',
        'color': 'red',
        'damage': 15,
        'effect': 'burning',
        'message': 'You step into molten lava! Your armor sizzles!'
    },
    'acid_rain': {
        'atmospheric': True,
        'damage_per_turn': 2,
        'duration': 50,
        'message': 'Acidic rain burns exposed skin!'
    },
    'radiation_zone': {
        'symbol': '☢',
        'color': 'green',
        'damage': 5,
        'effect': 'radiation_sickness',
        'max_hp_reduction': 1,
        'message': 'You feel sick from radiation exposure!'
    }
}
```

### 11. Combo System
**Implementation**:
```python
COMBOS = {
    'force_blade': {
        'sequence': ['force_push', 'melee_attack'],
        'bonus_damage': 20,
        'message': 'Force-enhanced blade strike!'
    },
    'lightning_chain': {
        'sequence': ['force_lightning', 'force_lightning'],
        'aoe': True,
        'bonus_damage': 10,
        'message': 'Chain lightning arcs between enemies!'
    },
    'tactical_retreat': {
        'sequence': ['force_push', 'force_pull'],
        'effect': 'stun_all_nearby',
        'message': 'You unleash a Force shockwave!'
    }
}
```

---

## 🎯 TRADING SYSTEM CHECK

### 12. Verify Merchant System
**Tests Needed**:
1. Check if merchants spawn on map
2. Verify 'T' key opens trade menu near merchants
3. Test buy/sell functionality
4. Confirm gold economy works

---

## 📊 IMPLEMENTATION ORDER

1. **Stat Block Fix** (5 min) - Critical visual bug
2. **Inspect Enhancement** (15 min) - Show all adjacent tiles
3. **Inventory Inspect** (10 min) - Add 'x' in inventory
4. **Item Lore Expansion** (30 min) - Add lore for all items
5. **NPC Spawn Fix** (20 min) - Enable NPC system
6. **Character Sheet** (15 min) - Add '@' sheet display
7. **Compass** (20 min) - Add 'c' scan feature
8. **Crafting Progression** (25 min) - XP and levels
9. **Combo System** (30 min) - Track sequences, apply bonuses
10. **Environmental Hazards** (40 min) - Hazard tiles and effects
11. **Ritual Integration** (30 min) - Wire rituals to effects
12. **Trading Test** (10 min) - Verify merchants work

**Total Time: ~4 hours**

---

## TESTING CHECKLIST

- [ ] Stat block shows all stats correctly
- [ ] Inspect shows info from all 9 tiles around player
- [ ] Can press 'x' in inventory to inspect items
- [ ] All items have lore text when inspected
- [ ] NPCs appear on map and can be talked to
- [ ] '@' key shows detailed character sheet
- [ ] 'c' key shows compass with nearby POIs
- [ ] Crafting grants XP and levels up
- [ ] Combos trigger and show bonus damage
- [ ] Environmental hazards deal damage
- [ ] Rituals have actual effects when performed
- [ ] Merchants can be traded with using 'T'
