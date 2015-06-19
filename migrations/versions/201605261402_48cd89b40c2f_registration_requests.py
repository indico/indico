"""Add table for registration requests

Revision ID: 48cd89b40c2f
Revises: 52bc314861ba
Create Date: 2016-05-26 14:02:31.301641
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '48cd89b40c2f'
down_revision = '52bc314861ba'


def upgrade():
    op.create_table(
        'registration_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('comment', sa.String(), nullable=True),
        sa.Column('approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        schema='users'
    )


def downgrade():
    op.drop_table('registration_requests', schema='users')
