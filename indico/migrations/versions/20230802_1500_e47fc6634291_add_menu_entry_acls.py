"""Add menu entry ACLs

Revision ID: e47fc6634291
Revises: aba7935f9226
Create Date: 2023-03-06 09:05:08.848298
"""

from enum import Enum

import sqlalchemy as sa
from alembic import context, op

from indico.core.db.sqlalchemy import PyIntEnum


# revision identifiers, used by Alembic.
revision = 'e47fc6634291'
down_revision = 'aba7935f9226'
branch_labels = None
depends_on = None


class _ProtectionMode(int, Enum):
    public = 0
    inheriting = 1
    protected = 2


class _PrincipalType(int, Enum):
    user = 1
    local_group = 2
    multipass_group = 3
    email = 4
    network = 5
    event_role = 6
    category_role = 7
    registration_form = 8


class _MenuEntryAccess(int, Enum):
    everyone = 1
    registered_participants = 2
    speakers = 3


class _MenuEntryType(int, Enum):
    separator = 1
    internal_link = 2
    user_link = 3
    plugin_link = 4
    page = 5


def _upgrade_access_data():
    """
    Upgrade the access column to protection_mode, speaker_allowed, and the principals.

    Here is the mapping:
        access                  || protection_mode | speaker_allowed | menu_entry_principals
        ========================++=================+=================+===========================
        everyone                ||  inheriting     |   false         | none set
        ------------------------++-----------------+-----------------+---------------------------
        registered_participants ||  protected      |   false         | One reg principal for each
                                ||                 |                 | regform in the event
        ------------------------++-----------------+-----------------+---------------------------
        speakers                ||  protected      |   true          | none set
    """
    conn = op.get_bind()

    # Update access mode to protected for registered_participants and speakers
    conn.execute(
        sa.text('UPDATE events.menu_entries SET protection_mode = :protected WHERE access != :everyone'),
        protected=_ProtectionMode.protected.value,
        everyone=_MenuEntryAccess.everyone.value,
    )

    # Migrate "Registered participants" to principal entries for each registration form
    conn.execute(
        sa.text(
            '''
               INSERT INTO events.menu_entry_principals(menu_entry_id, type, registration_form_id)
                    SELECT me.id AS menu_entry_id,
                           :principal_type AS type,
                           frm.id AS registration_form_id
                      FROM events.menu_entries me
          RIGHT OUTER JOIN event_registration.forms frm ON me.event_id = frm.event_id
                     WHERE me.type NOT IN (:internal_link, :separator)
                       AND me.access = :registered
            '''
        ),
        principal_type=_PrincipalType.registration_form.value,
        internal_link=_MenuEntryType.internal_link.value,
        separator=_MenuEntryType.separator.value,
        registered=_MenuEntryAccess.registered_participants.value,
    )

    # Migrate "Speaker" access to allowing speaker access, unless we've already provided broader
    # access for registered participants
    conn.execute(
        sa.text(
            '''
                    UPDATE events.menu_entries
                       SET speaker_allowed = TRUE
                     WHERE access = :speakers
                       AND id NOT IN (
                         SELECT menu_entry_id AS id
                           FROM events.menu_entry_principals mep
                          WHERE mep.type = :regform
                       )
            '''
        ),
        speakers=_MenuEntryAccess.speakers.value,
        regform=_PrincipalType.registration_form.value,
    )


def _downgrade_access_data():
    """
    Downgrade the protection_mode, speaker_allowed and principals to the access column. This isn't
    lossless given the new feature is more fine-grained, but best effort.

    Here is the mapping:

         protection_mode | speaker_allowed | menu_entry_principals     || access
        =================+=================+===========================++========================
          protected      | true            | doesn't contain regform   ||  speakers
                         |                 | principals                ||
        -----------------+-----------------+---------------------------++------------------------
          inheriting     |                 | doesn't contain regform   ||  speakers
        parent=protected | parent=true     | principals                ||
        -----------------+-----------------+---------------------------++------------------------
          protected      | regardless      | at least one regform      ||  registered_participants
                         |                 | principal                 ||
        -----------------+-----------------+---------------------------++------------------------
          inheriting     | regardless      | parent has at least one   ||  registered_participants
                         |                 | regform principal         ||
        -----------------+-----------------+---------------------------++------------------------
          protected      | false           | doesn't contain regform   ||  everyone
                         |                 | principals                ||  (no good mapping)
        -----------------+-----------------+---------------------------++------------------------
          inheriting     | false           | doesn't contain regform   ||  everyone
                         |                 | principals                ||
        -----------------+-----------------+---------------------------++------------------------
          all other combinations                                       ||  everyone
                                                                       ||  (no good mapping)
        -----------------+-----------------+---------------------------++------------------------
    """
    conn = op.get_bind()

    # The server_default is set to give everyone access to all menu entries. We need to restrict
    # those appropriately now. Start with locking down for speakers, and then open up to registered
    # participants if applicable

    # Any menu entry that is accessible to speakers should only be open to speakers. If it is also
    # open to registrants, we'll expand this later on.
    conn.execute(
        sa.text(
            '''
                    UPDATE events.menu_entries
                       SET access = :speakers
                     WHERE speaker_allowed = TRUE
                       AND protection_mode = :protected
            '''
        ),
        speakers=_MenuEntryAccess.speakers.value,
        protected=_ProtectionMode.protected.value
    )

    # Inheriting menu entries with the parent accessible to speakers should be only open to
    # speakers. Again expanding to others later on.
    conn.execute(
        sa.text(
            '''
                    UPDATE events.menu_entries
                       SET access = :speakers
                     WHERE menu_entries.id IN (
                                      SELECT me.id
                                        FROM events.menu_entries me
                             LEFT OUTER JOIN events.menu_entries parent_me ON me.parent_id = parent_me.id
                                       WHERE me.type NOT IN (:internal_link, :separator)
                                         AND me.parent_id IS NOT NULL
                                         AND me.protection_mode = :inheriting
                                         AND parent_me.protection_mode = :protected
                                         AND parent_me.speaker_allowed = TRUE
                    )

            '''
        ),
        speakers=_MenuEntryAccess.speakers.value,
        internal_link=_MenuEntryType.internal_link.value,
        separator=_MenuEntryType.separator.value,
        inheriting=_ProtectionMode.inheriting.value,
        protected=_ProtectionMode.protected.value,
    )

    # Any menu entry that has a registration attached to it should be registered participants only,
    # provided its protection mode is set to protected
    conn.execute(
        sa.text(
            '''
                    UPDATE events.menu_entries
                       SET access = :registered
                     WHERE menu_entries.id IN (
                             SELECT menu_entry_id
                               FROM events.menu_entry_principals
                              WHERE type = :regform
                           )
                       AND protection_mode = :protected
            '''
        ),
        registered=_MenuEntryAccess.registered_participants.value,
        regform=_PrincipalType.registration_form.value,
        protected=_ProtectionMode.protected.value,
    )

    # Menu entries that are inheriting with their parent set to protected and containing
    # registrations get the same treatment
    conn.execute(
        sa.text(
            '''
                    UPDATE events.menu_entries
                       SET access = :registered
                     WHERE id IN (
                                      SELECT me.id
                                        FROM events.menu_entries me
                             LEFT OUTER JOIN events.menu_entries parent_me ON me.parent_id = parent_me.id
                            RIGHT OUTER JOIN events.menu_entry_principals mep ON mep.menu_entry_id = parent_me.id
                                       WHERE me.type NOT IN (:internal_link, :separator)
                                         AND me.parent_id IS NOT NULL
                                         AND me.protection_mode = :inheriting
                                         AND parent_me.protection_mode = :protected
                                         AND mep.type = :regform
                           )
            '''
        ),
        registered=_MenuEntryAccess.registered_participants.value,
        internal_link=_MenuEntryType.internal_link.value,
        separator=_MenuEntryType.separator.value,
        inheriting=_ProtectionMode.inheriting.value,
        protected=_ProtectionMode.protected.value,
        regform=_PrincipalType.registration_form.value,
    )


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')

    # Principals table
    op.create_table(
        'menu_entry_principals',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('menu_entry_id', sa.Integer(), nullable=False),
        sa.Column('type', PyIntEnum(_PrincipalType, exclude_values={_PrincipalType.email, _PrincipalType.network}),
                  nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('local_group_id', sa.Integer(), nullable=True),
        sa.Column('mp_group_provider', sa.String(), nullable=True),
        sa.Column('mp_group_name', sa.String(), nullable=True),
        sa.Column('event_role_id', sa.Integer(), nullable=True),
        sa.Column('category_role_id', sa.Integer(), nullable=True),
        sa.Column('registration_form_id', sa.Integer(), nullable=True),
        sa.CheckConstraint(
            'type != 1 OR (category_role_id IS NULL AND event_role_id IS NULL AND local_group_id IS NULL AND '
            'mp_group_name IS NULL AND mp_group_provider IS NULL AND registration_form_id IS NULL AND '
            'user_id IS NOT NULL)',
            name='valid_user',
        ),
        sa.CheckConstraint(
            'type != 2 OR (category_role_id IS NULL AND event_role_id IS NULL AND mp_group_name IS NULL AND '
            'mp_group_provider IS NULL AND registration_form_id IS NULL AND user_id IS NULL AND '
            'local_group_id IS NOT NULL)',
            name='valid_local_group',
        ),
        sa.CheckConstraint(
            'type != 3 OR (category_role_id IS NULL AND event_role_id IS NULL AND local_group_id IS NULL AND '
            'registration_form_id IS NULL AND user_id IS NULL AND mp_group_name IS NOT NULL AND '
            'mp_group_provider IS NOT NULL)',
            name='valid_multipass_group',
        ),
        sa.CheckConstraint(
            'type != 6 OR (category_role_id IS NULL AND local_group_id IS NULL AND mp_group_name IS NULL AND '
            'mp_group_provider IS NULL AND registration_form_id IS NULL AND user_id IS NULL AND '
            'event_role_id IS NOT NULL)',
            name='valid_event_role',
        ),
        sa.CheckConstraint(
            'type != 7 OR (event_role_id IS NULL AND local_group_id IS NULL AND mp_group_name IS NULL AND '
            'mp_group_provider IS NULL AND registration_form_id IS NULL AND user_id IS NULL AND '
            'category_role_id IS NOT NULL)',
            name='valid_category_role',
        ),
        sa.CheckConstraint(
            'type != 8 OR (category_role_id IS NULL AND event_role_id IS NULL AND local_group_id IS NULL AND '
            'mp_group_name IS NULL AND mp_group_provider IS NULL AND user_id IS NULL AND '
            'registration_form_id IS NOT NULL)',
            name='valid_registration_form',
        ),
        sa.ForeignKeyConstraint(['category_role_id'], ['categories.roles.id']),
        sa.ForeignKeyConstraint(['event_role_id'], ['events.roles.id']),
        sa.ForeignKeyConstraint(['local_group_id'], ['users.groups.id']),
        sa.ForeignKeyConstraint(['menu_entry_id'], ['events.menu_entries.id']),
        sa.ForeignKeyConstraint(['registration_form_id'], ['event_registration.forms.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        schema='events',
    )
    op.create_index(None, 'menu_entry_principals', ['category_role_id'], schema='events')
    op.create_index(None, 'menu_entry_principals', ['event_role_id'], schema='events')
    op.create_index(None, 'menu_entry_principals', ['local_group_id'], schema='events')
    op.create_index(None, 'menu_entry_principals', ['mp_group_provider', 'mp_group_name'], schema='events')
    op.create_index(None, 'menu_entry_principals', ['registration_form_id'], schema='events')
    op.create_index(None, 'menu_entry_principals', ['user_id'], schema='events')
    op.create_index(
        'ix_uq_menu_entry_principals_local_group',
        'menu_entry_principals', ['local_group_id', 'menu_entry_id'],
        unique=True, schema='events', postgresql_where=sa.text('type = 2')
    )
    op.create_index(
        'ix_uq_menu_entry_principals_mp_group',
        'menu_entry_principals', ['mp_group_provider', 'mp_group_name', 'menu_entry_id'],
        unique=True, schema='events', postgresql_where=sa.text('type = 3')
    )
    op.create_index(
        'ix_uq_menu_entry_principals_user',
        'menu_entry_principals', ['user_id', 'menu_entry_id'],
        unique=True, schema='events', postgresql_where=sa.text('type = 1')
    )

    # Menu entries columns - protection_mode, speaker_allowed
    op.add_column(
        'menu_entries',
        sa.Column('protection_mode', PyIntEnum(_ProtectionMode, exclude_values={_ProtectionMode.public}),
                  nullable=False, server_default=str(_ProtectionMode.inheriting.value)),
        schema='events',
    )
    op.add_column(
        'menu_entries',
        sa.Column('speaker_allowed', sa.Boolean(), nullable=False, server_default='false'),
        schema='events'
    )
    op.alter_column('menu_entries', 'speaker_allowed', server_default=None, schema='events')
    op.alter_column('menu_entries', 'protection_mode', server_default=None, schema='events')

    # Migrate data
    _upgrade_access_data()

    # Clear access column
    op.drop_column('menu_entries', 'access', schema='events')


def downgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')

    # Add back access column
    op.add_column(
        'menu_entries',
        sa.Column('access', PyIntEnum(_MenuEntryAccess), nullable=False,
                  server_default=str(_MenuEntryAccess.everyone.value)),
        schema='events'
    )
    op.alter_column('menu_entries', 'access', server_default=None, schema='events')

    # Unmigrate data
    _downgrade_access_data()

    # Drop menu entries columns - protection_mode, speaker_allowed
    op.drop_column('menu_entries', 'speaker_allowed', schema='events')
    op.drop_column('menu_entries', 'protection_mode', schema='events')

    # Drop menu_entry_principals
    op.drop_table('menu_entry_principals', schema='events')
