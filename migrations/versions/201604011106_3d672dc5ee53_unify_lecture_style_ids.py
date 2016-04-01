"""Unify lecture style ids

Revision ID: 3d672dc5ee53
Revises: 506ad8bf647c
Create Date: 2016-03-17 10:03:17.857070
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3d672dc5ee53'
down_revision = '506ad8bf647c'


def _move_theme(from_, to):
    print "Moving '{}' -> '{}' themes".format(from_, to)
    op.execute("""
        UPDATE events.settings
        SET value = '"%s"'::json
        WHERE name = 'timetable_theme'
        AND module = 'layout'
        AND value#>>'{}' = '%s'
    """ % (to, from_))


def upgrade():
    _move_theme('event', 'lecture')
    _move_theme('text', 'standard')
    _move_theme('jacow', 'standard')
    _move_theme('xml', 'standard')
    _move_theme('cdsagenda', 'standard')
    _move_theme('cdsagenda_inline_minutes', 'standard_inline_minutes')
    _move_theme('cdsagenda_olist', 'standard')


def downgrade():
    pass
