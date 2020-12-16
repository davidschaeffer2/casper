"""
File: db_models.py

This file sets up the SQLAlchemy table ORM objects. This file is imported by any file
needing access to one or more of the defined table ORM objects below.
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

from cogs.warcraft.database.db_engine_session_init import engine

Base = declarative_base()


class WarcraftCharacter(Base):
    __tablename__ = 'Warcraft Characters'
    name = Column(String, primary_key=True)
    realm = Column(String, primary_key=True)
    region = Column(String)
    guild = Column(String)
    guild_rank = Column(Integer)
    char_class = Column(String)
    ilvl = Column(Integer)
    m_plus_key = Column(String)
    m_plus_key_level = Column(Integer)
    m_plus_score_overall = Column(Integer)
    m_plus_rank_overall = Column(Integer)
    m_plus_rank_class = Column(Integer)
    m_plus_weekly_high = Column(Integer)
    m_plus_prev_weekly_high = Column(Integer)
    last_updated = Column(DateTime)
    # Expansion "Feature"
    covenant = Column(String)
    renown = Column(String)


class WarcraftCharacterWeeklyRun(Base):
    __tablename__ = 'Warcraft Character Weekly Runs'
    id = Column(Integer, autoincrement=True, primary_key=True)
    run_id = Column(String)
    character_name = Column(String)
    dungeon_name = Column(String)
    dungeon_level = Column(Integer)


Base.metadata.create_all(engine)
