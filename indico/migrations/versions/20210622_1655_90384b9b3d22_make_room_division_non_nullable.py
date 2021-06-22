"""Make room division non-nullable

Revision ID: 90384b9b3d22
Revises: 79e770865675
Create Date: 2021-06-22 16:55:42.973082
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '90384b9b3d22'
down_revision = '79e770865675'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE roombooking.rooms SET division = '' WHERE division IS NULL")
    op.alter_column('rooms', 'division', nullable=False, schema='roombooking')


def downgrade():
    op.alter_column('rooms', 'division', nullable=True, schema='roombooking')
