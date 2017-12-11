"""Add AttachmentFolder.is_hidden

Revision ID: 813ea74ce8dc
Revises: c820455976ba
Create Date: 2018-01-29 08:42:10.760814
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '813ea74ce8dc'
down_revision = 'c820455976ba'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('folders', sa.Column('is_hidden', sa.Boolean(), nullable=False, server_default='false'),
                  schema='attachments')
    op.alter_column('folders', 'is_hidden', server_default=None, schema='attachments')
    op.create_check_constraint('is_hidden_not_is_always_visible', 'folders', 'NOT (is_hidden AND is_always_visible)',
                               schema='attachments')


def downgrade():
    op.drop_constraint('ck_folders_is_hidden_not_is_always_visible', 'folders', schema='attachments')
    op.drop_column('folders', 'is_hidden', schema='attachments')
