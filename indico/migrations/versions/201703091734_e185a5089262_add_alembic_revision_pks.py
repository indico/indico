"""Add alembic revision PKs

Revision ID: e185a5089262
Revises: 505bf893f00f
Create Date: 2017-03-09 17:34:54.624923
"""

import sqlalchemy as sa
from alembic import op, context


# revision identifiers, used by Alembic.
revision = 'e185a5089262'
down_revision = '505bf893f00f'
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    res = conn.execute(sa.text("""
        SELECT t.table_name
        FROM information_schema.tables t
        WHERE
            t.table_schema = 'public' AND
            (t.table_name = 'alembic_version' OR t.table_name LIKE 'alembic_version_%') AND
            NOT EXISTS (
                SELECT 1
                FROM information_schema.table_constraints tc
                WHERE
                    tc.table_name = t.table_name AND
                    tc.table_schema = t.table_schema AND
                    tc.constraint_type = 'PRIMARY KEY'
            )
    """))
    for table_name, in res:
        conn.execute('ALTER TABLE {name} ADD CONSTRAINT {name}_pkc PRIMARY KEY (version_num);'.format(name=table_name))


def downgrade():
    if context.is_offline_mode():
        raise Exception('This downgrade is only possible in online mode')
    conn = op.get_bind()
    res = conn.execute(sa.text("""
        SELECT t.table_name, tc.constraint_name
        FROM information_schema.tables t
        JOIN information_schema.table_constraints tc ON (
            tc.table_name = t.table_name AND tc.table_schema = t.table_schema AND tc.constraint_type = 'PRIMARY KEY'
        )
        WHERE t.table_schema = 'public' AND (t.table_name = 'alembic_version' OR t.table_name LIKE 'alembic_version_%')
    """))
    for table_name, constraint_name in res:
        conn.execute('ALTER TABLE {name} DROP CONSTRAINT {pk};'.format(name=table_name, pk=constraint_name))
