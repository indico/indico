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

    # Create new tables in 'event_abstracts' schema
    op.create_table('abstracts',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('legacy_id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('description', sa.Text(), nullable=False),
                    sa.Column('accepted_track_id', sa.Integer(), nullable=True, index=True),
                    sa.Column('accepted_type_id', sa.Integer(), nullable=True, index=True),
                    sa.Column('type_id', sa.Integer(), nullable=True),
                    sa.Index(None, 'legacy_id', 'event_id'),
                    sa.ForeignKeyConstraint(['event_id'], [u'events.events.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='event_abstracts')
    op.create_table('abstract_field_values',
                    sa.Column('data', postgresql.JSON(), nullable=False),
                    sa.Column('abstract_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('contribution_field_id', sa.Integer(), nullable=False, index=True),
                    sa.ForeignKeyConstraint(['abstract_id'], [u'event_abstracts.abstracts.id']),
                    sa.ForeignKeyConstraint(['contribution_field_id'], [u'events.contribution_fields.id']),
                    sa.PrimaryKeyConstraint('abstract_id', 'contribution_field_id'),
                    schema='event_abstracts')

    # add missing columns in 'events' schema
    op.add_column('contribution_fields', sa.Column('legacy_id', sa.VARCHAR(), autoincrement=False, nullable=True),
                  schema='events')
    op.create_foreign_key(None,
                          'contributions', 'abstracts',
                          ['abstract_id'], ['id'],
                          source_schema='events', referent_schema='event_abstracts')

    # indices for 'events' schema
    op.create_index(None, 'contributions', ['abstract_id'], postgresql_where=sa.text('NOT is_deleted'), unique=True,
                    schema='events')
    op.create_index(None, 'contributions', ['abstract_id'], unique=False, schema='events')


def downgrade():
    op.drop_index(op.f('ix_contributions_abstract_id'), table_name='contributions', schema='events')
    op.drop_index('ix_uq_abstract_id', table_name='contributions', schema='events')

    op.drop_constraint('fk_contributions_abstract_id_abstracts', 'contributions', schema='events')

    op.drop_column('contribution_fields', 'legacy_id', schema='events')

    op.drop_table('abstract_field_values', schema='event_abstracts')
    op.drop_table('abstracts', schema='event_abstracts')

    op.execute(DropSchema('event_abstracts'))
