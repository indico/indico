"""Add abstract email logs

Revision ID: 39a46a2830ab
Revises: 129262ccf1dd
Create Date: 2016-08-19 16:56:37.379574
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import UTCDateTime
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '39a46a2830ab'
down_revision = '129262ccf1dd'


def upgrade():
    op.create_table(
        'email_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('abstract_id', sa.Integer(), nullable=False, index=True),
        sa.Column('email_template_id', sa.Integer(), nullable=True, index=True),
        sa.Column('sent_dt', UTCDateTime, nullable=False),
        sa.Column('reciptients', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('data', postgresql.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['abstract_id'], ['event_abstracts.abstracts.id']),
        sa.ForeignKeyConstraint(['email_template_id'], ['event_abstracts.email_templates.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_abstracts'
    )


def downgrade():
    op.drop_table('email_logs', schema='event_abstracts')
