"""Add indico_unaccent function

Revision ID: 4074211727ba
Revises: 3f3a9554a6da
Create Date: 2015-06-05 14:21:52.752777
"""

from alembic import op, context

from indico.core.db.sqlalchemy.custom.unaccent import SQL_FUNCTION_UNACCENT, SQL_FUNCTION_NOOP
from indico.core.db.sqlalchemy.util.queries import has_extension


# revision identifiers, used by Alembic.
revision = '4074211727ba'
down_revision = '3f3a9554a6da'


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')

    if has_extension(op.get_bind(), 'unaccent'):
        print 'Unaccent extension is available - indico_unaccent will use it'
        op.execute(SQL_FUNCTION_UNACCENT)
    else:
        print 'Unaccent extension is NOT available - indico_unaccent will not touch its argument'
        op.execute(SQL_FUNCTION_NOOP)


def downgrade():
    op.execute("DROP FUNCTION indico_unaccent(TEXT)")
