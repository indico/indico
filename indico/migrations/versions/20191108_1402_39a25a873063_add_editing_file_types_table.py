"""Add editing file_types table

Revision ID: 39a25a873063
Revises: bb522e9f9066
Create Date: 2019-11-08 14:02:33.351292
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.ddl import CreateSchema, DropSchema


# revision identifiers, used by Alembic.
revision = '39a25a873063'
down_revision = 'bb522e9f9066'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(CreateSchema('event_editing'))
    op.create_table(
        'file_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('extensions', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('allow_multiple_files', sa.Boolean(), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=False),
        sa.Column('publishable', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_editing'
    )
    op.create_index('ix_uq_file_types_event_id_name_lower', 'file_types', ['event_id', sa.text('lower(name)')],
                    unique=True, schema='event_editing')


def downgrade():
    op.drop_table('file_types', schema='event_editing')
    op.execute(DropSchema('event_editing'))
