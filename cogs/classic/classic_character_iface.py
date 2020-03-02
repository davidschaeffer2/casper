from database.db_models import ClassicCharacter
from database.db_engine_session_initialization import Session


class ClassicCharacterInterface:
    @classmethod
    async def update_character(cls, name, race, class_, realm, region):
        session = Session()
        character = session.query(ClassicCharacter).filter_by(
            name=name.lower(), realm=realm.replace('', ''), region=region).first()
        if character is None:
            character = ClassicCharacter()
            character.name = name.lower()
            character.realm = realm
            character.region = region
        character.char_class = class_
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
    async def character_exists(cls, name, realm, region):
        session = Session()
        character = session.query(ClassicCharacter).filter_by(
            name=name.lower(), realm=realm.lower(), region=region.lower()).first()
        if character is None:
            return False
        return True

    @classmethod
    async def get_character(cls, name, realm, region):
        """
        Retrieves a character from the database.
        :param name:
        :param realm:
        :param region:
        :return:
        """
        session = Session()
        character = session.query(ClassicCharacter).filter_by(
            name=name.lower(), realm=realm.lower(), region=region.lower()).first()
        session.close()
        return character

    @classmethod
    async def get_guild_members(cls, guild, realm, region, ranks=None):
        session = Session()
        if ranks is None:
            guild_members = session.query(ClassicCharacter).filter_by(
                guild=guild, realm=realm, region=region).all()
            session.close()
            return guild_members
        else:
            guild_members = session.query(ClassicCharacter).filter_by(
                guild=guild, realm=realm, region=region).filter(
                ClassicCharacter.guild_rank.in_(ranks)).all()
            session.close()
            return guild_members
