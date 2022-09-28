"""Move affiliation into users table

Revision ID: 0c4bb2973536
Revises: 1950e5d12ab5
Create Date: 2022-05-31 14:39:54.326359
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '0c4bb2973536'
down_revision = '1950e5d12ab5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('affiliation', sa.String(), nullable=False, server_default=''), schema='users')
    op.add_column('users', sa.Column('affiliation_id', sa.Integer(), nullable=True), schema='users')
    op.alter_column('users', 'affiliation', server_default=None, schema='users')
    op.execute('''
        UPDATE users.users u
        SET affiliation = ua.name, affiliation_id = ua.affiliation_id
        FROM users.affiliations ua
        WHERE u.id = ua.user_id;
    ''')
    op.create_index(None, 'users', ['affiliation'], unique=False, schema='users')
    op.create_index(None, 'users', ['affiliation_id'], unique=False, schema='users')
    op.create_foreign_key(None, 'users', 'affiliations', ['affiliation_id'], ['id'],
                          source_schema='users', referent_schema='indico')
    op.create_index(
        op.f('ix_users_affiliation_unaccent'),
        'users',
        [sa.text('indico.indico_unaccent(lower(affiliation))')],
        postgresql_using='gin',
        postgresql_ops={'indico.indico_unaccent(lower(affiliation))': 'gin_trgm_ops'},
        schema='users'
    )
    op.drop_table('affiliations', schema='users')


def downgrade():
    op.create_table(
        'affiliations',
        sa.Column('id', sa.Integer(), server_default=sa.text("nextval('users.affiliations_id_seq'::regclass)"), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('name', sa.String(), autoincrement=False, nullable=False),
        sa.Column('affiliation_id', sa.Integer(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['affiliation_id'], ['indico.affiliations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='users'
    )
    op.execute('''
        INSERT INTO users.affiliations (user_id, name, affiliation_id)
        SELECT id, affiliation, affiliation_id FROM users.users;
    ''')
    op.create_index(None, 'affiliations', ['user_id'], unique=False, schema='users')
    op.create_index(None, 'affiliations', ['name'], unique=False, schema='users')
    op.create_index(None, 'affiliations', ['affiliation_id'], unique=False, schema='users')
    op.create_index(
        op.f('ix_affiliations_name_unaccent'),
        'affiliations',
        [sa.text('indico.indico_unaccent(lower(name))')],
        postgresql_using='gin',
        postgresql_ops={'indico.indico_unaccent(lower(name))': 'gin_trgm_ops'},
        schema='users'
    )
    op.drop_column('users', 'affiliation_id', schema='users')
    op.drop_column('users', 'affiliation', schema='users')
