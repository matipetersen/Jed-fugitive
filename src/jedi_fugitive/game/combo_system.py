"""
Combo system - track action sequences and reward players with bonus effects.
"""

# Combo definitions with lore-appropriate sequences
COMBOS = {
    # Force + Melee combos
    'force_blade': {
        'sequence': ['force_push', 'melee_attack'],
        'window': 2,  # Must complete within 2 turns
        'bonus_damage': 15,
        'description': 'Force-enhanced blade strike',
        'message': "⚡ FORCE BLADE! Your weapon crackles with Force energy! (+15 damage)",
        'corruption_shift': 0,  # Neutral combo
    },
    'sith_fury': {
        'sequence': ['force_lightning', 'melee_attack', 'melee_attack'],
        'window': 3,
        'bonus_damage': 25,
        'description': 'Channel dark side fury into rapid strikes',
        'message': "⚡ SITH FURY! Lightning flows through your strikes! (+25 damage)",
        'corruption_shift': 3,  # Dark side combo
    },
    'jedi_guardian': {
        'sequence': ['force_heal', 'melee_attack'],
        'window': 2,
        'bonus_damage': 10,
        'bonus_defense': 5,
        'description': 'Balanced defense and offense',
        'message': "✨ JEDI GUARDIAN! You strike with righteous precision! (+10 dmg, +5 def for 3 turns)",
        'corruption_shift': -2,  # Light side combo
        'duration': 3,
    },
    
    # Force + Force combos
    'lightning_chain': {
        'sequence': ['force_lightning', 'force_lightning'],
        'window': 2,
        'aoe': True,
        'aoe_damage': 20,
        'aoe_radius': 3,
        'description': 'Chain lightning arcs between nearby enemies',
        'message': "⚡⚡ CHAIN LIGHTNING! Electric arcs jump between enemies! (20 damage in 3-tile radius)",
        'corruption_shift': 5,  # Very dark
    },
    'force_storm': {
        'sequence': ['force_push', 'force_pull', 'force_push'],
        'window': 3,
        'aoe': True,
        'aoe_damage': 15,
        'stun': True,
        'description': 'Create a Force whirlwind that stuns and damages',
        'message': "🌀 FORCE STORM! A whirlwind of Force energy erupts! (Enemies stunned + 15 damage)",
        'corruption_shift': 1,
    },
    'force_mastery': {
        'sequence': ['force_push', 'force_pull'],
        'window': 2,
        'bonus_force_regen': 10,
        'description': 'Demonstrate mastery of telekinesis',
        'message': "✨ FORCE MASTERY! Your connection deepens! (+10 Force energy restored)",
        'corruption_shift': 0,
    },
    
    # Tactical combos
    'hit_and_run': {
        'sequence': ['ranged_attack', 'force_push'],
        'window': 2,
        'bonus_evasion': 20,
        'description': 'Shoot and create distance',
        'message': "🏹 HIT & RUN! You create tactical distance! (+20% evasion for 2 turns)",
        'corruption_shift': 0,
        'duration': 2,
    },
    'assassination': {
        'sequence': ['force_sense', 'melee_attack'],
        'window': 2,
        'critical_chance': 50,  # +50% crit chance
        'description': 'Sense weakness, then exploit it',
        'message': "🗡 ASSASSINATION! You strike at the perfect moment! (+50% crit chance)",
        'corruption_shift': 2,
    },
    'tactical_retreat': {
        'sequence': ['grenade', 'force_push'],
        'window': 2,
        'knockback': True,
        'description': 'Explosive escape',
        'message': "💥 TACTICAL RETREAT! Enemies are blasted away!",
        'corruption_shift': 0,
    },
}

class ComboTracker:
    """Tracks player action sequences and triggers combo bonuses."""
    
    def __init__(self, game):
        self.game = game
        self.action_history = []  # List of recent actions
        self.active_buffs = []  # List of active combo buffs
        self.last_combo_turn = -999  # Track when last combo triggered
    
    def record_action(self, action_type):
        """Record a player action and check for combo triggers."""
        turn = getattr(self.game, 'turn_count', 0)
        
        # Add to history
        self.action_history.append({
            'type': action_type,
            'turn': turn,
        })
        
        # Keep only recent history (last 10 actions)
        if len(self.action_history) > 10:
            self.action_history = self.action_history[-10:]
        
        # Check for combo triggers
        self.check_combos()
    
    def check_combos(self):
        """Check if any combos have been triggered."""
        turn = getattr(self.game, 'turn_count', 0)
        
        for combo_name, combo_data in COMBOS.items():
            sequence = combo_data['sequence']
            window = combo_data.get('window', 3)
            
            # Check if we have enough actions
            if len(self.action_history) < len(sequence):
                continue
            
            # Check if sequence matches recent actions within window
            recent_actions = self.action_history[-(len(sequence)):]
            
            # Check turn window
            oldest_action_turn = recent_actions[0]['turn']
            if turn - oldest_action_turn > window:
                continue
            
            # Check sequence match
            action_types = [a['type'] for a in recent_actions]
            if action_types == sequence:
                self.trigger_combo(combo_name, combo_data)
                # Clear history after combo to prevent re-triggering
                self.action_history = []
                self.last_combo_turn = turn
                break
    
    def trigger_combo(self, combo_name, combo_data):
        """Trigger a combo effect."""
        turn = getattr(self.game, 'turn_count', 0)
        
        # Show message
        try:
            message = combo_data.get('message', f'COMBO: {combo_name}!')
            self.game.ui.messages.add(message)
        except:
            pass
        
        # Apply immediate effects
        if 'bonus_damage' in combo_data:
            # Store for next attack
            self.game.player.combo_damage_bonus = combo_data['bonus_damage']
        
        if 'aoe' in combo_data and combo_data['aoe']:
            self.apply_aoe_damage(combo_data)
        
        if 'bonus_force_regen' in combo_data:
            if hasattr(self.game.player, 'force_energy'):
                self.game.player.force_energy = min(
                    self.game.player.max_force_energy,
                    self.game.player.force_energy + combo_data['bonus_force_regen']
                )
        
        # Apply duration buffs (their stat bonuses used to be display-only)
        if 'duration' in combo_data:
            p = self.game.player
            p.defense = getattr(p, 'defense', 0) + int(combo_data.get('bonus_defense', 0))
            p.evasion = getattr(p, 'evasion', 0) + int(combo_data.get('bonus_evasion', 0))
            p.crit_chance_bonus = getattr(p, 'crit_chance_bonus', 0) + int(combo_data.get('critical_chance', 0))
            buff = {
                'name': combo_name,
                'data': combo_data,
                'turns_remaining': combo_data['duration'],
                'start_turn': turn,
            }
            self.active_buffs.append(buff)
        
        # Corruption shift
        if 'corruption_shift' in combo_data:
            shift = combo_data['corruption_shift']
            self.game.player.dark_corruption = max(0, min(100, 
                self.game.player.dark_corruption + shift
            ))
    
    def apply_aoe_damage(self, combo_data):
        """Apply area-of-effect damage from combo."""
        px = self.game.player.x
        py = self.game.player.y
        radius = combo_data.get('aoe_radius', 3)
        damage = combo_data.get('aoe_damage', 10)
        
        enemies_hit = []
        for enemy in getattr(self.game, 'enemies', []):
            if not getattr(enemy, 'is_alive', lambda: True)():
                continue
            
            ex = getattr(enemy, 'x', -999)
            ey = getattr(enemy, 'y', -999)
            dist = abs(ex - px) + abs(ey - py)
            
            if dist <= radius:
                enemy.hp = getattr(enemy, 'hp', 0) - damage
                enemies_hit.append(getattr(enemy, 'name', 'enemy'))
                
                # Apply stun if combo has it
                if combo_data.get('stun'):
                    enemy.stunned = 2  # Stunned for 2 turns
        
        if enemies_hit:
            try:
                self.game.ui.messages.add(f"Hit {len(enemies_hit)} enemies: {', '.join(enemies_hit[:3])}")
            except:
                pass
    
    def tick_buffs(self):
        """Process active combo buffs each turn."""
        buffs_to_remove = []
        
        for buff in self.active_buffs:
            buff['turns_remaining'] -= 1
            
            if buff['turns_remaining'] <= 0:
                buffs_to_remove.append(buff)
                d = buff['data']
                p = self.game.player
                p.defense = getattr(p, 'defense', 0) - int(d.get('bonus_defense', 0))
                p.evasion = getattr(p, 'evasion', 0) - int(d.get('bonus_evasion', 0))
                p.crit_chance_bonus = getattr(p, 'crit_chance_bonus', 0) - int(d.get('critical_chance', 0))
                try:
                    self.game.ui.messages.add(f"[{buff['name']} combo effect fades]")
                except:
                    pass
                continue
            
            # Apply ongoing effects
            data = buff['data']
            
            if 'bonus_defense' in data:
                # Defense bonus already applied, will be removed when buff expires
                pass
        
        # Remove expired buffs
        for buff in buffs_to_remove:
            self.active_buffs.remove(buff)
    
    def get_active_bonuses(self):
        """Get currently active combo bonuses for display."""
        bonuses = []
        for buff in self.active_buffs:
            data = buff['data']
            turns = buff['turns_remaining']
            
            if 'bonus_defense' in data:
                bonuses.append(f"+{data['bonus_defense']} DEF ({turns}t)")
            if 'bonus_evasion' in data:
                bonuses.append(f"+{data['bonus_evasion']}% EVA ({turns}t)")
            if 'critical_chance' in data:
                bonuses.append(f"+{data['critical_chance']}% CRIT ({turns}t)")
        
        return bonuses
    
    def clear_temp_bonuses(self):
        """Clear temporary single-use bonuses after they're consumed."""
        if hasattr(self.game.player, 'combo_damage_bonus'):
            delattr(self.game.player, 'combo_damage_bonus')
