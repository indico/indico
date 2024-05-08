"""Update merged users in registrations

Revision ID: 735dc4e8d2f3
Revises: 178d297eae7e
Create Date: 2021-06-07 15:48:19.154975
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '735dc4e8d2f3'
down_revision = '178d297eae7e'
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

        UPDATE event_registration.registrations r
        SET user_id = mm.current_user_id
        FROM merge_map mm
        WHERE mm.user_id = r.user_id AND mm.current_user_id != r.user_id AND NOT EXISTS (
            -- avoid conflcit with existing registration of the target user
            SELECT 1
            FROM event_registration.registrations r2
            WHERE r2.registration_form_id = r.registration_form_id AND r2.user_id = mm.current_user_id
        ) AND NOT EXISTS (
            -- avoid conflict with existing registration of another user merged into the same target user
            SELECT 1
            FROM event_registration.registrations r3
            JOIN merge_map mm2 ON (mm2.user_id = r3.user_id AND mm2.current_user_id = mm.current_user_id)
            WHERE r3.registration_form_id = r.registration_form_id AND mm2.user_id != r.user_id
        );

        DROP TABLE merge_map;
    ''')


def downgrade():
    pass
