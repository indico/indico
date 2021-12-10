"""Add publish registrations with consent

Revision ID: 82fb6c6ac6db
Revises: 3dafee32ba7d
Create Date: 2021-12-07 11:06:31.529341
"""
from enum import Enum

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum


# revision identifiers, used by Alembic.
revision = '82fb6c6ac6db'
down_revision = '3dafee32ba7d'
branch_labels = None
depends_on = None


class _PublishRegistrationsMode(int, Enum):
    hide_all = 0
    show_with_consent = 1
    show_all = 2


class _PublishConsentType(int, Enum):
    not_given = 0
    participants = 1
    all = 2


def upgrade():
    op.add_column('forms',
                  sa.Column('publish_registrations_mode', PyIntEnum(_PublishRegistrationsMode), server_default='0',
                            nullable=False),
                  schema='event_registration')
    op.alter_column('forms', 'publish_registrations_mode', server_default=None, schema='event_registration')
    op.execute('UPDATE event_registration.forms SET publish_registrations_mode = 2 WHERE publish_registrations_enabled')
    op.drop_column('forms', 'publish_registrations_enabled', schema='event_registration')
    op.add_column('registrations',
                  sa.Column('consent_to_publish', PyIntEnum(_PublishConsentType), server_default='2', nullable=False),
                  schema='event_registration')
    op.alter_column('registrations', 'consent_to_publish', server_default=None, schema='event_registration')


def downgrade():
    op.add_column('forms',
                  sa.Column('publish_registrations_enabled', sa.Boolean(), server_default='false', nullable=False),
                  schema='event_registration')
    op.alter_column('forms', 'publish_registrations_enabled', server_default=None, schema='event_registration')
    op.execute('''
        UPDATE event_registration.forms
        SET publish_registrations_enabled = true
        WHERE publish_registrations_mode = 2
    ''')
    op.drop_column('forms', 'publish_registrations_mode', schema='event_registration')
    op.drop_column('registrations', 'consent_to_publish', schema='event_registration')
