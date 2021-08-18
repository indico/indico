"""Add event category request

Revision ID: 9d00917b2fa8
Revises: 4b097412a8d9
Create Date: 2021-07-15 12:11:28.157824
"""
from enum import Enum

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime


# revision identifiers, used by Alembic.
revision = '9d00917b2fa8'
down_revision = '4b097412a8d9'
branch_labels = None
depends_on = None


class _MoveRequestState(int, Enum):
    pending = 0
    accepted = 1
    rejected = 2
    withdrawn = 3


class _EventCreationMode(int, Enum):
    restricted = 1
    moderated = 2
    open = 3


def upgrade():
    op.create_table(
        'event_move_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('category_id', sa.Integer(), nullable=False, index=True),
        sa.Column('requestor_id', sa.Integer(), nullable=False, index=True),
        sa.Column('state', PyIntEnum(_MoveRequestState), nullable=False),
        sa.Column('requestor_comment', sa.String(), nullable=False, default=''),
        sa.Column('moderator_comment', sa.String(), nullable=False, default=''),
        sa.Column('moderator_id', sa.Integer(), nullable=True),
        sa.Column('requested_dt', UTCDateTime, nullable=False),
        sa.CheckConstraint('(state in (1, 2) AND moderator_id IS NOT NULL) OR moderator_id IS NULL',
                           name='moderator_state'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.categories.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['moderator_id'], ['users.users.id']),
        sa.ForeignKeyConstraint(['requestor_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='categories'
    )
    op.create_index(None, 'event_move_requests', ['event_id'], unique=True,
                    schema='categories', postgresql_where=sa.text('state = 0'))

    op.add_column('categories',
                  sa.Column('event_creation_mode', PyIntEnum(_EventCreationMode), nullable=False, server_default='1'),
                  schema='categories')
    op.alter_column('categories', 'event_creation_mode', server_default=None, schema='categories')
    op.execute('UPDATE categories.categories SET event_creation_mode = 3 WHERE NOT event_creation_restricted')
    op.drop_column('categories', 'event_creation_restricted', schema='categories')


def downgrade():
    op.add_column('categories',
                  sa.Column('event_creation_restricted', sa.Boolean(), nullable=False, server_default='true'),
                  schema='categories')
    op.alter_column('categories', 'event_creation_restricted', server_default=None, schema='categories')
    op.execute('UPDATE categories.categories SET event_creation_restricted = false WHERE event_creation_mode = 3')
    op.drop_column('categories', 'event_creation_mode', schema='categories')
    op.drop_table('event_move_requests', schema='categories')
