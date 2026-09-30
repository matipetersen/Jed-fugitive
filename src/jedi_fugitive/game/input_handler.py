import curses
import traceback
from jedi_fugitive.game.level import Display
from jedi_fugitive.game import equipment
from jedi_fugitive.game import inspection
from jedi_fugitive.game import logger
log = getattr(logger, 'log', None)


def _fire_gun(game, tx, ty):
    """Fire ranged weapon at target coordinates (tx, ty)."""
    try:
        px = getattr(game.player, "x", 0)
        py = getattr(game.player, "y", 0)
        
        # Get weapon stats
        weapon = getattr(game.player, 'equipped_weapon', None)
        if not weapon:
            try: game.ui.messages.add("No weapon equipped!")
            except Exception as e:
                if log:
                    log.exception("Error in _fire_gun: no weapon equipped", exc_info=e)
            return False
        
        # Get weapon properties
        weapon_range = 5
        weapon_damage = 10
        weapon_accuracy = 80
        weapon_name = "Weapon"
        weapon_ammo = 0
        
        if isinstance(weapon, dict):
            weapon_range = weapon.get('range', 5)
            weapon_damage = weapon.get('base_damage', weapon.get('damage', 10))
            weapon_accuracy = weapon.get('accuracy', 80)
            weapon_name = weapon.get('name', 'Weapon')
            weapon_ammo = weapon.get('ammo', 0)
        elif hasattr(weapon, 'name'):
            weapon_range = getattr(weapon, 'range', 5)
            weapon_damage = getattr(weapon, 'base_damage', getattr(weapon, 'damage', 10))
            weapon_accuracy = getattr(weapon, 'accuracy', 80)
            weapon_name = weapon.name
            weapon_ammo = getattr(weapon, 'ammo', 0)
        
        # Check ammo
        if weapon_ammo <= 0:
            try: game.ui.messages.add(f"{weapon_name} is out of ammo! Cannot fire.")
            except Exception as e:
                if log:
                    log.exception("Error in _fire_gun: out of ammo", exc_info=e)
            return False
        
        # Check range - minimum 2 tiles, maximum weapon_range
        dist = abs(tx - px) + abs(ty - py)
        if dist < 2:
            try: game.ui.messages.add(f"Target too close! Ranged weapons require at least 2 tiles distance.")
            except Exception as e:
                if log:
                    log.exception("Error in _fire_gun: target too close", exc_info=e)
            return False
        if dist > weapon_range:
            try: game.ui.messages.add(f"Target too far! Weapon range: {weapon_range} tiles.")
            except Exception as e:
                if log:
                    log.exception("Error in _fire_gun: target too far", exc_info=e)
            return False
        
        # Find enemy at target
        target_enemy = None
        for enemy in getattr(game, 'enemies', []):
            if getattr(enemy, 'x', -1) == tx and getattr(enemy, 'y', -1) == ty:
                target_enemy = enemy
                break
        
        if not target_enemy:
            try: game.ui.messages.add("No enemy at target location!")
            except Exception as e:
                if log:
                    log.exception("Error in _fire_gun: no enemy at target", exc_info=e)
            return False
        
        # Calculate hit chance
        import random
        hit_chance = weapon_accuracy - getattr(target_enemy, 'evasion', 0)
        hit_roll = random.randint(1, 100)
        
        if hit_roll <= hit_chance:
            # Hit! Deal damage
            damage = max(1, weapon_damage - getattr(target_enemy, 'defense', 0))
            
            if hasattr(target_enemy, 'take_damage'):
                target_enemy.take_damage(damage)
            else:
                target_enemy.hp = getattr(target_enemy, 'hp', 0) - damage
            
            # Consume ammo
            if isinstance(weapon, dict):
                weapon['ammo'] = weapon.get('ammo', 0) - 1
            elif hasattr(weapon, 'ammo'):
                weapon.ammo = getattr(weapon, 'ammo', 0) - 1
            
            remaining_ammo = weapon.get('ammo', 0) if isinstance(weapon, dict) else getattr(weapon, 'ammo', 0)
            
            try:
                game.ui.messages.add(f"Shot {getattr(target_enemy, 'name', 'enemy')} for {damage} damage! [{remaining_ammo} rounds left]")
            except Exception as e:
                if log:
                    log.exception("Error in _fire_gun: add message after hit", exc_info=e)
                pass
            
            # Add to travel log
            try:
                if hasattr(game.player, 'add_log_entry'):
                    entry = game.player.narrative_text(
                        light_version=f"Fired {weapon_name} in defense, striking {getattr(target_enemy, 'name', 'enemy')}.",
                        dark_version=f"Gunned down {getattr(target_enemy, 'name', 'enemy')} without hesitation!",
                        balanced_version=f"Shot {getattr(target_enemy, 'name', 'enemy')} with {weapon_name}."
                    )
                    game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
            except Exception as e:
                if log:
                    log.exception("Error in _fire_gun: add log entry after hit", exc_info=e)
                pass
        else:
            # Miss! Still consume ammo
            if isinstance(weapon, dict):
                weapon['ammo'] = weapon.get('ammo', 0) - 1
            elif hasattr(weapon, 'ammo'):
                weapon.ammo = getattr(weapon, 'ammo', 0) - 1
            
            remaining_ammo = weapon.get('ammo', 0) if isinstance(weapon, dict) else getattr(weapon, 'ammo', 0)
            
            try:
                game.ui.messages.add(f"Shot missed {getattr(target_enemy, 'name', 'enemy')}! [{remaining_ammo} rounds left]")
            except Exception:
                pass
        
        # Consume turn
        try:
            pass  # turn_count advances once per world tick (GameManager._world_tick)
        except Exception:
            pass
        
        return True
    except Exception as e:
        try: game.ui.messages.add(f"Gun error: {e}")
        except Exception: pass
        return False


def _throw_grenade(game, tx, ty):
    """Throw a grenade at target coordinates (tx, ty)."""
    try:
        px = getattr(game.player, "x", 0)
        py = getattr(game.player, "y", 0)
        
        # Check range (max 3 tiles Manhattan distance)
        dist = abs(tx - px) + abs(ty - py)
        if dist > 3:
            try: game.ui.messages.add("Target too far! Grenades have 3-tile range.")
            except Exception as e:
                if log:
                    log.exception("Error in _fire_gun: add log entry (fail)", exc_info=e)
            return False
        
        # Find grenade in inventory
        inv = getattr(game.player, 'inventory', []) or []
        grenade = None
        grenade_idx = None
        for idx, item in enumerate(inv):
            if isinstance(item, dict) and item.get('id') in ['grenade', 'thermal_grenade']:
                grenade = item
                grenade_idx = idx
                break
        
        if grenade is None:
            try: game.ui.messages.add("No grenades in inventory!")
            except Exception as e:
                if log:
                    log.exception("Error in _fire_gun: add log entry (fail 2)", exc_info=e)
            return False
        
        # Get grenade stats
        dmg = 12
        radius = 3
        if isinstance(grenade, dict) and 'effect' in grenade:
            eff = grenade['effect']
            dmg = int(eff.get('area_damage', dmg))
            radius = int(eff.get('radius', radius))
        
        # Deal damage to all enemies in radius and track kills
        affected = []
        killed = []
        for e in list(getattr(game, 'enemies', []) or []):
            try:
                ex = int(getattr(e, 'x', 0))
                ey = int(getattr(e, 'y', 0))
                dx = ex - tx
                dy = ey - ty
                # Circular radius check
                if (dx*dx + dy*dy) <= (radius * radius):
                    hp_before = getattr(e, 'hp', 0)
                    if hasattr(e, 'take_damage'):
                        e.take_damage(dmg)
                    else:
                        e.hp = getattr(e, 'hp', 0) - dmg
                    
                    affected.append(getattr(e, 'name', 'enemy'))
                    
                    # Check if enemy died from grenade
                    hp_after = getattr(e, 'hp', 0)
                    if hp_after <= 0 and hp_before > 0:
                        killed.append(e)
            except Exception:
                continue
        
        # Remove grenade from inventory
        try:
            inv.pop(grenade_idx)
        except Exception:
            pass
        
        # Award Dark XP for kills with multi-kill bonus
        try:
            if killed:
                # Base Dark XP per kill (reduced from 10 to 3)
                base_xp = 3
                total_xp = 0
                
                # Calculate XP with multi-kill bonuses
                kill_count = len(killed)
                for i, e in enumerate(killed):
                    enemy_xp = base_xp
                    
                    # Bonus for enemy level (reduced from 5 to 2)
                    enemy_level = getattr(e, 'level', 1)
                    enemy_xp += (enemy_level - 1) * 2
                    
                    # Multi-kill multiplier: 1x, 1.5x, 2x, 2.5x, 3x, etc.
                    if kill_count >= 2:
                        multi_bonus = 1.0 + (0.5 * (kill_count - 1))
                        enemy_xp = int(enemy_xp * multi_bonus)
                    
                    total_xp += enemy_xp
                    
                    # Update kill count
                    game.player.kills_count = getattr(game.player, 'kills_count', 0) + 1
                
                # Award Dark XP for killing (combat is a dark path)
                game.player.dark_xp = getattr(game.player, 'dark_xp', 0) + total_xp
                
                # Check for dark side level up - USE UNIFIED SYSTEM
                while game.player.dark_xp >= getattr(game.player, 'xp_to_next_dark', 100):
                    game.player.dark_level = getattr(game.player, 'dark_level', 1) + 1
                    game.player.dark_xp -= getattr(game.player, 'xp_to_next_dark', 100)
                    game.player.xp_to_next_dark = int(game.player.xp_to_next_dark * 1.5)
                    game.player.level = max(game.player.light_level, game.player.dark_level)
                    
                    # Call unified level_up() which shows interactive menu
                    try:
                        game.player.level_up()
                        game.ui.messages.add(f"#1#DARK SIDE LEVEL UP!#0# Now Dark Level {game.player.dark_level}")
                    except Exception:
                        pass
                
                # Messages
                if kill_count == 1:
                    try:
                        game.ui.messages.add(f"Killed 1 enemy! +{total_xp} Dark XP")
                    except Exception:
                        pass
                else:
                    try:
                        multi_bonus_pct = int((0.5 * (kill_count - 1)) * 100)
                        game.ui.messages.add(f"MULTI-KILL! {kill_count} enemies eliminated! +{multi_bonus_pct}% bonus")
                        game.ui.messages.add(f"Gained {total_xp} Dark XP!")
                    except Exception:
                        pass
        except Exception:
            pass
        
        # Messages
        try:
            if affected:
                game.ui.messages.add(f"Grenade explodes! {dmg} damage to {len(affected)} enemies: {', '.join(affected[:3])}")
            else:
                game.ui.messages.add(f"Grenade explodes harmlessly.")
        except Exception:
            pass
        
        # Add to travel log
        try:
            if hasattr(game.player, 'add_log_entry') and affected:
                if killed:
                    kill_count = len(killed)
                    if kill_count >= 3:
                        entry = game.player.narrative_text(
                            light_version=f"Reluctantly used explosives, neutralizing {kill_count} hostiles to protect myself.",
                            dark_version=f"GLORIOUS! {kill_count} enemies obliterated in a single blast of righteous fury!",
                            balanced_version=f"Tactical grenade eliminated {kill_count} enemies in one explosion."
                        )
                    else:
                        entry = game.player.narrative_text(
                            light_version=f"Used a grenade defensively, catching {len(affected)} enemies.",
                            dark_version=f"Hurled explosive death at {len(affected)} foes, savoring the destruction!",
                            balanced_version=f"Threw a grenade, damaging {len(affected)} enemies."
                        )
                else:
                    entry = game.player.narrative_text(
                        light_version=f"Used a grenade defensively, catching {len(affected)} enemies.",
                        dark_version=f"Hurled explosive death at {len(affected)} foes, savoring the destruction!",
                        balanced_version=f"Threw a grenade, damaging {len(affected)} enemies."
                    )
                game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
        except Exception:
            pass
        
        # Consume turn
        try:
            pass  # turn_count advances once per world tick (GameManager._world_tick)
        except Exception:
            pass
        
        return True
    except Exception as e:
        try: game.ui.messages.add(f"Grenade error: {e}")
        except Exception: pass
        return False


def _show_centered(game, lines, title: str = ""):
    """Try to show a centered dialog in interactive mode; fall back to messages.

    If the UI is headless (getch returns -1) the centered_dialog will return None
    and we then add the same lines to the message buffer so headless runs stay
    non-blocking.
    """
    if not lines:
        return
    try:
        ui = getattr(game, 'ui', None)
        use_popup = getattr(game, 'show_popups', False) and ui is not None and hasattr(ui, 'centered_dialog')
        if use_popup:
            try:
                res = ui.centered_dialog(lines, title=title)
                if res is None:
                    # headless or non-interactive; fall back to messages
                    for ln in lines:
                        try:
                            game.add_message(ln)
                        except Exception:
                            try: ui.messages.add(ln)
                            except Exception: pass
                return
            except Exception:
                # on any UI error fallback to message buffer
                pass
    except Exception:
        pass
    # default message buffer path
    for ln in lines:
        try:
            game.add_message(ln)
        except Exception:
            try: game.ui.messages.add(ln)
            except Exception as e:
                if log:
                    log.exception("Error in _fire_gun: add log entry (fail 3)", exc_info=e)

def handle_input(game, key):
    """Handle player input. Returns True if player took a turn-consuming action, False otherwise."""
    # Build Lightsaber menu (B key) - Enhanced with visual builder
    if key == ord('B'):
        try:
            from jedi_fugitive.items.lightsaber_parts import SaberPart, Lightsaber, BladeType
            inv = getattr(game.player, 'inventory', [])
            crystals = [item for item in inv if isinstance(item, SaberPart) and item.part_type == 'crystal']
            hilts = [item for item in inv if isinstance(item, SaberPart) and item.part_type == 'hilt']
            emitters = [item for item in inv if isinstance(item, SaberPart) and item.part_type == 'emitter']
            if not (crystals and hilts and emitters):
                game.ui.messages.add("You need at least one crystal, hilt, and emitter in your inventory to build a lightsaber.")
                return False
            
            # Select blade type first
            blade_type_items = [
                ("Single Blade", "Standard single-blade configuration. Balanced and precise.", {'bonus': 'Balanced stats'}),
                ("Double-Bladed", "Staff configuration with blades on both ends. Offensive power.", {'bonus': '+5 Attack, -2 Defense'}),
                ("Crossguard", "Blade with lateral vents forming a cross. Enhanced protection.", {'bonus': '+3 Attack, +3 Defense'}),
                ("Dual Wield", "Two separate sabers wielded simultaneously. Superior agility.", {'bonus': '+4 Attack, +2 Evasion'})
            ]
            blade_idx = game.ui.popup_dialogue(blade_type_items, title="SELECT BLADE TYPE", show_details=True)
            if blade_idx is None:
                return False
            blade_type = [BladeType.SINGLE, BladeType.DOUBLE, BladeType.CROSSGUARD, BladeType.DUAL_WIELD][blade_idx]
            
            # Build popup items for crystals
            crystal_items = [(c.name, c.description, {}) for c in crystals]
            c_idx = game.ui.popup_dialogue(crystal_items, title="SELECT KYBER CRYSTAL", show_details=True)
            if c_idx is None:
                return False
            
            # Build popup items for hilts
            hilt_items = [(h.name, h.description, {}) for h in hilts]
            h_idx = game.ui.popup_dialogue(hilt_items, title="SELECT HILT", show_details=True)
            if h_idx is None:
                return False
            
            # Build popup items for emitters
            emitter_items = [(e.name, e.description, {}) for e in emitters]
            e_idx = game.ui.popup_dialogue(emitter_items, title="SELECT EMITTER", show_details=True)
            if e_idx is None:
                return False
            
            # Preview with ASCII diagram
            crystal = crystals[c_idx]
            hilt = hilts[h_idx]
            emitter = emitters[e_idx]
            player_corruption = getattr(game.player, 'corruption', 50)
            saber = Lightsaber(crystal, hilt, emitter, blade_type=blade_type, player_corruption=player_corruption)
            
            # Get blade display and color
            blade_display = saber.get_blade_display()
            blade_color = saber.get_blade_color()
            blade_type_name = {
                BladeType.SINGLE: "Single Blade",
                BladeType.DOUBLE: "Double-Bladed",
                BladeType.CROSSGUARD: "Crossguard",
                BladeType.DUAL_WIELD: "Dual Wield"
            }[blade_type]
            
            # Create visual lightsaber diagram
            diagram = []
            diagram.append("╔═══════════════════════════════════════════════════════════╗")
            diagram.append("║         LIGHTSABER CONSTRUCTION PREVIEW                   ║")
            diagram.append("╚═══════════════════════════════════════════════════════════╝")
            diagram.append("")
            diagram.append("                    ┌─────────────┐")
            diagram.append(f"    EMITTER →       │   {emitter.name[:11]:^11s}   │")
            diagram.append("                    └──────┬──────┘")
            diagram.append("                           │")
            diagram.append(f"                    {blade_display}   ← {blade_color} Blade")
            diagram.append("                           │")
            diagram.append("                    ┌──────┴──────┐")
            diagram.append(f"    CRYSTAL →       │  {crystal.name[:12]:^12s} │   ← Power Source")
            diagram.append("                    └──────┬──────┘")
            diagram.append("                           │")
            diagram.append("                    ┌──────┴──────┐")
            diagram.append(f"    HILT →          │  {hilt.name[:12]:^12s} │   ← Grip & Control")
            diagram.append("                    └─────────────┘")
            diagram.append("")
            diagram.append(f"  Blade Type: {blade_type_name}")
            diagram.append(f"  Blade Color: {blade_color}")
            diagram.append("")
            diagram.append("═══════════════════════════════════════════════════════════")
            diagram.append("                    COMBAT STATISTICS")
            diagram.append("═══════════════════════════════════════════════════════════")
            for k, v in saber.stats.items():
                diagram.append(f"  {k.capitalize():15s} : {v}")
            diagram.append(f"  {'Style':15s} : {saber.style}")
            diagram.append("")
            diagram.append("═══════════════════════════════════════════════════════════")
            diagram.append("")
            diagram.append("Equip this lightsaber?")
            diagram.append("")
            diagram.append("[Yes] Equip and wield this weapon")
            diagram.append("[No]  Return to previous menu")
            
            confirm = game.ui.centered_menu(diagram, title="Lightsaber Assembly")
            if confirm is not None and confirm < len(diagram) - 3:  # Not one of the option lines
                # Assume Yes if they pressed enter on diagram
                game.player.lightsaber = saber
                game.player.equipped_weapon = saber
                game.ui.messages.add("╔═══════════════════════════════════════════════════════╗")
                game.ui.messages.add("║   LIGHTSABER CONSTRUCTION COMPLETE                    ║")
                game.ui.messages.add("╚═══════════════════════════════════════════════════════╝")
                game.ui.messages.add(f"Equipped: {crystal.name} + {hilt.name} + {emitter.name}")
            else:
                game.ui.messages.add("Lightsaber construction cancelled.")
        except Exception as e:
            try: game.ui.messages.add(f"Lightsaber build error: {e}")
            except Exception: pass
        return False  # UI action, no turn consumed
    """Central input handler: movement, actions and ability targeting.
    Safe, defensive and will report internal errors to game UI messages.
    """
    try:
        if key is None or key < 0:
            return False

        if getattr(game, '_confirm_quit', False):
            game._confirm_quit = False
            if key in (ord('q'), ord('y'), ord('Y')):
                try: game.ui.messages.add("Quitting...")
                except Exception: pass
                game.running = False
            else:
                try: game.ui.messages.add("You press on.")
                except Exception: pass
            return

        move_map = {
            # Arrow keys
            curses.KEY_UP: (0, -1), curses.KEY_DOWN: (0, 1),
            curses.KEY_LEFT: (-1, 0), curses.KEY_RIGHT: (1, 0),
            # Vi keys (hjkl)
            ord('k'): (0, -1), ord('j'): (0, 1),
            ord('h'): (-1, 0), ord('l'): (1, 0),
            # Vi diagonal keys (ybu) - using 'u' for up-right since use item moved to different key
            ord('y'): (-1, -1),  # up-left
            ord('u'): (1, -1),   # up-right
            ord('b'): (-1, 1),   # down-left
            ord('n'): (1, 1),    # down-right
            # Numpad-style diagonal keys (7893)
            ord('7'): (-1, -1), ord('9'): (1, -1),
            ord('1'): (-1, 1), ord('3'): (1, 1),
        }

        # Talk to NPC (t key)
        if key == ord('t'):
            try:
                if hasattr(game, 'handle_npc_interactions'):
                    npc = game.handle_npc_interactions()
                    if not npc:
                        game.ui.messages.add("No one nearby to talk to.")
                else:
                    game.ui.messages.add("Interaction system not initialized.")
            except Exception as e:
                game.ui.messages.add(f"Error talking to NPC: {e}")
            return False  # UI action

        # Crafting Menu (C key) - Enhanced with popup dialogue
        if key == ord('C'):
            try:
                if hasattr(game, 'crafting_manager'):
                    # Get available recipes
                    recipes = game.crafting_manager.get_available_recipes()
                    if not recipes:
                        game.ui.messages.add("No recipes available at your level.")
                        return False  # No turn consumed
                    
                    # Build popup items with recipe info
                    popup_items = []
                    for r in recipes:
                        can_craft = game.crafting_manager.can_craft(r)
                        status = "✓ Available" if can_craft else "✗ Missing Materials"
                        name = f"{r.name} (Lv.{r.required_level})"
                        popup_items.append((name, status, {}))
                    
                    # Show recipe selection popup
                    idx = game.ui.popup_dialogue(popup_items, title="CRAFTING STATION", show_details=True)
                    
                    if idx is not None and 0 <= idx < len(recipes):
                        recipe = recipes[idx]
                        
                        # Build materials list
                        mat_lines = []
                        mat_lines.append(f"Craft: {recipe.name}")
                        mat_lines.append("")
                        mat_lines.append(recipe.description)
                        mat_lines.append("")
                        mat_lines.append("Required Materials:")
                        
                        # Check inventory for each material
                        can_craft = game.crafting_manager.can_craft(recipe)
                        for mat, qty in recipe.materials.items():
                            mat_lines.append(f"  • {mat}: {qty}")
                        
                        mat_lines.append("")
                        if can_craft:
                            mat_lines.append("You have all required materials!")
                        else:
                            mat_lines.append("Missing some materials...")
                        
                        # Show confirmation
                        confirm = game.ui.centered_menu(mat_lines + ["", "Craft Item", "Cancel"], title="Recipe Details")
                        if confirm == len(mat_lines) + 1:  # "Craft Item" index
                            game.crafting_manager.craft(recipe)
                else:
                    game.ui.messages.add("Crafting system not initialized.")
            except Exception as e:
                game.ui.messages.add(f"Error opening crafting: {e}")
            return False  # Crafting menu browsing doesn't consume turn (actual crafting does)

        # Reticle / pending ability handling (Force abilities, grenade throwing, OR gun shooting)
        if getattr(game, "pending_force_ability", None) is not None or getattr(game, "pending_grenade_throw", False) or getattr(game, "pending_gun_shot", False):
            # cancel
            if key in (27, ord('c')):
                game.pending_force_ability = None
                game.pending_grenade_throw = False
                game.pending_gun_shot = False
                try: game.ui.messages.add("Action cancelled.") 
                except Exception: pass
                return False  # Cancelling doesn't consume a turn
            # confirm
            if key in (10, 13, ord(' ')):
                tx = getattr(game, "target_x", getattr(game.player, "x", 0))
                ty = getattr(game, "target_y", getattr(game.player, "y", 0))
                
                # Check if it's a gun shot
                if getattr(game, "pending_gun_shot", False):
                    try:
                        _fire_gun(game, tx, ty)
                    except Exception as e:
                        try: game.ui.messages.add(f"Shot failed: {e}") 
                        except Exception: pass
                    finally:
                        game.pending_gun_shot = False
                # Check if it's a grenade throw
                elif getattr(game, "pending_grenade_throw", False):
                    try:
                        _throw_grenade(game, tx, ty)
                    except Exception as e:
                        try: game.ui.messages.add(f"Grenade throw failed: {e}") 
                        except Exception: pass
                    finally:
                        game.pending_grenade_throw = False
                # Otherwise it's a Force ability
                elif getattr(game, "pending_force_ability", None) is not None:
                    try:
                        from jedi_fugitive.game.abilities import use_force_ability
                        use_force_ability(game, game.pending_force_ability, tx, ty)
                    except Exception:
                        try: game.ui.messages.add("Force use failed.") 
                        except Exception: pass
                    finally:
                        game.pending_force_ability = None
                return True  # Ability use consumes a turn
            # move reticle
            if key in move_map:
                dx, dy = move_map[key]
                max_y = len(game.game_map); max_x = len(game.game_map[0]) if max_y else 0
                nx = max(0, min(getattr(game, "target_x", getattr(game.player, "x", 0)) + dx, max_x - 1 if max_x else 0))
                ny = max(0, min(getattr(game, "target_y", getattr(game.player, "y", 0)) + dy, max_y - 1 if max_y else 0))
                
                # Limit grenade throw to 3 tiles range
                if getattr(game, "pending_grenade_throw", False):
                    px = getattr(game.player, "x", 0)
                    py = getattr(game.player, "y", 0)
                    dist = abs(nx - px) + abs(ny - py)  # Manhattan distance
                    if dist <= 3:
                        game.target_x, game.target_y = nx, ny
                # Limit gun shots to weapon range
                elif getattr(game, "pending_gun_shot", False):
                    px = getattr(game.player, "x", 0)
                    py = getattr(game.player, "y", 0)
                    weapon_range = getattr(game, "gun_range", 5)
                    dist = abs(nx - px) + abs(ny - py)
                    if dist <= weapon_range:
                        game.target_x, game.target_y = nx, ny
                else:
                    game.target_x, game.target_y = nx, ny
                return

        # Narrative choice handling
        if hasattr(game, 'pending_narrative_choice') and game.pending_narrative_choice is not None:
            if key in (ord('1'), ord('2'), ord('3')):
                choice_num = int(chr(key))
                event_data, choice_mapping, event_type = game.pending_narrative_choice
                
                if choice_num in choice_mapping:
                    try:
                        from jedi_fugitive.game import narrative_events
                        
                        choice_key = choice_mapping[choice_num]
                        outcome, corruption, reward = narrative_events.process_narrative_choice(
                            event_data, choice_key, game.player, game
                        )
                        
                        # Display outcome
                        game.ui.messages.add("─" * 60)
                        game.ui.messages.add(outcome)
                        
                        # Apply corruption change
                        if corruption != 0:
                            old_corruption = game.player.corruption
                            game.player.corruption = max(0, min(100, game.player.corruption + corruption))
                            if corruption > 0:
                                game.ui.messages.add(f"[Dark Side influence: +{corruption}]")
                            else:
                                game.ui.messages.add(f"[Light Side influence: {corruption}]")
                        
                        # Apply reward with actual effects
                        if reward:
                            try:
                                from jedi_fugitive.game.reward_system import apply_narrative_reward
                                reward_message = apply_narrative_reward(game, reward)
                                game.ui.messages.add(f"[Reward: {reward_message}]")
                            except Exception as e:
                                game.ui.messages.add(f"[Reward Error: {e}]")
                        
                        game.ui.messages.add("─" * 60)
                        
                        # Clear pending choice
                        game.pending_narrative_choice = None
                        
                    except Exception as e:
                        game.ui.messages.add(f"Choice processing failed: {e}")
                        game.pending_narrative_choice = None
                else:
                    game.ui.messages.add(f"Invalid choice. Press 1, 2, or 3.")
                return
            elif key == 27:  # ESC to cancel
                game.ui.messages.add("You hesitate and the moment passes...")
                game.pending_narrative_choice = None
                if hasattr(game, '_choices_shown'):
                    delattr(game, '_choices_shown')
                return

        # Fauna interaction handling
        if (hasattr(game, 'fauna_manager') and hasattr(game.fauna_manager, 'active_encounters') 
            and game.fauna_manager.active_encounters):
            # Numbered key handling for fauna is now done in popup menus
            pass
            # ESC handling for fauna is now done in popup menus
            pass

        # Global keys
        if key in (ord('q'), 27):
            # ask first: a stray ESC used to end the run instantly
            game._confirm_quit = True
            try: game.ui.messages.add("Abandon your journey? Press q again (or y) to quit, any other key to continue.")
            except Exception: pass
            return

        # Quest response handling
        if hasattr(game, 'active_conversations') and game.active_conversations:
            # Check if any conversation is waiting for input
            for pos, conversation in list(game.active_conversations.items()):
                if conversation.get('type') == 'quest_offer':
                    if game.handle_npc_response(key, pos[0], pos[1]):
                        return  # Input was handled

        # Manual save
        if key == ord('S'):  # Capital S to avoid accidents
            try:
                from jedi_fugitive.game.save_system import save_game
                if save_game(game, is_autosave=False):
                    try: game.ui.messages.add("Game saved successfully!")
                    except Exception: pass
                else:
                    try: game.ui.messages.add("Failed to save game.")
                    except Exception: pass
            except Exception as e:
                try: game.ui.messages.add(f"Save error: {e}")
                except Exception: pass
            return False  # No turn consumed

        if key == ord('P'):
            try:
                if hasattr(game, "reveal_map"):
                    game.reveal_map(100)
                try: game.ui.messages.add("Map revealed (debug).")
                except Exception: pass
            except Exception as e:
                if log:
                    log.exception("Error in _fire_gun: add log entry (fail 4)", exc_info=e)
                try: game.ui.messages.add("Reveal failed.") 
                except Exception: pass
            return False  # No turn consumed

        if key == ord('r') or key == ord('R'):
            try:
                _open_ritual_menu(game)
            except Exception as e:
                try: 
                    game.ui.messages.add(f"Ritual menu error: {e}")
                except Exception: 
                    pass
            return False  # No turn consumed

        if key == ord('p'):
            game.show_popups = not getattr(game, "show_popups", False)
            try: game.ui.messages.add(f"Popups {'on' if game.show_popups else 'off'}.")
            except Exception: pass
            return False  # No turn consumed

        if key == ord('v'):
            game.show_codex = not getattr(game, "show_codex", False)
            try:
                if game.show_codex:
                    game.ui.messages.add("Sith Codex opened. Press 'v' again to close.")
                else:
                    game.ui.messages.add("Sith Codex closed.")
            except Exception: pass
            return False  # No turn consumed
        
        # Form/Stance switching (X key) - Migrated to popup
        if key == ord('X'):
            try:
                from jedi_fugitive.game.lightsaber_forms import FORMS_BY_NAME
                known_forms = getattr(game.player, 'known_forms', ["Shii-Cho"])
                active_form = getattr(game.player, 'active_form', "Shii-Cho")
                
                if len(known_forms) <= 1:
                    game.ui.messages.add("You only know one form. Learn more forms by leveling up!")
                else:
                    # Build popup items with form details
                    form_items = []
                    for name in known_forms:
                        form_obj = FORMS_BY_NAME.get(name)
                        if form_obj:
                            status = "[ACTIVE]" if name == active_form else form_obj.focus
                            form_items.append((f"Form {form_obj.number}: {name}", status, {}))
                        else:
                            status = "[ACTIVE]" if name == active_form else ""
                            form_items.append((name, status, {}))
                    
                    choice = game.ui.popup_dialogue(form_items, title="LIGHTSABER FORMS", show_details=True)
                    if choice is not None and 0 <= choice < len(known_forms):
                        new_form = known_forms[choice]
                        game.player.active_form = new_form
                        form_obj = FORMS_BY_NAME.get(new_form)
                        if form_obj:
                            game.ui.messages.add(f"═══ FORM {form_obj.number}: {form_obj.name.upper()} ═══")
                            game.ui.messages.add(f"Stance changed to {new_form} - {form_obj.focus}")
                        else:
                            game.ui.messages.add(f"Stance changed to {new_form}")
            except Exception as e:
                try:
                    game.ui.messages.add(f"Form switching error: {e}")
                except:
                    pass
            return False  # No turn consumed

        # Throw grenade (using 'G' key)
        if key == ord('G'):
            try:
                # Check if player has grenades
                inv = getattr(game.player, 'inventory', [])
                has_grenade = any(isinstance(item, dict) and item.get('id') in ['grenade', 'thermal_grenade'] for item in inv)
                
                if not has_grenade:
                    try: game.ui.messages.add("No grenades in inventory!")
                    except Exception: pass
                    return
                    
                # Enter grenade targeting mode
                game.pending_grenade_throw = True
                game.target_x = getattr(game.player, 'x', 0)
                game.target_y = getattr(game.player, 'y', 0)
                try: game.ui.messages.add("Select grenade target (Arrow keys/WASD to aim, Space to throw, ESC to cancel)")
                except Exception: pass
            except Exception as e:
                try: game.ui.messages.add(f"Grenade throw failed: {e}")
                except Exception: pass
            return False  # No turn consumed
            
        # Toggle map display using 'M' key
        if key == ord('M'):
            try:
                # Toggle map visibility
                current_visible = getattr(game, 'map_visible', True)
                game.map_visible = not current_visible
                status = "visible" if game.map_visible else "hidden"
                try: game.ui.messages.add(f"Map display: {status}")
                except Exception: pass
            except Exception as e:
                try: game.ui.messages.add(f"Map toggle failed: {e}")
                except Exception: pass
            return False  # No turn consumed
            
        # Hide/Stealth (Z key) - NEW SYSTEM
        if key == ord('Z'):
            try:
                if hasattr(game, 'stealth_system'):
                    success, message = game.stealth_system.attempt_hide(game.player, game)
                    game.ui.messages.add(message)
                    if success:
                        # Update stealth state notification
                        game.stealth_system.update_stealth(game.player, game, action_type="idle")
                    return True  # Hiding consumes a turn
                else:
                    game.ui.messages.add("Stealth system not initialized.")
            except Exception as e:
                game.ui.messages.add(f"Hide failed: {e}")
            return False
        
        # Equip Disguise (Shift+D key) - NEW SYSTEM
        if key == ord('D'):
            try:
                from jedi_fugitive.items.disguises import DISGUISE_TYPES
                inv = getattr(game.player, 'inventory', [])
                disguises = [item for item in inv if hasattr(item, '__class__') and item.__class__.__name__ == 'Disguise']
                
                if not disguises:
                    game.ui.messages.add("No disguises in inventory.")
                    return False
                
                # Build disguise selection menu
                disguise_items = []
                for d in disguises:
                    desc = f"{d.description} | Detection: +{d.detection_bonus}"
                    disguise_items.append((d.name, desc, {}))
                
                # Show selection popup
                idx = game.ui.popup_dialogue(disguise_items, title="EQUIP DISGUISE", show_details=True)
                
                if idx is not None and 0 <= idx < len(disguises):
                    selected = disguises[idx]
                    # Equip disguise
                    game.player.equip_disguise(selected)
                    game.ui.messages.add(f"Equipped disguise: {selected.name}")
                    game.ui.messages.add(f"Faction access: {', '.join(selected.allowed_factions)}")
            except Exception as e:
                game.ui.messages.add(f"Disguise equip failed: {e}")
            return False  # No turn consumed
        
        # Show controls menu using 'H' key (Help)
        if key == ord('H'):
            _show_controls_popup(game)
            return False  # No turn consumed
            
        # Show token legend using 'L' key (Legend)
        if key == ord('L'):
            _show_token_legend(game)
            return False  # No turn consumed
        
        # Character Sheet - '@' key (NEW)
        if key == ord('@'):
            try:
                from jedi_fugitive.game.character_sheet import show_character_sheet
                show_character_sheet(game)
            except Exception as e:
                try:
                    game.ui.messages.add(f"Character sheet failed: {e}")
                except:
                    pass
            return False  # No turn consumed
        
        # Compass/Scan - 'c' key (NEW)
        if key == ord('c'):
            try:
                from jedi_fugitive.game.compass import show_compass_scan
                show_compass_scan(game)
            except Exception as e:
                try:
                    game.ui.messages.add(f"Compass scan failed: {e}")
                except:
                    pass
            return False  # No turn consumed
            
        # Help screen
        if key == ord('?'):
            try:
                help_lines = [
                    "╔═══════════════════════════════════════════════════════════╗",
                    "║              J E D I   F U G I T I V E                    ║",
                    "║                     CONTROLS & HELP                       ║",
                    "╚═══════════════════════════════════════════════════════════╝",
                    "",
                    "MOVEMENT:",
                    "  Arrow Keys = Standard directional (↑↓←→)",
                    "  hjkl       = Vi-style cardinal movement",
                    "  yubn       = Vi-style diagonal (y=↖ u=↗ b=↙ n=↘)",
                    "  Numpad 1379 = Numpad diagonal (7=↖ 9=↗ 1=↙ 3=↘)",
                    "",
                    "INVENTORY & ITEMS:",
                    "  g = Pick up item at your location",
                    "  e = Equip weapon or armor from inventory",
                    "  u = Use/consume item (stimpack, artifact, etc.)",
                    "  d = Drop item from inventory",
                    "  q = Unequip weapon",
                    "  o = Unequip armor/offhand",
                    "  x = Inspect tile (examine objects/enemies)",
                    "",
                    "COMBAT:",
                    "  Walk into enemy = Attack in melee",
                    "  f = Fire ranged weapon (auto-aim to nearest enemy)",
                    "  G = Throw grenade (targeting, 3-tile range)",
                    "  F = Fire ranged weapon (manual targeting)",
                    "",
                    "FORCE ABILITIES:",
                    "  z = Open Force powers menu (Force Push, Lightning, etc.)",
                    "  r/R = Open Rituals menu (meditation, crystal attunement, ceremonies)",
                    "",
                    "INFORMATION:",
                    "  J = Journal/Travel Log (view your story)",
                    "  i = Inventory (view/manage items)",
                    "  v = Sith Codex (toggle lore & discoveries)",
                    "",
                    "CRAFTING & TRADING:",
                    "  C = Crafting Bench (upgrade weapons, craft items)",
                    "  H = Controls menu (this help)",
                    "  T = Trade with merchant (must be near merchant camp)",
                    "  Shields and offhand weapons available!",
                    "  Dual-wield: Equip 1H weapon + 1H weapon",
                    "  Tank: Equip 1H weapon + Shield",
                    "",
                    "LANDMARKS & POINTS OF INTEREST:",
                    "  When you find ruins, relics, or power sources:",
                    "    A = ABSORB → Dark Side (+corruption, gain power)",
                    "    D = DESTROY → Light Side (-corruption, gain XP)",
                    "",
                    "ARTIFACTS (Critical Choice!):",
                    "  When using artifacts from inventory (press 'u'):",
                    "    'a' = ABSORB → Dark Side path (+corruption, dark powers)",
                    "    'd' = DESTROY → Light Side path (-corruption, light powers)",
                    "",
                    "ALIGNMENT:",
                    "  Your choices shape who you become:",
                    "    0-35% corruption   = Light Side Jedi",
                    "    36-65% corruption  = Balanced Force User",
                    "    66-100% corruption = Dark Side Sith",
                    "",
                    "ENCOUNTERS & EXPLORATION:",
                    "  ? markers = Random encounters (walk to marker to trigger)",
                    "  Encounters spawn every 200-300 turns with rewards",
                    "  Animal encounters = Press numbers (1-5) to interact when prompted",
                    "",
                    "FAUNA SYMBOLS ON MAP:",
                    "  · = Tiny creatures (insects, small birds)",
                    "  o = Small creatures (rodents, reptiles)",  
                    "  Ω = Medium creatures (human-sized)",
                    "  ♦ = Large creatures (horse-sized)",
                    "  █ = Massive creatures (rancor-sized)",
                    "  Colors: Cyan=Force-sensitive, Green=Passive, Yellow=Neutral,", 
                    "          Red=Aggressive, Purple=Corrupted by dark side",
                    "",
                    "OTHER:",
                    "  ? = Show this help screen",
                    "  m = Meditate (reduce stress if safe)",
                    "  p = Toggle popup messages",
                    "  S = Save game (manual save)",
                    "  P = Reveal map (debug/cheat)",
                    "  q / ESC = Quit game (asks for confirmation)",
                    "",
                    "Press any key to close..."
                ]
                _show_centered(game, help_lines, title="Help")
            except Exception:
                try: game.ui.messages.add("Help display failed.")
                except Exception: pass
            return False  # No turn consumed

        # Fire weapon (uppercase F) — use targeting mode
        if key == ord('F'):
            try:
                # Check if player has ranged weapon equipped
                weapon = getattr(game.player, 'equipped_weapon', None)
                is_ranged = False
                weapon_range = 5
                weapon_name = ''
                
                if weapon:
                    # Check if it's a ranged weapon by type or range
                    if isinstance(weapon, dict):
                        weapon_name = weapon.get('name', '').lower()
                        weapon_range = weapon.get('range', 5)
                        # Dict weapons with range > 1 are ranged
                        is_ranged = weapon_range > 1
                    elif hasattr(weapon, 'name'):
                        weapon_name = weapon.name.lower()
                        weapon_range = getattr(weapon, 'range', 1)
                        # Check by weapon_type or range attribute
                        if hasattr(weapon, 'weapon_type'):
                            from jedi_fugitive.items.weapons import WeaponType
                            wtype = weapon.weapon_type
                            is_ranged = wtype in [WeaponType.BLASTER_PISTOL, WeaponType.BLASTER_RIFLE, 
                                                 WeaponType.HEAVY_BLASTER, WeaponType.WOOKIE_BOWCASTER, 
                                                 WeaponType.RANGED]
                        else:
                            # Fallback: any weapon with range > 1 is ranged
                            is_ranged = weapon_range > 1
                
                if not is_ranged:
                    try: game.ui.messages.add('No ranged weapon equipped!')
                    except Exception: pass
                    return
                
                # Enter targeting mode for gun
                game.pending_gun_shot = True
                game.gun_range = weapon_range
                game.target_x = getattr(game.player, "x", 0)
                game.target_y = getattr(game.player, "y", 0)
                try: game.ui.messages.add(f"Fire Weapon ({weapon_range}-tile range) — move reticle and press Enter, Esc to cancel.")
                except Exception: pass
            except Exception:
                try: game.ui.messages.add('Fire command failed.')
                except Exception: pass
            return False  # No turn consumed

        if key == ord('i'):
            try:
                equipment.inventory_chooser(game)
            except Exception:
                try: game.ui.messages.add("Inventory view failed.") 
                except Exception: pass
            return False  # No turn consumed

        # Inspect / examine (what's in a tile or nearby) - ENHANCED to scan 5x5 area
        if key == ord('x'):
            try:
                # NEW: Scan 5x5 tiles around player (25 tiles total)
                px = getattr(game.player, 'x', 0)
                py = getattr(game.player, 'y', 0)
                
                inspect_lines = []
                inspect_lines.append("═══ INSPECT: AREA SCAN ═══")
                inspect_lines.append(f"Scanning 5x5 area around position ({px}, {py})")
                inspect_lines.append("")
                
                found_something = False
                
                # Scan 5x5 grid centered on player (radius 2)
                for dy in [-2, -1, 0, 1, 2]:
                    for dx in [-2, -1, 0, 1, 2]:
                        scan_x = px + dx
                        scan_y = py + dy
                        
                        # Skip out of bounds
                        if not (0 <= scan_y < len(game.game_map) and 0 <= scan_x < len(game.game_map[0])):
                            continue
                        
                        # Check for enemy at this position
                        for enemy in getattr(game, 'enemies', []):
                            if not getattr(enemy, 'is_alive', lambda: True)():
                                continue
                            if getattr(enemy, 'x', -999) == scan_x and getattr(enemy, 'y', -999) == scan_y:
                                found_something = True
                                enemy_name = getattr(enemy, 'name', 'Enemy')
                                enemy_hp = getattr(enemy, 'hp', '?')
                                enemy_max_hp = getattr(enemy, 'max_hp', '?')
                                enemy_level = getattr(enemy, 'level', '?')
                                
                                direction = ""
                                if dx < 0:
                                    direction += "W"
                                elif dx > 0:
                                    direction += "E"
                                if dy < 0:
                                    direction += "N"
                                elif dy > 0:
                                    direction += "S"
                                if not direction:
                                    direction = "CENTER"
                                
                                inspect_lines.append(f"⚔ [{direction}] {enemy_name} (Lv.{enemy_level})")
                                inspect_lines.append(f"   HP: {enemy_hp}/{enemy_max_hp} | ATK: {getattr(enemy, 'attack', '?')} | DEF: {getattr(enemy, 'defense', '?')}")
                        
                        # Check for item at this position
                        for item in getattr(game, 'items_on_map', []):
                            if item.get('x') == scan_x and item.get('y') == scan_y:
                                found_something = True
                                item_name = item.get('name', item.get('token', 'Item'))
                                
                                direction = ""
                                if dx < 0:
                                    direction += "W"
                                elif dx > 0:
                                    direction += "E"
                                if dy < 0:
                                    direction += "N"
                                elif dy > 0:
                                    direction += "S"
                                if not direction:
                                    direction = "CENTER"
                                
                                # Get lore if available
                                try:
                                    tok = item.get('token')
                                    player_corruption = getattr(game.player, 'dark_corruption', 50)
                                    lore_data = inspection.get_item_inspection(tok, item_name, player_corruption)
                                    inspect_lines.append(f"📦 [{direction}] {item_name}")
                                    inspect_lines.append(f"   {lore_data.get('description', 'An item.')}")
                                except:
                                    inspect_lines.append(f"📦 [{direction}] {item_name}")
                        
                        # Check for NPC at this position
                        npcs_on_map = getattr(game, 'npcs_on_map', {})
                        if (scan_x, scan_y) in npcs_on_map:
                            found_something = True
                            npc = npcs_on_map[(scan_x, scan_y)]
                            npc_name = getattr(npc, 'name', 'Survivor')
                            
                            direction = ""
                            if dx < 0:
                                direction += "W"
                            elif dx > 0:
                                direction += "E"
                            if dy < 0:
                                direction += "N"
                            elif dy > 0:
                                direction += "S"
                            if not direction:
                                direction = "CENTER"
                            
                            inspect_lines.append(f"👤 [{direction}] {npc_name}")
                            inspect_lines.append(f"   Press 't' to talk")
                
                # Always provide atmospheric description of current location
                if not found_something:
                    inspect_lines.append("No enemies or items detected in vicinity.")
                
                inspect_lines.append("")
                inspect_lines.append("═══ ATMOSPHERE ═══")
                try:
                    tile_char = game.game_map[py][px]
                    biome = None
                    if hasattr(game, 'map_biomes') and game.map_biomes:
                        try:
                            biome = game.map_biomes[py][px]
                        except:
                            pass
                    
                    in_tomb = hasattr(game, 'tomb_levels') and game.tomb_levels is not None
                    
                    tile_desc = inspection.get_tile_description(tile_char, biome, in_tomb)
                    if tile_desc:
                        inspect_lines.append(f"📍 {tile_desc['description']}")
                        inspect_lines.append(f"   {tile_desc['lore']}")
                    else:
                        inspect_lines.append("The air feels heavy with ancient dread.")
                        inspect_lines.append("Shadows cling to every surface, reluctant to release their grip.")
                except Exception:
                    inspect_lines.append("An oppressive atmosphere weighs upon you.")
                    inspect_lines.append("The Force whispers warnings you cannot understand.")
                
                _show_centered(game, inspect_lines, title="Inspect")
                return
                
                # OLD CODE PRESERVED BELOW (not reached)
                # determine target coords: prefer pending reticle, then UI cursor, else nearby scan
                tx = None; ty = None
                if getattr(game, 'pending_force_ability', None) is not None and hasattr(game, 'target_x'):
                    tx = getattr(game, 'target_x', None); ty = getattr(game, 'target_y', None)
                elif hasattr(game.ui, 'cursor') and getattr(game.ui.cursor, 'visible', False):
                    tx = getattr(game.ui.cursor, 'x', None); ty = getattr(game.ui.cursor, 'y', None)
                # fallback: inspect adjacent tiles and report nearby foes
                nearby = []
                if tx is None or ty is None:
                    # attempt to inspect the tile the player is facing first
                    try:
                        fdx, fdy = getattr(game.player, 'facing', (1, 0))
                        px = getattr(game.player, 'x', 0); py = getattr(game.player, 'y', 0)
                        fx = px + int(fdx); fy = py + int(fdy)
                        # ensure in bounds
                        mh = len(game.game_map); mw = len(game.game_map[0]) if mh else 0
                        if 0 <= fx < mw and 0 <= fy < mh:
                            # check enemy at facing tile
                            for e in getattr(game, 'enemies', []) or []:
                                try:
                                    if getattr(e, 'x', None) == fx and getattr(e, 'y', None) == fy and getattr(e, 'is_alive', lambda: True)():
                                        # reuse the existing inspect-on-tile flow by setting tx/ty
                                        tx, ty = fx, fy
                                        break
                                except Exception:
                                    continue
                            # if we found an item at facing tile and no enemy, set tx/ty
                            if tx is None and ty is None:
                                found = None
                                for it in getattr(game, 'items_on_map', []) or []:
                                    try:
                                        if it.get('x') == fx and it.get('y') == fy:
                                            found = it
                                            break
                                    except Exception:
                                        continue
                                if found is not None:
                                    # directly report item at facing tile
                                    try:
                                        desc = found.get('name') or found.get('token') or str(found)
                                        # try to resolve via ITEM_DEFS first, then TOKEN_MAP fallback
                                        try:
                                            from jedi_fugitive.items.consumables import ITEM_DEFS
                                            tok = found.get('token') or (found.get('item') and found.get('item').get('token'))
                                            if tok:
                                                for d in ITEM_DEFS:
                                                    if d.get('token') == tok or d.get('id') == tok:
                                                        desc = d.get('name') + ' - ' + d.get('description', '')
                                                        break
                                        except Exception:
                                            pass
                                        try:
                                            from jedi_fugitive.items.tokens import TOKEN_MAP as _tmap
                                            tok = found.get('token') or (found.get('item') and found.get('item').get('token'))
                                            if tok and tok in _tmap:
                                                tinfo = _tmap.get(tok, {})
                                                desc = (tinfo.get('name') or tok) + ' - ' + (tinfo.get('description') or '')
                                        except Exception:
                                            pass
                                        _show_centered(game, [f"Item ahead: {desc} @ {fx},{fy}"], title="Inspect")
                                        return
                                    except Exception:
                                        try: game.ui.messages.add("Inspect failed on item.")
                                        except Exception: pass
                                        return
                            # if tx/ty set to facing tile, fall through to detailed tile inspect
                            if tx is not None and ty is not None:
                                pass
                            else:
                                # First: scan a configurable radius around the player for any
                                # registered landmarks that include 'lore'. If found, surface
                                # their lore (centered dialog when interactive, otherwise
                                # message buffer). This ensures the Inspect key checks "all
                                # around" the player for story content rather than only
                                # facing/enemy tiles.
                                try:
                                    inspect_radius = int(getattr(game, 'inspect_radius', 3) or 3)
                                except Exception:
                                    inspect_radius = 3
                                px = getattr(game.player, 'x', 0); py = getattr(game.player, 'y', 0)
                                lm_map = getattr(game, 'map_landmarks', {}) or {}
                                found_lore_blocks = []
                                found_keys = []
                                try:
                                    for (lx, ly), info in list(lm_map.items()):
                                        try:
                                            if abs(lx - px) + abs(ly - py) <= inspect_radius:
                                                if info and isinstance(info, dict) and info.get('lore'):
                                                    title = info.get('name', 'Point of Interest')
                                                    art = info.get('art') or []
                                                    lore = info.get('lore') or []
                                                    desc = info.get('description', '')
                                                    block = []
                                                    if art:
                                                        block.extend(art)
                                                        block.append('')
                                                    if lore:
                                                        block.append(f"-- {title} --")
                                                        for ln in lore:
                                                            block.append(ln)
                                                        block.append('')
                                                    if desc:
                                                        block.append(desc)
                                                    if block:
                                                        found_lore_blocks.append(block)
                                                        found_keys.append((lx, ly))
                                        except Exception:
                                            continue
                                except Exception:
                                    found_lore_blocks = []

                                # If we found any lore, present them together and mark as consumed.
                                if found_lore_blocks:
                                    out_lines = []
                                    for i, blk in enumerate(found_lore_blocks):
                                        if i > 0:
                                            out_lines.append('')
                                        out_lines.extend(blk)
                                    try:
                                        _show_centered(game, out_lines, title="Nearby Lore")
                                    except Exception:
                                        for ln in out_lines:
                                            try: game.add_message(ln)
                                            except Exception:
                                                try: game.ui.messages.add(ln)
                                                except Exception: pass
                                        # Additionally: for each landmark we inspected, compute and append
                                        # a directional hint to the nearest tomb (if any). This gives
                                        # contextual guidance without being obtrusive.
                                        try:
                                            for k in found_keys:
                                                try:
                                                    info = getattr(game, 'find_nearest_tomb_info', None)
                                                    if callable(info):
                                                        res = game.find_nearest_tomb_info(k[0], k[1])
                                                        if res:
                                                            tx, ty, dist, dstr = res
                                                            hint = f"Hint: the ruins suggest a tomb lies ~{dist} tiles to the {dstr}."
                                                            try: game.add_message(hint)
                                                            except Exception: pass
                                                except Exception:
                                                    continue
                                        except Exception:
                                            pass
                                    # mark lore consumed so it doesn't repeatedly trigger
                                    try:
                                        for k in found_keys:
                                            try:
                                                info = lm_map.get(k, {}) or {}
                                                if 'lore' in info:
                                                    del info['lore']
                                                    lm_map[k] = info
                                            except Exception:
                                                continue
                                        try:
                                            setattr(game, 'map_landmarks', lm_map)
                                        except Exception:
                                            pass
                                    except Exception:
                                        pass
                                    return

                                # collect nearby enemies within 2 tiles as before
                                px = getattr(game.player, 'x', 0); py = getattr(game.player, 'y', 0)
                                nearby = []
                                # continue to existing nearby scan below
                        else:
                            px = getattr(game.player, 'x', 0); py = getattr(game.player, 'y', 0)
                            nearby = []
                    except Exception:
                        px = getattr(game.player, 'x', 0); py = getattr(game.player, 'y', 0)
                        nearby = []
                    for e in getattr(game, 'enemies', []) or []:
                        try:
                            if not getattr(e, 'is_alive', lambda: True)():
                                continue
                            ex = int(getattr(e, 'x', -999)); ey = int(getattr(e, 'y', -999))
                            dist = abs(ex - px) + abs(ey - py)
                            if dist <= 2:
                                nearby.append((dist, e))
                        except Exception:
                            continue
                    if nearby:
                        nearby.sort(key=lambda t: t[0])
                        lines = []
                        for d, e in nearby:
                            try:
                                name = getattr(e, 'name', str(e))
                                hp = getattr(e, 'hp', None); mhp = getattr(e, 'max_hp', None)
                                lvl = getattr(e, 'level', None)
                                parts = [f"{name} (dist {d})"]
                                if hp is not None:
                                    parts.append(f"HP: {hp}{('/'+str(mhp)) if mhp else ''}")
                                if lvl is not None:
                                    parts.append(f"Lvl: {lvl}")
                                lines.append(" | ".join(parts))
                            except Exception:
                                continue
                        _show_centered(game, lines, title="Nearby")
                        return
                    # nothing nearby
                    _show_centered(game, ["Nothing of interest nearby."], title="Inspect")
                    return

                # If we have coordinates, inspect that tile
                try:
                    if tx is None or ty is None:
                        try: game.add_message("Inspect target unknown."); return
                        except Exception: return
                    # check for an enemy at that tile
                    enemy = None
                    for e in getattr(game, 'enemies', []) or []:
                        try:
                            if getattr(e, 'x', None) == tx and getattr(e, 'y', None) == ty and getattr(e, 'is_alive', lambda: True)():
                                enemy = e; break
                        except Exception:
                            continue
                    if enemy:
                        try:
                            # Get detailed inspection with lore
                            enemy_name = getattr(enemy, 'name', 'Enemy')
                            player_corruption = getattr(game.player, 'dark_corruption', 50)
                            
                            # Get lore data
                            lore_data = inspection.get_enemy_inspection(enemy_name, player_corruption)
                            
                            # Build display lines with both stats and lore
                            lines = []
                            lines.append(f"═══ {lore_data['title']} ═══")
                            lines.append(f"Location: ({tx}, {ty})")
                            lines.append("")
                            
                            # Stats
                            stats = []
                            if hasattr(enemy, 'hp') and hasattr(enemy, 'max_hp'):
                                stats.append(f"HP: {enemy.hp}/{enemy.max_hp}")
                            elif hasattr(enemy, 'hp'):
                                stats.append(f"HP: {enemy.hp}")
                            if hasattr(enemy, 'level'):
                                stats.append(f"Level: {getattr(enemy,'level')}")
                            if hasattr(enemy, 'attack'):
                                stats.append(f"Attack: {getattr(enemy,'attack')}")
                            if hasattr(enemy, 'defense'):
                                stats.append(f"Defense: {getattr(enemy,'defense')}")
                            
                            if stats:
                                lines.append(" | ".join(stats))
                                lines.append("")
                            
                            # Abilities
                            fas = getattr(enemy, 'force_abilities', None)
                            if fas:
                                try:
                                    names = [getattr(a,'name',str(a)) for a in (fas.values() if hasattr(fas,'values') else fas)]
                                    lines.append(f"Force Abilities: {', '.join(names)}")
                                    lines.append("")
                                except Exception:
                                    pass
                            
                            # Lore content
                            lines.append(lore_data['description'])
                            lines.append("")
                            lines.append(f"Lore: {lore_data['lore']}")
                            lines.append("")
                            lines.append(f"Tactics: {lore_data['tactics']}")
                            
                            # Personal note based on corruption
                            if lore_data.get('personal_note'):
                                lines.append("")
                                lines.append(f"[{lore_data['personal_note']}]")
                            
                            _show_centered(game, lines, title=enemy_name)
                        except Exception:
                            try: game.ui.messages.add("Inspect failed on enemy.")
                            except Exception: pass
                        return
                    # else, check items_on_map
                    itm = None
                    for it in getattr(game, 'items_on_map', []) or []:
                        try:
                            if it.get('x') == tx and it.get('y') == ty:
                                itm = it; break
                        except Exception:
                            continue
                    if itm:
                        try:
                            # Get item name and token
                            item_name = itm.get('name')
                            tok = itm.get('token') or (itm.get('item') and itm.get('item').get('token'))
                            
                            # Try to get name from ITEM_DEFS or TOKEN_MAP if not present
                            basic_desc = ""
                            try:
                                from jedi_fugitive.items.consumables import ITEM_DEFS
                                if tok:
                                    for d in ITEM_DEFS:
                                        if d.get('token') == tok or d.get('id') == tok:
                                            if not item_name:
                                                item_name = d.get('name')
                                            basic_desc = d.get('description', '')
                                            break
                            except Exception:
                                pass
                            
                            # TOKEN_MAP fallback
                            try:
                                from jedi_fugitive.items.tokens import TOKEN_MAP as _tmap
                                if tok and tok in _tmap:
                                    tinfo = _tmap.get(tok, {})
                                    if not item_name:
                                        item_name = tinfo.get('name') or tok
                                    if not basic_desc:
                                        basic_desc = tinfo.get('description', '')
                            except Exception:
                                pass
                            
                            # Get detailed inspection with lore
                            player_corruption = getattr(game.player, 'dark_corruption', 50)
                            lore_data = inspection.get_item_inspection(tok, item_name, player_corruption)
                            
                            # Build display lines
                            lines = []
                            lines.append(f"═══ {lore_data['name']} ═══")
                            lines.append(f"Location: ({tx}, {ty})")
                            lines.append("")
                            lines.append(lore_data['description'])
                            
                            # Add basic description if different from lore description
                            if basic_desc and basic_desc != lore_data['description']:
                                lines.append("")
                                lines.append(f"Properties: {basic_desc}")
                            
                            # Add lore text
                            if lore_data.get('lore'):
                                lines.append("")
                                lines.append(lore_data['lore'])
                            
                            # Add condition text (for lightsabers)
                            if lore_data.get('condition'):
                                lines.append("")
                                lines.append(lore_data['condition'])
                            
                            # Add choice prompt (for artifacts)
                            if lore_data.get('choice'):
                                lines.append("")
                                lines.append(lore_data['choice'])
                            
                            _show_centered(game, lines, title=lore_data['name'])
                        except Exception:
                            try: game.ui.messages.add("Inspect failed on item.")
                            except Exception: pass
                        return
                    # fallback: show tile glyph meaning
                    try:
                        ch = None
                        try: ch = game.game_map[ty][tx]
                        except Exception: ch = None
                        if ch is None:
                            _show_centered(game, ["Nothing at that location."], title="Inspect")
                            return
                        # map common glyphs to words
                        if ch == getattr(Display,'FLOOR','.'):
                            _show_centered(game, [f"Open ground at {tx},{ty}."], title="Tile")
                        elif ch == getattr(Display,'WALL','#'):
                            _show_centered(game, [f"Wall at {tx},{ty}."], title="Tile")
                        elif ch == getattr(Display,'TREE','T'):
                            _show_centered(game, [f"Tree at {tx},{ty}."], title="Tile")
                        elif ch == getattr(Display,'SHIP','S'):
                            _show_centered(game, [f"A crashed ship is here ({tx},{ty})."], title="Tile")
                        elif ch == getattr(Display,'COMMS','C'):
                            _show_centered(game, [f"A comms terminal is here ({tx},{ty})."], title="Tile")
                        else:
                            # check for registered landmarks with lore
                            try:
                                lm = getattr(game, 'map_landmarks', {}) or {}
                                key = (tx, ty)
                                if key in lm:
                                    info = lm.get(key, {})
                                    title = info.get('name', 'Point of Interest')
                                    desc = info.get('description', '')
                                    art = info.get('art')
                                    lore = info.get('lore')
                                    lines = []
                                    if art:
                                        lines.extend(art)
                                        lines.append('')
                                    if lore:
                                        for ln in lore:
                                            lines.append(ln)
                                        lines.append('')
                                    if desc:
                                        lines.append(desc)
                                    if not lines:
                                        lines = [f"{title} at {tx},{ty}"]
                                    _show_centered(game, lines, title=title)
                                else:
                                    _show_centered(game, [f"Tile '{str(ch)}' at {tx},{ty}."], title="Tile")
                            except Exception:
                                _show_centered(game, [f"Tile '{str(ch)}' at {tx},{ty}."], title="Tile")
                    except Exception:
                        try: game.ui.messages.add("Inspect failed (unknown tile).")
                        except Exception: pass
                except Exception:
                    try: game.ui.messages.add("Inspect failed (internal).")
                    except Exception: pass
            except Exception:
                try:
                    game.ui.messages.add("Inspect handling error.")
                except Exception:
                    pass
                # debug trace removed in follow-up
            return False  # No turn consumed

        if key == ord('g'):
            try:
                px = getattr(game.player, 'x', 0)
                py = getattr(game.player, 'y', 0)
                
                # Check for narrative events (journal, holocron, distress signal)
                if hasattr(game, 'map_landmarks') and (px, py) in game.map_landmarks:
                    landmark = game.map_landmarks[(px, py)]
                    landmark_type = landmark.get('type', '')
                    
                    # Handle journal discovery
                    if landmark_type == 'journal' and not landmark.get('discovered', False):
                        journal = landmark.get('data', {})
                        formatted = __import__('jedi_fugitive.game.narrative_events', fromlist=['format_journal_display']).format_journal_display(journal)
                        game.ui.centered_menu(formatted, f"Discovery: {journal.get('title', 'Journal')}")
                        
                        # Apply corruption effect
                        if 'corruption_effect' in journal:
                            game.player.dark_corruption = max(0, min(100, 
                                getattr(game.player, 'dark_corruption', 50) + journal['corruption_effect']))
                        
                        # Mark as discovered and remove from map
                        landmark['discovered'] = True
                        game.game_map[py][px] = '.'
                        del game.map_landmarks[(px, py)]
                        game.ui.messages.add(f"#3#Journal discovered and logged.#0#")
                        return
                    
                    # Handle holocron discovery
                    elif landmark_type == 'holocron' and not landmark.get('discovered', False):
                        holocron = landmark.get('data', {})
                        formatted = __import__('jedi_fugitive.game.narrative_events', fromlist=['format_holocron_display']).format_holocron_display(holocron)
                        game.ui.centered_menu(formatted, "Discovery: Ancient Holocron")
                        
                        # Apply corruption effect
                        if 'corruption_effect' in holocron:
                            game.player.dark_corruption = max(0, min(100,
                                getattr(game.player, 'dark_corruption', 50) + holocron['corruption_effect']))
                        
                        # Mark as discovered and remove from map
                        landmark['discovered'] = True
                        game.game_map[py][px] = '.'
                        del game.map_landmarks[(px, py)]
                        game.ui.messages.add(f"#3#Holocron message received.#0#")
                        return
                    
                    # Handle distress signal
                    elif landmark_type == 'distress_signal' and not landmark.get('discovered', False):
                        signal = landmark.get('data', {})
                        formatted, choice_mapping = __import__('jedi_fugitive.game.narrative_events', fromlist=['format_distress_signal']).format_distress_signal(signal)
                        game.ui.centered_menu(formatted, f"{signal['signal_type'].upper().replace('_', ' ')}")
                        
                        # Store pending choice
                        game.pending_narrative_choice = (signal, choice_mapping, 'distress')
                        
                        # Mark as discovered and remove from map
                        landmark['discovered'] = True
                        game.game_map[py][px] = '.'
                        del game.map_landmarks[(px, py)]
                        game.ui.messages.add(f"#3#Signal received - press 1-3 to respond.#0#")
                        return
                
                # Check if standing on a loot cache
                if hasattr(game, 'map_landmarks') and (px, py) in game.map_landmarks:
                    landmark = game.map_landmarks[(px, py)]
                    if landmark.get('is_loot_cache', False) and not landmark.get('looted', False):
                        # Check if cache guards are nearby (only enemies with "Cache Guard" in name)
                        guards_alive = []
                        for enemy in game.enemies:
                            ex = getattr(enemy, 'x', -999)
                            ey = getattr(enemy, 'y', -999)
                            dist = abs(ex - px) + abs(ey - py)
                            enemy_name = getattr(enemy, 'name', '')
                            # Only count enemies that are specifically cache guards
                            if dist <= 10 and 'Cache Guard' in enemy_name:
                                guards_alive.append(enemy)
                        
                        if guards_alive:
                            try: 
                                game.ui.messages.add(f"⚠ Cache guarded by {len(guards_alive)} hostile(s)! Clear them first.")
                            except Exception: pass
                            return
                        
                        # Open the loot cache
                        cache_name = landmark.get('name', 'Loot Cache')
                        try: 
                            game.ui.messages.add(f"═══ {cache_name} ═══")
                            game.ui.messages.add("Opening cache...")
                        except Exception: pass
                        
                        # Get loot from cache
                        loot = getattr(game, 'loot_caches', {}).get((px, py), [])
                        
                        if loot:
                            try: 
                                game.ui.messages.add(f"Found {len(loot)} items!")
                            except Exception: pass
                            
                            # Add all loot to map for pickup
                            for item in loot:
                                game.items_on_map.append({'x': px, 'y': py, 'item': item})
                            
                            # Mark as looted
                            landmark['looted'] = True
                            
                            try:
                                game.ui.messages.add(f"Loot added to this location. Use 'g' again to pick up items.")
                            except Exception: pass
                        else:
                            try: game.ui.messages.add("Cache is empty (already looted).")
                            except Exception: pass
                        
                        return
                
                # Normal pickup
                equipment.pick_up(game)
            except Exception as e:
                try: 
                    import traceback
                    game.ui.messages.add(f"Pick up failed: {str(e)}")
                    # Debug: print to terminal
                    # Error: Pick up error: {e}
                    traceback.print_exc()
                except Exception: pass
            return False  # No turn consumed

        if key == ord('e'):
            try:
                equipment.equip_item(game)
                # Suspicion/Disguise: Equipping a disguise lowers suspicion
                if hasattr(game.player, 'disguise') and game.player.disguise:
                    if hasattr(game.player, 'suspicion'):
                        game.player.suspicion = max(0, game.player.suspicion - 10)
                # Pursuit: Equipping a disguise can lower detection
                if hasattr(game.player, 'pursuit_system') and game.player.pursuit_system:
                    game.player.pursuit_system.update_detection('stealth', disguise_bonus=10)
            except Exception as e:
                try: 
                    import traceback
                    game.ui.messages.add(f"Equip failed: {str(e)}")
                    traceback.print_exc()
                except Exception: pass
            return False  # No turn consumed

        # Toggle map display using 'M' key
        if key == ord('M'):
            try:
                # Toggle map visibility
                current_visible = getattr(game, 'map_visible', True)
                game.map_visible = not current_visible
                status = "visible" if game.map_visible else "hidden"
                try: game.ui.messages.add(f"Map display: {status}")
                except Exception: pass
            except Exception as e:
                try: game.ui.messages.add(f"Map toggle failed: {e}")
                except Exception: pass
            return False  # No turn consumed
            
        if key == ord('u'):  # Use/consume item from inventory
            try:
                equipment.use_item(game)
                # Suspicion: Using a disguise item (e.g., consumable) can lower suspicion
                if hasattr(game.player, 'disguise') and game.player.disguise:
                    if hasattr(game.player, 'suspicion'):
                        game.player.suspicion = max(0, game.player.suspicion - 5)
            except Exception as e:
                try: 
                    import traceback
                    game.ui.messages.add(f"Use failed: {str(e)}")
                    traceback.print_exc()
                except Exception: pass
            return False  # No turn consumed

        if key == ord('d'):
            try:
                equipment.drop_item(game)
            except Exception:
                try: game.ui.messages.add("Drop failed.") 
                except Exception: pass
            return False  # No turn consumed

        # Destroy POI for XP (capital D) - Light Side action
        if key == ord('D'):
            try:
                px = getattr(game.player, 'x', 0)
                py = getattr(game.player, 'y', 0)
                # Check if player is standing on a landmark/POI
                if hasattr(game, 'map_landmarks') and (px, py) in game.map_landmarks:
                    landmark = game.map_landmarks[(px, py)]
                    poi_name = landmark.get('name', 'Point of Interest')
                    # Give XP reward (base 30, plus bonus for certain types)
                    xp_reward = 30
                    if 'sith_lore' in landmark:
                        xp_reward = 50
                    game.player.light_xp = getattr(game.player, 'light_xp', 0) + xp_reward
                    # Reduce corruption (light side action)
                    if hasattr(game.player, 'corruption_system') and game.player.corruption_system:
                        game.player.corruption_system.adjust_corruption(-5)
                    else:
                        game.player.dark_corruption = max(0, game.player.dark_corruption - 5)
                    # Faction: Cleansing Sith POI may increase Republic/Settler rep
                    if hasattr(game.player, 'faction_manager') and game.player.faction_manager:
                        game.player.faction_manager.adjust_reputation('Republic', 2)
                        game.player.faction_manager.adjust_reputation('Settlers', 2)
                    # Pursuit: Destroying POI is a visible action
                    if hasattr(game.player, 'pursuit_system') and game.player.pursuit_system:
                        game.player.pursuit_system.update_detection('combat')
                    # Check for level up - USE UNIFIED SYSTEM
                    while game.player.light_xp >= game.player.xp_to_next_light:
                        game.player.light_xp -= game.player.xp_to_next_light
                        game.player.light_level += 1
                        game.player.level = max(game.player.light_level, game.player.dark_level)
                        game.player.xp_to_next_light = int(game.player.xp_to_next_light * 1.5)
                        # Call unified level_up() which shows interactive menu
                        try:
                            game.player.level_up()
                            try: game.ui.messages.add(f"LIGHT SIDE LEVEL UP! Now level {game.player.level}")
                            except Exception: pass
                        except Exception:
                            pass
                    cell = game.game_map[py][px]
                    floor = getattr(Display, "FLOOR", ".")
                    game.game_map[py][px] = floor
                    del game.map_landmarks[(px, py)]
                    try:
                        if hasattr(game.player, 'add_log_entry'):
                            entry = game.player.narrative_text(
                                light_version=f"Destroyed {poi_name} to cleanse this evil place. Gained {xp_reward} XP.",
                                dark_version=f"Destroyed {poi_name}, wasting its power. Gained {xp_reward} XP.",
                                balanced_version=f"Destroyed {poi_name}. Gained {xp_reward} XP."
                            )
                            game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
                    except Exception:
                        pass
                    try: game.ui.messages.add(f"Destroyed {poi_name}! +{xp_reward} XP (Light)")
                    except Exception: pass
                    try:
                        pass  # turn_count advances once per world tick (GameManager._world_tick)
                    except Exception:
                        pass
                else:
                    try: game.ui.messages.add("No POI here to destroy.")
                    except Exception: pass
            except Exception as e:
                try: game.ui.messages.add(f"Destroy failed: {e}")
                except Exception: pass
            return False  # No turn consumed

        # Absorb energy from POI for dark side XP (capital A)
        if key == ord('A'):
            try:
                px = getattr(game.player, 'x', 0)
                py = getattr(game.player, 'y', 0)
                # Check if player is standing on a landmark/POI
                if hasattr(game, 'map_landmarks') and (px, py) in game.map_landmarks:
                    landmark = game.map_landmarks[(px, py)]
                    poi_name = landmark.get('name', 'Point of Interest')
                    # Give XP reward (less than destruction - 20 base, 35 for Sith lore)
                    xp_reward = 20
                    if 'sith_lore' in landmark:
                        xp_reward = 35
                    game.player.dark_xp = getattr(game.player, 'dark_xp', 0) + xp_reward
                    # Increase corruption (dark side action)
                    if hasattr(game.player, 'corruption_system') and game.player.corruption_system:
                        game.player.corruption_system.adjust_corruption(8)
                    else:
                        game.player.dark_corruption = min(100, game.player.dark_corruption + 8)
                    # Faction: Absorbing Sith POI may lower Republic/Settler rep, increase Sith Empire rep
                    if hasattr(game.player, 'faction_manager') and game.player.faction_manager:
                        game.player.faction_manager.adjust_reputation('Sith Empire', 2)
                        game.player.faction_manager.adjust_reputation('Republic', -2)
                        game.player.faction_manager.adjust_reputation('Settlers', -2)
                    # Pursuit: Absorbing POI is a visible action
                    if hasattr(game.player, 'pursuit_system') and game.player.pursuit_system:
                        game.player.pursuit_system.update_detection('force')
                    # Check for level up - USE UNIFIED SYSTEM
                    while game.player.dark_xp >= game.player.xp_to_next_dark:
                        game.player.dark_xp -= game.player.xp_to_next_dark
                        game.player.dark_level += 1
                        game.player.level = max(game.player.light_level, game.player.dark_level)
                        game.player.xp_to_next_dark = int(game.player.xp_to_next_dark * 1.5)
                        # Call unified level_up() which shows interactive menu
                        try:
                            game.player.level_up()
                            try: game.ui.messages.add(f"DARK SIDE LEVEL UP! Now level {game.player.level}")
                            except Exception: pass
                        except Exception:
                            pass
                    cell = game.game_map[py][px]
                    floor = getattr(Display, "FLOOR", ".")
                    game.game_map[py][px] = floor
                    del game.map_landmarks[(px, py)]
                    try:
                        if hasattr(game.player, 'add_log_entry'):
                            entry = game.player.narrative_text(
                                light_version=f"Absorbed dark energy from {poi_name} by necessity. Gained {xp_reward} XP.",
                                dark_version=f"Drained {poi_name}, consuming its dark power! Gained {xp_reward} XP.",
                                balanced_version=f"Absorbed energy from {poi_name}. Gained {xp_reward} XP."
                            )
                            game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
                    except Exception:
                        pass
                    try: game.ui.messages.add(f"Absorbed energy from {poi_name}! +{xp_reward} XP (Dark)")
                    except Exception: pass
                    try:
                        pass  # turn_count advances once per world tick (GameManager._world_tick)
                    except Exception:
                        pass
                else:
                    try: game.ui.messages.add("No POI here to absorb from.")
                    except Exception: pass
            except Exception as e:
                try: game.ui.messages.add(f"Absorb failed: {e}")
                except Exception: pass
            return False  # No turn consumed

        # Trade with merchant (capital T)
        if key == ord('T'):
            try:
                px = getattr(game.player, 'x', 0)
                py = getattr(game.player, 'y', 0)
                # Check if standing on or near merchant
                if hasattr(game, 'merchants') and (px, py) in game.merchants:
                    _open_merchant_menu(game, px, py)
                    # Faction: Trading with merchants can increase reputation
                    if hasattr(game.player, 'faction_manager') and game.player.faction_manager:
                        merchant = game.merchants[(px, py)]
                        faction = merchant.get('faction', None)
                        if faction:
                            game.player.faction_manager.adjust_reputation(faction, 1)
                else:
                    # Check adjacent tiles
                    found_merchant = False
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            check_pos = (px + dx, py + dy)
                            if hasattr(game, 'merchants') and check_pos in game.merchants:
                                _open_merchant_menu(game, check_pos[0], check_pos[1])
                                found_merchant = True
                                # Faction: Trading with merchants can increase reputation
                                if hasattr(game.player, 'faction_manager') and game.player.faction_manager:
                                    merchant = game.merchants[check_pos]
                                    faction = merchant.get('faction', None)
                                    if faction:
                                        game.player.faction_manager.adjust_reputation(faction, 1)
                                break
                        if found_merchant:
                            break
                    if not found_merchant:
                        try: game.ui.messages.add("No merchant nearby. Look for merchant camps (3x3 X squares).")
                        except Exception: pass
            except Exception as e:
                try: game.ui.messages.add(f"Trade failed: {e}")
                except Exception: pass
            return False  # No turn consumed
        
        # Talk to NPC (lowercase t)
        if key == ord('t'):
            try:
                # Talk to NPC
                npc = game.handle_npc_interactions()
                if npc:
                    _show_npc_interaction_popup(game, npc)
                    # Faction: Talking to NPCs can increase Settler reputation
                    if hasattr(game.player, 'faction_manager') and game.player.faction_manager:
                        game.player.faction_manager.adjust_reputation('Settlers', 1)
                else:
                    try: 
                        game.ui.messages.add("No one to talk to here.")
                    except Exception: pass
            except Exception:
                try: game.ui.messages.add("Talk interaction failed.")
                except Exception: pass
            return False  # No turn consumed
            
        # Throw grenade (using 'G' key)
        if key == ord('G'):
            try:
                # Check if player has grenades
                inv = getattr(game.player, 'inventory', [])
                has_grenade = any(isinstance(item, dict) and item.get('id') in ['grenade', 'thermal_grenade'] for item in inv)
                
                if not has_grenade:
                    try: game.ui.messages.add("No grenades in inventory!")
                    except Exception: pass
                    return
                    
                # Enter grenade targeting mode
                game.pending_grenade_throw = True
                game.target_x = getattr(game.player, 'x', 0)
                game.target_y = getattr(game.player, 'y', 0)
                try: game.ui.messages.add("Select grenade target (Arrow keys/WASD to aim, Space to throw, ESC to cancel)")
                except Exception: pass
            except Exception as e:
                try: game.ui.messages.add(f"Grenade throw failed: {e}")
                except Exception: pass
            return False  # No turn consumed

        if key == ord('q'):  # Unequip weapon/item
            try:
                if hasattr(game, "unequip_item"):
                    game.unequip_item()
                elif hasattr(game.player, "unequip_weapon"):
                    game.player.unequip_weapon(); game.ui.messages.add("Unequipped weapon.")
                else:
                    try: game.ui.messages.add("No unequip available.") 
                    except Exception: pass
            except Exception:
                try: game.ui.messages.add("Unequip failed.") 
                except Exception: pass
            return False  # No turn consumed

        if key == ord('o'):
            try:
                if hasattr(game, "unequip_armor"):
                    game.unequip_armor()
                elif hasattr(game.player, "unequip_armor"):
                    game.player.unequip_armor(); game.ui.messages.add("Unequipped armor.")
                else:
                    try: game.ui.messages.add("No unequip available.") 
                    except Exception: pass
            except Exception:
                try: game.ui.messages.add("Unequip armor failed.") 
                except Exception: pass
            return False  # No turn consumed

        # Fire weapon with 'f' key (auto-aim)
        if key == ord('f'):
            try:
                # Check both main hand and offhand for ranged weapons
                weapon = getattr(game.player, 'equipped_weapon', None)
                offhand = getattr(game.player, 'equipped_offhand', None)
                
                # Determine which weapon to use (prefer main hand, fallback to offhand)
                active_weapon = None
                is_ranged = False
                weapon_range = 5
                
                # Check main hand first
                if weapon:
                    weapon_name = ''
                    if isinstance(weapon, dict):
                        weapon_name = weapon.get('name', '').lower()
                        weapon_range = weapon.get('range', 5)
                    elif hasattr(weapon, 'name'):
                        weapon_name = weapon.name.lower()
                        weapon_range = getattr(weapon, 'range', 5)
                    
                    if 'blaster' in weapon_name or 'pistol' in weapon_name or 'rifle' in weapon_name or 'bowcaster' in weapon_name:
                        is_ranged = True
                        active_weapon = weapon
                
                # Check offhand if no ranged in main hand
                if not is_ranged and offhand:
                    weapon_name = ''
                    if isinstance(offhand, dict):
                        weapon_name = offhand.get('name', '').lower()
                        weapon_range = offhand.get('range', 5)
                    elif hasattr(offhand, 'name'):
                        weapon_name = offhand.name.lower()
                        weapon_range = getattr(offhand, 'range', 5)
                    
                    if 'blaster' in weapon_name or 'pistol' in weapon_name or 'rifle' in weapon_name or 'bowcaster' in weapon_name:
                        is_ranged = True
                        active_weapon = offhand
                
                if is_ranged and active_weapon:
                    # Auto-aim to nearest enemy within range
                    px = getattr(game.player, "x", 0)
                    py = getattr(game.player, "y", 0)
                    nearest_enemy = None
                    min_dist = weapon_range + 1
                    
                    # Find nearest enemy within weapon range
                    for enemy in game.enemies:
                        if hasattr(enemy, 'hp') and enemy.hp > 0:
                            dx = abs(enemy.x - px)
                            dy = abs(enemy.y - py)
                            dist = max(dx, dy)  # Chebyshev distance
                            if dist <= weapon_range and dist < min_dist:
                                nearest_enemy = enemy
                                min_dist = dist
                    
                    if nearest_enemy:
                        # Auto-fire at nearest enemy with descriptive combat log
                        try:
                            from jedi_fugitive.game.projectiles import spawn_blaster
                            weapon_damage = getattr(active_weapon, 'base_damage', 6) if hasattr(active_weapon, 'base_damage') else 6
                            
                            # Get weapon name for description
                            weapon_name = ''
                            if isinstance(active_weapon, dict):
                                weapon_name = active_weapon.get('name', 'blaster')
                            elif hasattr(active_weapon, 'name'):
                                weapon_name = active_weapon.name
                            else:
                                weapon_name = 'blaster'
                            
                            # Create descriptive fire message
                            fire_messages = [
                                f"#2#Your {weapon_name} hums as it fires a searing bolt at {nearest_enemy.name}!#0#",
                                f"#2#Crimson energy lances from your {weapon_name} toward {nearest_enemy.name}!#0#",
                                f"#2#You squeeze the trigger - your {weapon_name} unleashes deadly plasma at {nearest_enemy.name}!#0#",
                                f"#2#A brilliant bolt of energy streaks from your {weapon_name} toward {nearest_enemy.name}!#0#",
                                f"#2#Your {weapon_name} erupts with blaster fire - the bolt races toward {nearest_enemy.name}!#0#",
                            ]
                            
                            import random
                            try: game.ui.messages.add(random.choice(fire_messages))
                            except Exception: pass
                            
                            spawn_blaster(game, px, py, nearest_enemy.x, nearest_enemy.y, damage=weapon_damage, symbol='-', color_pair=9)
                            return True  # Turn consumed
                        except Exception as e:
                            try: game.ui.messages.add(f"Weapon malfunction: {e}")
                            except Exception: pass
                            return False
                    else:
                        try: game.ui.messages.add(f"No enemies within {weapon_range}-tile range!")
                        except Exception: pass
                        return False
                else:
                    try: game.ui.messages.add('No ranged weapon equipped.')
                    except Exception: pass
                    return False
            except Exception:
                try: game.ui.messages.add('Weapon fire failed.')
                except Exception: pass
                return False

        # Force abilities menu with 'z' key (EXCLUSIVELY for Force powers - no other 'z' bindings)
        if key == ord('z'):
            try:
                from jedi_fugitive.game.abilities import choose_ability
                chosen = choose_ability(game)
            except Exception:
                chosen = None
            
            if not chosen:
                try: game.ui.messages.add('No Force ability selected.')
                except Exception: pass
                return False
            
            game.pending_force_ability = chosen
            game.target_x = getattr(game.player, "x", 0)
            game.target_y = getattr(game.player, "y", 0)
            
            # Pursuit/Detection: Using Force powers
            if hasattr(game.player, 'pursuit_system') and game.player.pursuit_system:
                game.player.pursuit_system.update_detection('force')
            
            # Corruption: Using dark side powers increases corruption
            if hasattr(game.player, 'corruption_system') and game.player.corruption_system:
                if hasattr(chosen, 'alignment') and chosen.alignment == 'dark':
                    game.player.corruption_system.adjust_corruption(5)
            
            try: game.ui.messages.add(f"Targeting: {getattr(chosen,'name',str(chosen))} — move reticle and press Enter to confirm, Esc to cancel.")
            except Exception: pass
            return False  # No turn consumed

        # Meditate: spend a turn to reduce stress if safe
        # View travel log (journal)
        if key == ord('J'):
            try:
                _show_hero_journey_journal(game)
            except Exception as e:
                try: 
                    game.ui.messages.add(f"Cannot view journal: {e}")
                except Exception: 
                    pass
            return False  # No turn consumed

        # Crafting menu (capital C)
        if key == ord('C'):
            try:
                equipment.open_crafting_menu(game)
            except Exception:
                try: game.ui.messages.add("Crafting menu failed.")
                except Exception: pass
            return False  # No turn consumed

        if key == ord('m'):
            try:
                _show_meditation_menu(game)
                return
            except Exception:
                try: game.ui.messages.add("Meditation failed.")
                except Exception: pass
                return

        # Stairs interaction - Descend (>)
        if key == ord('>'):
            try:
                px = getattr(game.player, 'x', 0)
                py = getattr(game.player, 'y', 0)
                cell = game.game_map[py][px] if 0 <= py < len(game.game_map) and 0 <= px < len(game.game_map[0]) else None
                
                if cell == '>' or cell == 'D':  # '>' for stairs, 'D' for tomb entrances
                    # Check if we're at a tomb entrance
                    if hasattr(game, 'tomb_entrances') and (px, py) in game.tomb_entrances:
                        # Enter tomb
                        if hasattr(game, 'enter_special_dungeon'):
                            game.ui.messages.add("You descend into the ancient tomb...")
                            game.enter_special_dungeon((px, py))
                            return True  # Consumes turn
                        elif hasattr(game, 'enter_tomb'):
                            game.ui.messages.add("You descend into the ancient tomb...")
                            game.enter_tomb()
                            return True  # Consumes turn
                    # Check if we're in a tomb and can descend deeper
                    elif hasattr(game, 'tomb_levels') and game.tomb_levels is not None:
                        current_level = getattr(game, 'current_tomb_level', 0)
                        max_tomb_depth = 5  # Default max depth
                        if current_level < max_tomb_depth:
                            game.ui.messages.add(f"You descend deeper into the tomb... (Level {current_level + 1})")
                            # Generate next level if needed
                            if hasattr(game, 'descend_tomb_level'):
                                game.descend_tomb_level()
                            return True  # Consumes turn
                        else:
                            game.ui.messages.add("The way down is blocked by ancient rubble.")
                    else:
                        game.ui.messages.add("These stairs lead somewhere, but you cannot descend here.")
                else:
                    game.ui.messages.add("There are no stairs here.")
            except Exception as e:
                try: game.ui.messages.add(f"Cannot descend: {e}")
                except Exception: pass
            return False  # UI action
        
        # Stairs interaction - Ascend (<)
        if key == ord('<'):
            try:
                px = getattr(game.player, 'x', 0)
                py = getattr(game.player, 'y', 0)
                cell = game.game_map[py][px] if 0 <= py < len(game.game_map) and 0 <= px < len(game.game_map[0]) else None
                
                if cell == '<':
                    # Check if we're in a tomb and can ascend
                    if hasattr(game, 'tomb_levels') and game.tomb_levels is not None:
                        current_level = getattr(game, 'current_tomb_level', 0)
                        if current_level > 0:
                            game.ui.messages.add(f"You climb back up... (Level {current_level - 1})")
                            if hasattr(game, 'ascend_tomb_level'):
                                game.ascend_tomb_level()
                            return True  # Consumes turn
                        else:
                            # Exit tomb
                            game.ui.messages.add("You emerge from the tomb back into the harsh surface...")
                            if hasattr(game, 'exit_tomb'):
                                game.exit_tomb()
                            return True  # Consumes turn
                    else:
                        game.ui.messages.add("These stairs lead up, but you cannot ascend here.")
                else:
                    game.ui.messages.add("There are no stairs here.")
            except Exception as e:
                try: game.ui.messages.add(f"Cannot ascend: {e}")
                except Exception: pass
            return False  # UI action

        # Movement
        if key in move_map:
            dx, dy = move_map[key]
            px = getattr(game.player, "x", 0)
            py = getattr(game.player, "y", 0)
            nx = px + dx
            ny = py + dy
            
            # Wraparound movement (360° world with no boundaries)
            max_y = len(game.game_map)
            max_x = len(game.game_map[0]) if max_y else 0
            
            if max_x > 0 and max_y > 0:
                # Wrap coordinates to opposite side if they go out of bounds
                nx = nx % max_x  # Wraps horizontally
                ny = ny % max_y  # Wraps vertically
                
                # Add wraparound message for immersion
                try:
                    wraparound_msg = None
                    if px == 0 and dx == -1:
                        wraparound_msg = "You reach the edge of the world and emerge on the far side..."
                    elif px == max_x - 1 and dx == 1:
                        wraparound_msg = "The landscape loops back upon itself..."
                    elif py == 0 and dy == -1:
                        wraparound_msg = "The horizon bends impossibly, bringing you to the other side..."
                    elif py == max_y - 1 and dy == 1:
                        wraparound_msg = "Space itself folds, transporting you across the world..."
                    
                    if wraparound_msg:
                        game.ui.messages.add(wraparound_msg)
                except Exception:
                    pass
            else:
                return
            
            cell = None
            try: cell = game.game_map[ny][nx]
            except Exception: cell = None

            # resolved cell available as 'cell' (no debug trace)

            # deterministic blocking: allow only floor tiles, stairs, ship/comms, '*' or items
            try:
                wall_char = getattr(Display, "WALL", "#")
                cell_str = str(cell) if cell is not None else ''
                
                # NON-walkable tiles (walls and major obstacles)
                # Display.WALL = '█', but some maps use '#'
                # Special dungeon walls: ▓, ♦, █, ╬, ║, ▤, ▣
                non_walkable = {
                    '█',  # Display.WALL / Shadowmaze walls
                    '#',  # Legacy wall tile
                    '^',  # Mountains (impassable)
                    '▓',  # Memory Vault crystal walls
                    '♦',  # Crystal Garden walls
                    '╬',  # Bone Cathedral walls
                    '║',  # Echo Chambers acoustic walls
                    '▤',  # Twisted Library bookshelf walls
                    '▣',  # Pain Forge metal walls
                }
                
                # WALKABLE special dungeon floor tiles
                # These must be explicitly allowed for special dungeons to work
                special_floors = {
                    '◊',  # Memory Vault crystal floor
                    '.',  # Crystal Garden rocky ground / normal floor
                    '▪',  # Shadowmaze shadow floor
                    '≈',  # Bone Cathedral bone debris
                    '≋',  # Echo Chambers resonant floor
                    '▫',  # Twisted Library parchment floor
                    '░',  # Pain Forge forge floor
                    '∞',  # Dream Nexus dream floor
                    '·',  # Standard floor tile
                }
                
                # Block ONLY if it's in non_walkable AND NOT in special_floors
                # Special floors override non_walkable (allows special dungeon navigation)
                if cell_str in non_walkable and cell_str not in special_floors:
                    try: game.ui.messages.add("Blocked.")
                    except Exception: pass
                    return
            except Exception:
                # If blocking check fails, allow movement (permissive fallback)
                pass

            # attack if enemy there
            enemy = None
            try:
                if hasattr(game, "enemy_at"):
                    enemy = game.enemy_at(nx, ny)
                else:
                    for e in getattr(game, "enemies", []):
                        if getattr(e, "x", -1) == nx and getattr(e, "y", -1) == ny and getattr(e, "is_alive", lambda: True)():
                            enemy = e; break
            except Exception:
                enemy = None

            if enemy:
                try:
                    perform_player_attack(game, enemy)
                    # Pursuit/Detection: Combat action
                    if hasattr(game.player, 'pursuit_system') and game.player.pursuit_system:
                        game.player.pursuit_system.update_detection('combat')
                    # Faction: Attacking certain enemies may affect reputation
                    if hasattr(game.player, 'faction_manager') and game.player.faction_manager:
                        if hasattr(enemy, 'faction') and enemy.faction:
                            game.player.faction_manager.adjust_reputation(enemy.faction, -5)
                    # Corruption: Killing innocents or dark actions can increase corruption
                    if hasattr(game.player, 'corruption_system') and game.player.corruption_system:
                        if hasattr(enemy, 'is_innocent') and enemy.is_innocent:
                            game.player.corruption_system.adjust_corruption(10)
                except Exception:
                    try: game.ui.messages.add("Attack failed (internal).")
                    except Exception: pass
                return True  # Attacking consumes a turn

            # Prefer centralized mover if available (_try_move_player) which already
            # contains canonical blocking logic used elsewhere in the codebase.
            moved = False
            try:
                if hasattr(game, '_try_move_player') and callable(game._try_move_player):
                    moved = game._try_move_player(dx, dy)
                else:
                    # fallback: same behavior as before
                    game.player.x = nx
                    game.player.y = ny
                    moved = True
            except Exception:
                moved = False

            if moved:
                # movement happened; UI will be updated by caller loop
                try:
                    game.player.facing = (int(dx), int(dy))
                except Exception:
                    pass
                
                # Apply atmospheric movement costs (Force energy drain)
                try:
                    if hasattr(game, 'atmospheric_manager'):
                        movement_cost = game.atmospheric_manager.get_movement_cost_modifier()
                        if movement_cost > 1.0:
                            # Extra movement cost drains Force energy
                            extra_cost = int((movement_cost - 1.0) * 10)  # Scale to reasonable numbers
                            if hasattr(game.player, 'force_energy'):
                                old_energy = game.player.force_energy
                                game.player.force_energy = max(0, game.player.force_energy - extra_cost)
                                if old_energy > 0 and game.player.force_energy == 0:
                                    try:
                                        game.ui.messages.add("The harsh conditions exhaust your Force reserves!")
                                    except Exception:
                                        pass
                except Exception:
                    pass
                
                # increment turn and update visibility
                pass  # turn_count advances once per world tick (GameManager._world_tick)
                try:
                    if hasattr(game, "compute_visibility"):
                        game.compute_visibility()
                except Exception:
                    pass
            return True  # Moving consumes a turn

        # Try registered commands as final fallback (like 'c' for Force Sense)
        if _process_registered_commands(game, key):
            return False  # Most registered commands are UI actions
        
        # If we get here, key was not handled
        return False

    except Exception:
        try: game.ui.messages.add("Input handling error.") 
        except Exception: pass
        return False

def perform_player_attack(game, enemy):
    """Defensive attack wrapper: try game combat then fallback to simple damage with messages."""
    try:
        # count attack as a player turn
        try:
            pass  # turn_count advances once per world tick (GameManager._world_tick)
        except Exception as e:
            if log:
                log.exception("Error in _fire_gun outer", exc_info=e)
            pass
        # Try calling combat function if available
        try:
            from jedi_fugitive.game.combat import player_attack
            player_attack(game.player, enemy, messages=getattr(game.ui, "messages", None), game=game)
        except TypeError:
            try:
                from jedi_fugitive.game.combat import player_attack
                player_attack(game.player, enemy)
            except Exception:
                pass
        except Exception:
            pass

        # Fallback simple attack if enemy still alive
        try:
            if getattr(enemy, "hp", None) is None or getattr(enemy, "hp", 1) > 0:
                atk = int(getattr(game.player, "attack", 1) or 1)
                defn = int(getattr(enemy, "defense", 0) or 0)
                dmg = max(1, atk - defn)
                try:
                    enemy.hp = getattr(enemy, "hp", 0) - dmg
                except Exception:
                    pass
                try:
                    game.ui.messages.add(f"You hit {getattr(enemy,'name','enemy')} for {dmg}.")
                except Exception:
                    pass
        except Exception:
            pass

        # check for death; do NOT award XP for kills. XP is awarded by artifact consumption.
        try:
            hp_after = getattr(enemy, "hp", 0)
            if hp_after <= 0:
                try:
                    game.ui.messages.add(f"{getattr(enemy,'name','Enemy')} was defeated!")
                except Exception:
                    pass
                # Track kill for milestone system
                try:
                    current_kills = getattr(game.player, 'total_kills', 0)
                    game.player.total_kills = current_kills + 1
                except Exception:
                    pass

                # Add to travel log with immersive, lore-rich narrative
                try:
                    if hasattr(game.player, 'add_log_entry'):
                        from jedi_fugitive.game.journal_entries import get_combat_victory_entry
                        enemy_name = getattr(enemy, 'name', 'an enemy')
                        
                        # Get player alignment and current biome
                        player_alignment = game.player.get_alignment() if hasattr(game.player, 'get_alignment') else 'balanced'
                        biome = getattr(game, 'current_biome', 'wasteland')
                        
                        # Determine weapon type for contextual entries
                        weapon = getattr(game.player, 'equipped_weapon', None)
                        weapon_type = None
                        if weapon:
                            weapon_name = getattr(weapon, 'name', '')
                            if isinstance(weapon, dict):
                                weapon_name = weapon.get('name', '')
                            weapon_type = weapon_name
                        
                        entry = get_combat_victory_entry(enemy_name, player_alignment, biome, weapon_type)
                        game.player.add_log_entry(entry, getattr(game, 'turn_count', 0))
                        game.player.kills_count = getattr(game.player, 'kills_count', 0) + 1
                except Exception:
                    pass

                # Reduce stress when defeating enemies (victory relief)
                try:
                    # Base stress reduction for defeating an enemy
                    stress_reduction = 2
                    
                    # More stress relief for defeating bosses or tough enemies
                    if is_boss:
                        stress_reduction = 8
                    elif enemy_level >= 3:
                        stress_reduction = 4
                    
                    game.player.reduce_stress(stress_reduction)
                except Exception:
                    pass

                # Grant dark path XP for killing enemies (10 points per kill)
                try:
                    game.player.dark_xp = getattr(game.player, 'dark_xp', 0) + 10
                    # Check for dark side level up
                    if game.player.dark_xp >= getattr(game.player, 'xp_to_next_dark', 100):
                        game.player.dark_level = getattr(game.player, 'dark_level', 1) + 1
                        game.player.dark_xp -= getattr(game.player, 'xp_to_next_dark', 100)
                        
                        # Apply stat bonuses: all stats +1, extra +1 attack for dark path
                        game.player.max_hp = game.player.max_hp + 5
                        game.player.attack = game.player.attack + 2  # +2 for dark path
                        game.player.defense = game.player.defense + 1
                        game.player.evasion = game.player.evasion + 1
                        game.player.accuracy = game.player.accuracy + 1
                        
                        game.ui.messages.add(f"Level up! You are now Level {game.player.dark_level}")
                        game.ui.messages.add(f"Dark path: +5 HP, +2 ATK, +1 DEF, +1 EVA, +1 ACC")
                except Exception:
                    pass

                # Equipment drop system - better enemies drop better equipment
                try:
                    from jedi_fugitive.items.weapons import WEAPONS
                    from jedi_fugitive.items.armor import ARMORS
                    from jedi_fugitive.items.consumables import ITEM_DEFS
                    import random
                    
                    enemy_name = getattr(enemy, 'name', '').lower()
                    enemy_level = getattr(enemy, 'level', 1)
                    is_boss = getattr(enemy, 'is_boss', False)
                    
                    # Determine drop chance and equipment tier based on enemy type
                    drop_chance = 0.0
                    equipment_tier = 'common'
                    rare_drop_chance = 0.0
                    
                    if is_boss:
                        drop_chance = 1.0  # Bosses always drop
                        equipment_tier = 'legendary'
                        rare_drop_chance = 0.5
                    elif 'lord' in enemy_name or 'regent' in enemy_name:
                        drop_chance = 0.9
                        equipment_tier = 'rare'
                        rare_drop_chance = 0.3
                    elif 'inquisitor' in enemy_name or 'officer' in enemy_name or 'sorcerer' in enemy_name:
                        drop_chance = 0.6
                        equipment_tier = 'uncommon'
                        rare_drop_chance = 0.15
                    elif 'assassin' in enemy_name or 'warrior' in enemy_name or 'acolyte' in enemy_name:
                        drop_chance = 0.4
                        equipment_tier = 'common'
                        rare_drop_chance = 0.08
                    elif 'trooper' in enemy_name or 'guard' in enemy_name:
                        drop_chance = 0.3
                        equipment_tier = 'common'
                        rare_drop_chance = 0.05
                    else:
                        drop_chance = 0.2
                        equipment_tier = 'common'
                        rare_drop_chance = 0.02
                    
                    # Adjust drop chance by enemy level
                    drop_chance = min(0.95, drop_chance + (enemy_level * 0.02))
                    
                    # Check if equipment drops
                    if random.random() < drop_chance:
                        # Decide drop type: 35% weapon, 15% armor, 15% shield, 15% consumable, 20% material
                        drop_roll = random.random()
                        if drop_roll < 0.35:
                            drop_type = 'weapon'
                        elif drop_roll < 0.50:
                            drop_type = 'armor'
                        elif drop_roll < 0.65:
                            drop_type = 'shield'
                        elif drop_roll < 0.80:
                            drop_type = 'consumable'
                        else:
                            drop_type = 'material'
                        
                        dropped_item = None
                        item_name = ''
                        item_rarity = 'Common'
                        
                        if drop_type == 'weapon':
                            # Get weapon pool based on tier
                            weapon_pool = []
                            
                            if equipment_tier == 'legendary' or (equipment_tier == 'rare' and random.random() < rare_drop_chance):
                                weapon_pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                                             w.rarity in ['Legendary', 'Rare'] and hasattr(w, 'name')]
                            elif equipment_tier == 'rare' or (equipment_tier == 'uncommon' and random.random() < rare_drop_chance):
                                weapon_pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                                             w.rarity in ['Rare', 'Uncommon'] and hasattr(w, 'name')]
                            elif equipment_tier == 'uncommon':
                                weapon_pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                                             w.rarity in ['Uncommon', 'Common'] and hasattr(w, 'name')]
                            else:
                                weapon_pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                                             w.rarity == 'Common' and hasattr(w, 'name')]
                            
                            if not weapon_pool:
                                weapon_pool = [w for w in WEAPONS if hasattr(w, 'name')][:5]
                            
                            if weapon_pool:
                                dropped_item = random.choice(weapon_pool)
                                item_name = getattr(dropped_item, 'name', 'Unknown Weapon')
                                item_rarity = getattr(dropped_item, 'rarity', 'Common')
                        
                        elif drop_type == 'armor':
                            # Get armor pool based on tier
                            armor_pool = []
                            
                            if equipment_tier == 'legendary':
                                armor_pool = [a for a in ARMORS if hasattr(a, 'rarity') and 
                                            a.rarity.lower() in ['epic', 'rare'] and hasattr(a, 'name')]
                            elif equipment_tier == 'rare':
                                armor_pool = [a for a in ARMORS if hasattr(a, 'rarity') and 
                                            a.rarity.lower() in ['rare', 'uncommon'] and hasattr(a, 'name')]
                            elif equipment_tier == 'uncommon':
                                armor_pool = [a for a in ARMORS if hasattr(a, 'rarity') and 
                                            a.rarity.lower() in ['uncommon', 'common'] and hasattr(a, 'name')]
                            else:
                                armor_pool = [a for a in ARMORS if hasattr(a, 'rarity') and 
                                            a.rarity.lower() == 'common' and hasattr(a, 'name')]
                            
                            if not armor_pool and ARMORS:
                                armor_pool = ARMORS[:2]  # Fallback
                            
                            if armor_pool:
                                dropped_item = random.choice(armor_pool)
                                item_name = getattr(dropped_item, 'name', 'Unknown Armor')
                                item_rarity = getattr(dropped_item, 'rarity', 'common').capitalize()
                        
                        elif drop_type == 'shield':
                            # Get shield pool based on tier
                            from jedi_fugitive.items.shields import SHIELDS
                            shield_pool = []
                            
                            if equipment_tier == 'legendary':
                                shield_pool = [s for s in SHIELDS if hasattr(s, 'rarity') and 
                                            s.rarity in ['Legendary', 'Rare'] and hasattr(s, 'name')]
                            elif equipment_tier == 'rare':
                                shield_pool = [s for s in SHIELDS if hasattr(s, 'rarity') and 
                                            s.rarity in ['Rare', 'Uncommon'] and hasattr(s, 'name')]
                            elif equipment_tier == 'uncommon':
                                shield_pool = [s for s in SHIELDS if hasattr(s, 'rarity') and 
                                            s.rarity in ['Uncommon', 'Common'] and hasattr(s, 'name')]
                            else:
                                shield_pool = [s for s in SHIELDS if hasattr(s, 'rarity') and 
                                            s.rarity == 'Common' and hasattr(s, 'name')]
                            
                            if not shield_pool and SHIELDS:
                                shield_pool = SHIELDS[:3]  # Fallback
                            
                            if shield_pool:
                                dropped_item = random.choice(shield_pool)
                                item_name = getattr(dropped_item, 'name', 'Unknown Shield')
                                item_rarity = getattr(dropped_item, 'rarity', 'Common')
                        
                        elif drop_type == 'consumable':
                            # Consumables - healing/utility items
                            consumable_pool = []
                            
                            # Better enemies drop better consumables
                            if equipment_tier in ['legendary', 'rare']:
                                # High tier: medkits, grenades, special items
                                consumable_pool = [item for item in ITEM_DEFS 
                                                 if item.get('type') == 'consumable' and 
                                                 item.get('id') in ['medkit_small', 'grenade', 'nutrient_paste', 
                                                                   'jedi_meditation_focus', 'ration']]
                            elif equipment_tier == 'uncommon':
                                # Mid tier: stimpacks, rations
                                consumable_pool = [item for item in ITEM_DEFS 
                                                 if item.get('type') == 'consumable' and 
                                                 item.get('id') in ['stimpack', 'ration', 'water_canteen', 'calming_tea']]
                            else:
                                # Low tier: basic healing
                                consumable_pool = [item for item in ITEM_DEFS 
                                                 if item.get('type') == 'consumable' and 
                                                 item.get('id') in ['water_canteen', 'calming_tea']]
                            
                            if not consumable_pool:
                                consumable_pool = [item for item in ITEM_DEFS if item.get('type') == 'consumable'][:3]
                            
                            if consumable_pool:
                                dropped_item = random.choice(consumable_pool)
                                item_name = dropped_item.get('name', 'Unknown Item')
                                item_rarity = 'Consumable'
                        
                        elif drop_type == 'material':
                            # Crafting materials - rarity based on enemy tier
                            from jedi_fugitive.items.crafting import MATERIALS
                            material_pool = []
                            
                            # Better enemies drop rarer materials
                            if equipment_tier == 'legendary':
                                # Legendary tier: Kyber, Beskar, Phrik
                                material_pool = [m for m in MATERIALS if m.rarity in ['Legendary', 'Epic']]
                            elif equipment_tier == 'rare':
                                # Rare tier: Cortosis, Energy Cells, Rare Alloys
                                material_pool = [m for m in MATERIALS if m.rarity in ['Epic', 'Rare', 'Uncommon']]
                            elif equipment_tier == 'uncommon':
                                # Uncommon tier: Crystals, Electronics, Rare Alloys
                                material_pool = [m for m in MATERIALS if m.rarity in ['Rare', 'Uncommon', 'Common']]
                            else:
                                # Common tier: Scrap Metal, Common Alloy, Basic parts
                                material_pool = [m for m in MATERIALS if m.rarity in ['Common', 'Uncommon']]
                            
                            if not material_pool:
                                material_pool = MATERIALS[:3]  # Fallback to first 3 materials
                            
                            if material_pool:
                                dropped_item = random.choice(material_pool)
                                item_name = dropped_item.name
                                item_rarity = dropped_item.rarity
                        
                        # Place equipment at enemy's location as a token
                        if dropped_item:
                            try:
                                ex, ey = getattr(enemy, 'x', 0), getattr(enemy, 'y', 0)
                                # Drops are found by position; the 'E' glyph is only a marker.
                                # Never overwrite stairs, tomb entrances, bridges or other drops:
                                # use the nearest free floor tile instead.
                                map_token = 'E'
                                floor_ch = getattr(Display, 'FLOOR', '.')
                                drops_now = getattr(game, 'equipment_drops', {}) or {}
                                spot = None
                                for r in range(0, 3):
                                    for ddy in range(-r, r + 1):
                                        for ddx in range(-r, r + 1):
                                            tx, ty = ex + ddx, ey + ddy
                                            if (0 <= ty < len(game.game_map) and 0 <= tx < len(game.game_map[0])
                                                    and game.game_map[ty][tx] == floor_ch and (tx, ty) not in drops_now):
                                                spot = (tx, ty)
                                                break
                                        if spot:
                                            break
                                    if spot:
                                        break
                                if spot is None:
                                    raise ValueError("no free tile for drop")
                                ex, ey = spot
                                if hasattr(game, 'game_map') and 0 <= ey < len(game.game_map) and 0 <= ex < len(game.game_map[0]):
                                    game.game_map[ey][ex] = map_token
                                    
                                    # Store equipment data for pickup
                                    if not hasattr(game, 'equipment_drops'):
                                        game.equipment_drops = {}
                                    game.equipment_drops[(ex, ey)] = {
                                        'type': drop_type,
                                        'item': dropped_item,
                                        'name': item_name,
                                        'rarity': item_rarity
                                    }
                                    
                                    # Message based on rarity
                                    if item_rarity in ['Legendary', 'Epic']:
                                        game.ui.messages.add(f"★★★ {enemy_name} dropped {item_name} ({drop_type})! ★★★")
                                    elif item_rarity == 'Rare':
                                        game.ui.messages.add(f"★★ {enemy_name} dropped {item_name} ({drop_type})! ★★")
                                    elif item_rarity == 'Uncommon':
                                        game.ui.messages.add(f"★ {enemy_name} dropped {item_name} ({drop_type})")
                                    else:
                                        game.ui.messages.add(f"{enemy_name} dropped {item_name} ({drop_type})")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Check if boss was defeated (victory condition)
                try:
                    if getattr(enemy, 'is_boss', False):
                        try:
                            # The story ends when you escape: defeating the hunter opens the way to the ship.
                            game.ui.messages.add(f"{getattr(enemy, 'name', 'Your nemesis')} falls! Nothing stands between you and your ship now.")
                            if enemy is getattr(game, 'final_boss', None):
                                game.player.add_to_travel_log(f"[DUEL] I defeated {getattr(enemy, 'name', 'my pursuer')} beside the wreck. Time to leave this world.")
                        except Exception:
                            pass
                except Exception:
                    pass

                # Award Dark XP for killing enemy (already handled in enemy.take_damage())
                except Exception:
                    pass
                
                # remove dead enemy from list (best-effort)
                try:
                    if enemy in getattr(game, "enemies", []):
                        try: game.enemies.remove(enemy)
                        except Exception: pass
                except Exception:
                    pass
        except Exception:
            pass

    except Exception:
        try:
            game.ui.messages.add("Attack failed (internal).")
        except Exception:
            pass


def _open_merchant_menu(game, mx, my):
    """Open trading interface with a merchant."""
    try:
        from jedi_fugitive.game.merchants import get_merchant_dialogue, calculate_sell_price
        
        merchant_data = game.merchants[(mx, my)]
        faction = merchant_data['faction']
        merchant_name = merchant_data['name']
        camp_name = merchant_data['camp_name']
        inventory = merchant_data['inventory']
        
        # Show greeting
        greeting = get_merchant_dialogue(faction, 'greeting')
        game.ui.messages.add(f"═══ {camp_name} ═══")
        game.ui.messages.add(f"{merchant_name}: \"{greeting}\"")
        game.ui.messages.add(f"Gold: {getattr(game.player, 'gold_collected', 0)}")
        
        # Create menu options
        options = ["[B]uy Items", "[S]ell Items", "[L]eave"]
        
        popup_items = [(opt, "", {}) for opt in options]
        choice = game.ui.popup_dialogue(popup_items, title=f"TRADING: {merchant_name.upper()}")
        
        if choice == 0:  # Buy
            _merchant_buy_menu(game, mx, my)
        elif choice == 1:  # Sell
            _merchant_sell_menu(game, mx, my)
        # else: Leave (choice == 2 or None)
        
    except Exception as e:
        try:
            game.ui.messages.add(f"Trade error: {e}")
        except:
            pass


def _merchant_buy_menu(game, mx, my):
    """Show merchant's inventory for purchase."""
    try:
        from jedi_fugitive.game.merchants import get_merchant_dialogue
        
        merchant_data = game.merchants[(mx, my)]
        faction = merchant_data['faction']
        merchant_name = merchant_data['name']
        inventory = merchant_data['inventory']
        
        if not inventory:
            game.ui.messages.add(f"{merchant_name}: \"Sold out! Check back later.\"")
            return False  # No turn consumed
        
        # Create menu items
        menu_items = []
        for i, inv_item in enumerate(inventory):
            item = inv_item['item']
            price = inv_item['price']
            quantity = inv_item.get('quantity', 1)
            
            # Handle both dict items (consumables) and object items (weapons/armor)
            if isinstance(item, dict):
                item_name = item.get('name', item.get('token', 'Unknown Item'))
            else:
                item_name = getattr(item, 'name', 'Unknown Item')
            
            if quantity > 1:
                menu_items.append(f"{item_name} x{quantity} - {price}g")
            else:
                menu_items.append(f"{item_name} - {price}g")
        
        menu_items.append("[Cancel]")
        
        popup_items = [(item, "", {}) for item in menu_items]
        choice = game.ui.popup_dialogue(popup_items, title=f"BUY FROM {merchant_name.upper()} | Gold: {getattr(game.player, 'gold_collected', 0)}")
        
        if choice is None or choice >= len(inventory):
            return False  # No turn consumed
        
        # Process purchase
        inv_item = inventory[choice]
        item = inv_item['item']
        price = inv_item['price']
        quantity = inv_item.get('quantity', 1)
        
        player_gold = getattr(game.player, 'gold_collected', 0)
        
        if player_gold < price:
            game.ui.messages.add(f"{merchant_name}: \"Not enough credits!\"")
            return False  # No turn consumed
        
        # Deduct gold
        game.player.gold_collected -= price
        # Invalidate stats cache so gold counter updates in GUI
        game.player._stats_cache_dirty = True
        
        # Add item to player inventory
        if quantity > 1:
            # Add multiple items (consumables)
            for _ in range(quantity):
                game.player.inventory.append(item)
        else:
            game.player.inventory.append(item)
        
        # Remove from merchant inventory
        inventory.pop(choice)
        
        # Success message
        buy_message = get_merchant_dialogue(faction, 'buy')
        game.ui.messages.add(f"{merchant_name}: \"{buy_message}\"")
        
        # Handle both dict items (consumables) and object items (weapons/armor)
        if isinstance(item, dict):
            item_name = item.get('name', item.get('token', 'Unknown Item'))
        else:
            item_name = getattr(item, 'name', 'Unknown Item')
        
        if quantity > 1:
            game.ui.messages.add(f"Purchased {item_name} x{quantity} for {price}g")
        else:
            game.ui.messages.add(f"Purchased {item_name} for {price}g")
        
    except Exception as e:
        try:
            game.ui.messages.add(f"Purchase failed: {e}")
        except:
            pass


def _merchant_sell_menu(game, mx, my):
    """Sell items from player inventory to merchant."""
    try:
        from jedi_fugitive.game.merchants import get_merchant_dialogue, calculate_sell_price
        
        merchant_data = game.merchants[(mx, my)]
        faction = merchant_data['faction']
        merchant_name = merchant_data['name']
        
        player_inventory = getattr(game.player, 'inventory', [])
        
        if not player_inventory:
            game.ui.messages.add("You have nothing to sell.")
            return False  # No turn consumed
        
        # Create menu items
        menu_items = []
        for item in player_inventory:
            # Handle both dict items (tokens) and object items (weapons/armor)
            if isinstance(item, dict):
                item_name = item.get('name', item.get('token', str(item)))
            else:
                item_name = getattr(item, 'name', str(item))
            sell_price = calculate_sell_price(item, faction)
            menu_items.append(f"{item_name} - Sell for {sell_price}g")
        
        menu_items.append("[Cancel]")
        
        popup_items = [(item, "", {}) for item in menu_items]
        choice = game.ui.popup_dialogue(popup_items, title=f"SELL TO {merchant_name.upper()} | Gold: {getattr(game.player, 'gold_collected', 0)}")
        
        if choice is None or choice >= len(player_inventory):
            return False  # No turn consumed
        
        # Process sale
        item = player_inventory[choice]
        sell_price = calculate_sell_price(item, faction)
        
        # Add gold to player
        game.player.gold_collected = getattr(game.player, 'gold_collected', 0) + sell_price
        # Invalidate stats cache so gold counter updates in GUI
        game.player._stats_cache_dirty = True
        
        # Remove from player inventory
        player_inventory.pop(choice)
        
        # Success message
        sell_message = get_merchant_dialogue(faction, 'sell')
        game.ui.messages.add(f"{merchant_name}: \"{sell_message}\"")
        # Handle both dict items (tokens) and object items (weapons/armor)
        if isinstance(item, dict):
            item_name = item.get('name', item.get('token', str(item)))
        else:
            item_name = getattr(item, 'name', str(item))
        game.ui.messages.add(f"Sold {item_name} for {sell_price}g")
        
    except Exception as e:
        try:
            game.ui.messages.add(f"Sale failed: {e}")
        except:
            pass

def _open_ritual_menu(game):
    """Open the ritual selection menu."""
    try:
        from .rituals import get_available_rituals, perform_ritual, format_ritual_display
        
        # Get player's current state
        player = game.player
        corruption_level = getattr(player, 'alignment_score', 0)
        # Convert alignment to corruption (positive alignment = lower corruption)
        if corruption_level > 0:
            corruption = max(0, 50 - corruption_level * 2)  # Light side = low corruption
        else:
            corruption = min(100, 50 + abs(corruption_level) * 2)  # Dark side = high corruption
            
        level = getattr(player, 'level', 1)
        tombs_completed = getattr(player, 'tombs_cleared', 0)
        
        # Determine location type for location-specific rituals
        location = None
        if hasattr(game, 'in_tomb') and game.in_tomb:
            location = 'tomb'
        # Check if we're near a meditation shrine (look for '?' symbols nearby)
        px, py = getattr(player, 'x', 0), getattr(player, 'y', 0)
        if hasattr(game, 'current_map') and game.current_map:
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    check_x, check_y = px + dx, py + dy
                    if (0 <= check_y < len(game.current_map) and 
                        0 <= check_x < len(game.current_map[0]) and
                        game.current_map[check_y][check_x] == '?'):
                        location = 'meditation_shrine'
                        break
                if location:
                    break
        
        # Get available rituals
        available_rituals = get_available_rituals(corruption, location, level, tombs_completed)
        
        if not available_rituals:
            try:
                game.ui.messages.add("No rituals are available to you at this time.")
                game.ui.messages.add("Your current alignment, location, or progress may limit your options.")
            except:
                pass
            return False  # No turn consumed
        
        # Create menu options
        menu_options = []
        ritual_data = []
        
        for category, ritual_id, ritual_info in available_rituals:
            name = ritual_info['name']
            
            # Add category prefix for clarity
            if category == 'crystal':
                prefix = "[Crystal] "
            elif category == 'jedi':
                prefix = "[Jedi] "
            elif category == 'sith':
                prefix = "[Sith] "
            elif category == 'burial':
                prefix = "[Burial] "
            elif category == 'milestone':
                prefix = "[Milestone] "
            else:
                prefix = ""
                
            menu_options.append(f"{prefix}{name}")
            ritual_data.append((category, ritual_id, ritual_info))
        
        menu_options.append("[Cancel]")
        
        # Show ritual selection menu
        popup_items = [(opt, "", {}) for opt in menu_options]
        choice = game.ui.popup_dialogue(popup_items, title="AVAILABLE RITUALS")
        
        if choice is None or choice == len(menu_options) - 1:  # Cancel
            return False  # No turn consumed
            
        # Get selected ritual
        selected_category, selected_id, selected_ritual = ritual_data[choice]
        
        # Show ritual details and confirm
        details = format_ritual_display(selected_category, selected_id, selected_ritual)
        details.append("")
        details.append("Do you wish to perform this ritual?")
        
        # Create confirmation menu
        confirm_choice = game.ui.centered_menu(["Yes, perform ritual", "No, cancel"], 
                                             title=selected_ritual['name'])
        
        if confirm_choice == 0:  # Yes, perform ritual
            # Perform the ritual
            description_lines, effects = perform_ritual(selected_category, selected_id, player, game)
            
            # Display ritual description
            try:
                game.ui.messages.add(f"=== {selected_ritual['name']} ===")
                for line in description_lines:
                    game.ui.messages.add(line)
            except:
                pass
            
            # Apply effects
            _apply_ritual_effects(game, effects)
            
            try:
                game.ui.messages.add(effects.get('message', 'The ritual is complete.'))
            except:
                pass
                
    except Exception as e:
        try:
            game.ui.messages.add(f"Ritual menu error: {e}")
        except:
            pass

def _apply_ritual_effects(game, effects):
    """Apply ritual effects to the player and game state."""
    try:
        player = game.player
        
        # Apply corruption changes
        if 'corruption_change' in effects:
            change = effects['corruption_change']
            current_corruption = getattr(player, 'corruption', 50)
            new_corruption = max(0, min(100, current_corruption + change))
            game.update_player_corruption(new_corruption)
        
        # Apply HP restoration
        if 'hp_restore' in effects:
            restore_amount = effects['hp_restore']
            current_hp = getattr(player, 'hp', 0)
            max_hp = getattr(player, 'max_hp', 100)
            player.hp = min(max_hp, current_hp + restore_amount)
        
        # Apply Force restoration
        if 'force_restore' in effects:
            restore_amount = effects['force_restore']
            if hasattr(player, 'force') and hasattr(player.force, 'current_force_points'):
                current_fp = player.force.current_force_points
                max_fp = getattr(player.force, 'max_force_points', 100)
                player.force.current_force_points = min(max_fp, current_fp + restore_amount)
        
        # Apply stat boosts (temporary or permanent)
        if 'attack_boost' in effects:
            boost = effects['attack_boost']
            current_attack = getattr(player, 'attack', 0)
            player.attack = current_attack + boost
        
        if 'defense_boost' in effects:
            boost = effects['defense_boost']
            current_defense = getattr(player, 'defense', 0)
            player.defense = current_defense + boost
        
        # Learn new lightsaber forms
        if 'learn_form' in effects:
            form_name = effects['learn_form']
            if not hasattr(player, 'known_forms'):
                player.known_forms = ["Shii-Cho"]
            if form_name not in player.known_forms:
                player.known_forms.append(form_name)
                try:
                    game.ui.messages.add(f"You have learned {form_name}!")
                except:
                    pass
            
        # Apply max HP boost
        if 'max_hp_boost' in effects:
            boost = effects['max_hp_boost']
            current_max = getattr(player, 'max_hp', 100)
            player.max_hp = current_max + boost
        
        # Apply title gains
        if 'title_gained' in effects:
            title = effects['title_gained']
            if not hasattr(player, 'titles'):
                player.titles = []
            if title not in player.titles:
                player.titles.append(title)
                try:
                    game.ui.messages.add(f"Title gained: {title}")
                except:
                    pass
        
        # Apply XP bonus
        if 'xp_bonus' in effects:
            xp_gain = effects['xp_bonus']
            if hasattr(player, 'add_xp'):
                player.add_xp(xp_gain)
            else:
                current_xp = getattr(player, 'xp', 0)
                player.xp = current_xp + xp_gain
        
        # Special effect flags
        if 'dark_powers_unlocked' in effects and effects['dark_powers_unlocked']:
            if not hasattr(player, 'dark_powers_unlocked'):
                player.dark_powers_unlocked = True
        
        if 'hybrid_mastery' in effects and effects['hybrid_mastery']:
            if not hasattr(player, 'hybrid_mastery'):
                player.hybrid_mastery = True
                
    except Exception as e:
        try:
            game.ui.messages.add(f"Effect application error: {e}")
        except:
            pass

def _show_hero_journey_journal(game):
    """Display the enhanced hero's journey journal."""
    from jedi_fugitive.game.hero_journal import enhance_existing_journal_system
    try:
        # Initialize or get existing journal system
        journal = enhance_existing_journal_system(game.player)
        # Get journey summary
        summary = journal.generate_journey_summary()
        # Build display based on user choice
        journal_options = [
            "📖 Recent Entries (Last 15)",
            "📚 Full Chronicle by Chapter", 
            "⚡ Character Arc Summary",
            "📊 Journey Statistics",
            "🌟 Story Threads & Milestones",
            "📝 Export/Share Journal",
            "🌅 Prologue",
            "🏁 Epilogue"
        ]
        popup_items = [(opt, "", {}) for opt in journal_options]
        choice = game.ui.popup_dialogue(popup_items, title="HERO'S JOURNEY JOURNAL")
        if choice == 0:  # Recent entries
            _show_recent_entries(game, journal)
        elif choice == 1:  # Full chronicle  
            _show_full_chronicle(game, summary)
        elif choice == 2:  # Character arc
            _show_character_arc(game, summary)
        elif choice == 3:  # Statistics
            _show_journey_statistics(game, summary)
        elif choice == 4:  # Story threads
            _show_story_threads(game, journal)
        elif choice == 5:  # Export/share
            _export_journal(game, journal)
        elif choice == 6:  # Prologue
            _show_prologue(game, journal)
        elif choice == 7:  # Epilogue
            _show_epilogue(game, journal)
    except Exception as e:
        game.ui.messages.add(f"Journal system error: {e}")
def _show_prologue(game, journal):
    """Display a dynamic prologue based on player state."""
    lines = [
        "🌅 PROLOGUE 🌅",
        "",
        "You awaken amidst the wreckage of your ship, the Force swirling with uncertainty.",
        "A world unknown stretches before you, haunted by the shadow of the Sith and the hope of the Jedi.",
        "",
        "Your journey will be shaped by every choice, every victory, every fall...",
        "",
        "Press any key to close..."
    ]
    _show_centered(game, lines, title="Prologue")

def _show_epilogue(game, journal):
    """Display a dynamic epilogue based on current journey state."""
    summary = journal.generate_journey_summary()
    lines = [
        "🏁 EPILOGUE 🏁",
        "",
        summary['epilogue'],
        "",
        "Press any key to close..."
    ]
    _show_centered(game, lines, title="Epilogue")

def _export_journal(game, journal):
    """Export the full journal to a text file for sharing or archiving."""
    import os
    from datetime import datetime
    player = game.player
    summary = journal.generate_journey_summary()
    export_lines = []
    export_lines.append(f"=== {summary['title']} ===\n")
    export_lines.append("Prologue:\n  You awaken amidst the wreckage of your ship...")
    export_lines.append("")
    for chapter_num, entries in summary['chapters'].items():
        export_lines.append(f"--- Chapter {chapter_num} ---")
        for entry in entries:
            turn = entry.get('turn', 0)
            text = entry.get('text', '')
            export_lines.append(f"Turn {turn}: {text}")
        export_lines.append("")
    export_lines.append(f"Epilogue:\n  {summary['epilogue']}")
    export_lines.append("")
    filename = f"journal_export_{getattr(player, 'name', 'player')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(os.getcwd(), filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(export_lines))
        game.ui.messages.add(f"Journal exported to {filename}")
    except Exception as e:
        game.ui.messages.add(f"Export failed: {e}")

def _show_recent_entries(game, journal):
    """Show recent journal entries with enhanced formatting."""
    log = getattr(game.player, 'travel_log', [])
    
    if not log:
        lines = [
            "🌅 THE JOURNEY BEGINS 🌅",
            "",
            "Your ship lies in ruins behind you.",
            "The dark side of this world calls.",
            "Every choice will shape your destiny.",
            "",
            "Will you fall to darkness or rise above it?",
            "",
            "Press any key to close..."
        ]
    else:
        corruption = getattr(game.player, 'corruption', 50)
        alignment = journal.get_alignment_description(corruption)
        lines = [
            f"🌟 {journal.get_story_title()} 🌟",
            f"📊 Current Alignment: {alignment} ({corruption}% corruption)",
            f"⚔️ Chapter {journal.get_chapter_number(journal.current_phase)}: {journal.current_phase.title()}",
            "",
            "═══ RECENT ENTRIES ═══",
            ""
        ]
        # Show last 15 entries with enhanced formatting and basic markdown
        recent_entries = log[-15:]
        for entry in recent_entries:
            turn = entry.get('turn', 0)
            text = entry.get('text', '')
            entry_type = entry.get('type', 'reflection')
            phase = entry.get('phase', 'initiation')
            # Add type icons
            type_icons = {
                'milestone': '[MILE]',
                'combat': '[FIGHT]', 
                'discovery': '[FIND]',
                'reflection': '[THINK]',
                'atmosphere': '[ATMO]',
                'fauna': '[LIFE]',
                'corruption': '[DARK]',
                'victory': '[WIN]',
                'death': '[END]'
            }
            icon = type_icons.get(entry_type, '[NOTE]')
            # Rich formatting: bold for milestones, italics for reflection, etc.
            if entry_type == 'milestone':
                text = f"**{text}**"
            elif entry_type == 'reflection':
                text = f"*{text}*"
            lines.append(f"{icon} Turn {turn}: {text}")
        lines.extend(["", "Press any key to close..."])
    _show_centered(game, lines, title="Recent Chronicle")

def _show_full_chronicle(game, summary):
    """Show the full chronicle organized by chapters."""
    chapters = summary['chapters']
    
    if not chapters:
        lines = ["No chronicle entries found.", "", "Press any key to close..."]
    else:
        lines = [
            f"📚 {summary['title']} 📚",
            "",
            "═══ FULL CHRONICLE ═══",
            ""
        ]
        
        chapter_names = {
            1: "Chapter I: The Crash",
            2: "Chapter II: Trials of Survival", 
            3: "Chapter III: The Transformation",
            4: "Chapter IV: The Final Path"
        }
        
        for chapter_num in sorted(chapters.keys()):
            chapter_entries = chapters[chapter_num]
            chapter_name = chapter_names.get(chapter_num, f"Chapter {chapter_num}")
            
            lines.append(f"📖 {chapter_name}")
            lines.append("─" * 40)
            
            for entry in chapter_entries:
                turn = entry.get('turn', 0)
                text = entry.get('text', '')
                lines.append(f"  Turn {turn}: {text}")
            
            lines.append("")
        
        lines.extend([summary['epilogue'], "", "Press any key to close..."])
    
    _show_centered(game, lines, title="Full Chronicle")

def _show_character_arc(game, summary):
    """Show character development arc."""
    lines = [
        f">>> {summary['title']} <<<",
        "",
        "═══ CHARACTER ARC ═══",
        "",
        summary['character_arc'],
        "",
        "═══ JOURNEY PROGRESSION ═══",
        f"🏆 Trials Faced: {summary['statistics']['trials_faced']}",
        f"⚔️ Enemies Defeated: {summary['statistics']['enemies_defeated']}",
        f"🌟 Major Milestones: {summary['statistics']['major_milestones']}",
        f"📚 Story Threads: {summary['statistics']['story_threads_completed']}/9",
        "",
        "═══ EPILOGUE ═══",
        summary['epilogue'],
        "",
        "Press any key to close..."
    ]
    
    _show_centered(game, lines, title="Character Arc")

def _show_journey_statistics(game, summary):
    """Show detailed journey statistics."""
    corruption = getattr(game.player, 'corruption', 50)
    level = getattr(game.player, 'level', 1)
    turn = getattr(game, 'turn_count', 0)
    
    lines = [
        "📊 JOURNEY STATISTICS 📊",
        "",
        "═══ PROGRESSION ═══",
        f"🎯 Character Level: {level}",
        f"⏰ Turns Survived: {turn}",
        f"📈 Corruption Level: {corruption}%",
        "",
        "═══ EXPERIENCES ═══", 
        f"[TRIALS] Trials Faced: {summary['statistics']['trials_faced']}",
        f"[COMBAT] Battles Won: {summary['statistics']['enemies_defeated']}",
        f"[CORRUPT] Corruption Events: {summary['statistics']['corruption_events']}",
        f"[MILES] Major Milestones: {summary['statistics']['major_milestones']}",
        "",
        "═══ STORY COMPLETION ═══",
        f"[STORY] Story Threads: {summary['statistics']['story_threads_completed']}/9",
        "",
        "Your legend grows with each choice...",
        "",
        "Press any key to close..."
    ]
    
    _show_centered(game, lines, title="Statistics")

def _show_story_threads(game, journal):
    """Show major story threads and their completion status."""
    lines = [
        "🌟 STORY THREADS & MILESTONES 🌟",
        "",
        "═══ MAJOR STORY MOMENTS ═══",
        ""
    ]
    
    thread_descriptions = {
        'master_memory': "[MEMORY] Remember fallen Master",
        'first_kill': "[KILL] First enemy defeated", 
        'dark_temptation': "[DARK] Embrace dark temptation",
        'light_choice': "[LIGHT] Choose the light",
        'tomb_entered': "[TOMB] Enter ancient Sith tomb",
        'artifact_found': "[RELIC] Discover Sith artifact",
        'breaking_point': "[BREAK] Face breaking point",
        'redemption': "[REDEMP] Find redemption",
        'final_trial': "[FINAL] Complete final trial"
    }
    
    for thread_key, description in thread_descriptions.items():
        status = "[DONE]" if journal.story_threads.get(thread_key, False) else "[PENDING]"
        lines.append(f"{status} {description}")
    
    lines.extend([
        "",
        "═══ JOURNEY PHASES ═══",
        f"📍 Current Phase: {journal.current_phase.title()}",
        f"🎭 Trials Faced: {journal.trials_faced}",
        f"💀 Enemies Defeated: {journal.enemies_defeated}",
        "",
        "Your destiny unfolds with each step...",
        "",
        "Press any key to close..."
    ])
    
    _show_centered(game, lines, title="Story Progress")


def _show_meditation_menu(game):
    """Enhanced meditation menu with rituals"""
    try:
        menu_options = [
            "1. Meditate (Restore Force Energy)",
            "2. Perform Ritual",
            "3. Review Past Ceremonies", 
            "4. Cancel"
        ]
        
        # Add message to the menu options instead
        full_menu = [
            "Focus your mind and connect with the Force...",
            "",
            "1. Meditate (Restore Force Energy)",
            "2. Perform Ritual", 
            "3. Review Past Ceremonies",
            "4. Cancel"
        ]
        
        choice = game.ui.centered_menu(
            full_menu,
            title="Meditation & Rituals"
        )
        
        # Adjust choice index since we added header lines
        if choice >= 2:
            choice = choice - 2
        
        if choice == 0:  # Regular meditation
            _handle_meditation(game)
        elif choice == 1:  # Perform ritual
            _show_ritual_menu(game)
        elif choice == 2:  # Review ceremonies
            _show_ceremony_history(game)
    except Exception as e:
        try:
            game.ui.messages.add(f"Meditation menu error: {e}")
        except Exception:
            pass


def _handle_meditation(game):
    """Handle basic meditation"""
    try:
        acted = False
        if hasattr(game, 'meditate') and callable(game.meditate):
            acted = game.meditate()
        else:
            # Fallback meditation
            game.player.force_energy = min(getattr(game.player, 'max_force_energy', 100), 
                                         getattr(game.player, 'force_energy', 0) + 20)
            acted = True
            
        if acted:
            # consume a turn and tick effects
            try:
                game.turn_count = getattr(game, 'turn_count', 0) + 1
                if hasattr(game, '_tick_effects') and callable(game._tick_effects):
                    game._tick_effects()
            except Exception:
                pass
            try: 
                game.ui.messages.add("You take a moment to meditate and restore your Force energy.")
            except Exception as e2:
                if log:
                    log.exception("Error in _fire_gun: add log entry (fail 5)", exc_info=e2)
    except Exception as e:
        try:
            game.ui.messages.add(f"Meditation failed: {e}")
        except Exception:
            pass


def _show_ritual_menu(game):
    """Show available rituals based on location and player state"""
    try:
        from jedi_fugitive.game.rituals import get_available_rituals
        
        # Get player corruption level
        corruption = getattr(game.player, 'corruption', 50)
        location = _get_current_location(game)
        level = getattr(game.player, 'level', 1)
        tombs_completed = getattr(game.player, 'tombs_cleared', 0)
        
        # Get available rituals
        available_rituals = get_available_rituals(
            corruption_level=corruption,
            location=location,
            level=level,
            tombs_completed=tombs_completed
        )
        
        if not available_rituals:
            try:
                game.ui.messages.add("No rituals are available at this location or time.")
            except Exception:
                pass
            return False  # No turn consumed
        
        # Create ritual options - available_rituals returns tuples of (category, ritual_id, ritual_data)
        ritual_options = []
        for i, (category, ritual_id, ritual_data) in enumerate(available_rituals):
            ritual_name = ritual_data.get('name', f'Ritual {i+1}')
            ritual_options.append(f"{i+1}. {ritual_name}")
        ritual_options.append(f"{len(ritual_options)+1}. Cancel")
        
        choice = game.ui.centered_menu(
            ritual_options,
            title="Available Rituals"
        )
        
        if choice is not None and choice < len(available_rituals):
            category, ritual_id, ritual_data = available_rituals[choice]
            _perform_ritual(game, category, ritual_id, ritual_data)
    except Exception as e:
        try:
            game.ui.messages.add(f"Ritual menu error: {e}")
        except Exception:
            pass


def _perform_ritual(game, category, ritual_id, ritual_data):
    """Perform the selected ritual"""
    try:
        from jedi_fugitive.game.rituals import perform_ritual
        
        # Show ritual description first
        description = ritual_data.get('description', [])
        if description:
            try:
                game.ui.centered_menu(
                    description + ["", "Press any key to perform this ritual..."],
                    title=ritual_data.get('name', 'Ritual')
                )
            except Exception:
                pass
        
        # Perform the ritual using the existing function
        result = perform_ritual(category, ritual_id, game.player, game)
        
        if isinstance(result, str):
            # Success - result is a message
            try:
                game.ui.messages.add(result)
            except Exception:
                pass
            
            # Record ceremony in player history
            if not hasattr(game.player, 'ceremonies_performed'):
                game.player.ceremonies_performed = []
            
            ceremony_record = {
                'name': ritual_data.get('name', 'Unknown Ritual'),
                'turn': getattr(game, 'turn_count', 0),
                'location': _get_current_location(game),
                'corruption_at_time': getattr(game.player, 'corruption', 50)
            }
            game.player.ceremonies_performed.append(ceremony_record)
            
            # Consume a turn
            try:
                game.turn_count = getattr(game, 'turn_count', 0) + 1
                if hasattr(game, '_tick_effects') and callable(game._tick_effects):
                    game._tick_effects()
            except Exception:
                pass
            
        else:
            # Failed - result might be an error message or False
            error_msg = "Ritual failed for unknown reasons."
            if isinstance(result, dict) and 'error' in result:
                error_msg = result['error']
            elif isinstance(result, str):
                error_msg = result
                
            try:
                game.ui.messages.add(error_msg)
            except Exception:
                pass
                
    except Exception as e:
        try:
            game.ui.messages.add(f"Ritual performance failed: {e}")
        except Exception:
            pass


def _show_ceremony_history(game):
    """Show history of performed ceremonies"""
    try:
        ceremonies = getattr(game.player, 'ceremonies_performed', [])
        
        if not ceremonies:
            try:
                game.ui.messages.add("You have not performed any ceremonies yet.")
            except Exception:
                pass
            return False  # No turn consumed
        
        history_lines = ["═══ CEREMONY HISTORY ═══", ""]
        for ceremony in ceremonies[-10:]:  # Show last 10 ceremonies
            name = ceremony.get('name', 'Unknown')
            turn = ceremony.get('turn', 0)
            location = ceremony.get('location', 'Unknown')
            corruption = ceremony.get('corruption_at_time', 50)
            
            history_lines.append(f"• {name}")
            history_lines.append(f"  Location: {location}, Turn: {turn}")
            history_lines.append(f"  Corruption at time: {corruption}%")
            history_lines.append("")
        
        history_lines.append("Press any key to close...")
        
        try:
            game.ui.centered_menu(
                history_lines,
                title="Ceremony History"
            )
        except Exception:
            pass
    except Exception:
        pass

def _show_controls_popup(game):
    """Show detailed controls popup menu."""
    try:
        controls = [
            "DARK MERIDIAN - COMPLETE CONTROLS",
            "",
            "MOVEMENT (8-Directional):",
            "  h/← = West        l/→ = East",
            "  j/↓ = South       k/↑ = North", 
            "  y   = Northwest   u   = Northeast",
            "  b   = Southwest   n   = Southeast",
            "  7,9,1,3 = Numpad diagonal movement",
            "",
            "COMBAT & ACTIONS:",
            "  Space = Attack/Confirm targeting",
            "  F     = Force abilities menu",
            "  G     = Throw grenade (if available)",
            "  z     = Use item from inventory",
            "  ESC/c = Cancel action/targeting",
            "",
            "INTERACTION:",
            "  g = Pick up items",
            "  t = Talk to NPCs", 
            "  i = Open inventory",
            "  m = Meditate & perform rituals",
            "",
            "EQUIPMENT:",
            "  e = Equip/unequip items",
            "  w = Wield weapon",
            "  A = Unequip armor",
            "  r/R = Drop item",
            "",
            "INTERFACE:",
            "  ? = Help screen",
            "  C = This controls menu",
            "  L = Token legend & color guide",
            "  M = Toggle map display",
            "  v = Sith Codex (lore & discoveries)",
            "  p = Toggle popup messages", 
            "  x = Examine surroundings",
            "",
            "SPECIAL ABILITIES:",
            "  1-5 = Interact with numbered creatures",
            "  P   = Force Push/Pull (if learned)",
            "  S   = Force Sense (if learned)",
            "",
            "TOKEN COLORS (Press L for detailed legend):",
            "  #red#Red#0#     = Weapons & combat items",
            "  #blue#Blue#0#    = Armor & defensive equipment", 
            "  #green#Green#0#   = Consumables & healing items",
            "  #yellow#Yellow#0#  = Tools & utility items",
            "  #white#White#0#   = Common crafting materials",
            "  #cyan#Cyan#0#    = Lightsabers & rare materials",
            "  #magenta#Magenta#0# = Quest items & legendary materials",
        ]
        
        game.ui.centered_menu(controls, title="Complete Controls")
        
    except Exception as e:
        try:
            game.ui.messages.add(f"Controls menu error: {e}")
        except Exception:
            pass
        except Exception:
            pass
            
    except Exception as e:
        try:
            game.ui.messages.add(f"Failed to show ceremony history: {e}")
        except Exception:
            pass


def _get_current_location(game):
    """Get current location type for ritual availability"""
    try:
        if getattr(game, 'tomb_floor', None) is not None:
            return 'tomb'
        
        # Check for meditation shrine nearby
        px = getattr(game.player, 'x', 0)
        py = getattr(game.player, 'y', 0)
        
        if hasattr(game, 'game_map') and game.game_map:
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    check_x, check_y = px + dx, py + dy
                    if (0 <= check_y < len(game.game_map) and 
                        0 <= check_x < len(game.game_map[0]) and
                        game.game_map[check_y][check_x] == '?'):
                        return 'meditation_shrine'
        
        return 'wilderness'
    except Exception:
        return 'wilderness'


def _show_npc_interaction_popup(game, npc):
    """Show NPC interaction menu"""
    try:
        # Get available interactions for this NPC
        if hasattr(npc, 'get_available_interactions'):
            options = npc.get_available_interactions(game.player)
        else:
            # Fallback for NPCs without this method
            options = ["Talk", "Trade"] if hasattr(npc, 'inventory') else ["Talk"]
        
        if not options:
            try:
                game.ui.messages.add(f"{npc.name} has nothing to discuss right now.")
            except Exception:
                pass
            return False  # No turn consumed
        
        # Create menu options
        menu_options = [f"{i+1}. {option}" for i, option in enumerate(options)]
        menu_options.append(f"{len(options)+1}. Leave")
        
        # Show interaction popup
        try:
            # Get greeting safely
            if hasattr(npc, 'get_greeting'):
                try:
                    greeting = npc.get_greeting(game.player)
                except TypeError:
                    greeting = npc.get_greeting()
            else:
                greeting = f"Hello, traveler."
            description = getattr(npc, 'description', f"You meet {getattr(npc, 'name', 'someone')}.")
            
            choice = game.ui.centered_menu(
                menu_options,
                title=f"Interact with {getattr(npc, 'name', 'NPC')}"
            )
            
            if choice is not None and choice < len(options):
                # Handle the interaction
                if hasattr(npc, 'handle_interaction'):
                    result = npc.handle_interaction(choice, game.player)
                    if result:
                        try:
                            game.ui.messages.add(result)
                        except Exception:
                            pass
                else:
                    # Fallback interaction
                    try:
                        game.ui.messages.add(f"{getattr(npc, 'name', 'NPC')}: {greeting}")
                    except Exception:
                        pass
        except Exception as e:
            try:
                game.ui.messages.add(f"Interaction error: {e}")
            except Exception:
                pass
                
    except Exception as e:
        try:
            game.ui.messages.add(f"NPC interaction failed: {e}")
        except Exception:
            pass


def _show_token_legend(game):
    """Show organized token legend with categories and colors."""
    try:
        from jedi_fugitive.items.tokens import get_token_color_legend, TOKEN_CATEGORIES, TOKEN_MAP
        
        legend_lines = [
            "DARK MERIDIAN - TOKEN LEGEND",
            "═" * 50,
            "",
            "Token Categories & Colors:",
            ""
        ]
        
        # Add category legend
        for cat_name, cat_data in TOKEN_CATEGORIES.items():
            color = cat_data['color']
            symbols = cat_data['symbols'][:8] + ('...' if len(cat_data['symbols']) > 8 else '')
            desc = cat_data['description']
            formatted_name = cat_name.replace('_', ' ').title()
            legend_lines.append(f"#{color}#{symbols}#0# - {formatted_name}: {desc}")
        
        legend_lines.extend([
            "",
            "Examples by Category:",
            "─" * 30,
        ])
        
        # Show examples of each category
        categories_shown = set()
        for token, data in sorted(TOKEN_MAP.items()):
            category = data.get('category', data.get('type', 'misc'))
            if category not in categories_shown and len(categories_shown) < 6:
                color = data.get('color', 'white')
                name = data.get('name', 'Unknown')
                token_char = data.get('token', '?')
                legend_lines.append(f"#{color}#{token_char}#0# = {name}")
                categories_shown.add(category)
        
        legend_lines.extend([
            "",
            "Navigation:",
            "─" * 15,
            "Arrow keys or hjkl = Move",
            "Diagonals: y,u,b,n or numpad", 
            "Enter/Space = Pick up item",
            "i = Inspect item details",
            "L = This legend menu",
            "",
            "Press any key to close..."
        ])
        
        game.ui.centered_menu(legend_lines, title="Token Color Guide")
        
    except Exception as e:
        try:
            game.ui.messages.add(f"Token legend error: {e}")
        except Exception:
            pass


# Add registered command processing to handle_input at the very end
def _process_registered_commands(game, key):
    """Process commands registered via game.register_command()"""
    try:
        if hasattr(game, 'key_bindings') and game.key_bindings:
            key_char = chr(key) if 32 <= key <= 126 else None
            if key_char and key_char in game.key_bindings:
                try:
                    handler = game.key_bindings[key_char]
                    if callable(handler):
                        handler()
                        return True
                except Exception as e:
                    try:
                        game.ui.messages.add(f"Command '{key_char}' error: {e}")
                    except Exception:
                        pass
    except Exception:
        pass
    return False