"""Add Room.notification_emails column

Revision ID: fe73a07da0b4
Revises: 3e4a0c08eae6
Create Date: 2019-03-19 17:28:46.354942
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'fe73a07da0b4'
down_revision = '3e4a0c08eae6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('rooms', sa.Column('notification_emails', postgresql.ARRAY(sa.String()), nullable=False,
                                     server_default='{}'), schema='roombooking')
    op.alter_column('rooms', 'notification_emails', server_default=None, schema='roombooking')
    # import data from attributes
    op.execute('''
        WITH notification_emails AS (
            SELECT rav.room_id, string_to_array(lower(replace(rav.value #>> '{}', ' ', '')), ',') AS emails
            FROM roombooking.room_attribute_values rav
            WHERE rav.attribute_id = (SELECT id FROM roombooking.room_attributes WHERE name = 'notification-email')
        )
        UPDATE roombooking.rooms r SET notification_emails = ne.emails
        FROM notification_emails ne
        WHERE r.id = ne.room_id;
    ''')


def downgrade():
    # restore attribute and data
    op.execute('''
        WITH attr AS (
            INSERT INTO roombooking.room_attributes
                (name, title, is_hidden) VALUES ('notification-email', 'Notification Email', true)
                -- DO NOTHING wouldn't return us the id so we do a no-op update
                ON CONFLICT (name) DO UPDATE SET name = excluded.name
                RETURNING id
        )
        INSERT INTO roombooking.room_attribute_values (attribute_id, room_id, value)
        SELECT attr.id, r.id, to_json(array_to_string(notification_emails, ','))
        FROM roombooking.rooms r, attr
        WHERE r.notification_emails != '{}'
        ON CONFLICT (attribute_id, room_id) DO UPDATE SET value = excluded.value;
    ''')

    op.drop_column('rooms', 'notification_emails', schema='roombooking')
