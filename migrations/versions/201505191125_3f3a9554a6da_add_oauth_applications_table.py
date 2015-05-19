"""Add OAuth applications table

Revision ID: 3f3a9554a6da
Revises: 45f41372799d
Create Date: 2015-05-19 11:25:26.268379
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '3f3a9554a6da'
down_revision = '45f41372799d'


def upgrade():
    op.execute('CREATE SCHEMA oauth')
    op.create_table('applications',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('description', sa.Text(), nullable=False),
                    sa.Column('client_id', sa.String(), nullable=False),
                    sa.Column('client_secret', sa.String(), nullable=False),
                    sa.Column('is_enabled', sa.Boolean(), nullable=False),
                    sa.Column('is_trusted', sa.Boolean(), nullable=False),
                    sa.Column('default_scopes', sa.Text(), nullable=True),
                    sa.Column('redirect_uris', sa.Text(), nullable=True),
                    sa.PrimaryKeyConstraint('id', name=op.f('pk_applications')),
                    sa.UniqueConstraint('client_id', name=op.f('uq_applications_client_id')),
                    schema='oauth')


def downgrade():
    op.drop_table('applications', schema='oauth')
    op.execute('DROP SCHEMA oauth')
