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
down_revision = '3d672dc5ee53'


def upgrade():
    op.create_table('abstracts',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('legacy_id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False),
                    sa.Column('description', sa.Text(), nullable=False),
                    sa.ForeignKeyConstraint(['event_id'],
                                            [u'events.events.id'],
                                            name=op.f('fk_abstracts_event_id_events')),
                    sa.PrimaryKeyConstraint('id', name=op.f('pk_abstracts')),
                    schema='events')
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
                    schema='events')
    op.create_index(op.f('ix_abstract_field_values_abstract_id'),
                    'abstract_field_values',
                    ['abstract_id'],
                    unique=False,
                    schema='events')
    op.create_index(op.f('ix_abstract_field_values_contribution_field_id'),
                    'abstract_field_values',
                    ['contribution_field_id'],
                    unique=False,
                    schema='events')
    op.create_index(op.f('ix_abstracts_event_id'),
                    'abstracts', ['event_id'],
                    unique=False,
                    schema='events')
    op.create_index(op.f('ix_uq_abstracts_legacy_id_event_id'),
                    'abstracts',
                    ['legacy_id', 'event_id'],
                    unique=True,
                    schema='events')


def downgrade():
    op.drop_index(op.f('ix_uq_abstracts_legacy_id_event_id'), table_name='abstracts', schema='events')
    op.drop_index(op.f('ix_abstracts_event_id'), table_name='abstracts', schema='events')
    op.drop_index(op.f('ix_abstract_field_values_contribution_field_id'),
                  table_name='abstract_field_values',
                  schema='events')
    op.drop_index(op.f('ix_abstract_field_values_abstract_id'), table_name='abstract_field_values', schema='events')
    op.drop_table('abstract_field_values', schema='events')
    op.drop_table('abstracts', schema='events')
