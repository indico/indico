"""Delete user links table

Revision ID: 399ef1b54f18
Revises: 3f98ee63652f
Create Date: 2017-02-08 10:56:17.508638
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg


# revision identifiers, used by Alembic.
revision = '399ef1b54f18'
down_revision = '3f98ee63652f'


def upgrade():
    op.drop_table('links', schema='users')


def downgrade():
    op.create_table('links',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('type', sa.String(), nullable=False),
                    sa.Column('role', sa.String(), nullable=False),
                    sa.Column('data', pg.JSON(), nullable=False),
                    sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='users')
    op.create_index(None, 'links', ['user_id', 'type', 'role'], unique=False, schema='users')
