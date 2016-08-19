"""Add abstract comments

Revision ID: 1eb296cc7b9e
Revises: 3fa15b0846df
Create Date: 2016-08-18 14:04:26.112289
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '1eb296cc7b9e'
down_revision = '3fa15b0846df'


def upgrade():
    op.create_table(
        'abstract_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('abstract_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('modified_by_id', sa.Integer(), nullable=True, index=True),
        sa.Column('created_dt', UTCDateTime, nullable=False),
        sa.Column('modified_dt', UTCDateTime, nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['abstract_id'], ['event_abstracts.abstracts.id']),
        sa.ForeignKeyConstraint(['modified_by_id'], ['users.users.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_abstracts'
    )


def downgrade():
    op.drop_table('abstract_comments', schema='event_abstracts')
