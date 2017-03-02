"""Move abstract fields to SQLAlchemy

Revision ID: 4878972d7e2f
Revises: 38ed666dda98
Create Date: 2016-03-24 18:26:58.290527
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.ddl import CreateSchema, DropSchema


# revision identifiers, used by Alembic.
revision = '4878972d7e2f'
down_revision = '38ed666dda98'


def upgrade():
    op.execute(CreateSchema('event_abstracts'))

    op.create_table('abstracts',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('friendly_id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('description', sa.Text(), nullable=False),
                    sa.Column('accepted_track_id', sa.Integer(), nullable=True, index=True),
                    sa.Column('accepted_type_id', sa.Integer(), nullable=True, index=True),
                    sa.Column('type_id', sa.Integer(), nullable=True, index=True),
                    sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
                    sa.ForeignKeyConstraint(['accepted_type_id'], ['events.contribution_types.id']),
                    sa.ForeignKeyConstraint(['type_id'], ['events.contribution_types.id']),
                    sa.UniqueConstraint('friendly_id', 'event_id'),
                    sa.PrimaryKeyConstraint('id'),
                    schema='event_abstracts')

    op.create_table('abstract_field_values',
                    sa.Column('data', postgresql.JSON(), nullable=False),
                    sa.Column('abstract_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('contribution_field_id', sa.Integer(), nullable=False, index=True),
                    sa.ForeignKeyConstraint(['abstract_id'], ['event_abstracts.abstracts.id']),
                    sa.ForeignKeyConstraint(['contribution_field_id'], ['events.contribution_fields.id'],
                                            name='fk_abstract_field_values_contribution_field'),
                    sa.PrimaryKeyConstraint('abstract_id', 'contribution_field_id'),
                    schema='event_abstracts')

    op.create_foreign_key(None,
                          'contributions', 'abstracts',
                          ['abstract_id'], ['id'],
                          source_schema='events', referent_schema='event_abstracts')


def downgrade():
    op.drop_constraint('fk_contributions_abstract_id_abstracts', 'contributions', schema='events')
    op.drop_table('abstract_field_values', schema='event_abstracts')
    op.drop_table('abstracts', schema='event_abstracts')
    op.execute(DropSchema('event_abstracts'))
