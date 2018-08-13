"""Remove room thumbnail

Revision ID: 93985a8c11ed
Revises: a13e25814c4c
Create Date: 2018-08-03 17:03:28.054462
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '93985a8c11ed'
down_revision = 'a13e25814c4c'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('photos', 'thumbnail', schema='roombooking')


def downgrade():
    op.add_column('photos', sa.Column('thumbnail', sa.LargeBinary(), nullable=True), schema='roombooking')
