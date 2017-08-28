"""Add file MD5 checksum

Revision ID: dc2c2fa6f5be
Revises: bf8a98f310b3
Create Date: 2017-08-23 16:35:36.634285
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'dc2c2fa6f5be'
down_revision = 'bf8a98f310b3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('files', sa.Column('md5', sa.String, nullable=False, server_default=''), schema='attachments')
    op.add_column('files', sa.Column('md5', sa.String, nullable=False, server_default=''), schema='event_abstracts')
    op.add_column(
        'files',
        sa.Column('md5', sa.String, nullable=False, server_default=''),
        schema='event_paper_reviewing'
    )
    op.add_column(
        'templates',
        sa.Column('md5', sa.String, nullable=False, server_default=''),
        schema='event_paper_reviewing'
    )
    op.add_column(
        'registration_data',
        sa.Column('md5', sa.String, nullable=True),
        schema='event_registration'
    )
    op.add_column('image_files', sa.Column('md5', sa.String, nullable=False, server_default=''), schema='events')
    op.add_column('static_sites', sa.Column('md5', sa.String, nullable=True), schema='events')
    op.add_column(
        'designer_image_files',
        sa.Column('md5', sa.String, nullable=False, server_default=''),
        schema='indico'
    )
    op.alter_column('files', 'md5', server_default=None, schema='attachments')
    op.alter_column('files', 'md5', server_default=None, schema='event_abstracts')
    op.alter_column('files', 'md5', server_default=None, schema='event_paper_reviewing')
    op.alter_column('templates', 'md5', server_default=None, schema='event_paper_reviewing')
    op.alter_column('image_files', 'md5', server_default=None, schema='events')
    op.alter_column('designer_image_files', 'md5', server_default=None, schema='indico')
    for table in ('event_registration.registration_data', 'events.static_sites'):
        op.execute("""UPDATE {} SET md5 = '' WHERE storage_file_id IS NOT NULL""".format(table))


def downgrade():
    op.drop_column('designer_image_files', 'md5', schema='indico')
    op.drop_column('static_sites', 'md5', schema='events')
    op.drop_column('image_files', 'md5', schema='events')
    op.drop_column('registration_data', 'md5', schema='event_registration')
    op.drop_column('templates', 'md5', schema='event_paper_reviewing')
    op.drop_column('files', 'md5', schema='event_paper_reviewing')
    op.drop_column('files', 'md5', schema='event_abstracts')
    op.drop_column('files', 'md5', schema='attachments')
