"""Add natsort function

Revision ID: 66ecbb1c0ddd
Revises: 813ea74ce8dc
Create Date: 2018-04-23 16:02:35.682560
"""

from alembic import op

from indico.core.db.sqlalchemy.custom.natsort import SQL_FUNCTION_NATSORT


# revision identifiers, used by Alembic.
revision = '66ecbb1c0ddd'
down_revision = '813ea74ce8dc'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(SQL_FUNCTION_NATSORT)


def downgrade():
    op.execute('DROP FUNCTION indico.natsort(value TEXT)')
