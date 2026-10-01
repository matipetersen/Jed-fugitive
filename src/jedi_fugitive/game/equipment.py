
import curses
from jedi_fugitive.game.level import Display
from jedi_fugitive.config import MAX_INVENTORY_SIZE
from jedi_fugitive.game import logger as game_logger
log = getattr(game_logger, 'get_logger', lambda name=None: None)("equipment")


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
            
            # Actually grant the ability to the player
            try:
                from jedi_fugitive.game.force_abilities import FORCE_ABILITIES
                import copy
                
                # Find the ability by name
                for ability in FORCE_ABILITIES:
                    if getattr(ability, 'name', '').lower().replace(' ', '').replace('/', '') == ability_name.lower().replace(' ', '').replace('/', ''):
                        # Create unlocked copy for player
                        player_ability = copy.deepcopy(ability)
                        player_ability.unlocked = True
                        game.player.force_abilities[ability_name] = player_ability
                        break
            except Exception:
                pass
            
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
            
            # Actually grant the ability to the player
            try:
                from jedi_fugitive.game.force_abilities import FORCE_ABILITIES
                import copy
                
                # Find the ability by name
                for ability in FORCE_ABILITIES:
                    if getattr(ability, 'name', '').lower().replace(' ', '').replace('/', '') == ability_name.lower().replace(' ', '').replace('/', ''):
                        # Create unlocked copy for player
                        player_ability = copy.deepcopy(ability)
                        player_ability.unlocked = True
                        game.player.force_abilities[ability_name] = player_ability
                        break
            except Exception:
                pass
            
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


def _inspect_inventory_item(game, item):
    """Display detailed inspection of an inventory item with lore."""
    try:
        from jedi_fugitive.game import inspection
        
        # Get item name and token
        item_name = None
        item_token = None
        
        if isinstance(item, str):
            item_token = item
            token_names = {'v': 'Vibroblade', 'b': 'Blaster Pistol', 's': 'Armor', 'L': 'Lightsaber'}
            item_name = token_names.get(item, item)
        elif isinstance(item, dict):
            item_name = item.get('name', 'Unknown')
            item_token = item.get('token', item.get('id'))
        else:
            item_name = getattr(item, 'name', str(item))
            item_token = getattr(item, 'id', None)
        
        # Get lore data
        player_corruption = getattr(game.player, 'dark_corruption', 50)
        lore_data = inspection.get_item_inspection(item_token, item_name, player_corruption)
        
        # Build display lines
        lines = []
        lines.append("╔═════════════════════════════════════════════════╗")
        lines.append(f"║     ITEM INSPECTION: {lore_data['name'][:28]}")
        lines.append("╚═════════════════════════════════════════════════╝")
        lines.append("")
        lines.append(lore_data['description'])
        lines.append("")
        
        # Show stats if available
        if isinstance(item, dict):
            if 'damage' in item or 'base_damage' in item:
                dmg = item.get('damage', item.get('base_damage', 0))
                lines.append(f"Damage: {dmg}")
            if 'defense' in item:
                lines.append(f"Defense: +{item.get('defense', 0)}")
            if 'accuracy' in item:
                lines.append(f"Accuracy: {item.get('accuracy', 0)}%")
            if 'range' in item:
                lines.append(f"Range: {item.get('range', 0)} tiles")
            if 'ammo' in item and 'max_ammo' in item:
                lines.append(f"Ammo: {item.get('ammo', 0)}/{item.get('max_ammo', 0)}")
            if 'effect' in item:
                effect = item['effect']
                if isinstance(effect, dict):
                    if 'heal' in effect:
                        lines.append(f"Heals: +{effect['heal']} HP")
                    if 'force_restore' in effect:
                        lines.append(f"Force: +{effect['force_restore']}")
            lines.append("")
        
        # Add lore text
        if lore_data.get('lore'):
            lines.append("═══ LORE ═══")
            lines.append(lore_data['lore'])
            lines.append("")
        
        # Add condition text (for lightsabers)
        if lore_data.get('condition'):
            lines.append(lore_data['condition'])
            lines.append("")
        
        # Add choice prompt (for artifacts)
        if lore_data.get('choice'):
            lines.append("⚠ WARNING ⚠")
            lines.append(lore_data['choice'])
            lines.append("")
        
        lines.append("Press any key to return to inventory...")
        
        # Display
        if hasattr(game.ui, 'centered_dialog'):
            game.ui.centered_dialog(lines, title="Item Inspection")
        else:
            for line in lines:
                try:
                    game.ui.messages.add(line)
                except:
                    pass
    except Exception as e:
        try:
            game.ui.messages.add(f"Item inspection failed: {e}")
        except:
            pass

def _is_equippable_item(item):
    """Check if an item can be equipped (weapon, armor, shield)."""
    if isinstance(item, str):
        # Token-based items (legacy system)
        return item in ['v', 'b', 's', 'L']  # vibroblade, blaster, shield, lightsaber
    elif isinstance(item, dict):
        item_type = item.get('type', '')
        return item_type in ['weapon', 'armor', 'shield', 'equipment']
    elif hasattr(item, 'weapon_type') or hasattr(item, 'armor_type'):
        # Object-based weapons/armor
        return True
    elif hasattr(item, 'shield_type') or hasattr(item, 'is_shield'):
        # Object-based shields
        return True
    return False

def _is_usable_item(item):
    """Check if an item can be used/consumed."""
    if isinstance(item, str):
        return False  # Token items are equippable, not consumable
    elif isinstance(item, dict):
        item_type = item.get('type', '')
        # Usable items: consumables, artifacts, special items
        return item_type in ['consumable', 'stimpack', 'medkit', 'grenade'] or item.get('artifact_id')
    elif hasattr(item, 'consumable') or hasattr(item, 'uses'):
        return True
    return False

def inventory_chooser(game, filter_type=None):
    """Enhanced chooser with filtering using popup dialogue. filter_type: 'equippable', 'usable', or None (all items)."""
    try:
        all_inv = getattr(game.player, "inventory", []) or []
        
        # Filter inventory based on type
        if filter_type == 'equippable':
            inv = [item for item in all_inv if _is_equippable_item(item)]
            title = "EQUIPPABLE ITEMS"
        elif filter_type == 'usable':
            inv = [item for item in all_inv if _is_usable_item(item)]
            title = "USABLE ITEMS"
        else:
            inv = all_inv
            title = "INVENTORY"
        
        if not inv:
            filter_msg = {
                'equippable': "No equippable items in inventory.",
                'usable': "No usable items in inventory.", 
                None: "Inventory empty."
            }
            try: 
                game.ui.messages.add(filter_msg.get(filter_type, "Inventory empty."))
            except Exception: 
                pass
            return None
        
        # Build items list for popup dialogue
        popup_items = []
        for it in inv:
            name = it if isinstance(it, str) else (it.get("name") if isinstance(it, dict) else getattr(it, "name", str(it)))
            desc = ""
            
            # Generate descriptions
            if isinstance(it, str):
                token_names = {'v': 'Vibroblade', 'b': 'Blaster', 's': 'Armor'}
                name = token_names.get(it, it)
                desc = "Equipment"
            elif isinstance(it, dict):
                item_type = it.get("type", "")
                if item_type:
                    desc = item_type.title()
                elif it.get("artifact_id"):
                    desc = "Artifact"
            elif hasattr(it, 'hands'):
                hands = getattr(it, 'hands', None)
                if hands:
                    desc = f"{hands.value} Weapon"
                else:
                    desc = "Weapon"
            elif hasattr(it, 'is_shield') and getattr(it, 'is_shield', False):
                def_bonus = getattr(it, 'defense_bonus', 0)
                ev_bonus = getattr(it, 'evasion_bonus', 0)
                if ev_bonus > 0:
                    desc = f"Shield: +{def_bonus} DEF, +{ev_bonus} EVA"
                elif ev_bonus < 0:
                    desc = f"Shield: +{def_bonus} DEF, {ev_bonus} EVA"
                else:
                    desc = f"Shield: +{def_bonus} DEF"
            elif hasattr(it, 'defense_bonus'):
                desc = f"Armor: +{getattr(it, 'defense_bonus', 0)} DEF"
            elif hasattr(it, 'defense'):
                desc = "Armor"
            elif hasattr(it, 'base_damage'):
                damage = getattr(it, 'base_damage', 0)
                desc = f"Weapon: {damage} DMG"
            
            popup_items.append((name, desc, {}))
        
        # Show popup dialogue
        try:
            result = game.ui.popup_dialogue(popup_items, title=title, show_details=True, allow_inspect=True)
            
            # Handle inspect action
            if isinstance(result, tuple) and result[0] == 'inspect':
                idx = result[1]
                if 0 <= idx < len(inv):
                    _inspect_inventory_item(game, inv[idx])
                    # Return to inventory after inspect
                    return inventory_chooser(game, filter_type)
                return None
            
            # Handle selection
            if result is not None and 0 <= result < len(inv):
                return inv[result]
            
        except Exception:
            # Fallback to None if popup fails
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
            # Mark stats cache as dirty to force UI refresh
            game.player._stats_cache_dirty = True
    except Exception:
        pass

def _remove_equipment_effects(game, slot):
    """Restore base stats and clear the named slot ('weapon'|'armor'). Reapply remaining equipment."""
    try:
        base = getattr(game.player, "_base_stats", None)
        if base:
            current_hp = getattr(game.player, "hp", 10)
            
            game.player.attack = base.get("attack", getattr(game.player, "attack", 1))
            game.player.defense = base.get("defense", getattr(game.player, "defense", 0))
            game.player.evasion = base.get("evasion", getattr(game.player, "evasion", 0))
            game.player.max_hp = base.get("max_hp", getattr(game.player, "max_hp", 10))
            
            # CRITICAL: Never let HP go to 0 when re-equipping
            # Keep current HP, but cap it to new max_hp if needed
            try:
                if current_hp > 0:
                    game.player.hp = min(current_hp, game.player.max_hp)
                else:
                    # HP was already 0 (player is dead), don't change it
                    game.player.hp = current_hp
            except Exception:
                game.player.hp = max(1, current_hp)  # Emergency fallback: ensure at least 1 HP
        if slot == "weapon":
            game.player.equipped_weapon = None
        elif slot == "armor":
            game.player.equipped_armor = None
        # Mark stats cache as dirty to force UI refresh
        game.player._stats_cache_dirty = True
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
            # Invalidate stats cache so gold counter updates in GUI
            game.player._stats_cache_dirty = True
            game.game_map[py][px] = floor
            try: 
                game.ui.messages.add(f"Found {gold_amount} gold! (Total: {game.player.gold_collected})")
            except Exception: 
                pass
            
            # Gold pickup no longer added to travel log (too spammy)
            
            try:
                pass  # turn_count advances once per world tick (GameManager._world_tick)
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
        
        # Unified pickup: enemy drops, explicit map entries, then bare item glyphs.
        # Everything is materialized into its real inventory form (see items/registry.py).
        from jedi_fugitive.items import registry
        if not hasattr(game.player, 'inventory') or game.player.inventory is None:
            game.player.inventory = []
        inv = game.player.inventory
        max_inv = game.player.get_max_inventory() if hasattr(game.player, 'get_max_inventory') else int(getattr(game, 'max_inventory', 9) or 9)
        drops = getattr(game, 'equipment_drops', None) or {}
        try:
            items_here = [it for it in getattr(game, 'items_on_map', []) or [] if it.get('x') == px and it.get('y') == py]
        except Exception:
            items_here = []

        picked = []
        journal_kind = None
        rarity = ''
        if (px, py) in drops:
            if len(inv) >= max_inv:
                try: game.ui.messages.add("Inventory full. Can't pick up item.")
                except Exception: pass
                return
            drop = drops.pop((px, py))
            picked = [registry.materialize(drop.get('item'))]
            journal_kind = drop.get('type', 'item')
            rarity = drop.get('rarity', '')
        elif items_here:
            entry = items_here[0]
            is_cache = entry.get('guarded') or entry.get('name') == 'Guarded Supply Cache'
            if is_cache:
                picked = registry.cache_loot()
            else:
                picked = [registry.materialize(entry)]
            if len(inv) + len(picked) > max_inv:
                try: game.ui.messages.add("Inventory full. Can't pick up item.")
                except Exception: pass
                return
            try:
                game.items_on_map.remove(entry)
            except Exception:
                pass
            if is_cache:
                try: game.ui.messages.add("You force the Sith supply cache open.")
                except Exception: pass
        elif cell in token_map:
            if len(inv) >= max_inv:
                try: game.ui.messages.add("Inventory full. Can't pick up item.")
                except Exception: pass
                return
            picked = [registry.materialize(token_map.get(cell))]

        picked = [it for it in picked if it is not None]
        if picked:
            for it in picked:
                inv.append(it)
                nm = registry.item_name(it)
                if rarity in ('Legendary', 'Epic'):
                    msg = f"★★★ You pick up the {rarity.upper()} {nm}! ★★★"
                elif rarity == 'Rare':
                    msg = f"★★ You pick up the RARE {nm}! ★★"
                else:
                    msg = f"Picked up {nm}."
                try: game.ui.messages.add(msg)
                except Exception: pass
                # Jedi artifacts power the comms terminal: tell the player where they stand
                if isinstance(it, dict) and it.get('type') == 'quest_item':
                    have = sum(1 for i in inv if isinstance(i, dict) and i.get('type') == 'quest_item')
                    game.artifacts_collected = max(getattr(game, 'artifacts_collected', 0), have)
                    try:
                        game.ui.messages.add(f"Jedi Artifact recovered ({have}/{getattr(game, 'artifacts_needed', 3)}). Bring them to the comms terminal.")
                    except Exception: pass
                    try:
                        game.player.add_to_travel_log(f"[ARTIFACT] Recovered a corrupted Jedi relic ({have}/3). Its dark pulse beats against my palm.")
                    except Exception: pass
            # clear the glyph once nothing else lies on this tile
            try:
                still = (px, py) in drops or any(it.get('x') == px and it.get('y') == py for it in getattr(game, 'items_on_map', []) or [])
                if not still and cell in registry.ITEM_GLYPHS | {'L'}:
                    game.game_map[py][px] = floor
            except Exception:
                pass
            if journal_kind and hasattr(game.player, 'add_log_entry'):
                try:
                    nm = registry.item_name(picked[0])
                    game.player.add_log_entry(f"Found {nm}{' (' + rarity + ')' if rarity else ''} on a fallen foe.", getattr(game, 'turn_count', 0))
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
                            # Sith artifacts are a temptation, not the quest relics that power the comms
                            game.sith_artifacts_collected = getattr(game, 'sith_artifacts_collected', 0) + 1
                            try:
                                game.ui.messages.add("A Sith artifact. Use it (u) to ABSORB or DESTROY its power.")
                            except Exception:
                                pass
                        except Exception:
                            pass
                        try:
                            game.ui.messages.add(f"Picked up {art_item.get('name')}.")
                        except Exception:
                            pass
                        try:
                            pass  # turn_count advances once per world tick (GameManager._world_tick)
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
            
            # capacity check for regular items (base + armor bonus)
            max_inv = game.player.get_max_inventory() if hasattr(game.player, 'get_max_inventory') else MAX_INVENTORY_SIZE
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
                    game.sith_artifacts_collected = getattr(game, 'sith_artifacts_collected', 0) + 1
            except Exception:
                pass
            try: game.ui.messages.add(f"Picked up {it.get('name','item')}.") 
            except Exception: pass
            try:
                pass  # turn_count advances once per world tick (GameManager._world_tick)
            except Exception:
                pass
            return
        # Do not pick up arbitrary map glyphs (landmarks, stairs, outposts). Only pick explicit
        # item entries (game.items_on_map), token_map entries, or known pickup_map glyphs.
        try: game.ui.messages.add("Nothing to pick up here.") 
        except Exception: pass
    except Exception as e:
        try:
            game.ui.messages.add(f"Pick up failed: {str(e)}")
            if log:
                log.exception("Pick up failed", exc_info=e)
        except Exception as log_exc:
            if log:
                log.error(f"Pick up error logging failed: {log_exc}")

def equip_item(game):
    """Equip item: uses filtered inventory chooser for equippable items only."""
    try:
        # Get only equippable items
        all_inv = getattr(game.player, "inventory", []) or []
        equippable_inv = [item for item in all_inv if _is_equippable_item(item)]
        
        if not equippable_inv:
            try: 
                game.ui.messages.add("No equippable items found.")
                game.ui.messages.add("Equippable: weapons, armor, shields")
            except Exception: 
                pass
            return
            
        chosen = None
        if len(equippable_inv) > 1:
            chosen = inventory_chooser(game, filter_type='equippable')
        else:
            chosen = equippable_inv[0]
        if chosen is None:
            try: game.ui.messages.add("Equip cancelled.") 
            except Exception: pass
            return

        # explicit token -> name map (same tokens used when placing/picking up)
        token_map = {"v": "Vibroblade", "s": "Energy Shield", "b": "Blaster Pistol", "L": "Lightsaber"}

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
        # Check if it's an ENERGY_SHIELD weapon type (these should always be shields)
        elif hasattr(chosen, 'weapon_type'):
            try:
                from jedi_fugitive.items.weapons import WeaponType
                if chosen.weapon_type == WeaponType.ENERGY_SHIELD:
                    is_shield = True
            except Exception:
                pass
            
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
                    game.player.inventory.remove(chosen)
                except Exception:
                    for i in list(game.player.inventory):
                        if i == chosen:
                            try: game.player.inventory.remove(i)
                            except Exception: pass
                            break
            return

        # CRITICAL FIX: Return previously equipped items to inventory before equipping new ones
        if is_armor:
            # Return old armor to inventory if it exists
            if prev_armor is not None:
                try:
                    if not hasattr(game.player, 'inventory') or game.player.inventory is None:
                        game.player.inventory = []
                    game.player.inventory.append(prev_armor)
                    try:
                        old_armor_name = getattr(prev_armor, 'name', str(prev_armor))
                        game.ui.messages.add(f"Returned {old_armor_name} to inventory.")
                    except Exception:
                        pass
                except Exception:
                    pass
            
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
            # Return old weapon to inventory if it exists
            if prev_weapon is not None:
                try:
                    if not hasattr(game.player, 'inventory') or game.player.inventory is None:
                        game.player.inventory = []
                    game.player.inventory.append(prev_weapon)
                    try:
                        old_weapon_name = getattr(prev_weapon, 'name', str(prev_weapon))
                        game.ui.messages.add(f"Returned {old_weapon_name} to inventory.")
                    except Exception:
                        pass
                except Exception:
                    pass
            
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
            game.player.inventory.remove(chosen)
        except Exception:
            for i in list(game.player.inventory):
                if i == chosen:
                    try: game.player.inventory.remove(i) 
                    except Exception: pass
                    break

        # Message already displayed in equip logic above (with attack bonus for weapons)
        if is_armor:
            try: game.ui.messages.add(f"Equipped {name}.") 
            except Exception: pass
        try:
            pass  # turn_count advances once per world tick (GameManager._world_tick)
        except Exception:
            pass
    except Exception as e:
        try:
            game.ui.messages.add("Equip failed (internal).")
            if log:
                log.exception("Equip failed (internal)", exc_info=e)
        except Exception as log_exc:
            if log:
                log.error(f"Equip error logging failed: {log_exc}")


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
            chosen = inventory_chooser(game, filter_type=None)  # Show all items for dropping
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
        
        # Keep the real object so picking it back up restores the same item
        try:
            from jedi_fugitive.items import registry
            item_entry = registry.map_entry(chosen, px, py, token=item_entry.get('token') if isinstance(chosen, dict) else None)
        except Exception:
            pass
        # Add to map items
        if not hasattr(game, 'items_on_map') or game.items_on_map is None:
            game.items_on_map = []
        game.items_on_map.append(item_entry)
        try:
            if game.game_map[py][px] == getattr(Display, 'FLOOR', '.'):
                game.game_map[py][px] = item_entry.get('token') or 'E'
        except Exception:
            pass
        
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
            pass  # turn_count advances once per world tick (GameManager._world_tick)
        except Exception:
            pass
        
        return True
    except Exception as e:
        try:
            game.ui.messages.add(f"Drop failed: {e}")
            if log:
                log.exception("Drop failed", exc_info=e)
        except Exception as log_exc:
            if log:
                log.error(f"Drop error logging failed: {log_exc}")
        return False


def use_item(game):
    """Use a consumable from inventory - only shows usable items."""
    try:
        # Get only usable items
        all_inv = getattr(game.player, "inventory", []) or []
        usable_inv = [item for item in all_inv if _is_usable_item(item)]
        
        if not usable_inv:
            try: 
                game.ui.messages.add("No usable items found.")
                game.ui.messages.add("Usable: consumables, artifacts, stimpacks")
            except Exception: 
                pass
            return False
            
        chosen = None
        if len(usable_inv) > 1:
            chosen = inventory_chooser(game, filter_type='usable')
        else:
            chosen = usable_inv[0]
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
                        
                        # Check for dark side level up - USE UNIFIED SYSTEM
                        while game.player.dark_xp >= getattr(game.player, 'xp_to_next_dark', 100):
                            game.player.dark_level = getattr(game.player, 'dark_level', 1) + 1
                            game.player.dark_xp -= getattr(game.player, 'xp_to_next_dark', 100)
                            game.player.xp_to_next_dark = int(game.player.xp_to_next_dark * 1.5)
                            game.player.level = max(getattr(game.player, 'light_level', 1), game.player.dark_level)
                            
                            # Call unified level_up() which shows interactive menu
                            try:
                                game.player.level_up()
                                game.ui.messages.add(f"Dark Side Level Up! Now Dark Level {game.player.dark_level}")
                            except Exception:
                                pass
                        
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
                        
                        # Check for light side level up - USE UNIFIED SYSTEM
                        while game.player.light_xp >= getattr(game.player, 'xp_to_next_light', 100):
                            game.player.light_level = getattr(game.player, 'light_level', 1) + 1
                            game.player.light_xp -= getattr(game.player, 'xp_to_next_light', 100)
                            game.player.xp_to_next_light = int(game.player.xp_to_next_light * 1.5)
                            game.player.level = max(game.player.light_level, getattr(game.player, 'dark_level', 1))
                            
                            # Call unified level_up() which shows interactive menu
                            try:
                                game.player.level_up()
                                game.ui.messages.add(f"Light Side Level Up! Now Light Level {game.player.light_level}")
                            except Exception:
                                pass
                        
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
                    if chosen in game.player.inventory:
                        game.player.inventory.remove(chosen)
                        removed = True
                except Exception:
                    pass
                if not removed:
                    # Try removing by artifact_id match
                    for i in list(game.player.inventory):
                        try:
                            if isinstance(i, dict) and i.get('artifact_id') == aid:
                                game.player.inventory.remove(i)
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
                    pass  # turn_count advances once per world tick (GameManager._world_tick)
                except Exception:
                    pass
                return True
            except Exception as e:
                try:
                    game.ui.messages.add(f"Error consuming artifact: {e}")
                except Exception:
                    pass
                return False

        ctype = chosen.get('type') if isinstance(chosen, dict) else getattr(chosen, 'type', None)
        cname = chosen.get('name', 'item') if isinstance(chosen, dict) else getattr(chosen, 'name', 'item')
        if ctype == 'material':
            try: game.ui.messages.add(f"{cname} is a crafting material. Press 'C' to craft with it.")
            except Exception: pass
            return False
        if ctype == 'quest_item':
            try: game.ui.messages.add(f"The {cname} must be placed in the comms terminal. Keep it safe.")
            except Exception: pass
            return False

        if not item_obj or ('effect' not in item_obj and 'token' not in item_obj):
            try: game.ui.messages.add("That item can't be used directly. Try equipping it (press 'e').")
            except Exception: pass
            return False

        if isinstance(item_obj, dict) and not item_obj.get('effect'):
            try:
                from jedi_fugitive.items import registry
                resolved = registry.materialize(item_obj)
                if isinstance(resolved, dict):
                    item_obj = resolved
            except Exception:
                pass
        eff = item_obj.get('effect') or {}
        if not isinstance(eff, dict):
            eff = {}
        # Grenades are thrown, not detonated at your feet: hand over to the targeting mode
        if 'area_damage' in eff:
            game.pending_grenade_throw = True
            game.target_x = getattr(game.player, 'x', 0)
            game.target_y = getattr(game.player, 'y', 0)
            try: game.ui.messages.add("Grenade primed: move the reticle (range 3) and press Enter to throw, Esc to cancel.")
            except Exception: pass
            return False
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
                game.player.inventory.remove(chosen)
                return True
            except Exception:
                # try to remove matching token or dict
                for i in list(game.player.inventory):
                    try:
                        if isinstance(chosen, str) and (i == chosen or (isinstance(i, dict) and i.get('token') == chosen)):
                            game.player.inventory.remove(i); break
                        if isinstance(chosen, dict) and i == chosen:
                            game.player.inventory.remove(i); break
                    except Exception:
                        continue
                try:
                    pass  # turn_count advances once per world tick (GameManager._world_tick)
                except Exception:
                    pass
                return True

        try: game.ui.messages.add("Item use failed.")
        except Exception: pass
        return False
    except Exception as e:
        try:
            game.ui.messages.add(f"Use failed: {str(e)}")
            if log:
                log.exception("Use item failed", exc_info=e)
        except Exception as log_exc:
            if log:
                log.error(f"Use item error logging failed: {log_exc}")
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
        elif hasattr(item, 'type'):
            # Check type attribute directly (for Shield objects)
            item_type = getattr(item, 'type', None)
            item_name = getattr(item, 'name', 'item')
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
        
        # Mark stats cache dirty to force UI refresh
        game.player._stats_cache_dirty = True
        
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
    except Exception as e:
        try:
            game.ui.messages.add("Failed to equip offhand.")
            if log:
                log.exception("Equip offhand failed", exc_info=e)
        except Exception as log_exc:
            if log:
                log.error(f"Equip offhand error logging failed: {log_exc}")
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
    except Exception as e:
        try:
            game.ui.messages.add("Failed to unequip offhand.")
            if log:
                log.exception("Unequip offhand failed", exc_info=e)
        except Exception as log_exc:
            if log:
                log.error(f"Unequip offhand error logging failed: {log_exc}")
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
            
            # Check weapon compatibility for weapon upgrades
            is_compatible = True
            compatibility_reason = ""
            if recipe.recipe_type == "weapon_upgrade":
                weapon = getattr(game.player, 'equipped_weapon', None)
                if weapon:
                    try:
                        from jedi_fugitive.items.upgrade_compatibility import is_upgrade_compatible
                        is_compatible, compatibility_reason = is_upgrade_compatible(recipe.name, weapon)
                    except Exception:
                        is_compatible = True  # Fallback to allowing upgrade
                else:
                    is_compatible = False
                    compatibility_reason = "No weapon equipped"
            
            # Build display string
            materials_str = ", ".join([f"{count}x {name}" for name, count in recipe.materials.items()])
            
            # Determine status icon
            if not is_compatible:
                status = "✗"  # Incompatible weapon
            elif has_materials:
                status = "✓"  # Can craft
            else:
                status = "○"  # Missing materials but compatible
            
            # Recipe type indicator
            type_icon = {"weapon_upgrade": "⚔", "item_craft": "🛠", "repair": "🔧"}.get(recipe.recipe_type, "•")
            
            display_text = f"{status} {type_icon} {recipe.name}"
            
            # Build description with compatibility info
            description = f"   {recipe.description}\n   Needs: {materials_str}"
            if not is_compatible:
                description += f"\n   ⚠ {compatibility_reason}"
            
            # Store actual availability (materials AND compatibility)
            actual_availability = has_materials and is_compatible
            
            recipe_options.append((recipe, actual_availability, description, is_compatible))
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
            
            # Handle both old and new tuple formats for backward compatibility
            if len(recipe_options[selected]) == 4:
                recipe, can_craft, description, is_compatible = recipe_options[selected]
            else:
                recipe, can_craft, description = recipe_options[selected]
                is_compatible = True
            
            if not can_craft:
                # Determine why it cannot be crafted
                has_materials = check_materials(game.player.inventory, recipe.materials)
                if not has_materials:
                    materials_str = ", ".join([f"{count}x {name}" for name, count in recipe.materials.items()])
                    try: game.ui.messages.add(f"Cannot craft {recipe.name}! Missing: {materials_str}")
                    except Exception: pass
                elif not is_compatible:
                    try: game.ui.messages.add(f"Cannot craft {recipe.name}! Not compatible with equipped weapon.")
                    except Exception: pass
                else:
                    try: game.ui.messages.add(f"Cannot craft {recipe.name}!")
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
        
        # PRE-VALIDATION: Check all requirements BEFORE consuming materials
        
        # 1. Check materials availability
        if not check_materials(game.player.inventory, recipe.materials):
            materials_str = ", ".join([f"{count}x {name}" for name, count in recipe.materials.items()])
            try: game.ui.messages.add(f"Missing materials: {materials_str}")
            except Exception: pass
            return False
        
        # 2. Check crafting skill level requirement
        if not game.player.can_craft_recipe(recipe.__dict__):
            required_level = getattr(recipe, 'required_level', 1)
            current_level = getattr(game.player, 'craft_level', 1)
            try: 
                game.ui.messages.add(f"Recipe requires crafting level {required_level} (you have {current_level})")
            except Exception: pass
            return False
        
        # 2. For weapon upgrades, validate weapon compatibility BEFORE consuming materials
        if recipe.recipe_type == "weapon_upgrade":
            weapon = getattr(game.player, 'equipped_weapon', None)
            if not weapon:
                try: game.ui.messages.add("No weapon equipped to upgrade!")
                except Exception: pass
                return False
            
            # Check weapon type compatibility
            try:
                from jedi_fugitive.items.upgrade_compatibility import is_upgrade_compatible
                is_compatible, reason = is_upgrade_compatible(recipe.name, weapon)
                if not is_compatible:
                    try: 
                        weapon_name = getattr(weapon, 'name', 'your weapon')
                        game.ui.messages.add(f"Cannot apply {recipe.name} to {weapon_name}: {reason}")
                    except Exception: 
                        game.ui.messages.add(f"{recipe.name} is not compatible with this weapon type")
                    return False
            except Exception:
                # If compatibility system fails, allow upgrade (backward compatibility)
                pass
        
        # ALL VALIDATION PASSED - Now consume materials and apply upgrade
        game.player.inventory = consume_materials(game.player.inventory, recipe.materials)
        
        # Apply result based on recipe type
        if recipe.recipe_type == "weapon_upgrade":
            # At this point we know weapon exists and is compatible
            
            result = recipe.result
            stat = result.get('stat')
            bonus = result.get('bonus', 0)
            upgrade_name = result.get('name', 'Upgraded')
            
            # Apply bonus to weapon (equipment system will handle player stat application)
            if stat == 'attack':
                current_damage = getattr(weapon, 'base_damage', 0)
                weapon.base_damage = current_damage + bonus
                weapon.upgrade_damage = getattr(weapon, 'upgrade_damage', 0) + bonus  # read by combat.weapon_roll
                # Note: Player attack will be updated when equipment effects are reapplied
            elif stat == 'accuracy':
                current_acc = getattr(weapon, 'accuracy_mod', 0)
                weapon.accuracy_mod = current_acc + bonus
                # Note: Player accuracy will be updated when equipment effects are reapplied
            elif stat == 'defense':
                # Defense upgrades apply directly to player (not weapon-dependent)
                game.player.defense += bonus
            elif stat == 'damage':  # Handle 'damage' stat (used by some recipes)
                current_damage = getattr(weapon, 'base_damage', 0)
                weapon.base_damage = current_damage + bonus
                weapon.upgrade_damage = getattr(weapon, 'upgrade_damage', 0) + bonus  # read by combat.weapon_roll
            
            # Handle secondary stat bonuses (e.g., Crystal Focus gives accuracy + attack)
            if 'stat2' in result and 'bonus2' in result:
                stat2 = result.get('stat2')
                bonus2 = result.get('bonus2', 0)
                if stat2 == 'attack':
                    current_damage = getattr(weapon, 'base_damage', 0)
                    weapon.base_damage = current_damage + bonus2
                    weapon.upgrade_damage = getattr(weapon, 'upgrade_damage', 0) + bonus2  # read by combat.weapon_roll
                elif stat2 == 'accuracy':
                    current_acc = getattr(weapon, 'accuracy_mod', 0)
                    weapon.accuracy_mod = current_acc + bonus2
                elif stat2 == 'defense':
                    game.player.defense += bonus2
                elif stat2 == 'durability':
                    # Handle durability bonuses (for future implementation)
                    pass
            
            # Update player stats by reapplying equipment effects
            # This ensures the new weapon bonuses are properly reflected
            try:
                # Temporarily remove weapon effects, then reapply with new bonuses
                _remove_equipment_effects(game, "weapon")
                _apply_equipment_effects(game, weapon, "weapon")
            except Exception:
                # Fallback: manually update attack based on weapon upgrade
                if stat == 'attack' or stat == 'damage':
                    game.player.attack = getattr(game.player.attack, 0, 10) + bonus
                elif stat == 'accuracy':
                    game.player.accuracy = getattr(game.player.accuracy, 0, 80) + bonus
            
            # Update weapon name
            weapon_name = getattr(weapon, 'name', 'Weapon')
            if upgrade_name not in weapon_name:
                weapon.name = f"{weapon_name} ({upgrade_name})"
            
            try: 
                game.ui.messages.add(f"Upgraded {weapon_name} with {recipe.name}!")
            except Exception: pass
            
            # Grant crafting XP based on recipe difficulty
            xp_gain = getattr(recipe, 'required_level', 1) * 25
            level_up_msg = game.player.gain_craft_xp(xp_gain)
            if level_up_msg:
                try:
                    game.ui.messages.add(level_up_msg)
                    game.ui.messages.add("💡 Keep crafting to unlock better recipes!")
                except Exception: pass
            else:
                # Show crafting XP progress
                try:
                    current_xp = getattr(game.player, 'craft_xp', 0)
                    xp_needed = getattr(game.player, 'craft_xp_to_next', 100)
                    game.ui.messages.add(f"Gained {xp_gain} crafting XP! ({current_xp}/{xp_needed} to next level)")
                except Exception:
                    pass
            
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
            
            # Grant crafting XP based on recipe difficulty
            xp_gain = getattr(recipe, 'required_level', 1) * 25
            level_up_msg = game.player.gain_craft_xp(xp_gain)
            if level_up_msg:
                try:
                    game.ui.messages.add(level_up_msg)
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
        try:
            game.ui.messages.add(f"Crafting error: {e}")
            if log:
                log.exception("Crafting menu error", exc_info=e)
        except Exception as log_exc:
            if log:
                log.error(f"Crafting menu error logging failed: {log_exc}")
        return False