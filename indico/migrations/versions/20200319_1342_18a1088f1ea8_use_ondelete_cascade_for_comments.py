"""Use ondelete=cascade for comments

Revision ID: 18a1088f1ea8
Revises: b3ce69ab24d9
Create Date: 2020-03-19 13:42:35.728545
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '18a1088f1ea8'
down_revision = 'b3ce69ab24d9'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('fk_comments_revision_id_revisions', 'comments', schema='event_editing')
    op.create_foreign_key(None, 'comments', 'revisions', ['revision_id'], ['id'],
                          source_schema='event_editing', referent_schema='event_editing', ondelete='CASCADE')


def downgrade():
    op.drop_constraint('fk_comments_revision_id_revisions', 'comments', schema='event_editing')
    op.create_foreign_key(None, 'comments', 'revisions', ['revision_id'], ['id'],
                          source_schema='event_editing', referent_schema='event_editing')
