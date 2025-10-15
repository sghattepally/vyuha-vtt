# app/main.py

# ==================================
# 1. Imports
# ==================================
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models
from .models import engine, SessionLocal
import pydantic
import random
from typing import List
from . import game_rules # Importing game rules for potential future use



# ==================================
# 2. Database Setup
# ==================================
# This line creates the database tables if they don't exist
models.Base.metadata.create_all(bind=engine)


# ==================================
# 3. Pydantic Schemas (Data Shapes)
# ==================================
class UserCreate(pydantic.BaseModel):
    username: str

class CharacterCreate(pydantic.BaseModel):
    name: str
    race: str
    character_class: str
    owner_id: int

class CharacterSchema(pydantic.BaseModel):
    id: int
    name: str
    race: str
    character_class: str
    level: int
    bala: int
    dakshata: int
    dhriti: int
    buddhi: int
    prajna: int
    samkalpa: int
    max_prana: int
    max_tapas: int
    max_maya: int

    class Config:
        from_attributes = True

# Schema for a character's state *within* a session
class SessionCharacterSchema(pydantic.BaseModel):
    character_id: int
    current_prana: int
    current_tapas: int
    current_maya: int
    x_pos: int | None = None # Using | None makes it optional
    y_pos: int | None = None

    class Config:
        from_attributes = True

# Schema for creating a new game session
class GameSessionCreate(pydantic.BaseModel):
    campaign_name: str
    gm_id: int # The User ID of the Game Master
    character_ids: List[int] # A list of character IDs to add to the game

# Schema for viewing a full game session
class GameSessionSchema(pydantic.BaseModel):
    id: int
    campaign_name: str
    current_mode: str
    active_loka_resonance: str
    participants: List[SessionCharacterSchema] = [] # Will contain a list of participants

    class Config:
        from_attributes = True

# Schema for UPDATING a session
class GameSessionUpdate(pydantic.BaseModel):
    current_mode: str | None = None
    active_loka_resonance: str | None = None

# Schema for performing an action in a game session
class GameAction(pydantic.BaseModel):
    actor_id: int
    target_id: int
    ability_id: int # The ID of the ABILITY being used

# --- The Ability Model ---
class AbilityCreate(pydantic.BaseModel):
    name: str
    description: str | None = None
    action_type: str
    resource_cost: int = 0
    resource_type: str | None = None
    to_hit_attribute: str | None = None
    effect_type: str
    damage_dice: str | None = None
    damage_attribute: str | None = None
    status_effect: str | None = None

# --- Ability Schema with ID ---
class AbilitySchema(AbilityCreate):
    id: int
    class Config:
        from_attributes = True

# --- CharacterAbility Link Table Schema ---
class CharacterAbilityCreate(pydantic.BaseModel):
    ability_id: int


# ==================================
# 4. The FastAPI App Instance
# ==================================
# THIS IS THE CRUCIAL LINE that was likely in the wrong place.
# It must come BEFORE any @app decorators.
app = FastAPI()


# ==================================
# 5. Reusable Database Dependency
# ==================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================================
# 6. API Endpoints
# ==================================
@app.get("/")
def read_root():
    return {"message": "Welcome to the Vyuha VTT Backend! The database is connected."}

@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users/")
def read_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.post("/characters/", response_model=CharacterSchema)
def create_character(character_input: CharacterCreate, db: Session = Depends(get_db)):
    # 1. Look up the class template from our game rules
    template = game_rules.CLASS_TEMPLATES.get(character_input.character_class)
    if not template:
        # We can add error handling here later
        return {"error": "Invalid character class"}

    # 2. Calculate starting Prana (Health)
    dhriti_modifier = game_rules.get_attribute_modifier(template["attributes"]["dhriti"])
    starting_prana = 10 + dhriti_modifier

    # 3. Create the full character data dictionary
    character_data = {
        "name": character_input.name,
        "race": character_input.race,
        "character_class": character_input.character_class,
        "owner_id": character_input.owner_id,
        "level": 1,
        "max_prana": starting_prana,
        "max_tapas": template["max_tapas"],
        "max_maya": template["max_maya"],
        **template["attributes"] # This cleverly unpacks all the attributes (bala, etc.)
    }

    # 4. Create the SQLAlchemy model and save to DB
    new_character = models.Character(**character_data)
    
    db.add(new_character)
    db.commit()
    db.refresh(new_character)
    
    return new_character

@app.get("/characters/", response_model=List[CharacterSchema])
def read_characters(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # 1. Query the database for all characters
    characters = db.query(models.Character).filter(models.Character.owner_id == user_id).offset(skip).limit(limit).all()
    
    # 2. Return the list of characters
    return characters

@app.post("/sessions/", response_model=GameSessionSchema)
def create_session(session_input: GameSessionCreate, db: Session = Depends(get_db)):
    # 1. Create the main GameSession object
    new_session = models.GameSession(
        campaign_name=session_input.campaign_name,
        # gm_id=session_input.gm_id  <-- We need to add gm_id to the model first!
    )
    db.add(new_session)
    db.commit() # Commit here to get an ID for the new_session

    # 2. Add the selected characters to the session
    for char_id in session_input.character_ids:
        # Find the character's template in the database
        character_template = db.query(models.Character).filter(models.Character.id == char_id).first()
        if not character_template:
            continue # Or raise an error that the character wasn't found

        # Create the session-specific character state
        session_character = models.SessionCharacter(
            session_id=new_session.id,
            character_id=char_id,
            # Start them with full resources!
            current_prana=character_template.max_prana,
            current_tapas=character_template.max_tapas,
            current_maya=character_template.max_maya
        )
        db.add(session_character)

    # 3. Commit the new session characters and refresh the main session
    db.commit()
    db.refresh(new_session)

    return new_session

@app.get("/sessions/{session_id}/", response_model=GameSessionSchema)
def read_session(session_id: int, db: Session = Depends(get_db)):
    # 1. Query the database for a session with the matching ID
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    
    # 2. If no session is found, raise a 404 Not Found error
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # 3. If the session is found, return it
    return session

@app.patch("/sessions/{session_id}/", response_model=GameSessionSchema)
def update_session(session_id: int, session_update: GameSessionUpdate, db: Session = Depends(get_db)):
    # 1. Find the existing session in the database
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Update the fields if new values were provided
    update_data = session_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session, key, value)

    # 3. Commit the changes and return the updated session
    db.commit()
    db.refresh(session)
    return session

# Create a new ability in our "rulebook"
@app.post("/abilities/", response_model=AbilitySchema)
def create_ability(ability: AbilityCreate, db: Session = Depends(get_db)):
    new_ability = models.Ability(**ability.model_dump())
    db.add(new_ability)
    db.commit()
    db.refresh(new_ability)
    return new_ability

# "Teach" an ability to a character
@app.post("/characters/{character_id}/learn_ability/", response_model=CharacterSchema)
def learn_ability(character_id: int, ability_link: CharacterAbilityCreate, db: Session = Depends(get_db)):
    # Create the link in our junction table
    new_link = models.CharacterAbility(
        character_id=character_id,
        ability_id=ability_link.ability_id
    )
    db.add(new_link)
    db.commit()
    
    # Return the full character sheet to show they've learned it
    character = db.query(models.Character).filter(models.Character.id == character_id).first()
    return character

# Perform an action in a game session
@app.post("/sessions/{session_id}/action", response_model=GameSessionSchema)
def perform_action(session_id: int, action: GameAction, db: Session = Depends(get_db)):
    # 1. Fetch all the necessary data from the database
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    actor = db.query(models.SessionCharacter).filter(models.SessionCharacter.id == action.actor_id).first()
    target = db.query(models.SessionCharacter).filter(models.SessionCharacter.id == action.target_id).first()
    ability = db.query(models.Ability).filter(models.Ability.id == action.ability_id).first()

    if not all([session, actor, target, ability]):
        raise HTTPException(status_code=404, detail="Game resource not found")

    actor_template = actor.character
    target_template = target.character
    
    # --- PRE-ACTION CHECKS (Resource Costs) ---
    if ability.resource_type == "Tapas":
        if actor.current_tapas < ability.resource_cost:
            raise HTTPException(status_code=400, detail="Not enough Tapas!")
        actor.current_tapas -= ability.resource_cost
    elif ability.resource_type == "Māyā":
        if actor.current_maya < ability.resource_cost:
            raise HTTPException(status_code=400, detail="Not enough Māyā!")
        actor.current_maya -= ability.resource_cost

    # --- THE DYNAMIC GAME ENGINE LOGIC ---
    message = f"{actor_template.name} uses {ability.name} on {target_template.name}."

    # --- A. ATTACK ROLL LOGIC (for abilities that need to hit) ---
    if ability.action_type in ["MELEE_ATTACK", "RANGED_ATTACK"]:
        # Get the rule for hitting from the ability
        to_hit_attr_name = ability.to_hit_attribute
        actor_to_hit_score = getattr(actor_template, to_hit_attr_name)
        to_hit_modifier = game_rules.get_attribute_modifier(actor_to_hit_score)
        
        attack_roll = random.randint(1, 20)
        total_attack_value = attack_roll + to_hit_modifier
        
        # Calculate target's Evasion DC (our house rule for now)
        target_evasion_modifier = game_rules.get_attribute_modifier(target_template.dakshata)
        evasion_dc = 10 + target_evasion_modifier
        
        if total_attack_value < evasion_dc:
            message += f" It misses! (Rolled {total_attack_value} vs DC {evasion_dc})"
        else:
            message += f" It hits! (Rolled {total_attack_value} vs DC {evasion_dc})"
            # --- B. EFFECT LOGIC (if the attack hits) ---
            if ability.effect_type == "DAMAGE":
                damage_modifier = 0
                if ability.damage_attribute != "none":
                    damage_attr_name = ability.damage_attribute
                    actor_damage_score = getattr(actor_template, damage_attr_name)
                    damage_modifier = game_rules.get_attribute_modifier(actor_damage_score)
                
                num_dice, dice_type = map(int, ability.damage_dice.split('d'))
                damage_roll = sum(random.randint(1, dice_type) for _ in range(num_dice))
                total_damage = max(0, damage_roll + damage_modifier) # Can't do negative damage
                
                target.current_prana -= total_damage
                message += f" for {total_damage} damage."

    # --- C. MANTRA / SPELL LOGIC (for abilities that don't roll to hit) ---
    elif ability.action_type == "MANTRA_EFFECT":
        # For now, mantras are automatic hits. We can add saving throws later.
        if ability.effect_type == "DAMAGE":
            damage_modifier = 0
            if ability.damage_attribute != "none":
                damage_attr_name = ability.damage_attribute
                actor_damage_score = getattr(actor_template, damage_attr_name)
                damage_modifier = game_rules.get_attribute_modifier(actor_damage_score)
            
            num_dice, dice_type = map(int, ability.damage_dice.split('d'))
            damage_roll = sum(random.randint(1, dice_type) for _ in range(num_dice))
            total_damage = max(0, damage_roll + damage_modifier)
            
            target.current_prana -= total_damage
            message += f" It deals {total_damage} damage."

    # Commit all changes (like damage and resource costs) to the database
    db.commit()
    
    # Return the full, updated session state
    db.refresh(session)
    # We can add the 'message' to the response later
    return session