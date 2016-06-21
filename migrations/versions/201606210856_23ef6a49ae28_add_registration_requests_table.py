"""Add RegistrationRequest table

Revision ID: 23ef6a49ae28
Revises: 3bdd6bf0181a
Create Date: 2016-06-21 08:56:11.768469
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '23ef6a49ae28'
down_revision = '3bdd6bf0181a'


def upgrade():
    op.create_table(
        'registration_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('comment', sa.String(), nullable=True),
        sa.Column('user_data', postgresql.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='users'
    )


def downgrade():
    op.drop_table('registration_requests', schema='users')
