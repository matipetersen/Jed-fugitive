import curses
from jedi_fugitive.game.level import Display


def _unlock_dark_ability(game):
    """Unlock a Dark Side Force ability when leveling up on dark path."""
    try:
        dark_level = getattr(game.player, 'dark_level', 1)
        
        # Define dark abilities by level
        dark_abilities = {
            2: ("Force Choke", "Crush an enemy's throat from afar"),
            3: ("Force Lightning", "Unleash devastating lightning"),
            4: ("Drain Life", "Steal HP from enemies"),
            5: ("Dark Rage", "Boost attack but lose control"),
            6: ("Dominate Mind", "Control weak-willed enemies"),
        }
        
        if dark_level in dark_abilities:
            ability_name, desc = dark_abilities[dark_level]
            game.ui.messages.add(f"Dark Side Power Unlocked: {ability_name} - {desc}")
            if hasattr(game.player, 'add_log_entry'):
                # Dark ability unlock - narrative reflects embrace of power
                entry = game.player.narrative_text(
                    light_version=f"Reluctantly learned {ability_name}, fearing its corrupting influence.",
                    dark_version=f"Mastered {ability_name}, feeling the intoxicating power of the dark side!",
                    balanced_version=f"Gained dark power: {ability_name}"
                )
                game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
    except Exception:
        pass


def _unlock_light_ability(game):
    """Unlock a Light Side Force ability when leveling up on light path."""
    try:
        light_level = getattr(game.player, 'light_level', 1)
        
        # Define light abilities by level
        light_abilities = {
            2: ("Force Heal", "Restore HP with the Force"),
            3: ("Force Shield", "Create a protective barrier"),
            4: ("Battle Meditation", "Boost all stats temporarily"),
            5: ("Force Enlightenment", "Reveal hidden paths and items"),
            6: ("Redemption", "Purify corruption and heal stress"),
        }
        
        if light_level in light_abilities:
            ability_name, desc = light_abilities[light_level]
            game.ui.messages.add(f"Light Side Power Unlocked: {ability_name} - {desc}")
            if hasattr(game.player, 'add_log_entry'):
                # Light ability unlock - narrative reflects wisdom and restraint
                entry = game.player.narrative_text(
                    light_version=f"Achieved harmony with the Force, gaining insight into {ability_name}.",
                    dark_version=f"Learned {ability_name}, though it feels weak compared to dark powers.",
                    balanced_version=f"Gained light power: {ability_name}"
                )
                game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
    except Exception:
        pass


def inventory_chooser(game):
    """Simple chooser: list inventory to messages and wait for a number key (1..9)."""
    try:
        inv = getattr(game.player, "inventory", []) or []
        if not inv:
            try: game.ui.messages.add("Inventory empty.") 
            except Exception: pass
            return None
        # Clear messages and show selection prompt
        try:
            game.ui.messages.add("=== SELECT ITEM (press 1-9, ESC to cancel) ===")
        except Exception:
            pass
        # show up to 9 options
        for i, it in enumerate(inv[:9]):
            name = it if isinstance(it, str) else (it.get("name") if isinstance(it, dict) else getattr(it, "name", str(it)))
            try:
                # Show item type/description if available
                desc = ""
                if isinstance(it, dict):
                    item_type = it.get("type", "")
                    if item_type:
                        desc = f" [{item_type}]"
                    elif it.get("artifact_id"):
                        desc = " [artifact]"
                elif hasattr(it, 'hands'):
                    desc = f" [{it.get_hand_requirement()}]"
                game.ui.messages.add(f"  {i+1}) {name}{desc}")
            except Exception:
                pass
        try:
            game.ui.messages.add("===========================================")
        except Exception:
            pass
        # force a draw so messages appear
        try:
            from jedi_fugitive.game.ui_renderer import draw
            draw(game)
        except Exception:
            pass
        # wait for a single keypress
        key = game.stdscr.getch()
        # Handle ESC to cancel
        if key == 27:
            try:
                game.ui.messages.add("Selection cancelled.")
            except Exception:
                pass
            return None
        if key >= ord('1') and key <= ord('9'):
            idx = key - ord('1')
            if idx < len(inv):
                return inv[idx]
        try:
            game.ui.messages.add("Invalid selection. Press 1-9 to choose.")
        except Exception:
            pass
    except Exception:
        try: game.ui.messages.add("Inventory chooser failed.")
        except Exception: pass
    return None

def _apply_equipment_effects(game, item, slot, apply_only=False):
    """Apply stat modifiers for an item (str token, dict or object). If not apply_only, set equipped slot."""
    try:
        # canonical token-based fallbacks
        token_stats = {"v": {"attack": 3}, "b": {"attack": 2}, "s": {"defense": 2, "max_hp": 5}}
        stats = {}
        # If item is a simple token string, map to token_stats
        if isinstance(item, str):
            stats = token_stats.get(item, {})
        elif isinstance(item, dict):
            # if dict carries a token key, prefer token_stats fallback when explicit numeric stats absent
            tok = item.get('token') if isinstance(item, dict) else None
            if tok and tok in token_stats:
                stats.update(token_stats.get(tok, {}))
            # then collect explicit numeric modifiers from the dict
            for k in ("attack", "defense", "evasion", "hp_bonus", "max_hp"):
                if k in item:
                    if k == "hp_bonus":
                        stats.setdefault("max_hp", 0)
                        stats["max_hp"] += int(item.get(k, 0))
                    else:
                        try:
                            stats[k] = int(item.get(k))
                        except Exception:
                            pass
        else:
            # Handle weapon objects with base_damage attribute
            if hasattr(item, "base_damage"):
                stats["attack"] = int(getattr(item, "base_damage"))
            elif hasattr(item, "attack"):
                stats["attack"] = int(getattr(item, "attack"))
            if hasattr(item, "defense"):
                stats["defense"] = int(getattr(item, "defense"))
            # Check for both evasion (weapons) and evasion_mod (armor)
            if hasattr(item, "evasion_mod"):
                stats["evasion"] = int(getattr(item, "evasion_mod"))
            elif hasattr(item, "evasion"):
                stats["evasion"] = int(getattr(item, "evasion"))
            if hasattr(item, "hp_bonus"):
                stats.setdefault("max_hp", 0)
                stats["max_hp"] += int(getattr(item, "hp_bonus"))
        # apply additively
        if stats:
            if "attack" in stats:
                game.player.attack = getattr(game.player, "attack", 1) + int(stats["attack"])
            if "defense" in stats:
                game.player.defense = getattr(game.player, "defense", 0) + int(stats["defense"])
            if "evasion" in stats:
                game.player.evasion = getattr(game.player, "evasion", 0) + int(stats["evasion"])
            if "max_hp" in stats:
                old = getattr(game.player, "max_hp", getattr(game.player, "hp", 10))
                game.player.max_hp = old + int(stats["max_hp"])
                game.player.hp = min(game.player.max_hp, getattr(game.player, "hp", game.player.max_hp) + int(stats.get("max_hp", 0)))
        if not apply_only:
            if slot == "weapon":
                game.player.equipped_weapon = item
            elif slot == "armor":
                game.player.equipped_armor = item
    except Exception:
        pass

def _remove_equipment_effects(game, slot):
    """Restore base stats and clear the named slot ('weapon'|'armor'). Reapply remaining equipment."""
    try:
        base = getattr(game.player, "_base_stats", None)
        if base:
            game.player.attack = base.get("attack", getattr(game.player, "attack", 1))
            game.player.defense = base.get("defense", getattr(game.player, "defense", 0))
            game.player.evasion = base.get("evasion", getattr(game.player, "evasion", 0))
            game.player.max_hp = base.get("max_hp", getattr(game.player, "max_hp", getattr(game.player, "hp", 10)))
            # restore hp without referencing undefined self
            try:
                game.player.hp = min(getattr(game.player, "hp", game.player.max_hp), game.player.max_hp)
            except Exception:
                game.player.hp = getattr(game.player, "hp", game.player.max_hp)
        if slot == "weapon":
            game.player.equipped_weapon = None
        elif slot == "armor":
            game.player.equipped_armor = None
        # reapply remaining equipment if any
        try:
            if getattr(game.player, "equipped_armor", None) is not None:
                _apply_equipment_effects(game, game.player.equipped_armor, "armor", apply_only=True)
            if getattr(game.player, "equipped_weapon", None) is not None:
                _apply_equipment_effects(game, game.player.equipped_weapon, "weapon", apply_only=True)
        except Exception:
            pass
    except Exception:
        pass

def pick_up(game):
    """Pick up item at player's tile and add to inventory."""
    try:
        px = getattr(game.player, "x", 0)
        py = getattr(game.player, "y", 0)
        if not (0 <= py < len(game.game_map) and 0 <= px < len(game.game_map[0])):
            try: game.ui.messages.add("Nothing to pick up here.") 
            except Exception: pass
            return
        cell = game.game_map[py][px]
        floor = getattr(Display, "FLOOR", ".")
        
        # FIRST: Check if this is a landmark/POI (they use various glyphs including '$')
        # Landmarks should NOT be picked up, they're interacted with separately
        if hasattr(game, 'map_landmarks') and (px, py) in game.map_landmarks:
            try: game.ui.messages.add("This is a point of interest. Explore it instead of picking it up.")
            except Exception: pass
            return
        
        # SECOND: Special handling for gold - goes to counter, not inventory
        # Must check BEFORE token_map to avoid gold being treated as regular item
        if cell in ['$', 'G', getattr(Display, 'GOLD', '$')]:
            import random
            gold_amount = random.randint(5, 20)
            game.player.gold_collected = getattr(game.player, 'gold_collected', 0) + gold_amount
            game.game_map[py][px] = floor
            try: 
                game.ui.messages.add(f"Found {gold_amount} gold! (Total: {game.player.gold_collected})")
            except Exception: 
                pass
            
            # Gold pickup no longer added to travel log (too spammy)
            
            try:
                game.turn_count = getattr(game, 'turn_count', 0) + 1
            except Exception:
                pass
            return
        
        # Use a canonical token registry so tokens have the same metadata as real items
        try:
            from jedi_fugitive.items.tokens import TOKEN_MAP as token_map
        except Exception:
            token_map = {}
        pickup_map = {
            # Gold is now handled above before this check
            getattr(Display, "WRECKAGE", "w"): {"name":"Wreckage"},
            getattr(Display, "POTION", "p"): {"name":"Potion"},
            # artifact handling is special-cased below to wire into the Sith Codex and artifact effects
            getattr(Display, "ARTIFACT", "A"): {"name":"Artifact"},
        }
        
        # Check for enemy equipment drops (uses 'E' token for equipment, 'M' token for materials)
        if (cell == 'E' or cell == 'M') and hasattr(game, 'equipment_drops'):
            try:
                equipment_drop = game.equipment_drops.get((px, py))
                if equipment_drop:
                    # capacity check
                    max_inv = int(getattr(game, 'max_inventory', 9) or 9)
                    cur_inv = len(getattr(game.player, 'inventory', []) or [])
                    if cur_inv >= max_inv:
                        try: game.ui.messages.add("Inventory full. Can't pick up item.")
                        except Exception: pass
                        return
                    
                    if not hasattr(game.player, 'inventory') or game.player.inventory is None:
                        game.player.inventory = []
                    
                    # Add the actual item object to inventory
                    dropped_item = equipment_drop['item']
                    game.player.inventory.append(dropped_item)
                    
                    # Clear the map
                    game.game_map[py][px] = floor
                    
                    # Remove from equipment_drops
                    del game.equipment_drops[(px, py)]
                    
                    # Message
                    item_name = equipment_drop.get('name', 'equipment')
                    try: game.ui.messages.add(f"Picked up {item_name}.")
                    except Exception: pass
                    
                    # Add to travel log with item details
                    try:
                        if hasattr(game.player, 'add_log_entry'):
                            item_type = equipment_drop.get('type', 'item')
                            item_rarity = equipment_drop.get('rarity', 'Common')
                            
                            # Get item description
                            item_desc = ""
                            if hasattr(dropped_item, 'description'):
                                item_desc = getattr(dropped_item, 'description', '')
                            elif isinstance(dropped_item, dict):
                                item_desc = dropped_item.get('description', '')
                            
                            # Create narrative entry
                            if item_type == 'weapon':
                                base_dmg = getattr(dropped_item, 'base_damage', 0) if hasattr(dropped_item, 'base_damage') else 0
                                entry = game.player.narrative_text(
                                    light_version=f"Found {item_name} ({item_rarity}). {item_desc}",
                                    dark_version=f"Claimed {item_name} ({item_rarity}) - a fitting tool for my power! {item_desc}",
                                    balanced_version=f"Found {item_name} ({item_rarity}, +{base_dmg} attack). {item_desc}"
                                )
                            elif item_type == 'armor':
                                entry = game.player.narrative_text(
                                    light_version=f"Found {item_name} ({item_rarity}) for protection. {item_desc}",
                                    dark_version=f"Seized {item_name} ({item_rarity}) to strengthen myself. {item_desc}",
                                    balanced_version=f"Found {item_name} ({item_rarity}). {item_desc}"
                                )
                            elif item_type == 'material':
                                entry = game.player.narrative_text(
                                    light_version=f"Collected {item_name} ({item_rarity}) - may be useful for crafting. {item_desc}",
                                    dark_version=f"Scavenged {item_name} ({item_rarity}) - a resource for my arsenal. {item_desc}",
                                    balanced_version=f"Found crafting material: {item_name} ({item_rarity}). {item_desc}"
                                )
                            else:
                                entry = game.player.narrative_text(
                                    light_version=f"Found {item_name}. {item_desc}",
                                    dark_version=f"Acquired {item_name} to fuel my journey. {item_desc}",
                                    balanced_version=f"Found {item_name}. {item_desc}"
                                )
                            game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
                    except Exception:
                        pass
                    
                    try:
                        game.turn_count = getattr(game, 'turn_count', 0) + 1
                    except Exception:
                        pass
                    
                    return
            except Exception as e:
                print(f"Error picking up equipment drop: {e}")
                pass
        
        # Prefer explicit item entries placed on the map (game.items_on_map)
        try:
            items_here = [it for it in getattr(game, 'items_on_map', []) or [] if it.get('x') == px and it.get('y') == py]
        except Exception:
            items_here = []
        # inventory capacity (default 9)
        max_inv = int(getattr(game, 'max_inventory', 9) or 9)
        cur_inv = len(getattr(game.player, 'inventory', []) or [])
        if items_here:
            it = items_here[0]
            try:
                if cur_inv >= max_inv:
                    try: game.ui.messages.add("Inventory full. Can't pick up item.")
                    except Exception: pass
                    return
                if not hasattr(game.player, 'inventory') or game.player.inventory is None:
                    game.player.inventory = []
                entry = dict(it) if isinstance(it, dict) else it
                game.player.inventory.append(entry)
                # remove map entry and clear glyph on the map
                try:
                    game.items_on_map.remove(it)
                except Exception:
                    game.items_on_map = [i for i in getattr(game, 'items_on_map', []) or [] if not (i.get('x') == px and i.get('y') == py)]
                try:
                    game.game_map[py][px] = floor
                except Exception:
                    pass
                
                item_name = entry.get('name', entry.get('token', 'item'))
                try: game.ui.messages.add(f"Picked up {item_name}.")
                except Exception: pass
                
                # Add to travel log
                try:
                    if hasattr(game.player, 'add_log_entry'):
                        item_desc = entry.get('description', '')
                        entry_text = game.player.narrative_text(
                            light_version=f"Found {item_name}. {item_desc}",
                            dark_version=f"Acquired {item_name} for my arsenal. {item_desc}",
                            balanced_version=f"Found {item_name}. {item_desc}"
                        )
                        game.player.add_log_entry(entry_text, getattr(game, 'turn_count', 0))
                except Exception:
                    pass
                
                try:
                    game.turn_count = getattr(game, 'turn_count', 0) + 1
                except Exception:
                    pass
                return
            except Exception:
                pass

        if cell in token_map:
            # add rich item dict so equip/use logic has full info
            if not hasattr(game.player, "inventory") or game.player.inventory is None:
                game.player.inventory = []
            # capacity check
            max_inv = int(getattr(game, 'max_inventory', 9) or 9)
            cur_inv = len(getattr(game.player, 'inventory', []) or [])
            if cur_inv >= max_inv:
                try: game.ui.messages.add("Inventory full. Can't pick up item.")
                except Exception: pass
                return
            info = token_map.get(cell)
            try:
                # make a shallow copy to avoid mutating shared prototypes
                item_entry = dict(info)
            except Exception:
                item_entry = {"token": cell, "name": str(cell)}
            # ensure token/name present
            item_entry.setdefault('token', cell)
            item_entry.setdefault('name', item_entry.get('name', str(cell)))
            game.player.inventory.append(item_entry)
            game.game_map[py][px] = floor
            try: game.ui.messages.add(f"Picked up {item_entry.get('name','item')}.") 
            except Exception: pass
            try:
                game.turn_count = getattr(game, 'turn_count', 0) + 1
            except Exception:
                pass
            return
        
        # Gold is now handled at the top of this function
        
        if cell in pickup_map:
            it = pickup_map[cell]
            # Special wiring for artifacts: create a rich artifact item and register discovery with the Sith Codex
            if cell == getattr(Display, 'ARTIFACT', 'A'):
                try:
                    # choose an artifact id from the canonical definitions if available
                    from jedi_fugitive.game.sith_codex import SITH_ARTIFACTS
                    import random as _rnd
                    aid = None
                    try:
                        aid = _rnd.choice(list(SITH_ARTIFACTS.keys()))
                    except Exception:
                        aid = None
                    if aid and aid in SITH_ARTIFACTS:
                        meta = SITH_ARTIFACTS[aid]
                        art_item = {
                            'artifact_id': aid,
                            'name': meta.get('name', 'Sith Artifact'),
                            'effect': meta.get('effect'),
                            'lore': meta.get('lore'),
                            'stress_effect': int(meta.get('stress_effect', 0)),
                            'force_echo': bool(meta.get('force_echo', False)),
                        }
                        if not hasattr(game.player, "inventory") or game.player.inventory is None:
                            game.player.inventory = []
                        game.player.inventory.append(art_item)
                        game.game_map[py][px] = floor
                        # narrative counter
                        try:
                            game.artifacts_collected = getattr(game, 'artifacts_collected', 0) + 1
                            try:
                                game.ui.messages.add(f"Artifact collected ({game.artifacts_collected}/{getattr(game, 'artifacts_needed', 3)})")
                            except Exception:
                                pass
                        except Exception:
                            pass
                        try:
                            game.ui.messages.add(f"Picked up {art_item.get('name')}.")
                        except Exception:
                            pass
                        try:
                            game.turn_count = getattr(game, 'turn_count', 0) + 1
                        except Exception:
                            pass
                        # register in codex if available and apply side-effects
                        try:
                            if getattr(game, 'sith_codex', None) is not None:
                                msg, is_echo = game.sith_codex.discover_entry('sith_artifacts', aid)
                                if msg:
                                    try: game.add_message(msg)
                                    except Exception: pass
                                if is_echo:
                                    try:
                                        # apply force insight if player supports it
                                        if hasattr(game.player, 'gain_force_insight'):
                                            try: game.player.gain_force_insight(aid)
                                            except Exception: pass
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                        # apply stress impact of artifact pickup
                        try:
                            se = int(art_item.get('stress_effect', 0))
                            if se and hasattr(game.player, 'add_stress'):
                                try:
                                    added = game.player.add_stress(se, source='artifact_pickup')
                                    try: game.ui.messages.add(f"The artifact's presence unsettles you. (+{added} stress)")
                                    except Exception: pass
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        return
                except Exception:
                    # fallback to generic artifact handling below
                    pass

            # Generic pickups (wreckage, potion, fallback artifact)
            # Note: Gold is now handled earlier in the function before pickup_map check
            
            # capacity check for regular items
            max_inv = int(getattr(game, 'max_inventory', 9) or 9)
            cur_inv = len(getattr(game.player, 'inventory', []) or [])
            if cur_inv >= max_inv:
                try: game.ui.messages.add("Inventory full. Can't pick up item.")
                except Exception: pass
                return
            if not hasattr(game.player, "inventory") or game.player.inventory is None:
                game.player.inventory = []
            game.player.inventory.append(it)
            game.game_map[py][px] = floor
            # track narrative artifact collection (game-level counter)
            try:
                if cell == getattr(Display, 'ARTIFACT', 'A'):
                    game.artifacts_collected = getattr(game, 'artifacts_collected', 0) + 1
                    try:
                        game.ui.messages.add(f"Artifact collected ({game.artifacts_collected}/{getattr(game, 'artifacts_needed', 3)})")
                    except Exception:
                        pass
            except Exception:
                pass
            try: game.ui.messages.add(f"Picked up {it.get('name','item')}.") 
            except Exception: pass
            try:
                game.turn_count = getattr(game, 'turn_count', 0) + 1
            except Exception:
                pass
            return
        # Do not pick up arbitrary map glyphs (landmarks, stairs, outposts). Only pick explicit
        # item entries (game.items_on_map), token_map entries, or known pickup_map glyphs.
        try: game.ui.messages.add("Nothing to pick up here.") 
        except Exception: pass
    except Exception as e:
        try: 
            import traceback
            game.ui.messages.add(f"Pick up failed: {str(e)}")
            # Debug: print to terminal
            # Error: Pick up error: {e}
            traceback.print_exc()
        except Exception: pass

def equip_item(game):
    """Equip item: uses inventory_chooser when multiple, applies stat effects and removes from inventory."""
    try:
        inv = getattr(game.player, "inventory", []) or []
        if not inv:
            try: game.ui.messages.add("No items to equip.") 
            except Exception: pass
            return
        chosen = None
        if len(inv) > 1:
            chosen = inventory_chooser(game)
        else:
            chosen = inv[0]
        if chosen is None:
            try: game.ui.messages.add("Equip cancelled.") 
            except Exception: pass
            return

        # explicit token -> name map (same tokens used when placing/picking up)
        token_map = {"v": "Vibroblade", "s": "Energy Shield", "b": "Blaster Pistol"}

        # helper to get display name for heuristics
        def _name(it):
            if isinstance(it, str):
                return token_map.get(it, it)
            if isinstance(it, dict):
                return it.get("name", str(it))
            return getattr(it, "name", str(it))

        name = _name(chosen)
        
        # Check if it's a material (crafting component, not equippable)
        item_type_attr = None
        if isinstance(chosen, dict):
            item_type_attr = chosen.get("type", None)
        elif hasattr(chosen, 'type'):
            item_type_attr = getattr(chosen, 'type', None)
        
        if item_type_attr == "material":
            try: game.ui.messages.add(f"{name} is a crafting material. Use 'C' (Shift+c) to craft with it.")
            except Exception: pass
            return
        
        # determine slot using mapped name so tokens are classified correctly
        # Also check if it's actually a Shield class instance
        is_shield = False
        item_class_name = type(chosen).__name__ if hasattr(chosen, '__class__') else str(type(chosen))
        
        # Check multiple ways if it's a shield
        if "shield" in name.lower() or "buckler" in name.lower():
            is_shield = True
        elif isinstance(chosen, dict):
            if chosen.get("slot") == "offhand" or chosen.get("type") == "shield":
                is_shield = True
        elif hasattr(chosen, 'slot') and getattr(chosen, 'slot') == "offhand":
            is_shield = True
        elif hasattr(chosen, 'type') and getattr(chosen, 'type') == "shield":
            is_shield = True
        elif hasattr(chosen, 'is_shield') and getattr(chosen, 'is_shield'):
            is_shield = True
        elif item_class_name == "Shield":
            is_shield = True
            
        is_armor = ("armor" in name.lower()) or (isinstance(chosen, dict) and chosen.get("slot") == "body")
        is_offhand_weapon = False
        
        # Check if it's a one-handed weapon that could be offhand
        if not is_shield and not is_armor:
            try:
                from jedi_fugitive.items.weapons import HandRequirement
                if hasattr(chosen, 'hands') and chosen.hands == HandRequirement.ONE_HAND:
                    # Ask if main or offhand when main hand is already occupied
                    main_weapon = getattr(game.player, 'equipped_weapon', None)
                    if main_weapon:
                        # Check if main weapon allows offhand (not 2H or Dual)
                        main_hands = getattr(main_weapon, 'hands', HandRequirement.ONE_HAND)
                        if main_hands == HandRequirement.ONE_HAND:
                            # Prompt player: main hand (replace) or offhand (dual wield)?
                            try:
                                main_weapon_name = getattr(main_weapon, 'name', 'current weapon')
                                game.ui.messages.add(f"━━━ DUAL WIELD? ━━━")
                                game.ui.messages.add(f"Equipping 1H weapon: {name}")
                                game.ui.messages.add(f"Press 'm' = Replace {main_weapon_name} in main hand")
                                game.ui.messages.add(f"Press 'o' = Dual wield in offhand")
                                game.ui.messages.add(f"Press ESC = Cancel")
                                
                                # Force a draw so messages appear
                                try:
                                    from jedi_fugitive.game.ui_renderer import draw
                                    draw(game)
                                except Exception as e:
                                    pass  # Error: Draw failed
                                
                                # Wait for player choice
                                choice = game.stdscr.getch()
                                
                                if choice == ord('o'):
                                    # Equip to offhand
                                    is_offhand_weapon = True
                                    game.ui.messages.add(f"Dual-wielding {name}!")
                                elif choice == ord('m'):
                                    # Equip to main hand (continue normal flow)
                                    is_offhand_weapon = False
                                    game.ui.messages.add(f"Replacing main weapon with {name}")
                                else:
                                    # Cancel
                                    try: game.ui.messages.add("Equip cancelled.")
                                    except Exception: pass
                                    return
                            except Exception as e:
                                # Default to main hand if prompt fails (safer than offhand)
                                pass  # Error: Dual wield prompt failed
                                game.ui.messages.add(f"Equipping {name} to main hand (prompt failed)")
                                is_offhand_weapon = False
                        else:
                            # Main weapon is 2H or Dual, can't use offhand - will replace main
                            is_offhand_weapon = False
            except Exception:
                pass

        # backup current equipped to avoid accidental loss on failure
        prev_weapon = getattr(game.player, "equipped_weapon", None)
        prev_armor = getattr(game.player, "equipped_armor", None)
        prev_offhand = getattr(game.player, "equipped_offhand", None)

        # Handle shield or offhand weapon
        if is_shield or is_offhand_weapon:
            success = equip_offhand(game, chosen)
            if success:
                # Remove from inventory
                try:
                    inv.remove(chosen)
                except Exception:
                    for i in list(inv):
                        if i == chosen:
                            try: inv.remove(i)
                            except Exception: pass
                            break
            return

        # perform equip with proper slot handling and stat application
        if is_armor:
            try:
                _remove_equipment_effects(game, "armor")
                _apply_equipment_effects(game, chosen, "armor")
            except Exception as e:
                # restore previous on failure
                game.player.equipped_armor = prev_armor
                try: game.ui.messages.add(f"Equip failed, armor unchanged: {e}") 
                except Exception: pass
                return
        else:
            try:
                old_attack = getattr(game.player, 'attack', 0)
                _remove_equipment_effects(game, "weapon")
                _apply_equipment_effects(game, chosen, "weapon")
                new_attack = getattr(game.player, 'attack', 0)
                bonus = new_attack - old_attack if hasattr(game.player, '_base_stats') else 0
                if bonus > 0:
                    try: game.ui.messages.add(f"⚔ Equipped {name} ⚔ Attack +{bonus} (now {new_attack})")
                    except Exception: pass
            except Exception as e:
                # restore previous on failure
                game.player.equipped_weapon = prev_weapon
                try: game.ui.messages.add(f"Equip failed, weapon unchanged: {e}") 
                except Exception: pass
                return

        # remove one instance from inventory (best-effort)
        try:
            inv.remove(chosen)
        except Exception:
            for i in list(inv):
                if i == chosen:
                    try: inv.remove(i) 
                    except Exception: pass
                    break

        # Message already displayed in equip logic above (with attack bonus for weapons)
        if is_armor:
            try: game.ui.messages.add(f"Equipped {name}.") 
            except Exception: pass
        try:
            game.turn_count = getattr(game, 'turn_count', 0) + 1
        except Exception:
            pass
    except Exception:
        try: game.ui.messages.add("Equip failed (internal).") 
        except Exception: pass


def drop_item(game):
    """Drop an item from inventory onto the ground at player's location."""
    try:
        inv = getattr(game.player, "inventory", []) or []
        if not inv:
            try: game.ui.messages.add("No items to drop.")
            except Exception: pass
            return False
        
        chosen = None
        if len(inv) > 1:
            chosen = inventory_chooser(game)
        else:
            chosen = inv[0]
        
        if chosen is None:
            try: game.ui.messages.add("Drop cancelled.")
            except Exception: pass
            return False
        
        # Get player position
        px = getattr(game.player, "x", 0)
        py = getattr(game.player, "y", 0)
        
        # Create item entry for the map
        if isinstance(chosen, dict):
            item_entry = {**chosen, 'x': px, 'y': py}
        elif isinstance(chosen, str):
            # Token string - create dict entry
            item_entry = {'token': chosen, 'name': chosen, 'x': px, 'y': py}
        else:
            # Object with attributes
            item_entry = {
                'name': getattr(chosen, 'name', str(chosen)),
                'x': px,
                'y': py
            }
            if hasattr(chosen, 'token'):
                item_entry['token'] = getattr(chosen, 'token')
        
        # Add to map items
        if not hasattr(game, 'items_on_map') or game.items_on_map is None:
            game.items_on_map = []
        game.items_on_map.append(item_entry)
        
        # Remove from inventory
        try:
            inv.remove(chosen)
        except Exception:
            # Try to remove matching item
            for i in list(inv):
                if i == chosen:
                    try: 
                        inv.remove(i)
                        break
                    except Exception: 
                        pass
        
        # Get item name for message
        item_name = "item"
        if isinstance(chosen, dict):
            item_name = chosen.get('name', chosen.get('token', 'item'))
        elif isinstance(chosen, str):
            item_name = chosen
        elif hasattr(chosen, 'name'):
            item_name = getattr(chosen, 'name', 'item')
        
        try: 
            game.ui.messages.add(f"Dropped {item_name}.")
        except Exception: 
            pass
        
        try:
            game.turn_count = getattr(game, 'turn_count', 0) + 1
        except Exception:
            pass
        
        return True
    except Exception as e:
        try: 
            game.ui.messages.add(f"Drop failed: {e}")
        except Exception: 
            pass
        return False


def use_item(game):
    """Use a consumable from inventory (or a selected item)."""
    try:
        inv = getattr(game.player, "inventory", []) or []
        if not inv:
            try: game.ui.messages.add("No items to use.")
            except Exception: pass
            return False
        chosen = None
        if len(inv) > 1:
            chosen = inventory_chooser(game)
        else:
            chosen = inv[0]
        if chosen is None:
            try: game.ui.messages.add("Use cancelled.")
            except Exception: pass
            return False

        # normalize chosen to a dict with 'effect' if possible
        item_obj = None
        if isinstance(chosen, dict):
            item_obj = chosen
        elif isinstance(chosen, str):
            # token string or simple id
            # try to look up consumable definitions
            try:
                from jedi_fugitive.items.consumables import ITEM_DEFS
                for it in ITEM_DEFS:
                    if it.get('token') == chosen or it.get('id') == chosen:
                        item_obj = {**it}
                        break
            except Exception:
                item_obj = None
        elif hasattr(chosen, 'get'):
            item_obj = chosen

        # If not a consumable (e.g., weapon token), advise to equip
        # Special-case: Sith artifacts offer a CHOICE - absorb (dark path) or destroy (light path)
        if item_obj and isinstance(item_obj, dict) and item_obj.get('artifact_id'):
            try:
                aid = item_obj.get('artifact_id')
                artifact_name = item_obj.get('name', 'a Sith artifact')
                xp_gain = 150 if item_obj.get('force_echo') else 75 + int(item_obj.get('stress_effect', 0) or 0)
                
                # Prompt player for choice: Absorb (Dark) or Destroy (Light)
                try:
                    game.ui.messages.add(f"You hold {artifact_name}. What will you do?")
                    game.ui.messages.add("Press 'a' to ABSORB its power (Dark Side) or 'd' to DESTROY it (Light Side)")
                    
                    # Force a draw so messages appear
                    try:
                        from jedi_fugitive.game.ui_renderer import draw
                        draw(game)
                    except Exception:
                        pass
                    
                    # Wait for player choice
                    choice = game.stdscr.getch()
                    
                    if choice == ord('a'):
                        # ABSORB - Dark Side path
                        game.player.dark_xp = getattr(game.player, 'dark_xp', 0) + xp_gain
                        game.player.dark_corruption = min(100, getattr(game.player, 'dark_corruption', 0) + 15)
                        game.ui.messages.add(f"You ABSORB {artifact_name}'s dark power! +{xp_gain} Dark XP")
                        
                        # Check for dark side level up
                        if game.player.dark_xp >= getattr(game.player, 'xp_to_next_dark', 100):
                            game.player.dark_level = getattr(game.player, 'dark_level', 1) + 1
                            game.player.dark_xp -= getattr(game.player, 'xp_to_next_dark', 100)
                            game.player.xp_to_next_dark = game.player.dark_level * 100
                            
                            # Apply stat bonuses: all stats +1, extra +1 attack for dark path
                            game.player.max_hp = getattr(game.player, 'max_hp', 10) + 5
                            game.player.attack = getattr(game.player, 'attack', 10) + 2  # +2 for dark path
                            game.player.defense = getattr(game.player, 'defense', 5) + 1
                            game.player.evasion = getattr(game.player, 'evasion', 10) + 1
                            game.player.accuracy = getattr(game.player, 'accuracy', 80) + 1
                            
                            game.ui.messages.add(f"Level up! You are now Level {game.player.dark_level}")
                            game.ui.messages.add(f"Dark path: +5 HP, +2 ATK, +1 DEF, +1 EVA, +1 ACC")
                            # Unlock dark side ability
                            _unlock_dark_ability(game)
                        
                        if hasattr(game.player, 'add_log_entry'):
                            # Dark Side artifact absorption - narrative reflects growing corruption
                            entry = game.player.narrative_text(
                                light_version=f"Absorbed {artifact_name} with reluctance, feeling its dark power seep in.",
                                dark_version=f"Devoured the essence of {artifact_name}, reveling in its dark power!",
                                balanced_version=f"Absorbed {artifact_name}, embracing the dark side."
                            )
                            game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
                        
                    elif choice == ord('d'):
                        # DESTROY - Light Side path
                        game.player.light_xp = getattr(game.player, 'light_xp', 0) + xp_gain
                        game.player.dark_corruption = max(0, getattr(game.player, 'dark_corruption', 0) - 10)
                        game.ui.messages.add(f"You DESTROY {artifact_name}, purifying its essence! +{xp_gain} Light XP")
                        
                        # Check for light side level up
                        if game.player.light_xp >= getattr(game.player, 'xp_to_next_light', 100):
                            game.player.light_level = getattr(game.player, 'light_level', 1) + 1
                            game.player.light_xp -= getattr(game.player, 'xp_to_next_light', 100)
                            game.player.xp_to_next_light = game.player.light_level * 100
                            
                            # Apply stat bonuses: all stats +1, extra +1 evasion for light path
                            game.player.max_hp = getattr(game.player, 'max_hp', 10) + 5
                            game.player.attack = getattr(game.player, 'attack', 10) + 1
                            game.player.defense = getattr(game.player, 'defense', 5) + 1
                            game.player.evasion = getattr(game.player, 'evasion', 10) + 2  # +2 for light path
                            game.player.accuracy = getattr(game.player, 'accuracy', 80) + 1
                            
                            game.ui.messages.add(f"Level up! You are now Level {game.player.light_level}")
                            game.ui.messages.add(f"Light path: +5 HP, +1 ATK, +1 DEF, +2 EVA, +1 ACC")
                            # Unlock light side ability
                            _unlock_light_ability(game)
                        
                        if hasattr(game.player, 'add_log_entry'):
                            # Light Side artifact destruction - narrative reflects purity/resistance
                            entry = game.player.narrative_text(
                                light_version=f"Cleansed {artifact_name}, its corruption dissolved by the Force.",
                                dark_version=f"Destroyed {artifact_name}, though it felt like wasted power.",
                                balanced_version=f"Destroyed {artifact_name}, resisting the darkness."
                            )
                            game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
                    else:
                        game.ui.messages.add("Choice cancelled. Artifact remains in inventory.")
                        return False
                    
                    game.player.artifacts_consumed = getattr(game.player, 'artifacts_consumed', 0) + 1
                    
                except Exception as ex:
                    try:
                        game.ui.messages.add(f"Error processing artifact: {ex}")
                    except Exception:
                        pass
                    return False
                # apply force insight if applicable
                try:
                    if item_obj.get('force_echo') and hasattr(game.player, 'gain_force_insight'):
                        game.player.gain_force_insight(aid)
                except Exception:
                    pass
                # consume artifact (remove from inventory)
                removed = False
                try:
                    if chosen in inv:
                        inv.remove(chosen)
                        removed = True
                except Exception:
                    pass
                if not removed:
                    # Try removing by artifact_id match
                    for i in list(inv):
                        try:
                            if isinstance(i, dict) and i.get('artifact_id') == aid:
                                inv.remove(i)
                                removed = True
                                break
                        except Exception:
                            continue
                if not removed:
                    try:
                        game.ui.messages.add("Warning: Could not remove artifact from inventory.")
                    except Exception:
                        pass
                try:
                    game.turn_count = getattr(game, 'turn_count', 0) + 1
                except Exception:
                    pass
                return True
            except Exception as e:
                try:
                    game.ui.messages.add(f"Error consuming artifact: {e}")
                except Exception:
                    pass
                return False

        if not item_obj or ('effect' not in item_obj and 'token' not in item_obj):
            try: game.ui.messages.add("That item can't be used directly. Try equipping it (press 'e').")
            except Exception: pass
            return False

        eff = item_obj.get('effect', {})
        used = False
        # heal effect
        if 'heal' in eff:
            try:
                heal = int(eff.get('heal', 0))
                game.player.hp = min(getattr(game.player, 'max_hp', game.player.hp), getattr(game.player, 'hp', 0) + heal)
                try: game.ui.messages.add(f"Used {item_obj.get('name','item')}: healed {heal} HP.")
                except Exception: pass
                used = True
            except Exception:
                used = False

        # stress reduction effect (consumables like Meditation Focus / Calming Tea)
        if 'stress_reduction' in eff:
            try:
                amt = int(eff.get('stress_reduction', 0))
                game.player.reduce_stress(amt)
                try: game.ui.messages.add(f"Used {item_obj.get('name','item')}: -{amt} stress.")
                except Exception: pass
                used = True
            except Exception:
                used = False

        # area damage (grenade)
        if 'area_damage' in eff and 'radius' in eff:
            try:
                dmg = int(eff.get('area_damage', 0))
                rad = int(eff.get('radius', 1))
                px = getattr(game.player, 'x', 0); py = getattr(game.player, 'y', 0)
                affected = []
                for e in list(getattr(game, 'enemies', []) or []):
                    try:
                        ex = int(getattr(e, 'x', 0)); ey = int(getattr(e, 'y', 0))
                        dx = ex - px; dy = ey - py
                        # use circular distance so area looks round: dx*dx + dy*dy <= rad*rad
                        if (dx*dx + dy*dy) <= (rad * rad):
                            if hasattr(e, 'take_damage'):
                                e.take_damage(dmg)
                            else:
                                try: e.hp = getattr(e, 'hp', 0) - dmg
                                except Exception: pass
                            affected.append(e)
                    except Exception:
                        continue
                try: game.ui.messages.add(f"Used {item_obj.get('name','item')}: dealt {dmg} area damage to {len(affected)} targets.")
                except Exception: pass
                used = True
            except Exception:
                used = False

        # ammo / energy cell
        if 'ammo' in eff:
            try:
                amt = int(eff.get('ammo', 0))
                game.player.ammo = getattr(game.player, 'ammo', 0) + amt
                try: game.ui.messages.add(f"Used {item_obj.get('name','item')}: gained {amt} ammo.")
                except Exception: pass
                used = True
            except Exception:
                used = False

        # compass/tombfinder: trigger game.perform_scan() when present
        if 'compass' in eff and eff.get('compass'):
            try:
                # prefer GameManager.perform_scan if available
                if hasattr(game, 'perform_scan') and callable(game.perform_scan):
                    ok = game.perform_scan()
                    if ok:
                        used = True
                else:
                    # fallback: no scan available -> provide a small message
                    try: game.ui.messages.add("The compass whirs but reveals nothing.")
                    except Exception: pass
                    used = False
            except Exception:
                used = False

        if used:
            # consume one instance from inventory
            try:
                inv.remove(chosen)
            except Exception:
                # try to remove matching token or dict
                for i in list(inv):
                    try:
                        if isinstance(chosen, str) and (i == chosen or (isinstance(i, dict) and i.get('token') == chosen)):
                            inv.remove(i); break
                        if isinstance(chosen, dict) and i == chosen:
                            inv.remove(i); break
                    except Exception:
                        continue
                try:
                    game.turn_count = getattr(game, 'turn_count', 0) + 1
                except Exception:
                    pass
                return True

        try: game.ui.messages.add("Item use failed.")
        except Exception: pass
        return False
    except Exception as e:
        try: 
            import traceback
            game.ui.messages.add(f"Use failed: {str(e)}")
            # Debug: print to terminal
            # Error: Use item error: {e}
            traceback.print_exc()
        except Exception: pass
        return False


def equip_offhand(game, item):
    """Equip shield or offhand weapon. Returns True if successful."""
    try:
        from jedi_fugitive.items.weapons import HandRequirement
        
        # Check if main hand weapon allows offhand use
        main_weapon = getattr(game.player, 'equipped_weapon', None)
        if main_weapon:
            main_hands = getattr(main_weapon, 'hands', HandRequirement.ONE_HAND)
            if main_hands in [HandRequirement.TWO_HAND, HandRequirement.DUAL_WIELD]:
                try: 
                    game.ui.messages.add(f"Cannot use offhand with {main_weapon.name} (requires both hands)")
                except Exception: 
                    game.ui.messages.add("Main weapon requires both hands!")
                return False
        
        # Determine item type
        item_type = None
        item_name = "item"
        if isinstance(item, dict):
            item_type = item.get('type', '')
            item_name = item.get('name', 'item')
        elif hasattr(item, 'slot'):
            if item.slot == 'offhand':
                item_type = 'shield'
            item_name = getattr(item, 'name', 'item')
        elif hasattr(item, 'hands'):
            if item.hands == HandRequirement.ONE_HAND:
                item_type = 'weapon'
            item_name = getattr(item, 'name', 'item')
        
        # Must be shield or 1H weapon
        if item_type not in ['shield', 'weapon']:
            try: game.ui.messages.add("Cannot equip this in offhand!")
            except Exception: pass
            return False
        
        # Unequip current offhand if any
        old_offhand = getattr(game.player, 'equipped_offhand', None)
        if old_offhand:
            unequip_offhand(game)
        
        # Equip new offhand
        game.player.equipped_offhand = item
        
        # Apply bonuses
        if item_type == 'shield':
            defense_bonus = getattr(item, 'defense_bonus', 0)
            evasion_bonus = getattr(item, 'evasion_bonus', 0)
            game.player.defense += defense_bonus
            game.player.evasion += evasion_bonus
            try: 
                game.ui.messages.add(f"🛡 Equipped {item_name} 🛡 +{defense_bonus} Defense, +{evasion_bonus} Evasion")
            except Exception: pass
        else:  # offhand weapon
            attack_bonus = getattr(item, 'base_damage', 0)
            accuracy_bonus = getattr(item, 'accuracy_mod', 0)
            game.player.attack += int(attack_bonus * 0.5)  # Half damage for offhand
            game.player.accuracy += int(accuracy_bonus * 0.5)
            try: 
                game.ui.messages.add(f"Dual-wielding {item_name}! +{int(attack_bonus*0.5)} Attack")
            except Exception: pass
        
        # Add to travel log
        try:
            if hasattr(game.player, 'add_log_entry'):
                if item_type == 'shield':
                    entry = game.player.narrative_text(
                        light_version=f"Equipped {item_name} for protection.",
                        dark_version=f"Armed myself with {item_name}, ready for war.",
                        balanced_version=f"Equipped {item_name} in offhand."
                    )
                else:
                    entry = game.player.narrative_text(
                        light_version=f"Dual-wielding {item_name} out of necessity.",
                        dark_version=f"Now wielding {item_name} - more weapons, more power!",
                        balanced_version=f"Now dual-wielding {item_name}."
                    )
                game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
        except Exception:
            pass
        
        return True
    except Exception:
        try: game.ui.messages.add("Failed to equip offhand.")
        except Exception: pass
        return False


def unequip_offhand(game):
    """Remove offhand equipment and return bonuses."""
    try:
        offhand = getattr(game.player, 'equipped_offhand', None)
        if not offhand:
            try: game.ui.messages.add("No offhand equipped!")
            except Exception: pass
            return False
        
        # Determine type and remove bonuses
        if hasattr(offhand, 'slot') and offhand.slot == 'offhand':
            # Shield
            defense_bonus = getattr(offhand, 'defense_bonus', 0)
            evasion_bonus = getattr(offhand, 'evasion_bonus', 0)
            game.player.defense -= defense_bonus
            game.player.evasion -= evasion_bonus
        else:
            # Offhand weapon
            attack_bonus = getattr(offhand, 'base_damage', 0)
            accuracy_bonus = getattr(offhand, 'accuracy_mod', 0)
            game.player.attack -= int(attack_bonus * 0.5)
            game.player.accuracy -= int(accuracy_bonus * 0.5)
        
        # Add back to inventory
        inv = getattr(game.player, 'inventory', [])
        inv.append(offhand)
        
        offhand_name = getattr(offhand, 'name', 'offhand item')
        try: game.ui.messages.add(f"Unequipped {offhand_name}")
        except Exception: pass
        
        game.player.equipped_offhand = None
        return True
    except Exception:
        try: game.ui.messages.add("Failed to unequip offhand.")
        except Exception: pass
        return False


def open_crafting_menu(game):
    """Open crafting interface for upgrading weapons and crafting items."""
    try:
        from jedi_fugitive.items.crafting import CRAFTING_RECIPES, check_materials
        
        # Build recipe list with availability
        recipe_options = []
        menu_items = []
        
        for recipe in CRAFTING_RECIPES:
            # Check if player has materials
            has_materials = check_materials(game.player.inventory, recipe.materials)
            
            # Build display string
            materials_str = ", ".join([f"{count}x {name}" for name, count in recipe.materials.items()])
            status = "✓" if has_materials else "✗"
            
            # Recipe type indicator
            type_icon = {"weapon_upgrade": "⚔", "item_craft": "🛠", "repair": "🔧"}.get(recipe.recipe_type, "•")
            
            display_text = f"{status} {type_icon} {recipe.name}"
            description = f"   {recipe.description}\n   Needs: {materials_str}"
            
            recipe_options.append((recipe, has_materials, description))
            menu_items.append(display_text)
        
        if not menu_items:
            try: game.ui.messages.add("No crafting recipes available!")
            except Exception: pass
            return False
        
        # Show menu with descriptions
        try:
            # Use the UI's centered menu system
            ui = game.ui
            selected = ui.centered_menu(menu_items, title="═══ CRAFTING BENCH ═══")
            
            if selected is None or selected < 0 or selected >= len(recipe_options):
                try: game.ui.messages.add("Crafting cancelled.")
                except Exception: pass
                return False
            
            recipe, has_materials, description = recipe_options[selected]
            
            if not has_materials:
                materials_str = ", ".join([f"{count}x {name}" for name, count in recipe.materials.items()])
                try: game.ui.messages.add(f"Cannot craft {recipe.name}! Missing: {materials_str}")
                except Exception: pass
                return False
            
            # Craft the item
            success = craft_item(game, recipe.name)
            return success
            
        except Exception as e:
            try: game.ui.messages.add(f"Crafting menu error: {e}")
            except Exception: pass
            return False
    except Exception as e:
        try: game.ui.messages.add(f"Crafting failed: {e}")
        except Exception: pass
        return False


def craft_item(game, recipe_name):
    """Craft an item using a recipe."""
    try:
        from jedi_fugitive.items.crafting import get_recipe_by_name, check_materials, consume_materials
        
        recipe = get_recipe_by_name(recipe_name)
        if not recipe:
            try: game.ui.messages.add("Recipe not found!")
            except Exception: pass
            return False
        
        # Check materials
        if not check_materials(game.player.inventory, recipe.materials):
            materials_str = ", ".join([f"{count}x {name}" for name, count in recipe.materials.items()])
            try: game.ui.messages.add(f"Missing materials: {materials_str}")
            except Exception: pass
            return False
        
        # Consume materials
        game.player.inventory = consume_materials(game.player.inventory, recipe.materials)
        
        # Apply result based on recipe type
        if recipe.recipe_type == "weapon_upgrade":
            # Upgrade equipped weapon
            weapon = getattr(game.player, 'equipped_weapon', None)
            if not weapon:
                try: game.ui.messages.add("No weapon equipped to upgrade!")
                except Exception: pass
                return False
            
            result = recipe.result
            stat = result.get('stat')
            bonus = result.get('bonus', 0)
            upgrade_name = result.get('name', 'Upgraded')
            
            # Apply bonus to weapon
            if stat == 'attack':
                current_damage = getattr(weapon, 'base_damage', 0)
                weapon.base_damage = current_damage + bonus
                game.player.attack += bonus
            elif stat == 'accuracy':
                current_acc = getattr(weapon, 'accuracy_mod', 0)
                weapon.accuracy_mod = current_acc + bonus
                game.player.accuracy += bonus
            elif stat == 'defense':
                game.player.defense += bonus
            
            # Update weapon name
            weapon_name = getattr(weapon, 'name', 'Weapon')
            if upgrade_name not in weapon_name:
                weapon.name = f"{weapon_name} ({upgrade_name})"
            
            try: 
                game.ui.messages.add(f"Upgraded {weapon_name} with {recipe.name}!")
            except Exception: pass
            
            # Add to travel log
            try:
                if hasattr(game.player, 'add_log_entry'):
                    entry = game.player.narrative_text(
                        light_version=f"Carefully crafted {recipe.name} to improve my weapon.",
                        dark_version=f"Forged {recipe.name} - my weapon grows deadlier!",
                        balanced_version=f"Crafted {recipe.name} upgrade for weapon."
                    )
                    game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
            except Exception:
                pass
        
        elif recipe.recipe_type == "item_craft":
            # Create new item
            result = recipe.result
            new_item = dict(result)  # Create item dict
            game.player.inventory.append(new_item)
            
            item_name = result.get('name', 'Item')
            try: 
                game.ui.messages.add(f"Crafted {item_name}!")
            except Exception: pass
            
            # Add to travel log
            try:
                if hasattr(game.player, 'add_log_entry'):
                    entry = game.player.narrative_text(
                        light_version=f"Crafted {item_name} from salvaged parts.",
                        dark_version=f"Assembled {item_name} - resourcefulness is power.",
                        balanced_version=f"Crafted {item_name}."
                    )
                    game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
            except Exception:
                pass
        
        return True
    except Exception as e:
        try: game.ui.messages.add(f"Crafting error: {e}")
        except Exception: pass
        return False