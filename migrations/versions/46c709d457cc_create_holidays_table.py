"""Create holidays table

Revision ID: 46c709d457cc
Revises: None
Create Date: 2014-07-25 15:41:01.707475
"""

from alembic import op
import sqlalchemy as sa


from indico.core.db import db


# revision identifiers, used by Alembic.
revision = '46c709d457cc'
down_revision = None


def upgrade():
    upgrade_schema()


def downgrade():
    downgrade_schema()


def upgrade_schema():
    op.create_table('holidays',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('date', sa.Date(), nullable=False),
                    sa.Column('location_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['location_id'], ['locations.id']),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('date', 'location_id'))
    op.create_index(op.f('ix_holidays_date'), 'holidays', ['date'], unique=False)


def downgrade_schema():
    op.drop_table('holidays')
