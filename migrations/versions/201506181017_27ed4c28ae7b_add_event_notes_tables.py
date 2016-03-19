"""Add event notes tables

Revision ID: 27ed4c28ae7b
Revises: 9f0a44f8035
Create Date: 2015-06-18 10:17:33.787716
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.db.sqlalchemy.links import LinkType
from indico.modules.events.notes.models.notes import RenderMode


# revision identifiers, used by Alembic.
revision = '27ed4c28ae7b'
down_revision = '9f0a44f8035'


def upgrade():
    op.create_table(
        'notes',
        sa.Column('link_type', PyIntEnum(LinkType, exclude_values={LinkType.category}), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True, index=True),
        sa.Column('event_id', sa.Integer(), nullable=True, index=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('contribution_id', sa.String(), nullable=True),
        sa.Column('subcontribution_id', sa.String(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('html', sa.Text(), nullable=False),
        sa.Column('current_revision_id', sa.Integer(), nullable=True),
        sa.Index(None, 'event_id', unique=True, postgresql_where=sa.text('link_type = 2')),
        sa.Index(None, 'event_id', 'contribution_id', unique=True, postgresql_where=sa.text('link_type = 3')),
        sa.Index(None, 'event_id', 'contribution_id', 'subcontribution_id', unique=True,
                 postgresql_where=sa.text('link_type = 4')),
        sa.Index(None, 'event_id', 'session_id', unique=True, postgresql_where=sa.text('link_type = 5')),
        sa.CheckConstraint('link_type != 2 OR (contribution_id IS NULL AND subcontribution_id IS NULL AND '
                           'category_id IS NULL AND session_id IS NULL AND event_id IS NOT NULL)',
                           name='valid_event_link'),
        sa.CheckConstraint('link_type != 3 OR (subcontribution_id IS NULL AND category_id IS NULL AND '
                           'session_id IS NULL AND event_id IS NOT NULL AND contribution_id IS NOT NULL)',
                           name='valid_contribution_link'),
        sa.CheckConstraint('link_type != 4 OR (category_id IS NULL AND session_id IS NULL AND event_id IS NOT NULL AND '
                           'contribution_id IS NOT NULL AND subcontribution_id IS NOT NULL)',
                           name='valid_subcontribution_link'),
        sa.CheckConstraint('link_type != 5 OR (contribution_id IS NULL AND subcontribution_id IS NULL AND '
                           'category_id IS NULL AND event_id IS NOT NULL AND session_id IS NOT NULL)',
                           name='valid_session_link'),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_table(
        'note_revisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('note_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('created_dt', UTCDateTime, nullable=False),
        sa.Column('render_mode', PyIntEnum(RenderMode), nullable=False),
        sa.Column('source', sa.Text(), nullable=False),
        sa.Column('html', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['note_id'], ['events.notes.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_foreign_key(None,
                          'notes', 'note_revisions',
                          ['current_revision_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_constraint('fk_notes_current_revision_id_note_revisions', 'notes', schema='events')
    op.drop_table('note_revisions', schema='events')
    op.drop_table('notes', schema='events')
