from models import SessionLocal, User, Character, Race, Char_Class, Subclass, Ability, Item
import game_rules
import enum
import csv
import enum
from sqlalchemy.orm import Session


class ItemType(str, enum.Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    POTION = "potion"
    GENERAL = "general"

def seed_items_from_csv(db: Session, csv_path='app/items.csv'):
    print(f"Attempting to seed items from {csv_path}...")
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            items_added = 0
            for row in reader:
                # Check if item already exists
                exists = db.query(Item).filter(Item.puranic_name == row['puranic_name']).first()
                if not exists:
                    # Convert string 'true'/'false' to boolean
                    is_stackable = row.get('is_stackable', 'false').lower() == 'true'
                    
                    # Handle potentially empty on_use_ability_id
                    on_use_id = row.get('on_use_ability_id')
                    on_use_ability_id = int(on_use_id) if on_use_id else None

                    new_item = Item(
                        puranic_name=row.get('puranic_name'),
                        english_name=row.get('english_name'),
                        description=row.get('description'),
                        item_type=ItemType(row.get('item_type')),
                        is_stackable=row.get(is_stackable),
                        on_use_ability_id=on_use_ability_id
                    )
                    db.add(new_item)
                    items_added += 1
            
            db.commit()
            print(f"Successfully added {items_added} new items.")

    except FileNotFoundError:
        print(f"Error: Could not find the CSV file at {csv_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()

# --- Find the main execution block at the bottom of the file ---
if __name__ == "__main__":
    db = SessionLocal()
    try:
        # Replace the old seed_items call with the new one
        seed_items_from_csv(db)
        # ... (keep your other existing seed calls)
    finally:
        db.close()