"""Rename repetition fields

Revision ID: 1adcf9d3dc7
Revises: 449d51d3e162
Create Date: 2014-08-11 13:30:13.223235
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '1adcf9d3dc7'
down_revision = '449d51d3e162'


def upgrade():
    op.alter_column('reservations', 'repeat_unit', new_column_name='repeat_frequency')
    op.alter_column('reservations', 'repeat_step', new_column_name='repeat_interval')


def downgrade():
    op.alter_column('reservations', 'repeat_interval', new_column_name='repeat_step')
    op.alter_column('reservations', 'repeat_frequency', new_column_name='repeat_unit')
