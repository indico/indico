"""Use proper FK for API keys

Revision ID: 3463dd63745c
Revises: 1cdb1362b988
Create Date: 2015-04-10 17:43:49.134958
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3463dd63745c'
down_revision = '1cdb1362b988'


def upgrade():
    op.create_foreign_key(None,
                          'api_keys', 'users',
                          ['user_id'], ['id'],
                          source_schema='indico', referent_schema='users')


def downgrade():
    op.drop_constraint('fk_api_keys_user_id_users', 'api_keys', schema='indico')
