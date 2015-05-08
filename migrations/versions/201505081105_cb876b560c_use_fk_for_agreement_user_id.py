"""Use FK for agreement user_id

Revision ID: cb876b560c
Revises: 5a5297fea7bd
Create Date: 2015-05-08 11:05:27.852765
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'cb876b560c'
down_revision = '5a5297fea7bd'


def upgrade():
    op.create_foreign_key(None,
                          'agreements', 'users',
                          ['user_id'], ['id'],
                          source_schema='events', referent_schema='users')
    op.create_index(None, 'agreements', ['user_id'], unique=False, schema='events')


def downgrade():
    op.drop_index(op.f('ix_agreements_user_id'), table_name='agreements', schema='events')
    op.drop_constraint('fk_agreements_user_id_users', 'agreements', schema='events')
