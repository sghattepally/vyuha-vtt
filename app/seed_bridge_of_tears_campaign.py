# seed_bridge_of_tears_campaign.py
"""
Complete Bridge of Tears Campaign Setup
Creates campaign with characters, scenes, and all necessary data
Run this AFTER models are updated and migrated
"""

from models import SessionLocal, Campaign, Scene, Character, User
from sqlalchemy.orm import Session

GM_USER_ID = 1

def create_bridge_of_tears_campaign(db: Session):
    """Create the complete Bridge of Tears campaign"""
    
    print("Creating Bridge of Tears Campaign...")
    
    # Check if campaign already exists
    existing = db.query(Campaign).filter(Campaign.name == "Bridge of Tears").first()
    if existing:
        print("Campaign already exists. Skipping...")
        return existing
    
    # Get all character IDs (assume they're already created by seed_bridge_of_tears.py)
    player_char_names = [
        "Devrath the Dutiful",
        "Madhavi the Burdened",
        "Nalayira the Idealist",
        "Keshava the Calculator",
        "Tara the Mystic",
        "Vikram the Reformed"
    ]
    
    enemy_char_names = [
        "Rakshasa Warrior",
        "Rakshasa Shaman",
        "Rakshasa Chieftain"
    ]
    
    # Get character IDs
    player_char_ids = []
    for name in player_char_names:
        char = db.query(Character).filter(
            Character.name == name,
            Character.owner_id == GM_USER_ID
        ).first()
        if char:
            player_char_ids.append(char.id)
        else:
            print(f"WARNING: Character '{name}' not found. Run seed_bridge_of_tears.py first!")
    
    enemy_char_ids = []
    for name in enemy_char_names:
        char = db.query(Character).filter(
            Character.name == name,
            Character.owner_id == GM_USER_ID
        ).first()
        if char:
            enemy_char_ids.append(char.id)
        else:
            print(f"WARNING: Character '{name}' not found. Run seed_bridge_of_tears.py first!")
    
    # Create campaign
    campaign = Campaign(
        name="Bridge of Tears",
        description="""A moral test of sacrifice and duty. 

When refugees fleeing Rakshasa raiders arrive at an ancient bridge during monsoon season, the party must decide: save everyone and risk the bridge falling, or make impossible choices about who lives and who dies.

The bridge groans under the weight. The raiders close in. Not everyone can cross. Who do you save when every choice means someone else dies?""",
        theme="sacrifice",
        recommended_level=1,
        recommended_party_size=4,
        estimated_duration_minutes=60,
        player_character_ids=player_char_ids,
        npc_character_ids=[],  # NPCs are roleplay-only, not character records
        enemy_character_ids=enemy_char_ids,
        creator_user_id=GM_USER_ID,
        is_published=True
    )
    
    db.add(campaign)
    db.flush()  # Get campaign ID
    
    # Create scenes
    scenes_data = [
        {
            "name": "Act 1: The Storm Gathers",
            "description": "The party guards the bridge as refugees flee through the rain. The bridge groans under their weight.",
            "scene_order": 1,
            "background_url": "https://example.com/bridge_storm.jpg",  # Placeholder
            "cards": [
                {
                    "id": "bridge_card",
                    "name": "The Narmada Crossing",
                    "image_url": "https://example.com/bridge_icon.png",
                    "x": 100,
                    "y": 100,
                    "width": 300,
                    "height": 200,
                    "z_index": 1,
                    "collapsed": False,
                    "description": "An ancient stone bridge blessed by sage Agastya. Integrity: 30/30"
                },
                {
                    "id": "refugees_card",
                    "name": "Fleeing Refugees",
                    "image_url": "https://example.com/refugees_icon.png",
                    "x": 50,
                    "y": 350,
                    "width": 250,
                    "height": 150,
                    "z_index": 2,
                    "collapsed": False,
                    "description": "20 terrified refugees: Devi & her children, Grandfather Rajan, Meera & siblings, Vikrant the merchant..."
                }
            ]
        },
        {
            "name": "Act 2: The Raiders Arrive",
            "description": "Rakshasa warriors charge the bridge. Combat begins.",
            "scene_order": 2,
            "background_url": "https://example.com/bridge_combat.jpg",
            "cards": [
                {
                    "id": "combat_grid_card",
                    "name": "Battlefield",
                    "image_url": "https://example.com/grid_icon.png",
                    "x": 150,
                    "y": 100,
                    "width": 400,
                    "height": 300,
                    "z_index": 1,
                    "collapsed": False,
                    "description": "3 squares wide, 15 squares long. Narrow bridge = tactical positioning."
                }
            ]
        },
        {
            "name": "Act 3: The Aftermath",
            "description": "The battle is won, but at what cost? The final choice awaits.",
            "scene_order": 3,
            "background_url": "https://example.com/bridge_aftermath.jpg",
            "cards": [
                {
                    "id": "choice_card",
                    "name": "The Headman's Dilemma",
                    "image_url": "https://example.com/choice_icon.png",
                    "x": 200,
                    "y": 200,
                    "width": 350,
                    "height": 250,
                    "z_index": 1,
                    "collapsed": False,
                    "description": "100 gold pieces. Rebuild the bridge or help the refugees? You cannot do both."
                }
            ]
        }
    ]
    
    for scene_data in scenes_data:
        scene = Scene(
            campaign_id=campaign.id,
            name=scene_data["name"],
            description=scene_data["description"],
            scene_order=scene_data["scene_order"],
            background_url=scene_data["background_url"],
            cards=scene_data["cards"]
        )
        db.add(scene)
    
    db.commit()
    db.refresh(campaign)
    
    print(f"✓ Created campaign: {campaign.name} (ID: {campaign.id})")
    print(f"✓ Added {len(player_char_ids)} player characters")
    print(f"✓ Added {len(enemy_char_ids)} enemy templates")
    print(f"✓ Created {len(scenes_data)} scenes")
    
    return campaign


def print_campaign_setup_instructions(campaign: Campaign):
    """Print instructions for using the campaign"""
    
    print("\n" + "="*60)
    print("BRIDGE OF TEARS CAMPAIGN - READY TO PLAY")
    print("="*60)
    print(f"\nCampaign ID: {campaign.id}")
    print(f"Campaign Name: {campaign.name}")
    print(f"\nTO RUN THE CAMPAIGN:")
    print("\n1. GM creates a new session")
    print(f"2. GM selects campaign ID {campaign.id} for the session")
    print("   POST /sessions/{session_id}/select_campaign?campaign_id=" + str(campaign.id))
    print("\n3. Players join the lobby via access code")
    print("\n4. Players see the 6 available characters and select one")
    print("   POST /sessions/{session_id}/select_character")
    print("   Body: {\"player_id\": X, \"character_id\": Y}")
    print("\n5. Once 4 players have selected characters, GM starts the session")
    print("   POST /sessions/{session_id}/start_with_campaign")
    print("\n6. GM can set active scenes during play:")
    print("   POST /sessions/{session_id}/set_active_scene?scene_id=X")
    print("\n7. GM adds enemies during Act 2 using existing NPC manager")
    print("\n8. GM manages environmental object (bridge) using existing system")
    print("\nCHARACTERS AVAILABLE:")
    for char_id in campaign.player_character_ids:
        print(f"  - Character ID {char_id}")
    print("\nENEMIES AVAILABLE:")
    for char_id in campaign.enemy_character_ids:
        print(f"  - Enemy ID {char_id}")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        # Ensure characters exist first
        char_count = db.query(Character).filter(Character.owner_id == GM_USER_ID).count()
        if char_count < 9:  # 6 players + 3 enemies
            print("ERROR: Characters not found. Run seed_bridge_of_tears.py first!")
            print("Expected at least 9 characters (6 pre-gens + 3 enemies)")
            exit(1)
        
        campaign = create_bridge_of_tears_campaign(db)
        print_campaign_setup_instructions(campaign)
        
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
        raise
    finally:
        db.close()