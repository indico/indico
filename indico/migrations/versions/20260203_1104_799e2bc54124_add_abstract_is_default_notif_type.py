"""Add is_default and notification_type to abstract email templates

Revision ID: 799e2bc54124
Revises: af9d03d7073c
Create Date: 2026-02-03 11:04:06.572323
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.enum import IndicoIntEnum


# revision identifiers, used by Alembic.
revision = '799e2bc54124'
down_revision = 'af9d03d7073c'
branch_labels = None
depends_on = None


class _AbstractNotificationType(IndicoIntEnum):
    submitted = 1
    withdrawn = 2
    accepted = 3
    rejected = 4
    merged = 5
    invited = 6


def upgrade():
    op.add_column('email_templates', sa.Column('is_default', sa.Boolean(), nullable=True), schema='event_abstracts')
    op.add_column('email_templates', sa.Column('notification_type', PyIntEnum(_AbstractNotificationType), nullable=True), schema='event_abstracts')


def downgrade():
    op.drop_column('email_templates', 'is_default', schema='event_abstracts')
    op.drop_column('email_templates', 'notification_type', schema='event_abstracts')
