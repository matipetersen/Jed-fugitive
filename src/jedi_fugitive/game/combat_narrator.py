"""
Enhanced Combat Description System for Jedi Fugitive
Provides immersive, contextual combat narration and environmental storytelling.
"""

import random
from typing import Optional, Dict, List


class CombatNarrator:
    """Generates immersive combat descriptions based on context"""
    
    def __init__(self):
        self.body_parts = {
            "torso": ["chest", "ribs", "side", "torso", "midsection"],
            "limbs": ["arm", "leg", "shoulder", "thigh", "forearm"],
            "head": ["head", "face", "neck", "jaw", "temple"],
            "extremities": ["hand", "foot", "wrist", "ankle", "fingers"]
        }
        
        self.weapon_types = {
            "melee": ["blade", "weapon", "steel", "edge"],
            "lightsaber": ["lightsaber", "plasma blade", "Jedi weapon", "energy sword"],
            "force": ["dark energy", "Force power", "invisible hand", "mystical force"],
            "ranged": ["energy bolt", "blaster fire", "plasma shot", "laser burst"]
        }
    
    def get_attack_description(self, attacker_name: str, damage: int, 
                             weapon_type: str = "melee", 
                             target_area: str = "torso",
                             environmental_context: str = "neutral",
                             is_massive: bool = False) -> str:
        """Generate contextual attack description"""
        
        # Check for massive creature attacks first
        if is_massive:
            return self._get_massive_creature_attack(attacker_name, damage, target_area, environmental_context)
        
        # Determine damage severity
        if damage >= 15:
            severity = "fatal"
        elif damage >= 8:
            severity = "heavy"
        elif damage >= 4:
            severity = "normal"
        else:
            severity = "light"
        
        # Get appropriate body part
        body_part = self._get_body_part(target_area)
        weapon_name = self._get_weapon_name(weapon_type)
        
        # Environmental modifiers
        env_modifier = self._get_environmental_modifier(environmental_context, severity)
        
        # Base attack descriptions
        descriptions = {
            "fatal": [
                f"{attacker_name}'s {weapon_name} finds its deadly mark in your {body_part}!",
                f"A devastating strike from {attacker_name} pierces your {body_part}!",
                f"{attacker_name} delivers a killing blow to your {body_part}!",
                f"The fatal strike tears through your {body_part} with merciless precision!"
            ],
            "heavy": [
                f"{attacker_name}'s {weapon_name} carves deep into your {body_part}!",
                f"A savage blow from {attacker_name} tears into your {body_part}!",
                f"{attacker_name} strikes your {body_part} with brutal force!",
                f"Pain explodes through your {body_part} as {attacker_name} attacks!"
            ],
            "normal": [
                f"{attacker_name}'s {weapon_name} finds your {body_part}!",
                f"A solid strike from {attacker_name} connects with your {body_part}!",
                f"{attacker_name} wounds your {body_part} with practiced precision!",
                f"You grunt in pain as {attacker_name}'s attack hits your {body_part}!"
            ],
            "light": [
                f"{attacker_name}'s {weapon_name} grazes your {body_part}!",
                f"A glancing blow from {attacker_name} scrapes your {body_part}!",
                f"{attacker_name}'s attack barely clips your {body_part}!",
                f"The strike leaves a minor mark on your {body_part}!"
            ]
        }
        
        base_description = random.choice(descriptions[severity])
        
        # Add environmental context
        if env_modifier and random.random() < 0.3:  # 30% chance for environmental detail
            base_description += f" {env_modifier}"
        
        # Add damage amount
        base_description += f" [{damage} damage]"
        
        return base_description
    
    def get_death_description(self, killer_name: str, location: str, 
                            final_damage: int, cause: str = "combat") -> str:
        """Generate dramatic death descriptions"""
        
        location_deaths = {
            "desert": [
                f"Your blood seeps into the thirsty sand as {killer_name} stands victorious over your fallen form.",
                f"The merciless sun witnesses your final moments as {killer_name}'s attack proves fatal.",
                f"The desert claims another soul - your body will join the bones buried in these endless dunes.",
                f"Under the scorching sky, {killer_name} delivers the blow that ends your journey forever."
            ],
            "forest": [
                f"You fall among the ancient roots as {killer_name} emerges triumphant in the shadowed grove.",
                f"The forest bears witness to your last breath as {killer_name}'s weapon finds its mark.",
                f"Your spirit joins the woodland as {killer_name} stands over your still form.",
                f"The trees will remember this violence as {killer_name} claims victory over your corpse."
            ],
            "mountains": [
                f"From these towering heights, {killer_name} casts you into the abyss of death.",
                f"The mountain peaks echo with your final cry as {killer_name} delivers the killing blow.",
                f"Your body will tumble into the rocky depths, another casualty of {killer_name}'s blade.",
                f"The thin mountain air carries your dying breath as {killer_name} stands victorious."
            ],
            "tomb": [
                f"Ancient stones witness your demise as {killer_name} adds another soul to the tomb's collection.",
                f"You join the countless dead in these cursed halls as {killer_name} prevails.",
                f"The tomb's eternal darkness welcomes you as {killer_name} delivers the final strike.",
                f"Your spirit will haunt these corridors alongside the victims of ages past."
            ],
            "crash_site": [
                f"Among the twisted wreckage, {killer_name} adds your name to the casualty list.",
                f"Your fate mirrors that of the doomed vessel as {killer_name} strikes you down.",
                f"The burning debris provides a funeral pyre as {killer_name} claims victory.",
                f"Technology failed the ship's crew, and now your body joins theirs in death."
            ]
        }
        
        # Get location-specific death or fallback to generic
        deaths = location_deaths.get(location, [
            f"In this desolate place, {killer_name} ends your journey with a final, decisive blow.",
            f"Your adventure ends here as {killer_name} proves to be your superior in combat.",
            f"The ground drinks your blood as {killer_name} stands triumphant over your broken body."
        ])
        
        return random.choice(deaths)
    
    def get_environmental_description(self, biome: str, context: str = "ambient") -> str:
        """Generate atmospheric environmental descriptions"""
        
        descriptions = {
            "desert": {
                "ambient": [
                    "The merciless sun beats down upon endless dunes of shifting sand.",
                    "Heat waves shimmer in the distance, creating dancing mirages of false hope.",
                    "Ancient bones peer through the sand, testament to the desert's hunger.",
                    "The air shimmers with intense heat as wind-carved rocks stand like silent sentinels.",
                    "Vultures circle overhead, patient scavengers waiting for the inevitable."
                ],
                "combat": [
                    "Sand swirls violently around the combatants in the scorching wind.",
                    "Each footfall kicks up clouds of burning sand particles.",
                    "The desert floor trembles with the impact of desperate combat.",
                    "Blood droplets sizzle and evaporate on contact with the superheated ground."
                ],
                "victory": [
                    "The desert wind carries away the sounds of battle, leaving only silence.",
                    "Sand begins to drift over the aftermath of violence.",
                    "The sun continues its relentless journey, indifferent to mortal struggles."
                ]
            },
            "forest": {
                "ambient": [
                    "Ancient trees whisper secrets in the gentle breeze, their branches forming a living cathedral.",
                    "Dappled sunlight filters through the dense canopy, creating patterns of light and shadow.",
                    "The air is thick with the rich scent of earth, moss, and growing things.",
                    "Mysterious sounds echo from the shadowed depths where few dare to venture.",
                    "Gnarled roots break through the forest floor like the fingers of sleeping giants."
                ],
                "combat": [
                    "Leaves rustle violently as the battle disturbs the forest's ancient peace.",
                    "Tree trunks provide cover and obstacles in the desperate fight for survival.",
                    "Branches crack and fall as the violence escalates beyond nature's tolerance.",
                    "Forest creatures flee in terror from the sounds of clashing steel and fury."
                ]
            },
            "mountains": {
                "ambient": [
                    "Towering peaks pierce the clouds like ancient spears thrust toward the heavens.",
                    "The thin air carries sounds for impossible distances across the rocky expanse.",
                    "Jagged stone formations create a maze of shadows and treacherous paths.",
                    "Snow-capped summits glisten in the distance like beacons of unreachable purity.",
                    "The wind howls through narrow passes, singing songs of isolation and danger."
                ],
                "combat": [
                    "The battle echoes off canyon walls with thunderous, amplified force.",
                    "Loose stones cascade down the mountainside with each heavy impact.",
                    "Combatants struggle for stable footing on the treacherous, shifting terrain.",
                    "The altitude makes each breath precious as the fight grows more desperate."
                ]
            },
            "tomb": {
                "ambient": [
                    "Ancient darkness seems to watch from every shadow and carved alcove.",
                    "The air is heavy with the weight of forgotten centuries and buried secrets.",
                    "Intricate stone carvings tell stories of civilizations lost to time.",
                    "Dust motes dance in artificial shafts of light like spirits of the dead.",
                    "The silence is so complete it seems to press against your very soul."
                ],
                "combat": [
                    "The ancient walls bear witness to yet another act of violence in their halls.",
                    "Echoes of battle disturb millennia of peaceful, deathly silence.",
                    "Stone faces carved in the walls seem to leer at the desperate combat.",
                    "The tomb's oppressive darkness appears to feed on the spilled blood."
                ]
            }
        }
        
        try:
            biome_descriptions = descriptions.get(biome, descriptions["desert"])
            context_descriptions = biome_descriptions.get(context, biome_descriptions["ambient"])
            return random.choice(context_descriptions)
        except Exception:
            return "The landscape bears silent witness to the unfolding drama."
    
    def _get_body_part(self, target_area: str) -> str:
        """Get random body part from specified area"""
        parts = self.body_parts.get(target_area, self.body_parts["torso"])
        return random.choice(parts)
    
    def _get_weapon_name(self, weapon_type: str) -> str:
        """Get descriptive weapon name"""
        weapons = self.weapon_types.get(weapon_type, self.weapon_types["melee"])
        return random.choice(weapons)
    
    def _get_environmental_modifier(self, environment: str, severity: str) -> Optional[str]:
        """Get environmental context for attacks"""
        
        modifiers = {
            "desert": {
                "fatal": "The desert heat intensifies the agony of your mortal wound.",
                "heavy": "Sand particles sting the fresh wound mercilessly.",
                "normal": "The arid wind carries away your cry of pain.",
                "light": "Desert sand clings to the minor cut."
            },
            "forest": {
                "fatal": "Your life's blood waters the forest floor.",
                "heavy": "Leaves flutter down like nature mourning your pain.",
                "normal": "Forest shadows seem to deepen with your suffering.",
                "light": "A gentle breeze carries away the sting of the wound."
            },
            "tomb": {
                "fatal": "Ancient stones seem to hunger for your spilled blood.",
                "heavy": "The tomb's darkness feeds on your agony.",
                "normal": "Dust swirls as if disturbed by your pain.",
                "light": "The ancestral spirits whisper of greater suffering to come."
            }
        }
        
        return modifiers.get(environment, {}).get(severity)


    def _get_massive_creature_attack(self, attacker_name: str, damage: int, 
                                   target_area: str, environmental_context: str) -> str:
        """Generate attack descriptions for massive creatures"""
        
        creature_type = attacker_name.lower()
        
        # Determine attack type based on native creature
        if "crimson" in creature_type or "leviathan" in creature_type:
            attacks = [
                f"The Crimson Leviathan's massive jaws snap shut inches from you, blood-stained teeth scraping across your {target_area}!",
                f"Enormous crimson claws rake across your {target_area} as the Leviathan strikes with desert fury!",
                f"The Leviathan's armored tail whips around, crushing impact against your {target_area}!",
                f"Ancient desert rage incarnate - the Crimson Leviathan's bite tears into your {target_area}!"
            ]
        elif "bone" in creature_type or "crusher" in creature_type:
            attacks = [
                f"The Bone Crusher's massive fist pounds down, crushing force impacting your {target_area}!",
                f"Slavering jaws close on your {target_area} with bone-splintering force!",
                f"The Crusher's claws rake down your {target_area} with devastating power!",
                f"A thunderous blow from the Bone Crusher sends shockwaves through your {target_area}!"
            ]
        elif "void" in creature_type or "tendril" in creature_type:
            attacks = [
                f"Void-touched tentacles wrap around your {target_area}, dark energy burning flesh!",
                f"The Void Tendril's corrupted appendages strike your {target_area} with Force-enhanced fury!",
                f"Dark energies crackle as void tendrils constrict around your {target_area}!",
                f"Reality tears as the Tendril's touch brands your {target_area} with Sith corruption!"
            ]
        elif "shadow" in creature_type or "stalker" in creature_type:
            attacks = [
                f"The Shadow Stalker materializes from darkness, claws raking your {target_area}!",
                f"Dark-enhanced speed blurs as the Stalker strikes your {target_area} multiple times!",
                f"The Stalker's shadow-cloaked form strikes your {target_area} with supernatural precision!",
                f"Darkness coalesces into claws that tear across your {target_area}!"
            ]
        elif "stone" in creature_type or "titan" in creature_type:
            attacks = [
                f"The Stone Titan's enormous stone fist crashes down on your {target_area}!",
                f"Massive granite fingers close around your {target_area} with crushing strength!",
                f"The Titan's fist impacts like an avalanche, force transmitted to your {target_area}!",
                f"Ancient stone strength focuses on your {target_area} with seismic force!"
            ]
        elif "tomb" in creature_type or "serpent" in creature_type:
            attacks = [
                f"The Tomb Serpent's ancient coils constrict around your {target_area} with crushing pressure!",
                f"Millenia-old fangs sink into your {target_area}, tomb-venom burning like acid!",
                f"The Serpent's massive body whips around, crushing your {target_area}!",
                f"Ancient tomb guardian strikes your {target_area} with primordial malice!"
            ]
        elif "dark" in creature_type or "weaver" in creature_type:
            attacks = [
                f"The Dark Weaver's Force-sensitive mandibles close on your {target_area} with eldritch fury!",
                f"Eight legs coordinate through the Force, claws raking across your {target_area}!",
                f"Sith-corrupted venom drips from hollow fangs as they pierce your {target_area}!",
                f"The Weaver's reality-warped webbing entangles your {target_area} in dark patterns!"
            ]
        elif "frost" in creature_type or "behemoth" in creature_type:
            attacks = [
                f"The Frost Behemoth's ice-encrusted claws tear through your {target_area}!",
                f"Massive arctic strength focuses on your {target_area} as permafrost spreads!",
                f"The Behemoth's frozen breath creates ice crystals as claws rake your {target_area}!",
                f"Eternal winter strikes your {target_area} with the force of a glacier!"
            ]
        else:
            # Generic massive creature
            attacks = [
                f"The massive creature's attack thunders into your {target_area}!",
                f"Enormous force impacts your {target_area} as the giant beast strikes!",
                f"The creature's massive form unleashes devastating power against your {target_area}!",
                f"Titanic strength focuses on your {target_area} with crushing impact!"
            ]
        
        # Add environmental flavor
        env_effects = {
            'desert': " Sand swirls in the wake of the massive attack!",
            'forest': " Ancient trees sway from the force of the blow!",
            'mountains': " The mountain stone cracks under the creature's power!",
            'tomb': " Dust and debris rain down from the impact!",
            'crash_site': " Wreckage shifts and groans from the tremors!"
        }
        
        description = random.choice(attacks)
        env_effect = env_effects.get(environmental_context, "")
        
        # Add damage-based intensity
        if damage >= 20:
            intensity = " The devastating force threatens to overwhelm you completely!"
        elif damage >= 15:
            intensity = " The crushing impact leaves you reeling!"
        elif damage >= 10:
            intensity = " The powerful blow sends shockwaves through your body!"
        else:
            intensity = " You barely withstand the creature's assault!"
        
        return f"{description}{env_effect}{intensity}"


# Global narrator instance
combat_narrator = CombatNarrator()