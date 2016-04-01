"""Partially added abstract judgmnts to Postgres

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
                                            [u'event_abstracts.abstracts.id'],
                                            name=op.f('fk_judgments_abstract_id_abstracts')),
                    sa.ForeignKeyConstraint(['accepted_type_id'],
                                            [u'events.contribution_types.id'],
                                            name=op.f('fk_judgments_accepted_type_id_contribution_types')),
                    sa.ForeignKeyConstraint(['judge_user_id'],
                                            [u'users.users.id'],
                                            name=op.f('fk_judgments_user_id_users')),
                    sa.PrimaryKeyConstraint('id', name=op.f('pk_judgments')),
                    schema='event_abstracts')
    op.create_index(op.f('ix_judgments_abstract_id'),
                    'judgments',
                    ['abstract_id'],
                    unique=False,
                    schema='event_abstracts')
    op.create_index(op.f('ix_judgments_accepted_type_id'),
                    'judgments',
                    ['accepted_type_id'],
                    unique=False,
                    schema='event_abstracts')
    op.create_index(op.f('ix_judgments_creation_dt'),
                    'judgments',
                    ['creation_dt'],
                    unique=False,
                    schema='event_abstracts')
    op.create_index(op.f('ix_judgments_judge_user_id'),
                    'judgments',
                    ['judge_user_id'],
                    unique=False,
                    schema='event_abstracts')
    op.create_index(op.f('ix_uq_judgments_abstract_id_track_id_judge_user_id'),
                    'judgments',
                    ['abstract_id', 'track_id', 'judge_user_id'],
                    unique=True,
                    schema='event_abstracts')


def downgrade():
    op.drop_index(op.f('ix_uq_judgments_abstract_id_track_id_judge_user_id'),
                  table_name='judgments',
                  schema='event_abstracts')
    op.drop_index(op.f('ix_judgments_judge_user_id'), table_name='judgments', schema='event_abstracts')
    op.drop_index(op.f('ix_judgments_creation_dt'), table_name='judgments', schema='event_abstracts')
    op.drop_index(op.f('ix_judgments_accepted_type_id'), table_name='judgments', schema='event_abstracts')
    op.drop_index(op.f('ix_judgments_abstract_id'), table_name='judgments', schema='event_abstracts')
    op.drop_table('judgments', schema='event_abstracts')
