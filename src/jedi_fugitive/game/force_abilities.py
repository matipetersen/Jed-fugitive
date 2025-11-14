from typing import Any

class ForceAbility:
    """Base class for simple force abilities (non-destructive, minimal API)."""
    name = "ForceAbility"
    base_cost = 1
    target_type = "self"  # "self" or "enemy"
    description = ""
    alignment = "neutral"  # "light", "dark", or "neutral"
    
    def get_actual_cost(self, user):
        """Calculate actual Force cost based on player alignment and mastery.
        
        Args:
            user: Player object
            
        Returns:
            int: Actual Force cost after alignment modifiers
        """
        # Get base cost (with stress multiplier for compatibility)
        try:
            import math
            base = int(math.ceil(self.base_cost * getattr(user, 'get_force_cost_multiplier', lambda: 1.0)()))
        except Exception:
            base = self.base_cost
        
        # Apply alignment cost modifier
        if hasattr(user, 'get_ability_cost_multiplier'):
            multiplier = user.get_ability_cost_multiplier(self.alignment)
            return int(math.ceil(base * multiplier))
        
        return base
    
    def get_power_scale(self, user):
        """Calculate power scaling based on alignment mastery.
        
        Args:
            user: Player object
            
        Returns:
            float: Power multiplier (0.5 to 1.5)
        """
        if hasattr(user, 'get_ability_power_scale'):
            return user.get_ability_power_scale(self.alignment)
        return 1.0

    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0) -> bool:
        """Perform the ability. Return True on success, False otherwise."""
        return False

class ForcePushPull(ForceAbility):
    name = "Push/Pull"
    base_cost = 1
    target_type = "enemy"
    description = "Push or pull a nearby enemy up to a few tiles (player uses wrapper physics)."

    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0, **kwargs) -> bool:
        """
        Deduct cost and validate a target exists.

        This method intentionally does not perform the positional movement when called
        with coordinate-like targets from the player's ability wrapper. The weaponized
        push/pull physics is applied by the caller (see abilities.use_force_ability) which
        knows how to move actors multiple tiles and handle blocking.

        If an actual actor object is provided as `target` this method will still only
        consume the resource and return True (movement left to caller).
        """
        # factor player's stress into force cost
        try:
            import math
            cost = int(math.ceil(self.base_cost * getattr(user, 'get_force_cost_multiplier', lambda: 1.0)()))
        except Exception:
            cost = self.base_cost
        if getattr(user, "force_points", 0) < cost:
            if messages is not None:
                try: messages.add("Not enough force points.")
                except Exception: pass
            return False
        try:
            user.force_points = getattr(user, "force_points", 0) - cost
        except Exception:
            pass

        # support both actor targets and coordinate targets (tuple/list)
        # when coordinates are given, the caller should have passed 'game' in kwargs
        if target is None:
            if messages is not None:
                try: messages.add("No target for Push/Pull.")
                except Exception: pass
            return False

        # if coords were provided, try to resolve actor at location
        if isinstance(target, (tuple, list)):
            gx = kwargs.get('game', None)
            if gx is None:
                if messages is not None:
                    try: messages.add("No game context to resolve target location for Push/Pull.")
                    except Exception: pass
                return False
            try:
                tx, ty = int(target[0]), int(target[1])
                found = None
                for e in getattr(gx, 'enemies', []) or []:
                    try:
                        if getattr(e, 'is_alive', lambda: False)() and getattr(e, 'x', -999) == tx and getattr(e, 'y', -999) == ty:
                            found = e; break
                    except Exception:
                        continue
                if found is None:
                    if messages is not None:
                        try: messages.add("No valid target at that location to move.")
                        except Exception: pass
                    return False
                # valid target found; consume cost already done, let caller handle actual movement
                return True
            except Exception:
                if messages is not None:
                    try: messages.add("Invalid target coordinates for Push/Pull.")
                    except Exception: pass
                return False

        # if an actor-like object is provided, just validate it appears alive
        try:
            if hasattr(target, 'is_alive') and callable(getattr(target, 'is_alive')) and not target.is_alive():
                if messages is not None:
                    try: messages.add("Target is not alive.")
                    except Exception: pass
                return False
        except Exception:
            pass

        # resource consumed and target looks valid; actual positional movement left to caller
        return True

class ForceReveal(ForceAbility):
    name = "Reveal"
    base_cost = 1
    target_type = "self"
    description = "Expand your field of view for a short time."

    def __init__(self, duration: int = 8, bonus: int = 4):
        self.duration = duration
        self.bonus = bonus

    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0) -> bool:
        try:
            import math
            cost = int(math.ceil(self.base_cost * getattr(user, 'get_force_cost_multiplier', lambda: 1.0)()))
        except Exception:
            cost = self.base_cost
        fp = getattr(user, "force_points", 0)
        if fp < cost:
            if messages is not None:
                try: messages.add("Not enough force points.")
                except Exception: pass
            return False
        try:
            user.force_points = fp - cost
        except Exception:
            pass
        # set duration (turns) and bonus radius so visibility code can use it
        user.los_bonus_turns = getattr(user, "los_bonus_turns", 0) + int(self.duration)
        # store the extra radius provided by this reveal (multiple reveals stack by taking max)
        try:
            user.los_bonus_radius = max(int(getattr(user, 'los_bonus_radius', 0) or 0), int(self.bonus))
        except Exception:
            try: user.los_bonus_radius = int(self.bonus)
            except Exception: user.los_bonus_radius = 0
        if messages is not None:
            try:
                messages.add(f"Force: Reveal activated (+{self.bonus} LOS for {self.duration} turns).")
            except Exception:
                pass
        # light-side action reduces stress modestly
        try:
            if hasattr(user, 'reduce_stress'):
                # Increased from 5 to 10 for more meaningful stress relief
                user.reduce_stress(10)
        except Exception:
            pass
        return True


class ForceHeal(ForceAbility):
    name = "Heal"
    base_cost = 1
    target_type = "self"
    description = "Restore a small amount of HP to the user."

    def __init__(self, amount: int = 8):
        self.amount = amount

    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0) -> bool:
        try:
            import math
            cost = int(math.ceil(self.base_cost * getattr(user, 'get_force_cost_multiplier', lambda: 1.0)()))
        except Exception:
            cost = self.base_cost
        fp = getattr(user, "force_points", 0)
        if fp < cost:
            if messages is not None:
                try: messages.add("Not enough force points.")
                except Exception: pass
            return False
        try:
            user.force_points = fp - cost
        except Exception:
            pass
        try:
            user.hp = min(getattr(user, "max_hp", getattr(user, "hp", 0)), getattr(user, "hp", 0) + int(self.amount))
            if messages is not None:
                try: messages.add(f"Force: Heal restored {self.amount} HP.")
                except Exception: pass
            # light-side reduces stress
            try:
                if hasattr(user, 'reduce_stress'):
                    # Increased from 5 to 10 for more meaningful stress relief
                    user.reduce_stress(10)
            except Exception:
                pass
            return True
        except Exception:
            return False


class ForceLightning(ForceAbility):
    name = "Lightning"
    base_cost = 2
    target_type = "enemy"
    description = "Strike a visible enemy in a straight line for damage."

    def __init__(self, damage: int = 10):
        self.damage = damage

    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0) -> bool:
        try:
            import math
            cost = int(math.ceil(self.base_cost * getattr(user, 'get_force_cost_multiplier', lambda: 1.0)()))
        except Exception:
            cost = self.base_cost
        fp = getattr(user, "force_points", 0)
        if fp < cost:
            if messages is not None:
                try: messages.add("Not enough force points.")
                except Exception: pass
            return False
        try:
            user.force_points = fp - cost
        except Exception:
            pass
        # target expected to be an actor object
        try:
            if not target:
                if messages is not None:
                    try: messages.add("No target for Lightning.")
                    except Exception: pass
                return False
            # apply damage
            if hasattr(target, 'take_damage'):
                try:
                    player_rank = getattr(user, 'level', 0)
                    base_dmg = int(self.damage + (player_rank if player_rank else 0))
                    # dark-side empowered when stressed >50
                    try:
                        if getattr(self, 'is_dark', False) and getattr(user, 'stress', 0) > 50:
                            base_dmg = int(base_dmg * 1.15)
                    except Exception:
                        pass
                    dmg = int(base_dmg)
                    target.take_damage(dmg)
                    if messages is not None:
                        try: messages.add(f"Force: Lightning deals {dmg} damage to {getattr(target,'name', 'the target')}.")
                        except Exception: pass
                    # dark-side costs stress; light-side reduces stress
                    try:
                        if getattr(self, 'is_dark', False) and hasattr(user, 'add_stress'):
                            user.add_stress(10, source='dark_ability')
                        else:
                            if hasattr(user, 'reduce_stress'):
                                user.reduce_stress(5)
                    except Exception:
                        pass
                    return True
                except Exception:
                    pass
        except Exception:
            pass
        if messages is not None:
            try: messages.add("Lightning failed.")
            except Exception: pass
        return False

# ==============================
# PHASE 1 NEW ABILITIES
# ==============================

class ForceProtect(ForceAbility):
    name = "Protect"
    base_cost = 15
    target_type = "self"
    description = "Shield yourself with the Force, gaining bonus defense for several turns."
    alignment = "light"
    
    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0) -> bool:
        """Grant temporary defense bonus."""
        actual_cost = self.get_actual_cost(user)
        power_scale = self.get_power_scale(user)
        
        # Check Force energy (use force_energy if available, fallback to force_points)
        force_available = getattr(user, 'force_energy', getattr(user, 'force_points', 0) * 50)
        if force_available < actual_cost:
            if messages:
                try: messages.add("Not enough Force energy.")
                except: pass
            return False
        
        # Deduct cost
        if hasattr(user, 'force_energy'):
            user.force_energy -= actual_cost
        else:
            user.force_points = max(0, getattr(user, 'force_points', 0) - (actual_cost // 50))
        
        # Calculate defense bonus (3-5 defense for 4-5 turns based on power scale)
        defense_bonus = int((3 + player_rank) * power_scale)
        duration = 4 + min(player_rank, 1)
        
        # Apply buff
        try:
            if hasattr(user, 'add_buff'):
                user.add_buff('defense', defense_bonus, duration)
            else:
                user.defense = getattr(user, 'defense', 0) + defense_bonus
            
            if messages:
                try: messages.add(f"A Force shield surrounds you! (+{defense_bonus} defense for {duration} turns)")
                except: pass
            
            # Light side reduces stress
            if hasattr(user, 'reduce_stress'):
                user.reduce_stress(5)
            
            return True
        except Exception:
            if messages:
                try: messages.add("Protect failed.")
                except: pass
            return False

class ForceMeditation(ForceAbility):
    name = "Meditation"
    base_cost = 0
    target_type = "self"
    description = "Meditate to restore Force energy, HP, and reduce stress. Risk: May attract enemies! Cannot be used in combat."
    alignment = "light"
    
    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0) -> bool:
        """Restore Force, heal HP, and reduce stress. Risk of spawning enemies."""
        import random
        
        # Check if in combat (if player has is_in_combat method)
        if hasattr(user, 'is_in_combat') and user.is_in_combat():
            if messages:
                try: messages.add("Cannot meditate during combat!")
                except: pass
            return False
        
        power_scale = self.get_power_scale(user)
        
        # Restore Force energy (20 base + mastery scaling)
        restore_amount = int(20 * power_scale)
        if hasattr(user, 'force_energy'):
            old_energy = user.force_energy
            user.force_energy = min(user.max_force_energy, user.force_energy + restore_amount)
            actual_restored = user.force_energy - old_energy
        else:
            actual_restored = restore_amount
            user.force_points = min(10, getattr(user, 'force_points', 0) + (restore_amount // 50))
        
        # Reduce stress (15 base + mastery scaling)
        stress_reduction = int(15 * power_scale)
        if hasattr(user, 'reduce_stress'):
            user.reduce_stress(stress_reduction)
        
        # NEW: Heal HP (scaled by alignment - Light Side heals more)
        # Light Side (low corruption): 15-25% max HP
        # Balanced: 10-15% max HP
        # Dark Side (high corruption): 5-10% max HP (harder to find peace)
        if hasattr(user, 'hp') and hasattr(user, 'max_hp'):
            corruption = getattr(user, 'alignment_score', 50)
            
            if corruption <= 20:  # Pure Light
                heal_percent = random.uniform(0.20, 0.30)
            elif corruption <= 40:  # Light
                heal_percent = random.uniform(0.15, 0.25)
            elif corruption <= 59:  # Balanced
                heal_percent = random.uniform(0.10, 0.15)
            elif corruption <= 79:  # Dark
                heal_percent = random.uniform(0.05, 0.10)
            else:  # Pure Dark
                heal_percent = random.uniform(0.03, 0.08)
            
            heal_amount = int(user.max_hp * heal_percent)
            old_hp = user.hp
            user.hp = min(user.max_hp, user.hp + heal_amount)
            actual_healed = user.hp - old_hp
        else:
            actual_healed = 0
        
        # NEW: Risk of attracting enemies (30% base chance)
        # Higher corruption = more likely to attract (dark presence disturbs the area)
        base_spawn_chance = 0.30
        corruption_modifier = getattr(user, 'alignment_score', 50) / 200.0  # 0.0 to 0.5
        spawn_chance = base_spawn_chance + corruption_modifier
        
        enemies_spawned = 0
        spawn_messages = []
        
        if random.random() < spawn_chance:
            # Spawn 1-3 enemies nearby
            num_enemies = random.randint(1, 3)
            
            # Try to spawn enemies near player
            if hasattr(user, 'x') and hasattr(user, 'y') and game_map:
                from jedi_fugitive.game.enemy import Enemy
                try:
                    # Get game manager to properly spawn enemies
                    game_manager = getattr(user, 'game_manager', None)
                    if not game_manager:
                        # Try to find it from messages object
                        if hasattr(messages, 'game'):
                            game_manager = messages.game
                    
                    for _ in range(num_enemies):
                        # Find valid spawn location near player (3-5 tiles away)
                        attempts = 0
                        spawned = False
                        while attempts < 20 and not spawned:
                            offset_x = random.randint(-5, 5)
                            offset_y = random.randint(-5, 5)
                            spawn_x = user.x + offset_x
                            spawn_y = user.y + offset_y
                            
                            # Check if location is valid
                            distance = abs(offset_x) + abs(offset_y)
                            if distance >= 3 and distance <= 5:
                                # Check walkable
                                if game_manager and hasattr(game_manager, 'is_walkable'):
                                    if game_manager.is_walkable(spawn_x, spawn_y):
                                        # Spawn appropriate enemy based on location
                                        if hasattr(game_manager, 'spawn_surface_enemy'):
                                            game_manager.spawn_surface_enemy(spawn_x, spawn_y)
                                            enemies_spawned += 1
                                            spawned = True
                            attempts += 1
                except Exception as e:
                    # Silently fail if spawning doesn't work
                    pass
            
            if enemies_spawned > 0:
                spawn_messages.append(f"Your meditation disturbed something... {enemies_spawned} {'enemy' if enemies_spawned == 1 else 'enemies'} approach!")
        
        # Build message
        if messages:
            try:
                msg_parts = [f"You meditate deeply... (+{actual_restored} Force"]
                if actual_healed > 0:
                    msg_parts.append(f"+{actual_healed} HP")
                msg_parts.append(f"-{stress_reduction} stress)")
                messages.add(" ".join(msg_parts))
                
                for spawn_msg in spawn_messages:
                    messages.add(spawn_msg)
            except: pass
        
        return True

class ForceChoke(ForceAbility):
    name = "Choke"
    base_cost = 20
    target_type = "enemy"
    description = "Crush an enemy's throat with the Force, dealing damage and stunning them."
    alignment = "dark"
    
    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0) -> bool:
        """Damage and stun target."""
        actual_cost = self.get_actual_cost(user)
        power_scale = self.get_power_scale(user)
        
        # Check Force energy
        force_available = getattr(user, 'force_energy', getattr(user, 'force_points', 0) * 50)
        if force_available < actual_cost:
            if messages:
                try: messages.add("Not enough Force energy.")
                except: pass
            return False
        
        if target is None:
            if messages:
                try: messages.add("No target to choke.")
                except: pass
            return False
        
        # Deduct cost
        if hasattr(user, 'force_energy'):
            user.force_energy -= actual_cost
        else:
            user.force_points = max(0, getattr(user, 'force_points', 0) - (actual_cost // 50))
        
        # Calculate damage (12 base + mastery scaling)
        damage = int(12 * power_scale)
        
        try:
            target.take_damage(damage)
            
            # Apply stun for 1 turn
            if hasattr(target, 'add_debuff'):
                target.add_debuff('stun', 1, 1)
            
            target_name = getattr(target, 'name', 'the enemy')
            if messages:
                try: messages.add(f"You choke {target_name} with the Force! ({damage} damage, stunned)")
                except: pass
            
            # Dark side increases stress
            if hasattr(user, 'add_stress'):
                user.add_stress(10, source='dark_ability')
            
            return True
        except Exception:
            if messages:
                try: messages.add("Choke failed.")
                except: pass
            return False

class ForceDrain(ForceAbility):
    name = "Drain"
    base_cost = 18
    target_type = "enemy"
    description = "Drain life force from an enemy, healing yourself."
    alignment = "dark"
    
    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0) -> bool:
        """Damage target and heal user."""
        actual_cost = self.get_actual_cost(user)
        power_scale = self.get_power_scale(user)
        
        # Check Force energy
        force_available = getattr(user, 'force_energy', getattr(user, 'force_points', 0) * 50)
        if force_available < actual_cost:
            if messages:
                try: messages.add("Not enough Force energy.")
                except: pass
            return False
        
        if target is None:
            if messages:
                try: messages.add("No target to drain.")
                except: pass
            return False
        
        # Deduct cost
        if hasattr(user, 'force_energy'):
            user.force_energy -= actual_cost
        else:
            user.force_points = max(0, getattr(user, 'force_points', 0) - (actual_cost // 50))
        
        # Calculate drain amount (10 base + mastery scaling)
        drain_amount = int(10 * power_scale)
        
        try:
            target.take_damage(drain_amount)
            
            # Heal user
            if hasattr(user, 'heal'):
                user.heal(drain_amount)
            else:
                user.hp = min(getattr(user, 'max_hp', 100), getattr(user, 'hp', 50) + drain_amount)
            
            target_name = getattr(target, 'name', 'the enemy')
            if messages:
                try: messages.add(f"You drain life from {target_name}! ({drain_amount} damage, +{drain_amount} HP)")
                except: pass
            
            # Dark side increases stress
            if hasattr(user, 'add_stress'):
                user.add_stress(8, source='dark_ability')
            
            return True
        except Exception:
            if messages:
                try: messages.add("Drain failed.")
                except: pass
            return False

class ForceFear(ForceAbility):
    name = "Fear"
    base_cost = 25
    target_type = "enemy"
    description = "Project terror into enemy minds, causing them to flee."
    alignment = "dark"
    
    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0) -> bool:
        """Make enemies flee."""
        actual_cost = self.get_actual_cost(user)
        power_scale = self.get_power_scale(user)
        
        # Check Force energy
        force_available = getattr(user, 'force_energy', getattr(user, 'force_points', 0) * 50)
        if force_available < actual_cost:
            if messages:
                try: messages.add("Not enough Force energy.")
                except: pass
            return False
        
        # Deduct cost
        if hasattr(user, 'force_energy'):
            user.force_energy -= actual_cost
        else:
            user.force_points = max(0, getattr(user, 'force_points', 0) - (actual_cost // 50))
        
        # Calculate duration (3 base turns)
        duration = 3
        
        try:
            # Apply fear to all visible enemies
            affected_count = 0
            if game_map and hasattr(game_map, 'actors'):
                for actor in game_map.actors:
                    if actor != user and hasattr(actor, 'ai'):
                        if hasattr(actor, 'add_debuff'):
                            actor.add_debuff('fear', duration, duration)
                        affected_count += 1
            
            if messages:
                if affected_count > 0:
                    try: messages.add(f"Dark terror grips your enemies! ({affected_count} enemies fleeing)")
                    except: pass
                else:
                    try: messages.add("No enemies to terrify.")
                    except: pass
            
            # Dark side increases stress significantly
            if hasattr(user, 'add_stress'):
                user.add_stress(15, source='dark_ability')
            
            return affected_count > 0
        except Exception:
            if messages:
                try: messages.add("Fear failed.")
                except: pass
            return False

# ensure FORCE_ABILITIES exists and append these abilities non-destructively
try:
    FORCE_ABILITIES
except NameError:
    FORCE_ABILITIES = []

# append instances if not already present (avoid duplicates)
_has = {type(a).__name__ for a in FORCE_ABILITIES}
if "ForcePushPull" not in _has:
    FORCE_ABILITIES.append(ForcePushPull())
if "ForceReveal" not in _has:
    FORCE_ABILITIES.append(ForceReveal())
if "ForceHeal" not in _has:
    FORCE_ABILITIES.append(ForceHeal())
if "ForceLightning" not in _has:
    FORCE_ABILITIES.append(ForceLightning())
# Phase 1 new abilities
if "ForceProtect" not in _has:
    FORCE_ABILITIES.append(ForceProtect())
if "ForceMeditation" not in _has:
    FORCE_ABILITIES.append(ForceMeditation())
if "ForceChoke" not in _has:
    FORCE_ABILITIES.append(ForceChoke())
if "ForceDrain" not in _has:
    FORCE_ABILITIES.append(ForceDrain())
if "ForceFear" not in _has:
    FORCE_ABILITIES.append(ForceFear())