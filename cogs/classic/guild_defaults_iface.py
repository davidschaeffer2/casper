from database.db_models import GuildDefaults
from database.db_engine_session_initialization import Session


class GuildDefaultsInterface:
    @classmethod
    async def update_guild_defaults(cls, guild_id, guild_name, warcraft_guild, realm, region):
        session = Session()
        guild = session.query(GuildDefaults).filter_by(
            guild_id=guild_id).first()
        success = True
        if guild is None:
            guild = GuildDefaults()
            guild.guild_id = guild_id
        guild.guild_name = guild_name.lower()
        guild.classic_guild = warcraft_guild.lower()
        guild.classic_realm = realm.lower()
        guild.classic_region = region.lower()
        try:
            session.add(guild)
            session.commit()
        except Exception as e:
            session.rollback()
            success = False
            print(f'An error occurred while updating a guild:\n'
                  f'Guild: {guild_name}\n'
                  f'ERROR: {e}')
        finally:
            session.close()
            return success

    @classmethod
    async def get_guild_defaults(cls, guild_id):
        """
        Fetches defaults for a given guild
        :param guild_id:
        :return: The guild defaults if they exist, else none
        """
        session = Session()
        defaults = session.query(GuildDefaults).filter_by(
            guild_id=guild_id).first()
        session.close()
        return defaults
