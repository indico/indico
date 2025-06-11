"""Add conditional field columns

Revision ID: 281d849bc4df
Revises: 4615aff776e0
Create Date: 2025-05-19 17:19:09.269955
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '281d849bc4df'
down_revision = '4615aff776e0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('form_items', sa.Column('show_if_id', sa.Integer(), nullable=True), schema='event_registration')
    op.add_column('form_items', sa.Column('show_if_values', postgresql.JSONB(), nullable=True),
                  schema='event_registration')
    op.create_index(None, 'form_items', ['show_if_id'], unique=False, schema='event_registration')
    op.create_foreign_key(None, 'form_items', 'form_items', ['show_if_id'], ['id'], source_schema='event_registration',
                          referent_schema='event_registration')
    op.create_check_constraint('no_conditional_sections', 'form_items', 'show_if_id IS NULL OR type IN (2, 5, 3)',
                               schema='event_registration')
    op.create_check_constraint('conditional_has_values', 'form_items',
                               '(show_if_id IS NULL) = (show_if_values IS NULL)',
                               schema='event_registration')


def downgrade():
    op.drop_column('form_items', 'show_if_values', schema='event_registration')
    op.drop_column('form_items', 'show_if_id', schema='event_registration')
