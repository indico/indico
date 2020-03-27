"""Associate file types with editable types

Revision ID: 6444c893a21f
Revises: 56a26a721717
Create Date: 2020-03-27 15:01:29.736555
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.events.editing.models.editable import EditableType


# revision identifiers, used by Alembic.
revision = '6444c893a21f'
down_revision = '56a26a721717'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('file_types', sa.Column('type', PyIntEnum(EditableType), nullable=False,
                                          server_default='1'), schema='event_editing')
    op.alter_column('file_types', 'type', server_default=None, schema='event_editing')
    op.drop_index('ix_uq_file_types_event_id_name_lower', 'file_types', schema='event_editing')
    op.create_index('ix_uq_file_types_event_id_type_name_lower', 'file_types',
                    ['event_id', 'type', sa.text('lower(name)')], unique=True, schema='event_editing')


def downgrade():
    op.drop_index('ix_uq_file_types_event_id_type_name_lower', 'file_types', schema='event_editing')
    op.execute('DELETE FROM event_editing.file_types WHERE type != 1')
    op.drop_column('file_types', 'type', schema='event_editing')
    op.create_index('ix_uq_file_types_event_id_name_lower', 'file_types', ['event_id', sa.text('lower(name)')],
                    unique=True, schema='event_editing')
