"""Add event url shortcut

Revision ID: 27382212a99c
Revises: 2287c5d5680c
Create Date: 2017-01-10 15:58:11.040221
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '27382212a99c'
down_revision = '2287c5d5680c'


def upgrade():
    op.add_column('events', sa.Column('url_shortcut', sa.String(), nullable=True), schema='events')
    op.create_index('ix_uq_events_url_shortcut', 'events', [sa.text('lower(url_shortcut)')], unique=True,
                    postgresql_where=sa.text('NOT is_deleted'), schema='events')
    op.create_check_constraint('url_shortcut_not_empty', 'events', "url_shortcut != ''", schema='events')


def downgrade():
    op.drop_constraint('ck_events_url_shortcut_not_empty', 'events', schema='events')
    op.drop_column('events', 'url_shortcut', schema='events')
