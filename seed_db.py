# seed_db.py
import requests
import json

# The base URL of our running FastAPI server
BASE_URL = "http://localhost:8000"

def print_response(response):
    """Helper function to print API responses prettily."""
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print("Response Text:")
        print(response.text)
    print("-" * 20)

def main():
    """Runs the full seeding process."""
    print("--- STARTING DATABASE SEED SCRIPT ---")

    # === Phase 1: Create Users ===
    print("1. Creating Users...")
    gm_user = requests.post(f"{BASE_URL}/users/", json={"username": "GM"}).json()
    player1_user = requests.post(f"{BASE_URL}/users/", json={"username": "Player1"}).json()
    gm_id = gm_user['id']
    player1_id = player1_user['id']
    print(f"Created GM (ID: {gm_id}) and Player1 (ID: {player1_id})")
    print("-" * 20)

    # === Phase 2: Create Abilities (The Rulebook) ===
    print("2. Creating Abilities...")
    gada_strike = requests.post(f"{BASE_URL}/abilities/", json={
        "name": "Gada Strike", "description": "A powerful melee attack.", "action_type": "MELEE_ATTACK",
        "range": 1, "to_hit_attribute": "bala", "effect_type": "DAMAGE",
        "damage_dice": "1d8", "damage_attribute": "bala"
    }).json()

    longbow_shot = requests.post(f"{BASE_URL}/abilities/", json={
        "name": "Longbow Shot", "description": "A precise ranged shot.", "action_type": "RANGED_ATTACK",
        "range": 20, "to_hit_attribute": "dakshata", "effect_type": "DAMAGE",
        "damage_dice": "1d8", "damage_attribute": "none"
    }).json()

    dagger_strike = requests.post(f"{BASE_URL}/abilities/", json={
        "name": "Dagger Strike", "description": "A quick, agile melee attack.", "action_type": "MELEE_ATTACK",
        "range": 1, "to_hit_attribute": "dakshata", "effect_type": "DAMAGE",
        "damage_dice": "1d4", "damage_attribute": "dakshata"
    }).json()
    print("Created Gada Strike, Longbow Shot, and Dagger Strike.")
    print("-" * 20)

    # === Phase 3: Create Characters ===
    print("3. Creating Characters...")
    arjuna = requests.post(f"{BASE_URL}/characters/", json={
        "name": "Arjuna", "race": "Human", "character_class": "Dhanurdhara", "owner_id": player1_id
    }).json()

    bhima = requests.post(f"{BASE_URL}/characters/", json={
        "name": "Bhima", "race": "Human", "character_class": "Yodha", "owner_id": player1_id
    }).json()

    gaya = requests.post(f"{BASE_URL}/characters/", json={
        "name": "Gaya", "race": "Gandharva", "character_class": "Chara", "owner_id": player1_id
    }).json()
    print("Created Arjuna, Bhima, and Gaya.")
    print("-" * 20)

    # === Phase 4: Teach Abilities ===
    print("4. Teaching Abilities...")
    requests.post(f"{BASE_URL}/characters/{arjuna['id']}/learn_ability/", json={"ability_id": longbow_shot['id']})
    requests.post(f"{BASE_URL}/characters/{bhima['id']}/learn_ability/", json={"ability_id": gada_strike['id']})
    requests.post(f"{BASE_URL}/characters/{gaya['id']}/learn_ability/", json={"ability_id": dagger_strike['id']})
    print("Taught abilities to all characters.")
    print("-" * 20)
    
    # === Phase 5: Create Game Session ===
    print("5. Creating Game Session...")
    session_payload = {
        "campaign_name": "The Asura's Lair",
        "gm_id": gm_id,
        "character_ids": [arjuna['id'], bhima['id'], gaya['id']]
    }
    session_response = requests.post(f"{BASE_URL}/sessions/", json=session_payload)
    print("Created 'The Asura's Lair' session.")
    print_response(session_response)

    print("--- DATABASE SEEDING COMPLETE! ---")
    print("You can now refresh your UI at http://localhost:5173")


if __name__ == "__main__":
    main()