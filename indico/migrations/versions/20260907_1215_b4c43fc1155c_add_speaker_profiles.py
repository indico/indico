"""Add speaker profiles

Revision ID: b4c43fc1155c
Revises: c412156094d6
Create Date: 2026-09-07 12:15:33.168978
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b4c43fc1155c'
down_revision = '06a037da1ec6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('speaker_links',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('icon', sa.String(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['event_id'], ['events.events.id'], name=op.f('fk_speaker_links_event_id_events')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_speaker_links')),
    schema='events'
    )
    op.create_index(op.f('ix_speaker_links_event_id'), 'speaker_links', ['event_id'], unique=False, schema='events')
    op.create_index('ix_uq_link_name_lower', 'speaker_links', ['event_id', sa.text('lower(name)')], unique=True, schema='events')
    op.create_table('speaker_link_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('speaker_link_id', sa.Integer(), nullable=False),
    sa.Column('event_person_id', sa.Integer(), nullable=False),
    sa.Column('data', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['event_person_id'], ['events.persons.id'], name=op.f('fk_speaker_link_data_event_person_id_persons')),
    sa.ForeignKeyConstraint(['speaker_link_id'], ['events.speaker_links.id'], name=op.f('fk_speaker_link_data_speaker_link_id_speaker_links')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_speaker_link_data')),
    sa.UniqueConstraint('speaker_link_id', 'event_person_id', name=op.f('uq_speaker_link_data_speaker_link_id_event_person_id')),
    schema='events'
    )
    op.create_index(op.f('ix_speaker_link_data_event_person_id'), 'speaker_link_data', ['event_person_id'], unique=False, schema='events')
    op.create_index(op.f('ix_speaker_link_data_speaker_link_id'), 'speaker_link_data', ['speaker_link_id'], unique=False, schema='events')
    op.add_column('persons', sa.Column('speaker_photo_file_id', sa.Integer(), nullable=True), schema='events')
    op.add_column('persons', sa.Column('speaker_description', sa.Text(), nullable=True), schema='events')
    op.create_foreign_key(op.f('fk_persons_speaker_photo_file_id_files'), 'persons', 'files', ['speaker_photo_file_id'], ['id'], source_schema='events', referent_schema='indico')


def downgrade():
    op.drop_constraint(op.f('fk_persons_speaker_photo_file_id_files'), 'persons', schema='events', type_='foreignkey')
    op.drop_column('persons', 'speaker_description', schema='events')
    op.drop_column('persons', 'speaker_photo_file_id', schema='events')
    op.drop_index(op.f('ix_speaker_link_data_speaker_link_id'), table_name='speaker_link_data', schema='events')
    op.drop_index(op.f('ix_speaker_link_data_event_person_id'), table_name='speaker_link_data', schema='events')
    op.drop_table('speaker_link_data', schema='events')
    op.drop_index(op.f('ix_speaker_links_event_id'), table_name='speaker_links', schema='events')
    op.drop_index('ix_uq_link_name_lower', table_name='speaker_links', schema='events')
    op.drop_table('speaker_links', schema='events')
