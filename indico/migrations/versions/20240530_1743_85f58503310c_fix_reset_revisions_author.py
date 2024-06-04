"""Fix reset revisions author

Revision ID: 85f58503310c
Revises: 16c9445951f4
Create Date: 2024-05-30 17:43:01.306657
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '85f58503310c'
down_revision = '16c9445951f4'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        UPDATE event_editing.revisions
        SET user_id = (SELECT id FROM users.users WHERE is_system)
        WHERE type = 10
    ''')


def downgrade():
    pass
