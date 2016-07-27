"""Add favorite category FK

Revision ID: 2940c52467e4
Revises: 85637555724
Create Date: 2016-06-03 13:23:10.249330
"""

from alembic import op, context


# revision identifiers, used by Alembic.
revision = '2940c52467e4'
down_revision = '85637555724'


def upgrade():
    if not context.is_offline_mode():
        # sanity check to avoid running w/o categories migrated
        conn = op.get_bind()
        has_categories = conn.execute("SELECT EXISTS (SELECT 1 FROM categories.categories)").fetchone()[0]
        if not has_categories:
            raise Exception('Upgrade to {} and run the category zodb import first!'.format(down_revision))
    op.create_foreign_key(None,
                          'favorite_categories', 'categories',
                          ['target_id'], ['id'],
                          source_schema='users', referent_schema='categories')


def downgrade():
    op.drop_constraint('fk_favorite_categories_target_id_categories', 'favorite_categories', schema='users')
