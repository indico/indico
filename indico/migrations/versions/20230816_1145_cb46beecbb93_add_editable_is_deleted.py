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
    op.create_index(None, 'editables', ['contribution_id', 'type'], unique=True, schema='event_editing',
                    postgresql_where=sa.text('NOT is_deleted'))


def downgrade():
    op.execute('''
        DELETE FROM event_editing.revision_files fi
        USING event_editing.revisions rev, event_editing.editables ed
        WHERE fi.revision_id = rev.id AND rev.editable_id = ed.id AND ed.is_deleted;

        DELETE FROM event_editing.revision_tags tag
        USING event_editing.revisions rev, event_editing.editables ed
        WHERE tag.revision_id = rev.id AND rev.editable_id = ed.id AND ed.is_deleted;

        DELETE FROM event_editing.revisions rev
        USING event_editing.editables ed
        WHERE rev.editable_id = ed.id AND ed.is_deleted;

        DELETE FROM event_editing.editables WHERE is_deleted;
    ''')
    op.drop_column('editables', 'is_deleted', schema='event_editing')
    op.create_unique_constraint(None, 'editables', ['contribution_id', 'type'], schema='event_editing')
