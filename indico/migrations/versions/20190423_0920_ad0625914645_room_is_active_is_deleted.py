"""Room.is_active -> is_deleted

Revision ID: ad0625914645
Revises: 8521bce91242
Create Date: 2019-04-23 09:20:49.877823
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'ad0625914645'
down_revision = '8521bce91242'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('rooms', 'is_active', new_column_name='is_deleted', schema='roombooking')
    op.drop_index('ix_rooms_is_active', table_name='rooms', schema='roombooking')
    op.execute("UPDATE roombooking.rooms SET is_deleted = NOT is_deleted")


def downgrade():
    op.alter_column('rooms', 'is_deleted', new_column_name='is_active', schema='roombooking')
    op.create_index(None, 'rooms', ['is_active'], schema='roombooking')
    op.execute("UPDATE roombooking.rooms SET is_active = NOT is_active")
