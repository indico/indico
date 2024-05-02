"""Add hide registration form

Revision ID: 67e92eeca34f
Revises: 4e32f4d5ebe4
Create Date: 2024-05-01 14:31:21.090459
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '67e92eeca34f'
down_revision = '4e32f4d5ebe4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms', sa.Column('is_hidden', sa.Boolean(), nullable=False,
                  server_default='false'), schema='event_registration')
    op.alter_column('forms', 'is_hidden', server_default=None,
                    schema='event_registration')
    op.add_column('forms', sa.Column('uuid', postgresql.UUID(), nullable=True),
                  schema='event_registration')


def downgrade():
    op.drop_column('forms', 'uuid', schema='event_registration')
    op.drop_column('forms', 'is_hidden', schema='event_registration')
