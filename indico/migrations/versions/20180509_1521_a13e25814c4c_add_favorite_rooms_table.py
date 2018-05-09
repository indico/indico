"""Add favorite rooms table

Revision ID: a13e25814c4c
Revises: 66ecbb1c0ddd
Create Date: 2018-05-09 15:21:16.896601
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a13e25814c4c'
down_revision = '66ecbb1c0ddd'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'favorite_rooms',
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('room_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['room_id'], ['roombooking.rooms.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('user_id', 'room_id',),
        schema='roombooking'
    )


def downgrade():
    op.drop_table('favorite_rooms', schema='roombooking')
