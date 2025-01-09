"""move_user_sessions_to_postgres

Revision ID: fb255305ea83
Revises: 75db3a4a4ed4
Create Date: 2024-10-23 15:17:02.490888
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'fb255305ea83'
down_revision = '34f27622213b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sid', sa.String(), nullable=False, unique=True),
        sa.Column('data', sa.LargeBinary(), nullable=False),
        sa.Column('ttl', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        schema='users'
    )


def downgrade():
    op.drop_table('sessions', schema='users')
