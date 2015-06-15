"""Store category id as int

Revision ID: 48177e1c4aa4
Revises: 215a0824c32c
Create Date: 2015-06-15 13:38:05.945824
"""

import sqlalchemy as sa
from alembic import op, context


# revision identifiers, used by Alembic.
revision = '48177e1c4aa4'
down_revision = '215a0824c32c'


def _has_legacy_ids(table, column):
    conn = op.get_bind()
    return conn.execute(r"SELECT EXISTS(SELECT 1 FROM {0} WHERE {1} !~ '^[1-9]\d*$' AND {1} != '0')"
                        .format(table, column)).scalar()


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    if _has_legacy_ids('categories.category_index', 'id') or _has_legacy_ids('users.favorite_categories', 'target_id'):
        raise Exception('Please run the legacy_categories zodb importer first.')
    op.execute('ALTER TABLE categories.category_index ALTER COLUMN id TYPE int USING id::int')
    op.execute('ALTER TABLE users.favorite_categories ALTER COLUMN target_id TYPE int USING target_id::int')


def downgrade():
    op.alter_column('category_index', 'id', type_=sa.String, schema='categories')
    op.alter_column('favorite_categories', 'target_id', type_=sa.String, schema='users')
