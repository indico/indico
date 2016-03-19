"""Use proper FK for LinkMixin event_id

Revision ID: 13480f6da0e2
Revises: 1296030d8d14
Create Date: 2015-09-24 13:52:43.803571
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '13480f6da0e2'
down_revision = '1296030d8d14'


def _delete_orphaned():
    print 'Deleting orphaned notes...'
    op.execute("""
        CREATE TEMP TABLE orphaned_note_ids ON COMMIT DROP AS
            (SELECT id FROM events.notes x WHERE x.event_id IS NOT NULL and NOT EXISTS
                (SELECT 1 FROM events.events WHERE id = x.event_id));
    """)
    op.execute("""
        UPDATE events.notes SET current_revision_id = NULL WHERE id IN (SELECT id FROM orphaned_note_ids);
        DELETE FROM events.note_revisions WHERE note_id IN (SELECT id FROM orphaned_note_ids);
        DELETE FROM events.notes WHERE id IN (SELECT id FROM orphaned_note_ids);
    """)
    print 'Deleting orphaned attachments...'
    op.execute("""
        CREATE TEMP TABLE orphaned_folder_ids ON COMMIT DROP AS
            (SELECT id FROM attachments.folders x WHERE x.event_id IS NOT NULL and NOT EXISTS
                (SELECT 1 FROM events.events WHERE id = x.event_id));
        CREATE TEMP TABLE orphaned_attachment_ids ON COMMIT DROP AS
            (SELECT id FROM attachments.attachments WHERE folder_id IN (SELECT id FROM orphaned_folder_ids));
    """)
    op.execute("""
        UPDATE attachments.attachments SET file_id = NULL WHERE file_id IS NOT NULL AND id IN
            (SELECT id FROM orphaned_attachment_ids);
        DELETE FROM attachments.files WHERE attachment_id IN (SELECT id FROM orphaned_attachment_ids);
        DELETE FROM attachments.legacy_attachment_id_map WHERE attachment_id IN
            (SELECT id FROM orphaned_attachment_ids);
        DELETE FROM attachments.attachment_principals WHERE attachment_id IN (SELECT id FROM orphaned_attachment_ids);
        DELETE FROM attachments.attachments WHERE id IN (SELECT id FROM orphaned_attachment_ids);
        DELETE FROM attachments.legacy_folder_id_map WHERE folder_id IN (SELECT id FROM orphaned_folder_ids);
        DELETE FROM attachments.folder_principals WHERE folder_id IN (SELECT id FROM orphaned_folder_ids);
        DELETE FROM attachments.folders WHERE id IN (SELECT id FROM orphaned_folder_ids);
    """)


def upgrade():
    _delete_orphaned()
    op.create_foreign_key(None,
                          'notes', 'events',
                          ['event_id'], ['id'],
                          source_schema='events', referent_schema='events')
    op.create_foreign_key(None,
                          'folders', 'events',
                          ['event_id'], ['id'],
                          source_schema='attachments', referent_schema='events')
    op.create_foreign_key(None,
                          'legacy_attachment_id_map', 'events',
                          ['event_id'], ['id'],
                          source_schema='attachments', referent_schema='events')
    op.create_foreign_key(None,
                          'legacy_folder_id_map', 'events',
                          ['event_id'], ['id'],
                          source_schema='attachments', referent_schema='events')


def downgrade():
    op.drop_constraint(op.f('fk_legacy_folder_id_map_event_id_events'), 'legacy_folder_id_map',
                       schema='attachments')
    op.drop_constraint(op.f('fk_legacy_attachment_id_map_event_id_events'), 'legacy_attachment_id_map',
                       schema='attachments')
    op.drop_constraint(op.f('fk_folders_event_id_events'), 'folders', schema='attachments')
    op.drop_constraint(op.f('fk_notes_event_id_events'), 'notes', schema='events')
