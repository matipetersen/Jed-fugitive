# Alignment-Based Narrative System

## Overview
The travel log now reflects the player's alignment based on their corruption level. As you make choices throughout the game (absorbing vs destroying artifacts), your journal entries will shift in tone to match your Force alignment.

## How It Works

### Alignment Detection
- **Light Side** (0-30% corruption): Compassionate, restrained, seeking understanding
- **Balanced** (31-59% corruption): Neutral, pragmatic descriptions
- **Dark Side** (60-100% corruption): Aggressive, power-hungry, ruthless

### Narrative Changes

#### Combat
- **Light**: "Defended myself against Enemy, seeking only to survive."
- **Balanced**: "Slew Enemy in battle."
- **Dark**: "Obliterated Enemy without mercy or hesitation."

#### Boss Kills
- **Light**: "Defeated the fearsome Boss, bringing justice to the galaxy."
- **Balanced**: "Defeated the fearsome Boss in mortal combat!"
- **Dark**: "Crushed Boss utterly, proving your superior power!"

#### Absorbing Artifacts (Dark Side choice)
- **Light**: "Absorbed Artifact with reluctance, feeling its dark power seep in."
- **Balanced**: "Absorbed Artifact, embracing the dark side."
- **Dark**: "Devoured the essence of Artifact, reveling in its dark power!"

#### Destroying Artifacts (Light Side choice)
- **Light**: "Cleansed Artifact, its corruption dissolved by the Force."
- **Balanced**: "Destroyed Artifact, resisting the darkness."
- **Dark**: "Destroyed Artifact, though it felt like wasted power."

#### Unlocking Dark Abilities
- **Light**: "Reluctantly learned Force Lightning, fearing its corrupting influence."
- **Balanced**: "Gained dark power: Force Lightning"
- **Dark**: "Mastered Force Lightning, feeling the intoxicating power of the dark side!"

#### Unlocking Light Abilities
- **Light**: "Achieved harmony with the Force, gaining insight into Force Heal."
- **Balanced**: "Gained light power: Force Heal"
- **Dark**: "Learned Force Heal, though it feels weak compared to dark powers."

#### Descending Stairs
- **Light**: "Descended deeper, seeking to understand this dark place."
- **Balanced**: "Descended to level X."
- **Dark**: "Plunged deeper into darkness, hungry for more power."

#### Ascending Stairs
- **Light**: "Ascended, drawing closer to the light above."
- **Balanced**: "Climbed to level X."
- **Dark**: "Retreated upward, my conquest not yet complete."

#### Entering Tombs
- **Light**: "Entered the Sith tomb with caution, feeling the weight of its evil."
- **Balanced**: "Entered a Sith tomb, the darkness palpable."
- **Dark**: "Stormed into the Sith tomb, eager to claim its forbidden secrets!"

## Visual Feedback
Your player character (@) color also changes with corruption:
- **0-24%**: Bright cyan (pure Light Side)
- **25-49%**: Dim cyan (slightly corrupted)
- **50-74%**: Yellow (moderately corrupted)
- **75-100%**: Red (deeply corrupted Dark Side)

## Testing
Run `python scripts/test_alignment_narrative.py` to see examples of how the narrative changes across different corruption levels.

## Impact on Gameplay
This system provides:
1. **Immersion**: Your choices affect not just stats but how your character perceives the world
2. **Roleplaying**: Clear feedback on your character's descent into darkness or adherence to the Light
3. **Replayability**: Different playthroughs will have unique journal entries
4. **Narrative coherence**: The travel log reads like a personal journal that evolves with your choices

Press 'j' in-game to view your travel log and see your journey's narrative unfold!
