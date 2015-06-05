"""Add indico_unaccent function

Revision ID: 4074211727ba
Revises: 3f3a9554a6da
Create Date: 2015-06-05 14:21:52.752777
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '4074211727ba'
down_revision = '3f3a9554a6da'

SQL_FUNCTION_TEMPLATE = '''
    CREATE FUNCTION indico_unaccent(value TEXT)
        RETURNS TEXT
    AS $$
    BEGIN
        RETURN {return_value};
    END;
    $$
    LANGUAGE plpgsql;
'''


def upgrade():
    conn = op.get_bind()
    unaccent_extension_installed = conn.execute("""
        SELECT EXISTS(SELECT TRUE FROM pg_extension WHERE extname = 'unaccent')
    """).scalar()

    if unaccent_extension_installed:
        conn.execute(SQL_FUNCTION_TEMPLATE.format(return_value='unaccent(value)'))
    else:
        conn.execute(SQL_FUNCTION_TEMPLATE.format(return_value='value'))


def downgrade():
    conn = op.get_bind()
    conn.execute("DROP FUNCTION indico_unaccent(TEXT)")
