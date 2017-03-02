"""Add Event table

Revision ID: 365fe2261342
Revises: 3778dc365e54
Create Date: 2015-08-05 15:18:10.748257
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '365fe2261342'
down_revision = '3778dc365e54'


def upgrade():
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('logo_metadata', postgresql.JSON(), nullable=False),
        sa.Column('logo', sa.LargeBinary(), nullable=True),
        sa.Column('stylesheet_metadata', postgresql.JSON(), nullable=False),
        sa.Column('stylesheet', sa.Text(), nullable=True),
        sa.CheckConstraint("(logo IS NULL) = (logo_metadata::text = 'null')", name='valid_logo'),
        sa.CheckConstraint("(stylesheet IS NULL) = (stylesheet_metadata::text = 'null')", name='valid_stylesheet'),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )


def downgrade():
    op.drop_table('events', schema='events')
