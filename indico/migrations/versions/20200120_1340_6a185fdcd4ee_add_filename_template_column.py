"""Add filename_template column

Revision ID: 6a185fdcd4ee
Revises: e01c48de5a5e
Create Date: 2020-01-13 13:40:40.735646
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '6a185fdcd4ee'
down_revision = 'e01c48de5a5e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('file_types', sa.Column('filename_template', sa.String(), nullable=True), schema='event_editing')


def downgrade():
    op.drop_column('file_types', 'filename_template', schema='event_editing')
