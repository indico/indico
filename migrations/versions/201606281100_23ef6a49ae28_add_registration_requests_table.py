"""Add RegistrationRequest table

Revision ID: 23ef6a49ae28
Revises: 35a6ae289e03
Create Date: 2016-06-24 15:01:11.768469
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '23ef6a49ae28'
down_revision = '35a6ae289e03'


def upgrade():
    op.create_table(
        'registration_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('comment', sa.String(), nullable=True),
        sa.Column('user_data', postgresql.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("email = lower(email)", name='lowercase_email'),
        schema='users'
    )


def downgrade():
    op.drop_table('registration_requests', schema='users')
