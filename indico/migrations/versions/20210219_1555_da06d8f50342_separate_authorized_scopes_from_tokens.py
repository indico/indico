"""Separate authorized scopes from tokens

Revision ID: da06d8f50342
Revises: 3782de7970da
Create Date: 2021-02-19 15:55:53.134744
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'da06d8f50342'
down_revision = '3782de7970da'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'application_user_links',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('application_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('scopes', postgresql.ARRAY(sa.String()), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['oauth.applications.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.UniqueConstraint('application_id', 'user_id'),
        schema='oauth'
    )
    op.create_unique_constraint(None, 'tokens', ['application_id', 'user_id', 'scopes'], schema='oauth')
    op.drop_constraint('uq_tokens_application_id_user_id', 'tokens', schema='oauth')
    op.execute('''
        INSERT INTO oauth.application_user_links (application_id, user_id, scopes)
        SELECT application_id, user_id, scopes FROM oauth.tokens;
    ''')
    op.add_column('tokens', sa.Column('app_user_link_id', sa.Integer(), nullable=True), schema='oauth')
    op.create_index(None, 'tokens', ['app_user_link_id'], unique=False, schema='oauth')
    op.create_unique_constraint(None, 'tokens', ['app_user_link_id', 'scopes'], schema='oauth')
    op.execute('''
        UPDATE oauth.tokens t SET app_user_link_id = (
            SELECT id FROM oauth.application_user_links WHERE application_id = t.application_id AND user_id = t.user_id
        );
    ''')
    op.alter_column('tokens', 'app_user_link_id', nullable=False, schema='oauth')
    op.create_foreign_key(None, 'tokens', 'application_user_links', ['app_user_link_id'], ['id'],
                          source_schema='oauth', referent_schema='oauth', ondelete='CASCADE')
    op.drop_column('tokens', 'application_id', schema='oauth')
    op.drop_column('tokens', 'user_id', schema='oauth')


def downgrade():
    op.add_column('tokens', sa.Column('application_id', sa.Integer(), nullable=True), schema='oauth')
    op.add_column('tokens', sa.Column('user_id', sa.Integer(), nullable=True), schema='oauth')
    op.create_index(None, 'tokens', ['user_id'], unique=False, schema='oauth')
    op.execute('''
        DELETE FROM oauth.tokens
        WHERE app_user_link_id IN (
            SELECT app_user_link_id FROM oauth.tokens GROUP BY app_user_link_id HAVING COUNT(*) > 1
        );

        UPDATE oauth.tokens t SET application_id = (
            SELECT application_id FROM oauth.application_user_links WHERE id = t.app_user_link_id
        ), user_id = (
            SELECT user_id FROM oauth.application_user_links WHERE id = t.app_user_link_id
        );
    ''')
    op.create_foreign_key(None, 'tokens', 'applications', ['application_id'], ['id'],
                          source_schema='oauth', referent_schema='oauth')
    op.create_foreign_key(None, 'tokens', 'users', ['user_id'], ['id'],
                          source_schema='oauth', referent_schema='users')
    op.alter_column('tokens', 'application_id', nullable=False, schema='oauth')
    op.alter_column('tokens', 'user_id', nullable=False, schema='oauth')
    op.drop_column('tokens', 'app_user_link_id', schema='oauth')
    op.create_unique_constraint(None, 'tokens', ['application_id', 'user_id'], schema='oauth')
    op.drop_table('application_user_links', schema='oauth')
