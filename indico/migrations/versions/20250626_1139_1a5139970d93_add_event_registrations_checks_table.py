"""Add event_registrations.checks table.

Revision ID: 1a5139970d93
Revises: a5b6d7237997
Create Date: 2025-01-30 11:39:30.511470
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime


# revision identifiers, used by Alembic.
revision = '1a5139970d93'
down_revision = 'a5b6d7237997'
branch_labels = None
depends_on = None


class _CheckRule(int, Enum):
    once = 1
    multiple = 2
    once_daily = 3


def upgrade():
    op.create_table(
        'check_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('rule', PyIntEnum(_CheckRule), nullable=False),
        sa.Column('event_id', sa.Integer(), index=True),
        sa.Column('is_system_defined', sa.Boolean(), nullable=False),
        sa.Column('check_out_allowed', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_registration'
    )
    op.create_index('ix_uq_check_types_title_lower', 'check_types',
                    [sa.text('COALESCE(event_id, -1)'), sa.text('lower(title)')],
                    unique=True, schema='event_registration')
    op.create_check_constraint('valid_is_system_defined', 'check_types',
                               '((is_system_defined = true AND event_id IS NULL) '
                               'OR (is_system_defined = false AND event_id IS NOT NULL))',
                               schema='event_registration')
    conn = op.get_bind()
    system_user_id = conn.execute('SELECT id FROM users.users WHERE is_system').scalar()
    check_type_id = conn.execute('''
        INSERT INTO event_registration.check_types (title, rule, is_system_defined, check_out_allowed)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    ''', ('Initial Attendance Check', _CheckRule.once.value, True, True)).scalar()

    conn.execute('''
        INSERT INTO indico.settings (module, name, value)
        VALUES ('default_check_type', 'default_check_type', %s)
    ''', (str(check_type_id)))

    op.create_table(
        'checks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('registration_id', sa.Integer(), nullable=False, index=True),
        sa.Column('timestamp', UTCDateTime, nullable=False, index=True),
        sa.Column('check_type_id', sa.Integer(), nullable=False, index=True),
        sa.Column('is_check_out', sa.Boolean(), nullable=False),
        sa.Column('checked_by_user_id', sa.Integer(), index=True),
        sa.ForeignKeyConstraint(['registration_id'], ['event_registration.registrations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['check_type_id'], ['event_registration.check_types.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['checked_by_user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_registration'
    )

    conn.execute('''
        INSERT INTO event_registration.checks (registration_id, check_type_id, timestamp, is_check_out, checked_by_user_id)
        SELECT r.id, %s, r.checked_in_dt, %s, %s
        FROM event_registration.registrations r
        WHERE r.checked_in IS TRUE
    ''', (check_type_id, False, system_user_id))

    op.drop_column('registrations', 'checked_in', schema='event_registration')
    op.drop_column('registrations', 'checked_in_dt', schema='event_registration')

    op.add_column('events', sa.Column('default_check_type_id', sa.Integer(), nullable=False, index=True,
                                      server_default=str(check_type_id)), schema='events')
    op.alter_column('events', 'default_check_type_id', server_default=None, schema='events')
    op.create_foreign_key(None, 'events', 'check_types', ['default_check_type_id'], ['id'], source_schema='events',
                          referent_schema='event_registration')


def downgrade():
    op.drop_column('events', 'default_check_type_id', schema='events')
    op.add_column('registrations', sa.Column('checked_in', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_registration')
    op.alter_column('registrations', 'checked_in', server_default=None, schema='event_registration')
    op.add_column('registrations', sa.Column('checked_in_dt', UTCDateTime, nullable=True), schema='event_registration')

    conn = op.get_bind()
    check_type_id = conn.execute('''SELECT id FROM event_registration.check_types
                                 WHERE title='Initial Attendance Check'
                                 AND is_system_defined=True''').scalar()
    conn.execute('''
        UPDATE event_registration.registrations r
        SET checked_in = TRUE,
            checked_in_dt = last_check_in.timestamp
        FROM (
            SELECT c.registration_id, c.timestamp
            FROM event_registration.checks c
            WHERE c.timestamp = (
                SELECT MAX(c2.timestamp)
                FROM event_registration.checks c2
                WHERE c2.registration_id = c.registration_id
                AND c2.check_type_id = %s
            )
            AND c.is_check_out = False
        ) AS last_check_in
        WHERE r.id = last_check_in.registration_id
    ''', (check_type_id))

    conn.execute('''
        DELETE FROM indico.settings
        WHERE module = 'default_check_type' AND name = 'default_check_type'
    ''')

    op.drop_table('checks', schema='event_registration')
    op.drop_table('check_types', schema='event_registration')
