"""Update merged users in event creators

Revision ID: 379ba72f4096
Revises: 34f27622213b
Create Date: 2024-10-15 14:52:08.316473
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '379ba72f4096'
down_revision = '34f27622213b'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        CREATE TEMPORARY TABLE merge_map AS
        WITH RECURSIVE merge_map (user_id, current_user_id) AS (
            SELECT id, id FROM users.users WHERE merged_into_id IS NULL
            UNION ALL
            SELECT u.id, mm.current_user_id FROM users.users u, merge_map mm WHERE u.merged_into_id = mm.user_id
        ) SELECT * FROM merge_map WHERE user_id != current_user_id;

        CREATE INDEX ix_merge_map_current_user_id ON merge_map USING btree (current_user_id);

        UPDATE events.events evt
        SET creator_id = mm.current_user_id
        FROM merge_map mm
        WHERE mm.user_id = evt.creator_id AND mm.current_user_id != evt.creator_id;

        DROP TABLE merge_map;
    ''')


def downgrade():
    pass
