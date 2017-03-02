"""Add contribution related tables

Revision ID: 225d0750c216
Revises: 212f3acb0b1f
Create Date: 2015-11-23 13:47:20.479122
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.users.models.users import UserTitle


# revision identifiers, used by Alembic.
revision = '225d0750c216'
down_revision = '212f3acb0b1f'


def upgrade():
    # ContributionField
    op.create_table(
        'contribution_fields',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('legacy_id', sa.String(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('field_type', sa.String(), nullable=True),
        sa.Column('field_data', pg.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.UniqueConstraint('event_id', 'legacy_id'),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )

    # ReferenceType
    op.create_table(
        'reference_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('scheme', sa.String(), nullable=False),
        sa.Column('url_template', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='indico'
    )
    op.create_index('ix_uq_reference_types_name_lower', 'reference_types', [sa.text('lower(name)')], unique=True,
                    schema='indico')

    # Session
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('friendly_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('default_contribution_duration', sa.Interval(), nullable=False),
        sa.Column('is_poster', sa.Boolean(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('text_color', sa.String(), nullable=False),
        sa.Column('background_color', sa.String(), nullable=False),
        sa.Column('protection_mode', PyIntEnum(ProtectionMode), nullable=False),
        sa.Column('room_name', sa.String(), nullable=False),
        sa.Column('inherit_location', sa.Boolean(), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('venue_id', sa.Integer(), nullable=True, index=True),
        sa.Column('venue_name', sa.String(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=True, index=True),
        sa.CheckConstraint("(room_id IS NULL) OR (venue_name = '' AND room_name = '')",
                           name='no_custom_location_if_room'),
        sa.CheckConstraint("(venue_id IS NULL) OR (venue_name = '')", name='no_venue_name_if_venue_id'),
        sa.CheckConstraint("(room_id IS NULL) OR (venue_id IS NOT NULL)", name='venue_id_if_room_id'),
        sa.CheckConstraint("NOT inherit_location OR (venue_id IS NULL AND room_id IS NULL AND venue_name = '' AND "
                           "room_name = '' AND address = '')", name='inherited_location'),
        sa.CheckConstraint("(text_color = '') = (background_color = '')", name='both_or_no_colors'),
        sa.CheckConstraint("text_color != '' AND background_color != ''", name='colors_not_empty'),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['room_id'], ['roombooking.rooms.id']),
        sa.ForeignKeyConstraint(['venue_id'], ['roombooking.locations.id']),
        sa.ForeignKeyConstraint(['venue_id', 'room_id'], ['roombooking.rooms.location_id', 'roombooking.rooms.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )

    # SessionPrincipal
    op.create_table(
        'session_principals',
        sa.Column('mp_group_provider', sa.String(), nullable=True),
        sa.Column('mp_group_name', sa.String(), nullable=True),
        sa.Column('read_access', sa.Boolean(), nullable=False),
        sa.Column('full_access', sa.Boolean(), nullable=False),
        sa.Column('roles', pg.ARRAY(sa.String()), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False, index=True),
        sa.Column('local_group_id', sa.Integer(), nullable=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('type', PyIntEnum(PrincipalType), nullable=True),
        sa.Column('email', sa.String(), nullable=True, index=True),
        sa.CheckConstraint('email IS NULL OR email = lower(email)', name='lowercase_email'),
        sa.CheckConstraint('read_access OR full_access OR array_length(roles, 1) IS NOT NULL', name='has_privs'),
        sa.CheckConstraint('type != 1 OR (local_group_id IS NULL AND mp_group_provider IS NULL AND email IS NULL AND '
                           'mp_group_name IS NULL AND user_id IS NOT NULL)', name='valid_user'),
        sa.CheckConstraint('type != 2 OR (user_id IS NULL AND mp_group_provider IS NULL AND email IS NULL AND '
                           'mp_group_name IS NULL AND local_group_id IS NOT NULL)',
                           name='valid_local_group'),
        sa.CheckConstraint('type != 3 OR (local_group_id IS NULL AND user_id IS NULL AND email IS NULL AND '
                           'mp_group_provider IS NOT NULL AND mp_group_name IS NOT NULL)',
                           name='valid_multipass_group'),
        sa.CheckConstraint('type != 4 OR (local_group_id IS NULL AND mp_group_provider IS NULL AND '
                           'mp_group_name IS NULL AND user_id IS NULL AND email IS NOT NULL)', name='valid_email'),
        sa.ForeignKeyConstraint(['local_group_id'], ['users.groups.id']),
        sa.ForeignKeyConstraint(['session_id'], ['events.sessions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_index(None, 'session_principals', ['mp_group_provider', 'mp_group_name'], schema='events')
    op.create_index('ix_uq_session_principals_email', 'session_principals', ['email', 'session_id'],
                    unique=True, schema='events', postgresql_where=sa.text('type = 4'))
    op.create_index('ix_uq_session_principals_local_group', 'session_principals', ['local_group_id', 'session_id'],
                    unique=True, schema='events', postgresql_where=sa.text('type = 2'))
    op.create_index('ix_uq_session_principals_mp_group', 'session_principals',
                    ['mp_group_provider', 'mp_group_name', 'session_id'], unique=True, schema='events',
                    postgresql_where=sa.text('type = 3'))
    op.create_index('ix_uq_session_principals_user', 'session_principals', ['user_id', 'session_id'], unique=True,
                    schema='events', postgresql_where=sa.text('type = 1'))

    # SessionBlock
    op.create_table(
        'session_blocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('duration', sa.Interval(), nullable=False),
        sa.Column('room_name', sa.String(), nullable=False),
        sa.Column('inherit_location', sa.Boolean(), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('venue_id', sa.Integer(), nullable=True, index=True),
        sa.Column('venue_name', sa.String(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=True, index=True),
        sa.CheckConstraint("(room_id IS NULL) OR (venue_name = '' AND room_name = '')",
                           name='no_custom_location_if_room'),
        sa.CheckConstraint("(venue_id IS NULL) OR (venue_name = '')", name='no_venue_name_if_venue_id'),
        sa.CheckConstraint("(room_id IS NULL) OR (venue_id IS NOT NULL)", name='venue_id_if_room_id'),
        sa.CheckConstraint("NOT inherit_location OR (venue_id IS NULL AND room_id IS NULL AND venue_name = '' AND "
                           "room_name = '' AND address = '')", name='inherited_location'),
        sa.ForeignKeyConstraint(['room_id'], ['roombooking.rooms.id']),
        sa.ForeignKeyConstraint(['venue_id'], ['roombooking.locations.id']),
        sa.ForeignKeyConstraint(['venue_id', 'room_id'], ['roombooking.rooms.location_id', 'roombooking.rooms.id']),
        sa.ForeignKeyConstraint(['session_id'], ['events.sessions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id', 'session_id'),
        schema='events'
    )

    # ContributionType
    op.create_table(
        'contribution_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_index('ix_uq_contribution_types_event_id_name_lower', 'contribution_types',
                    ['event_id', sa.text('lower(name)')], unique=True, schema='events')

    # Contribution
    op.create_table(
        'contributions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('friendly_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('session_id', sa.Integer(), nullable=True, index=True),
        sa.Column('session_block_id', sa.Integer(), nullable=True, index=True),
        sa.Column('track_id', sa.Integer(), nullable=True),
        sa.Column('abstract_id', sa.Integer(), nullable=True, index=True),
        sa.Column('type_id', sa.Integer(), nullable=True, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('duration', sa.Interval(), nullable=False),
        sa.Column('board_number', sa.String(), nullable=False),
        sa.Column('keywords', pg.ARRAY(sa.String()), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('last_friendly_subcontribution_id', sa.Integer(), nullable=False),
        sa.Column('protection_mode', PyIntEnum(ProtectionMode), nullable=False),
        sa.Column('room_name', sa.String(), nullable=False),
        sa.Column('inherit_location', sa.Boolean(), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('venue_id', sa.Integer(), nullable=True, index=True),
        sa.Column('venue_name', sa.String(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=True, index=True),
        sa.CheckConstraint("session_block_id IS NULL OR session_id IS NOT NULL",
                           name='session_block_if_session'),
        sa.CheckConstraint("(room_id IS NULL) OR (venue_name = '' AND room_name = '')",
                           name='no_custom_location_if_room'),
        sa.CheckConstraint("(venue_id IS NULL) OR (venue_name = '')", name='no_venue_name_if_venue_id'),
        sa.CheckConstraint("(room_id IS NULL) OR (venue_id IS NOT NULL)", name='venue_id_if_room_id'),
        sa.CheckConstraint("NOT inherit_location OR (venue_id IS NULL AND room_id IS NULL AND venue_name = '' AND "
                           "room_name = '' AND address = '')", name='inherited_location'),
        sa.Index(None, 'abstract_id', unique=True, postgresql_where=sa.text("NOT is_deleted")),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['room_id'], ['roombooking.rooms.id']),
        sa.ForeignKeyConstraint(['venue_id'], ['roombooking.locations.id']),
        sa.ForeignKeyConstraint(['venue_id', 'room_id'], ['roombooking.rooms.location_id', 'roombooking.rooms.id']),
        sa.ForeignKeyConstraint(['session_block_id', 'session_id'],
                                ['events.session_blocks.id', 'events.session_blocks.session_id']),
        sa.ForeignKeyConstraint(['session_block_id'], ['events.session_blocks.id']),
        sa.ForeignKeyConstraint(['session_id'], ['events.sessions.id']),
        sa.ForeignKeyConstraint(['type_id'], ['events.contribution_types.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_index(None, 'contributions', ['event_id', 'track_id'], schema='events')
    op.create_index(None, 'contributions', ['event_id', 'abstract_id'], schema='events')
    op.create_index(None, 'contributions', ['friendly_id', 'event_id'], unique=True, schema='events')

    # ContributionPrincipal
    op.create_table(
        'contribution_principals',
        sa.Column('mp_group_provider', sa.String(), nullable=True),
        sa.Column('mp_group_name', sa.String(), nullable=True),
        sa.Column('read_access', sa.Boolean(), nullable=False),
        sa.Column('full_access', sa.Boolean(), nullable=False),
        sa.Column('roles', pg.ARRAY(sa.String()), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contribution_id', sa.Integer(), nullable=False, index=True),
        sa.Column('local_group_id', sa.Integer(), nullable=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('type', PyIntEnum(PrincipalType), nullable=True),
        sa.Column('email', sa.String(), nullable=True, index=True),
        sa.CheckConstraint('email IS NULL OR email = lower(email)', name='lowercase_email'),
        sa.CheckConstraint('read_access OR full_access OR array_length(roles, 1) IS NOT NULL', name='has_privs'),
        sa.CheckConstraint('type != 1 OR (local_group_id IS NULL AND mp_group_provider IS NULL AND email IS NULL AND '
                           'mp_group_name IS NULL AND user_id IS NOT NULL)', name='valid_user'),
        sa.CheckConstraint('type != 2 OR (user_id IS NULL AND mp_group_provider IS NULL AND email IS NULL AND '
                           'mp_group_name IS NULL AND local_group_id IS NOT NULL)',
                           name='valid_local_group'),
        sa.CheckConstraint('type != 3 OR (local_group_id IS NULL AND user_id IS NULL AND email IS NULL AND '
                           'mp_group_provider IS NOT NULL AND mp_group_name IS NOT NULL)',
                           name='valid_multipass_group'),
        sa.CheckConstraint('type != 4 OR (local_group_id IS NULL AND mp_group_provider IS NULL AND '
                           'mp_group_name IS NULL AND user_id IS NULL AND email IS NOT NULL)', name='valid_email'),
        sa.ForeignKeyConstraint(['contribution_id'], ['events.contributions.id']),
        sa.ForeignKeyConstraint(['local_group_id'], ['users.groups.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_index(None, 'contribution_principals', ['mp_group_provider', 'mp_group_name'], schema='events')
    op.create_index('ix_uq_contribution_principals_email', 'contribution_principals', ['email', 'contribution_id'],
                    unique=True, schema='events', postgresql_where=sa.text('type = 4'))
    op.create_index('ix_uq_contribution_principals_local_group', 'contribution_principals',
                    ['local_group_id', 'contribution_id'], unique=True, schema='events',
                    postgresql_where=sa.text('type = 2'))
    op.create_index('ix_uq_contribution_principals_mp_group', 'contribution_principals',
                    ['mp_group_provider', 'mp_group_name', 'contribution_id'], unique=True, schema='events',
                    postgresql_where=sa.text('type = 3'))
    op.create_index('ix_uq_contribution_principals_user', 'contribution_principals', ['user_id', 'contribution_id'],
                    unique=True, schema='events', postgresql_where=sa.text('type = 1'))

    # ContributionFieldValue
    op.create_table(
        'contribution_field_values',
        sa.Column('data', pg.JSON(), nullable=False),
        sa.Column('contribution_id', sa.Integer(), nullable=False, index=True),
        sa.Column('contribution_field_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['contribution_field_id'], ['events.contribution_fields.id'],
                                name='fk_contribution_field_values_contribution_field'),
        sa.ForeignKeyConstraint(['contribution_id'], ['events.contributions.id']),
        sa.PrimaryKeyConstraint('contribution_id', 'contribution_field_id'),
        schema='events'
    )

    # SubContribution
    op.create_table(
        'subcontributions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('friendly_id', sa.Integer(), nullable=False),
        sa.Column('contribution_id', sa.Integer(), nullable=False, index=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('duration', sa.Interval(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['contribution_id'], ['events.contributions.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_index(None, 'subcontributions', ['friendly_id', 'contribution_id'], unique=True, schema='events')

    # SubContributionReference
    op.create_table(
        'subcontribution_references',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('subcontribution_id', sa.Integer(), nullable=False, index=True),
        sa.Column('reference_type_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['reference_type_id'], ['indico.reference_types.id']),
        sa.ForeignKeyConstraint(['subcontribution_id'], ['events.subcontributions.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )

    # ContributionReference
    op.create_table(
        'contribution_references',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('contribution_id', sa.Integer(), nullable=False, index=True),
        sa.Column('reference_type_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['contribution_id'], ['events.contributions.id']),
        sa.ForeignKeyConstraint(['reference_type_id'], ['indico.reference_types.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )

    # EventReference
    op.create_table(
        'event_references',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('reference_type_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['reference_type_id'], ['indico.reference_types.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )

    # EventPerson
    op.create_table(
        'persons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False, index=True),
        sa.Column('title', PyIntEnum(UserTitle), nullable=False),
        sa.Column('affiliation', sa.String(), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.UniqueConstraint('event_id', 'user_id'),
        sa.CheckConstraint('email = lower(email)', name='lowercase_email'),
        sa.Index(None, 'event_id', 'email', unique=True, postgresql_where=sa.text("email != ''")),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )

    # EventPersonLink
    op.create_table(
        'event_person_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('person_id', sa.Integer(), nullable=False, index=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('title', PyIntEnum(UserTitle), nullable=True),
        sa.Column('affiliation', sa.String(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['person_id'], ['events.persons.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.UniqueConstraint('person_id', 'event_id'),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )

    # SessionBlockPersonLink
    op.create_table(
        'session_block_person_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_block_id', sa.Integer(), nullable=False, index=True),
        sa.Column('person_id', sa.Integer(), nullable=False, index=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('title', PyIntEnum(UserTitle), nullable=True),
        sa.Column('affiliation', sa.String(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['person_id'], ['events.persons.id']),
        sa.ForeignKeyConstraint(['session_block_id'], ['events.session_blocks.id']),
        sa.UniqueConstraint('person_id', 'session_block_id'),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )

    # ContributionPersonLink
    op.create_table(
        'contribution_person_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contribution_id', sa.Integer(), nullable=False, index=True),
        sa.Column('person_id', sa.Integer(), nullable=False, index=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('title', PyIntEnum(UserTitle), nullable=True),
        sa.Column('affiliation', sa.String(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('is_speaker', sa.Boolean(), nullable=False),
        sa.Column('author_type', PyIntEnum(AuthorType), nullable=False),
        sa.ForeignKeyConstraint(['contribution_id'], ['events.contributions.id']),
        sa.ForeignKeyConstraint(['person_id'], ['events.persons.id']),
        sa.UniqueConstraint('person_id', 'contribution_id'),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )

    # SubContributionPersonLink
    op.create_table(
        'subcontribution_person_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subcontribution_id', sa.Integer(), nullable=False, index=True),
        sa.Column('person_id', sa.Integer(), nullable=False, index=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('title', PyIntEnum(UserTitle), nullable=True),
        sa.Column('affiliation', sa.String(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['person_id'], ['events.persons.id']),
        sa.ForeignKeyConstraint(['subcontribution_id'], ['events.subcontributions.id']),
        sa.UniqueConstraint('person_id', 'subcontribution_id'),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )

    # LegacyContributionMapping
    op.create_table(
        'legacy_contribution_id_map',
        sa.Column('event_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('legacy_contribution_id', sa.String(), nullable=False),
        sa.Column('contribution_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['contribution_id'], ['events.contributions.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('event_id', 'legacy_contribution_id'),
        schema='events'
    )

    # LegacySubContributionMapping
    op.create_table(
        'legacy_subcontribution_id_map',
        sa.Column('event_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('legacy_contribution_id', sa.String(), nullable=False),
        sa.Column('legacy_subcontribution_id', sa.String(), nullable=False),
        sa.Column('subcontribution_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['subcontribution_id'], ['events.subcontributions.id'],
                                name='fk_legacy_subcontribution_id_map_subcontribution'),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('event_id', 'legacy_contribution_id', 'legacy_subcontribution_id'),
        schema='events'
    )

    # LegacySessionMapping
    op.create_table(
        'legacy_session_id_map',
        sa.Column('event_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('legacy_session_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['session_id'], ['events.sessions.id']),
        sa.PrimaryKeyConstraint('event_id', 'legacy_session_id'),
        schema='events'
    )

    # LegacySessionBlockMapping
    op.create_table(
        'legacy_session_block_id_map',
        sa.Column('event_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('legacy_session_id', sa.String(), nullable=False),
        sa.Column('legacy_session_block_id', sa.String(), nullable=False),
        sa.Column('session_block_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['session_block_id'], ['events.session_blocks.id']),
        sa.PrimaryKeyConstraint('event_id', 'legacy_session_id', 'legacy_session_block_id'),
        schema='events'
    )

    # New event columns
    op.add_column('events',
                  sa.Column('last_friendly_contribution_id', sa.Integer(), nullable=False, server_default='0'),
                  schema='events')
    op.add_column('events',
                  sa.Column('last_friendly_session_id', sa.Integer(), nullable=False, server_default='0'),
                  schema='events')
    op.alter_column('events', 'last_friendly_contribution_id', server_default=None, schema='events')
    op.alter_column('events', 'last_friendly_session_id', server_default=None, schema='events')


def downgrade():
    op.drop_column('events', 'last_friendly_session_id', schema='events')
    op.drop_column('events', 'last_friendly_contribution_id', schema='events')
    op.drop_table('legacy_session_block_id_map', schema='events')
    op.drop_table('legacy_session_id_map', schema='events')
    op.drop_table('legacy_contribution_id_map', schema='events')
    op.drop_table('legacy_subcontribution_id_map', schema='events')
    op.drop_table('subcontribution_person_links', schema='events')
    op.drop_table('contribution_person_links', schema='events')
    op.drop_table('session_block_person_links', schema='events')
    op.drop_table('event_person_links', schema='events')
    op.drop_table('persons', schema='events')
    op.drop_table('event_references', schema='events')
    op.drop_table('contribution_references', schema='events')
    op.drop_table('subcontribution_references', schema='events')
    op.drop_table('subcontributions', schema='events')
    op.drop_table('contribution_field_values', schema='events')
    op.drop_table('contribution_principals', schema='events')
    op.drop_table('contributions', schema='events')
    op.drop_table('contribution_types', schema='events')
    op.drop_table('session_blocks', schema='events')
    op.drop_table('session_principals', schema='events')
    op.drop_table('sessions', schema='events')
    op.drop_table('reference_types', schema='indico')
    op.drop_table('contribution_fields', schema='events')
