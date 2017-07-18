"""Add backside_template column

Revision ID: 3ca338ed5192
Revises: be7bdea6dd4d
Create Date: 2017-05-17 11:33:30.295538
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '3ca338ed5192'
down_revision = 'be7bdea6dd4d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('designer_templates', sa.Column('backside_template_id', sa.Integer(), nullable=True), schema='indico')
    op.create_foreign_key(None,
                          'designer_templates', 'designer_templates',
                          ['backside_template_id'], ['id'],
                          source_schema='indico', referent_schema='indico')
    op.create_index(None, 'designer_templates', ['backside_template_id'], schema='indico')


def downgrade():
    op.drop_index('ix_designer_templates_backside_template_id', table_name='designer_templates', schema='indico')
    op.drop_constraint('fk_designer_templates_backside_template_id_designer_templates', 'designer_templates',
                       schema='indico')
    op.drop_column('designer_templates', 'backside_template_id', schema='indico')
