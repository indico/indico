"""Add default badge to categories

Revision ID: c997dc927fbc
Revises: 497c61b68050
Create Date: 2020-07-30 14:23:35.808229
"""

import json

import sqlalchemy as sa
from alembic import context, op

from indico.core.db.sqlalchemy.util.management import DEFAULT_BADGE_DATA


# revision identifiers, used by Alembic.
revision = 'c997dc927fbc'
down_revision = '497c61b68050'
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    op.add_column('categories', sa.Column('default_badge_template_id', sa.Integer(), nullable=True),
                  schema='categories')
    op.create_index(None, 'categories', ['default_badge_template_id'], unique=False, schema='categories')
    op.create_foreign_key(None, 'categories', 'designer_templates', ['default_badge_template_id'], ['id'],
                          source_schema='categories', referent_schema='indico')
    conn = op.get_bind()
    root_categ_id = conn.execute('SELECT id FROM categories.categories WHERE parent_id IS NULL').scalar()
    badge_id = conn.execute('''
        INSERT INTO indico.designer_templates
        (category_id, title, type, is_system_template, is_clonable, data) VALUES
        (%s         , %s   , %s  , true              , true       , %s)
        RETURNING id
    ''', (root_categ_id, 'Default badge', 1, json.dumps(DEFAULT_BADGE_DATA))).scalar()
    conn.execute('''
        UPDATE categories.categories
        SET default_badge_template_id = %s
        WHERE id = %s
    ''', (badge_id, root_categ_id))


def downgrade():
    if context.is_offline_mode():
        raise Exception('This downgrade is only possible in online mode')
    conn = op.get_bind()
    id_ = conn.execute('SELECT default_badge_template_id FROM categories.categories WHERE parent_id IS NULL').scalar()
    op.drop_column('categories', 'default_badge_template_id', schema='categories')
    conn.execute('DELETE FROM indico.designer_templates WHERE is_system_template AND id = %s', (id_,))
