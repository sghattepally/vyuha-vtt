# app/main.py

# ==================================
# 1. Imports
# ==================================
import os
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from . import models, game_rules
from .models import engine, SessionLocal, ItemType, ActionType, ResourceType, TargetType 
import pydantic
import random
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware
import json, string
import asyncio
import datetime
import math
from .ability_system import (
    AbilitySystem, 
    AbilityExecutionRequest, 
    TargetInfo,
    AbilityExecutionResult
)

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
    action_type: ActionType # Use the Enum for strict validation
    resource_cost: int
    resource_type: Optional[ResourceType] = None # Use the Enum
    requirements: Optional[Dict[str, Any]] = None # For JSON data
    target_type: TargetType
    effect_radius: int = 0
    range: int = 1
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

class ItemSchema(pydantic.BaseModel):
    id: int
    puranic_name: str
    english_name: str | None = None
    description: str | None = None
    item_type: ItemType
    is_stackable: bool

    class Config:
        from_attributes = True # Pydantic v2 syntax

class CharacterInventorySchema(pydantic.BaseModel):
    id: int
    quantity: int
    is_equipped: bool
    item: ItemSchema # This is the nested item data

    class Config:
        from_attributes = True

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
    currency: int = 0 
    inventory: List[CharacterInventorySchema] = [] 
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

class EnvironmentalObjectSectionSchema(pydantic.BaseModel):
    id: int
    section_name: str
    section_index: int
    grid_positions: List[Dict[str, int]] = []
    current_integrity: int
    max_integrity: int
    evasion_dc: int
    armor_value: int
    is_destroyed: bool
    is_critical: bool
    
    class Config:
        from_attributes = True


class EnvironmentalObjectSchema(pydantic.BaseModel):
    id: int
    session_id: int
    name: str
    object_type: str
    description: str
    icon_url: Optional[str] = None
    grid_positions: List[Dict[str, int]] = []
    has_sections: bool
    total_sections: int
    current_integrity: int
    max_integrity: int
    critical_threshold: int
    evasion_dc: int
    armor_value: int
    is_functional: bool
    is_visible_to_players: bool
    camp_metadata: Dict[str, Any] = {}
    sections: List[EnvironmentalObjectSectionSchema] = []
    
    class Config:
        from_attributes = True


class EnvironmentalObjectCreate(pydantic.BaseModel):
    name: str
    object_type: str
    description: str = ""
    icon_url: Optional[str] = None
    grid_positions: List[Dict[str, int]] = []
    has_sections: bool = False
    total_sections: int = 1
    max_integrity: int = 100
    critical_threshold: int = 0
    evasion_dc: int = 10
    armor_value: int = 0
    camp_metadata: Dict[str, Any] = {}


class DamageEnvironmentalObjectRequest(pydantic.BaseModel):
    damage: int
    section_id: Optional[int] = None


class RepairEnvironmentalObjectRequest(pydantic.BaseModel):
    repair_amount: int
    section_id: Optional[int] = None

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
    actions: int
    bonus_actions: int
    reactions: int
    character: CharacterSchema
    class Config:
        from_attributes = True

class GameSessionCreate(pydantic.BaseModel):
    campaign_name: str
    gm_id: int
    gm_access_code: str
    character_ids: List[int] = []

class SkillCheckRequest(pydantic.BaseModel):
    participant_ids: List[int]
    check_type: str
    dc: int
    description: str

class SkillCheckRoll(pydantic.BaseModel):
    skill_check_id: int # Renamed from pending_check_id for clarity
    use_advantage: bool = False

class SkillCheckSchema(pydantic.BaseModel):
    id: int
    participant_id: int
    check_type: str
    dc: int
    description: str
    status: str

    class Config:
        from_attributes = True

class GameSessionSchema(pydantic.BaseModel):
    id: int
    gm_id: int
    access_code: str | None = None
    campaign_name: str
    current_mode: str
    active_loka_resonance: str
    participants: List[SessionCharacterSchema] = []
    turn_order: List[int] = []
    campaign_id: Optional[int] = None
    character_selections: Dict[int, int] = {}
    active_scene_id: Optional[int] = None
    current_turn_index: int = 0
    skill_checks: List[SkillCheckSchema] = []
    environmental_objects: List[EnvironmentalObjectSchema] = []

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

class GiveItemRequest(pydantic.BaseModel):
    character_id: int
    item_id: int
    quantity: int = 1

class GiveItemPlayerRequest(pydantic.BaseModel):
    target_character_id: int
    quantity: int

class ActionPayload(pydantic.BaseModel):
    actor_id: int
    ability_id: int
    target_id: int | None = None
    target_pos: dict | None = None # e.g., {"x": 10, "y": 12}

class CampaignCreate(pydantic.BaseModel):
    name: str
    description: str = ""
    theme: str = ""
    recommended_level: int = 1
    recommended_party_size: int = 4
    estimated_duration_minutes: int = 60
    player_character_ids: List[int] = []
    npc_character_ids: List[int] = []
    enemy_character_ids: List[int] = []
    creator_user_id: Optional[int] = None
    is_published: bool = False


class SceneSchema(pydantic.BaseModel):
    id: int
    campaign_id: int
    name: str
    description: Optional[str] = None
    scene_order: int
    background_url: Optional[str] = None
    cards: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True


class CampaignSchema(pydantic.BaseModel):
    id: int
    name: str
    description: str
    theme: str
    recommended_level: int
    recommended_party_size: int
    estimated_duration_minutes: int
    player_character_ids: List[int]
    npc_character_ids: List[int]
    enemy_character_ids: List[int]
    creator_user_id: Optional[int]
    is_published: bool
    scenes: List[SceneSchema] = []
    
    class Config:
        from_attributes = True


class SceneCreate(pydantic.BaseModel):
    campaign_id: int
    name: str
    description: str = ""
    scene_order: int = 0
    background_url: Optional[str] = None
    cards: List[Dict[str, Any]] = []


class CharacterSelectionRequest(pydantic.BaseModel):
    player_id: int
    character_id: int


class CharacterDeselectionRequest(pydantic.BaseModel):
    player_id: int

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
    char_class = db.query(models.Char_Class).filter(models.Char_Class.id == new_character.char_class_id).first()
    if not char_class:
        # This is a fallback in case the class ID is invalid
        return new_character

    # 2. Look up the default equipment list for this class
    default_items = game_rules.DEFAULT_EQUIPMENT_BY_CLASS.get(char_class.name)

    if default_items:
        # 3. Loop through the list and add each item to the character's inventory
        for item_name, quantity in default_items:
            # Find the master item in the 'items' table
            item_to_add = db.query(models.Item).filter(models.Item.puranic_name == item_name).first()
            if item_to_add:
                # Create the new inventory entry
                new_inventory_item = models.CharacterInventory(
                    character_id=new_character.id,
                    item_id=item_to_add.id,
                    quantity=quantity,
                    is_equipped=False # Items are not equipped by default
                )
                db.add(new_inventory_item)
    
        db.commit() 
        db.refresh(new_character)

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

@app.get("/character/{character_id}/inventory", response_model=List[CharacterInventorySchema])
async def get_character_inventory(character_id: int, db: Session = Depends(get_db)):
    """
    Fetches the complete inventory for a specific character.
    """
    # Query for all inventory entries belonging to the character.
    # `joinedload` tells SQLAlchemy to also fetch the related item data in a single, efficient query.
    inventory_items = db.query(models.CharacterInventory).options(
        joinedload(models.CharacterInventory.item)
    ).filter(models.CharacterInventory.character_id == character_id).all()
    
    if not inventory_items:
        # It's not an error to have an empty inventory, just return an empty list.
        return []
        
    return inventory_items

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
        remaining_speed=char_schema.movement_speed,
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
    for p in session.participants:
        p.actions = 1
        p.bonus_actions = 1
        p.reactions = 4
        db.add(p)
    session.turn_order = [result['participant_id'] for result in initiative_results]
    session.current_turn_index = 0
    session.current_mode = 'combat'
    
    order_string = " > ".join([res['participant_name'] for res in initiative_results])
    log_event(db, session_id, 'turn_order_set', details={"order": order_string})

    db.commit()

    background_tasks.add_task(manager.broadcast_session_state, session_id, db)
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))
    
    return GameSessionSchema.model_validate(session)


@app.post("/sessions/{session_id}/ability", response_model=ActionResponse)
async def execute_ability(
    session_id: int, 
    request: AbilityExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    New unified endpoint for ability execution.
    Handles all ability types: attacks, heals, buffs, area effects, etc.
    """
    
    # Initialize the ability system
    ability_system = AbilitySystem(db, session_id)
    
    # Execute the ability
    result = ability_system.execute_ability(request)
    
    if not result.success:
        print(f"DEBUG: Ability FAILED - {result.message}")
        raise HTTPException(status_code=400, detail=result.message)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"CRITICAL DB ERROR: Failed to commit ability execution: {e}")
        raise HTTPException(status_code=500, detail="Database update failed after action.")
    # Log all events
    for log_detail in result.log_events:
        event_type = log_detail.pop("event_type")
        log_event(
            db, 
            session_id, 
            event_type,
            actor_id=request.actor_id,
            target_id=log_detail.get("target_id"),
            details=log_detail
        )
    
    # Broadcast updates
    background_tasks.add_task(manager.broadcast_session_state, session_id, db)
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))
    
    # Fetch and return updated session
    session = db.query(models.GameSession).filter(
        models.GameSession.id == session_id
    ).first()
    
    return ActionResponse(
        session=GameSessionSchema.model_validate(session),
        message=result.message
    )


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
    if next_char: 
        next_char.remaining_speed = next_char.character.movement_speed
        next_char.actions = 1
        next_char.bonus_actions = 1
    
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

    for p in session.participants:
        p.initiative = None
        p.x_pos = None
        p.y_pos = None
        # We can also reset status if needed, e.g., from 'unconscious' to 'active'
        # if p.current_prana > 0 and p.status != 'active':
        #     p.status = 'active'
        db.add(p)

    # Reset the session's combat-specific fields
    session.current_mode = 'exploration'
    session.turn_order = []
    session.current_turn_index = 0
    db.add(session)
    
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
                current_maya=char_schema.max_maya,
                remaining_speed=char_schema.movement_speed
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

@app.post("/sessions/{session_id}/skill_check/request")
async def request_skill_check(session_id: int, request: SkillCheckRequest, db: Session = Depends(get_db)):
    """
    Endpoint for a GM to request a skill check from one or more participants.
    This creates the pending check records in the database.
    """
    gm_actor_name = "Game Master" # Or fetch GM character name if you have one

    targets = db.query(models.SessionCharacter).options(
        joinedload(models.SessionCharacter.character)
    ).filter(
        models.SessionCharacter.id.in_(request.participant_ids),
        models.SessionCharacter.session_id == session_id
    ).all()

    target_names = [p.character.name for p in targets if p.character]
    if not target_names:
        raise HTTPException(status_code=400, detail="No valid participants found for this skill check.")

    # Now, log a single, detailed event that lists all targeted players.
    log_event(db, session_id, 'skill_check_initiated', details={
        "actor_name": gm_actor_name,
        "description": request.description,
        "check_type": request.check_type.capitalize(),
        "dc": request.dc,
        "target_names": target_names  # This new field lists the players
    })
    # --- END OF CHANGE ---

    # We can reuse the 'targets' list to create the individual check for each participant.
    for participant in targets:
        new_check = models.SkillCheck(
            session_id=session_id,
            participant_id=participant.id,
            check_type=request.check_type,
            dc=request.dc,
            description=request.description,
            status="pending"
        )
        db.add(new_check)

    db.commit()

    # Broadcast the new state to all clients.
    await manager.broadcast_session_state(session_id, db)
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))

    return {"message": f"Skill check request sent to {len(target_names)} participants."}


@app.post("/sessions/{session_id}/skill_check/roll")
async def roll_skill_check(session_id: int, request: SkillCheckRoll, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Performs a skill check. All modifier logic is self-contained in this function.
    """
    skill_check = db.query(models.SkillCheck).options(
        joinedload(models.SkillCheck.participant).
        joinedload(models.SessionCharacter.character).
        joinedload(models.Character.race),
        joinedload(models.SkillCheck.participant).
        joinedload(models.SessionCharacter.character).
        joinedload(models.Character.char_class)
    ).filter(models.SkillCheck.id == request.skill_check_id).first()

    if not skill_check or skill_check.session_id != session_id or skill_check.status != 'pending':
        raise HTTPException(status_code=404, detail="Pending skill check not found.")

    participant = skill_check.participant
    character = participant.character
    if not character:
        raise HTTPException(status_code=400, detail="Participant has no character.")

    validated_character = CharacterSchema.model_validate(character)
    modifier = 0
    check_type = skill_check.check_type

    # 2. Use game_rules ONLY to get the list of derived skills.
    if check_type in game_rules.DERIVED_SKILLS:
        attr1_name, attr2_name = game_rules.DERIVED_SKILLS[check_type]
        score1 = getattr(validated_character, attr1_name)
        score2 = getattr(validated_character, attr2_name)
        mod1 = get_modifier(score1)
        mod2 = get_modifier(score2)
        modifier = math.floor((mod1 + mod2) / 2)
    else:
        score = getattr(validated_character, check_type)
        modifier = get_modifier(score)
        

    roll1 = random.randint(1, 20)
    final_roll = roll1
    advantage_used = False

    if request.use_advantage:
        primary_attribute = check_type
        if check_type in game_rules.DERIVED_SKILLS:
            # For derived skills, the resource is typically tied to the spiritual/willpower attribute
            primary_attribute = game_rules.DERIVED_SKILLS[check_type][1]
        
        resource_to_use = game_rules.ATTRIBUTE_TO_RESOURCE.get(primary_attribute, "tapas") # Default to Tapas

        if resource_to_use == "tapas" and participant.current_tapas > 0:
            participant.current_tapas -= 1
            advantage_used = True
        elif resource_to_use == "maya" and participant.current_maya > 0:
            participant.current_maya -= 1
            advantage_used = True
        
        if advantage_used:
            roll2 = random.randint(1, 20)
            final_roll = max(roll1, roll2)

    total_score = final_roll + modifier
    success = total_score >= skill_check.dc
    skill_check.status = 'completed'
    db.add(skill_check)
    
    # FIX: Add background task for broadcasting state
    # This was missing in the original function.
    background_tasks.add_task(manager.broadcast_session_state, session_id, db)

    log_event(db, session_id, 'skill_check_result', actor_id=participant.id, details={
        "character_name": character.name, "check_type": check_type.capitalize(),
        "roll": final_roll, "modifier": modifier, "total": total_score, "dc": skill_check.dc,
        "success": success, "advantage_used": advantage_used,
        "roll_breakdown": f"{roll1}" + (f", {roll2}" if advantage_used else "")
    })
    
    db.commit()

    # The broadcast for state is now in a background task, but we still need the log entry notification.
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))

    return {
        "success": success,
        "total": total_score,
        "roll": final_roll,
        "modifier": modifier,
        "roll_breakdown": f"{roll1}" + (f", {roll2}" if advantage_used else ""),
        "advantage_used": advantage_used
    }

@app.post("/gm/give-item")
async def gm_give_item(request: GiveItemRequest, db: Session = Depends(get_db)):
    """
    Allows a GM to give a specified quantity of an item to a character.
    If the character already has the item and it's stackable, it updates the quantity.
    Otherwise, it creates a new inventory entry.
    """
    # Find the character and the master item entry
    character = db.query(models.Character).filter(models.Character.id == request.character_id).first()
    item = db.query(models.Item).filter(models.Item.id == request.item_id).first()

    if not character or not item:
        raise HTTPException(status_code=404, detail="Character or Item not found.")

    # Check if the character already has this item
    inventory_entry = db.query(models.CharacterInventory).filter(
        models.CharacterInventory.character_id == request.character_id,
        models.CharacterInventory.item_id == request.item_id
    ).first()

    log_details = {
        "gm_action": "Gave Item",
        "character_name": character.name,
        "item_name": item.puranic_name,
        "quantity": request.quantity
    }

    if inventory_entry and item.is_stackable:
        # If the item exists and is stackable, just increase the quantity
        inventory_entry.quantity += request.quantity
        db.add(inventory_entry)
    else:
        # If the item is new or not stackable, create a new entry
        new_inventory_item = models.CharacterInventory(
            character_id=request.character_id,
            item_id=request.item_id,
            quantity=request.quantity,
            is_equipped=False # Items are never equipped by default
        )
        db.add(new_inventory_item)

    db.commit()

    # Find the session this character is in to broadcast an update
    session_character = db.query(models.SessionCharacter).filter(
        models.SessionCharacter.character_id == request.character_id
    ).first()

    if session_character:
        log_event(db, session_character.session_id, 'gm_give_item', details=log_details)
        await manager.broadcast_session_state(session_character.session_id, db)
        await manager.broadcast_json(session_character.session_id, json.dumps({"type": "new_log_entry"}))

    return {"message": f"Successfully gave {request.quantity} of {item.puranic_name} to {character.name}."}

@app.get("/items", response_model=List[ItemSchema])
async def get_all_items(db: Session = Depends(get_db)):
    """
    Fetches the master list of all items available in the game.
    """
    items = db.query(models.Item).order_by(models.Item.puranic_name).all()
    return items

@app.post("/character/{character_id}/inventory/{inventory_id}/toggle-equip")
async def toggle_equip_item(character_id: int, inventory_id: int, db: Session = Depends(get_db)):
    """
    Toggles the equipped status of an inventory item.
    Enforces game rules, such as unequipping other items of the same type.
    """
    # Find the specific inventory item the player is trying to equip/unequip
    target_inventory_item = db.query(models.CharacterInventory).options(
        joinedload(models.CharacterInventory.item)
    ).filter(
        models.CharacterInventory.id == inventory_id,
        models.CharacterInventory.character_id == character_id
    ).first()

    if not target_inventory_item:
        raise HTTPException(status_code=404, detail="Inventory item not found for this character.")

    # Determine if we are equipping or unequipping
    is_equipping = not target_inventory_item.is_equipped

    if is_equipping:
        # --- Rule Enforcement: Unequip other items of the same type ---
        item_type_to_equip = target_inventory_item.item.item_type
        
        # We only enforce this for single-slot types like weapons and armor
        if item_type_to_equip in [models.ItemType.WEAPON, models.ItemType.ARMOR]:
            # Find any other currently equipped items of the same type
            currently_equipped = db.query(models.CharacterInventory).options(
                joinedload(models.CharacterInventory.item)
            ).filter(
                models.CharacterInventory.character_id == character_id,
                models.CharacterInventory.is_equipped == True
            ).all()

            for equipped_item in currently_equipped:
                if equipped_item.item.item_type == item_type_to_equip:
                    equipped_item.is_equipped = False
                    db.add(equipped_item)

    # Toggle the state of the target item
    target_inventory_item.is_equipped = is_equipping
    db.add(target_inventory_item)
    db.commit()

    # Find the session this character is in to broadcast the update
    session_character = db.query(models.SessionCharacter).filter(
        models.SessionCharacter.character_id == character_id
    ).first()

    if session_character:
        log_event(db, session_character.session_id, 'item_equip', details={
            "character_name": target_inventory_item.character.name,
            "item_name": target_inventory_item.item.puranic_name,
            "equipped": is_equipping
        })
        await manager.broadcast_session_state(session_character.session_id, db)
        await manager.broadcast_json(session_character.session_id, json.dumps({"type": "new_log_entry"}))

    return {"message": f"Item state toggled for {target_inventory_item.item.puranic_name}."}

@app.delete("/inventory/{inventory_id}/destroy")
async def destroy_inventory_item(inventory_id: int, db: Session = Depends(get_db)):
    # 1. Eagerly load all relationships to get the data upfront
    inventory_item = db.query(models.CharacterInventory).options(
        joinedload(models.CharacterInventory.character),
        joinedload(models.CharacterInventory.item)
    ).filter(models.CharacterInventory.id == inventory_id).first()

    if not inventory_item:
        raise HTTPException(status_code=404, detail="Inventory item not found.")
    
    # 2. Store all necessary information for the log BEFORE changing the database
    character_id = inventory_item.character_id
    character_name = inventory_item.character.name
    item_name = inventory_item.item.puranic_name
    
    # 3. Now, perform the database deletion
    db.delete(inventory_item)
    db.commit()

    # Broadcast update to the relevant session
    session_character = db.query(models.SessionCharacter).filter(models.SessionCharacter.character_id == character_id).first()
    if session_character:
        # 4. Use the safe, pre-stored variables for the log event
        log_event(db, session_character.session_id, 'item_destroy', details={
            "character_name": character_name,
            "item_name": item_name
        })
        # The broadcast function does not need the 'db' argument
        await manager.broadcast_session_state(session_character.session_id, db)
        await manager.broadcast_json(session_character.session_id, json.dumps({"type": "new_log_entry"}))
        
    return {"message": "Item destroyed."}

@app.post("/inventory/{inventory_id}/give")
async def give_inventory_item(inventory_id: int, request: GiveItemPlayerRequest, db: Session = Depends(get_db)):
    # Eagerly load relationships to have all data available upfront
    source_item = db.query(models.CharacterInventory).options(
        joinedload(models.CharacterInventory.character),
        joinedload(models.CharacterInventory.item)
    ).filter(models.CharacterInventory.id == inventory_id).first()

    if not source_item:
        raise HTTPException(status_code=404, detail="Source item not found.")
    if request.quantity <= 0 or request.quantity > source_item.quantity:
        raise HTTPException(status_code=400, detail="Invalid quantity specified.")

    target_character = db.query(models.Character).filter(models.Character.id == request.target_character_id).first()
    if not target_character:
        raise HTTPException(status_code=404, detail="Target character not found.")

    # --- Store all data for the log BEFORE making database changes ---
    source_character_id = source_item.character_id
    giver_name = source_item.character.name
    receiver_name = target_character.name
    item_name = source_item.item.puranic_name
    
    # --- START OF NEW LOGIC ---
    # Check if the target already has a stack of this item
    target_existing_item = db.query(models.CharacterInventory).filter(
        models.CharacterInventory.character_id == request.target_character_id,
        models.CharacterInventory.item_id == source_item.item_id
    ).first()

    if target_existing_item and source_item.item.is_stackable:
        # Add to the target's existing stack
        target_existing_item.quantity += request.quantity
        db.add(target_existing_item)
    else:
        # Create a new inventory entry for the target
        new_inventory_item = models.CharacterInventory(
            character_id=request.target_character_id,
            item_id=source_item.item_id,
            quantity=request.quantity,
            is_equipped=False
        )
        db.add(new_inventory_item)

    # Decrement the source stack
    source_item.quantity -= request.quantity
    if source_item.quantity <= 0:
        # If the source stack is empty, delete it
        db.delete(source_item)
    else:
        db.add(source_item)
    # --- END OF NEW LOGIC ---
    
    db.commit()

    session_character = db.query(models.SessionCharacter).filter(models.SessionCharacter.character_id == source_character_id).first()
    if session_character:
        log_event(db, session_character.session_id, 'item_give', details={
            "giver_name": giver_name,
            "receiver_name": receiver_name,
            "item_name": item_name,
            "quantity": request.quantity # Use the requested quantity for the log
        })
        await manager.broadcast_session_state(session_character.session_id, db)
        await manager.broadcast_json(session_character.session_id, json.dumps({"type": "new_log_entry"}))

    return {"message": "Item transferred."}

@app.post("/inventory/{inventory_id}/use")
async def use_inventory_item(inventory_id: int, db: Session = Depends(get_db)):
    
    inventory_item = db.query(models.CharacterInventory).options(
        joinedload(models.CharacterInventory.item),
        joinedload(models.CharacterInventory.character) 
    ).filter(models.CharacterInventory.id == inventory_id).first()
    
    if not inventory_item:
        raise HTTPException(status_code=404, detail="Item not found.")

    # Retrieve the ability ID directly from the loaded item
    # NOTE: This assumes you have already added the 'on_use_ability_id' column to your Item model!
    ability_id_to_use = getattr(inventory_item.item, 'on_use_ability_id', None) 
    
    # CRITICAL: Find the active SessionCharacter (Actor)
    active_participant = db.query(models.SessionCharacter).filter(
        models.SessionCharacter.character_id == inventory_item.character_id
    ).first()

    if not active_participant:
        # If the character is not active in a session, they can't use an item.
        raise HTTPException(status_code=400, detail="Character is not an active participant in a session.")

    # Get necessary IDs
    actor_id = active_participant.id
    session_id = active_participant.session_id
    
    # 2. Decrement quantity and handle deletion
    inventory_item.quantity -= 1
    
    if inventory_item.quantity <= 0:
        db.delete(inventory_item)
    else:
        db.add(inventory_item)
    
    log_details = {
        "action": "Used Item",
        "character_name": inventory_item.character.name,
        "item_name": inventory_item.item.puranic_name
    }

    # 3. Execute the Linked Ability (NEW CRITICAL LOGIC)
    if ability_id_to_use:
        # Query the ability directly to get its name for logging
        triggered_ability = db.query(models.Ability).filter(
            models.Ability.id == ability_id_to_use
        ).first()
        
        if not triggered_ability:
             db.rollback() 
             raise HTTPException(status_code=404, detail=f"Linked Ability ID {ability_id_to_use} not found.")

        # Create the ability request (targets SELF for healing potions)
        request = AbilityExecutionRequest(
            actor_id=actor_id,
            ability_id=ability_id_to_use,
            primary_target=TargetInfo(participant_id=actor_id) 
        )
        
        # Initialize and execute the ability system
        ability_system = AbilitySystem(db, session_id=session_id)
        result = ability_system.execute_ability(request)
        
        if not result.success:
            # Item was consumed, but ability failed.
            log_details["ability_failure"] = f"{triggered_ability.name} failed: {result.message}"
        else:
            # Log all events generated by the ability (e.g., 'heal' event)
            for log_detail in result.log_events:
                event_type = log_detail.pop("event_type", "ability_effect")
                log_event(
                    db, 
                    session_id, 
                    event_type,
                    actor_id=actor_id,
                    target_id=actor_id,
                    details=log_detail
                )
            
            log_details["ability_success"] = triggered_ability.name
            
        # Commit any pending log entries and session changes from the ability system
        db.commit() 
        
    # 4. Log and Broadcast 
    log_event(db, session_id, 'item_use', details=log_details)
    await manager.broadcast_session_state(session_id, db)
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))

    return {"message": f"{inventory_item.item.puranic_name} was used."}

@app.post("/sessions/{session_id}/environmental_objects", response_model=EnvironmentalObjectSchema)
async def create_environmental_object(
    session_id: int,
    obj_data: EnvironmentalObjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    GM creates an environmental object in the session.
    If has_sections=True, automatically generates sections.
    """
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    new_obj = models.EnvironmentalObject(
        session_id=session_id,
        name=obj_data.name,
        object_type=obj_data.object_type,
        description=obj_data.description,
        icon_url=obj_data.icon_url,
        grid_positions=obj_data.grid_positions,
        has_sections=obj_data.has_sections,
        total_sections=obj_data.total_sections,
        current_integrity=obj_data.max_integrity,
        max_integrity=obj_data.max_integrity,
        critical_threshold=obj_data.critical_threshold,
        evasion_dc=obj_data.evasion_dc,
        armor_value=obj_data.armor_value,
        camp_metadata=obj_data.camp_metadata
    )
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    
    # If sectioned, create sections
    if obj_data.has_sections and obj_data.total_sections > 0:
        section_integrity = obj_data.max_integrity // obj_data.total_sections
        
        for i in range(obj_data.total_sections):
            section = models.EnvironmentalObjectSection(
                parent_id=new_obj.id,
                section_name=f"{obj_data.name} - Section {i+1}",
                section_index=i,
                grid_positions=[],  # GM can configure later
                current_integrity=section_integrity,
                max_integrity=section_integrity,
                evasion_dc=obj_data.evasion_dc,
                armor_value=obj_data.armor_value
            )
            db.add(section)
        db.commit()
        db.refresh(new_obj)
    
    log_event(db, session_id, 'env_object_created', details={
        "object_name": new_obj.name,
        "object_type": new_obj.object_type
    })
    
    background_tasks.add_task(manager.broadcast_session_state, session_id, db)
    
    return new_obj


@app.get("/sessions/{session_id}/environmental_objects", response_model=List[EnvironmentalObjectSchema])
def get_environmental_objects(session_id: int, db: Session = Depends(get_db)):
    """Get all environmental objects in a session"""
    objects = db.query(models.EnvironmentalObject).filter(
        models.EnvironmentalObject.session_id == session_id
    ).all()
    return objects


@app.patch("/sessions/{session_id}/environmental_objects/{object_id}/damage")
async def damage_environmental_object(
    session_id: int,
    object_id: int,
    damage_request: DamageEnvironmentalObjectRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Damage an environmental object or specific section.
    Handles armor reduction, critical thresholds, destruction.
    """
    env_obj = db.query(models.EnvironmentalObject).filter(
        models.EnvironmentalObject.id == object_id,
        models.EnvironmentalObject.session_id == session_id
    ).first()
    
    if not env_obj:
        raise HTTPException(status_code=404, detail="Environmental object not found")
    
    damage_amount = damage_request.damage
    section_id = damage_request.section_id
    
    # Apply armor reduction
    final_damage = max(0, damage_amount - env_obj.armor_value)
    
    # Damage specific section or whole object
    if section_id:
        section = db.query(models.EnvironmentalObjectSection).filter(
            models.EnvironmentalObjectSection.id == section_id
        ).first()
        
        if section:
            section.current_integrity = max(0, section.current_integrity - final_damage)
            
            if section.current_integrity == 0 and not section.is_destroyed:
                section.is_destroyed = True
                log_event(db, session_id, 'env_section_destroyed', details={
                    "object_name": env_obj.name,
                    "section_name": section.section_name,
                    "damage": final_damage
                })
            
            db.add(section)
            
            # Recalculate overall object integrity
            total_integrity = sum(s.current_integrity for s in env_obj.sections)
            env_obj.current_integrity = total_integrity
    else:
        # Damage whole object
        env_obj.current_integrity = max(0, env_obj.current_integrity - final_damage)
        
        if env_obj.current_integrity == 0 and env_obj.is_functional:
            env_obj.is_functional = False
            log_event(db, session_id, 'env_object_destroyed', details={
                "object_name": env_obj.name,
                "damage": final_damage
            })
    
    # Check if object hit critical threshold
    if env_obj.current_integrity <= env_obj.critical_threshold and env_obj.is_functional:
        env_obj.is_functional = False
        log_event(db, session_id, 'env_object_critical_failure', details={
            "object_name": env_obj.name,
            "message": f"{env_obj.name} has critically failed!"
        })
    
    db.add(env_obj)
    db.commit()
    
    await manager.broadcast_session_state(session_id, db)
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))
    
    return {"success": True, "object": EnvironmentalObjectSchema.model_validate(env_obj)}


@app.patch("/sessions/{session_id}/environmental_objects/{object_id}/repair")
async def repair_environmental_object(
    session_id: int,
    object_id: int,
    repair_request: RepairEnvironmentalObjectRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Repair an environmental object"""
    env_obj = db.query(models.EnvironmentalObject).filter(
        models.EnvironmentalObject.id == object_id
    ).first()
    
    if not env_obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    repair_amount = repair_request.repair_amount
    section_id = repair_request.section_id
    
    if section_id:
        section = db.query(models.EnvironmentalObjectSection).filter(
            models.EnvironmentalObjectSection.id == section_id
        ).first()
        if section:
            section.current_integrity = min(
                section.max_integrity,
                section.current_integrity + repair_amount
            )
            if section.current_integrity > 0:
                section.is_destroyed = False
            db.add(section)
    else:
        env_obj.current_integrity = min(
            env_obj.max_integrity,
            env_obj.current_integrity + repair_amount
        )
        if env_obj.current_integrity > env_obj.critical_threshold:
            env_obj.is_functional = True
        db.add(env_obj)
    
    db.commit()
    
    log_event(db, session_id, 'env_object_repaired', details={
        "object_name": env_obj.name,
        "repair_amount": repair_amount
    })
    
    await manager.broadcast_session_state(session_id, db)
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))
    
    return {"success": True, "object": EnvironmentalObjectSchema.model_validate(env_obj)}


@app.delete("/sessions/{session_id}/environmental_objects/{object_id}")
async def delete_environmental_object(
    session_id: int,
    object_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """GM deletes an environmental object"""
    env_obj = db.query(models.EnvironmentalObject).filter(
        models.EnvironmentalObject.id == object_id
    ).first()
    
    if not env_obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    db.delete(env_obj)
    db.commit()
    
    await manager.broadcast_session_state(session_id, db)
    
    return {"success": True}

# ==================================
# CAMPAIGN ENDPOINTS
# ==================================

@app.post("/campaigns", response_model=CampaignSchema)
def create_campaign(campaign_data: CampaignCreate, db: Session = Depends(get_db)):
    """Create a new campaign template"""
    new_campaign = models.Campaign(
        name=campaign_data.name,
        description=campaign_data.description,
        theme=campaign_data.theme,
        recommended_level=campaign_data.recommended_level,
        recommended_party_size=campaign_data.recommended_party_size,
        estimated_duration_minutes=campaign_data.estimated_duration_minutes,
        player_character_ids=campaign_data.player_character_ids,
        npc_character_ids=campaign_data.npc_character_ids,
        enemy_character_ids=campaign_data.enemy_character_ids,
        creator_user_id=campaign_data.creator_user_id,
        is_published=campaign_data.is_published
    )
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)
    return new_campaign


@app.get("/campaigns", response_model=List[CampaignSchema])
def list_campaigns(published_only: bool = False, db: Session = Depends(get_db)):
    """List all campaigns (or only published ones)"""
    query = db.query(models.Campaign).options(joinedload(models.Campaign.scenes))
    if published_only:
        query = query.filter(models.Campaign.is_published == True)
    return query.all()


@app.get("/campaigns/{campaign_id}", response_model=CampaignSchema)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Get a specific campaign with all its details"""
    campaign = db.query(models.Campaign).options(
        joinedload(models.Campaign.scenes)
    ).filter(models.Campaign.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@app.get("/campaigns/{campaign_id}/characters")
def get_campaign_characters(campaign_id: int, db: Session = Depends(get_db)):
    """
    Get all characters associated with a campaign
    Returns separate lists for players, NPCs, and enemies
    """
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Fetch player characters
    player_chars = []
    if campaign.player_character_ids:
        player_chars = db.query(models.Character).filter(
            models.Character.id.in_(campaign.player_character_ids)
        ).all()
    
    # Fetch NPC characters
    npc_chars = []
    if campaign.npc_character_ids:
        npc_chars = db.query(models.Character).filter(
            models.Character.id.in_(campaign.npc_character_ids)
        ).all()
    
    # Fetch enemy characters
    enemy_chars = []
    if campaign.enemy_character_ids:
        enemy_chars = db.query(models.Character).filter(
            models.Character.id.in_(campaign.enemy_character_ids)
        ).all()
    
    return {
        "player_characters": [CharacterSchema.model_validate(c) for c in player_chars],
        "npcs": [CharacterSchema.model_validate(c) for c in npc_chars],
        "enemies": [CharacterSchema.model_validate(c) for c in enemy_chars]
    }


# ==================================
# SCENE ENDPOINTS
# ==================================

@app.post("/scenes", response_model=SceneSchema)
def create_scene(scene_data: SceneCreate, db: Session = Depends(get_db)):
    """Create a new scene for a campaign"""
    # Verify campaign exists
    campaign = db.query(models.Campaign).filter(models.Campaign.id == scene_data.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    new_scene = models.Scene(
        campaign_id=scene_data.campaign_id,
        name=scene_data.name,
        description=scene_data.description,
        scene_order=scene_data.scene_order,
        background_url=scene_data.background_url,
        cards=scene_data.cards
    )
    db.add(new_scene)
    db.commit()
    db.refresh(new_scene)
    return new_scene


@app.get("/campaigns/{campaign_id}/scenes", response_model=List[SceneSchema])
def get_campaign_scenes(campaign_id: int, db: Session = Depends(get_db)):
    """Get all scenes for a campaign, ordered by scene_order"""
    scenes = db.query(models.Scene).filter(
        models.Scene.campaign_id == campaign_id
    ).order_by(models.Scene.scene_order).all()
    return scenes


@app.patch("/scenes/{scene_id}", response_model=SceneSchema)
def update_scene(scene_id: int, scene_data: SceneCreate, db: Session = Depends(get_db)):
    """Update a scene's details"""
    scene = db.query(models.Scene).filter(models.Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    scene.name = scene_data.name
    scene.description = scene_data.description
    scene.scene_order = scene_data.scene_order
    scene.background_url = scene_data.background_url
    scene.cards = scene_data.cards
    
    db.commit()
    db.refresh(scene)
    return scene


# ==================================
# SESSION-CAMPAIGN INTEGRATION
# ==================================

@app.post("/sessions/{session_id}/select_campaign")
async def select_campaign_for_session(
    session_id: int,
    campaign_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Attach a campaign to a session
    This makes campaign characters available for selection
    """
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    session.campaign_id = campaign_id
    session.campaign_name = campaign.name  # Update session name to match campaign
    db.commit()
    
    await manager.broadcast_session_state(session_id, db)
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))
    return {"message": "Campaign selected successfully", "campaign_id": campaign_id}


@app.post("/sessions/{session_id}/select_character")
async def select_character_in_lobby(
    session_id: int,
    request: CharacterSelectionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Player selects a character in the lobby (before game starts)
    Updates character_selections in session
    """
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.current_mode != 'lobby':
        raise HTTPException(status_code=400, detail="Can only select characters in lobby")
    
    # Check if character is already selected by someone else
    if request.character_id in session.character_selections.values():
        raise HTTPException(status_code=400, detail="Character already selected by another player")
    
    # Check if this player already has a selection
    if request.player_id in session.character_selections:
        # They're changing their selection
        pass
    
    # Update selections
    selections = session.character_selections.copy() if session.character_selections else {}
    selections[str(request.player_id)] = request.character_id  # JSON keys must be strings
    session.character_selections = selections
    character = db.query(models.Character).filter(models.Character.id == request.character_id).first()
    player = db.query(models.User).filter(models.User.id == request.player_id).first()
    if character and player:
        log_entry = models.GameLogEntry(
            session_id=session_id,
            event_type='character_selection',
            details={
                'player_name': player.display_name,
                'character_name': character.name
            }
        )
    db.add(log_entry)

    db.commit()
    await manager.broadcast_session_state(session_id, db)
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))
    
    return {"message": "Character selected successfully"}


@app.post("/sessions/{session_id}/deselect_character")
async def deselect_character_in_lobby(
    session_id: int,
    request: CharacterDeselectionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Player deselects their character in the lobby"""
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.current_mode != 'lobby':
        raise HTTPException(status_code=400, detail="Can only deselect characters in lobby")
    
    # Remove player's selection
    selections = session.character_selections.copy() if session.character_selections else {}
    selections.pop(str(request.player_id), None)
    session.character_selections = selections
    character = db.query(models.Character).filter(models.Character.id == request.character_id).first()
    player = db.query(models.User).filter(models.User.id == request.player_id).first()
    if character and player:
        log_entry = models.GameLogEntry(
            session_id=session_id,
            event_type='character_selection',
            details={
                'player_name': player.display_name,
                'character_name': character.name
            }
        )
    db.add(log_entry)

    db.commit()
    await manager.broadcast_session_state(session_id, db)
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))
    
    
    return {"message": "Character deselected successfully"}


@app.post("/sessions/{session_id}/start_with_campaign")
async def start_session_with_campaign(
    session_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    GM starts the session - creates SessionCharacters from selected characters
    """
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.current_mode != 'lobby':
        raise HTTPException(status_code=400, detail="Session already started")
    
    if not session.character_selections:
        raise HTTPException(status_code=400, detail="No characters selected yet")
    
    # Create SessionCharacters for each selected character
    for player_id_str, character_id in session.character_selections.items():
        player_id = int(player_id_str)
        
        # Get the character template
        character = db.query(models.Character).options(
            joinedload(models.Character.race),
            joinedload(models.Character.char_class)
        ).filter(models.Character.id == character_id).first()
        
        if not character:
            continue
        
        # Get character's abilities
        ability_links = db.query(models.CharacterAbility).filter(
            models.CharacterAbility.character_id == character_id
        ).all()
        ability_ids = [link.ability_id for link in ability_links]
        
        # Calculate max resources using CharacterSchema
        char_schema = CharacterSchema.model_validate(character)
        
        # Create SessionCharacter
        session_char = models.SessionCharacter(
            session_id=session_id,
            character_id=character_id,
            player_id=player_id,
            level=character.level,
            learned_abilities=ability_ids,
            npc_type=None,  # Player characters have no npc_type
            current_prana=char_schema.max_prana,
            current_tapas=char_schema.max_tapas,
            current_maya=char_schema.max_maya,
            remaining_speed=char_schema.movement_speed
        )
        db.add(session_char)
    
    # Update session mode
    session.current_mode = 'exploration'
    db.commit()
    
    await manager.broadcast_session_state(session_id, db)
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))
    return {"message": "Session started successfully"}


# ==================================
# SCENE BROADCASTING
# ==================================

@app.post("/sessions/{session_id}/set_active_scene")
async def set_active_scene(
    session_id: int,
    scene_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """GM sets the active scene that players see"""
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify scene exists and belongs to session's campaign
    if scene_id:
        scene = db.query(models.Scene).filter(models.Scene.id == scene_id).first()
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        if session.campaign_id and scene.campaign_id != session.campaign_id:
            raise HTTPException(status_code=400, detail="Scene does not belong to this campaign")
    
    session.active_scene_id = scene_id
    db.commit()
    
    await manager.broadcast_session_state(session_id, db)
    await manager.broadcast_json(session_id, json.dumps({"type": "new_log_entry"}))
    return {"message": "Active scene updated"}


@app.get("/sessions/{session_id}/active_scene", response_model=SceneSchema)
def get_active_scene(session_id: int, db: Session = Depends(get_db)):
    """Get the currently active scene for a session"""
    session = db.query(models.GameSession).filter(models.GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.active_scene_id:
        raise HTTPException(status_code=404, detail="No active scene")
    
    scene = db.query(models.Scene).filter(models.Scene.id == session.active_scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    return scene






