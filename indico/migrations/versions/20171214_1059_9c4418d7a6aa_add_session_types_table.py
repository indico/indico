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
    # Create session type table
    op.create_table('session_types',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('is_poster', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['event_id'], [u'events.events.id']),
                    sa.PrimaryKeyConstraint('id', name=op.f('pk_session_types')),
                    schema='events')
    op.create_index(None, 'session_types', ['event_id'], unique=False, schema='events')
    op.create_index('ix_uq_session_types_event_id_name_lower', 'session_types', ['event_id', sa.text('lower(name)')],
                    unique=True, schema='events')

    # Add session type to sessions
    op.add_column('sessions', sa.Column('type_id', sa.Integer(), nullable=True), schema='events')
    op.create_index(None, 'sessions', ['type_id'], unique=False, schema='events')
    op.create_foreign_key(None, 'sessions', 'session_types', ['type_id'], ['id'], source_schema='events',
                          referent_schema='events')

    # Migrate poster sessions to sessions with poster session type
    op.execute('''
      INSERT INTO events.session_types (event_id, name, is_poster)
      SELECT event_id, 'poster session', true
      FROM events.sessions
      WHERE is_poster = true
      GROUP BY event_id;
      UPDATE events.sessions
      SET type_id = (SELECT events.session_types.id FROM events.session_types
                     WHERE events.sessions.event_id = events.session_types.event_id
                     AND events.sessions.is_poster = true);
    ''')
    op.drop_column('sessions', 'is_poster', schema='events')


def downgrade():
    # Migrate poster session types to poster sessions
    op.add_column('sessions', sa.Column('is_poster', sa.Boolean(), nullable=False, server_default='false'),
                  schema='events')
    op.execute('''
        UPDATE events.sessions
        SET is_poster = true
        WHERE (SELECT events.session_types.id FROM events.session_types
        WHERE events.sessions.type_id = events.session_types.id
        AND events.session_types.is_poster = true)
        IS NOT NULL
    ''')

    # Delete session type from sessions
    op.drop_column('sessions', 'type_id', schema='events')
    # Delete session types table
    op.drop_table('session_types', schema='events')
