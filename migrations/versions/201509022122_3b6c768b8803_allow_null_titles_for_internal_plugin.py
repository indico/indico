"""Allow NULL titles for internal/plugin entries

Revision ID: 3b6c768b8803
Revises: 3fcf833adc2d
Create Date: 2015-09-02 21:22:56.516913
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3b6c768b8803'
down_revision = '3fcf833adc2d'


def upgrade():
    op.drop_constraint('ck_menu_entries_valid_title', 'menu_entries', schema='events')
    op.create_check_constraint('valid_title', 'menu_entries',
                               "(type = 1 AND title IS NULL) OR (type IN (3, 5) AND title IS NOT NULL) OR "
                               "(type NOT IN (1, 3, 5))",
                               schema='events')
    op.create_check_constraint('title_not_empty', 'menu_entries',
                               "title != ''",
                               schema='events')


def downgrade():
    op.drop_constraint('ck_menu_entries_valid_title', 'menu_entries', schema='events')
    op.drop_constraint('ck_menu_entries_title_not_empty', 'menu_entries', schema='events')
    op.create_check_constraint('valid_title', 'menu_entries',
                               "(type = 1 AND title IS NULL) OR (type != 1 AND title IS NOT NULL)",
                               schema='events')
