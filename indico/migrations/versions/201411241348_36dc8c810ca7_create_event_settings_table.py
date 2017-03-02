"""Create event settings table

Revision ID: 36dc8c810ca7
Revises: 48084f0df78c
Create Date: 2014-11-24 13:48:04.662300
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '36dc8c810ca7'
down_revision = '48084f0df78c'


def upgrade():
    op.create_table('settings',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('module', sa.String(), nullable=False, index=True),
                    sa.Column('name', sa.String(), nullable=False, index=True),
                    sa.Column('value', postgresql.JSON(), nullable=False),
                    sa.Column('event_id', sa.String(), nullable=False, index=True),
                    sa.CheckConstraint('module = lower(module)', 'lowercase_module'),
                    sa.CheckConstraint('name = lower(name)', 'lowercase_name'),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('event_id', 'module', 'name'),
                    schema='events')
    op.create_index('ix_settings_event_id_module', 'settings', ['event_id', 'module'], unique=False, schema='events')
    op.create_index('ix_settings_event_id_module_name', 'settings', ['event_id', 'module', 'name'], unique=False,
                    schema='events')


def downgrade():
    op.drop_table('settings', schema='events')
