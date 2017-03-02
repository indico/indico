"""Prepare attachment tables for proper IDs

Revision ID: 421ef2bc48ae
Revises: 3977853711e4
Create Date: 2016-01-05 16:42:27.139437
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '421ef2bc48ae'
down_revision = '3977853711e4'


LEGACY_TABLES = ('legacy_folder_id_map', 'legacy_attachment_id_map')


def upgrade():
    # folders table
    op.alter_column('folders', 'session_id', new_column_name='legacy_session_id', schema='attachments')
    op.alter_column('folders', 'contribution_id', new_column_name='legacy_contribution_id', schema='attachments')
    op.alter_column('folders', 'subcontribution_id', new_column_name='legacy_subcontribution_id', schema='attachments')
    op.drop_constraint('ck_folders_valid_category_link', 'folders', schema='attachments')
    op.drop_constraint('ck_folders_valid_event_link', 'folders', schema='attachments')
    op.drop_constraint('ck_folders_valid_session_link', 'folders', schema='attachments')
    op.drop_constraint('ck_folders_valid_contribution_link', 'folders', schema='attachments')
    op.drop_constraint('ck_folders_valid_subcontribution_link', 'folders', schema='attachments')
    op.drop_index('ix_uq_folders_event_id', 'events', schema='attachments')
    op.drop_index('ix_uq_folders_event_id_session_id', 'events', schema='attachments')
    op.drop_index('ix_uq_folders_event_id_contribution_id', 'events', schema='attachments')
    op.drop_index('ix_uq_folders_event_id_contribution_id_subcontribution_id', 'events', schema='attachments')
    op.add_column('folders', sa.Column('linked_event_id', sa.Integer(), nullable=True), schema='attachments')
    op.add_column('folders', sa.Column('session_id', sa.Integer(), nullable=True), schema='attachments')
    op.add_column('folders', sa.Column('contribution_id', sa.Integer(), nullable=True), schema='attachments')
    op.add_column('folders', sa.Column('subcontribution_id', sa.Integer(), nullable=True), schema='attachments')
    op.create_foreign_key(None,
                          'folders', 'events',
                          ['linked_event_id'], ['id'],
                          source_schema='attachments', referent_schema='events')
    op.create_foreign_key(None,
                          'folders', 'sessions',
                          ['session_id'], ['id'],
                          source_schema='attachments', referent_schema='events')
    op.create_foreign_key(None,
                          'folders', 'contributions',
                          ['contribution_id'], ['id'],
                          source_schema='attachments', referent_schema='events')
    op.create_foreign_key(None,
                          'folders', 'subcontributions',
                          ['subcontribution_id'], ['id'],
                          source_schema='attachments', referent_schema='events')
    op.create_index(None, 'folders', ['linked_event_id'], schema='attachments')
    op.create_index(None, 'folders', ['session_id'], schema='attachments')
    op.create_index(None, 'folders', ['contribution_id'], schema='attachments')
    op.create_index(None, 'folders', ['subcontribution_id'], schema='attachments')
    op.create_index(None, 'folders', ['linked_event_id'], unique=True, schema='attachments',
                    postgresql_where=sa.text('link_type = 2 AND is_default'))
    op.create_index(None, 'folders', ['session_id'], unique=True, schema='attachments',
                    postgresql_where=sa.text('link_type = 5 AND is_default'))
    op.create_index(None, 'folders', ['contribution_id'], unique=True, schema='attachments',
                    postgresql_where=sa.text('link_type = 3 AND is_default'))
    op.create_index(None, 'folders', ['subcontribution_id'], unique=True, schema='attachments',
                    postgresql_where=sa.text('link_type = 4 AND is_default'))
    op.create_check_constraint('valid_event_id', 'folders', '(event_id IS NULL) = (link_type = 1)',
                               schema='attachments')
    op.execute("""UPDATE attachments.folders SET linked_event_id = event_id WHERE link_type = 2""")
    op.create_check_constraint('valid_category_link', 'folders',
                               'link_type != 1 OR (contribution_id IS NULL AND linked_event_id IS NULL AND '
                               'session_id IS NULL AND subcontribution_id IS NULL AND category_id IS NOT NULL)',
                               schema='attachments')
    op.create_check_constraint('valid_event_link', 'folders',
                               'link_type != 2 OR (category_id IS NULL AND contribution_id IS NULL AND '
                               'session_id IS NULL AND subcontribution_id IS NULL AND linked_event_id IS NOT NULL)',
                               schema='attachments')
    # legacy tables
    for table in LEGACY_TABLES:
        op.drop_constraint('ck_{}_valid_event_link'.format(table), table, schema='attachments')
        op.drop_constraint('ck_{}_valid_session_link'.format(table), table, schema='attachments')
        op.drop_constraint('ck_{}_valid_contribution_link'.format(table), table, schema='attachments')
        op.drop_constraint('ck_{}_valid_subcontribution_link'.format(table), table, schema='attachments')
        op.drop_column(table, 'link_type', schema='attachments')
        op.drop_column(table, 'category_id', schema='attachments')
        op.alter_column(table, 'event_id', nullable=False, schema='attachments')


def downgrade():
    # folders table
    op.drop_constraint('ck_folders_valid_event_id', 'folders', schema='attachments')
    op.drop_constraint('ck_folders_valid_category_link', 'folders', schema='attachments')
    op.drop_constraint('ck_folders_valid_event_link', 'folders', schema='attachments')
    op.drop_column('folders', 'linked_event_id', schema='attachments')
    op.drop_column('folders', 'session_id', schema='attachments')
    op.drop_column('folders', 'contribution_id', schema='attachments')
    op.drop_column('folders', 'subcontribution_id', schema='attachments')
    op.alter_column('folders', 'legacy_session_id', new_column_name='session_id', schema='attachments')
    op.alter_column('folders', 'legacy_contribution_id', new_column_name='contribution_id', schema='attachments')
    op.alter_column('folders', 'legacy_subcontribution_id', new_column_name='subcontribution_id', schema='attachments')
    op.create_check_constraint('valid_category_link', 'folders',
                               'link_type != 1 OR (event_id IS NULL AND contribution_id IS NULL AND '
                               'subcontribution_id IS NULL AND session_id IS NULL AND category_id IS NOT NULL)',
                               schema='attachments')
    op.create_check_constraint('valid_event_link', 'folders',
                               'link_type != 2 OR (contribution_id IS NULL AND subcontribution_id IS NULL AND '
                               'category_id IS NULL AND session_id IS NULL AND event_id IS NOT NULL)',
                               schema='attachments')
    op.create_check_constraint('valid_session_link', 'folders',
                               'link_type != 5 OR (contribution_id IS NULL AND subcontribution_id IS NULL AND '
                               'category_id IS NULL AND event_id IS NOT NULL AND session_id IS NOT NULL)',
                               schema='attachments')
    op.create_check_constraint('valid_contribution_link', 'folders',
                               'link_type != 3 OR (subcontribution_id IS NULL AND category_id IS NULL AND '
                               'session_id IS NULL AND event_id IS NOT NULL AND contribution_id IS NOT NULL)',
                               schema='attachments')
    op.create_check_constraint('valid_subcontribution_link', 'folders',
                               'link_type != 4 OR (category_id IS NULL AND session_id IS NULL AND event_id IS NOT NULL '
                               'AND contribution_id IS NOT NULL AND subcontribution_id IS NOT NULL)',
                               schema='attachments')
    op.create_index(None, 'folders', ['event_id'], unique=True, schema='attachments',
                    postgresql_where=sa.text('link_type = 2 AND is_default'))
    op.create_index(None, 'folders', ['event_id', 'session_id'], unique=True, schema='attachments',
                    postgresql_where=sa.text('link_type = 5 AND is_default'))
    op.create_index(None, 'folders', ['event_id', 'contribution_id'], unique=True, schema='attachments',
                    postgresql_where=sa.text('link_type = 3 AND is_default'))
    op.create_index(None, 'folders', ['event_id', 'contribution_id', 'subcontribution_id'], unique=True,
                    schema='attachments', postgresql_where=sa.text('link_type = 4 AND is_default'))
    # legacy tables
    for table in LEGACY_TABLES:
        op.alter_column(table, 'event_id', nullable=True, schema='attachments')
        op.add_column(table, sa.Column('link_type', sa.Integer(), nullable=True), schema='attachments')
        op.add_column(table, sa.Column('category_id', sa.Integer(), nullable=True), schema='attachments')
        op.execute("""
            UPDATE attachments.{} SET link_type = CASE
                WHEN subcontribution_id IS NOT NULL THEN 4
                WHEN contribution_id IS NOT NULL THEN 3
                WHEN session_id IS NOT NULL THEN 5
                ELSE 2
            END
        """.format(table))
        op.alter_column(table, 'link_type', nullable=False, schema='attachments')
        op.create_index(None, table, ['category_id'], schema='attachments')
        op.create_check_constraint('valid_event_link', table,
                                   'link_type != 2 OR (contribution_id IS NULL AND subcontribution_id IS NULL AND '
                                   'category_id IS NULL AND session_id IS NULL AND event_id IS NOT NULL)',
                                   schema='attachments')
        op.create_check_constraint('valid_session_link', table,
                                   'link_type != 5 OR (contribution_id IS NULL AND subcontribution_id IS NULL AND '
                                   'category_id IS NULL AND event_id IS NOT NULL AND session_id IS NOT NULL)',
                                   schema='attachments')
        op.create_check_constraint('valid_contribution_link', table,
                                   'link_type != 3 OR (subcontribution_id IS NULL AND category_id IS NULL AND '
                                   'session_id IS NULL AND event_id IS NOT NULL AND contribution_id IS NOT NULL)',
                                   schema='attachments')
        op.create_check_constraint('valid_subcontribution_link', table,
                                   'link_type != 4 OR (category_id IS NULL AND session_id IS NULL AND '
                                   'event_id IS NOT NULL AND contribution_id IS NOT NULL AND '
                                   'subcontribution_id IS NOT NULL)',
                                   schema='attachments')
