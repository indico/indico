"""Add personal access tokens

Revision ID: 1f6738730753
Revises: 356b8985ae7c
Create Date: 2021-06-29 12:05:07.347139
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '1f6738730753'
down_revision = '356b8985ae7c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('access_token_hash', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('scopes', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('created_dt', UTCDateTime, nullable=False),
        sa.Column('last_used_dt', UTCDateTime, nullable=True),
        sa.Column('revoked_dt', UTCDateTime, nullable=True),
        sa.Index('ix_uq_user_id_name_lower', 'user_id', sa.text('lower(name)'), unique=True,
                 postgresql_where=sa.text('revoked_dt IS NULL')),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='users'
    )


def downgrade():
    op.drop_table('tokens', schema='users')
