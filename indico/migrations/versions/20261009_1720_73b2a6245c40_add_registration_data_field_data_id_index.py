"""Add registration_data field_data_id index

Revision ID: 73b2a6245c40
Revises: 91cd48f93283
Create Date: 2026-10-09 17:20:21.991174
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '73b2a6245c40'
down_revision = '91cd48f93283'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(None, 'registration_data', ['field_data_id'], schema='event_registration')


def downgrade():
    op.drop_index('ix_registration_data_field_data_id', table_name='registration_data', schema='event_registration')
