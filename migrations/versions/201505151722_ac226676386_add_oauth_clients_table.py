"""Add OAuth clients table

Revision ID: ac226676386
Revises: 45f41372799d
Create Date: 2015-05-15 17:22:24.968899
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'ac226676386'
down_revision = '45f41372799d'


def upgrade():
    op.execute('CREATE SCHEMA oauth')
    op.create_table('clients',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('description', sa.Text(), nullable=True),
                    sa.Column('client_id', sa.String(), nullable=False),
                    sa.Column('client_secret', sa.String(), nullable=False),
                    sa.Column('is_confidential', sa.Boolean(), nullable=False),
                    sa.Column('is_enabled', sa.Boolean(), nullable=False),
                    sa.Column('is_trusted', sa.Boolean(), nullable=False),
                    sa.Column('_default_scopes', sa.Text(), nullable=True),
                    sa.Column('_redirect_uris', sa.Text(), nullable=True),
                    sa.PrimaryKeyConstraint('id', name=op.f('pk_clients')),
                    sa.UniqueConstraint('client_id', name=op.f('uq_clients_client_id')),
                    sa.UniqueConstraint('client_secret', name=op.f('uq_clients_client_secret')),
                    schema='oauth')


def downgrade():
    op.drop_table('clients', schema='oauth')
    op.execute('DROP SCHEMA oauth')
