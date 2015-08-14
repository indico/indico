"""Added event-level stylesheet storage

Revision ID: 35e20fe25c8f
Revises: 2fd1bc34a83c
Create Date: 2015-08-14 13:19:09.311973
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '35e20fe25c8f'
down_revision = '2fd1bc34a83c'


def upgrade():
    op.create_table('css_files',
                    sa.Column('created_dt', UTCDateTime, nullable=False),
                    sa.Column('filename', sa.String(), nullable=False),
                    sa.Column('content_type', sa.String(), nullable=False),
                    sa.Column('size', sa.BigInteger(), nullable=False),
                    sa.Column('storage_backend', sa.String(), nullable=False),
                    sa.Column('storage_file_id', sa.String(), nullable=False),
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['event_id'], [u'events.events.id'],
                                            name=op.f('fk_css_files_event_id_events')),
                    sa.PrimaryKeyConstraint('id', name=op.f('pk_css_files')),
                    schema='events'
                    )
    op.create_index(op.f('ix_css_files_event_id'), 'css_files', ['event_id'], unique=False, schema='events')


def downgrade():
    op.drop_index(op.f('ix_css_files_event_id'), table_name='css_files', schema='events')
    op.drop_table('css_files', schema='events')
