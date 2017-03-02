"""Add minimal paper reviewing data to DB

Revision ID: 33eb26faf225
Revises: 1af04f7ede7a
Create Date: 2016-04-03 11:58:16.756125
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.ddl import CreateSchema, DropSchema

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.util.struct.enum import RichIntEnum

# revision identifiers, used by Alembic.
revision = '33eb26faf225'
down_revision = '3b0b69b541a2'


class PaperReviewingRoleType(RichIntEnum):
    reviewer = 0
    referee = 1
    editor = 2


def upgrade():
    op.execute(CreateSchema('event_paper_reviewing'))

    op.create_table(
        'contribution_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('contribution_id', sa.Integer(), nullable=False, index=True),
        sa.Column('role', PyIntEnum(PaperReviewingRoleType), nullable=False, index=True),
        sa.ForeignKeyConstraint(['contribution_id'], [u'events.contributions.id']),
        sa.ForeignKeyConstraint(['user_id'], [u'users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_paper_reviewing'
    )

    op.create_table(
        'paper_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contribution_id', sa.Integer(), nullable=False, index=True),
        sa.Column('revision_id', sa.Integer(), nullable=True),
        sa.Column('storage_backend', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('storage_file_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('created_dt', UTCDateTime, nullable=False),
        sa.ForeignKeyConstraint(['contribution_id'], [u'events.contributions.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_paper_reviewing'
    )


def downgrade():
    op.drop_table('paper_files', schema='event_paper_reviewing')
    op.drop_table('contribution_roles', schema='event_paper_reviewing')
    op.execute(DropSchema('event_paper_reviewing'))
