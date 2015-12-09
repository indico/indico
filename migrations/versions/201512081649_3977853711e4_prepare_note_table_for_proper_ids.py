"""Prepare note table for proper IDs

Revision ID: 3977853711e4
Revises: 33a1d6f25951
Create Date: 2015-12-08 16:49:21.108104
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '3977853711e4'
down_revision = '33a1d6f25951'


def upgrade():
    op.alter_column('notes', 'session_id', new_column_name='legacy_session_id', schema='events')
    op.alter_column('notes', 'contribution_id', new_column_name='legacy_contribution_id', schema='events')
    op.alter_column('notes', 'subcontribution_id', new_column_name='legacy_subcontribution_id', schema='events')
    op.drop_constraint('ck_notes_valid_event_link', 'notes', schema='events')
    op.drop_constraint('ck_notes_valid_session_link', 'notes', schema='events')
    op.drop_constraint('ck_notes_valid_contribution_link', 'notes', schema='events')
    op.drop_constraint('ck_notes_valid_subcontribution_link', 'notes', schema='events')
    op.drop_column('notes', 'category_id', schema='events')
    op.drop_index('ix_uq_notes_event_id', 'events', schema='events')
    op.drop_index('ix_uq_notes_event_id_session_id', 'events', schema='events')
    op.drop_index('ix_uq_notes_event_id_contribution_id', 'events', schema='events')
    op.drop_index('ix_uq_notes_event_id_contribution_id_subcontribution_id', 'events', schema='events')
    op.add_column('notes', sa.Column('linked_event_id', sa.Integer(), nullable=True), schema='events')
    op.add_column('notes', sa.Column('session_id', sa.Integer(), nullable=True), schema='events')
    op.add_column('notes', sa.Column('contribution_id', sa.Integer(), nullable=True), schema='events')
    op.add_column('notes', sa.Column('subcontribution_id', sa.Integer(), nullable=True), schema='events')
    op.create_foreign_key(None,
                          'notes', 'events',
                          ['linked_event_id'], ['id'],
                          source_schema='events', referent_schema='events')
    op.create_foreign_key(None,
                          'notes', 'sessions',
                          ['session_id'], ['id'],
                          source_schema='events', referent_schema='events')
    op.create_foreign_key(None,
                          'notes', 'contributions',
                          ['contribution_id'], ['id'],
                          source_schema='events', referent_schema='events')
    op.create_foreign_key(None,
                          'notes', 'subcontributions',
                          ['subcontribution_id'], ['id'],
                          source_schema='events', referent_schema='events')
    op.create_index(None, 'notes', ['linked_event_id'], schema='events')
    op.create_index(None, 'notes', ['session_id'], schema='events')
    op.create_index(None, 'notes', ['contribution_id'], schema='events')
    op.create_index(None, 'notes', ['subcontribution_id'], schema='events')
    op.create_index(None, 'notes', ['linked_event_id'], unique=True, schema='events',
                    postgresql_where=sa.text('link_type = 2'))
    op.create_index(None, 'notes', ['session_id'], unique=True, schema='events',
                    postgresql_where=sa.text('link_type = 5'))
    op.create_index(None, 'notes', ['contribution_id'], unique=True, schema='events',
                    postgresql_where=sa.text('link_type = 3'))
    op.create_index(None, 'notes', ['subcontribution_id'], unique=True, schema='events',
                    postgresql_where=sa.text('link_type = 4'))
    op.create_check_constraint('valid_event_id', 'notes', '(event_id IS NULL) = (link_type = 1)', schema='events')
    op.execute("""UPDATE events.notes SET linked_event_id = event_id WHERE link_type = 2""")
    op.create_check_constraint('valid_event_link', 'notes',
                               'link_type != 2 OR (contribution_id IS NULL AND session_id IS NULL AND '
                               'subcontribution_id IS NULL AND linked_event_id IS NOT NULL)',
                               schema='events')


def downgrade():
    op.drop_constraint('ck_notes_valid_event_id', 'notes', schema='events')
    op.drop_constraint('ck_notes_valid_event_link', 'notes', schema='events')
    op.drop_column('notes', 'linked_event_id', schema='events')
    op.drop_column('notes', 'session_id', schema='events')
    op.drop_column('notes', 'contribution_id', schema='events')
    op.drop_column('notes', 'subcontribution_id', schema='events')
    op.alter_column('notes', 'legacy_session_id', new_column_name='session_id', schema='events')
    op.alter_column('notes', 'legacy_contribution_id', new_column_name='contribution_id', schema='events')
    op.alter_column('notes', 'legacy_subcontribution_id', new_column_name='subcontribution_id', schema='events')
    op.add_column('notes', sa.Column('category_id', sa.Integer(), nullable=True), schema='events')
    op.create_check_constraint('valid_event_link', 'notes',
                               'link_type != 2 OR (contribution_id IS NULL AND subcontribution_id IS NULL AND '
                               'category_id IS NULL AND session_id IS NULL AND event_id IS NOT NULL)',
                               schema='events')
    op.create_check_constraint('valid_session_link', 'notes',
                               'link_type != 5 OR (contribution_id IS NULL AND subcontribution_id IS NULL AND '
                               'category_id IS NULL AND event_id IS NOT NULL AND session_id IS NOT NULL)',
                               schema='events')
    op.create_check_constraint('valid_contribution_link', 'notes',
                               'link_type != 3 OR (subcontribution_id IS NULL AND category_id IS NULL AND '
                               'session_id IS NULL AND event_id IS NOT NULL AND contribution_id IS NOT NULL)',
                               schema='events')
    op.create_check_constraint('valid_subcontribution_link', 'notes',
                               'link_type != 4 OR (category_id IS NULL AND session_id IS NULL AND event_id IS NOT NULL '
                               'AND contribution_id IS NOT NULL AND subcontribution_id IS NOT NULL)',
                               schema='events')
    op.create_index(None, 'notes', ['category_id'], schema='events')
    op.create_index(None, 'notes', ['event_id'], unique=True, schema='events',
                    postgresql_where=sa.text('link_type = 2'))
    op.create_index(None, 'notes', ['event_id', 'session_id'], unique=True, schema='events',
                    postgresql_where=sa.text('link_type = 5'))
    op.create_index(None, 'notes', ['event_id', 'contribution_id'], unique=True, schema='events',
                    postgresql_where=sa.text('link_type = 3'))
    op.create_index(None, 'notes', ['event_id', 'contribution_id', 'subcontribution_id'], unique=True, schema='events',
                    postgresql_where=sa.text('link_type = 4'))
