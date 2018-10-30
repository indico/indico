"""Add room features

Revision ID: 7e03b2262e9e
Revises: 868c04697dd7
Create Date: 2018-10-26 13:22:27.627996
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '7e03b2262e9e'
down_revision = '868c04697dd7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'features',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False, index=True, unique=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('icon', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='roombooking'
    )
    op.create_table(
        'equipment_features',
        sa.Column('equipment_id', sa.Integer(), nullable=False, autoincrement=False),
        sa.Column('feature_id', sa.Integer(), nullable=False, autoincrement=False),
        sa.ForeignKeyConstraint(['equipment_id'], ['roombooking.equipment_types.id']),
        sa.ForeignKeyConstraint(['feature_id'], ['roombooking.features.id']),
        sa.PrimaryKeyConstraint('equipment_id', 'feature_id'),
        schema='roombooking'
    )


def downgrade():
    op.drop_table('equipment_features', schema='roombooking')
    op.drop_table('features', schema='roombooking')
