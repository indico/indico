"""Add event category id FK

Revision ID: 535f817f2533
Revises: ff7e1027bd4
Create Date: 2016-06-06 17:00:27.043772
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '535f817f2533'
down_revision = 'ff7e1027bd4'


def upgrade():
    # remove category information of events referencing a hard-deleted category
    # need to use immediate constraint execution to avoid pending trigger events
    op.execute("""
        SET CONSTRAINTS ALL IMMEDIATE;
        UPDATE events.events e
        SET category_id = NULL, category_chain = NULL
        WHERE is_deleted AND NOT EXISTS (
            SELECT 1 FROM categories.categories WHERE id = e.category_id
        );
    """)
    op.create_foreign_key(None,
                          'events', 'categories',
                          ['category_id'], ['id'],
                          source_schema='events', referent_schema='categories')


def downgrade():
    op.drop_constraint('fk_events_category_id_categories', 'events', schema='events')
