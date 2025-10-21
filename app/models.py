# app/models.py

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.types import JSON, DateTime
from sqlalchemy.sql import func
import os 
from dotenv import load_dotenv 

load_dotenv() 

# --- Database Setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Core Models ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String, index=True)
    current_session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=True)
    characters = relationship("Character", back_populates="owner")

class Ability(Base):
    __tablename__ = "abilities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String, nullable=True)
    action_type = Column(String)
    resource_cost = Column(Integer, default=0)
    resource_type = Column(String, nullable=True)
    to_hit_attribute = Column(String, nullable=True)
    effect_type = Column(String)
    damage_dice = Column(String, nullable=True)
    damage_attribute = Column(String, nullable=True)
    status_effect = Column(String, nullable=True)
    range = Column(Integer, default=1)

class Race(Base):
    __tablename__ = "races"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    
    # --- Racial Attribute Modifiers ---
    # Storing these as separate columns for clarity and performance.
    bala_mod = Column(Integer, default=0)
    dakshata_mod = Column(Integer, default=0)
    dhriti_mod = Column(Integer, default=0)
    buddhi_mod = Column(Integer, default=0)
    prajna_mod = Column(Integer, default=0)
    samkalpa_mod = Column(Integer, default=0)
    
    # This relationship will link Races back to Characters.
    characters = relationship("Character", back_populates="race")

class Char_Class(Base):
    __tablename__ = "char_classes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    primary_attribute = Column(String) # e.g., "Bala" or "Buddhi"
    
    # --- Base Attribute Scores ---
    # This is the starting point for a character's attributes, 
    # determined by their class.
    base_bala = Column(Integer, default=10)
    base_dakshata = Column(Integer, default=10)
    base_dhriti = Column(Integer, default=10)
    base_buddhi = Column(Integer, default=10)
    base_prajna = Column(Integer, default=10)
    base_samkalpa = Column(Integer, default=10)
    default_abilities = Column(JSON, default=list)
    # This relationship will link Classes back to Characters.
    characters = relationship("Character", back_populates="char_class")
    subclasses = relationship("Subclass", back_populates="base_class")

class Subclass(Base):
    __tablename__ = "subclasses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)

    # --- Subclass-Specific Rules ---
    level_requirement = Column(Integer, default=3)
    tapas_bonus = Column(Integer, default=0)
    maya_bonus = Column(Integer, default=0)
    
    # --- Foreign Key to the Base Class ---
    base_class_id = Column(Integer, ForeignKey('char_classes.id'))

    # --- Relationships ---
    base_class = relationship("Char_Class", back_populates="subclasses")

class Character(Base):
    __tablename__ = "characters"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    race_id = Column(Integer, ForeignKey("races.id"))
    char_class_id = Column(Integer, ForeignKey("char_classes.id"))
    owner = relationship("User", back_populates="characters")
    race = relationship("Race", back_populates="characters")
    char_class = relationship("Char_Class", back_populates="characters")
    subclass_id = Column(Integer, ForeignKey('subclasses.id'), nullable=True)
    subclass = relationship("Subclass")
    level = Column(Integer, default=1)
    unlocked_loka_attunement = Column(String, nullable=True)
    movement_speed = Column(Integer, default=6)
    session_characters = relationship("SessionCharacter", back_populates="character")

# --- Junction / Link Tables ---
class CharacterAbility(Base):
    __tablename__ = "character_abilities"
    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"))
    ability_id = Column(Integer, ForeignKey("abilities.id"))

class SessionCharacter(Base):
    __tablename__ = "session_characters"
    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"))
    session_id = Column(Integer, ForeignKey("game_sessions.id"))
    player_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    current_prana = Column(Integer)
    current_tapas = Column(Integer)
    current_maya = Column(Integer)
    remaining_speed = Column(Integer, default=0)
    status = Column(String, default="active") # e.g., 'active', 'downed'
    x_pos = Column(Integer, nullable=True)
    y_pos = Column(Integer, nullable=True)
    character = relationship("Character")
    session = relationship("GameSession", back_populates="participants")

class GameSession(Base):
    __tablename__ = "game_sessions"
    id = Column(Integer, primary_key=True, index=True)
    gm_id = Column(Integer, ForeignKey("users.id"))
    campaign_name = Column(String)
    current_mode = Column(String, default='lobby')
    active_loka_resonance = Column(String, default='none')
    turn_order = Column(JSON, default=[])
    current_turn_index = Column(Integer, default=0)
    access_code = Column(String, unique=True, index=True, nullable=True)
    participants = relationship("SessionCharacter", back_populates="session")
    log_entries = relationship("GameLogEntry", back_populates="session", cascade="all, delete-orphan")
    skill_checks = relationship("SkillCheck", back_populates="session", cascade="all, delete-orphan")

class GameLogEntry(Base):
    __tablename__ = "game_log_entries"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String, nullable=False) # e.g., 'player_join', 'attack_roll'
    actor_id = Column(Integer, ForeignKey("session_characters.id"), nullable=True)
    target_id = Column(Integer, ForeignKey("session_characters.id"), nullable=True)
    details = Column(JSON, nullable=True) 
    session = relationship("GameSession", back_populates="log_entries")

class SkillCheck(Base):
    __tablename__ = "skill_checks"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    participant_id = Column(Integer, ForeignKey("session_characters.id"), nullable=False)
    
    check_type = Column(String, nullable=False) # e.g., "dakshata", "moha"
    dc = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, default="pending") # Can be 'pending' -> 'completed'

    participant = relationship("SessionCharacter")
    session = relationship("GameSession")