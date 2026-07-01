"""Add created_by to registrations

Revision ID: d7e2a9c14f6b
Revises: e1e229910f7e
Create Date: 2026-06-29 12:00:00.000000
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'd7e2a9c14f6b'
down_revision = 'e1e229910f7e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('registrations', sa.Column('created_by_id', sa.Integer(), nullable=True),
                  schema='event_registration')
    op.create_index(None, 'registrations', ['created_by_id'], schema='event_registration')
    op.create_foreign_key(None, 'registrations', 'users', ['created_by_id'], ['id'],
                          source_schema='event_registration', referent_schema='users')


def downgrade():
    op.drop_column('registrations', 'created_by_id', schema='event_registration')
