"""Add visibility options to contribution fields

Revision ID: 093533d27a96
Revises: 9c4418d7a6aa
Create Date: 2017-11-30 17:15:07.141552
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.events.contributions.models.fields import ContributionFieldVisibility


# revision identifiers, used by Alembic.
revision = '093533d27a96'
down_revision = '9c4418d7a6aa'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('contribution_fields',
                  sa.Column('is_user_editable', sa.Boolean(), nullable=False, server_default='true'),
                  schema='events')
    op.add_column('contribution_fields',
                  sa.Column('visibility', PyIntEnum(ContributionFieldVisibility),
                            nullable=False, server_default='1'),
                  schema='events')
    op.alter_column('contribution_fields', 'is_user_editable', server_default=None, schema='events')
    op.alter_column('contribution_fields', 'visibility', server_default=None, schema='events')


def downgrade():
    op.drop_column('contribution_fields', 'visibility', schema='events')
    op.drop_column('contribution_fields', 'is_user_editable', schema='events')
