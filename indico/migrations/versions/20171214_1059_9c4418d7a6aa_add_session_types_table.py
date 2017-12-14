"""add session types table

Revision ID: 9c4418d7a6aa
Revises: 566d5de4e0e5
Create Date: 2017-12-14 10:59:47.872426
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '9c4418d7a6aa'
down_revision = '566d5de4e0e5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'session_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_poster', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_index(op.f('ix_session_types_event_id'), 'session_types', ['event_id'], unique=False, schema='events')
    op.create_foreign_key(op.f('fk_session_types_event_id_events'), 'session_types', 'events', ['event_id'], ['id'],
                          source_schema='events', referent_schema='events')
    op.add_column('sessions', sa.Column('type_id', sa.Integer(), nullable=True), schema='events')
    op.create_index(op.f('ix_sessions_type_id'), 'sessions', ['type_id'], unique=False, schema='events')
    op.create_foreign_key(op.f('fk_sessions_type_id_session_types'), 'sessions', 'session_types', ['type_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_constraint(op.f('fk_sessions_type_id_session_types'), 'sessions', schema='events', type_='foreignkey')
    op.drop_index(op.f('ix_sessions_type_id'), table_name='sessions', schema='events')
    op.drop_column('sessions', 'type_id', schema='events')
    op.drop_constraint(op.f('fk_session_types_event_id_events'), 'session_types', schema='events', type_='foreignkey')
    op.drop_index(op.f('ix_session_types_event_id'), table_name='session_types', schema='events')
    op.drop_table('session_types', schema='events')
