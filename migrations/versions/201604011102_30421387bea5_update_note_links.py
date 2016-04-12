"""Update note links

Revision ID: 30421387bea5
Revises: 338772789e1f
Create Date: 2016-01-04 10:00:35.572008
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '30421387bea5'
down_revision = '338772789e1f'


def upgrade():
    op.execute("""
        UPDATE events.notes n SET contribution_id = (
            SELECT contribution_id
            FROM events.legacy_contribution_id_map
            WHERE event_id = n.event_id AND legacy_contribution_id = n.legacy_contribution_id
        ) WHERE link_type = 3 AND contribution_id IS NULL;

        UPDATE events.notes n SET subcontribution_id = (
            SELECT subcontribution_id
            FROM events.legacy_subcontribution_id_map
            WHERE event_id = n.event_id AND legacy_contribution_id = n.legacy_contribution_id AND
                  legacy_subcontribution_id = n.legacy_subcontribution_id
        ) WHERE link_type = 4 AND subcontribution_id IS NULL;

        UPDATE events.notes n SET session_id = (
            SELECT session_id
            FROM events.legacy_session_id_map
            WHERE event_id = n.event_id AND legacy_session_id = n.legacy_session_id
        ) WHERE link_type = 5 AND session_id IS NULL;
    """)
    op.execute("""
        CREATE TEMP TABLE orphaned_note_ids ON COMMIT DROP AS (
            SELECT n.id
            FROM events.notes n
            JOIN events.events e ON (e.id = n.event_id)
            WHERE (
                n.is_deleted AND (
                    (n.link_type = 3 AND contribution_id IS NULL) OR
                    (n.link_type = 4 AND subcontribution_id IS NULL) OR
                    (n.link_type = 5 AND session_id IS NULL)
                ) OR e.is_deleted
            )
        );
        UPDATE events.notes SET current_revision_id = NULL WHERE id IN (SELECT id FROM orphaned_note_ids);
        DELETE FROM events.note_revisions WHERE note_id IN (SELECT id FROM orphaned_note_ids);
        DELETE FROM events.notes WHERE id IN (SELECT id FROM orphaned_note_ids);
    """)
    op.create_check_constraint('valid_session_link', 'notes',
                               'link_type != 5 OR (contribution_id IS NULL AND linked_event_id IS NULL AND '
                               'subcontribution_id IS NULL AND session_id IS NOT NULL)',
                               schema='events')
    op.create_check_constraint('valid_contribution_link', 'notes',
                               'link_type != 3 OR (linked_event_id IS NULL AND session_id IS NULL AND '
                               'subcontribution_id IS NULL AND contribution_id IS NOT NULL)',
                               schema='events')
    op.create_check_constraint('valid_subcontribution_link', 'notes',
                               'link_type != 4 OR (contribution_id IS NULL AND linked_event_id IS NULL AND '
                               'session_id IS NULL AND subcontribution_id IS NOT NULL)',
                               schema='events')
    op.drop_column('notes', 'legacy_session_id', schema='events')
    op.drop_column('notes', 'legacy_contribution_id', schema='events')
    op.drop_column('notes', 'legacy_subcontribution_id', schema='events')


def downgrade():
    op.add_column('notes', sa.Column('legacy_session_id', sa.String(), nullable=True), schema='events')
    op.add_column('notes', sa.Column('legacy_contribution_id', sa.String(), nullable=True), schema='events')
    op.add_column('notes', sa.Column('legacy_subcontribution_id', sa.String(), nullable=True), schema='events')
    op.drop_constraint('ck_notes_valid_session_link', 'notes', schema='events')
    op.drop_constraint('ck_notes_valid_contribution_link', 'notes', schema='events')
    op.drop_constraint('ck_notes_valid_subcontribution_link', 'notes', schema='events')
