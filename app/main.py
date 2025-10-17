# app/main.py

# ==================================
# 1. Imports
# ==================================
import os
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from . import models, game_rules
from .models import engine, SessionLocal
import pydantic
import random
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import json, string
import asyncio


# ==================================
# 2. Database Setup
# ==================================
models.Base.metadata.create_all(bind=engine)

# ==================================
# 3. Pydantic Schemas
# ==================================
# --- User Schemas ---
class PlayerCreate(pydantic.BaseModel):
    display_name: str

class PlayerSchema(pydantic.BaseModel):
    id: int
    display_name: str
    current_session_id: int | None = None
    class Config:
        from_attributes = True


# --- Ability Schemas ---
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

# --- Character Schemas ---
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
    bala: int
    dakshata: int
    dhriti: int
    buddhi: int
    prajna: int
    samkalpa: int
    max_prana: int
    max_tapas: int
    max_maya: int
    movement_speed: int
    class Config:
        from_attributes = True

# --- Session Schemas ---
class SessionCharacterSchema(pydantic.BaseModel):
    id: int
    player_id: int | None = None
    x_pos: int | None = None
    y_pos: int | None = None
    current_prana: int
    current_tapas: int
    current_maya: int
    remaining_speed: int
    status: str
    character: CharacterSchema
    class Config:
        from_attributes = True

class GameSessionCreate(pydantic.BaseModel):
    campaign_name: str
    gm_id: int
    gm_access_code: str
    character_ids: List[int] = []

class GameSessionSchema(pydantic.BaseModel):
    id: int
    gm_id: int
    access_code: str | None = None
    campaign_name: str
    current_mode: str
    active_loka_resonance: str
    participants: List[SessionCharacterSchema] = []
    turn_order: List[int] = []
    current_turn_index: int = 0
    log: List[str] = []
    class Config:
        from_attributes = True

class AddCharacterRequest(pydantic.BaseModel):
    player_id: int
    character_id: int

class JoinRequest(pydantic.BaseModel):
    access_code: str
    display_name: str

class JoinResponse(pydantic.BaseModel):
    player: PlayerSchema
    session: GameSessionSchema

class ParticipantPosition(pydantic.BaseModel):
    participant_id: int
    x_pos: int
    y_pos: int

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

class ActionResponse(pydantic.BaseModel):
    session: GameSessionSchema
    message: str

# ==================================
# 4. The FastAPI App Instance & CORS
# ==================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: int):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: int):
        if session_id in self.active_connections and websocket in self.active_connections[session_id]:
            self.active_connections[session_id].remove(websocket)

    async def broadcast_json(self, session_id: int, json_data: str):
        if session_id in self.active_connections:
            # Create a list of tasks for sending messages
            tasks = [connection.send_text(json_data) for connection in self.active_connections[session_id]]
            # Run them concurrently
            await asyncio.gather(*tasks)

    # This is a new helper function we've added.
    async def broadcast_session_state(self, session_id: int, db: Session):
        """Fetches the session from DB, validates it, and broadcasts it."""
        print(f"Attempting to broadcast state for session {session_id}")
        session_db = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
        if session_db:
            # Convert the SQLAlchemy object to a Pydantic schema
            session_schema = GameSessionSchema.from_orm(session_db)
            # Convert the schema to a JSON string
            json_payload = session_schema.model_dump_json()
            # Broadcast the JSON string
            await self.broadcast_json(session_id, json_payload)
            print(f"Successfully broadcasted state for session {session_id}")
        else:
            print(f"Could not find session {session_id} in DB to broadcast.")
manager = ConnectionManager()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ==================================
# 5. DB Dependency
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

def generate_access_code(length: int = 6) -> str:
    """Generates a random alphanumeric access code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.get("/rules/races", response_model=List[str])
def get_races():
    """Returns a list of all available player races."""
    # This list is based on your Player's Handbook
    return [
        "Manushya", "Vaanara", "Yaksha", "Gandharva", 
        "Apsara", "Kinnara", "Vidyadhara", "Naga", "Asura"
    ]

@app.get("/rules/classes", response_model=List[str])
def get_classes():
    """Returns a list of all available player classes."""
    # This dynamically gets the class names from your game_rules file
    return list(game_rules.CLASS_TEMPLATES.keys())

@app.websocket("/ws/{session_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: int, user_id: int):
    await manager.connect(websocket, session_id)
    db = SessionLocal()
    try:
        # When a user connects, immediately broadcast the latest game state to everyone in the session.
        await manager.broadcast_session_state(session_id, db)
        
        # Keep the connection alive to listen for future messages (e.g., chat)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"User {user_id} disconnected from session {session_id}")
        manager.disconnect(websocket, session_id)
    finally:
        db.close()

# --- USER ENDPOINTS ---
@app.post("/users/", response_model=PlayerSchema)
def get_or_create_user(user: PlayerCreate, db: Session = Depends(get_db)):
    """
    Finds a user by display_name. If they don't exist, creates them.
    This prevents creating duplicate users.
    """
    db_user = db.query(models.User).filter(models.User.display_name == user.display_name).first()
    if db_user:
        return db_user
    
    new_user = models.User(display_name=user.display_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/join", response_model=JoinResponse)
async def join_session(join_request: JoinRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    session = db.query(models.GameSession).filter(models.GameSession.access_code == join_request.access_code.upper()).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session with that access code not found.")
    
    # Create a new player (User) record for this session
    new_player = models.User(
        display_name=join_request.display_name,
        current_session_id=session.id
    )
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    
    # Broadcast the updated session state to everyone in the lobby
    background_tasks.add_task(manager.broadcast_session_state, session.id, db)
    
    return {
        "player": PlayerSchema.model_validate(new_player),
        "session": GameSessionSchema.model_validate(session)
    }

@app.get("/users/", response_model=List[PlayerSchema])
def read_all_users(db: Session = Depends(get_db)):
    """Returns a list of all users."""
    return db.query(models.User).all()

# --- ABILITY ENDPOINTS ---
@app.post("/abilities/", response_model=AbilitySchema)
def create_ability(ability: AbilityCreate, db: Session = Depends(get_db)):
    new_ability = models.Ability(**ability.model_dump())
    db.add(new_ability); db.commit(); db.refresh(new_ability)
    return new_ability

@app.get("/abilities/", response_model=List[AbilitySchema])
def read_all_abilities(db: Session = Depends(get_db)):
    """Returns a list of all abilities available in the game."""
    return db.query(models.Ability).all()

# --- CHARACTER ENDPOINTS ---
@app.post("/characters/", response_model=CharacterSchema)
def create_character(character_input: CharacterCreate, db: Session = Depends(get_db)):
    template = game_rules.CLASS_TEMPLATES.get(character_input.character_class)
    if not template: raise HTTPException(status_code=400, detail="Invalid character class")
    dhriti_mod = game_rules.get_attribute_modifier(template["attributes"]["dhriti"])
    character_data = {
        "name": character_input.name, "race": character_input.race,
        "character_class": character_input.character_class, "owner_id": character_input.owner_id,
        "max_prana": 10 + dhriti_mod,
        "max_tapas": template["max_tapas"], "max_maya": template["max_maya"],
        **template["attributes"]
    }
    new_character = models.Character(**character_data)
    db.add(new_character); db.commit(); db.refresh(new_character)
    DEFAULT_ABILITIES = {
        "Yodha": "Gada Strike",
        "Dhanurdhara": "Longbow Shot",
        "Chara": "Dagger Strike",
        "Rishi": "Agni Mantra",
        "Sutradhara": "Dagger Strike"
    }
    
    ability_name_to_learn = DEFAULT_ABILITIES.get(new_character.character_class)
    
    if ability_name_to_learn:
        # Find the ability in the database
        ability_to_learn = db.query(models.Ability).filter(models.Ability.name == ability_name_to_learn).first()
        
        if ability_to_learn:
            # Create the link between the new character and the ability
            new_link = models.CharacterAbility(
                character_id=new_character.id, 
                ability_id=ability_to_learn.id
            )
            db.add(new_link)
            db.commit()
            print(f"Assigned '{ability_name_to_learn}' to new character '{new_character.name}'")
    return new_character

@app.get("/users/{user_id}/characters", response_model=List[CharacterSchema])
def get_user_characters(user_id: int, db: Session = Depends(get_db)):
    """Fetches all character templates owned by a specific user."""
    characters = db.query(models.Character).filter(models.Character.owner_id == user_id).all()
    if not characters:
        return []
    return characters

@app.post("/characters/{character_id}/learn_ability/", response_model=CharacterSchema)
def learn_ability(character_id: int, ability_link: CharacterAbilityCreate, db: Session = Depends(get_db)):
    character = db.query(models.Character).filter(models.Character.id == character_id).first()
    if not character: raise HTTPException(status_code=404, detail="Character not found")
    new_link = models.CharacterAbility(character_id=character_id, ability_id=ability_link.ability_id)
    db.add(new_link); db.commit()
    return character

@app.get("/characters/{character_id}/abilities/", response_model=List[AbilitySchema])
def get_character_abilities(character_id: int, db: Session = Depends(get_db)):
    """Returns a list of all abilities a specific character has learned."""
    character = db.query(models.Character).filter(models.Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    ability_links = db.query(models.CharacterAbility).filter(models.CharacterAbility.character_id == character_id).all()
    
    abilities = []
    for link in ability_links:
        ability = db.query(models.Ability).filter(models.Ability.id == link.ability_id).first()
        if ability:
            abilities.append(ability)
            
    return abilities

# --- SESSION ENDPOINTS ---
@app.post("/sessions", response_model=GameSessionSchema)
def create_session(session_input: GameSessionCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    SECRET_GM_CODE = os.getenv("GM_ACCESS_CODE")
    if not SECRET_GM_CODE or session_input.gm_access_code != SECRET_GM_CODE:
        raise HTTPException(status_code=403, detail="Invalid GM Access Code. Cannot create session.")

    # Find the GM user record
    gm_user = db.query(models.User).filter(models.User.id == session_input.gm_id).first()
    if not gm_user:
        raise HTTPException(status_code=404, detail="GM user not found.")

    while True:
        code = generate_access_code()
        if not db.query(models.GameSession).filter(models.GameSession.access_code == code).first():
            break

    new_session = models.GameSession(
        campaign_name=session_input.campaign_name, 
        gm_id=session_input.gm_id,
        access_code=code
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    
    gm_user.current_session_id = new_session.id
    db.commit()
    return new_session

@app.get("/sessions/{session_id}/", response_model=GameSessionSchema)
def read_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session: raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.get("/sessions/{session_id}/players", response_model=List[PlayerSchema])
def get_session_players(session_id: int, db: Session = Depends(get_db)):
    """Returns a list of all players currently in a session's lobby."""
    players = db.query(models.User).filter(models.User.current_session_id == session_id).all()
    if not players:
        return []
    return players

@app.patch("/sessions/{session_id}/", response_model=GameSessionSchema)
async def update_session(session_id: int, session_update: GameSessionUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session: raise HTTPException(status_code=404, detail="Session not found")
    
    # ... (The logic inside this function remains the same)
    update_data = session_update.model_dump(exclude_unset=True)
    if "current_mode" in update_data: session.current_mode = update_data["current_mode"]
    if "active_loka_resonance" in update_data: session.active_loka_resonance = update_data["active_loka_resonance"]
    if session_update.participant_positions:
        for pos_data in session_update.participant_positions:
            p = db.query(models.SessionCharacter).filter(models.SessionCharacter.id == pos_data.participant_id, models.SessionCharacter.session_id == session_id).first()
            if p: p.x_pos = pos_data.x_pos; p.y_pos = pos_data.y_pos
    
    db.commit()
    
    updated_schema = GameSessionSchema.model_validate(session)
    background_tasks.add_task(manager.broadcast_json, session_id, updated_schema.model_dump_json())

    return updated_schema

@app.post("/sessions/{session_id}/add_character", response_model=GameSessionSchema)
async def add_character_to_session(session_id: int, request: AddCharacterRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Adds a player's chosen character to the game session."""
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    character = db.query(models.Character).filter(models.Character.id == request.character_id).first()
    player = db.query(models.User).filter(models.User.id == request.player_id).first()

    if not all([session, character, player]):
        raise HTTPException(status_code=404, detail="Session, Character, or Player not found.")

    if character.owner_id != player.id:
        raise HTTPException(status_code=403, detail="Player does not own this character.")

    # Check if this player already has a character in the session
    existing_participant = db.query(models.SessionCharacter).filter(
        models.SessionCharacter.session_id == session_id,
        models.SessionCharacter.player_id == request.player_id
    ).first()

    if existing_participant:
        raise HTTPException(status_code=400, detail="Player already has a character in this session.")

    # Create the new session participant
    new_participant = models.SessionCharacter(
        session_id=session_id,
        character_id=request.character_id,
        player_id=request.player_id,
        current_prana=character.max_prana,
        current_tapas=character.max_tapas,
        current_maya=character.max_maya,
        x_pos=None,
        y_pos=None
    )
    db.add(new_participant)
    db.commit()

    # Broadcast the update to all connected clients
    background_tasks.add_task(manager.broadcast_session_state, session_id, db)
    
    return session

@app.delete("/sessions/{session_id}/participants/{participant_id}", response_model=GameSessionSchema)
async def remove_character_from_session(session_id: int, participant_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Removes a participant (SessionCharacter) from a game session."""
    
    # Find the specific participant record to delete
    participant = db.query(models.SessionCharacter).filter(
        models.SessionCharacter.session_id == session_id,
        models.SessionCharacter.id == participant_id
    ).first()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found in this session.")

    session = participant.session # Get a reference to the session before deleting

    db.delete(participant)
    db.commit()

    # Broadcast the update to all connected clients
    background_tasks.add_task(manager.broadcast_session_state, session_id, db)
    
    return session

@app.post("/sessions/{session_id}/begin_combat", response_model=GameSessionSchema)
async def begin_combat(session_id: int, background_tasks: BackgroundTasks,db: Session = Depends(get_db)):
    # ... (The logic inside this function remains the same)
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session or session.current_mode != 'staging': raise HTTPException(status_code=400, detail="Not in staging.")
    initiative_results = []
    for p in session.participants:
        dakshata_mod = game_rules.get_attribute_modifier(p.character.dakshata)
        roll = random.randint(1, 20)
        initiative_results.append({"participant_id": p.id, "score": roll + dakshata_mod, "dakshata": p.character.dakshata})
        p.status = 'active'
    initiative_results.sort(key=lambda x: (x['score'], x['dakshata']), reverse=True)
    session.turn_order = [result['participant_id'] for result in initiative_results]
    session.current_turn_index = 0; session.current_mode = 'combat'
    if session.turn_order:
        first_char = db.query(models.SessionCharacter).filter(models.SessionCharacter.id == session.turn_order[0]).first()
        if first_char: first_char.remaining_speed = first_char.character.movement_speed
    
    db.commit()

    updated_schema = GameSessionSchema.model_validate(session)
    background_tasks.add_task(manager.broadcast_json, session_id, updated_schema.model_dump_json())

    return updated_schema


# --- THE GAME ENGINE ---
# In app/main.py, replace the entire perform_action function with this:

@app.post("/sessions/{session_id}/action", response_model=ActionResponse)
async def perform_action(session_id: int, action: GameAction, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    actor = db.query(models.SessionCharacter).filter(models.SessionCharacter.id == action.actor_id).first()
    if not session or not actor or actor.session_id != session_id:
        raise HTTPException(status_code=400, detail="Invalid actor or session")

    if actor.status == "downed":
        raise HTTPException(status_code=400, detail=f"{actor.character.name} is downed and cannot take actions.")

    message = ""

    if action.action_type == "MOVE":
        if actor.x_pos is None: raise HTTPException(status_code=400, detail="Actor not on grid")
        distance = abs(actor.x_pos - action.new_x) + abs(actor.y_pos - action.new_y)
        
        # --- THE FIX for movement ---
        # It now correctly checks against remaining_speed
        if distance > actor.remaining_speed:
            raise HTTPException(status_code=400, detail=f"Move exceeds remaining speed of {actor.remaining_speed}")
        
        actor.x_pos = action.new_x
        actor.y_pos = action.new_y
        actor.remaining_speed -= distance # Subtract the distance moved
        # ----------------------------

        message = f"{actor.character.name} moves to ({action.new_x}, {action.new_y}). Remaining speed: {actor.remaining_speed}."

    elif action.action_type == "ATTACK":
        target = db.query(models.SessionCharacter).filter(models.SessionCharacter.id == action.target_id).first()
        ability = db.query(models.Ability).filter(models.Ability.id == action.ability_id).first()
        if not target or not ability: raise HTTPException(status_code=404, detail="Target or Ability not found")
        if actor.x_pos is None or target.x_pos is None: raise HTTPException(status_code=400, detail="Characters not on grid")
        
        distance = max(abs(actor.x_pos - target.x_pos), abs(actor.y_pos - target.y_pos))
        if distance > ability.range:
            raise HTTPException(status_code=400, detail=f"Target out of range! (Range: {ability.range}, Dist: {distance})")
        
        to_hit_mod = game_rules.get_attribute_modifier(getattr(actor.character, ability.to_hit_attribute))
        attack_roll = random.randint(1, 20)
        total_attack = attack_roll + to_hit_mod
        
        evasion_dc = 10 + game_rules.get_attribute_modifier(target.character.dakshata)
        
        if total_attack >= evasion_dc:
            damage_mod = 0
            if ability.damage_attribute and ability.damage_attribute != "none":
                damage_mod = game_rules.get_attribute_modifier(getattr(actor.character, ability.damage_attribute))
            
            num, dice = map(int, ability.damage_dice.split('d'))
            damage_roll = sum(random.randint(1, dice) for _ in range(num))
            total_damage = max(0, damage_roll + damage_mod)
            
            target.current_prana = max(0, target.current_prana - total_damage)
            
            # --- NEW, DETAILED MESSAGE ---
            message = (
                f"{actor.character.name}'s {ability.name} hits {target.character.name}! "
                f"(Roll: {attack_roll} + Mod: {to_hit_mod} = {total_attack} vs DC {evasion_dc}). "
                f"Deals {total_damage} damage. {target.character.name} has {target.current_prana} Prāṇa remaining."
            )
            # ---------------------------

            if target.current_prana == 0:
                target.status = "downed"
                message += f" {target.character.name} is downed!"

        else:
            # --- NEW, DETAILED MESSAGE ---
            message = (
                f"{actor.character.name}'s {ability.name} misses {target.character.name}! "
                f"(Roll: {attack_roll} + Mod: {to_hit_mod} = {total_attack} vs DC {evasion_dc})."
            )
            # ---------------------------
    if message:
        # Prepend the new message to the session's log.
        # We check `session.log` exists to avoid errors on older sessions in your DB.
        current_log = session.log if session.log else []
        new_log = [message] + current_log
        # Limit the log to the most recent 50 messages to prevent it from getting too large.
        session.log = new_log[:50]
    # <--- MODIFICATION END --->
    db.commit()
    updated_schema = GameSessionSchema.model_validate(session)
    background_tasks.add_task(manager.broadcast_json, session_id, updated_schema.model_dump_json())
    
    return {"session": updated_schema, "message": message}

@app.post("/sessions/{session_id}/next_turn", response_model=GameSessionSchema)
async def next_turn(session_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # ... (The logic inside this function remains the same)
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session or session.current_mode != 'combat': raise HTTPException(status_code=400, detail="Not in combat.")
    current_char = db.query(models.SessionCharacter).filter(models.SessionCharacter.id == session.turn_order[session.current_turn_index]).first()
    if current_char: current_char.remaining_speed = 0
    next_index = (session.current_turn_index + 1) % len(session.turn_order)
    session.current_turn_index = next_index
    next_char = db.query(models.SessionCharacter).filter(models.SessionCharacter.id == session.turn_order[next_index]).first()
    if next_char: next_char.remaining_speed = next_char.character.movement_speed
    
    db.commit()

    updated_schema = GameSessionSchema.model_validate(session)
    background_tasks.add_task(manager.broadcast_json, session_id, updated_schema.model_dump_json())

    return updated_schema

@app.post("/sessions/{session_id}/end_combat", response_model=GameSessionSchema)
async def end_combat(session_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Ends the current combat, switching the mode back to exploration."""
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.current_mode != 'combat':
        raise HTTPException(status_code=400, detail="Session is not in combat.")

    session.current_mode = 'exploration'
    db.commit()

    # Broadcast the updated state to all players
    background_tasks.add_task(manager.broadcast_session_state, session.id, db)
    return session