"""Move indico_unaccent to indico schema

Revision ID: 8763fe20f41
Revises: 28b674f8290d
Create Date: 2016-08-15 15:52:40.160475
"""

from alembic import context, op


# revision identifiers, used by Alembic.
revision = '8763fe20f41'
down_revision = '28b674f8290d'


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    res = conn.execute("SELECT routine_schema FROM information_schema.routines WHERE routine_name = 'indico_unaccent'")
    schema = res.fetchone()[0]
    if schema != 'indico':
        op.execute("ALTER FUNCTION {}.indico_unaccent(TEXT) SET SCHEMA indico".format(schema))


def downgrade():
    op.execute("ALTER FUNCTION indico.indico_unaccent(TEXT) SET SCHEMA public")
