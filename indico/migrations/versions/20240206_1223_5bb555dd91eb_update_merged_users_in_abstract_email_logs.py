"""Update merged users in abstract email logs

Revision ID: 5bb555dd91eb
Revises: 8e08236a529f
Create Date: 2024-02-06 12:23:43.406547
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '5bb555dd91eb'
down_revision = '8e08236a529f'
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

        UPDATE event_abstracts.email_logs eml
        SET user_id = mm.current_user_id
        FROM merge_map mm
        WHERE mm.user_id = eml.user_id AND mm.current_user_id != eml.user_id;

        DROP TABLE merge_map;
    ''')


def downgrade():
    pass
