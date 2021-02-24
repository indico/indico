"""Use cascading FKs for oauth

Revision ID: ecc7088914e7
Revises: d354278c6d95
Create Date: 2021-02-24 18:05:51.453397
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'ecc7088914e7'
down_revision = 'd354278c6d95'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('fk_application_user_links_application_id_applications', 'application_user_links',
                       schema='oauth')
    op.drop_constraint('fk_application_user_links_user_id_users', 'application_user_links', schema='oauth')
    op.create_foreign_key(None, 'application_user_links', 'applications', ['application_id'], ['id'],
                          source_schema='oauth', referent_schema='oauth', ondelete='CASCADE')
    op.create_foreign_key(None, 'application_user_links', 'users', ['user_id'], ['id'],
                          source_schema='oauth', referent_schema='users', ondelete='CASCADE')


def downgrade():
    op.drop_constraint('fk_application_user_links_user_id_users', 'application_user_links', schema='oauth')
    op.drop_constraint('fk_application_user_links_application_id_applications', 'application_user_links',
                       schema='oauth')
    op.create_foreign_key(None, 'application_user_links', 'users', ['user_id'], ['id'],
                          source_schema='oauth', referent_schema='users')
    op.create_foreign_key(None, 'application_user_links', 'applications', ['application_id'], ['id'],
                          source_schema='oauth', referent_schema='oauth')
