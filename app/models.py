# app/models.py

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# --- Database Setup ---
DATABASE_URL = "sqlite:///./vyuha.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- The User Model ---
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)

# --- The SessionCharacter Model ---
# This table links a Character to a GameSession and stores their state *within that session*.
class SessionCharacter(Base):
    __tablename__ = "session_characters"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys to link everything
    character_id = Column(Integer, ForeignKey("characters.id"))
    session_id = Column(Integer, ForeignKey("game_sessions.id"))

    # Session-specific, temporary stats
    current_prana = Column(Integer)
    current_tapas = Column(Integer)
    current_maya = Column(Integer)
    x_pos = Column(Integer, nullable=True)
    y_pos = Column(Integer, nullable=True)

    # SQLAlchemy relationships to easily access the linked data
    character = relationship("Character")
    session = relationship("GameSession", back_populates="participants")


# --- The GameSession Model ---
class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    gm_id = Column(Integer, ForeignKey("users.id")) 
    campaign_name = Column(String)
    current_mode = Column(String, default='exploration')
    active_loka_resonance = Column(String, default='none')
    
    # This relationship creates a convenient way to get all participants in a session
    participants = relationship("SessionCharacter", back_populates="session")


# --- The Character Model (now a pure template) ---
class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User")
    name = Column(String, index=True)
    race = Column(String)
    character_class = Column(String)

    # Core Attributes
    bala = Column(Integer, default=10)
    dakshata = Column(Integer, default=10)
    dhriti = Column(Integer, default=10)
    buddhi = Column(Integer, default=10)
    prajna = Column(Integer, default=10)
    samkalpa = Column(Integer, default=10)

    # Maximum Resource Stats (the 'current' values are gone)
    max_prana = Column(Integer, default=10)
    max_tapas = Column(Integer, default=4)
    max_maya = Column(Integer, default=4)

    # Progression
    level = Column(Integer, default=1)
    unlocked_loka_attunement = Column(String, nullable=True)

# --- The Ability Model  ---
class Ability(Base):
    __tablename__ = "abilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String, nullable=True) # Good to have for the UI later

    # --- The "Rules Engine" Fields ---
    action_type = Column(String) # e.g., 'MELEE_ATTACK', 'MANTRA_EFFECT', 'ASTRA_SHOT'
    resource_cost = Column(Integer, default=0)
    resource_type = Column(String, nullable=True) # 'Tapas' or 'Māyā'
    
    # Rules for hitting
    to_hit_attribute = Column(String, nullable=True) # 'bala', 'dakshata', 'buddhi'

    # Rules for the effect
    effect_type = Column(String) # 'DAMAGE', 'HEALING', 'STATUS_EFFECT'
    damage_dice = Column(String, nullable=True) # e.g., '1d8', '2d6'
    damage_attribute = Column(String, nullable=True) # e.g., 'bala', 'buddhi', 'none'
    status_effect = Column(String, nullable=True) # e.g., 'Restrained', 'Staggered'


# --- CharacterAbility Link Table ---
class CharacterAbility(Base):
    __tablename__ = "character_abilities"
    
    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"))
    ability_id = Column(Integer, ForeignKey("abilities.id"))
