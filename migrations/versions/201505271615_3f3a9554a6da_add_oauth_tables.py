"""Add OAuth tables

Revision ID: 3f3a9554a6da
Revises: 55583215f6fb
Create Date: 2015-05-19 11:25:26.268379
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.ddl import CreateSchema, DropSchema

from indico.core.db.sqlalchemy import UTCDateTime

# revision identifiers, used by Alembic.
revision = '3f3a9554a6da'
down_revision = '55583215f6fb'


def upgrade():
    op.execute(CreateSchema('oauth'))
    op.create_table('applications',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('description', sa.Text(), nullable=False),
                    sa.Column('client_id', postgresql.UUID(), nullable=False),
                    sa.Column('client_secret', postgresql.UUID, nullable=False),
                    sa.Column('default_scopes', postgresql.ARRAY(sa.String()), nullable=False),
                    sa.Column('redirect_uris', postgresql.ARRAY(sa.String()), nullable=False),
                    sa.Column('is_enabled', sa.Boolean(), nullable=False),
                    sa.Column('is_trusted', sa.Boolean(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('client_id'),
                    schema='oauth')

    op.create_index(op.f('ix_uq_applications_name_lower'), 'applications', [sa.text('lower(name)')], unique=True,
                    schema='oauth')

    op.create_table('tokens',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('application_id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('access_token', postgresql.UUID, nullable=False),
                    sa.Column('scopes', postgresql.ARRAY(sa.String()), nullable=True),
                    sa.Column('last_used_dt', UTCDateTime, nullable=True),
                    sa.ForeignKeyConstraint(['application_id'], ['oauth.applications.id']),
                    sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('access_token'),
                    sa.UniqueConstraint('application_id', 'user_id'),
                    schema='oauth')


def downgrade():
    op.drop_table('tokens', schema='oauth')
    op.drop_table('applications', schema='oauth')
    op.execute(DropSchema('oauth'))
