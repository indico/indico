"""Make event timetable consistency trigger conditional

Revision ID: 3bdd6bf0181a
Revises: 438138fdf6ce
Create Date: 2016-06-20 15:28:37.547704
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3bdd6bf0181a'
down_revision = '438138fdf6ce'


def _drop_triggers():
    op.execute('''
        DROP TRIGGER consistent_timetable ON events.events;
        DROP TRIGGER consistent_timetable ON events.contributions;
        DROP TRIGGER consistent_timetable ON events.breaks;
        DROP TRIGGER consistent_timetable ON events.session_blocks;
    ''')


def upgrade():
    _drop_triggers()
    op.execute('''
        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER UPDATE OF start_dt, end_dt
        ON events.events
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('event');

        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER INSERT OR UPDATE OF event_id, session_id, session_block_id, duration
        ON events.contributions
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('contribution');

        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER INSERT OR UPDATE OF duration
        ON events.breaks
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('break');

        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER INSERT OR UPDATE OF session_id, duration
        ON events.session_blocks
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('session_block');
    ''')


def downgrade():
    _drop_triggers()
    op.execute('''
        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER UPDATE
        ON events.events
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('event');

        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER INSERT OR UPDATE
        ON events.contributions
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('contribution');

        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER INSERT OR UPDATE
        ON events.breaks
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('break');

        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER INSERT OR UPDATE
        ON events.session_blocks
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('session_block');
    ''')
