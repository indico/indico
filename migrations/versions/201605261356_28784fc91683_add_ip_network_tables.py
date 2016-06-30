"""Add IP network tables

Revision ID: 28784fc91683
Revises: 52bc314861ba
Create Date: 2016-05-26 13:56:46.434597
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import PyIPNetwork


# revision identifiers, used by Alembic.
revision = '28784fc91683'
down_revision = '52bc314861ba'


def upgrade():
    op.create_table(
        'ip_network_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='indico'
    )
    op.create_index('ix_uq_ip_network_groups_name_lower', 'ip_network_groups', [sa.text('lower(name)')], unique=True,
                    schema='indico')
    op.create_table(
        'ip_networks',
        sa.Column('group_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('network', PyIPNetwork(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['indico.ip_network_groups.id']),
        sa.PrimaryKeyConstraint('group_id', 'network'),
        schema='indico'
    )


def downgrade():
    op.drop_table('ip_networks', schema='indico')
    op.drop_table('ip_network_groups', schema='indico')
