"""Add indico_unaccent function

Revision ID: 4074211727ba
Revises: 3f3a9554a6da
Create Date: 2015-06-05 14:21:52.752777
"""

from alembic import op

from indico.core.db.sqlalchemy.custom.unaccent import SQL_FUNCTION_UNACCENT


# revision identifiers, used by Alembic.
revision = '4074211727ba'
down_revision = '3f3a9554a6da'


def upgrade():
    op.execute(SQL_FUNCTION_UNACCENT)


def downgrade():
    op.execute("DROP FUNCTION indico_unaccent(TEXT)")
