"""
File: db_models.py

This file sets up the SQLAlchemy table ORM objects. This file is imported by any file
needing access to one or more of the defined table ORM objects below.
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

from cogs.twitch.database.db_engine_session_init import engine

Base = declarative_base()


class FitnessUser(Base):
    __tablename__ = 'Fitness Users'
    user = Column(String, primary_key=True)
    gender = Column(String)
    height = Column(Integer)
    weight = Column(Integer)
    goal_weight = Column(Integer)
    bench = Column(Integer)
    squat = Column(Integer)
    deadlift = Column(Integer)
    ohp = Column(Integer)
    mile = Column(Integer)
    rowing = Column(Integer)
    burpees = Column(Integer)
    plank = Column(String)


Base.metadata.create_all(engine)
