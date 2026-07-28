"""Disallow internal name on regform labels

Revision ID: c412156094d6
Revises: d7e2a9c14f6b
Create Date: 2026-07-28 12:48:27.294714
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'c412156094d6'
down_revision = 'd7e2a9c14f6b'
branch_labels = None
depends_on = None


def upgrade():
    # There shouldn't be any text fields w/ an internal nane, but just in case...
    op.execute('''
        UPDATE event_registration.form_items
        SET internal_name = NULL
        WHERE type = 3 AND internal_name IS NOT NULL;
    ''')
    op.create_check_constraint(
        'text_no_internal_name',
        'form_items',
        '(type != 3) OR (internal_name IS NULL)',
        schema='event_registration'
    )


def downgrade():
    op.drop_constraint('ck_form_items_text_no_internal_name', 'form_items', schema='event_registration')
