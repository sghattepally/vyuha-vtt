# loka_system_final.py
"""
VYUHA LOKA SYSTEM - FINAL SPECIFICATION
========================================

Philosophical Foundation:
-------------------------
Lokas are dimensional overlays at every physical coordinate.
- Urdhva Lokas: Realm of spirit (Atman), accessed through mental discipline
- Bhuloka: Balanced middle realm where humans naturally exist
- Paatala Lokas: Realm of matter (Deha), accessed through physical mastery

The three-fold alignment:
- Deha (Body) â†’ Tapas â†’ Paatala
- Atman (Spirit) â†’ Maya â†’ Urdhva
- Bhuloka â†’ Balance (both Deha & Atman)

Game Mechanics Overview:
------------------------
1. RACIAL ATTUNEMENT: Fixed by race, determines which Loka you can summon
2. ENVIRONMENTAL RESONANCE: GM-set, represents location's natural energy
3. LOKA Ä€VÄ€HANA: Player ability to possess battlefield with their Loka
4. LEVEL 6 CHOICES: Character progression options

Design Goals:
-------------
- Create meaningful race-class tensions (Gandharva Yodha, Asura Rishi)
- Reward strategic thinking over level grinding
- Enable tactical sacrifices (summoning your Loka may hurt your own abilities)
- Provide character progression choices that matter
"""

# ================================================================
# RACIAL ATTUNEMENT (Fixed at Character Creation)
# ================================================================

RACIAL_ATTUNEMENT = {
    # Urdhva-Attuned Races (Spirit-focused, celestial beings)
    "Gandharva": "Urdhva",
    "Apsara": "Urdhva",
    "Kinnara": "Urdhva",
    "Vidyadhara": "Urdhva",
    
    # Bhu-Attuned Races (Balanced, no natural affinity)
    "Manushya": "Bhu",
    "Vaanara": "Bhu",
    "Yaksha": "Bhu",
    
    # Paatala-Attuned Races (Body-focused, material beings)
    "Asura": "Paatala",
    "Naga": "Paatala",
}

# ================================================================
# LOKA RESONANCE EFFECTS
# ================================================================

"""
CRITICAL DESIGN PRINCIPLE:
Resonance affects ABILITIES and SKILLS, NOT races.

When Urdhva Resonance is active:
- Maya abilities (resource) â†’ Bonuses
- Tapas abilities (resource) â†’ Penalties
- Atman attribute checks (Buddhi/Prajna/Samkalpa) â†’ Bonuses
- Deha attribute checks (Bala/Dakshata/Dhriti) â†’ Penalties

Race only determines WHO CAN SUMMON, not who benefits/suffers.
"""

RESONANCE_EFFECTS = {
    "Urdhva": {
        "display_name": "Urdhva Resonance",
        "description": "The realm of spirit manifests here. Mental powers flourish while physical strength wanes.",
        "lore": "Celestial energy permeates this space. The air shimmers with ethereal light, and thoughts feel sharper while the body grows distant.",
        
        # Visual/Audio Cues for GM
        "environmental_cues": [
            "Air shimmers with iridescent light",
            "Distant celestial music (gandharva songs)",
            "Gravity feels slightly lighter",
            "Colors appear more vivid and dreamlike",
            "Mental clarity increases, physical sensations dull"
        ],
        
        # Mechanical Effects
        "maya_abilities": {
            "cost_modifier": -1,  # Maya abilities cost 1 less (minimum 0)
            "roll_modifier": 2,   # +2 to Maya ability attack rolls and DCs
        },
        "tapas_abilities": {
            "cost_modifier": 1,   # Tapas abilities cost 1 more
            "roll_modifier": -2,  # -2 to Tapas ability attack rolls and DCs
        },
        "atman_checks": {
            "modifier": 2,  # +2 to Buddhi, Prajna, Samkalpa checks
        },
        "deha_checks": {
            "modifier": -2,  # -2 to Bala, Dakshata, Dhriti checks
        },
    },
    
    "Paatala": {
        "display_name": "Paatala Resonance",
        "description": "The realm of matter manifests here. Physical might surges while mental faculties fade.",
        "lore": "Raw material power thrums through this space. Density is palpable, muscles feel empowered, but thoughts become sluggish.",
        
        # Visual/Audio Cues for GM
        "environmental_cues": [
            "Air feels thick and heavy",
            "Low, rumbling vibrations underfoot",
            "Gravity feels stronger, more grounded",
            "Colors appear muted and earthy",
            "Physical sensations intensify, mental clarity dulls"
        ],
        
        # Mechanical Effects (Inverse of Urdhva)
        "tapas_abilities": {
            "cost_modifier": -1,  # Tapas abilities cost 1 less (minimum 0)
            "roll_modifier": 2,   # +2 to Tapas ability attack rolls and DCs
        },
        "maya_abilities": {
            "cost_modifier": 1,   # Maya abilities cost 1 more
            "roll_modifier": -2,  # -2 to Maya ability attack rolls and DCs
        },
        "deha_checks": {
            "modifier": 2,  # +2 to Bala, Dakshata, Dhriti checks
        },
        "atman_checks": {
            "modifier": -2,  # -2 to Buddhi, Prajna, Samkalpa checks
        },
    },
    
    "none": {
        "display_name": "No Resonance",
        "description": "This location exists in the balanced middle realm. No dimensional energies are active.",
        "lore": "The natural state of Bhuloka. Body and spirit are in equilibrium.",
        "environmental_cues": ["Normal battlefield conditions"],
        # No mechanical effects
    }
}

# ================================================================
# ENHANCED RESONANCE (Level 6: Loka Mastery)
# ================================================================

ENHANCED_RESONANCE_EFFECTS = {
    "Urdhva": {
        "display_name": "Enhanced Urdhva Resonance",
        "description": "Mastery of Urdhva energy creates overwhelming spiritual power.",
        
        # Enhanced Mechanical Effects
        "maya_abilities": {
            "cost_modifier": -2,  # Maya abilities cost 2 less (minimum 0)
            "roll_modifier": 3,   # +3 to Maya ability attack rolls and DCs
        },
        "tapas_abilities": {
            "cost_modifier": 2,   # Tapas abilities cost 2 more
            "roll_modifier": -3,  # -3 to Tapas ability attack rolls and DCs
        },
        "atman_checks": {
            "modifier": 3,  # +3 to Buddhi, Prajna, Samkalpa checks
        },
        "deha_checks": {
            "modifier": -3,  # -3 to Bala, Dakshata, Dhriti checks
        },
        
        # Duration and Range Enhancements
        "duration_turns": 7,  # Instead of 5
        "range_squares": 20,  # Instead of 15
    },
    
    "Paatala": {
        "display_name": "Enhanced Paatala Resonance",
        "description": "Mastery of Paatala energy creates overwhelming physical dominance.",
        
        # Enhanced Mechanical Effects (Inverse)
        "tapas_abilities": {
            "cost_modifier": -2,
            "roll_modifier": 3,
        },
        "maya_abilities": {
            "cost_modifier": 2,
            "roll_modifier": -3,
        },
        "deha_checks": {
            "modifier": 3,
        },
        "atman_checks": {
            "modifier": -3,
        },
        
        # Duration and Range Enhancements
        "duration_turns": 7,
        "range_squares": 20,
    }
}

# ================================================================
# LOKA Ä€VÄ€HANA (Loka Possession Ability)
# ================================================================

"""
LOKA Ä€VÄ€HANA - Core Mechanic

Unlocked at:
- Level 1 for Urdhva/Paatala races (based on racial attunement)
- Level 6 for Bhu races (after choosing attunement)

Effect: Possesses the battlefield with your Loka's dimensional energy.
"""

LOKA_AVAHANA_BASE = {
    "name": "Loka Ä€vÄhana",
    "display_name": "Loka Possession",
    "description": "Channel your dimensional origin to possess this space with your Loka's energy.",
    
    # Mechanics
    "action_type": "action",  # Costs your Action for the turn
    "resource_cost": 0,  # Free (no Tapas or Maya cost)
    "frequency": "once_per_combat",  # Can use once per combat OR once per rest
    "range_self": True,  # Centered on caster
    "aoe_radius": 15,  # 15 square radius
    "duration_turns": 5,  # Lasts 5 turns
    
    # Stacking Rules
    "overwrites_environmental": True,  # Completely replaces GM's environmental resonance
    "blocks_other_summonings": True,  # No other Loka Ä€vÄhana can be cast in this area while active
    
    # Flavor
    "activation_flavor": {
        "Urdhva": "You close your eyes and chant. Celestial light erupts from your body, transforming the battlefield into a fragment of the divine realms.",
        "Paatala": "You strike the ground with tremendous force. The earth groans and reality shifts, pulling material power from the depths into this space."
    }
}

# ================================================================
# LEVEL 6 PROGRESSION CHOICES
# ================================================================

"""
LEVEL 6 MILESTONE

Bhu Races (Manushya/Vaanara/Yaksha):
- Choose permanent attunement: Urdhva OR Paatala
- Unlock Loka Ä€vÄhana ability

Urdhva/Paatala Races:
- Choose ONE upgrade:
  A) Loka Resistance (personal nullification)
  B) Loka Mastery (enhanced summoning)
"""

LEVEL_6_BHU_ATTUNEMENT = {
    "name": "Loka Attunement Choice",
    "description": "After years of spiritual or physical discipline, you align yourself with one dimensional path.",
    "unlock_requirement": "Reach Level 6 as a Bhu-attuned race",
    
    "choices": ["Urdhva", "Paatala"],
    "permanent": True,  # Cannot be changed once chosen
    
    "urdhva_choice": {
        "display_name": "Attune to Urdhva",
        "description": "You have walked the path of spirit, transcending physical limitations through meditation and mental discipline.",
        "effect": "Unlock Loka Ä€vÄhana (Urdhva). You can now summon Urdhva Resonance.",
        "rp_guidance": "This choice reflects a character who has pursued knowledge, wisdom, and spiritual growth."
    },
    
    "paatala_choice": {
        "display_name": "Attune to Paatala",
        "description": "You have mastered your physical form, pushing your body to extremes and gaining control over matter itself.",
        "effect": "Unlock Loka Ä€vÄhana (Paatala). You can now summon Paatala Resonance.",
        "rp_guidance": "This choice reflects a character who has pursued physical excellence, martial mastery, and material power."
    }
}

LEVEL_6_URDHVA_PAATALA_UPGRADE = {
    "name": "Loka Mastery Choice",
    "description": "Your connection to your native Loka deepens. Choose how to evolve your power.",
    "unlock_requirement": "Reach Level 6 as an Urdhva or Paatala-attuned race",
    
    "choices": ["Loka Resistance", "Loka Mastery"],
    
    "loka_resistance": {
        "display_name": "Loka Resistance",
        "description": "You have learned to exist outside your Loka's influence, maintaining balance even when channeling its power.",
        "effect": "You personally ignore ALL resonance and summoning effects (yours or others'). You still CREATE resonances with Loka Ä€vÄhana, but are unaffected by them.",
        "rp_guidance": "This represents a character who has transcended their origin, achieving balance despite their nature.",
        "tactical_use": "Ideal for characters whose CLASS conflicts with their RACE (Gandharva Yodha, Asura Rishi). Allows you to support team without hindering yourself."
    },
    
    "loka_mastery": {
        "display_name": "Loka Mastery",
        "description": "You have fully embraced your dimensional origin, channeling its power with overwhelming force.",
        "effect": "Your Loka Ä€vÄhana is enhanced: +1 to all bonuses/penalties, +2 turns duration, +5 squares radius.",
        "rp_guidance": "This represents a character who has doubled down on their nature, becoming a conduit of pure Loka energy.",
        "tactical_use": "Ideal for characters whose CLASS synergizes with their RACE (Gandharva Rishi, Asura Yodha). Maximizes team impact."
    }
}

# ================================================================
# RESONANCE HIERARCHY & STACKING RULES
# ================================================================

"""
HIERARCHY (Bottom to Top):
1. BASE STATE (No Resonance) - Default battlefield
2. ENVIRONMENTAL RESONANCE - GM sets (Deva temple = Urdhva, Naga cave = Paatala)
3. LOKA Ä€VÄ€HANA - Player summons, COMPLETELY OVERWRITES environmental
4. PERSONAL EFFECTS - Level 6 Loka Resistance affects individual only

STACKING RULES:
- Only ONE Loka Ä€vÄhana can be active in an area at a time
- First summoning blocks all others until duration expires
- When summoning ends, reverts to environmental resonance (if any)
- Personal effects (Loka Resistance) don't create zones, just affect the individual

EXAMPLE SEQUENCE:
Turn 1: Battle in Deva Temple (Environmental Urdhva)
Turn 3: Asura uses Loka Ä€vÄhana (Paatala) â†’ Temple now Paatala inside bubble
Turn 5: Gandharva tries Loka Ä€vÄhana (Urdhva) â†’ BLOCKED, Asura's still active
Turn 8: Asura's summoning expires â†’ Reverts to Temple's Urdhva
Turn 9: Gandharva can now summon if desired
"""

RESONANCE_HIERARCHY = [
    {
        "level": 0,
        "name": "Base State",
        "source": "default",
        "description": "No dimensional energy present"
    },
    {
        "level": 1,
        "name": "Environmental Resonance",
        "source": "gm_set",
        "description": "Location's natural energy (temples, caves, sacred sites)",
        "can_be_overwritten_by": ["Loka Ä€vÄhana"]
    },
    {
        "level": 2,
        "name": "Loka Ä€vÄhana",
        "source": "player_ability",
        "description": "Active summoning completely replaces environment",
        "blocks": ["Other Loka Ä€vÄhana in same area"],
        "duration": "5 turns (7 with Loka Mastery)"
    },
    {
        "level": 3,
        "name": "Personal Effects",
        "source": "character_feature",
        "description": "Loka Resistance - affects only the individual character",
        "does_not_affect_zone": True
    }
]

# ================================================================
# HELPER FUNCTIONS FOR GAME LOGIC
# ================================================================

def get_character_attunement(race_name: str, level: int, chosen_attunement: str = None) -> str:
    """
    Returns a character's Loka attunement.
    
    Args:
        race_name: Character's race
        level: Character's current level
        chosen_attunement: For Bhu races at level 6+, their chosen attunement
    
    Returns:
        "Urdhva", "Paatala", "Bhu", or None
    """
    base_attunement = RACIAL_ATTUNEMENT.get(race_name, None)
    
    if base_attunement in ["Urdhva", "Paatala"]:
        return base_attunement
    
    if base_attunement == "Bhu":
        if level >= 6 and chosen_attunement in ["Urdhva", "Paatala"]:
            return chosen_attunement
        return "Bhu"
    
    return None

def can_use_loka_avahana(race_name: str, level: int, chosen_attunement: str = None) -> bool:
    """
    Determines if a character can use Loka Ä€vÄhana.
    
    Returns:
        True if character has unlocked the ability, False otherwise
    """
    attunement = get_character_attunement(race_name, level, chosen_attunement)
    
    if attunement in ["Urdhva", "Paatala"]:
        # Urdhva/Paatala races: unlocked at level 1
        # Bhu races with chosen attunement: unlocked at level 6
        if RACIAL_ATTUNEMENT.get(race_name) in ["Urdhva", "Paatala"]:
            return level >= 1
        elif RACIAL_ATTUNEMENT.get(race_name) == "Bhu":
            return level >= 6 and chosen_attunement is not None
    
    return False

def get_resonance_modifiers(
    resonance_type: str,
    is_enhanced: bool = False
) -> dict:
    """
    Returns the mechanical modifiers for a given resonance type.
    
    Args:
        resonance_type: "Urdhva", "Paatala", or "none"
        is_enhanced: True if summoner has Loka Mastery
    
    Returns:
        Dict of modifiers
    """
    if resonance_type == "none":
        return {}
    
    if is_enhanced:
        return ENHANCED_RESONANCE_EFFECTS.get(resonance_type, {})
    else:
        return RESONANCE_EFFECTS.get(resonance_type, {})

def apply_resonance_to_ability_cost(
    base_cost: int,
    ability_resource: str,  # "tapas" or "maya"
    active_resonance: str,  # "Urdhva", "Paatala", or "none"
    is_enhanced: bool = False,
    has_loka_resistance: bool = False
) -> int:
    """
    Calculates modified ability cost based on active resonance.
    
    Args:
        base_cost: Original resource cost of ability
        ability_resource: Which resource the ability uses
        active_resonance: Current battlefield resonance
        is_enhanced: Is this an enhanced resonance (Loka Mastery)?
        has_loka_resistance: Does the character have Loka Resistance?
    
    Returns:
        Modified cost (minimum 0)
    """
    if has_loka_resistance or active_resonance == "none":
        return base_cost
    
    modifiers = get_resonance_modifiers(active_resonance, is_enhanced)
    
    if ability_resource == "maya":
        cost_mod = modifiers.get("maya_abilities", {}).get("cost_modifier", 0)
    elif ability_resource == "tapas":
        cost_mod = modifiers.get("tapas_abilities", {}).get("cost_modifier", 0)
    else:
        return base_cost
    
    return max(0, base_cost + cost_mod)

def apply_resonance_to_ability_roll(
    base_roll: int,
    ability_resource: str,  # "tapas" or "maya"
    active_resonance: str,
    is_enhanced: bool = False,
    has_loka_resistance: bool = False
) -> int:
    """
    Calculates modified ability attack roll or DC based on resonance.
    
    Returns:
        Modified roll/DC
    """
    if has_loka_resistance or active_resonance == "none":
        return base_roll
    
    modifiers = get_resonance_modifiers(active_resonance, is_enhanced)
    
    if ability_resource == "maya":
        roll_mod = modifiers.get("maya_abilities", {}).get("roll_modifier", 0)
    elif ability_resource == "tapas":
        roll_mod = modifiers.get("tapas_abilities", {}).get("roll_modifier", 0)
    else:
        return base_roll
    
    return base_roll + roll_mod

def apply_resonance_to_skill_check(
    base_roll: int,
    primary_attribute: str,  # "bala", "buddhi", etc.
    active_resonance: str,
    is_enhanced: bool = False,
    has_loka_resistance: bool = False
) -> int:
    """
    Calculates modified skill check based on resonance.
    
    Args:
        base_roll: d20 + attribute modifiers
        primary_attribute: The main attribute for the check
        active_resonance: Current battlefield resonance
        is_enhanced: Is this an enhanced resonance?
        has_loka_resistance: Does character have Loka Resistance?
    
    Returns:
        Modified roll
    """
    if has_loka_resistance or active_resonance == "none":
        return base_roll
    
    modifiers = get_resonance_modifiers(active_resonance, is_enhanced)
    
    # Determine if this is a Deha or Atman attribute
    deha_attributes = ["bala", "dakshata", "dhriti"]
    atman_attributes = ["buddhi", "prajna", "samkalpa"]
    
    if primary_attribute in deha_attributes:
        check_mod = modifiers.get("deha_checks", {}).get("modifier", 0)
    elif primary_attribute in atman_attributes:
        check_mod = modifiers.get("atman_checks", {}).get("modifier", 0)
    else:
        return base_roll
    
    return base_roll + check_mod

# ================================================================
# INTEGRATION CHECKLIST FOR DEVELOPERS
# ================================================================

"""
TO IMPLEMENT THIS SYSTEM:

DATABASE CHANGES:
1. Character model already has: unlocked_loka_attunement (str)
   - Add: level_6_loka_choice (str) - "Resistance" or "Mastery"
   
2. GameSession model already has: active_loka_resonance (str)
   - Add: active_loka_summoning (dict) - {
       "type": "Urdhva/Paatala",
       "caster_id": int,
       "turns_remaining": int,
       "is_enhanced": bool,
       "center_x": int,
       "center_y": int,
       "radius": int
     }

ABILITY SYSTEM (app/ability_system.py):
1. Modify validate_ability_use() to check resonance-modified costs
2. Modify execute_ability() to apply resonance modifiers to rolls
3. Add handle_loka_avahana() for summoning ability

COMBAT SYSTEM (app/main.py):
1. Add turn_start trigger to decrement active_loka_summoning turns
2. When summoning expires, revert to environmental resonance
3. Prevent overlapping summonings (validation)

CHARACTER CREATION (app/main.py):
1. At Level 6, present choices:
   - Bhu races: Choose Urdhva or Paatala attunement
   - Urdhva/Paatala races: Choose Resistance or Mastery
   
UI COMPONENTS:
1. Display active resonance in combat UI (with visual indicators)
2. Show Loka Ä€vÄhana button when available
3. Character sheet: Display attunement and level 6 choice
4. GM panel: Set environmental resonance

TESTING SCENARIOS:
1. Gandharva Yodha in Urdhva temple (struggle test)
2. Asura Rishi uses Loka Ä€vÄhana (Paatala) to counter
3. Overlapping summoning blocked
4. Loka Resistance nullifies personal effects
5. Enhanced Loka Mastery shows increased numbers
"""