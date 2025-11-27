# Implementation Roadmap: System Integration Plan
*For Jedi Fugitive Missing Integrations*

## Implementation Order & Detailed Steps

### **PHASE 1: NPC System Integration** ⭐ PRIORITY 1
*Target: Week 1 | Risk Level: High | Impact: Critical*

#### Step 1.1: Game Manager Integration
**File**: `src/jedi_fugitive/game/game_manager.py`

```python
# Add to __init__ method (around line 85)
self.npcs_on_map = {}  # Dict mapping positions to NPC objects
self.npc_encounters = NPCEncounters()

# Add import at top
from jedi_fugitive.game.npc_encounters import NPCEncounters

# Add to update_game method
def handle_npc_interactions(self):
    """Check for NPC interactions at player position"""
    player_pos = (self.player.x, self.player.y)
    if player_pos in self.npcs_on_map:
        return self.npcs_on_map[player_pos]
    return None
```

#### Step 1.2: Map Generation Integration  
**File**: `src/jedi_fugitive/map/map_features.py`

```python
# Add NPC spawning to generate_biome_features method
def spawn_npcs_in_biome(self, biome_type, level_map):
    """Spawn NPCs appropriate for biome type"""
    from jedi_fugitive.game.npc_encounters import select_npc_for_biome
    
    # 5-15% chance per level to spawn NPC
    if random.random() < 0.1:  
        npc_type = select_npc_for_biome(biome_type)
        # Find valid spawn position
        for _ in range(50):  # 50 attempts
            x, y = random.randint(1, len(level_map[0])-2), random.randint(1, len(level_map)-2)
            if level_map[y][x] == '.':  # Floor tile
                return (x, y), npc_type
    return None, None
```

#### Step 1.3: Input Handler Integration
**File**: `src/jedi_fugitive/game/input_handler.py`

```python
# Add to handle_game_input method (around line 1800)
elif key == ord('t'):  # Talk to NPC
    npc = self.game_manager.handle_npc_interactions()
    if npc:
        self.show_npc_interaction_popup(npc)
    else:
        self.show_message("No one to talk to here.")

def show_npc_interaction_popup(self, npc):
    """Show NPC interaction menu"""
    options = npc.get_available_interactions(self.game_manager.player)
    choice = self.show_popup_menu(
        f"Interact with {npc.name}",
        options,
        f"{npc.description}\n\n{npc.get_greeting()}"
    )
    
    if choice is not None:
        result = npc.handle_interaction(choice, self.game_manager.player)
        if result:
            self.show_message(result)
```

#### Step 1.4: UI Renderer Integration  
**File**: `src/jedi_fugitive/ui/ui_renderer.py`

```python
# Add NPC symbols to render_map method
def render_npcs(self, stdscr, map_data, start_x, start_y):
    """Render NPC symbols on map"""
    for (x, y), npc in self.game_manager.npcs_on_map.items():
        screen_x = x - start_x + 1
        screen_y = y - start_y + 1
        
        if 0 <= screen_x < self.map_width and 0 <= screen_y < self.map_height:
            npc_symbol = npc.get_map_symbol()  # '@' for most NPCs
            try:
                stdscr.addch(screen_y, screen_x, npc_symbol, curses.color_pair(7))  # Yellow
            except curses.error:
                pass
```

---

### **PHASE 2: Crafting Skill System** ⭐ PRIORITY 1  
*Target: Week 1-2 | Risk Level: Low | Impact: Medium*

#### Step 2.1: Player Class Enhancement
**File**: `src/jedi_fugitive/game/player.py`

```python
# Add to __init__ method (around line 45)
self.craft_level = 1
self.craft_xp = 0
self.craft_xp_to_next = 100

# Add method
def gain_craft_xp(self, amount):
    """Gain crafting experience and level up if needed"""
    self.craft_xp += amount
    while self.craft_xp >= self.craft_xp_to_next:
        self.craft_xp -= self.craft_xp_to_next
        self.craft_level += 1
        self.craft_xp_to_next = int(self.craft_xp_to_next * 1.5)
        return f"Crafting level increased to {self.craft_level}!"
    return None

def can_craft_recipe(self, recipe):
    """Check if player can craft this recipe"""
    return self.craft_level >= recipe.get('required_level', 1)
```

#### Step 2.2: Equipment System Update
**File**: `src/jedi_fugitive/game/equipment.py`

```python
# Update craft_item method to include skill checks
def craft_item(self, player, recipe_name):
    """Craft item with skill level requirements"""
    recipe = self.recipes.get(recipe_name)
    if not recipe:
        return False, "Recipe not found."
    
    # Check skill requirement  
    if not player.can_craft_recipe(recipe):
        required = recipe.get('required_level', 1)
        return False, f"Requires crafting level {required} (you have {player.craft_level})"
    
    # Existing crafting logic...
    success = self.attempt_craft(player, recipe)
    
    if success:
        # Grant XP based on recipe difficulty
        xp_gain = recipe.get('required_level', 1) * 25
        level_up_msg = player.gain_craft_xp(xp_gain)
        
        message = f"Successfully crafted {recipe['result']}!"
        if level_up_msg:
            message += f" {level_up_msg}"
        
        return True, message
    
    return False, "Crafting failed."
```

#### Step 2.3: Recipe Updates
**Add skill requirements to existing recipes:**

```python
# Update recipes dictionary with required_level
self.recipes = {
    "sharpened_stick": {
        "materials": [("stick", 1), ("sharp_stone", 1)],
        "result": "sharpened_stick",
        "required_level": 1
    },
    "leather_armor": {
        "materials": [("leather_scraps", 3), ("fiber", 2)],
        "result": "leather_armor", 
        "required_level": 2
    },
    "energy_blade": {
        "materials": [("crystal_fragment", 2), ("metal_scraps", 3)],
        "result": "energy_blade",
        "required_level": 4
    }
    # Add required_level to all recipes...
}
```

---

### **PHASE 3: Complete Rituals Integration** ⭐ PRIORITY 2
*Target: Week 2-3 | Risk Level: Medium | Impact: Medium*

#### Step 3.1: Enhanced Meditation Menu
**File**: `src/jedi_fugitive/game/input_handler.py`

```python
# Update show_meditation_menu method (around line 2200)
def show_meditation_menu(self):
    """Enhanced meditation menu with rituals"""
    menu_options = [
        "1. Meditate (Restore Force Energy)",
        "2. Perform Ritual",
        "3. Review Past Ceremonies", 
        "4. Cancel"
    ]
    
    choice = self.show_popup_menu(
        "Meditation & Rituals",
        menu_options,
        "Focus your mind and connect with the Force..."
    )
    
    if choice == 0:  # Regular meditation
        self.handle_meditation()
    elif choice == 1:  # Perform ritual
        self.show_ritual_menu()
    elif choice == 2:  # Review ceremonies
        self.show_ceremony_history()

def show_ritual_menu(self):
    """Show available rituals based on location and player state"""
    from jedi_fugitive.game.rituals import RitualManager
    
    available_rituals = RitualManager.get_available_rituals(
        self.game_manager.player,
        self.game_manager.current_level,
        self.game_manager.last_enemy_defeated
    )
    
    if not available_rituals:
        self.show_message("No rituals are available at this location or time.")
        return
    
    ritual_options = [f"{i+1}. {ritual.name}" for i, ritual in enumerate(available_rituals)]
    ritual_options.append(f"{len(ritual_options)+1}. Cancel")
    
    choice = self.show_popup_menu(
        "Available Rituals",
        ritual_options,
        "Choose a ritual to perform..."
    )
    
    if choice is not None and choice < len(available_rituals):
        self.perform_ritual(available_rituals[choice])
```

#### Step 3.2: Burial Ceremony Triggers
**File**: `src/jedi_fugitive/game/combat.py`

```python
# Add to handle_enemy_death method
def handle_enemy_death(self, enemy):
    """Handle enemy death with burial ceremony option"""
    # Existing death handling...
    
    # Offer burial ceremony if appropriate
    if self.should_offer_burial_ceremony(enemy):
        self.game_manager.input_handler.offer_burial_ceremony(enemy)

def should_offer_burial_ceremony(self, enemy):
    """Check if burial ceremony should be offered"""
    # Only for sentient enemies, not beasts
    sentient_types = ["sith_acolyte", "imperial_guard", "jedi_knight"]
    return enemy.enemy_type in sentient_types
```

---

### **PHASE 4: System Consistency & Polish** ⭐ PRIORITY 3
*Target: Week 3-4 | Risk Level: Low | Impact: Low-Medium*

#### Step 4.1: Force Energy Standardization
**Files**: Multiple ability files

```python
# Standardize all abilities to use self.force_energy instead of self.force_points
# Update force_abilities.py, game/force_abilities.py, abilities/force_abilities.py

# Example fix in force_abilities.py:
def use_ability(self, player, ability_name):
    """Use force ability with consistent energy system"""
    ability = self.abilities.get(ability_name)
    if not ability:
        return False, "Unknown ability"
    
    # Use force_energy consistently  
    if player.force_energy < ability['cost']:
        return False, f"Need {ability['cost']} Force energy"
    
    player.force_energy -= ability['cost']
    # Apply ability effects...
```

#### Step 4.2: Save System Enhancement  
**File**: `src/jedi_fugitive/game/game_manager.py`

```python
# Update save_game method to include new attributes
def save_game(self, filename):
    """Save game with all new system data"""
    save_data = {
        'player': {
            # Existing player data...
            'craft_level': self.player.craft_level,
            'craft_xp': self.player.craft_xp,
            'craft_xp_to_next': self.player.craft_xp_to_next,
            'ceremonies_performed': getattr(self.player, 'ceremonies_performed', []),
            'npcs_met': getattr(self.player, 'npcs_met', [])
        },
        'game_state': {
            # Existing game state...
            'npcs_on_map': [(pos, npc.to_dict()) for pos, npc in self.npcs_on_map.items()],
            'ritual_history': getattr(self, 'ritual_history', [])
        }
    }
    # Existing save logic...
```

#### Step 4.3: UI Statistics Enhancement
**File**: `src/jedi_fugitive/ui/ui_renderer.py`

```python
# Update render_stats method to show new information
def render_stats(self, stdscr):
    """Render enhanced player statistics"""
    # Existing stats...
    
    # Add crafting level
    stdscr.addstr(y_pos, 2, f"Crafting Level: {self.player.craft_level}")
    y_pos += 1
    
    # Show force energy consistently
    stdscr.addstr(y_pos, 2, f"Force Energy: {self.player.force_energy}")
    y_pos += 1
    
    # Add ceremony count if performed any
    ceremony_count = len(getattr(self.player, 'ceremonies_performed', []))
    if ceremony_count > 0:
        stdscr.addstr(y_pos, 2, f"Ceremonies: {ceremony_count}")
        y_pos += 1
```

## Testing Protocol

### **Integration Testing Checklist**

#### Phase 1 Testing: NPC System  
- [ ] NPCs spawn on new levels
- [ ] 't' key detects NPCs at player position  
- [ ] NPC dialogue menus appear correctly
- [ ] NPC interactions affect player stats
- [ ] NPC symbols render on map
- [ ] Save/load preserves NPC positions

#### Phase 2 Testing: Crafting Skills
- [ ] craft_level prevents high-level recipes
- [ ] Successful crafting grants XP  
- [ ] Level up messages appear
- [ ] Stats screen shows crafting level
- [ ] Save/load preserves crafting progress

#### Phase 3 Testing: Rituals
- [ ] Meditation menu shows ritual options
- [ ] Location-appropriate rituals available
- [ ] Burial ceremonies trigger after combat
- [ ] Ritual effects apply correctly
- [ ] Ceremony history tracks properly

#### Phase 4 Testing: System Polish
- [ ] Force energy used consistently across all abilities
- [ ] All new attributes save/load correctly  
- [ ] UI shows all relevant statistics
- [ ] No regression in existing functionality

## Risk Mitigation

### **Backup Strategy**
```bash
# Before each phase, create backup branch
git checkout -b backup-before-phase-N
git add .
git commit -m "Backup before Phase N integration"
git checkout main
```

### **Rollback Plan**
- Each phase implemented as separate commits
- Test after each step, not just end of phase  
- Keep original files backed up during major changes
- Use feature flags for gradual integration testing

## Success Metrics

### **Phase 1 Success**: NPC Integration  
- ✅ 4 NPC types spawning and interactable
- ✅ Training interactions functional
- ✅ Moral choice dialogues working  
- ✅ NPC map symbols displaying

### **Phase 2 Success**: Crafting Skills
- ✅ Recipe skill requirements enforced
- ✅ Crafting progression working
- ✅ XP and leveling functional
- ✅ UI displays crafting level

### **Phase 3 Success**: Rituals Complete
- ✅ Enhanced meditation menu
- ✅ Burial ceremonies available  
- ✅ Location-based rituals working
- ✅ Ceremony history tracking

### **Phase 4 Success**: System Polish  
- ✅ Force energy standardized
- ✅ Enhanced save/load system
- ✅ Improved UI statistics
- ✅ No functionality regression

**Estimated Total Development Time**: 3-4 weeks
**Estimated Testing Time**: 1 week  
**Total Project Timeline**: 4-5 weeks for complete integration