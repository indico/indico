"""Add session types table

Revision ID: 9c4418d7a6aa
Revises: 2af245be72a6
Create Date: 2017-12-14 10:59:47.872426
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '9c4418d7a6aa'
down_revision = '2af245be72a6'
branch_labels = None
depends_on = None


def upgrade():
    # Create session type table
    op.create_table('session_types',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('is_poster', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='events')
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
      SELECT event_id, 'Poster session', true
      FROM events.sessions
      WHERE is_poster
      GROUP BY event_id;
      
      UPDATE events.sessions s
      SET type_id = st.id
      FROM events.session_types st
      WHERE st.event_id = s.event_id AND s.is_poster;
    ''')
    op.drop_column('sessions', 'is_poster', schema='events')


def downgrade():
    # Migrate poster session types to poster sessions
    op.add_column('sessions', sa.Column('is_poster', sa.Boolean(), nullable=False, server_default='false'),
                  schema='events')
    op.execute('''
        UPDATE events.sessions s
        SET is_poster = true
        FROM events.session_types st
        WHERE st.id = s.type_id AND st.is_poster;
    ''')

    # Delete session type from sessions
    op.drop_column('sessions', 'type_id', schema='events')
    # Delete session types table
    op.drop_table('session_types', schema='events')
