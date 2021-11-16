"""Ensure single_choice fields have item_type

Revision ID: 8993132179d3
Revises: b36825c7869e
Create Date: 2021-11-16 14:57:44.828347
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '8993132179d3'
down_revision = 'b36825c7869e'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        UPDATE event_registration.form_items
        SET data = data || '{"item_type": "dropdown"}'
        WHERE
        input_type = 'single_choice' AND
        (NOT (data ? 'item_type') OR (data ->> 'item_type') NOT IN ('dropdown', 'radiogroup'));
    ''')


def downgrade():
    pass
