"""Add speaker profile-related fields

Revision ID: 29e4999af408
Revises: c412156094d6
Create Date: 2026-07-27 13:25:38.098983
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '29e4999af408'
down_revision = 'c412156094d6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('persons', sa.Column('speaker_photo_file_id', sa.Integer(), nullable=True), schema='events')
    op.add_column('persons', sa.Column('speaker_description', sa.Text(), nullable=True), schema='events')
    op.add_column('persons', sa.Column('speaker_socials', postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema='events')
    op.create_foreign_key(None, 'persons', 'files', ['speaker_photo_file_id'], ['id'], source_schema='events', referent_schema='indico')


def downgrade():
    op.drop_column('persons', 'speaker_socials', schema='events')
    op.drop_column('persons', 'speaker_description', schema='events')
    op.drop_column('persons', 'speaker_photo_file_id', schema='events')
