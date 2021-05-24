"""Restrict event creation if cat has subcats

Revision ID: cf9e1b4e2f5f
Revises: d89585afaf2e
Create Date: 2021-05-24 14:47:29.681381
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'cf9e1b4e2f5f'
down_revision = 'd89585afaf2e'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        UPDATE categories.categories
        SET event_creation_restricted = true
        WHERE
        NOT event_creation_restricted AND
        NOT is_deleted AND
        EXISTS (
            SELECT 1
            FROM categories.categories AS c2
            WHERE c2.parent_id = categories.categories.id AND NOT c2.is_deleted
        );
    ''')


def downgrade():
    # nothing to do - keeping event creation restricted is fine
    pass
