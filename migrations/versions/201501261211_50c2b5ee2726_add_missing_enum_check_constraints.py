"""Add missing enum check constraints

Revision ID: 50c2b5ee2726
Revises: 324c23d14151
Create Date: 2015-01-26 12:11:37.919152
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '50c2b5ee2726'
down_revision = '324c23d14151'


def upgrade():
    op.create_check_constraint('blocked_rooms_state_check', 'blocked_rooms', 'state IN (0, 1, 2)', schema='roombooking')
    op.create_check_constraint('reservations_repeat_frequency_check', 'reservations',
                               'repeat_frequency IN (0, 1, 2, 3)', schema='roombooking')


def downgrade():
    op.drop_constraint('reservations_repeat_frequency_check', 'reservations', schema='roombooking')
    op.drop_constraint('blocked_rooms_state_check', 'blocked_rooms', schema='roombooking')
