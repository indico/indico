"""Update attachment links

Revision ID: 29232c09e58a
Revises: 30421387bea5
Create Date: 2016-01-06 11:18:01.623744
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '29232c09e58a'
down_revision = '30421387bea5'


def upgrade():
    print 'Updating IDs'
    op.execute("""
        UPDATE attachments.folders f SET contribution_id = (
            SELECT contribution_id
            FROM events.legacy_contribution_id_map
            WHERE event_id = f.event_id AND legacy_contribution_id = f.legacy_contribution_id
        ) WHERE link_type = 3 AND contribution_id IS NULL;

        UPDATE attachments.folders f SET subcontribution_id = (
            SELECT subcontribution_id
            FROM events.legacy_subcontribution_id_map
            WHERE event_id = f.event_id AND legacy_contribution_id = f.legacy_contribution_id AND
                  legacy_subcontribution_id = f.legacy_subcontribution_id
        ) WHERE link_type = 4 AND subcontribution_id IS NULL;

        UPDATE attachments.folders f SET session_id = (
            SELECT session_id
            FROM events.legacy_session_id_map
            WHERE event_id = f.event_id AND legacy_session_id = f.legacy_session_id
        ) WHERE link_type = 5 AND session_id IS NULL;
    """)
    # Delete orphans
    print 'Deleting orphaned attachments... (may take a few minutes)'
    op.execute("""
        CREATE TEMP TABLE orphaned_folder_ids ON COMMIT DROP AS (
            SELECT id FROM attachments.folders WHERE (
                (link_type = 3 AND contribution_id IS NULL) OR
                (link_type = 4 AND subcontribution_id IS NULL) OR
                (link_type = 5 AND session_id IS NULL)
            )
        );
        CREATE TEMP TABLE orphaned_attachment_ids ON COMMIT DROP AS (
            SELECT id FROM attachments.attachments WHERE folder_id IN (SELECT id FROM orphaned_folder_ids)
        );
        UPDATE attachments.attachments SET file_id = NULL WHERE file_id IS NOT NULL AND id IN (
            SELECT id FROM orphaned_attachment_ids
        );
        DELETE FROM attachments.files WHERE attachment_id IN (SELECT id FROM orphaned_attachment_ids);
        DELETE FROM attachments.legacy_attachment_id_map WHERE attachment_id IN (
            SELECT id FROM orphaned_attachment_ids
        );
        DELETE FROM attachments.attachment_principals WHERE attachment_id IN (SELECT id FROM orphaned_attachment_ids);
        DELETE FROM attachments.attachments WHERE id IN (SELECT id FROM orphaned_attachment_ids);
        DELETE FROM attachments.legacy_folder_id_map WHERE folder_id IN (SELECT id FROM orphaned_folder_ids);
        DELETE FROM attachments.folder_principals WHERE folder_id IN (SELECT id FROM orphaned_folder_ids);
        DELETE FROM attachments.folders WHERE id IN (SELECT id FROM orphaned_folder_ids);
    """)
    print 'Creating CHECKs'
    op.create_check_constraint('valid_session_link', 'folders',
                               'link_type != 5 OR (category_id IS NULL AND contribution_id IS NULL AND '
                               'linked_event_id IS NULL AND subcontribution_id IS NULL AND session_id IS NOT NULL)',
                               schema='attachments')
    op.create_check_constraint('valid_contribution_link', 'folders',
                               'link_type != 3 OR (category_id IS NULL AND linked_event_id IS NULL AND '
                               'session_id IS NULL AND subcontribution_id IS NULL AND contribution_id IS NOT NULL)',
                               schema='attachments')
    op.create_check_constraint('valid_subcontribution_link', 'folders',
                               'link_type != 4 OR (category_id IS NULL AND contribution_id IS NULL AND '
                               'linked_event_id IS NULL AND session_id IS NULL AND subcontribution_id IS NOT NULL)',
                               schema='attachments')
    op.drop_column('folders', 'legacy_session_id', schema='attachments')
    op.drop_column('folders', 'legacy_contribution_id', schema='attachments')
    op.drop_column('folders', 'legacy_subcontribution_id', schema='attachments')


def downgrade():
    op.add_column('folders', sa.Column('legacy_session_id', sa.String(), nullable=True), schema='attachments')
    op.add_column('folders', sa.Column('legacy_contribution_id', sa.String(), nullable=True), schema='attachments')
    op.add_column('folders', sa.Column('legacy_subcontribution_id', sa.String(), nullable=True), schema='attachments')
    op.drop_constraint('ck_folders_valid_session_link', 'folders', schema='attachments')
    op.drop_constraint('ck_folders_valid_contribution_link', 'folders', schema='attachments')
    op.drop_constraint('ck_folders_valid_subcontribution_link', 'folders', schema='attachments')
