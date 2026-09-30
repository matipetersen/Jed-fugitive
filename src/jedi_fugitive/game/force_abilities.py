from typing import Any

# Initialize FORCE_ABILITIES list at module level to avoid NameError
FORCE_ABILITIES = []

# Force Energy System Helpers (Phase 4: Standardization)
def get_force_energy(user):
    """Get current Force energy, with fallback to legacy force_points"""
    return getattr(user, 'force_energy', getattr(user, 'force_points', 0) * 50)

def get_max_force_energy(user):
    """Get max Force energy"""
    return getattr(user, 'max_force_energy', 100)

def consume_force_energy(user, amount):
    """Consume Force energy, updating both new and legacy systems"""
    current = get_force_energy(user)
    if current < amount:
        return False
    
    # Update force_energy system
    user.force_energy = current - amount
    
    # Update legacy force_points for compatibility (50 energy = 1 point)
    user.force_points = max(0, user.force_energy // 50)
    
    return True

def restore_force_energy(user, amount):
    """Restore Force energy, capped at maximum"""
    current = get_force_energy(user)
    max_energy = get_max_force_energy(user)
    
    user.force_energy = min(max_energy, current + amount)
    user.force_points = user.force_energy // 50  # Keep legacy in sync

class ForceAbility:
    """Base class for simple force abilities (non-destructive, minimal API)."""
    name = "ForceAbility"
    base_cost = 1
    target_type = "self"  # "self" or "enemy"
    description = ""
    alignment = "neutral"  # "light", "dark", or "neutral"
    
    def __init__(self):
        # Abilities start locked by default and must be explicitly unlocked
        self.unlocked = False
    
    def is_unlocked(self):
        """Check if this ability is unlocked and available for use."""
        return getattr(self, 'unlocked', False)
    
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
        
        # Skill-tree efficiency
        try:
            from jedi_fugitive.game import jedi_skills
            base = base * jedi_skills.force_cost_multiplier(user)
            from jedi_fugitive.game import form_combat
            base = base * form_combat.force_cost_multiplier(user)
        except Exception:
            pass

        # Apply alignment cost modifier
        if hasattr(user, 'get_ability_cost_multiplier'):
            multiplier = user.get_ability_cost_multiplier(self.alignment)
            return max(1, int(math.ceil(base * multiplier))) if self.base_cost > 0 else 0

        return max(1, int(math.ceil(base))) if self.base_cost > 0 else 0
    
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
        # Calculate Force cost with player's stress multiplier
        try:
            import math
            cost = int(math.ceil(self.base_cost * 50 * getattr(user, 'get_force_cost_multiplier', lambda: 1.0)()))
        except Exception:
            cost = self.base_cost * 50  # Standard Force energy cost
        
        # Check and consume Force energy using standardized system
        if not consume_force_energy(user, cost):
            # Only show message for player, not enemies to avoid spam
            if messages is not None and hasattr(user, 'name') and user.name == 'Player':
                try: messages.add("Not enough Force energy.")
                except Exception: pass
            return False


        # support both actor targets and coordinate targets (tuple/list)
        # when coordinates are given, the caller should have passed 'game' in kwargs
        if target is None:
            if messages is not None:
                try: messages.add("No target for Push/Pull.")
                except Exception: pass
            return False

        # if coords were provided, try to resolve actor or object at location
        if isinstance(target, (tuple, list)):
            gx = kwargs.get('game', None)
            if gx is None:
                if messages is not None:
                    try: messages.add("No game context to resolve target location for Push/Pull.")
                    except Exception: pass
                return False
                tx, ty = int(target[0]), int(target[1])
                found = None
                # Check for enemy at location
                for e in getattr(gx, 'enemies', []) or []:
                    try:
                        if getattr(e, 'is_alive', lambda: False)() and getattr(e, 'x', -999) == tx and getattr(e, 'y', -999) == ty:
                            found = e; break
                    except Exception:
                        continue
                if found is not None:
                    # valid target found; consume cost already done, let caller handle actual movement
                    return True
                # Check for movable object at location (environmental interaction)
                game_map_obj = None
                try:
                    game_map_obj = gx.game_map[ty][tx]
                except Exception:
                    pass
                if game_map_obj and hasattr(gx, 'move_environment_object'):
                    # Try to move the object using a game method (to be implemented)
                    moved = gx.move_environment_object(tx, ty, direction=getattr(user, 'facing', (0, 0)))
                    if moved:
                        if messages is not None:
                            try: messages.add("You use the Force to move an object!")
                            except Exception: pass
                        # Optionally trigger environmental effects here
                        return True
                if messages is not None:
                    try: messages.add("No valid target at that location to move.")
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
        super().__init__()
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
        super().__init__()
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
        super().__init__()
        self.damage = damage

    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0, game=None, **kwargs) -> bool:
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
                
                # Apply damage - handle both enemy and player targets
                if hasattr(target, 'take_damage'):
                    target.take_damage(dmg, game=game)
                elif hasattr(target, 'hp'):
                    # Player or other entity with direct HP manipulation
                    target.hp = max(0, target.hp - dmg)
                else:
                    # Fallback - can't apply damage
                    if messages is not None:
                        try: messages.add("Lightning cannot damage this target.")
                        except Exception: pass
                    return False
                
                # Track Force Lightning attack info for death logging
                try:
                    if hasattr(target, 'last_attacking_enemy'):
                        target.last_attacking_enemy = getattr(user, "name", "Sith Enemy")
                        target.last_damage_taken = dmg
                        target.last_attack_type = "Force Lightning"
                except Exception:
                    pass
                
                if messages is not None:
                    try: 
                        enemy_name = getattr(user, "name", "Enemy")
                        target_name = getattr(target, "name", "target")
                        if hasattr(target, 'hp') and target.hp <= 0:
                            # Fatal lightning descriptions
                            import random
                            fatal_messages = [
                                f"#13#Crackling dark energy erupts from your fingertips - {target_name} convulses and falls!#0#",
                                f"#13#Force Lightning arcs through {target_name}'s body - they collapse in a smoking heap!#0#",
                                f"#13#Blue-white electricity engulfs {target_name} - their scream cuts short as they drop!#0#",
                                f"#13#You channel the dark side's fury - {target_name} spasms violently and dies!#0#",
                            ]
                            messages.add(f"{random.choice(fatal_messages)} [{dmg} damage]")
                        else:
                            # Non-fatal lightning descriptions
                            import random
                            hit_messages = [
                                f"#13#Dark lightning lances from your hands, striking {target_name}!#0#",
                                f"#13#Tendrils of crackling energy surge into {target_name}!#0#",
                                f"#13#You unleash the storm - {target_name} writhes in agony!#0#",
                                f"#13#Force Lightning tears through {target_name}'s defenses!#0#",
                                f"#13#Sith fury manifests as pure energy, scorching {target_name}!#0#",
                            ]
                            messages.add(f"{random.choice(hit_messages)} [{dmg} damage]")
                    except Exception: 
                        messages.add(f"Force: Lightning deals {dmg} damage to {getattr(target,'name', 'the target')}.")
                
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
        
        # Reduce stress (25 base + mastery scaling) - Increased for better stress management
        base_stress_reduction = 25  # Increased from 15
        
        # Bonus stress reduction based on player level (confidence/mastery)
        player_level = getattr(user, 'level', 1)
        level_bonus = min(15, player_level * 1.5)  # Up to +15 at level 10
        
        # Total stress reduction
        stress_reduction = int((base_stress_reduction + level_bonus) * power_scale)
        
        if hasattr(user, 'reduce_stress'):
            user.reduce_stress(stress_reduction, source='meditation')
        
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
    
    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0, game=None) -> bool:
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
            target.take_damage(damage, game=game)
            
            # Apply stun for 1 turn
            if hasattr(target, 'add_debuff'):
                target.add_debuff('stun', 1, 1)
            
            target_name = getattr(target, 'name', 'the enemy')
            if messages:
                import random
                if hasattr(target, 'hp') and target.hp <= 0:
                    # Fatal choke descriptions
                    fatal_messages = [
                        f"#13#You close your fist - {target_name}'s throat crushes with a sickening crack!#0#",
                        f"#13#An invisible grip tightens around {target_name}'s neck - they collapse, lifeless!#0#",
                        f"#13#{target_name} claws desperately at their throat as the Force crushes the life from them!#0#",
                        f"#13#The dark side flows through you - {target_name} expires with a strangled gasp!#0#",
                    ]
                    try: messages.add(f"{random.choice(fatal_messages)} [{damage} damage]")
                    except: pass
                else:
                    # Non-fatal choke descriptions
                    choke_messages = [
                        f"#13#You reach out with the Force - {target_name} clutches at their throat, gasping!#0#",
                        f"#13#An invisible hand grips {target_name}'s windpipe - they struggle for air!#0#",
                        f"#13#{target_name} chokes and sputters as you crush their throat with the Force!#0#",
                        f"#13#You clench your fist - {target_name} writhes in agony, unable to breathe!#0#",
                        f"#13#The dark side surges through you, strangling {target_name} from afar!#0#",
                    ]
                    try: messages.add(f"{random.choice(choke_messages)} [{damage} damage, stunned]")
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
    
    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0, game=None, **kwargs) -> bool:
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
            target.take_damage(drain_amount, game=game)
            
            # Heal user
            if hasattr(user, 'heal'):
                user.heal(drain_amount)
            else:
                user.hp = min(getattr(user, 'max_hp', 100), getattr(user, 'hp', 50) + drain_amount)
            
            target_name = getattr(target, 'name', 'the enemy')
            if messages:
                import random
                if hasattr(target, 'hp') and target.hp <= 0:
                    # Fatal drain descriptions
                    fatal_messages = [
                        f"#13#You rip the life essence from {target_name} - they wither into a desiccated husk!#0#",
                        f"#13#{target_name}'s vitality flows into you as they age decades in seconds and collapse!#0#",
                        f"#13#Tendrils of dark energy drain {target_name} completely - their corpse falls like ash!#0#",
                        f"#13#You feast on {target_name}'s life force until nothing remains but an empty shell!#0#",
                    ]
                    try: messages.add(f"{random.choice(fatal_messages)} [{drain_amount} damage, +{drain_amount} HP]")
                    except: pass
                else:
                    # Non-fatal drain descriptions
                    drain_messages = [
                        f"#13#Dark tendrils snake out, siphoning {target_name}'s life essence into you!#0#",
                        f"#13#You feel invigorated as {target_name}'s vitality pours into your body!#0#",
                        f"#13#{target_name} weakens and pales as you drain their life force!#0#",
                        f"#13#Crimson energy flows from {target_name} to you - their strength becomes yours!#0#",
                        f"#13#You channel the dark side, leeching life from {target_name}'s trembling form!#0#",
                    ]
                    try: messages.add(f"{random.choice(drain_messages)} [{drain_amount} damage, +{drain_amount} HP]")
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

class ForceSpeed(ForceAbility):
    """Grant temporary extra movement and dodge chance."""
    name = "Force Speed"
    base_cost = 30
    target_type = "self"
    description = "Channel the Force to move with preternatural speed, increasing evasion."
    alignment = "neutral"
    
    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0) -> bool:
        actual_cost = self.get_actual_cost(user)
        
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
        
        # Grant evasion bonus for 5 turns
        try:
            if not hasattr(user, 'temp_evasion_bonus'):
                user.temp_evasion_bonus = 0
                user.temp_evasion_turns = 0
            
            user.temp_evasion_bonus = 20  # +20 evasion
            user.temp_evasion_turns = 5
            user.evasion = getattr(user, 'evasion', 0) + 20
            
            if messages:
                try: messages.add("Time slows as you move with Force-enhanced speed! (+20 evasion for 5 turns)")
                except: pass
            
            return True
        except Exception:
            if messages:
                try: messages.add("Force Speed failed.")
                except: pass
            return False


class ForceSight(ForceAbility):
    """Reveal all enemies on the map briefly."""
    name = "Force Sight"
    base_cost = 40
    target_type = "self"
    description = "See through the Force, revealing all living beings on the current floor."
    alignment = "light"
    
    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0) -> bool:
        actual_cost = self.get_actual_cost(user)
        
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
        
        try:
            # Count enemies
            enemy_count = 0
            if hasattr(user, 'game') and hasattr(user.game, 'enemies'):
                enemy_count = len([e for e in user.game.enemies if getattr(e, 'hp', 0) > 0])
            
            # Grant massive LOS bonus for 3 turns
            user.los_bonus_turns = getattr(user, "los_bonus_turns", 0) + 3
            user.los_bonus_radius = max(int(getattr(user, 'los_bonus_radius', 0) or 0), 20)
            
            if messages:
                try: messages.add(f"The Force reveals all! {enemy_count} life forms detected.")
                except: pass
            
            # Light side reduces stress
            if hasattr(user, 'reduce_stress'):
                user.reduce_stress(5)
            
            return True
        except Exception:
            if messages:
                try: messages.add("Force Sight failed.")
                except: pass
            return False


class ForceRage(ForceAbility):
    """Unleash dark side fury for massive damage boost but take stress."""
    name = "Force Rage"
    base_cost = 50
    target_type = "self"
    description = "Channel raw dark side power, greatly increasing attack but at the cost of your sanity."
    alignment = "dark"
    
    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0) -> bool:
        actual_cost = self.get_actual_cost(user)
        
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
        
        try:
            # Grant massive attack bonus for 4 turns
            if not hasattr(user, 'temp_attack_bonus'):
                user.temp_attack_bonus = 0
                user.temp_attack_turns = 0
            
            bonus = 15
            user.temp_attack_bonus = bonus
            user.temp_attack_turns = 4
            user.attack = getattr(user, 'attack', 0) + bonus
            
            if messages:
                try: messages.add(f"RAGE CONSUMES YOU! +{bonus} attack for 4 turns!")
                except: pass
            
            # Dark side MASSIVELY increases stress
            if hasattr(user, 'add_stress'):
                user.add_stress(25, source='dark_rage')
            
            return True
        except Exception:
            if messages:
                try: messages.add("Force Rage failed.")
                except: pass
            return False


class ForcePhantom(ForceAbility):
    """Create an illusory decoy that draws enemy attention."""
    name = "Force Phantom"
    base_cost = 35
    target_type = "location"
    description = "Project a Force illusion that enemies will target, buying you precious time."
    alignment = "neutral"
    mode = "decoy"  # Special mode for placement
    
    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0, **kwargs) -> bool:
        actual_cost = self.get_actual_cost(user)
        
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
        
        try:
            # Get game context
            game = kwargs.get('game', None)
            if not game:
                if messages:
                    try: messages.add("Cannot create phantom without game context.")
                    except: pass
                return False
            
            # Get target coordinates
            if isinstance(target, (tuple, list)):
                tx, ty = int(target[0]), int(target[1])
            else:
                if messages:
                    try: messages.add("Invalid target location for phantom.")
                    except: pass
                return False
            
            # Create decoy marker (lasts 6 turns)
            if not hasattr(game, 'force_phantoms'):
                game.force_phantoms = []
            
            # Remove old phantoms
            game.force_phantoms = [p for p in game.force_phantoms if p['turns_left'] > 0]
            
            # Add new phantom
            phantom = {
                'x': tx,
                'y': ty,
                'turns_left': 6,
                'display_char': '@',  # Looks like player
                'taunt_range': 8  # Enemies within 8 tiles are distracted
            }
            game.force_phantoms.append(phantom)
            
            if messages:
                try: messages.add(f"Force phantom appears at ({tx},{ty})! Enemies will be drawn to it.")
                except: pass
            
            # Reduce stress slightly (clever tactic)
            if hasattr(user, 'reduce_stress'):
                user.reduce_stress(3)
            
            return True
        except Exception as e:
            if messages:
                try: messages.add(f"Force Phantom failed: {e}")
                except: pass
            return False


class ForceBurst(ForceAbility):
    """Release an explosive wave of Force energy, damaging all nearby enemies."""
    name = "Force Burst"
    base_cost = 45
    target_type = "self"
    description = "Unleash a devastating shockwave that damages all enemies around you."
    alignment = "neutral"
    
    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0, **kwargs) -> bool:
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
        
        try:
            # Get game context
            game = kwargs.get('game', None)
            if not game:
                return False
            
            # Damage all enemies within 3 tiles
            px = getattr(user, 'x', 0)
            py = getattr(user, 'y', 0)
            radius = 3
            base_damage = int(12 * power_scale)
            
            hit_count = 0
            for e in list(getattr(game, 'enemies', []) or []):
                try:
                    ex = int(getattr(e, 'x', 0))
                    ey = int(getattr(e, 'y', 0))
                    dx = ex - px
                    dy = ey - py
                    
                    # Circular radius check
                    if (dx*dx + dy*dy) <= (radius * radius):
                        if hasattr(e, 'take_damage'):
                            e.take_damage(base_damage, game=game)
                        else:
                            e.hp = getattr(e, 'hp', 0) - base_damage
                        hit_count += 1
                except Exception:
                    continue
            
            if messages:
                if hit_count > 0:
                    try: messages.add(f"Force Burst! {base_damage} damage to {hit_count} nearby enemies!")
                    except: pass
                else:
                    try: messages.add("Force Burst hits nothing nearby.")
                    except: pass
            
            return True
        except Exception:
            if messages:
                try: messages.add("Force Burst failed.")
                except: pass
            return False


class ForceBlink(ForceAbility):
    """Teleport a short distance to escape danger."""
    name = "Force Blink"
    base_cost = 40
    target_type = "location"
    description = "Vanish and reappear at a nearby location, escaping immediate danger."
    alignment = "neutral"
    mode = "teleport"
    
    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0, **kwargs) -> bool:
        actual_cost = self.get_actual_cost(user)
        
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
        
        try:
            # Get game context
            game = kwargs.get('game', None)
            if not game:
                return False
            
            # Get target coordinates
            if isinstance(target, (tuple, list)):
                tx, ty = int(target[0]), int(target[1])
            else:
                return False
            
            # Check range (max 5 tiles)
            px = getattr(user, 'x', 0)
            py = getattr(user, 'y', 0)
            dist = abs(tx - px) + abs(ty - py)
            if dist > 5:
                if messages:
                    try: messages.add("Teleport range limited to 5 tiles!")
                    except: pass
                return False
            
            # Check if target is walkable
            from jedi_fugitive.game.level import Display
            map_h = len(game.game_map)
            map_w = len(game.game_map[0]) if map_h else 0
            
            if not (0 <= ty < map_h and 0 <= tx < map_w):
                if messages:
                    try: messages.add("Cannot teleport outside the map!")
                    except: pass
                return False
            
            cell = game.game_map[ty][tx]
            wall = getattr(Display, 'WALL', '#')
            tree = getattr(Display, 'TREE', 'T')
            
            if cell in (wall, tree):
                if messages:
                    try: messages.add("Cannot teleport into solid objects!")
                    except: pass
                return False
            
            # Check for enemies at target
            for e in getattr(game, 'enemies', []):
                if getattr(e, 'x', -1) == tx and getattr(e, 'y', -1) == ty:
                    if messages:
                        try: messages.add("Cannot teleport into an enemy!")
                        except: pass
                    return False
            
            # Teleport!
            user.x = tx
            user.y = ty
            
            if messages:
                try: messages.add(f"You blink through the Force to ({tx},{ty})!")
                except: pass
            
            # Reduce stress (escape from danger)
            if hasattr(user, 'reduce_stress'):
                user.reduce_stress(5)
            
            return True
        except Exception as e:
            if messages:
                try: messages.add(f"Force Blink failed: {e}")
                except: pass
            return False


class ForceStun(ForceAbility):
    """Paralyze an enemy temporarily, preventing them from acting."""
    name = "Force Stun"
    base_cost = 30
    target_type = "enemy"
    description = "Overwhelm an enemy's nervous system, stunning them for several turns."
    alignment = "light"
    
    def use(self, user, target, game_map, messages: Any = None, player_rank: int = 0, **kwargs) -> bool:
        actual_cost = self.get_actual_cost(user)
        
        # Check Force energy
        force_available = getattr(user, 'force_energy', getattr(user, 'force_points', 0) * 50)
        if force_available < actual_cost:
            if messages:
                try: messages.add("Not enough Force energy.")
                except: pass
            return False
        
        # Get game and target
        game = kwargs.get('game', None)
        if not game:
            return False
        
        # Find enemy at target location
        if isinstance(target, (tuple, list)):
            tx, ty = int(target[0]), int(target[1])
            found_enemy = None
            for e in getattr(game, 'enemies', []):
                if getattr(e, 'x', -1) == tx and getattr(e, 'y', -1) == ty:
                    if getattr(e, 'hp', 0) > 0:
                        found_enemy = e
                        break
            
            if not found_enemy:
                if messages:
                    try: messages.add("No valid enemy to stun at that location.")
                    except: pass
                return False
            
            target_enemy = found_enemy
        else:
            target_enemy = target
        
        # Deduct cost
        if hasattr(user, 'force_energy'):
            user.force_energy -= actual_cost
        else:
            user.force_points = max(0, getattr(user, 'force_points', 0) - (actual_cost // 50))
        
        try:
            # Apply stun effect (3 turns)
            if not hasattr(target_enemy, 'stunned_turns'):
                target_enemy.stunned_turns = 0
            
            target_enemy.stunned_turns = 3
            
            enemy_name = getattr(target_enemy, 'name', 'enemy')
            if messages:
                try: messages.add(f"{enemy_name} is paralyzed by the Force! (3 turns)")
                except: pass
            
            # Light side reduces stress
            if hasattr(user, 'reduce_stress'):
                user.reduce_stress(5)
            
            return True
        except Exception:
            if messages:
                try: messages.add("Force Stun failed.")
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
if "ForceSpeed" not in _has:
    FORCE_ABILITIES.append(ForceSpeed())
if "ForceSight" not in _has:
    FORCE_ABILITIES.append(ForceSight())
if "ForceRage" not in _has:
    FORCE_ABILITIES.append(ForceRage())
if "ForcePhantom" not in _has:
    FORCE_ABILITIES.append(ForcePhantom())
if "ForceBurst" not in _has:
    FORCE_ABILITIES.append(ForceBurst())
if "ForceBlink" not in _has:
    FORCE_ABILITIES.append(ForceBlink())
if "ForceStun" not in _has:
    FORCE_ABILITIES.append(ForceStun())