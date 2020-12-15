from datetime import datetime
from urllib import parse

from sqlalchemy import desc, asc

from database.db_models import WarcraftCharacter
from database.db_engine_session_initialization import Session


class WarcraftCharacterInterface:
    @classmethod
    async def update_character(cls, raiderio_data, rank=None):
        """
        Updates an existing character if found, otherwise creates a new entry.

        :param raiderio_data: A list of character data returned by the Raider.io API
        :param rank: Passed in during auto crawl of guilds from Blizzard API
        :return: None
        """
        session = Session()
        name = raiderio_data['name'].lower()
        realm = raiderio_data['realm'].replace(' ', '-').lower()
        region = raiderio_data['region'].lower()
        character = session.query(WarcraftCharacter).filter_by(
            name=name, realm=realm, region=region).first()
        if character is None:
            character = WarcraftCharacter()
            character.name = name
            character.realm = realm
            character.region = region
            character.m_plus_prev_weekly_high = 0
        if raiderio_data['guild'] is not None:
            character.guild = raiderio_data['guild']['name'].replace(' ', '-').lower()
        else:
            character.guild = ''
        if rank is not None:
            character.guild_rank = rank
        else:
            character.rank = None
        character.char_class = raiderio_data['class'].lower()
        character.ilvl = raiderio_data['gear']['item_level_equipped']
        character.m_plus_score_overall = raiderio_data['mythic_plus_scores_by_season'][0]['scores']['all']
        character.m_plus_rank_overall = raiderio_data['mythic_plus_ranks']['overall']['realm']
        character.m_plus_rank_class = raiderio_data['mythic_plus_ranks']['class']['realm']
        if len(raiderio_data['mythic_plus_weekly_highest_level_runs']) > 0:
            character.m_plus_weekly_high = raiderio_data['mythic_plus_weekly_highest_level_runs'][0]['mythic_level']
        else:
            character.m_plus_weekly_high = 0
        if len(raiderio_data['mythic_plus_previous_weekly_highest_level_runs']) > 0:
            character.m_plus_prev_weekly_high = raiderio_data['mythic_plus_previous_weekly_highest_level_runs'][0]['mythic_level']
        else:
            character.m_plus_prev_weekly_high = 0
        character.last_updated = datetime.now()
        # Expansion "Feature" TODO: FILL THIS IN WHEN API UPDATES!
        character.covenant = ""
        character.renown = ""
        try:
            session.add(character)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f'An error occurred while updating a character:\n'
                  f'{name.title()} on {realm.title()}-{region.title()}\n'
                  f'ERROR: {e}')
        finally:
            session.close()

    @classmethod
    async def remove_character(cls, character):
        """
        Removes character from database.

        :param character: a WarcraftCharacter object returned by get_character()
        :return: None
        """
        session = Session()
        try:
            session.delete(character)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f'An error occurred while attempting to delete a character:\n{e}')
        finally:
            session.close()

    @classmethod
    async def get_character(cls, name, realm, region):
        """
        Retrieves a character from the database. Presumes the character was
        found to exist already.

        :param name: Character name
        :param realm: Realm name, spaces are auto-sanitized
        :param region: 2-letter abbreviation for region - US, EU, RU, KR
        :return: A WarcraftCharacter object
        """
        session = Session()
        character = session.query(WarcraftCharacter).filter_by(
            name=name.lower(), realm=realm.lower().replace(' ', '-'),
            region=region.lower()).first()
        session.close()
        return character

    @classmethod
    async def get_all_characters(cls):
        """
        Returns all characters found in the database.

        :return: A list of WarcraftCharacter objects
        """
        session = Session()
        characters = session.query(WarcraftCharacter).all()
        session.close()
        return characters

    @classmethod
    async def get_guild_members(cls, guild, realm, region, ranks=None):
        """
        Returns all members belonging to the specified guild.

        :param guild: Guild name, spaces are auto-sanitized
        :param realm: Realm name, spaces are auto-sanitized
        :param region: 2-letter abbreviation for region - US, EU, RU, KR
        :param ranks: A list of numerical ranks to return filtered guild members
        :return: A list of WarcraftCharacter objects
        """
        session = Session()
        if ranks is None:
            guild_members = session.query(WarcraftCharacter).filter_by(
                guild=guild.lower().replace(' ', '-'), realm=realm.lower().replace(' ', '-'),
                region=region.lower()).all()
            session.close()
            return guild_members
        else:
            guild_members = session.query(WarcraftCharacter).filter_by(
                guild=guild.lower().replace(' ', '-'), realm=realm.lower().replace(' ', '-'),
                region=region.lower()).filter(
                WarcraftCharacter.guild_rank.in_(ranks)).all()
            session.close()
            return guild_members

    @classmethod
    async def get_guilds(cls):
        """
        Gets all guilds currently in the database.

        :return: A list of guilds, their realms, and their regions
        """
        session = Session()
        guilds = session.query(
            WarcraftCharacter.guild, WarcraftCharacter.realm, WarcraftCharacter.region
        ).distinct()
        session.close()
        return guilds

    @classmethod
    async def addkey(cls, character, key_name, key_level):
        """
        Adds mythic+ key info for a character.

        :param character: Name of character
        :param key_name: Full dungeon name
        :param key_level: Level of the key as int
        :return: None
        """
        session = Session()
        character.m_plus_key = key_name
        character.m_plus_key_level = key_level
        try:
            session.add(character)
            session.commit()
        except Exception as e:
            print('An error occurred when adding a key:\n{e}')
            session.rollback()
        finally:
            session.close()

    @classmethod
    async def removekey(cls, character):
        """
        Removes a mythic+ key for a character.

        :param character: Name of character
        :return: None
        """
        session = Session()
        character.m_plus_key = None
        character.m_plus_key_level = None
        try:
            session.add(character)
            session.commit()
        except Exception as e:
            print('An error occurred when removing a key:\n{e}')
            session.rollback()
        finally:
            session.close()

    @classmethod
    async def get_guild_keys(cls, guild, realm, region):
        """
        Gets all the guild members that have a mythic+ key for the week.

        :param guild: Name of guild, spaces are auto-sanitized
        :param realm: Realm name, spaces are auto-sanitized
        :param region: 2-letter abbreviation for region - US, EU, RU, KR
        :return: A list of WarcraftCharacter objects
        """
        session = Session()
        results = session.query(WarcraftCharacter).filter_by(
            guild=guild.lower().replace(' ', '-'), realm=realm.lower().replace(' ', '-'),
            region=region.lower()).filter(
            WarcraftCharacter.m_plus_key_level > 1).order_by(
            desc(WarcraftCharacter.m_plus_key_level)).order_by(
            asc(WarcraftCharacter.name)).all()
        session.close()
        return results

    @classmethod
    async def reset_keys(cls):
        """
        Resets mythic+ keys for the week.

        :return: None
        """
        session = Session()
        characters = session.query(WarcraftCharacter).filter(
            WarcraftCharacter.m_plus_key is not None).all()
        for char in characters:
            char.m_plus_key = None
            char.m_plus_key_level = None
            session.add(char)
        success = False
        try:
            session.commit()
            success = True
        except Exception as e:
            print(f'An error occurred when resetting keys.\n{e}')
            session.rollback()
        finally:
            session.close()
            return success
