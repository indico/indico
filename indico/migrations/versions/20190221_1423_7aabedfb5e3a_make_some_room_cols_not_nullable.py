"""Make some room cols not nullable

Revision ID: 7aabedfb5e3a
Revises: 416f9c877300
Create Date: 2019-02-21 14:23:33.341662
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '7aabedfb5e3a'
down_revision = '416f9c877300'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        UPDATE roombooking.rooms
        SET comments = COALESCE(comments, ''),
            key_location = COALESCE(key_location, ''),
            telephone = COALESCE(telephone, '')
    ''')
    op.alter_column('rooms', 'comments', nullable=False, schema='roombooking')
    op.alter_column('rooms', 'key_location', nullable=False, schema='roombooking')
    op.alter_column('rooms', 'telephone', nullable=False, schema='roombooking')


def downgrade():
    op.alter_column('rooms', 'telephone', nullable=True, schema='roombooking')
    op.alter_column('rooms', 'key_location', nullable=True, schema='roombooking')
    op.alter_column('rooms', 'comments', nullable=True, schema='roombooking')
