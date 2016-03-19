"""Add extra indexes for user search

Revision ID: a2dfbb4b85c
Revises: 4074211727ba
Create Date: 2015-06-08 12:44:42.485227
"""

import sqlalchemy as sa
from alembic import op, context

from indico.core.db.sqlalchemy.util.queries import has_extension


# revision identifiers, used by Alembic.
revision = 'a2dfbb4b85c'
down_revision = '4074211727ba'


def _create_index(has_trgm, table, column):
    col_func = 'indico_unaccent(lower({}))'.format(column)
    kwargs = {}
    if has_trgm:
        kwargs = {'postgresql_using': 'gin',
                  'postgresql_ops': {col_func: 'gin_trgm_ops'}}
    op.create_index(op.f('ix_{}_{}_unaccent'.format(table, column)), table, [sa.text(col_func)], schema='users',
                    **kwargs)


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')

    has_trgm = has_extension(op.get_bind(), 'pg_trgm')
    if has_trgm:
        print 'pg_trgm extension is available - creating trigram indexes'
    else:
        print 'pg_trgm extension is not available - creating normal indexes'

    _create_index(has_trgm, 'users', 'first_name')
    _create_index(has_trgm, 'users', 'last_name')
    _create_index(has_trgm, 'users', 'phone')
    _create_index(has_trgm, 'users', 'address')
    _create_index(has_trgm, 'affiliations', 'name')
    _create_index(has_trgm, 'emails', 'email')


def downgrade():
    op.drop_index('ix_users_first_name_unaccent', 'users', schema='users')
    op.drop_index('ix_users_last_name_unaccent', 'users', schema='users')
    op.drop_index('ix_users_phone_unaccent', 'users', schema='users')
    op.drop_index('ix_users_address_unaccent', 'users', schema='users')
    op.drop_index('ix_affiliations_name_unaccent', 'affiliations', schema='users')
    op.drop_index('ix_emails_email_unaccent', 'users', schema='users')
