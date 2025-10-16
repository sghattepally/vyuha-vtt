# seed_db.py (Complete Replacement)

import requests
import json
import sys

# Direct DB Imports for the rule seeding part
from app.models import SessionLocal, Ability, Base, engine

# The base URL of our running FastAPI server
BASE_URL = "http://localhost:8000"

def seed_rules_directly():
    """Uses a direct DB connection to seed foundational data like abilities."""
    db = SessionLocal()
    print("--- Phase 1: Seeding Rules Directly to DB ---")
    try:
        if db.query(Ability).first():
            print("Abilities already exist. Skipping rule seeding.")
            return

        print("Creating core abilities...")
        abilities_to_create = [
            Ability(
                name="Gada Strike", description="A powerful melee attack.", action_type="MELEE_ATTACK",
                range=1, to_hit_attribute="bala", effect_type="DAMAGE",
                damage_dice="1d8", damage_attribute="bala"
            ),
            Ability(
                name="Longbow Shot", description="A precise ranged shot.", action_type="RANGED_ATTACK",
                range=20, to_hit_attribute="dakshata", effect_type="DAMAGE",
                damage_dice="1d8", damage_attribute="none"
            ),
            Ability(
                name="Dagger Strike", description="A quick, agile melee attack.", action_type="MELEE_ATTACK",
                range=1, to_hit_attribute="dakshata", effect_type="DAMAGE",
                damage_dice="1d4", damage_attribute="dakshata"
            )
        ]
        db.add_all(abilities_to_create)
        db.commit()
        print(f"Successfully created {len(abilities_to_create)} abilities.")
    finally:
        db.close()
    print("-" * 20)


def seed_test_scenario_via_api():
    """Uses the API to seed a specific test scenario."""
    print("--- Phase 2: Seeding Test Scenario via API ---")

    def print_response(response):
        print(f"Status Code: {response.status_code}")
        try:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print("Response Text:")
            print(response.text)
        print("-" * 20)

    try:
        # --- 1. Create or Fetch Users ---
        print("1. Creating/Fetching Users...")
        gm_user, player1_user = None, None
        
        # Try to create users. If it fails (e.g., they already exist), fetch all users.
        create_gm_res = requests.post(f"{BASE_URL}/users/", json={"username": "GM"})
        create_p1_res = requests.post(f"{BASE_URL}/users/", json={"username": "Player1"})

        if create_gm_res.status_code < 400 and create_p1_res.status_code < 400:
             gm_user = create_gm_res.json()
             player1_user = create_p1_res.json()
        else:
            print("Users may already exist. Fetching all users instead.")
            all_users_res = requests.get(f"{BASE_URL}/users/")
            # This check prevents the TypeError
            if all_users_res.status_code == 200:
                all_users = all_users_res.json()
                gm_user = next((u for u in all_users if u['username'] == 'GM'), None)
                player1_user = next((u for u in all_users if u['username'] == 'Player1'), None)
            else:
                print(f"Error: Failed to fetch users. Status: {all_users_res.status_code}")
                sys.exit(1) # Exit the script if we can't get users

        if not gm_user or not player1_user:
            print("Error: Could not find or create GM and Player1 users. Aborting.")
            sys.exit(1)

        gm_id = gm_user['id']
        player1_id = player1_user['id']
        print(f"Using GM (ID: {gm_id}) and Player1 (ID: {player1_id})")
        print("-" * 20)

        # --- 2. Fetch Abilities ---
        print("2. Fetching Abilities...")
        abilities_res = requests.get(f"{BASE_URL}/abilities/")
        if abilities_res.status_code != 200:
            print(f"Error: Failed to fetch abilities. Status: {abilities_res.status_code}")
            sys.exit(1)
        
        all_abilities = abilities_res.json()
        gada_strike = next(a for a in all_abilities if a['name'] == 'Gada Strike')
        longbow_shot = next(a for a in all_abilities if a['name'] == 'Longbow Shot')
        dagger_strike = next(a for a in all_abilities if a['name'] == 'Dagger Strike')
        print("Fetched core abilities via API.")
        print("-" * 20)

        # --- 3. Create Characters ---
        print("3. Creating Characters...")
        arjuna = requests.post(f"{BASE_URL}/characters/", json={"name": "Arjuna", "race": "Human", "character_class": "Dhanurdhara", "owner_id": player1_id}).json()
        bhima = requests.post(f"{BASE_URL}/characters/", json={"name": "Bhima", "race": "Human", "character_class": "Yodha", "owner_id": player1_id}).json()
        gaya = requests.post(f"{BASE_URL}/characters/", json={"name": "Gaya", "race": "Gandharva", "character_class": "Chara", "owner_id": player1_id}).json()
        print("Created Arjuna, Bhima, and Gaya.")
        print("-" * 20)

        # --- 4. Teach Abilities ---
        print("4. Teaching Abilities...")
        requests.post(f"{BASE_URL}/characters/{arjuna['id']}/learn_ability/", json={"ability_id": longbow_shot['id']})
        requests.post(f"{BASE_URL}/characters/{bhima['id']}/learn_ability/", json={"ability_id": gada_strike['id']})
        requests.post(f"{BASE_URL}/characters/{gaya['id']}/learn_ability/", json={"ability_id": dagger_strike['id']})
        print("Taught abilities to all characters.")
        print("-" * 20)
        
        # --- 5. Create Game Session ---
        print("5. Creating Game Session...")
        session_payload = {"campaign_name": "The Asura's Lair", "gm_id": gm_id, "character_ids": [arjuna['id'], bhima['id'], gaya['id']]}
        session_response = requests.post(f"{BASE_URL}/sessions/", json=session_payload)
        print("Created 'The Asura's Lair' session.")
        print_response(session_response)

    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to the FastAPI server at " + BASE_URL)
        print("Please make sure the server is running before executing this script.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("--- STARTING DATABASE SEED SCRIPT ---")
    print("Verifying database tables exist...")
    Base.metadata.create_all(bind=engine)
    
    seed_rules_directly()
    seed_test_scenario_via_api()

    print("\n--- DATABASE SEEDING COMPLETE! ---")
    print("You can now refresh your UI at http://localhost:5173")