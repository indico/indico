"""Add email template model

Revision ID: 86873b143da2
Revises: 6fac01c501b6
Create Date: 2025-09-12 21:42:26.537009
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '86873b143da2'
down_revision = '6fac01c501b6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('email_templates',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('title', sa.String(), nullable=False),
                    sa.Column('type', sa.String(), nullable=False),
                    sa.Column('subject', sa.String(), nullable=False),
                    sa.Column('body', sa.Text(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=True, index=True),
                    sa.Column('category_id', sa.Integer(), nullable=True, index=True),
                    sa.Column('rules', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
                    sa.Column('is_active', sa.Boolean(), nullable=False),
                    sa.Column('is_system_template', sa.Boolean(), nullable=False),
                    sa.CheckConstraint('(event_id IS NULL) != (category_id IS NULL)',
                                       name='event_xor_category_id_null'),
                    sa.ForeignKeyConstraint(['category_id'], ['categories.categories.id']),
                    sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='indico')


def downgrade():
    op.drop_table('email_templates', schema='indico')
