"""Partially added abstract judgments to Postgres

Revision ID: da0ddef1744
Revises: 4878972d7e2f
Create Date: 2016-03-31 17:19:33.252461
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = 'da0ddef1744'
down_revision = '4878972d7e2f'


def upgrade():
    op.create_table('judgments',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('creation_dt', UTCDateTime, nullable=False),
                    sa.Column('abstract_id', sa.Integer(), nullable=False),
                    sa.Column('track_id', sa.Integer(), nullable=False),
                    sa.Column('judge_user_id', sa.Integer(), nullable=False),
                    sa.Column('accepted_type_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['abstract_id'],
                                            [u'event_abstracts.abstracts.id']),
                    sa.ForeignKeyConstraint(['accepted_type_id'],
                                            [u'events.contribution_types.id']),
                    sa.ForeignKeyConstraint(['judge_user_id'],
                                            [u'users.users.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='event_abstracts')
    op.create_index(None, 'judgments', ['abstract_id'], unique=False, schema='event_abstracts')
    op.create_index(None, 'judgments', ['accepted_type_id'], unique=False, schema='event_abstracts')
    op.create_index(None, 'judgments', ['creation_dt'], unique=False, schema='event_abstracts')
    op.create_index(None, 'judgments', ['judge_user_id'], unique=False, schema='event_abstracts')
    op.create_index(None, 'judgments', ['abstract_id', 'track_id', 'judge_user_id'], unique=True,
                    schema='event_abstracts')


def downgrade():
    op.drop_table('judgments', schema='event_abstracts')
