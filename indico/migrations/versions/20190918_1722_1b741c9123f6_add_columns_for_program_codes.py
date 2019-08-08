"""Add columns for program codes

Revision ID: 1b741c9123f6
Revises: eefba82b42c5
Create Date: 2019-08-08 11:13:05.922963
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '1b741c9123f6'
down_revision = 'eefba82b42c5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('contributions', sa.Column('code', sa.String(), nullable=False, server_default=''), schema='events')
    op.add_column('subcontributions', sa.Column('code', sa.String(), nullable=False, server_default=''),
                  schema='events')
    op.add_column('session_blocks', sa.Column('code', sa.String(), nullable=False, server_default=''), schema='events')
    op.add_column('session_types', sa.Column('code', sa.String(), nullable=False, server_default=''), schema='events')
    op.alter_column('contributions', 'code', server_default=None, schema='events')
    op.alter_column('subcontributions', 'code', server_default=None, schema='events')
    op.alter_column('session_blocks', 'code', server_default=None, schema='events')
    op.alter_column('session_types', 'code', server_default=None, schema='events')


def downgrade():
    op.drop_column('session_types', 'code', schema='events')
    op.drop_column('session_blocks', 'code', schema='events')
    op.drop_column('subcontributions', 'code', schema='events')
    op.drop_column('contributions', 'code', schema='events')
