"""Update category attachment links

Revision ID: ff7e1027bd4
Revises: 58de7b79b532
Create Date: 2016-06-06 10:04:36.954487
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'ff7e1027bd4'
down_revision = '58de7b79b532'


def upgrade():
    print 'Deleting orphaned attachments...'
    op.execute("""
        CREATE TEMP TABLE orphaned_folder_ids ON COMMIT DROP AS (
            SELECT id FROM attachments.folders fo WHERE fo.link_type = 1 AND NOT EXISTS (
                SELECT 1 FROM categories.categories WHERE id     = fo.category_id
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
    op.create_foreign_key(None,
                          'folders', 'categories',
                          ['category_id'], ['id'],
                          source_schema='attachments', referent_schema='categories')


def downgrade():
    op.drop_constraint('fk_folders_category_id_categories', 'folders', schema='attachments')
