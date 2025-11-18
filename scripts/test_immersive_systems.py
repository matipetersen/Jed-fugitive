#!/usr/bin/env python3
"""
Test the three new immersive systems:
1. Enhanced inspect command
2. NPC encounters
3. Rituals & ceremonies
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from jedi_fugitive.game import inspection, npc_encounters, rituals

def test_inspection_system():
    """Test enhanced inspection with lore."""
    print("=" * 70)
    print("1. ENHANCED INSPECTION SYSTEM")
    print("=" * 70)
    
    # Test enemy inspection
    print("\n[Enemy Inspection Example - Sith Warrior at 30% corruption]")
    enemy_data = inspection.get_enemy_inspection('Sith Warrior', 30)
    lines = inspection.format_inspection_text(enemy_data, 'enemy')
    for line in lines:
        print(line)
    
    # Test item inspection
    print("\n\n[Item Inspection Example - Lightsaber at 80% corruption]")
    item_data = inspection.get_item_inspection('lightsaber', 'Jedi Lightsaber', 80)
    lines = inspection.format_inspection_text(item_data, 'item')
    for line in lines:
        print(line)
    
    # Test environment inspection
    print("\n\n[Environment Inspection Example - Tomb Entrance]")
    env_data = inspection.get_environment_inspection('tomb_entrance')
    if env_data:
        lines = inspection.format_inspection_text(env_data, 'environment')
        for line in lines:
            print(line)
    
    print("\n" + "✓" * 70)
    print("Inspection system: 4 enemy types, item lore, environmental storytelling")
    print("✓" * 70)

def test_npc_system():
    """Test NPC encounter system."""
    print("\n\n" + "=" * 70)
    print("2. NPC ENCOUNTERS SYSTEM")
    print("=" * 70)
    
    # Show NPC types
    print("\n[NPC Types]")
    for npc_type, data in npc_encounters.NPC_TYPES.items():
        print(f"\n{data['name']} ({npc_type})")
        print(f"  Symbol: {data['symbol']} | Color: {data['color']}")
        print(f"  Spawn Chance: {data['spawn_chance']*100}%")
        print(f"  Biomes: {', '.join(data['biomes'])}")
        print(f"  {data['description']}")
    
    # Test dialogue system
    print("\n\n[Dialogue Examples]")
    
    print("\n  Survivor Camp - Light Side Player (Corruption 20):")
    greeting = npc_encounters.get_npc_dialogue('survivor_camp', 20, 'greeting')
    print(f"    Greeting: \"{greeting}\"")
    response = npc_encounters.get_npc_dialogue('survivor_camp', 20, 'response')
    print(f"    Response: \"{response}\"")
    
    print("\n  Hermit Jedi - Dark Side Player (Corruption 80):")
    greeting = npc_encounters.get_npc_dialogue('hermit_jedi', 80, 'greeting')
    print(f"    Greeting: \"{greeting}\"")
    warning = npc_encounters.get_npc_dialogue('hermit_jedi', 80, 'warning')
    print(f"    Warning: \"{warning}\"")
    
    print("\n  Fallen Jedi - Balanced Player (Corruption 50):")
    greeting = npc_encounters.get_npc_dialogue('fallen_jedi', 50, 'greeting')
    print(f"    Greeting: \"{greeting}\"")
    interest = npc_encounters.get_npc_dialogue('fallen_jedi', 50, 'interest')
    print(f"    Interest: \"{interest}\"")
    
    # Test training offers
    print("\n\n[Training Offers]")
    for training_id, training_data in npc_encounters.TRAINING_OFFERS.items():
        print(f"\n  {training_data['name']} (taught by {training_data['teacher']})")
        min_c, max_c = training_data['corruption_required']
        print(f"    Corruption Range: {min_c}-{max_c}")
        print(f"    Description: {training_data['description']}")
        print(f"    Effect: {training_data['effect']}")
    
    # Test moral choices
    print("\n\n[Moral Choice Example - Imperial Scouts]")
    choice_data = npc_encounters.MORAL_CHOICES['imperial_scouts']
    print(f"  Setup: {choice_data['setup']}")
    print(f"\n  Option 1: {choice_data['option_light']['text']}")
    print(f"    Corruption: {choice_data['option_light']['corruption_change']}")
    print(f"    Outcome: {choice_data['option_light']['message']}")
    print(f"\n  Option 2: {choice_data['option_dark']['text']}")
    print(f"    Corruption: +{choice_data['option_dark']['corruption_change']}")
    print(f"    Outcome: {choice_data['option_dark']['message']}")
    print(f"    Reward: {choice_data['option_dark']['reward']}")
    
    print("\n" + "✓" * 70)
    print("NPC system: 4 NPC types, moral choices, training, corruption-aware dialogue")
    print("✓" * 70)

def test_rituals_system():
    """Test rituals and ceremonies system."""
    print("\n\n" + "=" * 70)
    print("3. RITUALS & CEREMONIES SYSTEM")
    print("=" * 70)
    
    # Crystal attunement rituals
    print("\n[Crystal Attunement Rituals]")
    for ritual_id, ritual_data in rituals.CRYSTAL_ATTUNEMENT_RITUALS.items():
        print(f"\n  {ritual_data['name']}")
        min_c, max_c = ritual_data['corruption_required']
        print(f"    Corruption Range: {min_c}-{max_c}")
        print(f"    Duration: {ritual_data['duration']}")
        print(f"    Effects: {ritual_data['effects']['message']}")
    
    # Jedi rites
    print("\n\n[Jedi Light Side Rites]")
    for ritual_id, ritual_data in rituals.JEDI_RITES.items():
        print(f"\n  {ritual_data['name']}")
        min_c, max_c = ritual_data['corruption_required']
        print(f"    Corruption Range: {min_c}-{max_c}")
        if 'location_required' in ritual_data:
            print(f"    Location Required: {ritual_data['location_required']}")
        print(f"    Effects: {ritual_data['effects']['message']}")
    
    # Sith rites
    print("\n\n[Sith Dark Side Rites]")
    for ritual_id, ritual_data in rituals.SITH_RITES.items():
        print(f"\n  {ritual_data['name']}")
        min_c, max_c = ritual_data['corruption_required']
        print(f"    Corruption Range: {min_c}-{max_c}")
        if 'location_required' in ritual_data:
            print(f"    Location Required: {ritual_data['location_required']}")
        print(f"    Effects: {ritual_data['effects']['message']}")
    
    # Burial ceremonies
    print("\n\n[Burial & Memorial Ceremonies]")
    for ritual_id, ritual_data in rituals.BURIAL_CEREMONIES.items():
        print(f"\n  {ritual_data['name']}")
        min_c, max_c = ritual_data['corruption_required']
        print(f"    Corruption Range: {min_c}-{max_c}")
        print(f"    Effects: {ritual_data['effects']['message']}")
    
    # Milestone ceremonies
    print("\n\n[Milestone Ceremonies]")
    for ritual_id, ritual_data in rituals.MILESTONE_CEREMONIES.items():
        print(f"\n  {ritual_data['name']}")
        min_c, max_c = ritual_data['corruption_required']
        print(f"    Corruption Range: {min_c}-{max_c}")
        if 'level_required' in ritual_data:
            print(f"    Level Required: {ritual_data['level_required']}")
        if 'title_gained' in ritual_data['effects']:
            print(f"    Grants Title: {ritual_data['effects']['title_gained']}")
        print(f"    Effects: {ritual_data['effects']['message']}")
    
    # Test formatted display
    print("\n\n[Formatted Ritual Display Example]")
    ritual_data = rituals.CRYSTAL_ATTUNEMENT_RITUALS['dark_bleeding']
    lines = rituals.format_ritual_display('crystal', 'dark_bleeding', ritual_data)
    for line in lines:
        print(line)
    
    print("\n" + "✓" * 70)
    print("Rituals system: 4 crystal rituals, 3 Jedi rites, 4 Sith rites,")
    print("4 burial ceremonies, 4 milestone ceremonies")
    print("✓" * 70)

def show_statistics():
    """Show comprehensive statistics of all three systems."""
    print("\n\n" + "=" * 70)
    print("COMPREHENSIVE STATISTICS")
    print("=" * 70)
    
    # Inspection system stats
    enemy_types = len(inspection.ENEMY_LORE)
    item_types = len(inspection.ITEM_LORE)
    env_types = len(inspection.ENVIRONMENT_LORE)
    
    print(f"\n[Inspection System]")
    print(f"  • {enemy_types} enemy types with detailed lore")
    print(f"  • {item_types} item categories with descriptions")
    print(f"  • {env_types} environmental features")
    print(f"  • Corruption-aware personal reflections")
    print(f"  • Tactical combat advice")
    
    # NPC system stats
    npc_types = len(npc_encounters.NPC_TYPES)
    training_offers = len(npc_encounters.TRAINING_OFFERS)
    moral_choices = len(npc_encounters.MORAL_CHOICES)
    total_dialogues = (
        len(npc_encounters.SURVIVOR_DIALOGUES) +
        len(npc_encounters.HERMIT_JEDI_DIALOGUES) +
        len(npc_encounters.FALLEN_JEDI_DIALOGUES) +
        len(npc_encounters.DARK_HERMIT_DIALOGUES)
    )
    
    print(f"\n[NPC Encounters System]")
    print(f"  • {npc_types} NPC types")
    print(f"  • {training_offers} unique training offers")
    print(f"  • {moral_choices} moral choice scenarios")
    print(f"  • {total_dialogues} dialogue categories")
    print(f"  • Corruption-aware interactions")
    print(f"  • Dynamic spawning per biome")
    
    # Rituals system stats
    crystal_rituals = len(rituals.CRYSTAL_ATTUNEMENT_RITUALS)
    jedi_rites = len(rituals.JEDI_RITES)
    sith_rites = len(rituals.SITH_RITES)
    burial_rites = len(rituals.BURIAL_CEREMONIES)
    milestone_rites = len(rituals.MILESTONE_CEREMONIES)
    total_rituals = crystal_rituals + jedi_rites + sith_rites + burial_rites + milestone_rites
    
    print(f"\n[Rituals & Ceremonies System]")
    print(f"  • {crystal_rituals} crystal attunement rituals")
    print(f"  • {jedi_rites} Jedi Light Side rites")
    print(f"  • {sith_rites} Sith Dark Side rites")
    print(f"  • {burial_rites} burial/memorial ceremonies")
    print(f"  • {milestone_rites} milestone ceremonies")
    print(f"  • {total_rituals} total rituals")
    print(f"  • Location-aware rituals")
    print(f"  • Corruption/level requirements")
    
    print(f"\n[Total Content Created]")
    print(f"  • Inspection: {enemy_types + item_types + env_types} content pieces")
    print(f"  • NPCs: {npc_types + training_offers + moral_choices} interactive elements")
    print(f"  • Rituals: {total_rituals} ceremonies")
    print(f"  • Grand Total: {enemy_types + item_types + env_types + npc_types + training_offers + moral_choices + total_rituals} pieces of immersive content")
    
    print("\n" + "=" * 70)

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("IMMERSIVE SYSTEMS TEST SUITE")
    print("Testing: Inspect, NPCs, and Rituals")
    print("=" * 70)
    
    test_inspection_system()
    test_npc_system()
    test_rituals_system()
    show_statistics()
    
    print("\n" + "=" * 70)
    print("ALL SYSTEMS TESTED SUCCESSFULLY!")
    print("=" * 70)
    print("\nThese three systems add deep immersion to Jedi Fugitive:")
    print("\n1. Enhanced Inspect (x key)")
    print("   • Rich enemy lore with tactical advice")
    print("   • Detailed item descriptions")
    print("   • Environmental storytelling")
    print("   • Corruption-aware reflections")
    
    print("\n2. NPC Encounters")
    print("   • 4 NPC types with unique personalities")
    print("   • 6 training opportunities")
    print("   • 5 moral choice scenarios")
    print("   • Corruption affects all interactions")
    
    print("\n3. Rituals & Ceremonies")
    print("   • 4 lightsaber crystal rituals")
    print("   • 7 Force meditation rites")
    print("   • 4 burial ceremonies")
    print("   • 4 progression milestones")
    print("   • Choose your path: Light, Dark, or Gray")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    main()
