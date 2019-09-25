"""Add signature token column to User

Revision ID: a2472148d2c5
Revises: f6fba869a27c
Create Date: 2019-10-21 13:50:50.046577
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a2472148d2c5'
down_revision = 'f6fba869a27c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column(
            'signing_secret',
            postgresql.UUID(),
            nullable=False,
            # give every user a 'signing_secret' column with a random UUID
            # thanks to the author of https://stackoverflow.com/a/21327318
            server_default=sa.text("""
                uuid_in(overlay(overlay(md5(random()::text || ':' || clock_timestamp()::text) placing '4' from 13)
                placing to_hex(floor(random()*(11-8+1) + 8)::int)::text from 17)::cstring)""")
        ),
        schema='users'
    )
    op.alter_column('users', 'signing_secret', server_default=None, schema='users')


def downgrade():
    op.drop_column('users', 'signing_secret', schema='users')
