"""Add extra indexes for user search

Revision ID: a2dfbb4b85c
Revises: 4074211727ba
Create Date: 2015-06-08 12:44:42.485227
"""

import sqlalchemy as sa
from alembic import op, context


# revision identifiers, used by Alembic.
revision = 'a2dfbb4b85c'
down_revision = '4074211727ba'


def _create_index(table, column):
    col_func = 'indico_unaccent(lower({}))'.format(column)
    kwargs = {'postgresql_using': 'gin',
              'postgresql_ops': {col_func: 'gin_trgm_ops'}}
    op.create_index(op.f('ix_{}_{}_unaccent'.format(table, column)), table, [sa.text(col_func)], schema='users',
                    **kwargs)


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')

    _create_index('users', 'first_name')
    _create_index('users', 'last_name')
    _create_index('users', 'phone')
    _create_index('users', 'address')
    _create_index('affiliations', 'name')
    _create_index('emails', 'email')


def downgrade():
    op.drop_index('ix_users_first_name_unaccent', 'users', schema='users')
    op.drop_index('ix_users_last_name_unaccent', 'users', schema='users')
    op.drop_index('ix_users_phone_unaccent', 'users', schema='users')
    op.drop_index('ix_users_address_unaccent', 'users', schema='users')
    op.drop_index('ix_affiliations_name_unaccent', 'affiliations', schema='users')
    op.drop_index('ix_emails_email_unaccent', 'users', schema='users')
