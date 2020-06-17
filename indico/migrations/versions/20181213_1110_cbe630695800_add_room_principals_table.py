"""Add room principals table

Revision ID: cbe630695800
Revises: 252c0015c9a0
Create Date: 2018-12-13 11:10:12.684382
"""

from __future__ import print_function

import json

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.dialects import postgresql

from indico.core.auth import multipass
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.protection import ProtectionMode


# revision identifiers, used by Alembic.
revision = 'cbe630695800'
down_revision = '252c0015c9a0'
branch_labels = None
depends_on = None


def _create_acl_entry(conn, room_id, user_id=None, group_id=None, mp_group_provider=None, mp_group_name=None,
                      full_access=False, permissions=()):
    permissions = list(permissions)
    if user_id is not None:
        conn.execute('''
            INSERT INTO roombooking.room_principals
            (room_id, user_id, type, read_access, full_access, permissions) VALUES
            (%s,      %s,      %s,   false,       %s,          %s)
        ''', (room_id, user_id, PrincipalType.user.value, full_access, permissions))
    elif group_id is not None:
        conn.execute('''
            INSERT INTO roombooking.room_principals
            (room_id, local_group_id, type, read_access, full_access, permissions) VALUES
            (%s,      %s,             %s,   false,       %s,          %s)
        ''', (room_id, group_id, PrincipalType.local_group.value, full_access, permissions))
    else:
        conn.execute('''
            INSERT INTO roombooking.room_principals
            (room_id, mp_group_provider, mp_group_name, type, read_access, full_access, permissions) VALUES
            (%s,      %s,                %s,            %s,   false,       %s,          %s)
        ''', (room_id, mp_group_provider, mp_group_name, PrincipalType.multipass_group.value, full_access, permissions))


def _get_attr_value(conn, room_id, attr_id):
    query = 'SELECT value FROM roombooking.room_attribute_values WHERE room_id = %s AND attribute_id = %s'
    return conn.execute(query, (room_id, attr_id)).scalar()


def _get_default_group_provider():
    try:
        provider = multipass.default_group_provider
    except AttributeError:
        xargs = context.get_x_argument(as_dictionary=True)
        return xargs.get('default_group_provider')
    else:
        return provider.name


def _group_to_kwargs(group):
    default_group_provider = _get_default_group_provider()
    if default_group_provider:
        return {'mp_group_provider': default_group_provider, 'mp_group_name': group}
    else:
        try:
            return {'local_group_id': int(group)}
        except ValueError:
            # non-numeric group id
            return None


def _upgrade_permissions():
    conn = op.get_bind()
    booking_group_attr_id = conn.execute('SELECT id FROM roombooking.room_attributes WHERE name = %s',
                                         ('allowed-booking-group',)).scalar()
    manager_group_attr_id = conn.execute('SELECT id FROM roombooking.room_attributes WHERE name = %s',
                                         ('manager-group',)).scalar()
    query = 'SELECT id, owner_id, reservations_need_confirmation, is_reservable FROM roombooking.rooms'
    for room_id, owner_id, reservations_need_confirmation, is_reservable in conn.execute(query):
        booking_group = manager_group = None
        if booking_group_attr_id is not None:
            booking_group = _get_attr_value(conn, room_id, booking_group_attr_id)
        if manager_group_attr_id is not None:
            manager_group = _get_attr_value(conn, room_id, manager_group_attr_id)

        if not booking_group and is_reservable:
            conn.execute('UPDATE roombooking.rooms SET protection_mode = %s WHERE id = %s',
                         (ProtectionMode.public.value, room_id))
        if booking_group:
            group_kwargs = _group_to_kwargs(booking_group)
            if group_kwargs is None:
                print('WARNING: Invalid booking group: {}'.format(booking_group))
            else:
                permission = 'prebook' if reservations_need_confirmation else 'book'
                _create_acl_entry(conn, room_id, permissions={permission}, **group_kwargs)
        if manager_group:
            group_kwargs = _group_to_kwargs(manager_group)
            if group_kwargs is None:
                print('WARNING: Invalid manager group: {}'.format(manager_group))
            else:
                _create_acl_entry(conn, room_id, full_access=True, **group_kwargs)

    # is_reservable==false used allow the room owner to book the room, which
    # isn't the case anymore, so we mark all rooms as reservable.
    # above we already kept non-reservable rooms as protected
    conn.execute('UPDATE roombooking.rooms SET is_reservable = true')


def _create_attribute(conn, name, title):
    res = conn.execute('''
        INSERT INTO roombooking.room_attributes (name, title, is_hidden)
        VALUES (%s, %s, false)
        RETURNING id
    ''', (name, title))
    return res.fetchone()[0]


def _set_attribute_value(conn, room_id, attribute_id, value):
    res = conn.execute('SELECT value FROM roombooking.room_attribute_values WHERE room_id = %s AND attribute_id = %s',
                       (room_id, attribute_id))
    if not res.rowcount:
        conn.execute('''
            INSERT INTO roombooking.room_attribute_values
            (room_id, attribute_id, value) VALUES
            (%s, %s, %s)
        ''', (room_id, attribute_id, json.dumps(value)))
    elif res.scalar() != value:
        conn.execute('''
            UPDATE roombooking.room_attribute_values
            SET value = %s
            WHERE room_id = %s AND attribute_id = %s
        ''', (json.dumps(value), room_id, attribute_id))


def _downgrade_permissions():
    default_group_provider = _get_default_group_provider()
    conn = op.get_bind()
    booking_group_attr_id = conn.execute('SELECT id FROM roombooking.room_attributes WHERE name = %s',
                                         ('allowed-booking-group',)).scalar()
    manager_group_attr_id = conn.execute('SELECT id FROM roombooking.room_attributes WHERE name = %s',
                                         ('manager-group',)).scalar()
    if booking_group_attr_id is None:
        booking_group_attr_id = _create_attribute(conn, 'allowed-booking-group', 'Allowed Booking Group')
    if manager_group_attr_id is None:
        manager_group_attr_id = _create_attribute(conn, 'manager-group', 'Manager Group')

    query = 'SELECT id, owner_id, protection_mode FROM roombooking.rooms'
    for room_id, owner_id, protection_mode in conn.execute(query):
        res = conn.execute('SELECT * FROM roombooking.room_principals WHERE room_id = %s', (room_id,))
        if not res.rowcount and protection_mode == ProtectionMode.protected:
            conn.execute('UPDATE roombooking.rooms SET is_reservable = false WHERE id = %s', (room_id,))
        for row in res:
            if row.type == PrincipalType.user and row.user_id == owner_id:
                continue
            if row.type == PrincipalType.local_group and not default_group_provider:
                if row.full_access:
                    _set_attribute_value(conn, room_id, manager_group_attr_id, unicode(row.local_group_id))
                if 'book' in row.permissions or 'prebook' in row.permissions:
                    _set_attribute_value(conn, room_id, booking_group_attr_id, unicode(row.local_group_id))
            elif (row.type == PrincipalType.multipass_group and default_group_provider and
                    row.mp_group_provider == default_group_provider.name):
                if row.full_access:
                    _set_attribute_value(conn, room_id, manager_group_attr_id, row.mp_group_name)
                if 'book' in row.permissions or 'prebook' in row.permissions:
                    _set_attribute_value(conn, room_id, booking_group_attr_id, row.mp_group_name)


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    op.create_table(
        'room_principals',
        sa.Column('read_access', sa.Boolean(), nullable=False),
        sa.Column('full_access', sa.Boolean(), nullable=False),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False, index=True),
        sa.Column('local_group_id', sa.Integer(), nullable=True, index=True),
        sa.Column('mp_group_provider', sa.String(), nullable=True),
        sa.Column('mp_group_name', sa.String(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('type', PyIntEnum(PrincipalType, exclude_values={PrincipalType.email, PrincipalType.network,
                                                                   PrincipalType.event_role}), nullable=False),
        sa.CheckConstraint('NOT read_access', name='no_read_access'),
        sa.CheckConstraint('read_access OR full_access OR array_length(permissions, 1) IS NOT NULL', name='has_privs'),
        sa.CheckConstraint('type != 1 OR (local_group_id IS NULL AND mp_group_name IS NULL AND '
                           'mp_group_provider IS NULL AND user_id IS NOT NULL)', name='valid_user'),
        sa.CheckConstraint('type != 2 OR (mp_group_name IS NULL AND mp_group_provider IS NULL AND user_id IS NULL AND '
                           'local_group_id IS NOT NULL)', name='valid_local_group'),
        sa.CheckConstraint('type != 3 OR (local_group_id IS NULL AND user_id IS NULL AND mp_group_name IS NOT NULL AND '
                           'mp_group_provider IS NOT NULL)', name='valid_multipass_group'),
        sa.ForeignKeyConstraint(['local_group_id'], ['users.groups.id']),
        sa.ForeignKeyConstraint(['room_id'], ['roombooking.rooms.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='roombooking'
    )
    op.create_index(None, 'room_principals', ['mp_group_provider', 'mp_group_name'], schema='roombooking')
    op.create_index('ix_uq_room_principals_user', 'room_principals', ['user_id', 'room_id'], unique=True,
                    schema='roombooking', postgresql_where=sa.text('type = 1'))
    op.create_index('ix_uq_room_principals_local_group', 'room_principals', ['local_group_id', 'room_id'], unique=True,
                    schema='roombooking', postgresql_where=sa.text('type = 2'))
    op.create_index('ix_uq_room_principals_mp_group', 'room_principals',
                    ['mp_group_provider', 'mp_group_name', 'room_id'], unique=True, schema='roombooking',
                    postgresql_where=sa.text('type = 3'))
    op.add_column('rooms', sa.Column('protection_mode',
                                     PyIntEnum(ProtectionMode, exclude_values={ProtectionMode.inheriting}),
                                     nullable=False, server_default=unicode(ProtectionMode.protected.value)),
                  schema='roombooking')
    _upgrade_permissions()
    op.alter_column('rooms', 'protection_mode', server_default=None, schema='roombooking')


def downgrade():
    if context.is_offline_mode():
        raise Exception('This downgrade is only possible in online mode')
    _downgrade_permissions()
    op.drop_column('rooms', 'protection_mode', schema='roombooking')
    op.drop_table('room_principals', schema='roombooking')
