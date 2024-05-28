"""Add private registration form

Revision ID: 67e92eeca34f
Revises: 4e32f4d5ebe4
Create Date: 2024-05-01 14:31:21.090459
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '67e92eeca34f'
down_revision = '4e32f4d5ebe4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms', sa.Column('private', sa.Boolean(), nullable=False,
                  server_default='false'), schema='event_registration')
    op.alter_column('forms', 'private', server_default=None, schema='event_registration')
    op.add_column(
        'forms',
        sa.Column(
            'uuid',
            postgresql.UUID(),
            nullable=False,
            server_default=sa.text('''
                uuid_in(overlay(overlay(md5(random()::text || ':' || clock_timestamp()::text) placing '4' from 13)
                placing to_hex(floor(random()*(11-8+1) + 8)::int)::text from 17)::cstring)''')
        ),
        schema='event_registration'
    )
    op.alter_column('forms', 'uuid', server_default=None, schema='event_registration')
    op.create_unique_constraint(None, 'forms', ['uuid'], schema='event_registration')


def downgrade():
    op.drop_column('forms', 'uuid', schema='event_registration')
    op.drop_column('forms', 'private', schema='event_registration')
