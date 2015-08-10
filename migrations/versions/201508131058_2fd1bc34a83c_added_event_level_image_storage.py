"""Added event-level image storage

Revision ID: 2fd1bc34a83c
Revises: 365fe2261342
Create Date: 2015-08-13 10:58:25.469907
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '2fd1bc34a83c'
down_revision = '365fe2261342'


def upgrade():
    op.create_table('image_files',
                    sa.Column('created_dt', UTCDateTime, nullable=False),
                    sa.Column('filename', sa.String(), nullable=False),
                    sa.Column('content_type', sa.String(), nullable=False),
                    sa.Column('size', sa.BigInteger(), nullable=False),
                    sa.Column('storage_backend', sa.String(), nullable=False),
                    sa.Column('storage_file_id', sa.String(), nullable=False),
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), index=True, nullable=False),
                    sa.ForeignKeyConstraint(['event_id'], [u'events.events.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='events')
    op.create_table('legacy_image_id_map',
                    sa.Column('event_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('legacy_image_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('image_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['event_id'], [u'events.events.id']),
                    sa.ForeignKeyConstraint(['image_id'], [u'events.image_files.id']),
                    sa.PrimaryKeyConstraint('event_id', 'legacy_image_id'),
                    schema='events')


def downgrade():
    op.drop_table('legacy_image_id_map', schema='events')
    op.drop_table('image_files', schema='events')
