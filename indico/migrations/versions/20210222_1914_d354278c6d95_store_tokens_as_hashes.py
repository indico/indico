"""Store tokens as hashes

Revision ID: d354278c6d95
Revises: c36abe1c23c7
Create Date: 2021-02-22 19:14:03.752863
"""

import hashlib

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime
from indico.util.date_time import now_utc


# revision identifiers, used by Alembic.
revision = 'd354278c6d95'
down_revision = 'c36abe1c23c7'
branch_labels = None
depends_on = None


def sha256(token):
    return hashlib.sha256(str(token).encode()).hexdigest()


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    op.add_column('tokens', sa.Column('access_token_hash', sa.String(), nullable=True), schema='oauth')
    op.add_column('tokens', sa.Column('created_dt', UTCDateTime(), nullable=True), schema='oauth')
    conn.execute('UPDATE oauth.tokens SET created_dt = COALESCE(last_used_dt, %s)', (now_utc(),))
    op.alter_column('tokens', 'created_dt', nullable=False, schema='oauth')
    op.create_index(None, 'tokens', ['access_token_hash'], unique=True, schema='oauth')
    res = conn.execute('SELECT id, access_token FROM oauth.tokens')
    for token_id, access_token in res:
        conn.execute('UPDATE oauth.tokens SET access_token_hash = %s WHERE id = %s', (sha256(access_token), token_id))
    op.alter_column('tokens', 'access_token_hash', nullable=False, schema='oauth')
    op.drop_column('tokens', 'access_token', schema='oauth')
    op.drop_constraint('uq_tokens_app_user_link_id_scopes', 'tokens', schema='oauth')


def downgrade():
    op.execute('''
        DELETE FROM oauth.tokens
        WHERE (app_user_link_id, scopes) IN (
            SELECT app_user_link_id, scopes FROM oauth.tokens GROUP BY app_user_link_id, scopes HAVING COUNT(*) > 1
        );
    ''')
    op.create_unique_constraint(None, 'tokens', ['app_user_link_id', 'scopes'], schema='oauth')
    op.add_column(
        'tokens',
        sa.Column(
            'access_token',
            postgresql.UUID(),
            nullable=False,
            server_default=sa.text('''
                uuid_in(overlay(overlay(md5(random()::text || ':' || clock_timestamp()::text) placing '4' from 13)
                placing to_hex(floor(random()*(11-8+1) + 8)::int)::text from 17)::cstring)''')
        ),
        schema='oauth'
    )
    op.alter_column('tokens', 'access_token', server_default=None, schema='oauth')
    op.create_unique_constraint(None, 'tokens', ['access_token'], schema='oauth')
    op.drop_column('tokens', 'access_token_hash', schema='oauth')
    op.drop_column('tokens', 'created_dt', schema='oauth')
