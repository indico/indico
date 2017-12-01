"""Add visibility options to contribution fields

Revision ID: 093533d27a96
Revises: 566d5de4e0e5
Create Date: 2017-11-30 17:15:07.141552
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.events.contributions.models.fields import FieldVisibility


# revision identifiers, used by Alembic.
revision = '093533d27a96'
down_revision = '566d5de4e0e5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('contribution_fields',
                  sa.Column('user_editable', sa.Boolean(), nullable=False, server_default='true'),
                  schema='events')
    op.add_column('contribution_fields',
                  sa.Column('visibility', PyIntEnum(FieldVisibility),
                            nullable=False, server_default='1'),
                  schema='events')
    op.alter_column('contribution_fields', 'user_editable', server_default=None, schema='events')
    op.alter_column('contribution_fields', 'visibility', server_default=None, schema='events')


def downgrade():
    op.drop_column('contribution_fields', 'visibility', schema='events')
    op.drop_column('contribution_fields', 'user_editable', schema='events')
