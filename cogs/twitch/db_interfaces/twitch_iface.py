from sqlalchemy import desc, asc
from typing import List

from cogs.twitch.database.db_models import TwitchStream
from cogs.twitch.database.db_engine_session_init import Session


class TwitchDBInterface:
    @classmethod
    async def add_channel(cls, **kwargs) -> bool:
        channel = TwitchStream(
            username=kwargs.get('username'),
            is_live=kwargs.get('is_live', False)
        )
        success = False
        session = Session()
        try:
            session.add(channel)
            session.commit()
            success = True
        except Exception as e:
            session.rollback()
            print(f'An error occurred while updating the Twitch channel for:\n'
                  f'{kwargs.get("username")}\n'
                  f'ERROR: {e}')
        finally:
            session.close()
            return success

    @classmethod
    async def remove_channel(cls, username):
        session = Session()
        channel = session.query(TwitchStream).filter_by(username=username).first()
        if channel is not None:
            success = False
            try:
                session.delete(channel)
                session.commit()
                success = True
            except Exception as e:
                session.rollback()
                print(f'An error occurred while updating the Twitch channel for:\n'
                      f'{username}\n'
                      f'ERROR: {e}')
            finally:
                session.close()
                return success

    @classmethod
    async def get_all_channels(cls) -> List['TwitchStream']:
        session = Session()
        channels = session.query(TwitchStream).all()
        session.close()
        return channels

    @classmethod
    async def set_is_live(cls, username: str, is_live: bool) -> bool:
        session = Session()
        channel = session.query(TwitchStream).filter_by(
            username=username.lower()).first()
        channel.is_live = is_live
        success = False
        try:
            session.add(channel)
            session.commit()
            success = True
        except Exception as e:
            session.rollback()
            print(f'An error occurred when updating stream status for {username}:\n'
                  f'ERROR: {e}')
        finally:
            session.close()
            return success
