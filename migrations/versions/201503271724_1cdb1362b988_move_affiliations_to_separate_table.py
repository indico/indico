"""Move affiliations to separate table

Revision ID: 1cdb1362b988
Revises: 4dae1727a586
Create Date: 2015-03-27 17:24:16.643074
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '1cdb1362b988'
down_revision = '4dae1727a586'


def upgrade():
    op.create_table('affiliations',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('name', sa.String(), nullable=False, index=True),
                    sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='users')
    op.execute('INSERT INTO users.affiliations (user_id, name) SELECT id, affiliation FROM users.users;')
    op.drop_column('users', 'affiliation', schema='users')


def downgrade():
    op.add_column('users', sa.Column('affiliation', sa.String, nullable=False, server_default=''), schema='users')
    op.create_index('ix_users_affiliation', 'users', ['affiliation'], unique=False, schema='users')
    op.execute('UPDATE users.users u SET affiliation = aff.name FROM users.affiliations aff WHERE aff.user_id = u.id')
    op.alter_column('users', 'affiliation', server_default=None, schema='users')
    op.drop_table('affiliations', schema='users')
