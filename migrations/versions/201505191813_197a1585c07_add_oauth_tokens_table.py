"""Add OAuth tokens table

Revision ID: 197a1585c07
Revises: 3f3a9554a6da
Create Date: 2015-05-19 18:13:16.666459
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '197a1585c07'
down_revision = '3f3a9554a6da'


def upgrade():
    op.create_table('tokens',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('application_id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('access_token', sa.String(), nullable=False),
                    sa.Column('scopes', postgresql.ARRAY(sa.String()), nullable=True),
                    sa.Column('last_used_dt', UTCDateTime, nullable=True),
                    sa.ForeignKeyConstraint(['application_id'], [u'oauth.applications.id'],
                                            name=op.f('fk_tokens_application_id_applications')),
                    sa.ForeignKeyConstraint(['user_id'], [u'users.users.id'], name=op.f('fk_tokens_user_id_users')),
                    sa.PrimaryKeyConstraint('id', name=op.f('pk_tokens')),
                    sa.UniqueConstraint('access_token', name=op.f('uq_tokens_access_token')),
                    schema='oauth')
    op.create_index(op.f('ix_tokens_user_id'), 'tokens', ['user_id'], unique=False, schema='oauth')


def downgrade():
    op.drop_index(op.f('ix_tokens_user_id'), table_name='tokens', schema='oauth')
    op.drop_table('tokens', schema='oauth')
