"""Add table for notifications

Revision ID: 87d248818199
Revises: 06a4ec717b84
Create Date: 2019-05-31 12:20:19.089312
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.descriptions import RenderMode


# revision identifiers, used by Alembic.
revision = '87d248818199'
down_revision = '06a4ec717b84'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('subject', sa.Text(), nullable=False),
        sa.Column('render_mode', PyIntEnum(RenderMode), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('sent_dt', UTCDateTime, index=True),
        sa.Column('created_dt', UTCDateTime, index=True, nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='indico'
    )


def downgrade():
    op.drop_table('notifications', schema='indico')
