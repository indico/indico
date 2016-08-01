"""Add email templates

Revision ID: 4d4b95748173
Revises: 15661b6cd066
Create Date: 2016-08-01 17:09:48.158327
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '4d4b95748173'
down_revision = '15661b6cd066'


def upgrade():
    op.create_table(
        'email_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('include_authors', sa.Boolean(), nullable=False),
        sa.Column('include_submitter', sa.Boolean(), nullable=False),
        sa.Column('include_coauthors', sa.Boolean(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('reply_to_address', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('extra_cc_emails', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('stop_on_match', sa.Boolean(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('conditions', postgresql.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_abstracts'
    )


def downgrade():
    op.drop_table('email_templates', schema='event_abstracts')
