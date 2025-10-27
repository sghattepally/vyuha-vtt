# seed_bridge_of_tears.py
"""
Seed data for Bridge of Tears campaign
Creates the 6 pre-generated player characters and Rakshasa enemy templates
"""

from models import SessionLocal, Character, User, Race, Char_Class
from models import CharacterAbility, CharacterInventory, Item, Ability
from sqlalchemy.orm import Session

# Get the GM user (ID 1 owns these templates)
GM_USER_ID = 1

# ==================================
# PRE-GENERATED PLAYER CHARACTERS
# ==================================

BRIDGE_OF_TEARS_CHARACTERS = [
    {
        "name": "Devrath the Dutiful",
        "race": "Manushya",
        "char_class": "Yodha",
        "level": 1,
        "subclass": None,
        "unlocked_loka_attunement": None,
        "abilities": ["Gada Strike", "Shield Bash"],
        "inventory": [
            ("Gada", 1, True),  # (item_name, quantity, is_equipped)
            ("Charma", 1, True),
            ("Sanjeevani Ras", 2, False),
            ("Rope", 1, False),
            ("Torch", 3, False)
        ]
    },
    {
        "name": "Madhavi the Burdened",
        "race": "Asura",
        "char_class": "Rishi",
        "level": 1,
        "subclass": None,
        "unlocked_loka_attunement": None,
        "abilities": ["Agni Mantra", "Prana Vahana", "Staff Strike"],
        "inventory": [
            ("Danda", 1, True),
            ("Vastra", 1, True),
            ("Sanjeevani Ras", 3, False),
            ("Herb Pouch", 1, False)
        ]
    },
    {
        "name": "Nalayira the Idealist",
        "race": "Gandharva",
        "char_class": "Yodha",
        "level": 1,
        "subclass": None,
        "unlocked_loka_attunement": None,
        "abilities": ["Khadga Strike", "Inspiring Presence"],
        "inventory": [
            ("Khadga", 1, True),
            ("Charma", 1, True),
            ("Sanjeevani Ras", 2, False),
            ("Silk Scarf", 1, False)
        ]
    },
    {
        "name": "Keshava the Calculator",
        "race": "Vidyadhara",
        "char_class": "Chara",
        "level": 1,
        "subclass": None,
        "unlocked_loka_attunement": None,
        "abilities": ["Dagger Strike", "Shadow Step"],
        "inventory": [
            ("Khanjar", 2, True),
            ("Vastra", 1, True),
            ("Sanjeevani Ras", 2, False),
            ("Lockpicks", 1, False),
            ("Rope", 1, False)
        ]
    },
    {
        "name": "Tara the Mystic",
        "race": "Naga",
        "char_class": "Rishi",
        "level": 1,
        "subclass": None,
        "unlocked_loka_attunement": None,
        "abilities": ["Agni Mantra", "Prana Vahana"],
        "inventory": [
            ("Danda", 1, True),
            ("Vastra", 1, True),
            ("Sanjeevani Ras", 3, False),
            ("Sacred Text", 1, False)
        ]
    },
    {
        "name": "Vikram the Reformed",
        "race": "Vaanara",
        "char_class": "Dhanurdhara",
        "level": 1,
        "subclass": None,
        "unlocked_loka_attunement": None,
        "abilities": ["Longbow Shot", "Precise Shot"],
        "inventory": [
            ("Dhanush", 1, True),
            ("Arrow", 20, False),
            ("Charma", 1, True),
            ("Sanjeevani Ras", 2, False),
            ("Rope", 1, False)
        ]
    }
]

# ==================================
# RAKSHASA ENEMY TEMPLATES
# ==================================

RAKSHASA_ENEMIES = [
    {
        "name": "Rakshasa Warrior",
        "race": "Asura",  # Using Asura as base for physical prowess
        "char_class": "Yodha",
        "level": 1,
        "subclass": None,
        "unlocked_loka_attunement": None,
        "abilities": ["Gada Strike"],  # We'll manually adjust stats for claw attacks
        "inventory": []
        # Prana: 25 (will be set by CharacterSchema calculation)
        # Attack: 1d20+3, Damage: 1d10+2 (GM manages this)
        # Move: 6 squares
    },
    {
        "name": "Rakshasa Shaman",
        "race": "Asura",
        "char_class": "Rishi",
        "level": 1,
        "subclass": None,
        "unlocked_loka_attunement": None,
        "abilities": ["Agni Mantra"],
        "inventory": []
        # Prana: 18
        # Attack: Flame Bolt (range 12), 1d20+4, Damage: 2d6+2
        # Special: Can cast "Fear Roar" (DC 13 Samkalpa save or flee)
    },
    {
        "name": "Rakshasa Chieftain",
        "race": "Asura",
        "char_class": "Yodha",
        "level": 2,  # Boss is slightly higher level
        "subclass": None,
        "unlocked_loka_attunement": None,
        "abilities": ["Gada Strike"],  # Represents basic attack, cleave is GM-managed
        "inventory": [("Paraśu", 1, True)]  # Greataxe
        # Prana: 40
        # Attack: 1d20+4, Damage: 2d8+3
        # Move: 7 squares
        # Special: Cleave (hits all adjacent enemies)
    }
]

# ==================================
# SEEDING FUNCTIONS
# ==================================

def seed_campaign_characters(db: Session):
    """Create the 6 pre-generated player characters for Bridge of Tears"""
    
    print("Seeding Bridge of Tears pre-generated characters...")
    
    # Get GM user
    gm_user = db.query(User).filter(User.id == GM_USER_ID).first()
    if not gm_user:
        print(f"ERROR: GM user with ID {GM_USER_ID} not found. Create a user first.")
        return
    
    for char_data in BRIDGE_OF_TEARS_CHARACTERS:
        # Check if character already exists
        existing = db.query(Character).filter(
            Character.name == char_data["name"],
            Character.owner_id == GM_USER_ID
        ).first()
        
        if existing:
            print(f"  Skipped (exists): {char_data['name']}")
            continue
        
        # Look up race and class IDs
        race = db.query(Race).filter(Race.name == char_data["race"]).first()
        char_class = db.query(Char_Class).filter(Char_Class.name == char_data["char_class"]).first()
        
        if not race:
            print(f"  ERROR: Race '{char_data['race']}' not found for {char_data['name']}")
            continue
        if not char_class:
            print(f"  ERROR: Class '{char_data['char_class']}' not found for {char_data['name']}")
            continue
        
        # Create character
        new_char = Character(
            name=char_data["name"],
            owner_id=GM_USER_ID,
            race_id=race.id,
            char_class_id=char_class.id,
            level=char_data["level"],
            subclass_id=None,  # Changed from subclass_name
            unlocked_loka_attunement=char_data["unlocked_loka_attunement"]
        )
        db.add(new_char)
        db.flush()  # Get the ID without committing
        
        # Add abilities
        for ability_name in char_data["abilities"]:
            ability = db.query(Ability).filter(Ability.name == ability_name).first()
            if ability:
                char_ability = CharacterAbility(
                    character_id=new_char.id,
                    ability_id=ability.id
                )
                db.add(char_ability)
        
        # Add inventory
        for item_name, quantity, is_equipped in char_data["inventory"]:
            item = db.query(Item).filter(Item.puranic_name == item_name).first()
            if item:
                inv_item = CharacterInventory(
                    character_id=new_char.id,
                    item_id=item.id,
                    quantity=quantity,
                    is_equipped=is_equipped
                )
                db.add(inv_item)
            else:
                print(f"  WARNING: Item '{item_name}' not found for {char_data['name']}")
        
        print(f"  Created: {char_data['name']}")
    
    db.commit()
    print("Pre-generated characters seeded successfully!")


def seed_rakshasa_enemies(db: Session):
    """Create Rakshasa enemy templates for Bridge of Tears"""
    
    print("Seeding Rakshasa enemy templates...")
    
    # Get GM user
    gm_user = db.query(User).filter(User.id == GM_USER_ID).first()
    if not gm_user:
        print(f"ERROR: GM user with ID {GM_USER_ID} not found. Create a user first.")
        return
    
    for enemy_data in RAKSHASA_ENEMIES:
        # Check if enemy already exists
        existing = db.query(Character).filter(
            Character.name == enemy_data["name"],
            Character.owner_id == GM_USER_ID
        ).first()
        
        if existing:
            print(f"  Skipped (exists): {enemy_data['name']}")
            continue
        
        # Look up race and class IDs
        race = db.query(Race).filter(Race.name == enemy_data["race"]).first()
        char_class = db.query(Char_Class).filter(Char_Class.name == enemy_data["char_class"]).first()
        
        if not race:
            print(f"  ERROR: Race '{enemy_data['race']}' not found for {enemy_data['name']}")
            continue
        if not char_class:
            print(f"  ERROR: Class '{enemy_data['char_class']}' not found for {enemy_data['name']}")
            continue
        
        # Create enemy template
        new_enemy = Character(
            name=enemy_data["name"],
            owner_id=GM_USER_ID,
            race_id=race.id,
            char_class_id=char_class.id,
            level=enemy_data["level"],
            subclass_id=None,  # Changed from subclass_name
            unlocked_loka_attunement=enemy_data["unlocked_loka_attunement"]
        )
        db.add(new_enemy)
        db.flush()
        
        # Add abilities
        for ability_name in enemy_data["abilities"]:
            ability = db.query(Ability).filter(Ability.name == ability_name).first()
            if ability:
                enemy_ability = CharacterAbility(
                    character_id=new_enemy.id,
                    ability_id=ability.id
                )
                db.add(enemy_ability)
        
        # Add inventory
        for item_name, quantity, is_equipped in enemy_data["inventory"]:
            item = db.query(Item).filter(Item.puranic_name == item_name).first()
            if item:
                inv_item = CharacterInventory(
                    character_id=new_enemy.id,
                    item_id=item.id,
                    quantity=quantity,
                    is_equipped=is_equipped
                )
                db.add(inv_item)
        
        print(f"  Created: {enemy_data['name']}")
    
    db.commit()
    print("Rakshasa enemies seeded successfully!")


def print_campaign_setup_instructions():
    """Print instructions for GM to set up the Bridge of Tears campaign"""
    
    print("\n" + "="*60)
    print("BRIDGE OF TEARS CAMPAIGN SETUP")
    print("="*60)
    print("\nPre-generated characters and enemies are now in your database!")
    print("\nTO RUN THE CAMPAIGN:")
    print("\n1. Create a new session as GM")
    print("2. Add 4 of the 6 pre-gen characters to your session")
    print("3. When combat starts, add Rakshasa enemies:")
    print("   - 4x Rakshasa Warrior")
    print("   - 1x Rakshasa Shaman")
    print("   - 1x Rakshasa Chieftain")
    print("\n4. Create the Bridge environmental object:")
    print("   - Name: 'The Narmada Crossing'")
    print("   - Type: bridge")
    print("   - Size: 3 squares wide, 15 squares long")
    print("   - Starting Integrity: 30")
    print("   - Has sections: True")
    print("   - Total sections: 3")
    print("\n5. NAMED NPCs (track manually or use notes):")
    print("   - Devi (young mother) + baby + Arun (6yo son)")
    print("   - Grandfather Rajan (elderly, broken leg)")
    print("   - Meera (teenage girl) + 3 younger siblings")
    print("   - Vikrant (merchant)")
    print("   - 20 refugee tokens total")
    print("\n6. Bridge Integrity Rules:")
    print("   - Each refugee crossing = -1 integrity")
    print("   - Combat damage to bridge = varies")
    print("   - Player sacrifice = +5 integrity")
    print("   - At 0 integrity, bridge collapses")
    print("\n7. Environmental Hazard:")
    print("   - Every 3 rounds, roll 1d20")
    print("   - On 10 or less, a bridge section cracks")
    print("\nRefer to Bridge_of_Tears_Campaign.md for full GM script!")
    print("="*60 + "\n")


# ==================================
# MAIN EXECUTION
# ==================================

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_campaign_characters(db)
        seed_rakshasa_enemies(db)
        print_campaign_setup_instructions()
    except Exception as e:
        print(f"ERROR during seeding: {e}")
        db.rollback()
    finally:
        db.close()