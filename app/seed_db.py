# seed_db.py

from models import SessionLocal, User, Character, Race, Char_Class, Subclass, Ability
import game_rules

# ===============================================================
# SOURCE OF TRUTH: RACES (from main.py)
# ===============================================================
RACE_DATA = {
    "Manushya": {"description": "Adaptable humans, known for balanced potential.", "modifiers": {"bala": 1, "dakshata": 1, "dhriti": 1, "buddhi": 1, "prajna": 1, "samkalpa": 1}},
    "Vaanara": {"description": "Swift and agile forest-dwellers deeply connected to the spirits of nature. Often mistaken for monkey-folk due to the ceremonial masks and ornamented tails they wear in honor of their primal patrons.","modifiers": {"dakshata": 2, "prajna": 1}},
    "Yaksha": {"description": "Sturdy and resilient nature spirits, guardians of the earth's hidden treasures.", "modifiers": {"dhriti": 2, "bala": 1}},
    "Gandharva": {"description": "Ethereal and charismatic celestial musicians, masters of inspiration and illusion.", "modifiers": {"samkalpa": 2, "buddhi": 1}},
    "Apsara": {"description": "Celestial dancers of breathtaking grace and charm.", "modifiers": {"samkalpa": 2, "dakshata": 1}},
    "Kinnara": {"description": "Celestial musicians, lovers, and storytellers of paradise.", "modifiers": {"samkalpa": 2, "prajna": 1}},
    "Vidyadhara": {"description": "Ethereal bearers of knowledge and magical lore.", "modifiers": {"buddhi": 2, "prajna": 1}},
    "Naga": {"description": "Serpentine beings with natural grace and a connection to mystical arts.", "modifiers": {"dakshata": 2, "buddhi": 1}},
    "Asura": {"description": "Powerful and proud beings driven by passion, granting them immense physical might.", "modifiers": {"bala": 2, "dhriti": 1}}
}

# ===============================================================
# SOURCE OF TRUTH: CLASSES (from game_rules.py)
# Includes new 'default_abilities' key
# ===============================================================
CLASS_DATA = {
    "Yodha": {**game_rules.CLASSES["Yodha"], "default_abilities": ["Gada Strike"]},
    "Rishi": {**game_rules.CLASSES["Rishi"], "default_abilities": ["Agni Mantra"]},
    "Dhanurdhara": {**game_rules.CLASSES["Dhanurdhara"], "default_abilities": ["Longbow Shot"]},
    "Chara": {**game_rules.CLASSES["Chara"], "default_abilities": ["Dagger Strike"]},
    "Sutradhara": {**game_rules.CLASSES["Sutradhara"], "default_abilities": ["Dagger Strike"]}
}

# ===============================================================
# SOURCE OF TRUTH: SUBCLASSES (from Player's Handbook)
# ===============================================================
# ===============================================================
# SOURCE OF TRUTH: SUBCLASSES (from Player's Handbook, Final Section)
# ===============================================================
SUBCLASS_DATA = {
    # --- Yodha Subclasses ---
    "Raja-Yoddha": {"base_class": "Yodha", "description": "Inspiring leader, defends allies, controls battlefield.", "level_requirement": 3},
    "Gada-Yoddha": {"base_class": "Yodha", "description": "Unstoppable force, specializes in shattering blows.", "level_requirement": 3},
    "Astra-Yoddha": {"base_class": "Yodha", "description": "Versatile warrior, summons divine Astras.", "level_requirement": 3},

    # --- Rishi Subclasses ---
    "Tattvarshi": {"base_class": "Rishi", "description": "Powerful 'mage,' manipulates reality.", "level_requirement": 3},
    "Marga-Darshaka": {"base_class": "Rishi", "description": "Preceptor and strategist, buffs allies, debuffs enemies, reveals truths.", "level_requirement": 3},
    "Pranacharya": {"base_class": "Rishi", "description": "Ultimate healer, manipulates life flow.", "level_requirement": 3},

    # --- Dhanurdhara Subclasses ---
    "Deva-Dhanurdhara": {"base_class": "Dhanurdhara", "description": "Pinnacle of archery, channels divine Astras.", "level_requirement": 3},
    "Vana-Dhanurdhara": {"base_class": "Dhanurdhara", "description": "Stealthy hunter, uses environment for advantage.", "level_requirement": 3},
    "Sarathi-Dhanurdhara": {"base_class": "Dhanurdhara", "description": "Mobile weapons platform, specializes in mounted combat.", "level_requirement": 3},

    # --- Chara Subclasses ---
    "Mayavi": {"base_class": "Chara", "description": "Master of deception and psychological warfare, uses Buddhi-based Māyā.", "level_requirement": 3},
    "Marut-Gami": {"base_class": "Chara", "description": "Hyper-mobile skirmisher, focuses on speed and hit-and-run.", "level_requirement": 3},
    "Kamarupi": {"base_class": "Chara", "description": "Primal warrior, channels chaotic energy to alter form.", "level_requirement": 3},

    # --- Sutradhara Subclasses ---
    "Charana": {"base_class": "Sutradhara", "description": "Master of social graces, diplomacy, and enchantment.", "level_requirement": 3},
    "Kathakara": {"base_class": "Sutradhara", "description": "The Lore-Keeper.", "level_requirement": 3},
    "Bhata": {"base_class": "Sutradhara", "description": "The Herald at Arms.", "level_requirement": 3}
}


def seed_database():
    db = SessionLocal()
    print("Starting database seeding...")
    try:
        # 1. SEED RACES (No changes here)
        if db.query(Race).count() == 0:
            print("Seeding races...")
            for name, data in RACE_DATA.items():
                db.add(Race(name=name, description=data["description"], bala_mod=data["modifiers"].get("bala", 0), dakshata_mod=data["modifiers"].get("dakshata", 0), dhriti_mod=data["modifiers"].get("dhriti", 0), buddhi_mod=data["modifiers"].get("buddhi", 0), prajna_mod=data["modifiers"].get("prajna", 0), samkalpa_mod=data["modifiers"].get("samkalpa", 0)))
            db.commit()
            print("Races seeded.")

        # 2. SEED CHARACTER CLASSES (Updated)
        if db.query(Char_Class).count() == 0:
            print("Seeding character classes...")
            for name, data in CLASS_DATA.items():
                db.add(Char_Class(
                    name=name,
                    description=data["description"],
                    primary_attribute=data["primary_attribute"],
                    base_bala=data["base_attributes"].get("bala", 10),
                    base_dakshata=data["base_attributes"].get("dakshata", 10),
                    base_dhriti=data["base_attributes"].get("dhriti", 10),
                    base_buddhi=data["base_attributes"].get("buddhi", 10),
                    base_prajna=data["base_attributes"].get("prajna", 10),
                    base_samkalpa=data["base_attributes"].get("samkalpa", 10),
                    default_abilities=data.get("default_abilities", []) # Add the new field
                ))
            db.commit()
            print("Character classes seeded.")

        # 3. SEED SUBCLASSES (New)
        if db.query(Subclass).count() == 0:
            print("Seeding subclasses...")
            for name, data in SUBCLASS_DATA.items():
                base_class = db.query(Char_Class).filter(Char_Class.name == data["base_class"]).first()
                if base_class:
                    db.add(Subclass(
                        name=name,
                        description=data["description"],
                        base_class_id=base_class.id
                        # Add level_requirement, tapas_bonus, etc. here as you define them
                    ))
            db.commit()
            print("Subclasses seeded.")

        # 4. UPDATE EXISTING CHARACTERS (No changes here)
        default_race = db.query(Race).filter(Race.name == "Manushya").first()
        default_class = db.query(Char_Class).filter(Char_Class.name == "Yodha").first()
        if default_race and default_class:
            chars_to_update = db.query(Character).filter((Character.race_id == None) | (Character.char_class_id == None)).all()
            if chars_to_update:
                print(f"Updating {len(chars_to_update)} characters with defaults...")
                for char in chars_to_update:
                    char.race_id = default_race.id
                    char.char_class_id = default_class.id
                db.commit()
                print("Characters updated.")

    finally:
        db.close()
        print("Database seeding finished.")

if __name__ == "__main__":
    seed_database()