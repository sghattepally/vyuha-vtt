# app/main.py

# ==================================
# 1. Imports
# ==================================
import os
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from . import models, game_rules
from .models import engine, SessionLocal
import pydantic
import random
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import json, string
import asyncio
import datetime


# ==================================
# 2. Database Setup
# ==================================
models.Base.metadata.create_all(bind=engine)

# ==================================
# 3. Pydantic Schemas
# ==================================
def get_modifier(score: int) -> int:
    return (score - 10) // 2

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


class RaceSchema(pydantic.BaseModel):
    name: str
    description: str
    bala_mod: int
    dakshata_mod: int
    dhriti_mod: int
    buddhi_mod: int
    prajna_mod: int
    samkalpa_mod: int

    class Config:
        from_attributes = True

class CharClassSchema(pydantic.BaseModel):
    name: str
    description: str
    primary_attribute: str
    base_bala: int
    base_dakshata: int
    base_dhriti: int
    base_buddhi: int
    base_prajna: int
    base_samkalpa: int

    class Config:
        from_attributes = True

# --- Character Schemas ---
class CharacterAbilityCreate(pydantic.BaseModel):
    ability_id: int

class CharacterCreate(pydantic.BaseModel):
    name: str
    race: str
    char_class: str
    owner_id: int

class CharacterSchema(pydantic.BaseModel):
    id: int
    name: str
    race: RaceSchema
    char_class: CharClassSchema
    owner_id: int
    level: int
    movement_speed: int
    @pydantic.computed_field
    def bala(self) -> int:
        return self.char_class.base_bala + self.race.bala_mod

    @pydantic.computed_field
    def dakshata(self) -> int:
        return self.char_class.base_dakshata + self.race.dakshata_mod

    @pydantic.computed_field
    def dhriti(self) -> int:
        return self.char_class.base_dhriti + self.race.dhriti_mod

    @pydantic.computed_field
    def buddhi(self) -> int:
        return self.char_class.base_buddhi + self.race.buddhi_mod

    @pydantic.computed_field
    def prajna(self) -> int:
        return self.char_class.base_prajna + self.race.prajna_mod

    @pydantic.computed_field
    def samkalpa(self) -> int:
        return self.char_class.base_samkalpa + self.race.samkalpa_mod
    
    # Also calculate secondary stats
    @pydantic.computed_field
    def max_prana(self) -> int:
        # Prana is based on Fortitude (Dhriti)
        return 10 + (self.level * get_modifier(self.dhriti))

    @pydantic.computed_field
    def max_tapas(self) -> int:
        # Tapas is the sum of Deha (Body) attribute modifiers
        bala_mod = get_modifier(self.bala)
        dakshata_mod = get_modifier(self.dakshata)
        dhriti_mod = get_modifier(self.dhriti)
        return bala_mod + dakshata_mod + dhriti_mod

    @pydantic.computed_field
    def max_maya(self) -> int:
        # Māyā is the sum of Ātman (Spirit) attribute modifiers
        buddhi_mod = get_modifier(self.buddhi)
        prajna_mod = get_modifier(self.prajna)
        samkalpa_mod = get_modifier(self.samkalpa)
        return buddhi_mod + prajna_mod + samkalpa_mod

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

    class Config:
        from_attributes = True

class GameLogEntrySchema(pydantic.BaseModel):
    id: int
    timestamp: datetime.datetime
    event_type: str
    actor_id: int | None = None
    target_id: int | None = None
    details: dict | None = None
    
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

class AddNpcsRequest(pydantic.BaseModel):
    character_ids: List[int] # Expects a list of IDs

class UpdateNpcsRequest(pydantic.BaseModel):
    npc_ids: List[int]

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

    async def broadcast_session_state(self, session_id: int, db: Session):
        """Fetches the session from DB, validates it, and broadcasts it."""
        print(f"Attempting to broadcast state for session {session_id}")
        session_db = db.query(models.GameSession).options(joinedload(models.GameSession.participants).joinedload(models.SessionCharacter.character)).filter(models.GameSession.id == session_id).first()
        if session_db:
            # Convert the SQLAlchemy object to a Pydantic schema
            session_schema = GameSessionSchema.model_validate(session_db)
            
            typed_message = {
                "type": "session_update",
                "data": session_schema.model_dump()
            }
            json_payload = json.dumps(typed_message, default=str)
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

def log_event(db: Session, session_id: int, event_type: str, actor_id: int | None = None, target_id: int | None = None, details: dict | None = None):
    """Creates and saves a new structured log entry to the database."""
    new_entry = models.GameLogEntry(
        session_id=session_id,
        event_type=event_type,
        actor_id=actor_id,
        target_id=target_id,
        details=details if details else {}
    )
    db.add(new_entry)
    db.commit()

def generate_access_code(length: int = 6) -> str:
    """Generates a random alphanumeric access code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.get("/rules/races", response_model=List[RaceSchema])
def get_races(db: Session = Depends(get_db)):
    """Fetches all playable races with their full details from the database."""
    races = db.query(models.Race).order_by(models.Race.name).all()
    return races

@app.get("/rules/classes", response_model=List[CharClassSchema])
def get_classes(db: Session = Depends(get_db)):
    """Fetches all playable classes with their full details from the database."""
    classes = db.query(models.Char_Class).order_by(models.Char_Class.name).all()
    return classes

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
    log_event(db, session.id, 'player_join', details={"player_name": new_player.display_name})
    
    background_tasks.add_task(manager.broadcast_session_state, session.id, db)
    await manager.broadcast_json(session.id, json.dumps({"type": "new_log_entry"}))
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
    """
    Creates a new character, links it to a race and class from the database,
    and assigns default abilities defined in that class's database record.
    """
    # Look up the chosen Race and Class in the database.
    db_race = db.query(models.Race).filter(models.Race.name == character_input.race).first()
    if not db_race:
        raise HTTPException(status_code=400, detail=f"Invalid race: {character_input.race}")

    db_class = db.query(models.Char_Class).filter(models.Char_Class.name == character_input.char_class).first()
    if not db_class:
        raise HTTPException(status_code=400, detail=f"Invalid class: {character_input.char_class}")

    # Create the base character record using data from the input schema
    new_character = models.Character(
        name=character_input.name,
        owner_id=character_input.owner_id,
        race_id=db_race.id,
        char_class_id=db_class.id
    )
    db.add(new_character)
    db.commit()
    db.refresh(new_character)

    # Assign default abilities
    if db_class.default_abilities:
        abilities_to_learn = db.query(models.Ability).filter(
            models.Ability.name.in_(db_class.default_abilities)
        ).all()
        
        for ability in abilities_to_learn:
            new_link = models.CharacterAbility(
                character_id=new_character.id,
                ability_id=ability.id
            )
            db.add(new_link)
        
        db.commit()

    return new_character

    # Step 3: Assign default abilities using the list from the class's DB record.
    if db_class.default_abilities:
        abilities_to_learn = db.query(models.Ability).filter(
            models.Ability.name.in_(db_class.default_abilities)
        ).all()
        
        for ability in abilities_to_learn:
            # Use the existing CharacterAbility junction object to create the link.
            new_link = models.CharacterAbility(
                character_id=new_character.id,
                ability_id=ability.id
            )
            db.add(new_link)
        
        db.commit()
        print(f"Assigned default abilities to '{new_character.name}'")

    # Step 4: Return the character. The Pydantic schema will handle all stat calculations.
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
    if "current_mode" in update_data: 
        session.current_mode = update_data["current_mode"]
        log_event(db, session_id, 'mode_change', details={'new_mode': session.current_mode})
    if "active_loka_resonance" in update_data: session.active_loka_resonance = update_data["active_loka_resonance"]
    if session_update.participant_positions:
        for pos_data in session_update.participant_positions:
            p = db.query(models.SessionCharacter).filter(models.SessionCharacter.id == pos_data.participant_id, models.SessionCharacter.session_id == session_id).first()
            if p: 
                if p.x_pos is None and pos_data.x_pos is not None:
                    log_event(db, session_id, 'token_place', actor_id=p.id, 
                              details={'character_name': p.character.name, 
                                       'pos': {'x': pos_data.x_pos, 'y': pos_data.y_pos}})
                else:
                    log_event(db, session_id, 'token_move', details={
                        "character_name": p.character.name,
                        "pos": {"x": pos_data.x_pos, "y": pos_data.y_pos}
                    })
                p.x_pos = pos_data.x_pos
                p.y_pos = pos_data.y_pos
    
    db.commit()
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))
    background_tasks.add_task(manager.broadcast_session_state, session_id, db)
    return GameSessionSchema.model_validate(session)

@app.post("/sessions/{session_id}/add_character", response_model=GameSessionSchema)
async def add_character_to_session(session_id: int, request: AddCharacterRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Adds a character to the game session.
    - If added by a player, enforces a 1-character limit.
    - If added by the GM, it is treated as an NPC.
    """
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    requesting_user = db.query(models.User).filter(models.User.id == request.player_id).first()

    # REFACTOR: Eagerly load the character with its race and class for stat calculations.
    character = db.query(models.Character).options(
        joinedload(models.Character.race),
        joinedload(models.Character.char_class)
    ).filter(models.Character.id == request.character_id).first()

    if not all([session, character, requesting_user]):
        raise HTTPException(status_code=404, detail="Session, Character, or Requesting User not found.")

    is_request_from_gm = (session.gm_id == requesting_user.id)

    # ... (Your existing logic for checking ownership and character limits is correct and remains unchanged)
    if not is_request_from_gm:
        if character.owner_id != requesting_user.id:
            raise HTTPException(status_code=403, detail="Player does not own this character.")
        
        existing_participant = db.query(models.SessionCharacter).filter(
            models.SessionCharacter.session_id == session_id,
            models.SessionCharacter.player_id == request.player_id
        ).first()
        if existing_participant:
            raise HTTPException(status_code=400, detail="Player already has a character in this session.")
        
    elif is_request_from_gm and character.owner_id != session.gm_id:
         raise HTTPException(status_code=403, detail="GM does not own this character template.")
    
    # REFACTOR: Use the Pydantic schema to calculate the character's max values.
    char_schema = CharacterSchema.model_validate(character)
    
    # REFACTOR: Create the new participant using the calculated values.
    new_participant = models.SessionCharacter(
        session_id=session_id,
        character_id=request.character_id,
        # CORRECTED: NPCs added by the GM should be controlled by the GM.
        player_id=session.gm_id if is_request_from_gm else request.player_id,
        current_prana=char_schema.max_prana,
        current_tapas=char_schema.max_tapas,
        current_maya=char_schema.max_maya,
        x_pos=None,
        y_pos=None
    )

    db.add(new_participant)
    db.commit()
    log_event(db, session_id, 'character_select', actor_id=new_participant.id, details={"player_name": requesting_user.display_name, "character_name": character.name})
    background_tasks.add_task(manager.broadcast_session_state, session_id, db)
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))
    return GameSessionSchema.model_validate(session)

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

# app/main.py

@app.post("/sessions/{session_id}/begin_combat", response_model=GameSessionSchema)
async def begin_combat(session_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    session = db.query(models.GameSession).options(
        joinedload(models.GameSession.participants)
        .joinedload(models.SessionCharacter.character)  
        .joinedload(models.Character.race),            
        joinedload(models.GameSession.participants)
        .joinedload(models.SessionCharacter.character)  
        .joinedload(models.Character.char_class)       
    ).filter(models.GameSession.id == session_id).first()

    if not session or session.current_mode != 'staging':
        raise HTTPException(status_code=400, detail="Not in staging.")

    
    initiative_results = []
    for p in session.participants:
        if p.character:
            dakshata_mod = get_modifier(CharacterSchema.model_validate(p.character).dakshata)
            roll = random.randint(1, 20)
            total_score = roll + dakshata_mod
            
            log_event(db, session_id, 'initiative_roll', actor_id=p.id, details={
                "character_name": p.character.name,
                "roll": roll,
                "modifier": dakshata_mod,
                "total": total_score
            })

            initiative_results.append({
                "participant_id": p.id,
                "score": total_score,
                "dakshata": CharacterSchema.model_validate(p.character).dakshata,
                "participant_name": CharacterSchema.model_validate(p.character).name
            })
            p.status = 'active'
    
    initiative_results.sort(key=lambda x: (x['score'], x['dakshata']), reverse=True)
    
    session.turn_order = [result['participant_id'] for result in initiative_results]
    session.current_turn_index = 0
    session.current_mode = 'combat'
    
    order_string = " > ".join([res['participant_name'] for res in initiative_results])
    log_event(db, session_id, 'turn_order_set', details={"order": order_string})

    db.commit()

    background_tasks.add_task(manager.broadcast_session_state, session_id, db)
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))
    
    return GameSessionSchema.model_validate(session)

# --- THE GAME ENGINE ---
# In app/main.py, replace the entire perform_action function with this:

@app.post("/sessions/{session_id}/action", response_model=ActionResponse)
async def perform_action(session_id: int, action: GameAction, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    actor = db.query(models.SessionCharacter).filter(models.SessionCharacter.id == action.actor_id).first()
    validated_actor_character = CharacterSchema.model_validate(actor.character)
    if not session or not actor or actor.session_id != session_id:
        raise HTTPException(status_code=400, detail="Invalid actor or session")

    if actor.status == "downed":
        raise HTTPException(status_code=400, detail=f"{actor.character.name} is downed and cannot take actions.")

    message = ""

    if action.action_type == "MOVE":
        if actor.x_pos is None: raise HTTPException(status_code=400, detail="Actor not on grid")
        distance = abs(actor.x_pos - action.new_x) + abs(actor.y_pos - action.new_y)
        if distance > actor.remaining_speed:
            raise HTTPException(status_code=400, detail=f"Move exceeds remaining speed of {actor.remaining_speed}")
        
        actor.x_pos = action.new_x
        actor.y_pos = action.new_y
        actor.remaining_speed -= distance # Subtract the distance moved
        log_event(db, session_id, 'move', actor_id=actor.id, details={
            "character_name": actor.character.name,
            "new_pos": {"x": action.new_x, "y": action.new_y}
        })

        

    elif action.action_type == "ATTACK":
        target = db.query(models.SessionCharacter).filter(models.SessionCharacter.id == action.target_id).first()
        ability = db.query(models.Ability).filter(models.Ability.id == action.ability_id).first()
        if not target or not ability: raise HTTPException(status_code=404, detail="Target or Ability not found")
        if actor.x_pos is None or target.x_pos is None: raise HTTPException(status_code=400, detail="Characters not on grid")
        distance = max(abs(actor.x_pos - target.x_pos), abs(actor.y_pos - target.y_pos))
        if distance > ability.range:
            # Instead of raising an error, we just set the message.
            log_event(db, session_id, 'out_of_range', actor_id=actor.id, target_id=target.id, details={
                "actor_name": actor.character.name,
                "target_name": target.character.name,
                "ability_name": ability.name
            })
        else:
            # The rest of the attack logic only runs if the target is in range.
            to_hit_mod = get_modifier(getattr(validated_actor_character, ability.to_hit_attribute))
            attack_roll = random.randint(1, 20)
            total_attack = attack_roll + to_hit_mod
            evasion_dc = 10 + get_modifier(CharacterSchema.model_validate(target.character).dakshata)
            
            if total_attack >= evasion_dc:
                damage_mod = 0
                if ability.damage_attribute:
                    damage_mod = get_modifier(getattr(validated_actor_character, ability.damage_attribute))
                
                num, dice = map(int, ability.damage_dice.split('d'))
                damage_roll = sum(random.randint(1, dice) for _ in range(num))
                total_damage = max(0, damage_roll + damage_mod)
                target.current_prana = max(0, target.current_prana - total_damage)
                log_event(db, session_id, 'attack_hit', actor_id=actor.id, target_id=target.id, details={
                "actor_name": actor.character.name,
                "target_name": target.character.name,
                "ability_name": ability.name,
                "roll": attack_roll, "modifier": to_hit_mod, "total": total_attack, "dc": evasion_dc,
                "damage": total_damage
            })
                if target.current_prana == 0:
                    target.status = "downed"
                    log_event(db, session_id, 'status_change', target_id=target.id, details={"character_name": target.character.name, "new_status": "downed"})
            else:
                log_event(db, session_id, 'attack_miss', actor_id=actor.id, target_id=target.id, details={
                "actor_name": actor.character.name,
                "target_name": target.character.name,
                "ability_name": ability.name,
                "roll": attack_roll, "modifier": to_hit_mod, "total": total_attack, "dc": evasion_dc
            })
    
    db.commit()
    background_tasks.add_task(manager.broadcast_session_state, session_id, db)
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))
    
    return {"session": GameSessionSchema.model_validate(session), "message": message}

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

    
    background_tasks.add_task(manager.broadcast_session_state, session.id, db)

    return GameSessionSchema.model_validate(session)

@app.post("/sessions/{session_id}/end_combat", response_model=GameSessionSchema)
async def end_combat(session_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Ends the current combat, switching the mode back to exploration."""
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.current_mode != 'combat':
        raise HTTPException(status_code=400, detail="Session is not in combat.")

    session.current_mode = 'exploration'
    log_event(db, session_id, 'mode_change', details={"new_mode": "exploration"})
    db.commit()
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))
    # Broadcast the updated state to all players
    background_tasks.add_task(manager.broadcast_session_state, session.id, db)
    return GameSessionSchema.model_validate(session)

@app.post("/sessions/{session_id}/add_npcs", response_model=GameSessionSchema)
async def add_npcs_to_session(session_id: int, request: AddNpcsRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """GM-only endpoint to add multiple NPCs to a session at once."""
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # REFACTOR: Eagerly load the character templates with their race and class data.
    # This is essential for our calculations.
    character_templates = db.query(models.Character).options(
        joinedload(models.Character.race),
        joinedload(models.Character.char_class)
    ).filter(models.Character.id.in_(request.character_ids)).all()
    
    # Verify the GM owns all of them. This logic is unchanged.
    for char in character_templates:
        if char.owner_id != session.gm_id:
            raise HTTPException(status_code=403, detail=f"GM does not own character template: {char.name}")

    new_npcs = []
    for char in character_templates:
        # REFACTOR: Use our Pydantic schema to calculate the character's max values.
        char_schema = CharacterSchema.model_validate(char)
        
        # REFACTOR: Create the new SessionCharacter using the calculated values from the schema.
        new_npc = models.SessionCharacter(
            session_id=session.id,
            character_id=char.id,
            player_id=session.gm_id,
            current_prana=char_schema.max_prana,
            current_tapas=char_schema.max_tapas,
            current_maya=char_schema.max_maya,
            x_pos=None,
            y_pos=None
        )
        new_npcs.append(new_npc)

    db.add_all(new_npcs)
    db.commit()

    background_tasks.add_task(manager.broadcast_session_state, session_id, db)
    # The final returned session will correctly include the newly added NPCs.
    return GameSessionSchema.model_validate(session)

@app.post("/sessions/{session_id}/update_npcs/", response_model=GameSessionSchema)
async def update_session_npcs(session_id: int, request: UpdateNpcsRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Synchronizes the NPCs in a session with a provided list of character IDs.
    """
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # This logic for identifying current NPCs is correct, but we can make it more robust
    current_npc_participants = db.query(models.SessionCharacter).join(models.Character).filter(
        models.SessionCharacter.session_id == session_id,
        models.SessionCharacter.player_id == session.gm_id
    ).all()
    current_npc_ids = {p.character_id for p in current_npc_participants}
    
    requested_npc_ids = set(request.npc_ids)

    # This logic for determining which NPCs to add and remove is unchanged.
    ids_to_add = requested_npc_ids - current_npc_ids
    ids_to_remove = current_npc_ids - requested_npc_ids

    # This logic for removing NPCs is also unchanged.
    if ids_to_remove:
        participants_to_remove = [p for p in current_npc_participants if p.character_id in ids_to_remove]
        for p in participants_to_remove:
            db.delete(p)

    # REFACTOR: This section is updated to correctly calculate initial resources for new NPCs.
    if ids_to_add:
        # Step 1: Eagerly load the character templates with their race and class data.
        character_templates = db.query(models.Character).options(
            joinedload(models.Character.race),
            joinedload(models.Character.char_class)
        ).filter(models.Character.id.in_(ids_to_add)).all()

        for char in character_templates:
            # Security check remains the same.
            if char.owner_id != session.gm_id:
                raise HTTPException(status_code=403, detail=f"GM does not own character template: {char.name}")

            # Step 2: Use our Pydantic schema to calculate the character's max values.
            char_schema = CharacterSchema.model_validate(char)
            
            # Step 3: Create the new SessionCharacter using the calculated values.
            new_npc = models.SessionCharacter(
                session_id=session.id, 
                character_id=char.id, 
                player_id=session.gm_id, # NPCs are "owned" by the GM in a session
                current_prana=char_schema.max_prana, 
                current_tapas=char_schema.max_tapas, 
                current_maya=char_schema.max_maya
            )
            db.add(new_npc)

    db.commit()
    background_tasks.add_task(manager.broadcast_session_state, session_id, db)
    return GameSessionSchema.model_validate(session)

@app.get("/sessions/{session_id}/log", response_model=List[GameLogEntrySchema])
def get_session_log(session_id: int, db: Session = Depends(get_db)):
    """Fetches all log entries for a session, ordered by timestamp."""
    log_entries = db.query(models.GameLogEntry).filter(models.GameLogEntry.session_id == session_id).order_by(models.GameLogEntry.timestamp.asc()).all()
    return log_entries