"""Add registration tables

Revision ID: f9bb2a03ceb
Revises: 13480f6da0e2
Create Date: 2015-09-04 15:15:03.682231
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.ddl import CreateSchema, DropSchema

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.modules.events.registration.models.invitations import InvitationState
from indico.modules.events.registration.models.items import RegistrationFormItemType, PersonalDataType
from indico.modules.events.registration.models.forms import ModificationMode
from indico.modules.events.registration.models.registrations import RegistrationState


# revision identifiers, used by Alembic.
revision = 'f9bb2a03ceb'
down_revision = '13480f6da0e2'


def upgrade():
    op.execute(CreateSchema('event_registration'))
    op.create_table(
        'forms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('introduction', sa.Text(), nullable=False),
        sa.Column('contact_info', sa.String(), nullable=False),
        sa.Column('start_dt', UTCDateTime, nullable=True),
        sa.Column('end_dt', UTCDateTime, nullable=True),
        sa.Column('modification_mode', PyIntEnum(ModificationMode), nullable=False),
        sa.Column('modification_end_dt', UTCDateTime, nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('require_login', sa.Boolean(), nullable=False),
        sa.Column('require_user', sa.Boolean(), nullable=False),
        sa.Column('tickets_enabled', sa.Boolean(), nullable=False),
        sa.Column('ticket_on_email', sa.Boolean(), nullable=False),
        sa.Column('ticket_on_event_page', sa.Boolean(), nullable=False),
        sa.Column('ticket_on_summary_page', sa.Boolean(), nullable=False),
        sa.Column('registration_limit', sa.Integer(), nullable=True),
        sa.Column('publish_registrations_enabled', sa.Boolean(), nullable=False),
        sa.Column('moderation_enabled', sa.Boolean(), nullable=False),
        sa.Column('base_price', sa.Numeric(8, 2), nullable=False),
        sa.Column('notification_sender_address', sa.String(), nullable=True),
        sa.Column('message_pending', sa.Text(), nullable=False),
        sa.Column('message_unpaid', sa.Text(), nullable=False),
        sa.Column('message_complete', sa.Text(), nullable=False),
        sa.Column('manager_notifications_enabled', sa.Boolean(), nullable=False),
        sa.Column('manager_notification_recipients', postgresql.ARRAY(sa.String()), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.UniqueConstraint('id', 'event_id'),
        sa.PrimaryKeyConstraint('id'),
        schema='event_registration'
    )

    op.create_table(
        'form_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('registration_form_id', sa.Integer(), nullable=False, index=True),
        sa.Column('type', PyIntEnum(RegistrationFormItemType), nullable=False),
        sa.Column('personal_data_type', PyIntEnum(PersonalDataType), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True, index=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('is_manager_only', sa.Boolean(), nullable=False),
        sa.Column('input_type', sa.String(), nullable=True),
        sa.Column('data', postgresql.JSON(), nullable=False),
        sa.Column('current_data_id', sa.Integer(), nullable=True, index=True),
        sa.CheckConstraint("(input_type IS NULL) = (type NOT IN (2, 5))", name='valid_input'),
        sa.CheckConstraint("NOT is_manager_only OR type = 1", name='valid_manager_only'),
        sa.CheckConstraint("(type IN (1, 4)) = (parent_id IS NULL)", name='top_level_sections'),
        sa.CheckConstraint("(type != 5) = (personal_data_type IS NULL)", name='pd_field_type'),
        sa.CheckConstraint("NOT is_deleted OR (type NOT IN (4, 5))", name='pd_not_deleted'),
        sa.CheckConstraint("is_enabled OR type != 4", name='pd_section_enabled'),
        sa.CheckConstraint("is_enabled OR type != 5 OR personal_data_type NOT IN (1, 2, 3)", name='pd_field_enabled'),
        sa.CheckConstraint("is_required OR type != 5 OR personal_data_type NOT IN (1, 2, 3)", name='pd_field_required'),
        sa.CheckConstraint("current_data_id IS NULL OR type IN (2, 5)", name='current_data_id_only_field'),
        sa.Index('ix_uq_form_items_pd_section', 'registration_form_id', unique=True,
                 postgresql_where=sa.text('type = 4')),
        sa.Index('ix_uq_form_items_pd_field', 'registration_form_id', 'personal_data_type', unique=True,
                 postgresql_where=sa.text('type = 5')),
        sa.ForeignKeyConstraint(['parent_id'], ['event_registration.form_items.id']),
        sa.ForeignKeyConstraint(['registration_form_id'], ['event_registration.forms.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_registration'
    )

    op.create_table(
        'form_field_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=False, index=True),
        sa.Column('versioned_data', postgresql.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['field_id'], ['event_registration.form_items.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_registration'
    )

    op.create_foreign_key(None,
                          'form_items', 'form_field_data',
                          ['current_data_id'], ['id'],
                          source_schema='event_registration', referent_schema='event_registration')

    op.create_table(
        'registrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('friendly_id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID, nullable=False, index=True, unique=True),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('registration_form_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('transaction_id', sa.Integer(), nullable=True, index=True, unique=True),
        sa.Column('state', PyIntEnum(RegistrationState), nullable=False),
        sa.Column('base_price', sa.Numeric(8, 2), nullable=False),
        sa.Column('price_adjustment', sa.Numeric(8, 2), nullable=False),
        sa.Column('submitted_dt', UTCDateTime, nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('ticket_uuid', postgresql.UUID(), nullable=False, index=True, unique=True),
        sa.Column('checked_in', sa.Boolean(), nullable=False),
        sa.Column('checked_in_dt', UTCDateTime, nullable=True),
        sa.ForeignKeyConstraint(['registration_form_id'], ['event_registration.forms.id']),
        sa.ForeignKeyConstraint(['event_id', 'registration_form_id'],
                                ['event_registration.forms.event_id', 'event_registration.forms.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.CheckConstraint('email = lower(email)', name='lowercase_email'),
        sa.Index(None, 'friendly_id', 'event_id', unique=True),
        sa.Index(None, 'registration_form_id', 'user_id', unique=True,
                 postgresql_where=sa.text('NOT is_deleted AND (state NOT IN (3, 4))')),
        sa.Index(None, 'registration_form_id', 'email', unique=True,
                 postgresql_where=sa.text('NOT is_deleted AND (state NOT IN (3, 4))')),
        sa.PrimaryKeyConstraint('id'),
        schema='event_registration'
    )

    op.create_table(
        'registration_data',
        sa.Column('registration_id', sa.Integer(), nullable=False),
        sa.Column('field_data_id', sa.Integer(), nullable=False),
        sa.Column('data', postgresql.JSONB(), nullable=False),
        sa.Column('filename', sa.String(), nullable=True),
        sa.Column('content_type', sa.String(), nullable=True),
        sa.Column('size', sa.BigInteger(), nullable=True),
        sa.Column('storage_backend', sa.String(), nullable=True),
        sa.Column('storage_file_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['field_data_id'], ['event_registration.form_field_data.id']),
        sa.ForeignKeyConstraint(['registration_id'], ['event_registration.registrations.id']),
        sa.PrimaryKeyConstraint('registration_id', 'field_data_id'),
        schema='event_registration'
    )

    op.create_table(
        'legacy_registration_map',
        sa.Column('event_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('legacy_registrant_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('legacy_registrant_key', sa.String(), nullable=False),
        sa.Column('registration_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['registration_id'], ['event_registration.registrations.id']),
        sa.PrimaryKeyConstraint('event_id', 'legacy_registrant_id'),
        schema='event_registration'
    )

    op.create_table(
        'invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(), nullable=False, index=True, unique=True),
        sa.Column('registration_form_id', sa.Integer(), nullable=False, index=True),
        sa.Column('registration_id', sa.Integer(), nullable=True, index=True, unique=True),
        sa.Column('state', PyIntEnum(InvitationState), nullable=False),
        sa.Column('skip_moderation', sa.Boolean(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('affiliation', sa.String(), nullable=False),
        sa.CheckConstraint('(state = 1) OR (registration_id IS NULL)', name='registration_state'),
        sa.UniqueConstraint('registration_form_id', 'email'),
        sa.ForeignKeyConstraint(['registration_form_id'], ['event_registration.forms.id']),
        sa.ForeignKeyConstraint(['registration_id'], ['event_registration.registrations.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_registration')

    op.add_column('events',
                  sa.Column('last_friendly_registration_id', sa.Integer(), nullable=False, server_default='0'),
                  schema='events')
    op.alter_column('events', 'last_friendly_registration_id', server_default=None, schema='events')


def downgrade():
    op.drop_column('events', 'last_friendly_registration_id', schema='events')
    op.drop_constraint('fk_form_items_current_data_id_form_field_data',
                       'form_items', schema='event_registration')
    op.drop_table('invitations', schema='event_registration')
    op.drop_table('legacy_registration_map', schema='event_registration')
    op.drop_table('registration_data', schema='event_registration')
    op.drop_table('registrations', schema='event_registration')
    op.drop_table('form_field_data', schema='event_registration')
    op.drop_table('form_items', schema='event_registration')
    op.drop_table('forms', schema='event_registration')
    op.execute(DropSchema('event_registration'))
