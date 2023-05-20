"""Add Editable.is_deleted

Revision ID: cb46beecbb93
Revises: 0af8f63aa603
Create Date: 2023-08-16 11:45:47.447151
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'cb46beecbb93'
down_revision = '0af8f63aa603'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('editables', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_editing')
    op.alter_column('editables', 'is_deleted', server_default=None, schema='event_editing')
    op.drop_constraint('uq_editables_contribution_id_type', 'editables', schema='event_editing')
    op.create_index(op.f('ix_uq_editables_contribution_id_type'), 'editables', ['contribution_id', 'type'], unique=True,
                    schema='event_editing', postgresql_where=sa.text('NOT is_deleted'))


def downgrade():
    op.drop_column('editables', 'is_deleted', schema='event_editing')
    op.drop_index('ix_uq_editables_contribution_id_type', table_name='editables', schema='event_editing')
    op.create_unique_constraint(None, 'editables', ['contribution_id', 'type'], schema='event_editing')
