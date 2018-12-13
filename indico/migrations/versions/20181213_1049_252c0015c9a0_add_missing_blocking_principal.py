"""Add missing blocking principal constraints

Revision ID: 252c0015c9a0
Revises: 4f98f2f979c7
Create Date: 2018-12-13 10:49:51.279917
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '252c0015c9a0'
down_revision = '4f98f2f979c7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(None, 'blocking_principals', ['mp_group_provider', 'mp_group_name'], schema='roombooking')
    op.create_index('ix_uq_blocking_principals_local_group',
                    'blocking_principals',
                    ['local_group_id', 'blocking_id'],
                    unique=True, schema='roombooking', postgresql_where=sa.text('type = 2'))
    op.create_index('ix_uq_blocking_principals_mp_group',
                    'blocking_principals',
                    ['mp_group_provider', 'mp_group_name', 'blocking_id'],
                    unique=True, schema='roombooking', postgresql_where=sa.text('type = 3'))
    op.create_index('ix_uq_blocking_principals_user',
                    'blocking_principals',
                    ['user_id', 'blocking_id'],
                    unique=True, schema='roombooking', postgresql_where=sa.text('type = 1'))
    op.create_check_constraint('valid_user', 'blocking_principals',
                               "((type != 1) OR ((local_group_id IS NULL) AND (mp_group_name IS NULL) AND "
                               "(mp_group_provider IS NULL) AND (user_id IS NOT NULL)))", schema='roombooking')
    op.create_check_constraint('valid_local_group', 'blocking_principals',
                               "((type != 2) OR ((mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND "
                               "(user_id IS NULL) AND (local_group_id IS NOT NULL)))", schema='roombooking')
    op.create_check_constraint('valid_multipass_group', 'blocking_principals',
                               "((type <> 3) OR ((local_group_id IS NULL) AND (user_id IS NULL) AND "
                               "(mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL)))",
                               schema='roombooking')


def downgrade():
    op.drop_index('ix_uq_blocking_principals_user', table_name='blocking_principals', schema='roombooking')
    op.drop_index('ix_uq_blocking_principals_mp_group', table_name='blocking_principals', schema='roombooking')
    op.drop_index('ix_uq_blocking_principals_local_group', table_name='blocking_principals', schema='roombooking')
    op.drop_index('ix_blocking_principals_mp_group_provider_mp_group_name', table_name='blocking_principals',
                  schema='roombooking')
    op.drop_constraint('ck_blocking_principals_valid_user', 'blocking_principals', schema='roombooking')
    op.drop_constraint('ck_blocking_principals_valid_local_group', 'blocking_principals', schema='roombooking')
    op.drop_constraint('ck_blocking_principals_valid_multipass_group', 'blocking_principals', schema='roombooking')
