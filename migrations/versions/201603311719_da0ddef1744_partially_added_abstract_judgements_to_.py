"""Partially added abstract judgements to Postgres

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
    op.create_table('judgements',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('creation_dt', UTCDateTime, nullable=False),
                    sa.Column('abstract_id', sa.Integer(), nullable=False),
                    sa.Column('track_id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('accepted_type_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['abstract_id'],
                                            [u'event_abstracts.abstracts.id'],
                                            name=op.f('fk_judgements_abstract_id_abstracts')),
                    sa.ForeignKeyConstraint(['accepted_type_id'],
                                            [u'events.contribution_types.id'],
                                            name=op.f('fk_judgements_accepted_type_id_contribution_types')),
                    sa.ForeignKeyConstraint(['user_id'],
                                            [u'users.users.id'],
                                            name=op.f('fk_judgements_user_id_users')),
                    sa.PrimaryKeyConstraint('id', name=op.f('pk_judgements')),
                    schema='event_abstracts')
    op.create_index(op.f('ix_judgements_abstract_id'),
                    'judgements',
                    ['abstract_id'],
                    unique=False,
                    schema='event_abstracts')
    op.create_index(op.f('ix_judgements_accepted_type_id'),
                    'judgements',
                    ['accepted_type_id'],
                    unique=False,
                    schema='event_abstracts')
    op.create_index(op.f('ix_judgements_creation_dt'),
                    'judgements',
                    ['creation_dt'],
                    unique=False,
                    schema='event_abstracts')
    op.create_index(op.f('ix_judgements_user_id'),
                    'judgements',
                    ['user_id'],
                    unique=False,
                    schema='event_abstracts')
    op.create_index(op.f('ix_uq_judgements_abstract_id_track_id_user_id'),
                    'judgements',
                    ['abstract_id', 'track_id', 'user_id'],
                    unique=True,
                    schema='event_abstracts')


def downgrade():
    op.drop_index(op.f('ix_uq_judgements_abstract_id_track_id_user_id'),
                  table_name='judgements',
                  schema='event_abstracts')
    op.drop_index(op.f('ix_judgements_user_id'), table_name='judgements', schema='event_abstracts')
    op.drop_index(op.f('ix_judgements_creation_dt'), table_name='judgements', schema='event_abstracts')
    op.drop_index(op.f('ix_judgements_accepted_type_id'), table_name='judgements', schema='event_abstracts')
    op.drop_index(op.f('ix_judgements_abstract_id'), table_name='judgements', schema='event_abstracts')
    op.drop_table('judgements', schema='event_abstracts')
