"""Refactor editing revisions

Revision ID: 0af8f63aa603
Revises: aba7935f9226
Create Date: 2023-07-24 09:44:11.504348
"""

from enum import Enum

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum


# revision identifiers, used by Alembic.
revision = '0af8f63aa603'
down_revision = 'aba7935f9226'
branch_labels = None
depends_on = None


class _RevisionType(int, Enum):
    new = 1
    ready_for_review = 2
    needs_submitter_confirmation = 3
    changes_acceptance = 4
    needs_submitter_changes = 5
    acceptance = 6
    rejection = 7
    undo = 8
    reset = 9


class _FinalRevisionState(int, Enum):
    none = 0
    replaced = 1
    needs_submitter_confirmation = 2
    needs_submitter_changes = 3
    accepted = 4
    rejected = 5
    undone = 6


def _create_new_revisions(conn):
    query = '''
        SELECT id, editable_id, submitter_id, editor_id, reviewed_dt, final_state, comment
        FROM event_editing.revisions AS a
        WHERE a.final_state IN (3, 4, 5, 6) AND
              NOT EXISTS (SELECT 1
                          FROM event_editing.revisions AS b
                          WHERE a.id != b.id AND
                                a.editable_id = b.editable_id AND
                                a.final_state = 3 AND
                                b.final_state = 3 AND
                                a.editor_id IS NOT NULL AND
                                a.editor_id = b.editor_id AND
                                a.reviewed_dt IS NOT NULL AND
                                a.reviewed_dt = b.reviewed_dt)
    '''
    new_revisions = []
    for id, editable_id, submitter_id, editor_id, reviewed_dt, final_state, comment in conn.execute(query):
        revision_type = {
            _FinalRevisionState.needs_submitter_changes: _RevisionType.needs_submitter_changes,
            _FinalRevisionState.accepted: _RevisionType.acceptance,
            _FinalRevisionState.rejected: _RevisionType.rejection,
            _FinalRevisionState.undone: _RevisionType.undo,
        }[final_state]
        if revision_type == _RevisionType.acceptance and editor_id is None:
            revision_type = _RevisionType.changes_acceptance
        # note: for initial_state=needs_submitter_confirmation revisions which were undone, it's not possible to
        # know who was the editor
        new_revisions.append((editable_id, editor_id or submitter_id, id, reviewed_dt, revision_type, comment))
    return new_revisions


def _process_undone_judgment_comments(conn):
    #TODO support more undone judgment types
    query = '''
        SELECT r.editable_id, r.reviewed_dt, c.revision_id, c.user_id, c.created_dt, c.undone_judgment, c.text
        FROM event_editing.comments c
        JOIN event_editing.revisions r ON c.revision_id = r.id
        WHERE c.undone_judgment IN (4, 5) AND c.is_deleted = false
    '''
    new_revisions = []
    for editable_id, reviewed_dt, revision_id, user_id, created_dt, undone_judgment, text in conn.execute(query):
        revision_type = {
            _FinalRevisionState.accepted: _RevisionType.acceptance,
            _FinalRevisionState.rejected: _RevisionType.rejection,
        }[undone_judgment]
        new_revisions.append((editable_id, user_id, revision_id, created_dt, revision_type, text))
        # note: for undone revisions, it's not possible to know who undid it. the best guess is the editor who made
        # the revision
        new_revisions.append((editable_id, user_id, -1, reviewed_dt, _RevisionType.undo, ''))
    op.execute('''
        UPDATE event_editing.comments
        SET is_deleted = true
        WHERE undone_judgment IN (4, 5)
    ''')
    return new_revisions


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    new_revisions = _create_new_revisions(conn)
    new_revisions.extend(_process_undone_judgment_comments(conn))
    op.drop_column('comments', 'undone_judgment', schema='event_editing')
    op.add_column('revisions', sa.Column('revises_id', sa.Integer(), nullable=True), schema='event_editing')
    op.drop_constraint('ck_revisions_valid_state_combination', 'revisions', schema='event_editing')
    op.drop_constraint('ck_revisions_valid_enum_initial_state', 'revisions', schema='event_editing')
    op.alter_column('revisions', 'submitter_id', new_column_name='user_id', schema='event_editing')
    # deal with "request changes with files" revisions
    op.execute('''
        WITH revised_rev AS (
            SELECT a.id, a.comment
            FROM event_editing.revisions AS a
            WHERE EXISTS (SELECT 1
                          FROM event_editing.revisions AS b
                          WHERE a.id != b.id AND
                                a.editable_id = b.editable_id AND
                                a.final_state = 3 AND
                                b.final_state = 3 AND
                                a.editor_id IS NOT NULL AND
                                a.editor_id = b.editor_id AND
                                a.reviewed_dt IS NOT NULL AND
                                a.reviewed_dt = b.reviewed_dt AND
                                a.created_dt < b.created_dt)
        )
        UPDATE event_editing.revisions AS a
        SET user_id = editor_id, initial_state = 5, revises_id = revised_rev.id, comment = revised_rev.comment
        FROM revised_rev
        WHERE EXISTS (SELECT 1
                      FROM event_editing.revisions AS b
                      WHERE a.id != b.id AND
                            a.editable_id = b.editable_id AND
                            a.final_state = 3 AND
                            b.final_state = 3 AND
                            a.editor_id IS NOT NULL AND
                            a.editor_id = b.editor_id AND
                            a.reviewed_dt IS NOT NULL AND
                            a.reviewed_dt = b.reviewed_dt AND
                            a.created_dt > b.created_dt)
    ''')
    # move comments from "needs submitter confirmation" revisions
    op.execute('''
        WITH revs_lag AS (
            SELECT id, LAG(comment) OVER (PARTITION BY editable_id ORDER BY created_dt) AS prev_comment
            FROM event_editing.revisions
        )
        UPDATE event_editing.revisions AS revs
        SET comment = revs_lag.prev_comment
        FROM revs_lag
        WHERE revs.id = revs_lag.id AND revs.initial_state = 3
    ''')
    # delete comments from revisions already added in _create_new_revisions and in the above operations
    op.execute('''
        UPDATE event_editing.revisions AS a
        SET comment = ''
        WHERE a.final_state IN (3, 4, 5, 6) AND
              NOT EXISTS (SELECT 1
                          FROM event_editing.revisions AS b
                          WHERE a.id != b.id AND
                                a.editable_id = b.editable_id AND
                                a.final_state = 3 AND
                                b.final_state = 3 AND
                                a.editor_id IS NOT NULL AND
                                a.editor_id = b.editor_id AND
                                a.reviewed_dt IS NOT NULL AND
                                a.reviewed_dt = b.reviewed_dt AND
                                a.created_dt > b.created_dt)
    ''')
    op.drop_column('revisions', 'editor_id', schema='event_editing')
    op.alter_column('revisions', 'initial_state', new_column_name='type', schema='event_editing')
    op.create_check_constraint('valid_enum_type', 'revisions',
                               '(type = ANY (ARRAY[1, 2, 3, 4, 5, 6, 7, 8]))', schema='event_editing')
    op.create_index(op.f('ix_revisions_revises_id'), 'revisions', ['revises_id'], unique=False, schema='event_editing')
    op.create_foreign_key(op.f('fk_revisions_revises_id_revisions'), 'revisions', 'revisions', ['revises_id'], ['id'],
                          source_schema='event_editing', referent_schema='event_editing')
    op.drop_column('revisions', 'final_state', schema='event_editing')
    op.drop_column('revisions', 'reviewed_dt', schema='event_editing')
    for rev in new_revisions:
        if rev[2] == -1:
            conn.execute('''
                INSERT INTO event_editing.revisions
                (editable_id, user_id, revises_id, created_dt, type, comment) VALUES
                (%s, %s, (SELECT id FROM event_editing.revisions ORDER BY id DESC LIMIT 1), %s, %s, %s)
            ''', rev[:2] + rev[3:])
        else:
            conn.execute('''
                INSERT INTO event_editing.revisions
                (editable_id, user_id, revises_id, created_dt, type, comment) VALUES
                (%s,          %s,      %s,         %s,         %s,   %s)
            ''', rev)
    op.execute('''
        WITH revs_lag AS (
            SELECT id, LAG(id) OVER (PARTITION BY editable_id ORDER BY created_dt) AS prev_id
            FROM event_editing.revisions
        )
        UPDATE event_editing.revisions AS revs
        SET revises_id = revs_lag.prev_id
        FROM revs_lag
        WHERE revs.id = revs_lag.id AND revises_id IS NULL
    ''')
    op.create_check_constraint('revises_set_unless_new', 'revisions', 'type IN (1, 2) OR revises_id IS NOT NULL',
                               schema='event_editing')


def downgrade():
    op.add_column('revisions', sa.Column('reviewed_dt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True), schema='event_editing')
    op.add_column('revisions', sa.Column('final_state', PyIntEnum(_FinalRevisionState), nullable=False), schema='event_editing')
    op.drop_constraint('ck_revisions_revises_set_unless_new', 'revisions', schema='event_editing')
    op.drop_constraint('ck_revisions_valid_enum_type', 'revisions', schema='event_editing')
    op.alter_column('revisions', 'type', new_column_name='inital_state', schema='event_editing')
    op.create_check_constraint('valid_enum_initial_state', 'revisions',
                               '(initial_state = ANY (ARRAY[1, 2, 3]))', schema='event_editing')
    op.drop_constraint(op.f('fk_revisions_revises_id_revisions'), 'revisions', schema='event_editing', type_='foreignkey')
    op.drop_index(op.f('ix_revisions_revises_id'), table_name='revisions', schema='event_editing')
    op.drop_column('revisions', 'revises_id', schema='event_editing')
    op.add_column('revisions', sa.Column('editor_id', sa.Integer(), nullable=True), schema='event_editing') # TODO add FK
    op.alter_column('revisions', 'user_id', new_column_name='submitter_id', schema='event_editing')
    # TODO restore order here
    op.create_check_constraint('valid_state_combination', 'revisions',
                               '(initial_state=1 AND final_state IN (0,1)) OR (initial_state=2) OR '
                               '(initial_state=3 AND (final_state IN (0,3,4,6)))', schema='event_editing')
    op.add_column('comments', sa.Column('undone_judgment', PyIntEnum(_FinalRevisionState), nullable=False), schema='event_editing')
