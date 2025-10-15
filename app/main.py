# app/main.py

# ==================================
# 1. Imports
# ==================================
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, game_rules
from .models import engine, SessionLocal
import pydantic
import random
from typing import List

# ==================================
# 2. Database Setup
# ==================================
models.Base.metadata.create_all(bind=engine)

# ==================================
# 3. Pydantic Schemas
# ==================================
class UserCreate(pydantic.BaseModel):
    username: str

class AbilityCreate(pydantic.BaseModel):
    name: str
    description: str | None = None
    action_type: str
    range: int = 1
    resource_cost: int = 0
    resource_type: str | None = None
    to_hit_attribute: str | None = None
    effect_type: str
    damage_dice: str | None = None
    damage_attribute: str | None = None
    status_effect: str | None = None

class AbilitySchema(AbilityCreate):
    id: int
    class Config:
        from_attributes = True

class CharacterAbilityCreate(pydantic.BaseModel):
    ability_id: int

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
    bala: int; dakshata: int; dhriti: int; buddhi: int; prajna: int; samkalpa: int
    max_prana: int; max_tapas: int; max_maya: int
    movement_speed: int
    class Config:
        from_attributes = True

class SessionCharacterSchema(pydantic.BaseModel):
    id: int
    character_id: int
    character_name: str
    current_prana: int
    current_tapas: int
    current_maya: int
    x_pos: int | None = None
    y_pos: int | None = None
    class Config:
        from_attributes = True

class GameSessionCreate(pydantic.BaseModel):
    campaign_name: str
    gm_id: int
    character_ids: List[int]

class GameSessionSchema(pydantic.BaseModel):
    id: int
    campaign_name: str
    current_mode: str
    active_loka_resonance: str
    participants: List[SessionCharacterSchema] = []
    class Config:
        from_attributes = True

class ParticipantPosition(pydantic.BaseModel):
    participant_id: int # This is the SessionCharacter ID
    x_pos: int
    y_pos: int

# The new, more powerful update schema
class GameSessionUpdate(pydantic.BaseModel):
    current_mode: str | None = None
    active_loka_resonance: str | None = None
    participant_positions: List[ParticipantPosition] | None = None

class GameAction(pydantic.BaseModel):
    actor_id: int
    action_type: str
    ability_id: int | None = None
    target_id: int | None = None
    new_x: int | None = None
    new_y: int | None = None

# ==================================
# 4. The FastAPI App Instance
# ==================================
app = FastAPI()
origins = [
    "http://localhost:5173", # The address of our Vite React app
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)
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
    return {"message": "Welcome to the Vyuha VTT Backend!"}

# --- USER ENDPOINTS ---
@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = models.User(**user.model_dump())
    db.add(new_user); db.commit(); db.refresh(new_user)
    return new_user

# --- ABILITY ENDPOINTS (The Rulebook) ---
@app.post("/abilities/", response_model=AbilitySchema)
def create_ability(ability: AbilityCreate, db: Session = Depends(get_db)):
    new_ability = models.Ability(**ability.model_dump())
    db.add(new_ability); db.commit(); db.refresh(new_ability)
    return new_ability

# --- CHARACTER ENDPOINTS ---
@app.post("/characters/", response_model=CharacterSchema)
def create_character(character_input: CharacterCreate, db: Session = Depends(get_db)):
    template = game_rules.CLASS_TEMPLATES.get(character_input.character_class)
    if not template:
        raise HTTPException(status_code=400, detail="Invalid character class")
    dhriti_modifier = game_rules.get_attribute_modifier(template["attributes"]["dhriti"])
    character_data = {
        "name": character_input.name, "race": character_input.race,
        "character_class": character_input.character_class, "owner_id": character_input.owner_id,
        "max_prana": 10 + dhriti_modifier,
        "max_tapas": template["max_tapas"], "max_maya": template["max_maya"],
        **template["attributes"]
    }
    new_character = models.Character(**character_data)
    db.add(new_character); db.commit(); db.refresh(new_character)
    return new_character

@app.get("/users/{user_id}/characters/", response_model=List[CharacterSchema])
def read_user_characters(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Character).filter(models.Character.owner_id == user_id).all()

# --- THIS ENDPOINT WAS MISSING ---
@app.post("/characters/{character_id}/learn_ability/", response_model=CharacterSchema)
def learn_ability(character_id: int, ability_link: CharacterAbilityCreate, db: Session = Depends(get_db)):
    character = db.query(models.Character).filter(models.Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    new_link = models.CharacterAbility(
        character_id=character_id,
        ability_id=ability_link.ability_id
    )
    db.add(new_link)
    db.commit()
    return character
# ---------------------------------

# --- SESSION ENDPOINTS (The Game Itself) ---
@app.post("/sessions/", response_model=GameSessionSchema)
def create_session(session_input: GameSessionCreate, db: Session = Depends(get_db)):
    new_session = models.GameSession(campaign_name=session_input.campaign_name, gm_id=session_input.gm_id)
    db.add(new_session); db.commit()
    for char_id in session_input.character_ids:
        char_template = db.query(models.Character).filter(models.Character.id == char_id).first()
        if char_template:
            session_char = models.SessionCharacter(
                session_id=new_session.id, character_id=char_id,
                current_prana=char_template.max_prana,
                current_tapas=char_template.max_tapas, current_maya=char_template.max_maya
            )
            db.add(session_char)
    db.commit(); db.refresh(new_session)
    return read_session(new_session.id, db)

@app.get("/sessions/{session_id}/", response_model=GameSessionSchema)
def read_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    participants_data = []
    for p in session.participants:
        participants_data.append({
            "id": p.id, "character_id": p.character_id,
            "character_name": p.character.name, "current_prana": p.current_prana,
            "current_tapas": p.current_tapas, "current_maya": p.current_maya,
            "x_pos": p.x_pos, "y_pos": p.y_pos
        })
    return GameSessionSchema(
        id=session.id, campaign_name=session.campaign_name,
        current_mode=session.current_mode, active_loka_resonance=session.active_loka_resonance,
        participants=participants_data
    )

# app/main.py - in the API Endpoints section

@app.patch("/sessions/{session_id}/", response_model=GameSessionSchema)
def update_session(session_id: int, session_update: GameSessionUpdate, db: Session = Depends(get_db)):
    # 1. Find the existing session in the database
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Update the simple fields (mode, loka)
    update_data = session_update.model_dump(exclude_unset=True)
    if "current_mode" in update_data:
        session.current_mode = update_data["current_mode"]
    if "active_loka_resonance" in update_data:
        session.active_loka_resonance = update_data["active_loka_resonance"]

    # 3. Process participant positions
    if session_update.participant_positions:
        for pos_data in session_update.participant_positions:
            participant = db.query(models.SessionCharacter).filter(
                models.SessionCharacter.id == pos_data.participant_id,
                models.SessionCharacter.session_id == session_id
            ).first()
            if participant:
                participant.x_pos = pos_data.x_pos
                participant.y_pos = pos_data.y_pos

    # 4. Commit the changes
    db.commit()

    # 5. NEW SAFER RETURN: Refresh the session object we already have and return it
    db.refresh(session)
    # This manually rebuilds the response to ensure all data is fresh
    return read_session(session_id, db)

# --- THE GAME ENGINE ---
@app.post("/sessions/{session_id}/action")
def perform_action(session_id: int, action: GameAction, db: Session = Depends(get_db)):
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    actor = db.query(models.SessionCharacter).filter(models.SessionCharacter.id == action.actor_id).first()
    if not session or not actor or actor.session_id != session_id:
        raise HTTPException(status_code=400, detail="Invalid actor or session")
    if action.action_type == "MOVE":
        distance = abs(actor.x_pos - action.new_x) + abs(actor.y_pos - action.new_y)
        if distance > actor.character.movement_speed:
            raise HTTPException(status_code=400, detail="Move distance exceeds speed")
        actor.x_pos = action.new_x; actor.y_pos = action.new_y
    elif action.action_type == "ATTACK":
        target = db.query(models.SessionCharacter).filter(models.SessionCharacter.id == action.target_id).first()
        ability = db.query(models.Ability).filter(models.Ability.id == action.ability_id).first()
        if not target or not ability:
            raise HTTPException(status_code=404, detail="Target or Ability not found")
        distance = max(abs(actor.x_pos - target.x_pos), abs(actor.y_pos - target.y_pos))
        if distance > ability.range:
            raise HTTPException(status_code=400, detail=f"Target out of range (Range: {ability.range}, Dist: {distance})")
        to_hit_attr = getattr(actor.character, ability.to_hit_attribute)
        to_hit_mod = game_rules.get_attribute_modifier(to_hit_attr)
        attack_roll = random.randint(1, 20)
        total_attack = attack_roll + to_hit_mod
        evasion_mod = game_rules.get_attribute_modifier(target.character.dakshata)
        evasion_dc = 10 + evasion_mod
        if total_attack >= evasion_dc:
            damage_mod = 0
            if ability.damage_attribute and ability.damage_attribute != "none":
                damage_attr = getattr(actor.character, ability.damage_attribute)
                damage_mod = game_rules.get_attribute_modifier(damage_attr)
            num, dice = map(int, ability.damage_dice.split('d'))
            damage_roll = sum(random.randint(1, dice) for _ in range(num))
            total_damage = max(0, damage_roll + damage_mod)
            target.current_prana -= total_damage
    db.commit()
    return read_session(session_id, db)