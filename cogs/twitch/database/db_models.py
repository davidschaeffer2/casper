"""
File: db_models.py

This file sets up the SQLAlchemy table ORM objects. This file is imported by any file
needing access to one or more of the defined table ORM objects below.
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

from cogs.twitch.database.db_engine_session_init import engine

Base = declarative_base()


class TwitchStream(Base):
    __tablename__ = 'Twitch Streams'
    twitch_name = Column(String, primary_key=True)
    is_live = Column(Boolean)


Base.metadata.create_all(engine)
