"""Use FKs for request user ids

Revision ID: 3f63e79cdada
Revises: cb876b560c
Create Date: 2015-05-08 11:47:29.219140
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3f63e79cdada'
down_revision = 'cb876b560c'


def upgrade():
    op.create_foreign_key(None,
                          'requests', 'users',
                          ['created_by_id'], ['id'],
                          source_schema='events', referent_schema='users')
    op.create_foreign_key(None,
                          'requests', 'users',
                          ['processed_by_id'], ['id'],
                          source_schema='events', referent_schema='users')
    op.create_index(None, 'requests', ['created_by_id'], unique=False, schema='events')
    op.create_index(None, 'requests', ['processed_by_id'], unique=False, schema='events')


def downgrade():
    op.drop_index(op.f('ix_requests_processed_by_id'), table_name='requests', schema='events')
    op.drop_index(op.f('ix_requests_created_by_id'), table_name='requests', schema='events')
    op.drop_constraint('fk_requests_created_by_id_users', 'requests', schema='events')
    op.drop_constraint('fk_requests_processed_by_id_users', 'requests', schema='events')
