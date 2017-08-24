"""Add default_ticket_template to category table

Revision ID: f6cb3c9cf9ab
Revises: 75060428e775
Create Date: 2017-08-07 12:05:03.103271
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'f6cb3c9cf9ab'
down_revision = '75060428e775'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('categories', sa.Column('default_ticket_template_id', sa.Integer(), nullable=True, index=True),
                  schema='categories')
    op.create_foreign_key(None, 'categories', 'designer_templates', ['default_ticket_template_id'], ['id'],
                          source_schema='categories', referent_schema='indico')


def downgrade():
    op.drop_constraint(op.f('fk_categories_default_ticket_template_id_designer_templates'), 'categories',
                       schema='categories', type_='foreignkey')
    op.drop_column('categories', 'default_ticket_template_id', schema='categories')
