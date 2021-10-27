"""Add publish registrations with consent

Revision ID: 82fb6c6ac6db
Revises: b36825c7869e
Create Date: 2021-10-27 09:30:36.529341
"""
from enum import Enum

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum


# revision identifiers, used by Alembic.
revision = '82fb6c6ac6db'
down_revision = 'b36825c7869e'
branch_labels = None
depends_on = None


class _PublishRegistrationsMode(int, Enum):
    hide_all = 1
    show_with_consent = 2
    show_all = 3


def upgrade():
    op.add_column('forms', sa.Column('publish_registrations_mode', PyIntEnum(_PublishRegistrationsMode), server_default='1', nullable=False), schema='event_registration')
    op.execute('UPDATE event_registration.forms SET publish_registrations_mode = 2 WHERE publish_registrations_enabled')
    op.drop_column('forms', 'publish_registrations_enabled', schema='event_registration')


def downgrade():
    op.add_column('forms', sa.Column('publish_registrations_enabled', sa.BOOLEAN(), server_default='false', autoincrement=False, nullable=False), schema='event_registration')
    op.execute('UPDATE event_registration.forms SET publish_registrations_enabled = true WHERE publish_registrations_mode != 1')
    op.drop_column('forms', 'publish_registrations_mode', schema='event_registration')
