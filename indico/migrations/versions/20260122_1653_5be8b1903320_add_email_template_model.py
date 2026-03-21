"""Add email_template model

Revision ID: 5be8b1903320
Revises: 932389d22b1f
Create Date: 2026-01-22 16:53:42.659703
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum


# revision identifiers, used by Alembic.
revision = '5be8b1903320'
down_revision = '932389d22b1f'
branch_labels = None
depends_on = None


class _PrincipalType(int, Enum):
    user = 1
    local_group = 2
    multipass_group = 3
    email = 4
    network = 5
    event_role = 6
    category_role = 7
    registration_form = 8


class _RegistrationNotificationType(int, Enum):
    registration_creation = 1
    registration_state_update = 2
    registration_modification = 3
    registration_receipt_creation = 4


class _EmailTemplateType(int, Enum):
    registration = 1
    invitation = 2


def upgrade():
    op.create_table('email_templates',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('type', PyIntEnum(_EmailTemplateType), nullable=False),
                    sa.Column('notification_type', PyIntEnum(_RegistrationNotificationType), nullable=True),
                    sa.Column('title', sa.String(), nullable=False),
                    sa.Column('subject', sa.String(), nullable=False),
                    sa.Column('body', sa.Text(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=True, index=True),
                    sa.Column('category_id', sa.Integer(), nullable=True, index=True),
                    sa.Column('rules', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
                    sa.Column('is_active', sa.Boolean(), nullable=False),
                    sa.CheckConstraint('(event_id IS NULL) != (category_id IS NULL)',
                                       name='event_xor_category_id_null'),
                    sa.ForeignKeyConstraint(['category_id'], ['categories.categories.id']),
                    sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='indico')


def downgrade():
    op.drop_table('email_templates', schema='indico')
