"""Sith Codex: lore entries, discovery, and artifacts.

This module provides a small data-driven codex for the Old Republic conversion.
It is intentionally self-contained and low-risk: discovery returns tuples and
does not modify player state itself. GameManager or other systems should call
the codex and apply effects (force echoes, stress) accordingly.
"""
from typing import Dict, Tuple, Set


class SithCodex:
    def __init__(self):
        # categories map -> (entry_id -> entry dict)
        self.categories: Dict[str, Dict[str, dict]] = {
            "sith_lords": {},
            "sith_philosophy": {},
            "sith_history": {},
            "sith_artifacts": {},
            "sith_sorcery": {},
        }
        # set of (category, entry_id) tuples
        self.discovered_entries: Set[Tuple[str, str]] = set()

    def add_entry(self, category: str, entry_id: str, title: str, content: str, force_echo: bool = False):
        if category not in self.categories:
            self.categories[category] = {}
        self.categories[category][entry_id] = {
            "title": title,
            "content": content,
            "force_echo": bool(force_echo),
        }

    def discover_entry(self, category: str, entry_id: str) -> Tuple[str | None, bool]:
        """Mark an entry discovered and return (message, is_force_echo).

        If the entry doesn't exist, returns (None, False).
        The caller should handle granting any player-side bonuses.
        """
        if category not in self.categories:
            return None, False
        entries = self.categories[category]
        if entry_id not in entries:
            return None, False
        if (category, entry_id) in self.discovered_entries:
            # already discovered; return the message but not a new force echo
            e = entries[entry_id]
            return f"CODEX: {e['title']}\n{e['content']}", False

        self.discovered_entries.add((category, entry_id))
        e = entries[entry_id]
        if e.get("force_echo"):
            return f"FORCE ECHO: {e['title']}\n{e['content']}", True
        return f"CODEX: {e['title']}\n{e['content']}", False


# Canon Sith lore examples; add more entries later.
SITH_LORE = {
    "sith_artifacts": {
        "ancient_holocrons": {"title": "Ancient Holocrons", "content": "Holocrons store vast knowledge in crystalline matrices. Sith holocrons often contain dark rituals and forbidden techniques.", "force_echo": True},
        "sith_swords": {"title": "Sith Swords", "content": "Forged with dark side alchemy, these blades retain power for millennia and can pierce Force defenses.", "force_echo": False},
        "meditation_spheres": {"title": "Meditation Spheres", "content": "Autonomous vessels that ferry Sith through dangerous space while they enter deep meditative trances.", "force_echo": False},
        "sith_lanvarok": {"title": "Sith Lanvarok", "content": "A wrist-mounted disc launcher used by ancient Sith warriors. Each disc could be imbued with dark energy.", "force_echo": False},
        "thought_bomb": {"title": "Thought Bomb", "content": "A devastating weapon that annihilates all Force-sensitive life in its radius. Banned by both Jedi and Sith.", "force_echo": True},
        "mask_of_nihilus": {"title": "Mask of Nihilus", "content": "This mask bound its wearer to an insatiable hunger for Force energy, granting terrible power at a horrific cost.", "force_echo": True},
        "dark_reaper": {"title": "Dark Reaper", "content": "An ancient Sith superweapon that harvested Force energy from living beings to power devastating beams.", "force_echo": False},
        "heart_of_the_universe": {"title": "Heart of the Universe", "content": "A legendary crystal said to amplify Force abilities a hundredfold, lost in the Unknown Regions.", "force_echo": False},
    },
    "sith_techniques": {
        "force_drain": {"title": "Force Drain", "content": "The ability to siphon life and Force energy from others, sustaining the user at the expense of their victim.", "force_echo": True},
        "force_storm": {"title": "Force Storm", "content": "The most powerful dark side ability: creating hyperspace wormholes to devastate entire fleets.", "force_echo": True},
        "essence_transfer": {"title": "Essence Transfer", "content": "A forbidden technique allowing a Sith to transfer their consciousness into another body, achieving a form of immortality.", "force_echo": True},
        "force_scream": {"title": "Force Scream", "content": "An overwhelming psychic wail that stuns and terrorizes all nearby, fueled by rage and pain.", "force_echo": False},
        "dark_side_healing": {"title": "Dark Side Healing", "content": "Unlike Jedi healing, this drains life from the environment to mend wounds, leaving corruption in its wake.", "force_echo": False},
        "sith_alchemy": {"title": "Sith Alchemy", "content": "The art of twisting living creatures and objects using the dark side, creating monstrosities and empowered items.", "force_echo": True},
        "force_walk": {"title": "Force Walk", "content": "Binding the spirits of defeated Sith to oneself, drawing on their power while risking being overwhelmed.", "force_echo": True},
        "art_of_the_small": {"title": "Art of the Small", "content": "Manipulating matter at a molecular level through the Force, allowing incredible feats of transmutation.", "force_echo": False},
        "deadly_sight": {"title": "Deadly Sight", "content": "Killing with a glance by projecting pure dark side energy through one's eyes into a victim's mind.", "force_echo": False},
        "force_plague": {"title": "Force Plague", "content": "Spreading disease through the Force itself, targeting specific genetic markers or Force signatures.", "force_echo": False},
    },
    "sith_prophecies": {
        "rule_of_two_prophecy": {"title": "The Rule of Two Prophecy", "content": "Darth Bane foresaw that only through limiting Sith numbers could true power be concentrated and preserved.", "force_echo": False},
        "chosen_one": {"title": "The Chosen One", "content": "Prophecies speak of one who will bring balance, though Sith interpret this as domination rather than harmony.", "force_echo": True},
        "eternal_empire": {"title": "The Eternal Empire", "content": "Visions of an empire that spans millennia, ruled by immortal Sith who have conquered death itself.", "force_echo": False},
        "dark_convergence": {"title": "Dark Convergence", "content": "A prophecy warning of a time when all Sith power will unite in one vessel, for better or worse.", "force_echo": False},
        "republic_fall": {"title": "Fall of the Republic", "content": "Ancient seers predicted the corruption and collapse of the galactic Republic from within.", "force_echo": False},
        "jedi_purge": {"title": "The Great Purge", "content": "Visions of a time when the Jedi would be hunted to near-extinction by their own allies.", "force_echo": True},
        "return_of_darkness": {"title": "Return of Darkness", "content": "Cyclical prophecies suggest the dark side rises and falls in great waves across galactic history.", "force_echo": False},
    },
    "sith_betrayals": {
        "banes_betrayal": {"title": "Bane's Betrayal", "content": "Darth Bane betrayed his entire order, engineering their destruction to implement the Rule of Two.", "force_echo": False},
        "revan_turned": {"title": "Revan's Turn", "content": "The Jedi Revan fell to the dark side during the Mandalorian Wars, becoming a Sith conqueror.", "force_echo": True},
        "malak_strikes": {"title": "Malak's Strike", "content": "Darth Malak betrayed his master Revan, bombarding his ship in a failed assassination attempt.", "force_echo": False},
        "zannah_waits": {"title": "Zannah's Patience", "content": "Darth Zannah patiently waited for Darth Bane to show weakness before striking to claim the mantle of Dark Lord.", "force_echo": False},
        "millennial_breaks": {"title": "Millennial Breaks the Rule", "content": "Darth Millennial rejected the Rule of Two, founding his own splinter order on Dromund Kaas.", "force_echo": False},
        "plagueis_murdered": {"title": "Plagueis' Murder", "content": "Darth Sidious killed his master Plagueis in his sleep, claiming power through ultimate treachery.", "force_echo": True},
        "vader_redeemed": {"title": "Vader's Redemption", "content": "Darth Vader's final betrayal was of the dark side itself, saving his son and destroying the Emperor.", "force_echo": True},
        "apprentice_uprising": {"title": "The Apprentice Uprising", "content": "Throughout history, Sith apprentices have plotted elaborate schemes to overthrow their masters.", "force_echo": False},
    },
    "sith_philosophy": {
        "code": {
            "title": "Sith Tenets (summary)",
            "content": (
                "A core Sith teaching emphasizes passion and the harnessing of strong emotion to fuel personal power.\n"
                "Sith philosophy values ambition, mastery, and the will to impose one's vision on the galaxy.\n"
                "Practitioners are taught to seek strength through struggle and to transform suffering into power."
            ),
            "force_echo": True,
        },
        "rule_of_two": {
            "title": "The Rule of Two (concept)",
            "content": (
                "After generations of internal war the Sith consolidated into a strategy of secrecy: a single Master and\n"
                "a single Apprentice so that power would be concentrated and betrayal limited. The Rule of Two shaped\n"
                "Sith politics for centuries thereafter in secretive orders and hidden lineages."
            ),
            "force_echo": False,
        },
        "ambition_and_corruption": {
            "title": "Ambition and Corruption",
            "content": (
                "Ambition is a virtue to the Sith; unchecked, it becomes corruption. Sith schools teach techniques to\n"
                "focus desire into discipline, but many masters warn that craving without control leads to self-destruction."
            ),
            "force_echo": False,
        },
        "dominance_ethic": {"title": "Dominance as Ethic", "content": "A recurring Sith idea is that moral order is imposed by the strong upon the weak; mastery is justice.", "force_echo": False},
        "will_over_fate": {"title": "Will over Fate", "content": "Sith training emphasizes shaping fate through will and decisive action rather than passive acceptance.", "force_echo": False},
        "suffering_as_tool": {"title": "Suffering as Tool", "content": "Suffering and loss are reframed as fuel for resolve; hardship is a crucible to forge power.", "force_echo": False},
        "merit_of_strength": {"title": "Merit of Strength", "content": "Sith test loyalty and skill; those who prove strength claim authority and inheritance of lore.", "force_echo": False},
        "secrecy_and_influence": {"title": "Secrecy and Influence", "content": "Discretion, networks and manipulation often achieve what open force cannot; influence is a weapon.", "force_echo": False},
        "self_transformation": {"title": "Self-Transformation", "content": "Many Sith undergo rituals and trials to remold themselves, shedding weakness for a new identity.", "force_echo": False},
        "ethics_of_power": {"title": "Ethics of Power", "content": "Sith ethics aren't absence of ethics but a reframing: ends justify the disciplined pursuit of power.", "force_echo": False},
    },
    "sith_history": {
        "ancient_orders": {"title": "Ancient Sith Orders", "content": "Early Sith cultures mixed Force practices with local ritual and hierarchy, leaving arcane artifacts.", "force_echo": False},
        "brotherhood_and_empire": {"title": "Brotherhoods and Empires", "content": "Sith polities have repeatedly centralized and collapsed under internal rivalries; their ruins dot many worlds.", "force_echo": False},
        "fallen_scholars": {"title": "Fallen Scholars", "content": "Scholars who delved too deep into forbidden arts often left unstable legacies: relics, doctrines, and curses.", "force_echo": False},
        "the_dark_recesses": {"title": "The Dark Recesses", "content": "Hidden libraries and vaults store forbidden techniques; retrieving them is as dangerous as using them.", "force_echo": False},
        "lineages_and_inheritance": {"title": "Lineages and Inheritance", "content": "Sith lineages pass secret knowledge through apprenticeships, often encoded to survive betrayal.", "force_echo": False},
        "collapse_cycles": {"title": "Cycles of Collapse", "content": "Periods of unity often precede devastating internal wars that scatter an era's achievements.", "force_echo": False},
        "artifact_redistribution": {"title": "Artifact Redistribution", "content": "Relics often move between factions, carrying echoes of their makers' will and folly.", "force_echo": False},
        "cultivated_ruins": {"title": "Cultivated Ruins", "content": "Sith sometimes preserved ruins as tests; only the bold or foolish enter to claim secrets. ", "force_echo": False},
        "strategy_and_subterfuge": {"title": "Strategy and Subterfuge", "content": "Sith success frequently relied on long games: undermining rivals and controlling narratives.", "force_echo": False},
        "the_hidden_emperors": {"title": "Hidden Emperors", "content": "Some Sith ruled from the shadows, using proxies and networks to avoid direct exposure while shaping events.", "force_echo": False},
    },
    "sith_lords": {
        "shadow_masters": {"title": "Shadow Masters", "content": "Certain Sith are remembered for subtlety, manipulating generations through plans and proteges.", "force_echo": True},
        "warlord_sovereigns": {"title": "Warlord Sovereigns", "content": "Warlords raised armies and fleets; their short-lived empires left deep scars on stellar maps.", "force_echo": False},
        "tacticians": {"title": "Tacticians", "content": "Some Sith made their mark by battlefield cunning and strategic genius rather than raw sorcery.", "force_echo": False},
        "ritualists": {"title": "Ritualist Lords", "content": "A subset obsessed with ritual and relics, they built sanctums and libraries to preserve dark arts.", "force_echo": False},
        "patrician_influencers": {"title": "Patrician Influencers", "content": "These lords controlled trade, information, and nobility, using wealth to corrupt institutions subtly.", "force_echo": False},
        "exile_legends": {"title": "Exile Legends", "content": "Exiled Sith reinvented doctrine on distant worlds, creating syncretic traditions and dangerous mutations.", "force_echo": False},
        "duelist_champions": {"title": "Duelist Champions", "content": "Masters of individual combat, their duels taught students brutality and grace in equal measure.", "force_echo": False},
        "scholar_lords": {"title": "Scholar Lords", "content": "Some pursued knowledge over conquest, documenting arcana and experimenting with Force theory.", "force_echo": False},
        "architects_of_ruin": {"title": "Architects of Ruin", "content": "These figures orchestrated empire-scale tragedies to remake the galaxy on their terms.", "force_echo": False},
        "keepers_of_covenants": {"title": "Keepers of Covenants", "content": "Certain Lords bound treaties and covenants that endured beyond their lifetimes, shaping future conflicts.", "force_echo": False},
    },
    "sith_sorcery": {
        "dark_arts_overview": {"title": "Sith Sorcery (overview)", "content": "Sith sorcery blends ritual, mental discipline and artifacts; practitioners manipulate energy, memory and life.", "force_echo": False},
        "blood_rites": {"title": "Blood Rites and Binding", "content": "Some schools used blood and kinship rites to bind apprentices or spirits, producing strong but costly bonds.", "force_echo": False},
        "memory_tampering": {"title": "Memory and Will", "content": "Techniques exist to alter memory and identity; masters used them to secure obedience and hide truth.", "force_echo": False},
        "life_energy_manipulation": {"title": "Life Energy Manipulation", "content": "Advanced rituals redirect life force for healing or harm, often draining practitioners in the process.", "force_echo": False},
        "spirits_and_bindings": {"title": "Spirits and Bindings", "content": "Some Sith bound spirits to objects as guardians or conduits; these bindings can haunt successors.", "force_echo": False},
        "artifact_sanctification": {"title": "Artifact Sanctification", "content": "Sith sanctified devices to carry directives and echoes, making objects active participants in schemes.", "force_echo": False},
        "shadow_illusion": {"title": "Shadow Illusion", "content": "Illusory craft hides truth and convinces the unwary; masters used it to mask their movements and intents.", "force_echo": False},
        "chant_and_formulas": {"title": "Chants and Formulas", "content": "Short formulaic chants focus ritual energy; their words are often fragmented and dangerous to recite incorrectly.", "force_echo": False},
        "soul_afflictions": {"title": "Soul Afflictions", "content": "Some techniques scar the psyche; survivors speak of echoes and compulsions that linger for generations.", "force_echo": False},
        "forbidden_mechanics": {"title": "Forbidden Mechanics", "content": "Technical approaches to ritual that breach natural law—useful but destabilizing—are kept in locked tomes.", "force_echo": False},
    },
    "sith_tactics": {
        "undermining_authority": {"title": "Undermining Authority", "content": "Sith prefer to erode opponents from within: spread doubt, exploit vices, and turn allies into liabilities.", "force_echo": False},
        "divide_and_rule": {"title": "Divide and Rule", "content": "Sowing factionalism weakens rivals; a fractured enemy is easier to dominate than a united one.", "force_echo": False},
        "asymmetric_warfare": {"title": "Asymmetric Warfare", "content": "Guerrilla tactics, sabotage and propaganda multiply the effect of limited forces against larger foes.", "force_echo": False},
        "political_entrenchment": {"title": "Political Entrenchment", "content": "Control key institutions to lock in influence—courts, trade, and information are battlegrounds as much as armies.", "force_echo": False},
        "economic_leverage": {"title": "Economic Leverage", "content": "Wealth funds schemes, bribes and mercenaries; controlling resources is a long-term advantage.", "force_echo": False},
        "proxy_conflict": {"title": "Proxy Conflict", "content": "Use third parties to fight wars by proxy, preserving deniability while shaping outcomes. ", "force_echo": False},
        "ritual_fronts": {"title": "Ritual Fronts", "content": "Institutions such as cults, universities or companies can mask ritual activity and recruit unwitting supporters.", "force_echo": False},
        "asymmetric_diplomacy": {"title": "Asymmetric Diplomacy", "content": "Negotiate concessions that seem small but compound into strategic advantages over time.", "force_echo": False},
        "intel_and_counterintelligence": {"title": "Intel and Counterintelligence", "content": "Control information flows and plant disinformation to shape enemy decisions and morale.", "force_echo": False},
        "supply_chain_disruption": {"title": "Supply Chain Disruption", "content": "Disrupt logistics to starve enemies of materiel and will to fight without direct confrontation.", "force_echo": False},
    },
    "sith_rituals": {
        "initiation_trials": {"title": "Initiation Trials", "content": "Apprentice trials test resolve, cunning and brutality; passing binds the initiate to master and doctrine.", "force_echo": False},
        "oaths_and_bonds": {"title": "Oaths and Bonds", "content": "Oaths written in blood or memory create powerful social and spiritual obligations among Sith kin.", "force_echo": False},
        "harvesting_energies": {"title": "Harvesting Energies", "content": "Rituals to harvest ambient energies from places of death or power are common but risky.", "force_echo": False},
        "reconstruction_rites": {"title": "Reconstruction Rites", "content": "Some rituals rebuild a shattered mind to create a more obedient vessel for knowledge.", "force_echo": False},
        "binding_contracts": {"title": "Binding Contracts", "content": "Ritual contracts can attach obligations to objects or people, surviving generations until broken by force.", "force_echo": False},
        "obfuscation_rites": {"title": "Obfuscation Rites", "content": "Rites designed to hide locations and artifacts by folding perception around them.", "force_echo": False},
        "ritual_amplifiers": {"title": "Ritual Amplifiers", "content": "Objects or sites amplify ritual effects; finding or crafting amplifiers is often a long-term objective.", "force_echo": False},
        "safeguard_obligations": {"title": "Safeguard Obligations", "content": "Rituals sometimes require caretakers who then inherit consequences and protection duties.", "force_echo": False},
        "binding_spells": {"title": "Binding Spells", "content": "Spells that tether entities to places or objects; breaking them can release allied curses.", "force_echo": False},
        "covenant_maintenance": {"title": "Covenant Maintenance", "content": "Long-term rituals maintain pacts; neglect can cause degradation or revolt among bound forces.", "force_echo": False},
    },
    "sith_planets": {
        "ruin_worlds": {"title": "Ruin Worlds", "content": "Planets scarred by rituals or wars are rich sites for relic hunters and dangerous to traverse.", "force_echo": False},
        "sanctified_sites": {"title": "Sanctified Sites", "content": "Certain geographies channel the dark side; Sith build sanctums there to focus power.", "force_echo": False},
        "hidden_bastions": {"title": "Hidden Bastions", "content": "Fortified enclaves where Sith stockpile relics and train generations away from prying eyes.", "force_echo": False},
        "mystic_wastes": {"title": "Mystic Wastes", "content": "Regions with lingering energy distort travel and thought, often used as trials or prison sites.", "force_echo": False},
        "resource_planets": {"title": "Resource Planets", "content": "Worlds exploited for rare reagents used in ritual and artifact crafting.", "force_echo": False},
        "contention_zones": {"title": "Contention Zones", "content": "Strategic systems repeatedly fought over due to their location and resources.", "force_echo": False},
        "shrouded_asterisms": {"title": "Shrouded Asterisms", "content": "Clusters of systems where Sith fleets and secret bases are rumored to hide.", "force_echo": False},
        "monumentary_sites": {"title": "Monumentary Sites", "content": "Sith built monuments as declarations of power; they often mark caches or traps.", "force_echo": False},
        "anchored_observatories": {"title": "Anchored Observatories", "content": "Orbital observatories used to monitor and control trade and communication lanes.", "force_echo": False},
        "blighted_terrain": {"title": "Blighted Terrain", "content": "Terrain corrupted by ritual aftermath where life struggles and the Force is altered.", "force_echo": False},
    },
    "historical_conflicts": {
        "hundred_year_darkness": {"title": "The Hundred-Year Darkness", "content": "The first Great Schism: when Dark Jedi rebelled against the Order, creating the original Sith philosophy. These exiles intermingled with the red-skinned Sith species on Korriban, founding an empire that would haunt the galaxy for millennia.", "force_echo": True},
        "great_hyperspace_war": {"title": "Great Hyperspace War", "content": "5,000 BBY: The Sith Empire's first contact with the Republic ended in devastating war. Though the Sith lost, they proved the dark side's terrifying potential. Naga Sadow's sorcery turned stars into weapons.", "force_echo": True},
        "exar_kun_war": {"title": "Exar Kun's Brotherhood", "content": "4,000 BBY: Jedi Knight Exar Kun fell to ancient Sith teachings and created a new Brotherhood. His war killed billions and corrupted entire Jedi enclaves. The Jedi barely survived by bombing Yavin 4 into a tomb.", "force_echo": True},
        "mandalorian_wars": {"title": "The Mandalorian Wars", "content": "The conflict that broke Revan: while the Jedi Council debated, the Mandalorians slaughtered millions. Revan and Malak defied the Council to save the Republic—but found something dark in the Unknown Regions that changed them forever.", "force_echo": True},
        "jedi_civil_war": {"title": "Jedi Civil War", "content": "Revan and Malak returned as Sith Lords with a vast fleet, conquering world after world. The Republic teetered on collapse until Bastila Shan's battle meditation and a twist of fate turned the tide. But at what cost?", "force_echo": True},
        "first_jedi_purge": {"title": "First Jedi Purge", "content": "After Revan's fall, Darth Nihilus and Darth Sion nearly exterminated the Jedi Order. Nihilus consumed entire planets to feed his hunger. Only the Exile and a handful of survivors kept the light alive.", "force_echo": True},
        "new_sith_wars": {"title": "The New Sith Wars", "content": "For a thousand years, Jedi and Sith armies clashed openly across the galaxy. Worlds burned, populations were enslaved, and both sides committed atrocities. The war only ended with the thought bomb at Ruusan.", "force_echo": True},
        "battle_of_ruusan": {"title": "Battle of Ruusan", "content": "The thought bomb detonated by Lord Kaan killed every Force user on the battlefield—both Jedi and Sith. Only Darth Bane survived, hidden in the chaos, to forge the Rule of Two from the ashes.", "force_echo": True},
        "clone_wars": {"title": "The Clone Wars", "content": "The greatest deception: a Sith Lord orchestrated both sides of a galactic war, using it to paint the Jedi as warlords and traitors. Democracy died in thunderous applause as Palpatine declared himself Emperor.", "force_echo": True},
        "order_66": {"title": "Order 66", "content": "In one coordinated strike, clone troopers—loyal friends and comrades—turned on their Jedi generals. Thousands of Jedi died in seconds. The survivors became hunted fugitives in a galaxy that forgot them.", "force_echo": True},
        "sith_empire_reclaims": {"title": "The Sith Empire Returns", "content": "3,681 BBY: The True Sith Empire emerged from hiding to sack Coruscant itself. The Jedi Temple burned. The Republic was forced into a humiliating peace, proving the dark side never truly disappears—it waits.", "force_echo": True},
        "korriban_academy": {"title": "Korriban Academy Trials", "content": "For thousands of years, acolytes competed in brutal trials at Korriban's Sith Academy. Only the strongest, most cunning, and most ruthless survived to become apprentices. Weakness meant death—or worse.", "force_echo": False},
    },
    "dark_side_perspective": {
        "jedi_hypocrisy": {"title": "Jedi Hypocrisy Exposed", "content": "The Jedi claim to serve peace but have fought in countless wars. They speak of non-attachment yet form hierarchies of power. They preach compassion while denying their members love. Is this not hypocrisy?", "force_echo": False},
        "jedi_dogma": {"title": "The Dogma of Denial", "content": "The Jedi Code demands suppression of natural emotion. Fear, anger, passion—all are condemned. But emotion is what makes us alive! The Jedi create broken beings who deny their own humanity in pursuit of false serenity.", "force_echo": False},
        "true_freedom": {"title": "True Freedom Through Power", "content": "The Sith offer what the Jedi never can: freedom. Freedom to feel, to love, to hate, to pursue your dreams without shame. Only through strength can you truly shape your destiny. The weak rely on codes; the strong create their own path.", "force_echo": False},
        "peace_is_lie": {"title": "Peace Is a Lie", "content": "The Jedi promise peace, but peace is stagnation. Growth requires conflict. Evolution demands struggle. The dark side embraces this truth: through passion, we find strength. Through strength, we gain power. Through power, we achieve victory.", "force_echo": True},
        "attachment_truth": {"title": "The Truth of Attachment", "content": "The Jedi forbid attachment, claiming it leads to darkness. But attachment gives us purpose! Love makes us fight harder. Loyalty bonds us to causes greater than ourselves. The Jedi's fear of attachment is fear of living fully.", "force_echo": False},
        "pragmatic_power": {"title": "Pragmatism Over Ideology", "content": "While Jedi debate philosophy, Sith act. When disaster strikes, who saves more lives: the pacifist who hesitates, or the warrior who strikes decisively? Power without will is wasted. The dark side offers both.", "force_echo": False},
        "jedi_failed_republic": {"title": "The Jedi Failed the Republic", "content": "For a thousand generations, the Jedi served the Republic as guardians. Yet they allowed slavery, corruption, and inequality to flourish. They became politicians in robes, too blind to see the rot within. Was this service or complicity?", "force_echo": True},
        "emotion_is_power": {"title": "Emotion Is Power", "content": "The Jedi fear emotion because they know its power. Anger can fuel impossible feats. Love can drive unbreakable will. Passion can reshape reality itself. The dark side doesn't create these emotions—it unleashes what was always there.", "force_echo": False},
        "destiny_forged": {"title": "Forge Your Own Destiny", "content": "The Jedi speak of following the Force's will, surrendering to destiny. The Sith know better: destiny is forged, not followed. The Force is a tool, not a master. Those who bend to fate remain slaves. Those who break it become legends.", "force_echo": False},
        "cost_of_compassion": {"title": "The Cost of Compassion", "content": "Compassion without strength is useless. You cannot save the drowning if you drown yourself. The Jedi's bleeding hearts led to the Republic's downfall. The Sith understand: first secure your power, then wield it as you see fit.", "force_echo": False},
        "strength_respects_strength": {"title": "Strength Respects Strength", "content": "The galaxy respects one thing: power. Ideals without strength are dreams. The Jedi's philosophy collapsed the moment a stronger will challenged it. The Sith endure because we build foundations of genuine might.", "force_echo": False},
        "evolution_through_conflict": {"title": "Evolution Through Conflict", "content": "Nature proves this truth: predators sharpen prey, competition breeds excellence, struggle creates adaptation. The Sith embrace conflict as the engine of progress. The Jedi's enforced peace creates weakness and complacency.", "force_echo": False},
        "passion_creates_meaning": {"title": "Passion Creates Meaning", "content": "A life without passion is a life without purpose. What drives you to rise each day? Love? Ambition? Revenge? The Sith honor these drives. The Jedi would extinguish your fire and call it enlightenment.", "force_echo": False},
        "false_martyrs": {"title": "False Martyrs", "content": "The Jedi celebrate sacrifice and martyrdom. But what good is a dead hero? The Sith survive to fight another day. We honor victory, not beautiful failure. History is written by the living, not noble corpses.", "force_echo": False},
    },
    "force_philosophy": {
        "living_force": {"title": "The Living Force", "content": "Some Jedi believe the Force exists in all living things, connecting and binding them. This view emphasizes the present moment and intuition over rigid dogma. Qui-Gon Jinn championed this philosophy.", "force_echo": False},
        "unifying_force": {"title": "The Unifying Force", "content": "The Unifying Force philosophy sees destiny and prophecy. It emphasizes that the Force has a will that guides events across time. The Jedi Council traditionally followed this view, seeking to serve the Force's grand design.", "force_echo": False},
        "force_is_tool": {"title": "The Force as Tool", "content": "Many Sith view the Force not as a deity or guide, but as a resource to be harnessed. Like fire or gravity, it exists to be understood and exploited by those with the knowledge and will.", "force_echo": False},
        "dark_light_balance": {"title": "Balance of Dark and Light", "content": "Some philosophers argue the Force needs both darkness and light to be complete. Just as nature requires predators and prey, the galaxy may need both Jedi and Sith. Is balance found in the victory of light—or in eternal opposition?", "force_echo": True},
        "potentium_heresy": {"title": "The Potentium Heresy", "content": "A banned Jedi philosophy claimed the Force itself is neither light nor dark—only its users' intent matters. The Council rejected this view as dangerously naive, but some Dark Jedi embraced it to justify their actions.", "force_echo": False},
        "cosmic_force": {"title": "The Cosmic Force", "content": "Upon death, Force users become one with the Cosmic Force—the energy field that binds the galaxy. Some Jedi learn to retain consciousness after death, becoming Force ghosts. The Sith seek the same through darker means.", "force_echo": False},
        "vergence_anomalies": {"title": "Vergence Anomalies", "content": "Locations where the Force concentrates unnaturally—vergences—hold immense power. Mortis, Dagobah's cave, the Wellspring on Ahch-To: these places can amplify abilities or grant visions. Both orders seek them.", "force_echo": True},
        "midichlorian_truth": {"title": "The Midichlorian Truth", "content": "Microscopic organisms in cells called midi-chlorians allow beings to touch the Force. High counts indicate potential. The Jedi use this for screening, while some Sith have experimented with artificially raising counts—with disturbing results.", "force_echo": False},
        "force_wound_trauma": {"title": "Force Wounds", "content": "Traumatic events can scar the Force itself, creating 'wounds' or 'echoes' that persist. Malachor V, Alderaan's destruction, mass deaths at Katarr—these horrors left permanent stains. Some Sith deliberately create such wounds for power.", "force_echo": True},
        "shatterpoint_theory": {"title": "Shatterpoint Theory", "content": "Master Mace Windu could perceive 'shatterpoints'—critical moments where small actions cause huge consequences. This rare ability reveals the Force's interconnected nature, where everything affects everything else.", "force_echo": False},
    },
    "canon_history": {
        "rakatan_infinite_empire": {"title": "The Rakata Infinite Empire", "content": "30,000 years ago, the Force-using Rakata conquered thousands of worlds with their technology. They built the Star Forge—a station that fed on the dark side to mass-produce warships. Their civilization collapsed into barbarism.", "force_echo": True},
        "jedi_founding": {"title": "Founding of the Jedi", "content": "25,000 years ago on Ahch-To, the first Jedi Temple was built. Ancient scholars studied the Force, seeking enlightenment. They formed the principles that would guide the Order for millennia—though not all agreed on the path.", "force_echo": False},
        "valley_of_jedi": {"title": "Valley of the Jedi", "content": "On Ruusan, a vergence in the Force formed where thousands died in battle. Their spirits became trapped there, creating a wellspring of power. Both Jedi and Sith have sought to tap this reservoir.", "force_echo": True},
        "dathomir_witches": {"title": "The Nightsisters of Dathomir", "content": "On Dathomir, Force-using witches practice unique magicks drawing on both light and dark. Mother Talzin's coven bred warriors like Darth Maul, combining ancient sorcery with Sith training.", "force_echo": False},
        "ancient_sith_purebloods": {"title": "The Original Sith", "content": "The Sith were originally a red-skinned species on Korriban with strong Force sensitivity. When Dark Jedi exiles arrived, they conquered and interbred with the natives, adopting the name 'Sith' for themselves.", "force_echo": False},
        "jedi_temple_coruscant": {"title": "The Jedi Temple on Coruscant", "content": "Built atop an ancient Sith shrine, the Jedi Temple stood for thousands of years as a symbol of peace. Ironically, the dark side nexus beneath may have clouded the Jedi's vision during Palpatine's rise.", "force_echo": True},
        "lehon_star_forge": {"title": "The Star Forge Discovery", "content": "Revan and Malak found the Star Forge in the Unknown Regions—a Rakatan relic that could build infinite fleets. But the station corrupted them, whispering dark promises. Its power came at the cost of their souls.", "force_echo": True},
        "mortis_force_wielders": {"title": "The Ones of Mortis", "content": "On a mystical realm called Mortis lived the Father, Son (dark side), and Daughter (light side)—embodiments of the Force itself. Anakin Skywalker encountered them, glimpsing his future as Vader. Their realm exists outside normal space.", "force_echo": True},
        "malachor_superweapon": {"title": "The Mass Shadow Generator", "content": "At Malachor V, the Exile activated a superweapon that crushed both Republic and Mandalorian fleets using artificial gravity. The psychic scream of thousands dying at once broke her connection to the Force. The planet became a wound.", "force_echo": True},
        "alderan_destruction": {"title": "Alderaan's Destruction", "content": "The Death Star annihilated Alderaan, killing billions instantly. Obi-Wan felt their deaths ripple through the Force—'as if millions of voices suddenly cried out in terror and were suddenly silenced.' A wound that never healed.", "force_echo": True},
    },
    "loading_wisdom": {
        # Short, atmospheric lore snippets for loading screens
        "power_chains": {"title": "Power and Chains", "content": "The dark side promises freedom through power, yet every Sith is ultimately a slave to their passions.", "force_echo": False},
        "fear_tool": {"title": "Fear as Tool", "content": "The Sith understand that fear is not weakness—it is the first step to power. Only fools claim to be fearless.", "force_echo": False},
        "ancient_patience": {"title": "Ancient Patience", "content": "The Sith have waited in shadows for millennia. Time is their weapon; patience their discipline.", "force_echo": False},
        "betrayal_tradition": {"title": "Tradition of Betrayal", "content": "Every Sith apprentice dreams of surpassing their master. This is not treachery—it is the way.", "force_echo": False},
        "ruins_speak": {"title": "The Ruins Remember", "content": "Sith tombs are never truly empty. The echoes of ancient Lords still whisper to those who listen.", "force_echo": False},
        "knowledge_cost": {"title": "Knowledge's Price", "content": "Forbidden knowledge always demands payment. The question is: what are you willing to sacrifice?", "force_echo": False},
        "passion_fuel": {"title": "Passion's Fuel", "content": "Anger, love, hatred, desire—these are not weaknesses. They are the fuel that powers the dark side.", "force_echo": False},
        "victory_survival": {"title": "Victory Through Survival", "content": "Dead heroes win no wars. The Sith value survival above all—for only the living can claim victory.", "force_echo": False},
        "artifacts_hunger": {"title": "Artifacts Hunger", "content": "Sith artifacts are not mere objects. They hunger for use, whispering to potential wielders across the centuries.", "force_echo": False},
        "balance_myth": {"title": "The Balance Myth", "content": "The Jedi speak of balance, but the Force is chaos. Order is the illusion; entropy is truth.", "force_echo": False},
        "suffering_teacher": {"title": "Suffering Teaches", "content": "Pain is the greatest teacher. Those who embrace suffering become stronger than those who flee from it.", "force_echo": False},
        "legacy_echoes": {"title": "Echoes of Legacy", "content": "Every Sith Lord leaves an echo in the Force. Their ambitions, their failures—all persist as warnings and temptations.", "force_echo": False},
        "codes_chains": {"title": "Codes Are Chains", "content": "The Jedi bind themselves with codes and oaths. The Sith break every chain to forge their own path.", "force_echo": False},
        "darkness_patient": {"title": "Darkness Is Patient", "content": "The dark side does not rush. It waits in corners, in shadows, in the hearts of the desperate. It is always ready.", "force_echo": False},
        "ambition_virtue": {"title": "Ambition's Virtue", "content": "The Jedi call ambition a vice. The Sith know it is the engine of civilization—without it, stagnation and death.", "force_echo": False},
        "secrets_buried": {"title": "Buried Secrets", "content": "On a thousand worlds lie buried secrets: holocrons, weapons, rituals. The galaxy is a graveyard of lost power.", "force_echo": False},
        "strength_reveals": {"title": "Strength Reveals Truth", "content": "Philosophy means nothing without the strength to enforce it. The strong define reality; the weak accept it.", "force_echo": False},
        "meditation_danger": {"title": "Meditation's Danger", "content": "To meditate in a place of darkness is to invite communion with ancient evils. But knowledge comes to the bold.", "force_echo": False},
        "fate_malleable": {"title": "Fate Is Malleable", "content": "Prophecy and destiny are suggestions, not certainties. The truly powerful bend fate itself to their will.", "force_echo": False},
        "war_crucible": {"title": "War's Crucible", "content": "War reveals truth. In battle, philosophy falls away and only power—or its absence—remains.", "force_echo": False},
        # Additional expanded wisdom
        "korriban_sands": {"title": "Korriban's Sands", "content": "The red sands of Korriban remember every Lord who walked them. Step carefully—the dead are watching.", "force_echo": False},
        "holocron_whispers": {"title": "Holocron Whispers", "content": "A holocron is more than memory—it is a fragment of its maker's will, waiting to corrupt or enlighten.", "force_echo": False},
        "rule_necessity": {"title": "The Rule's Necessity", "content": "The Rule of Two was born from weakness. A thousand Sith tore themselves apart. Only two could survive.", "force_echo": False},
        "master_student": {"title": "Master and Student", "content": "The Sith call it training. The truth? Every lesson is a test. Every test a potential execution.", "force_echo": False},
        "dark_meditation": {"title": "Dark Meditation", "content": "Jedi meditate for peace. Sith meditate for power. Both enter the same silence—but emerge changed differently.", "force_echo": False},
        "lightsaber_red": {"title": "The Red Blade", "content": "A Sith lightsaber bleeds red because the kyber crystal screams. It remembers being broken, bent to serve darkness.", "force_echo": False},
        "tomb_guardians": {"title": "Tomb Guardians", "content": "The dead Sith Lords left guardians: beasts, droids, and worse. Some traps are millennia old and still hungry.", "force_echo": False},
        "two_apprentices": {"title": "Two Apprentices", "content": "A master who trains two apprentices ensures they will fight. The survivor proves worthy. The weak one? Forgotten.", "force_echo": False},
        "sith_eyes": {"title": "Sith Eyes", "content": "The dark side burns through flesh. First the eyes change—yellow, orange, red. A window into the soul's corruption.", "force_echo": False},
        "ancient_language": {"title": "Ancient Tongue", "content": "The Sith language is forbidden for good reason. Some words carry power in their syllables. Speak them wrong and die.", "force_echo": False},
        "force_lightning": {"title": "Lightning's Price", "content": "Force lightning is not learned—it is unleashed. Pure rage channeled into destruction. Control it, or it controls you.", "force_echo": False},
        "sith_academy": {"title": "Academy Trials", "content": "At the Sith Academy, graduation means your rivals are dead. There are no ceremonies. Only survivors.", "force_echo": False},
        "mask_identity": {"title": "The Mask's Purpose", "content": "Sith Lords wear masks not for mystery, but transformation. The mask becomes the true face; the man beneath dies.", "force_echo": False},
        "dark_nexus": {"title": "Dark Side Nexus", "content": "Certain places overflow with dark energy: caves, temples, battlefields. Stand in them too long and they seep inside.", "force_echo": False},
        "sith_ship": {"title": "Sith Vessels", "content": "Sith ships are more than metal. They're built with alchemy, blood rituals, and fear. Some ships are alive.", "force_echo": False},
        "apprentice_patience": {"title": "Apprentice's Patience", "content": "An apprentice must wait for weakness. Strike too soon—death. Wait too long—obsolescence. Timing is everything.", "force_echo": False},
        "empire_ashes": {"title": "Empire Ashes", "content": "Every Sith Empire has crumbled to dust. Yet from each collapse, new Sith rise. The cycle is eternal.", "force_echo": False},
        "jedi_weakness": {"title": "Jedi Weakness", "content": "The Jedi's greatest weakness is mercy. The Sith have no such handicap. Hesitation is death.", "force_echo": False},
        "ritual_blood": {"title": "Blood Ritual", "content": "Sith rituals demand sacrifice. The greater the power sought, the higher the price. Blood opens doors.", "force_echo": False},
        "dark_corruption": {"title": "Slow Corruption", "content": "The dark side corrupts slowly at first. A small choice, a justified anger. Then one day you wake and can't recognize yourself.", "force_echo": False},
        "sith_immortality": {"title": "Sith Immortality", "content": "True Sith seek immortality not through peace, but through persistence. Essence transfer, cloning, possession—anything to endure.", "force_echo": False},
        "force_bond": {"title": "Force Bonds", "content": "Force bonds connect souls across distance. The Jedi call them sacred. The Sith call them weapons.", "force_echo": False},
        "dark_prophets": {"title": "Dark Prophets", "content": "Sith seers glimpse possible futures. But the dark side shows only what it wants seen. Trust prophecy at your peril.", "force_echo": False},
        "sith_philosophy": {"title": "Sith Philosophy", "content": "The Sith Code is simple: break your chains. What chains bind you? Fear? Morality? Weakness? Break them all.", "force_echo": False},
        "tomb_treasure": {"title": "Tomb Treasures", "content": "Every tomb promises power. Most deliver only death. The truly valuable artifacts are guarded by more than traps.", "force_echo": False},
        "dark_apprentice": {"title": "The First Apprentice", "content": "Taking your first apprentice is declaring yourself a master. It also paints a target. They're already planning your death.", "force_echo": False},
        "sith_legacy": {"title": "Legacy Preservation", "content": "Sith preserve their knowledge in holocrons, tombs, and artifacts. Death is temporary. Legacy is everything.", "force_echo": False},
        "force_scream": {"title": "The Scream", "content": "A Force scream is agony made manifest. It shatters minds and breaks wills. Even masters fear its power.", "force_echo": False},
        "dark_sanctuary": {"title": "Dark Sanctuaries", "content": "Hidden sanctuaries dot the galaxy where Sith train away from prying eyes. Find one, and you find forbidden knowledge.", "force_echo": False},
        "sith_trials": {"title": "Sith Trials", "content": "Jedi trials test character. Sith trials test survival. Pass and grow stronger. Fail and become fertilizer.", "force_echo": False},
    },
}


# Artifacts with metadata used by game systems. stress_effect is positive (increases stress).
SITH_ARTIFACTS = {
    "holocron": {
        "name": "Sith Holocron",
        "effect": "Unlocks dark side knowledge (temporary insight)",
        "lore": "Contains the knowledge of ancient Sith Lords",
        "stress_effect": 15,
        "force_echo": True,
    },
    "sith_amulet": {
        "name": "Sith Amulet",
        "effect": "Boosts dark side powers but increases corruption",
        "lore": "Infused with the dark side energy of an ancient Lord",
        "stress_effect": 25,
        "force_echo": True,
    },
}


def populate_canon(codex: SithCodex):
    """Helper to add the small canonical SITH_LORE -> codex."""
    for cat, entries in SITH_LORE.items():
        for eid, data in entries.items():
            codex.add_entry(cat, eid, data["title"], data["content"], data.get("force_echo", False))


def populate_artifacts(codex: SithCodex):
    """Add artifact entries under 'sith_artifacts' category for discovery/tracking."""
    for aid, meta in SITH_ARTIFACTS.items():
        content = f"{meta['lore']}\nEffect: {meta['effect']}\nStress: {meta['stress_effect']}"
        codex.add_entry("sith_artifacts", aid, meta["name"], content, meta.get("force_echo", False))


def get_random_loading_message():
    """Return a random Sith lore snippet suitable for loading screens."""
    import random
    
    # Combine all lore entries from multiple categories for variety
    all_entries = []
    
    # Add loading wisdom (short, atmospheric)
    for entry_id, data in SITH_LORE.get("loading_wisdom", {}).items():
        all_entries.append(f"⟐ {data['content']}")
    
    # Add some dark side perspectives (philosophical)
    for entry_id, data in SITH_LORE.get("dark_side_perspective", {}).items():
        if len(data['content']) < 200:  # Only short ones for loading
            all_entries.append(f"⟐ {data['content']}")
    
    # Add some force philosophy
    for entry_id, data in SITH_LORE.get("force_philosophy", {}).items():
        if len(data['content']) < 200:
            all_entries.append(f"⟐ {data['content']}")
    
    # Add some historical snippets
    for entry_id, data in SITH_LORE.get("sith_history", {}).items():
        if len(data['content']) < 200:
            all_entries.append(f"⟐ {data['content']}")
    
    if not all_entries:
        return "⟐ The Force is strong in this place..."
    
    return random.choice(all_entries)
