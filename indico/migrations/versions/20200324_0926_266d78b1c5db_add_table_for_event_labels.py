"""Add table for event labels

Revision ID: 266d78b1c5db
Revises: 18a1088f1ea8
Create Date: 2020-03-24 09:26:07.095052
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '266d78b1c5db'
down_revision = '18a1088f1ea8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'labels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_index('ix_uq_labels_title_lower', 'labels', [sa.text('lower(title)')], unique=True, schema='events')
    op.add_column('events', sa.Column('label_id', sa.Integer(), nullable=True), schema='events')
    op.add_column('events', sa.Column('label_message', sa.Text(), nullable=False, server_default=''), schema='events')
    op.alter_column('events', 'label_message', server_default=None, schema='events')
    op.create_foreign_key(None, 'events', 'labels', ['label_id'], ['id'], source_schema='events',
                          referent_schema='events')
    op.create_index(None, 'events', ['label_id'], unique=False, schema='events')


def downgrade():
    op.drop_column('events', 'label_id', schema='events')
    op.drop_column('events', 'label_message', schema='events')
    op.drop_table('labels', schema='events')
