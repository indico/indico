"""Make event timetable consistency trigger conditional

Revision ID: 3bdd6bf0181a
Revises: 18755f50c6e7
Create Date: 2016-06-20 15:28:37.547704
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3bdd6bf0181a'
down_revision = '18755f50c6e7'


def upgrade():
    op.execute('DROP TRIGGER consistent_timetable ON events.events')
    op.execute('''
        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER UPDATE OF start_dt, end_dt
        ON events.events
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('event');
    ''')


def downgrade():
    op.execute('DROP TRIGGER consistent_timetable ON events.events')
    op.execute('''
        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER UPDATE
        ON events.events
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('event');
    ''')
