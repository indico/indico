"""Add evaluation tables

Revision ID: 3fcf833adc2d
Revises: 3778dc365e54
Create Date: 2015-07-27 11:14:06.639780
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '3fcf833adc2d'
down_revision = '3778dc365e54'


def upgrade():
    op.create_table(
        'evaluation_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('help', sa.Text(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('field_type', sa.String(), nullable=False),
        sa.Column('field_data', postgresql.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )


def downgrade():
    op.drop_table('evaluation_questions', schema='events')
