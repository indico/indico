"""Add is_default and tpl_path to abstract email templates

Revision ID: 799e2bc54124
Revises: af9d03d7073c
Create Date: 2026-02-03 11:04:06.572323
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '799e2bc54124'
down_revision = 'af9d03d7073c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('email_templates', sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'), schema='event_abstracts')
    op.alter_column('email_templates', 'is_default', server_default=None, schema='event_abstracts')
    op.add_column('email_templates', sa.Column('tpl_path', sa.String(), nullable=True), schema='event_abstracts')


def downgrade():
    op.drop_column('email_templates', 'is_default', schema='event_abstracts')
    op.drop_column('email_templates', 'tpl_path', schema='event_abstracts')
