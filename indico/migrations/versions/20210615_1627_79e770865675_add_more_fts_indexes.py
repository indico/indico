"""Add more FTS indexes

Revision ID: 79e770865675
Revises: fda76e047e87
Create Date: 2021-06-15 16:27:35.922384
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '79e770865675'
down_revision = 'fda76e047e87'
branch_labels = None
depends_on = None


def upgrade():
    op.create_check_constraint('valid_title', 'contributions', "title != ''", schema='events')
    op.create_check_constraint('valid_title', 'subcontributions', "title != ''", schema='events')
    op.create_index('ix_contributions_title_fts', 'contributions', [sa.text("to_tsvector('simple', title)")],
                    schema='events', postgresql_using='gin')
    op.create_index('ix_subcontributions_title_fts', 'subcontributions', [sa.text("to_tsvector('simple', title)")],
                    schema='events', postgresql_using='gin')
    op.create_index('ix_attachments_title_fts', 'attachments', [sa.text("to_tsvector('simple', title)")],
                    schema='attachments', postgresql_using='gin')
    op.create_index('ix_contributions_description_fts', 'contributions',
                    [sa.text("to_tsvector('simple', description)")],
                    schema='events', postgresql_using='gin')
    op.create_index('ix_subcontributions_description_fts', 'subcontributions',
                    [sa.text("to_tsvector('simple', description)")],
                    schema='events', postgresql_using='gin')
    op.create_index('ix_notes_html_fts', 'notes', [sa.text("to_tsvector('simple', html)")],
                    schema='events', postgresql_using='gin')


def downgrade():
    op.drop_constraint('ck_contributions_valid_title', 'contributions', schema='events')
    op.drop_constraint('ck_subcontributions_valid_title', 'subcontributions', schema='events')
    op.drop_index('ix_contributions_title_fts', table_name='contributions', schema='events')
    op.drop_index('ix_subcontributions_title_fts', table_name='subcontributions', schema='events')
    op.drop_index('ix_attachments_title_fts', table_name='attachments', schema='attachments')
    op.drop_index('ix_contributions_description_fts', table_name='contributions', schema='events')
    op.drop_index('ix_subcontributions_description_fts', table_name='subcontributions', schema='events')
    op.drop_index('ix_notes_html_fts', table_name='notes', schema='events')
