"""Add participation regforms

Revision ID: 38641fb3afac
Revises: 1d741fc6586c
Create Date: 2015-10-28 10:25:51.199436
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '38641fb3afac'
down_revision = '1d741fc6586c'


def upgrade():
    op.add_column('forms', sa.Column('is_participation', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_registration')
    op.alter_column('forms', 'is_participation', server_default=None, schema='event_registration')
    op.create_index('ix_uq_forms_participation', 'forms', ['event_id'], unique=True, schema='event_registration',
                    postgresql_where=sa.text('is_participation AND NOT is_deleted'))


def downgrade():
    op.drop_index('ix_uq_forms_participation', table_name='forms', schema='event_registration')
    op.drop_column('forms', 'is_participation', schema='event_registration')
