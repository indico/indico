"""Add legacy attachment mapping tables

Revision ID: 3778dc365e54
Revises: 20392a888368
Create Date: 2015-07-03 14:55:32.796877
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.links import LinkType


# revision identifiers, used by Alembic.
revision = '3778dc365e54'
down_revision = '20392a888368'


def upgrade():
    op.create_table(
        'legacy_folder_id_map',
        sa.Column('category_id', sa.Integer(), nullable=True, index=True),
        sa.Column('event_id', sa.Integer(), nullable=True, index=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('contribution_id', sa.String(), nullable=True),
        sa.Column('subcontribution_id', sa.String(), nullable=True),
        sa.Column('material_id', sa.String(), nullable=False),
        sa.Column('folder_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('link_type', PyIntEnum(LinkType, exclude_values={LinkType.category}), nullable=False),
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
        sa.ForeignKeyConstraint(['folder_id'], ['attachments.folders.id']),
        sa.PrimaryKeyConstraint('folder_id'),
        schema='attachments'
    )
    op.create_table(
        'legacy_attachment_id_map',
        sa.Column('category_id', sa.Integer(), nullable=True, index=True),
        sa.Column('event_id', sa.Integer(), nullable=True, index=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('contribution_id', sa.String(), nullable=True),
        sa.Column('subcontribution_id', sa.String(), nullable=True),
        sa.Column('material_id', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('attachment_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('link_type', PyIntEnum(LinkType, exclude_values={LinkType.category}), nullable=False),
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
        sa.ForeignKeyConstraint(['attachment_id'], ['attachments.attachments.id']),
        sa.PrimaryKeyConstraint('attachment_id'),
        schema='attachments'
    )


def downgrade():
    op.drop_table('legacy_attachment_id_map', schema='attachments')
    op.drop_table('legacy_folder_id_map', schema='attachments')
