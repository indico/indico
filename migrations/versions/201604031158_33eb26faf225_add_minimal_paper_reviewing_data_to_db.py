"""Add minimal paper reviewing data to DB

Revision ID: 33eb26faf225
Revises: 1af04f7ede7a
Create Date: 2016-04-03 11:58:16.756125
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.ddl import CreateSchema, DropSchema

from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.events.paper_reviewing.models.roles import PaperReviewingRoleType

# revision identifiers, used by Alembic.
revision = '33eb26faf225'
down_revision = '1af04f7ede7a'


def upgrade():
    op.execute(CreateSchema('event_abstracts'))

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


def downgrade():
    op.drop_table('contribution_roles', schema='event_paper_reviewing')
    op.execute(DropSchema('event_abstracts'))
