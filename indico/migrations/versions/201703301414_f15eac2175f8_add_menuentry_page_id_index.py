"""Add MenuEntry.page_id index

Revision ID: f15eac2175f8
Revises: e185a5089262
Create Date: 2017-03-30 14:14:09.632195
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'f15eac2175f8'
down_revision = 'e185a5089262'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(None, 'menu_entries', ['page_id'], unique=False, schema='events')


def downgrade():
    op.drop_index('ix_menu_entries_page_id', table_name='menu_entries', schema='events')
