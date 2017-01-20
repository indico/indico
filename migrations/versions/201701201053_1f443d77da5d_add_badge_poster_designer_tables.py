"""Add badge/poster designer tables

Revision ID: 1f443d77da5d
Revises: 459e5ec98b96
Create Date: 2017-01-20 10:53:30.734429
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy import UTCDateTime
from indico.modules.designer.models.templates import TemplateType
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '1f443d77da5d'
down_revision = '459e5ec98b96'


def upgrade():
    op.create_table('designer_templates',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('type', PyIntEnum(TemplateType), nullable=False),
                    sa.Column('title', sa.String(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=True, index=True),
                    sa.Column('category_id', sa.Integer(), nullable=True, index=True),
                    sa.Column('data', postgresql.JSON(), nullable=False),
                    sa.Column('background_image_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['category_id'], ['categories.categories.id']),
                    sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
                    sa.PrimaryKeyConstraint('id'),
                    sa.CheckConstraint('(event_id IS NULL) != (category_id IS NULL)', 'event_xor_category_id_null'),
                    schema='indico')
    op.create_table('designer_image_files',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('template_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('storage_backend', sa.String(), nullable=False),
                    sa.Column('content_type', sa.String(), nullable=False),
                    sa.Column('size', sa.BigInteger(), nullable=False),
                    sa.Column('storage_file_id', sa.String(), nullable=False),
                    sa.Column('filename', sa.String(), nullable=False),
                    sa.Column('created_dt', UTCDateTime, nullable=False),
                    sa.ForeignKeyConstraint(['template_id'], ['indico.designer_templates.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='indico')
    op.create_foreign_key(None,
                          'designer_templates', 'designer_image_files',
                          ['background_image_id'], ['id'],
                          source_schema='indico', referent_schema='indico')


def downgrade():
    op.drop_constraint('fk_designer_templates_background_image_id_designer_image_files', 'designer_templates',
                       schema='indico')
    op.drop_table('designer_image_files', schema='indico')
    op.drop_table('designer_templates', schema='indico')
