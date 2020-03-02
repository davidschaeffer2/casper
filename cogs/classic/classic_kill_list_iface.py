from database.db_models import ClassicKillList
from database.db_engine_session_initialization import Session


class ClassicKillListInterface:
    @classmethod
    async def update_character(cls, ctx, name, race, char_class, level, location,
                               bounty, infraction):
        session = Session()
        character = session.query(ClassicKillList).filter_by(
            name=name.lower(), guild=ctx.guild.id).first()
        if character is None:
            character = ClassicKillList()
            character.name = name.lower()
            character.guild = ctx.guild.id
        if race is None:
            character.race = ''
            character.char_class = ''
            character.level = ''
            character.infraction = ''
            character.location = ''
            character.bounty = ''
        else:
            character.race = race.lower()
            character.char_class = char_class.lower()
            character.level = level
            character.infraction = infraction
            character.location = location.lower()
            character.bounty = bounty
        try:
            session.add(character)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f'An error occurred while updating a character:\n'
                  f'{name.title()} on {ctx.guild.name.title()}\n'
                  f'ERROR: {e}')
        finally:
            session.close()

    @classmethod
    async def remove_character(cls, ctx, name):
        session = Session()
        character = session.query(ClassicKillList).filter_by(
            guild=ctx.guild.id, name=name.lower()).first()
        try:
            session.delete(character)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f'An error occurred while deleting a character:\n'
                  f'{name.title()} on {ctx.guild.name.title()}\n'
                  f'ERROR: {e}')
        finally:
            session.close()

    @classmethod
    async def get_kos_list(cls, ctx):
        session = Session()
        characters = session.query(ClassicKillList).filter_by(
            guild=ctx.guild.id).all()
        session.close()
        return characters
