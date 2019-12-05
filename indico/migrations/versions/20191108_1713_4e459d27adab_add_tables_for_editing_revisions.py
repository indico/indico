"""Add tables for editing revisions

Revision ID: 4e459d27adab
Revises: 39a25a873063
Create Date: 2019-11-08 17:13:48.096553
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.modules.events.editing.models.editable import EditableType
from indico.modules.events.editing.models.revisions import FinalRevisionState, InitialRevisionState


# revision identifiers, used by Alembic.
revision = '4e459d27adab'
down_revision = '39a25a873063'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'editables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contribution_id', sa.Integer(), nullable=False, index=True),
        sa.Column('type', PyIntEnum(EditableType), nullable=False),
        sa.Column('editor_id', sa.Integer(), nullable=True, index=True),
        sa.Column('published_revision_id', sa.Integer(), nullable=True, index=True),
        sa.ForeignKeyConstraint(['contribution_id'], ['events.contributions.id']),
        sa.ForeignKeyConstraint(['editor_id'], ['users.users.id']),
        sa.UniqueConstraint('contribution_id', 'type'),
        sa.PrimaryKeyConstraint('id'),
        schema='event_editing'
    )

    op.create_table(
        'revisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('editable_id', sa.Integer(), nullable=False, index=True),
        sa.Column('submitter_id', sa.Integer(), nullable=False, index=True),
        sa.Column('editor_id', sa.Integer(), nullable=True, index=True),
        sa.Column('created_dt', UTCDateTime, nullable=False),
        sa.Column('initial_state', PyIntEnum(InitialRevisionState), nullable=False),
        sa.Column('final_state', PyIntEnum(FinalRevisionState), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['editable_id'], ['event_editing.editables.id']),
        sa.ForeignKeyConstraint(['editor_id'], ['users.users.id']),
        sa.ForeignKeyConstraint(['submitter_id'], ['users.users.id']),
        sa.CheckConstraint('(initial_state=1 AND final_state IN (0,1)) OR (initial_state=2) OR '
                           '(initial_state=3 AND (final_state IN (0,3,4)))', name='valid_state_combination'),
        sa.PrimaryKeyConstraint('id'),
        schema='event_editing'
    )
    op.create_foreign_key(None, 'editables', 'revisions', ['published_revision_id'], ['id'],
                          source_schema='event_editing', referent_schema='event_editing')

    op.create_table(
        'revision_files',
        sa.Column('revision_id', sa.Integer(), nullable=False, index=True),
        sa.Column('file_id', sa.Integer(), nullable=False, index=True),
        sa.Column('file_type_id', sa.Integer(), nullable=True, index=True),
        sa.ForeignKeyConstraint(['file_id'], ['indico.files.id']),
        sa.ForeignKeyConstraint(['file_type_id'], ['event_editing.file_types.id']),
        sa.ForeignKeyConstraint(['revision_id'], ['event_editing.revisions.id']),
        sa.PrimaryKeyConstraint('revision_id', 'file_id'),
        schema='event_editing'
    )

    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=False),
        sa.Column('system', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_editing'
    )
    op.create_index('ix_uq_tags_event_id_code_lower', 'tags', ['event_id', sa.text('lower(code)')],
                    unique=True, schema='event_editing')

    op.create_table(
        'revision_tags',
        sa.Column('revision_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
        sa.Column('tag_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
        sa.ForeignKeyConstraint(['revision_id'], ['event_editing.revisions.id']),
        sa.ForeignKeyConstraint(['tag_id'], ['event_editing.tags.id']),
        sa.PrimaryKeyConstraint('revision_id', 'tag_id'),
        schema='event_editing'
    )

    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('revision_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('created_dt', UTCDateTime, nullable=False),
        sa.Column('modified_dt', UTCDateTime, nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('internal', sa.Boolean(), nullable=False),
        sa.Column('system', sa.Boolean(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.CheckConstraint('(user_id IS NULL) = system', name='system_comment_no_user'),
        sa.ForeignKeyConstraint(['revision_id'], ['event_editing.revisions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_editing'
    )


def downgrade():
    op.drop_table('comments', schema='event_editing')
    op.drop_table('revision_tags', schema='event_editing')
    op.drop_table('tags', schema='event_editing')
    op.drop_table('revision_files', schema='event_editing')
    op.drop_constraint('fk_editables_published_revision_id_revisions', 'editables', schema='event_editing')
    op.drop_table('revisions', schema='event_editing')
    op.drop_table('editables', schema='event_editing')
