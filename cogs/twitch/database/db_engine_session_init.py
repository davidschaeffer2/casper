"""
File: db_engine_session_initialization.py

This file sets up the SQLAlchemy engine and Session objects. This file is imported by the
db_models.py file for engine use to create the necessary tables and by any file needing
access to the Session object for database transactions.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///cogs/twitch/database/database.db',
                       echo=False)
Session = sessionmaker(bind=engine)
