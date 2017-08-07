"""Add ticket_template to registration_form table

Revision ID: 75060428e775
Revises: ebca3e91b139
Create Date: 2017-07-24 11:25:25.563180
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '75060428e775'
down_revision = 'ebca3e91b139'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms', sa.Column('ticket_template_id', sa.Integer(), nullable=True, index=True),
                  schema='event_registration')
    op.create_foreign_key(None, 'forms', 'designer_templates',
                          ['ticket_template_id'], ['id'], source_schema='event_registration', referent_schema='indico')


def downgrade():
    op.drop_column('forms', 'ticket_template_id', schema='event_registration')
