"""Allow network principals in events

Revision ID: abf75c26dc4
Revises: 28784fc91683
Create Date: 2016-05-26 18:35:16.376895
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'abf75c26dc4'
down_revision = '28784fc91683'


def upgrade():
    op.add_column('principals', sa.Column('ip_network_group_id', sa.Integer(), nullable=True), schema='events')
    op.create_index(None, 'principals', ['ip_network_group_id'], schema='events')
    op.create_foreign_key(None,
                          'principals', 'ip_network_groups',
                          ['ip_network_group_id'], ['id'],
                          source_schema='events', referent_schema='indico')
    op.create_check_constraint('networks_read_only', 'principals',
                               "type != 5 OR (NOT full_access AND array_length(roles, 1) IS NULL)",
                               schema='events')
    op.drop_constraint('ck_principals_valid_email', 'principals', schema='events')
    op.drop_constraint('ck_principals_valid_local_group', 'principals', schema='events')
    op.drop_constraint('ck_principals_valid_multipass_group', 'principals', schema='events')
    op.drop_constraint('ck_principals_valid_user', 'principals', schema='events')
    op.create_check_constraint('valid_user', 'principals',
                               'type != 1 OR (email IS NULL AND ip_network_group_id IS NULL AND local_group_id IS NULL '
                               'AND mp_group_name IS NULL AND mp_group_provider IS NULL AND user_id IS NOT NULL)',
                               schema='events'),
    op.create_check_constraint('valid_local_group', 'principals',
                               ' type != 2 OR (email IS NULL AND ip_network_group_id IS NULL AND '
                               'mp_group_name IS NULL AND mp_group_provider IS NULL AND user_id IS NULL AND '
                               'local_group_id IS NOT NULL)',
                               schema='events'),
    op.create_check_constraint('valid_multipass_group', 'principals',
                               'type != 3 OR (email IS NULL AND ip_network_group_id IS NULL AND '
                               'local_group_id IS NULL AND user_id IS NULL AND mp_group_name IS NOT NULL AND '
                               'mp_group_provider IS NOT NULL)',
                               schema='events'),
    op.create_check_constraint('valid_email', 'principals',
                               'type != 4 OR (ip_network_group_id IS NULL AND local_group_id IS NULL AND '
                               'mp_group_name IS NULL AND mp_group_provider IS NULL AND user_id IS NULL AND '
                               'email IS NOT NULL)',
                               schema='events'),
    op.create_check_constraint('valid_network', 'principals',
                               'type != 5 OR (email IS NULL AND local_group_id IS NULL AND mp_group_name IS NULL AND '
                               'mp_group_provider IS NULL AND user_id IS NULL AND ip_network_group_id IS NOT NULL)',
                               schema='events'),
    op.drop_constraint('ck_principals_valid_enum_type', 'principals', schema='events')
    op.create_check_constraint('valid_enum_type', 'principals', "type IN ({})".format(', '.join(map(str, range(1, 6)))),
                               schema='events')


def downgrade():
    op.drop_constraint('ck_principals_valid_enum_type', 'principals', schema='events')
    op.create_check_constraint('valid_enum_type', 'principals', "type IN ({})".format(', '.join(map(str, range(1, 5)))),
                               schema='events')
    op.drop_constraint('ck_principals_valid_email', 'principals', schema='events')
    op.drop_constraint('ck_principals_valid_local_group', 'principals', schema='events')
    op.drop_constraint('ck_principals_valid_multipass_group', 'principals', schema='events')
    op.drop_constraint('ck_principals_valid_user', 'principals', schema='events')
    op.drop_constraint('ck_principals_valid_network', 'principals', schema='events')
    op.create_check_constraint('valid_user', 'principals',
                               'type != 1 OR (email IS NULL AND local_group_id IS NULL AND mp_group_name IS NULL AND '
                               'mp_group_provider IS NULL AND user_id IS NOT NULL)',
                               schema='events'),
    op.create_check_constraint('valid_local_group', 'principals',
                               ' type != 2 OR (email IS NULL AND mp_group_name IS NULL AND '
                               'mp_group_provider IS NULL AND user_id IS NULL AND local_group_id IS NOT NULL)',
                               schema='events'),
    op.create_check_constraint('valid_multipass_group', 'principals',
                               'type != 3 OR (email IS NULL AND local_group_id IS NULL AND user_id IS NULL AND '
                               'mp_group_name IS NOT NULL AND mp_group_provider IS NOT NULL)',
                               schema='events'),
    op.create_check_constraint('valid_email', 'principals',
                               'type != 4 OR (local_group_id IS NULL AND mp_group_name IS NULL AND '
                               'mp_group_provider IS NULL AND user_id IS NULL AND email IS NOT NULL)',
                               schema='events'),
    op.drop_constraint('ck_principals_networks_read_only', 'principals', schema='events')
    op.drop_column('principals', 'ip_network_group_id', schema='events')
