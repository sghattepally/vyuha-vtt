# app/models.py

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.types import JSON
import os # <--- ADD THIS IMPORT
from dotenv import load_dotenv # <--- ADD THIS IMPORT

load_dotenv() # <--- ADD THIS LINE to load the .env file

# --- Database Setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Core Models ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)

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

class Character(Base):
    __tablename__ = "characters"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User")
    name = Column(String, index=True)
    race = Column(String)
    character_class = Column(String)
    bala = Column(Integer, default=10)
    dakshata = Column(Integer, default=10)
    dhriti = Column(Integer, default=10)
    buddhi = Column(Integer, default=10)
    prajna = Column(Integer, default=10)
    samkalpa = Column(Integer, default=10)
    max_prana = Column(Integer, default=10)
    max_tapas = Column(Integer, default=4)
    max_maya = Column(Integer, default=4)
    level = Column(Integer, default=1)
    unlocked_loka_attunement = Column(String, nullable=True)
    movement_speed = Column(Integer, default=6)

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
    current_mode = Column(String, default='exploration')
    active_loka_resonance = Column(String, default='none')
    turn_order = Column(JSON, default=[])
    current_turn_index = Column(Integer, default=0)
    log = Column(JSON, default=[])
    participants = relationship("SessionCharacter", back_populates="session")