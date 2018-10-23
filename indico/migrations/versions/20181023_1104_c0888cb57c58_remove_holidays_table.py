"""Remove holidays table

Revision ID: c0888cb57c58
Revises: f7ab9ee32bdf
Create Date: 2018-10-23 11:04:31.162671
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'c0888cb57c58'
down_revision = 'f7ab9ee32bdf'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('holidays', schema='roombooking')


def downgrade():
    op.create_table(
        'holidays',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['location_id'], ['roombooking.locations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'location_id'),
        schema='roombooking'
    )
