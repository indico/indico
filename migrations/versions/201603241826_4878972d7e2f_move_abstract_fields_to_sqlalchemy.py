"""Move abstract fields to SQLAlchemy

Revision ID: 4878972d7e2f
Revises: 3d672dc5ee53
Create Date: 2016-03-24 18:26:58.290527
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '4878972d7e2f'
down_revision = '38ed666dda98'


def upgrade():
    # Create new tables in 'event_abstracts' schema
    op.create_table('abstracts',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('legacy_id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False),
                    sa.Column('description', sa.Text(), nullable=False),
                    sa.Column('accepted_track_id', sa.Integer(), nullable=True),
                    sa.Column('accepted_type_id', sa.Integer(), nullable=True),
                    sa.Column('type_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['event_id'],
                                            [u'events.events.id'],
                                            name=op.f('fk_abstracts_event_id_events')),
                    sa.PrimaryKeyConstraint('id', name=op.f('pk_abstracts')),
                    schema='event_abstracts')
    op.create_table('abstract_field_values',
                    sa.Column('data', postgresql.JSON(), nullable=False),
                    sa.Column('abstract_id', sa.Integer(), nullable=False),
                    sa.Column('contribution_field_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['abstract_id'],
                                            [u'events.abstracts.id'],
                                            name=op.f('fk_abstract_field_values_abstract_id_abstracts')),
                    sa.ForeignKeyConstraint(
                        ['contribution_field_id'],
                        [u'events.contribution_fields.id'],
                        name=op.f('fk_abstract_field_values_contribution_field_id_contribution_fields')),
                    sa.PrimaryKeyConstraint('abstract_id', 'contribution_field_id',
                                            name=op.f('pk_abstract_field_values')),
                    schema='event_abstracts')


    # add missing columns in 'events' schema
    op.add_column('contribution_fields',
                  sa.Column('legacy_id', sa.VARCHAR(), autoincrement=False, nullable=True),
                  schema='events')
    op.create_foreign_key(None,
                          'contributions', 'abstracts',
                          ['abstract_id'], ['id'],
                          source_schema='events', referent_schema='event_abstracts')


    # indices for 'event_abstracts' schema
    op.create_index(op.f('ix_abstracts_accepted_type_id'),
                    'abstracts', ['accepted_type_id'],
                    unique=False,
                    schema='event_abstracts')
    op.create_index(op.f('ix_abstracts_type_id'),
                    'abstracts', ['type_id'],
                    unique=False,
                    schema='event_abstracts')
    op.create_index(op.f('ix_abstract_field_values_abstract_id'),
                    'abstract_field_values',
                    ['abstract_id'],
                    unique=False,
                    schema='event_abstracts')
    op.create_index(op.f('ix_abstract_field_values_contribution_field_id'),
                    'abstract_field_values',
                    ['contribution_field_id'],
                    unique=False,
                    schema='event_abstracts')
    op.create_index(op.f('ix_abstracts_event_id'),
                    'abstracts', ['event_id'],
                    unique=False,
                    schema='event_abstracts')
    op.create_index(op.f('ix_uq_abstracts_legacy_id_event_id'),
                    'abstracts',
                    ['legacy_id', 'event_id'],
                    unique=True,
                    schema='event_abstracts')

    # indices for 'events' schema
    op.create_index('ix_uq_abstract_id',
                    'contributions',
                    ['abstract_id'],
                    postgresql_where=sa.text('NOT is_deleted'),
                    unique=True,
                    schema='events')
    op.create_index(op.f('ix_contributions_abstract_id'),
                    'contributions',
                    ['abstract_id'],
                    unique=False,
                    schema='events')


def downgrade():
    op.drop_index(op.f('ix_contributions_abstract_id'), table_name='contributions', schema='events')
    op.drop_index('ix_uq_abstract_id', table_name='contributions', schema='events')

    op.drop_index(op.f('ix_uq_abstracts_legacy_id_event_id'), table_name='abstracts', schema='event_abstracts')
    op.drop_index(op.f('ix_abstracts_event_id'), table_name='abstracts', schema='event_abstracts')
    op.drop_index(op.f('ix_abstract_field_values_contribution_field_id'),
                  table_name='abstract_field_values',
                  schema='event_abstracts')
    op.drop_index(op.f('ix_abstract_field_values_abstract_id'),
                  table_name='abstract_field_values',
                  schema='event_abstracts')
    op.drop_index(op.f('ix_abstracts_type_id'), table_name='abstracts', schema='event_abstracts')
    op.drop_index(op.f('ix_abstracts_accepted_type_id'), table_name='abstracts', schema='event_abstracts')

    op.drop_column('contribution_fields', 'legacy_id', schema='events')

    op.drop_table('abstract_field_values', schema='event_abstracts')
    op.drop_table('abstracts', schema='event_abstracts')
