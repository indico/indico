"""Add event roles table

Revision ID: f1eee7b4880a
Revises:
Create Date: 2017-09-05 14:45:28.673606
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'f1eee7b4880a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=False),
        sa.Index(None, 'event_id', 'code', unique=True),
        sa.CheckConstraint('code = upper(code)', name='uppercase_code'),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_table(
        'role_members',
        sa.Column('role_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['role_id'], ['events.roles.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('role_id', 'user_id'),
        schema='events'
    )


def downgrade():
    op.drop_table('role_members', schema='events')
    op.drop_table('roles', schema='events')
