"""Add api key table

Revision ID: 2c9a1c09fce6
Revises: 456e966f0d00
Create Date: 2015-03-12 17:29:06.806505
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import UTCDateTime
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '2c9a1c09fce6'
down_revision = '456e966f0d00'


def upgrade():
    op.create_table('api_keys',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('token', postgresql.UUID(), nullable=False),
                    sa.Column('secret', postgresql.UUID(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('is_active', sa.Boolean(), nullable=False),
                    sa.Column('is_blocked', sa.Boolean(), nullable=False),
                    sa.Column('is_persistent_allowed', sa.Boolean(), nullable=False),
                    sa.Column('created_dt', UTCDateTime, nullable=False),
                    sa.Column('last_used_dt', UTCDateTime, nullable=True),
                    sa.Column('last_used_ip', postgresql.INET(), nullable=True),
                    sa.Column('last_used_uri', sa.String(), nullable=True),
                    sa.Column('last_used_auth', sa.Boolean(), nullable=True),
                    sa.Column('use_count', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('token'),
                    schema='indico')
    op.create_index(None, 'api_keys', ['user_id'], unique=True, schema='indico', postgresql_where=sa.text('is_active'))


def downgrade():
    op.drop_table('api_keys', schema='indico')
