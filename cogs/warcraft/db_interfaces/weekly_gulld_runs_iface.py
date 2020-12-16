from cogs.warcraft.database.db_models import WarcraftCharacterWeeklyRun
from cogs.warcraft.database.db_engine_session_init import Session


class WarcraftCharacterWeeklyRunsInterface:
    @classmethod
    async def add_run(cls, run_id, character_name, dungeon_name, dungeon_level):
        session = Session()
        existing_run = session.query(WarcraftCharacterWeeklyRun).filter_by(
            run_id=run_id, character_name=character_name.lower()).first()
        if existing_run is None:
            new_run = WarcraftCharacterWeeklyRun()
            new_run.run_id = run_id
            new_run.character_name = character_name.lower()
            new_run.dungeon_name = dungeon_name
            new_run.dungeon_level = dungeon_level
            success = False
            try:
                session.add(new_run)
                session.commit()
                success = True
            except Exception as e:
                print(f'An error occurred while adding a new weekly guild mplus run:\n{e}')
                session.rollback()
            finally:
                session.close()
            return success

    @classmethod
    async def get_player_runs(cls, character_name):
        session = Session()
        runs = session.query(WarcraftCharacterWeeklyRun).filter_by(
            character_name=character_name).all()
        session.close()
        return runs

    @classmethod
    async def reset_runs(cls):
        session = Session()
        runs = session.query(WarcraftCharacterWeeklyRun).all()
        success = False
        try:
            for r in runs:
                session.delete(r)
            session.commit()
            success = True
        except Exception as e:
            print(f'An error occurred when attempting to reset guild weekly runs:\n{e}')
            session.rollback()
        finally:
            session.close()
            return success
