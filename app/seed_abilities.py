# app/seed_abilities.py
"""
Sample ability definitions showcasing the system's capabilities.
Run this to populate your database with example abilities.
"""

from models import SessionLocal, Ability, ActionType, ResourceType, TargetType

SAMPLE_ABILITIES = [
    # === YODHA (WARRIOR) ABILITIES ===
    {
        "name": "Gada Strike",
        "description": "A powerful overhead strike with your mace.",
        "action_type": ActionType.ACTION,
        "resource_cost": 0,
        "resource_type": None,
        "requirements": {"equipped_weapon_type": "weapon"},
        "target_type": TargetType.ENEMY,
        "effect_radius": 0,
        "range": 1,
        "to_hit_attribute": "bala",
        "effect_type": "damage",
        "damage_dice": "1d8",
        "damage_attribute": "bala",
        "status_effect": None
    },
    {
        "name": "Crushing Blow",
        "description": "Spend Tapas to deliver a devastating strike that can stagger your foe.",
        "action_type": ActionType.ACTION,
        "resource_cost": 1,
        "resource_type": ResourceType.TAPAS,
        "requirements": {"equipped_weapon_type": "weapon"},
        "target_type": TargetType.ENEMY,
        "effect_radius": 0,
        "range": 1,
        "to_hit_attribute": "bala",
        "effect_type": "damage",
        "damage_dice": "2d8",
        "damage_attribute": "bala",
        "status_effect": "staggered"
    },
    {
        "name": "Second Wind",
        "description": "Draw on your inner reserves to recover vitality.",
        "action_type": ActionType.BONUS_ACTION,
        "resource_cost": 1,
        "resource_type": ResourceType.TAPAS,
        "requirements": None,
        "target_type": TargetType.SELF,
        "effect_radius": 0,
        "range": 0,
        "to_hit_attribute": None,
        "effect_type": "heal",
        "damage_dice": "1d10",
        "damage_attribute": "dhriti",
        "status_effect": None
    },
    
    # === RISHI (SAGE) ABILITIES ===
    {
        "name": "Agni Mantra",
        "description": "Channel divine fire to burn your enemies.",
        "action_type": ActionType.ACTION,
        "resource_cost": 1,
        "resource_type": ResourceType.MAYA,
        "requirements": None,
        "target_type": TargetType.ENEMY,
        "effect_radius": 0,
        "range": 6,
        "to_hit_attribute": "buddhi",
        "effect_type": "damage",
        "damage_dice": "2d6",
        "damage_attribute": "buddhi",
        "status_effect": None
    },
    {
        "name": "Sanjeevani Blessing",
        "description": "A healing mantra that restores an ally's life force.",
        "action_type": ActionType.ACTION,
        "resource_cost": 1,
        "resource_type": ResourceType.MAYA,
        "requirements": None,
        "target_type": TargetType.ALLY,
        "effect_radius": 0,
        "range": 6,
        "to_hit_attribute": None,
        "effect_type": "heal",
        "damage_dice": "2d8",
        "damage_attribute": "prajna",
        "status_effect": None
    },
    {
        "name": "Sacred Ward",
        "description": "Emit a protective aura around yourself.",
        "action_type": ActionType.BONUS_ACTION,
        "resource_cost": 2,
        "resource_type": ResourceType.MAYA,
        "requirements": None,
        "target_type": TargetType.GROUND,
        "effect_radius": 2,
        "range": 0,
        "to_hit_attribute": None,
        "effect_type": "buff",
        "damage_dice": None,
        "damage_attribute": None,
        "status_effect": "blessed"
    },
    
    # === DHANURDHARA (ARCHER) ABILITIES ===
    {
        "name": "Longbow Shot",
        "description": "A precise arrow strike from range.",
        "action_type": ActionType.ACTION,
        "resource_cost": 0,
        "resource_type": None,
        "requirements": {"equipped_weapon_type": "weapon"},
        "target_type": TargetType.ENEMY,
        "effect_radius": 0,
        "range": 12,
        "to_hit_attribute": "dakshata",
        "effect_type": "damage",
        "damage_dice": "1d8",
        "damage_attribute": "dakshata",
        "status_effect": None
    },
    {
        "name": "Agneyastra",
        "description": "Fire an arrow imbued with divine flame that explodes on impact.",
        "action_type": ActionType.ACTION,
        "resource_cost": 1,
        "resource_type": ResourceType.MAYA,
        "requirements": {"equipped_weapon_type": "weapon"},
        "target_type": TargetType.ENEMY,
        "effect_radius": 1,  # Hits nearby enemies
        "range": 12,
        "to_hit_attribute": "dakshata",
        "effect_type": "damage",
        "damage_dice": "2d6",
        "damage_attribute": "buddhi",
        "status_effect": "burning"
    },
    {
        "name": "Evasive Maneuver",
        "description": "Spend movement to reposition quickly.",
        "action_type": ActionType.BONUS_ACTION,
        "resource_cost": 2,
        "resource_type": ResourceType.SPEED,
        "requirements": None,
        "target_type": TargetType.GROUND,
        "effect_radius": 0,
        "range": 3,
        "to_hit_attribute": None,
        "effect_type": "teleport",
        "damage_dice": None,
        "damage_attribute": None,
        "status_effect": None
    },
    
    # === CHARA (AGENT) ABILITIES ===
    {
        "name": "Dagger Strike",
        "description": "A quick strike with your dagger.",
        "action_type": ActionType.ACTION,
        "resource_cost": 0,
        "resource_type": None,
        "requirements": None,
        "target_type": TargetType.ENEMY,
        "effect_radius": 0,
        "range": 1,
        "to_hit_attribute": "dakshata",
        "effect_type": "damage",
        "damage_dice": "1d4",
        "damage_attribute": "dakshata",
        "status_effect": None
    },
    {
        "name": "Phantom Strike",
        "description": "Become invisible and strike from the shadows.",
        "action_type": ActionType.ACTION,
        "resource_cost": 1,
        "resource_type": ResourceType.TAPAS,
        "requirements": None,
        "target_type": TargetType.ENEMY,
        "effect_radius": 0,
        "range": 3,
        "to_hit_attribute": "dakshata",
        "effect_type": "damage",
        "damage_dice": "3d6",
        "damage_attribute": "dakshata",
        "status_effect": None
    },
    {
        "name": "Shadow Step",
        "description": "Teleport to a nearby location using Māyā.",
        "action_type": ActionType.BONUS_ACTION,
        "resource_cost": 1,
        "resource_type": ResourceType.MAYA,
        "requirements": None,
        "target_type": TargetType.GROUND,
        "effect_radius": 0,
        "range": 6,
        "to_hit_attribute": None,
        "effect_type": "teleport",
        "damage_dice": None,
        "damage_attribute": None,
        "status_effect": "invisible_until_next_turn"
    },

    # === MOVE ABILITIES ===

    {
        "name": "Move",
        "description": "Move to a nearby location",
        "action_type": ActionType.FREE,
        "resource_cost": 6,
        "resource_type": ResourceType.SPEED,
        "requirements": None,
        "target_type": TargetType.GROUND,
        "effect_radius": 0,
        "range": 6,
        "to_hit_attribute": None,
        "effect_type": None,
        "damage_dice": None,
        "damage_attribute": None,
        "status_effect": None
    },
]

def seed_abilities():
    """Populate the database with sample abilities"""
    db = SessionLocal()
    try:
        print("Seeding abilities...")
        for ability_data in SAMPLE_ABILITIES:
            existing = db.query(Ability).filter(
                Ability.name == ability_data["name"]
            ).first()
            
            if not existing:
                new_ability = Ability(**ability_data)
                db.add(new_ability)
                print(f"  Added: {ability_data['name']}")
            else:
                print(f"  Skipped (exists): {ability_data['name']}")
        
        db.commit()
        print(f"Successfully seeded {len(SAMPLE_ABILITIES)} abilities.")
    except Exception as e:
        print(f"Error seeding abilities: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_abilities()