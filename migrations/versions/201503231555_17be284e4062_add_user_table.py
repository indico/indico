"""Add user table

Revision ID: 17be284e4062
Revises: 2c9a1c09fce6
Create Date: 2015-03-23 15:55:34.087209
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.ddl import CreateSchema, DropSchema

from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.users.models.users import UserTitle

# revision identifiers, used by Alembic.
revision = '17be284e4062'
down_revision = '2c9a1c09fce6'


def upgrade():
    op.execute(CreateSchema('users'))
    op.create_table('users',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('first_name', sa.String(), nullable=False, index=True),
                    sa.Column('last_name', sa.String(), nullable=False, index=True),
                    sa.Column('title', PyIntEnum(UserTitle), nullable=False),
                    sa.Column('phone', sa.String(), nullable=False),
                    sa.Column('affiliation', sa.String(), nullable=False, index=True),
                    sa.Column('address', sa.Text(), nullable=False),
                    sa.Column('merged_into_id', sa.Integer(), nullable=True),
                    sa.Column('is_admin', sa.Boolean(), nullable=False, index=True),
                    sa.Column('is_blocked', sa.Boolean(), nullable=False),
                    sa.Column('is_deleted', sa.Boolean(), nullable=False),
                    sa.Column('is_pending', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['merged_into_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='users')
    op.create_table('emails',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('email', sa.String(), nullable=False, index=True),
                    sa.Column('is_primary', sa.Boolean(), nullable=False),
                    sa.Column('is_user_deleted', sa.Boolean(), nullable=False),
                    sa.CheckConstraint('email = lower(email)', name='lowercase_email'),
                    sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='users')
    op.create_index(None, 'emails', ['email'], unique=True, schema='users',
                    postgresql_where=sa.text('NOT is_user_deleted'))
    op.create_index(None, 'emails', ['user_id'], unique=True, schema='users',
                    postgresql_where=sa.text('is_primary AND NOT is_user_deleted'))


def downgrade():
    op.drop_table('emails', schema='users')
    op.drop_table('users', schema='users')
    op.execute(DropSchema('users'))
