"""Add track principal

Revision ID: 2496c4adc7e9
Revises: 4e459d27adab
Create Date: 2019-10-02 18:20:33.866458
"""

import bisect

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.principals import PrincipalType


# revision identifiers, used by Alembic.
revision = '2496c4adc7e9'
down_revision = '4e459d27adab'
branch_labels = None
depends_on = None


def _update_event_acl_entry(conn, user_id, event_id, permissions):
    conn.execute('''
        UPDATE events.principals
        SET permissions = %s
        WHERE user_id = %s AND event_id = %s
    ''', [(permissions, user_id, event_id)])


def _create_track_acl_entry(conn, user_id, track_id, permissions):
    conn.execute('''
        INSERT INTO events.track_principals
        (track_id, user_id, type, read_access, full_access, permissions) VALUES
        (%s,       %s,      %s,   false,       false,       %s)
    ''', (track_id, user_id, PrincipalType.user.value, permissions))


def _upgrade_permissions():
    conn = op.get_bind()

    # Create track acl entries

    track_reviewers_conveners_stmt = '''
        SELECT user_id, track_id
        FROM events.track_abstract_reviewers r
        WHERE EXISTS (
            SELECT 1
            FROM events.track_conveners c
            WHERE r.user_id = c.user_id AND r.track_id = c.track_id
        )
    '''
    for user_id, track_id in conn.execute(track_reviewers_conveners_stmt):
        _create_track_acl_entry(conn, user_id, track_id, ['convene', 'review'])

    track_reviewers_stmt = '''
        SELECT user_id, track_id
        FROM events.track_abstract_reviewers r
        WHERE (
            track_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM events.track_conveners c
                WHERE r.user_id = c.user_id AND r.track_id = c.track_id
            )
        )
    '''
    for user_id, track_id in conn.execute(track_reviewers_stmt):
        _create_track_acl_entry(conn, user_id, track_id, ['review'])

    track_conveners_stmt = '''
        SELECT user_id, track_id
        FROM events.track_conveners c
        WHERE (
            track_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM events.track_abstract_reviewers r
                WHERE r.user_id = c.user_id AND r.track_id = c.track_id
            )
        )
    '''
    for user_id, track_id in conn.execute(track_conveners_stmt):
        _create_track_acl_entry(conn, user_id, track_id, ['convene'])

    # Update event acl entries

    event_reviewers_stmt = '''
        SELECT r.user_id, r.event_id, p.permissions
        FROM events.track_abstract_reviewers r
        JOIN events.principals p ON r.user_id = p.user_id AND r.event_id = p.event_id
        WHERE r.track_id IS NULL
    '''
    for user_id, event_id, permissions in conn.execute(event_reviewers_stmt):
        bisect.insort(permissions, 'review_all_abstracts')
        _update_event_acl_entry(conn, user_id, event_id, permissions)

    event_conveners_stmt = '''
        SELECT c.user_id, c.event_id, p.permissions
        FROM events.track_conveners c
        JOIN events.principals p ON c.user_id = p.user_id AND c.event_id = p.event_id
        WHERE c.track_id IS NULL
    '''
    for user_id, event_id, permissions in conn.execute(event_conveners_stmt):
        bisect.insort(permissions, 'convene_all_abstracts')
        _update_event_acl_entry(conn, user_id, event_id, permissions)


def upgrade():
    op.create_table(
        'track_principals',
        sa.Column('read_access', sa.Boolean(), nullable=False),
        sa.Column('full_access', sa.Boolean(), nullable=False),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('track_id', sa.Integer(), nullable=False, index=True),
        sa.Column('local_group_id', sa.Integer(), nullable=True, index=True),
        sa.Column('mp_group_provider', sa.String(), nullable=True),
        sa.Column('event_role_id', sa.Integer(), nullable=True, index=True),
        sa.Column('mp_group_name', sa.String(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column(
            'type',
            PyIntEnum(PrincipalType, exclude_values={PrincipalType.network}),
            nullable=False,
        ),
        sa.Column('email', sa.String(), nullable=True, index=True),
        sa.CheckConstraint('NOT full_access', name='no_full_access'),
        sa.CheckConstraint('NOT read_access', name='no_read_access'),
        sa.CheckConstraint('email IS NULL OR email = lower(email)', name='lowercase_email'),
        sa.CheckConstraint('read_access OR full_access OR array_length(permissions, 1) IS NOT NULL', name='has_privs'),
        sa.CheckConstraint(
            'type != 1 OR (email IS NULL AND event_role_id IS NULL AND local_group_id IS NULL AND '
            'mp_group_name IS NULL AND mp_group_provider IS NULL AND user_id IS NOT NULL)', name='valid_user'),
        sa.CheckConstraint(
            'type != 2 OR (email IS NULL AND event_role_id IS NULL AND mp_group_name IS NULL AND '
            'mp_group_provider IS NULL AND user_id IS NULL AND local_group_id IS NOT NULL)', name='valid_local_group'),
        sa.CheckConstraint(
            'type != 3 OR (email IS NULL AND event_role_id IS NULL AND local_group_id IS NULL AND '
            'user_id IS NULL AND mp_group_name IS NOT NULL AND mp_group_provider IS NOT NULL)',
            name='valid_multipass_group'
        ),
        sa.CheckConstraint(
            'type != 4 OR (event_role_id IS NULL AND local_group_id IS NULL AND mp_group_name IS NULL AND '
            'mp_group_provider IS NULL AND user_id IS NULL AND email IS NOT NULL)', name='valid_email'),
        sa.CheckConstraint(
            'type != 6 OR (email IS NULL AND local_group_id IS NULL AND mp_group_name IS NULL AND '
            'mp_group_provider IS NULL AND user_id IS NULL AND event_role_id IS NOT NULL)', name='valid_event_role'),
        sa.ForeignKeyConstraint(['event_role_id'], ['events.roles.id']),
        sa.ForeignKeyConstraint(['local_group_id'], ['users.groups.id']),
        sa.ForeignKeyConstraint(['track_id'], ['events.tracks.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events',
    )

    op.create_index(
        None,
        'track_principals',
        ['mp_group_provider', 'mp_group_name'],
        unique=False,
        schema='events',
    )
    op.create_index(
        'ix_uq_track_principals_email',
        'track_principals',
        ['email', 'track_id'],
        unique=True,
        schema='events',
        postgresql_where=sa.text('type = 4'),
    )
    op.create_index(
        'ix_uq_track_principals_local_group',
        'track_principals',
        ['local_group_id', 'track_id'],
        unique=True,
        schema='events',
        postgresql_where=sa.text('type = 2'),
    )
    op.create_index(
        'ix_uq_track_principals_mp_group',
        'track_principals',
        ['mp_group_provider', 'mp_group_name', 'track_id'],
        unique=True,
        schema='events',
        postgresql_where=sa.text('type = 3'),
    )
    op.create_index(
        'ix_uq_track_principals_user',
        'track_principals',
        ['user_id', 'track_id'],
        unique=True,
        schema='events',
        postgresql_where=sa.text('type = 1'),
    )

    _upgrade_permissions()

    op.drop_table('track_conveners', schema='events')
    op.drop_table('track_abstract_reviewers', schema='events')


def _create_abstract_reviewers_entry(conn, user_id, track_id=None, event_id=None):
    conn.execute('''
        INSERT INTO events.track_abstract_reviewers
        (user_id, track_id, event_id) VALUES
        (%s,       %s,      %s)
    ''', (user_id, track_id, event_id))


def _create_conveners_entry(conn, user_id, track_id=None, event_id=None):
    conn.execute('''
        INSERT INTO events.track_conveners
        (user_id, track_id, event_id) VALUES
        (%s,       %s,      %s)
    ''', (user_id, track_id, event_id))


def _downgrade_permissions():
    conn = op.get_bind()
    query_track_permissions = 'SELECT user_id, track_id, permissions FROM events.track_principals'
    for user_id, track_id, permissions in conn.execute(query_track_permissions):
        if 'review' in permissions:
            _create_abstract_reviewers_entry(conn, user_id, track_id=track_id)
        if 'convene' in permissions:
            _create_conveners_entry(conn, user_id, track_id=track_id)
    query_event_permissions = '''
        SELECT user_id, event_id, permissions FROM events.principals
        WHERE permissions && ARRAY['review_all_abstracts', 'convene_all_abstracts']::character varying[];
    '''
    for user_id, event_id, permissions in conn.execute(query_event_permissions):
        if 'review_all_abstracts' in permissions:
            _create_abstract_reviewers_entry(conn, user_id, event_id=event_id)
        if 'convene_all_abstracts' in permissions:
            _create_conveners_entry(conn, user_id, event_id=event_id)
        updated_permissions = [
            str(permission)
            for permission in permissions
            if permission not in ('review_all_abstracts', 'convene_all_abstracts')
        ]
        _update_event_acl_entry(conn, user_id, event_id, updated_permissions)


def downgrade():
    op.create_table(
        'track_abstract_reviewers',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, autoincrement=False, index=True),
        sa.Column('event_id', sa.Integer(), nullable=True, autoincrement=False, index=True),
        sa.Column('track_id', sa.Integer(), nullable=True, autoincrement=False, index=True),
        sa.ForeignKeyConstraint(['track_id'], ['events.tracks.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('(track_id IS NULL) != (event_id IS NULL)', name='track_xor_event_id_null'),
        schema='events'
    )

    op.create_table(
        'track_conveners',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, autoincrement=False, index=True),
        sa.Column('event_id', sa.Integer(), nullable=True, autoincrement=False, index=True),
        sa.Column('track_id', sa.Integer(), nullable=True, autoincrement=False, index=True),
        sa.ForeignKeyConstraint(['track_id'], ['events.tracks.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('(track_id IS NULL) != (event_id IS NULL)', name='track_xor_event_id_null'),
        schema='events'
    )
    _downgrade_permissions()
    op.drop_table('track_principals', schema='events')
