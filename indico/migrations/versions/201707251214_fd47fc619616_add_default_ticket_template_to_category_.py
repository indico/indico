"""Add default_ticket_template to category table

Revision ID: fd47fc619616
Revises: 75060428e775
Create Date: 2017-07-25 12:14:44.314018
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'fd47fc619616'
down_revision = '75060428e775'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('categories', sa.Column('default_ticket_template_id', sa.Integer(), nullable=True),
                  schema='categories')
    op.create_index(None, 'categories', ['default_ticket_template_id'], unique=False, schema='categories')
    op.create_foreign_key(None, 'categories', 'designer_templates', ['default_ticket_template_id'], ['id'],
                          source_schema='categories', referent_schema='indico')


def downgrade():
    op.drop_column('categories', 'default_ticket_template_id', schema='categories')
