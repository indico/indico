"""Remove JSONStringBridge from RoomAttribute

Revision ID: 22b58de5f40f
Revises: 2dcc90572846
Create Date: 2014-08-08 11:01:51.728091
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '22b58de5f40f'
down_revision = '2dcc90572846'


def upgrade():
    upgrade_schema()


def downgrade():
    downgrade_schema()


def upgrade_schema():
    op.add_column('room_attributes', sa.Column('is_hidden', sa.Boolean()))
    op.add_column('room_attributes', sa.Column('is_required', sa.Boolean()))
    op.add_column('room_attributes', sa.Column('type', sa.String()))
    op.execute(sa.text(
        """
        UPDATE room_attributes
        SET
          is_hidden = json_extract_path_text(raw_data::json, 'is_hidden')::boolean,
          is_required = json_extract_path_text(raw_data::json, 'is_required')::boolean,
          "type" = json_extract_path_text(raw_data::json, 'type')
        """
    ))
    op.alter_column('room_attributes', 'is_hidden', nullable=False)
    op.alter_column('room_attributes', 'is_required', nullable=False)
    op.alter_column('room_attributes', 'type', nullable=False)
    op.drop_column('room_attributes', 'raw_data')
    op.alter_column('rooms_attributes_association', 'raw_data', new_column_name='value')
    op.execute(sa.text("ALTER TABLE rooms_attributes_association ALTER COLUMN value TYPE json USING value::json"))


def downgrade_schema():
    op.alter_column('rooms_attributes_association', 'value', type_=sa.String, new_column_name='raw_data')
    op.add_column('room_attributes', sa.Column('raw_data', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.execute(sa.text(
        """
        UPDATE room_attributes ra
        SET raw_data = (SELECT row_to_json(x) FROM (
          SELECT "type", is_hidden, is_required
          FROM room_attributes
          WHERE id = ra.id) x);
        """
    ))
    op.drop_column('room_attributes', 'type')
    op.drop_column('room_attributes', 'is_required')
    op.drop_column('room_attributes', 'is_hidden')
