"""Add receipt data structures

Revision ID: 252d61f890a0
Revises: a707753d16e2
Create Date: 2021-10-01 15:30:14.789502
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '252d61f890a0'
down_revision = '0c4bb2973536'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'receipt_templates',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True, index=True),
        sa.Column('category_id', sa.Integer(), nullable=True, index=True),
        sa.Column('html', sa.String(), nullable=False),
        sa.Column('css', sa.String(), nullable=False),
        sa.Column('custom_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint('(event_id IS NULL) != (category_id IS NULL)', name='event_xor_category_id_null'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.categories.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        schema='indico',
    )


def downgrade():
    op.drop_table('receipt_templates', schema='indico')
