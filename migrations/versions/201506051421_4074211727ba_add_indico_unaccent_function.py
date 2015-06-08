"""Add indico_unaccent function

Revision ID: 4074211727ba
Revises: 3f3a9554a6da
Create Date: 2015-06-05 14:21:52.752777
"""

from alembic import op, context

# revision identifiers, used by Alembic.
revision = '4074211727ba'
down_revision = '3f3a9554a6da'


# if you wonder why search_path is set and the two-argument `unaccent` function is used,
# see this post on stackoverflow: http://stackoverflow.com/a/11007216/298479
SQL_FUNCTION_UNACCENT = '''
    CREATE FUNCTION indico_unaccent(value TEXT)
        RETURNS TEXT
    AS $$
    BEGIN
        RETURN unaccent('unaccent', value);
    END;
    $$
    LANGUAGE plpgsql IMMUTABLE SET search_path = public, pg_temp;
'''

SQL_FUNCTION_NOOP = '''
    CREATE FUNCTION indico_unaccent(value TEXT)
        RETURNS TEXT
    AS $$
    BEGIN
        RETURN value;
    END;
    $$
    LANGUAGE plpgsql IMMUTABLE;
'''


def _has_extension(name):
    conn = op.get_bind()
    return conn.execute("SELECT EXISTS(SELECT TRUE FROM pg_extension WHERE extname = %s)", (name,)).scalar()


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')

    if _has_extension('unaccent'):
        print 'Unaccent extension is available - indico_unaccent will use it'
        op.execute(SQL_FUNCTION_UNACCENT)
    else:
        print 'Unaccent extension is NOT available - indico_unaccent will not touch its argument'
        op.execute(SQL_FUNCTION_NOOP)


def downgrade():
    op.execute("DROP FUNCTION indico_unaccent(TEXT)")
