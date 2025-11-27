# Level Progression & Lightsaber Forms System

## Overview
Complete redesign of character progression incorporating canonical Star Wars lightsaber combat forms, ranked mastery system, and meaningful character specialization choices.

## What's Been Created

### 1. Lightsaber Forms System (`lightsaber_forms.py`)
**Status**: ✅ Created

**Contents**:
- 7 canonical lightsaber forms (I through VII)
- 2 specialized variants (Jar'Kai dual-wielding, Saberstaff)
- Complete stat bonuses and special effects for each form
- Form prerequisites and level requirements
- Helper functions for integration

**Forms Included**:
1. **Form I: Shii-Cho** - Basic foundation (Level 1, starting form)
2. **Form II: Makashi** - Elegant dueling (Level 3+)
3. **Form III: Soresu** - Ultimate defense (Level 4+, Obi-Wan's style)
4. **Form IV: Ataru** - Acrobatic aggression (Level 5+, Yoda's style)
5. **Form V: Shien/Djem So** - Power attacks (Level 6+, Anakin/Luke's style)
6. **Form VI: Niman** - Force integration (Level 7+, balanced)
7. **Form VII: Juyo/Vaapad** - Ferocious mastery (Level 10+, Mace Windu's style)
8. **Jar'Kai** - Dual-wielding (Level 5+, requires Shii-Cho + Ataru)
9. **Saberstaff Mastery** - Double-bladed (Level 6+, Darth Maul's style)

### 2. Analysis Tool (`scripts/analyze_progression.py`)
**Status**: ✅ Created and tested

**Provides**:
- Current system analysis
- Proposed improvements
- Example character builds
- Implementation roadmap

## Current System Issues

1. **Too Many Automatic Gains**: Stats increase automatically every level, making player choices feel less impactful
2. **No Fighting Stance System**: Missing the iconic lightsaber forms from Star Wars lore
3. **Flat Masteries**: Masteries are one-time bonuses with no progression
4. **Linear Scaling**: Predictable stat growth with no specialization
5. **Limited Build Diversity**: All characters feel similar

## Proposed Changes

### Phase 1: Reduce Automatic Gains
**Current**:
- Max HP: +5 automatic + optional +5 choice
- Attack: +1 automatic + optional +1 choice
- Defense: +1 automatic
- Evasion: +1 automatic + optional +1 choice
- Force Points: +1 automatic + optional +2 choice

**Proposed**:
- Max HP: +3 automatic + optional +10 choice
- Attack: +1 automatic + optional +2 choice
- Defense: +1 automatic + optional +2 choice
- Evasion: +0 automatic + optional +3 choice
- Force Points: +1 every 2 levels + optional +3 choice

### Phase 2: Add Lightsaber Forms to Level-Up Menu
**New Option**: "Learn Lightsaber Form"
- Shows available forms based on level and prerequisites
- Displays full form description with bonuses
- Forms provide significant combat bonuses
- Can switch active form outside combat

### Phase 3: Implement Ranked Mastery System
**Current**: Flat +2 damage or +2 defense bonuses

**Proposed**: 3-rank progression for each mastery
```
Melee Mastery:
  Rank 1 (Lv 2+): +1 damage
  Rank 2 (Lv 6+): +2 damage, ignore 2 defense
  Rank 3 (Lv 12+): +3 damage, 10% lifesteal

Ranged Mastery:
  Rank 1 (Lv 2+): +1 damage
  Rank 2 (Lv 6+): +2 damage, +1 range
  Rank 3 (Lv 12+): +3 damage, ignore cover

Shield Mastery:
  Rank 1 (Lv 3+): +2 defense
  Rank 2 (Lv 7+): +3 defense, block melee
  Rank 3 (Lv 13+): +4 defense, reflect projectiles

Force Mastery:
  Rank 1 (Lv 3+): -10% Force costs
  Rank 2 (Lv 8+): -20% costs, +1 FP regen/turn
  Rank 3 (Lv 14+): -30% costs, 2 abilities/turn
```

### Phase 4: Milestone Rewards
**Special unlocks at key levels**:
- **Level 5**: Specialization path choice
- **Level 10**: Signature technique (custom ability)
- **Level 15**: Master achievement (title + ultimate ability)
- **Level 20**: Legendary status (transcend limits)

### Phase 5: Combat Integration
- Apply form bonuses to attack/defense calculations
- Integrate crit chance bonuses
- Apply Force cost reductions
- Special form effects (counter-attacks, wide strikes, etc.)

### Phase 6: UI/UX Updates
- Add form switching command (suggest 'X' key)
- Display active form in status bar
- Show form bonuses in character sheet
- Add form descriptions to help screen
- Visual indicators for active stance

## Example Builds

### Jedi Guardian (Tank)
- **Form**: Soresu (Form III)
- **Stats**: High HP, High Defense
- **Masteries**: Shield Mastery Rank 3, Melee Rank 2
- **Abilities**: Force Protect, Force Heal
- **Playstyle**: Defensive wall, outlasts enemies

### Sith Marauder (DPS)
- **Form**: Juyo/Vaapad (Form VII)
- **Stats**: High Attack, High Crit
- **Masteries**: Melee Mastery Rank 3, Dual Wield
- **Abilities**: Force Rage, Force Lightning
- **Playstyle**: Relentless aggression, high damage

### Jedi Consular (Force Focus)
- **Form**: Niman (Form VI)
- **Stats**: High Force Points, High Evasion
- **Masteries**: Force Mastery Rank 3
- **Abilities**: Force Heal, Meditation, Stun
- **Playstyle**: Pure Force user, minimal melee

### Shadow Jedi (Mobility)
- **Form**: Ataru (Form IV)
- **Stats**: High Evasion, High Attack
- **Masteries**: Dual Wield, Melee Rank 2
- **Abilities**: Force Speed, Force Phantom
- **Playstyle**: Mobile striker, never gets hit

## Implementation Priority

### High Priority (Core Gameplay)
1. ✅ Create lightsaber_forms.py
2. ⏳ Modify player.py level_up() to reduce automatic gains
3. ⏳ Add "Learn Lightsaber Form" option to level-up menu
4. ⏳ Initialize player with Form I: Shii-Cho
5. ⏳ Apply form bonuses in combat calculations

### Medium Priority (Depth)
6. ⏳ Implement ranked mastery system
7. ⏳ Add form switching command
8. ⏳ Display active form in UI
9. ⏳ Update help screen with forms

### Low Priority (Polish)
10. ⏳ Milestone reward system
11. ⏳ Custom signature techniques
12. ⏳ Visual stance indicators
13. ⏳ Form-specific special effects

## Testing Needed

1. **Balance Testing**: Ensure forms are balanced and no dominant strategy
2. **Progression Testing**: Verify level-up choices feel meaningful
3. **Build Testing**: Test example builds for viability
4. **Combat Testing**: Confirm form bonuses apply correctly
5. **UI Testing**: Ensure form information displays clearly

## Backward Compatibility

**Existing saves**: Will need migration to add:
- `known_forms` list (default: ["Shii-Cho"])
- `active_form` string (default: "Shii-Cho")
- Update mastery values to rank system

## Next Steps

**Ready to implement**:
1. Would you like me to start modifying `player.py` to integrate the forms system?
2. Should I reduce the automatic stat gains now?
3. Do you want to see the new level-up menu first?

The lightsaber forms system is complete and ready to integrate into the game!
