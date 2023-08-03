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
    changes_rejection = 5
    needs_submitter_changes = 6
    acceptance = 7
    rejection = 8
    replacement = 9
    reset = 10


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
        SELECT editable_id, submitter_id, editor_id, reviewed_dt, final_state, comment
        FROM event_editing.revisions AS a
        WHERE a.final_state IN (3, 4, 5) AND
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
    for editable_id, submitter_id, editor_id, reviewed_dt, final_state, comment in conn.execute(query):
        revision_type = {
            _FinalRevisionState.needs_submitter_changes: _RevisionType.changes_rejection,
            _FinalRevisionState.accepted: _RevisionType.acceptance,
            _FinalRevisionState.rejected: _RevisionType.rejection,
        }[final_state]
        if revision_type == _RevisionType.acceptance and editor_id is None:
            revision_type = _RevisionType.changes_acceptance
        # note: for initial_state=needs_submitter_confirmation revisions which were undone, it's not possible to
        # know who was the editor
        new_revisions.append((editable_id, editor_id or submitter_id, reviewed_dt, revision_type, False, comment))
    return new_revisions


def _process_undone_judgment_comments(conn):
    #TODO support more undone judgment types (2,3 in particular)
    query = '''
        SELECT r.editable_id, c.user_id, c.created_dt, c.undone_judgment, c.text
        FROM event_editing.comments c
        JOIN event_editing.revisions r ON c.revision_id = r.id
        WHERE c.undone_judgment IN (4, 5) AND c.is_deleted = false
    '''
    new_revisions = []
    for editable_id, user_id, created_dt, undone_judgment, text in conn.execute(query):
        revision_type = {
            _FinalRevisionState.accepted: _RevisionType.acceptance,
            _FinalRevisionState.rejected: _RevisionType.rejection,
        }[undone_judgment]
        new_revisions.append((editable_id, user_id, created_dt, revision_type, True, text))
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
    # deal with erratic reviewed_dt's
    op.execute('''
        UPDATE event_editing.revisions
        SET reviewed_dt = created_dt + interval '1 millisecond'
        WHERE reviewed_dt <= created_dt
    ''')
    new_revisions = _create_new_revisions(conn)
    new_revisions.extend(_process_undone_judgment_comments(conn))
    op.drop_column('comments', 'undone_judgment', schema='event_editing')
    op.add_column('revisions', sa.Column('is_undone', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_editing')
    op.alter_column('revisions', 'is_undone', server_default=None, schema='event_editing')
    op.execute('''
        UPDATE event_editing.revisions
        SET is_undone = true
        WHERE final_state = 6
    ''')
    op.drop_constraint('ck_revisions_valid_state_combination', 'revisions', schema='event_editing')
    op.drop_constraint('ck_revisions_valid_enum_initial_state', 'revisions', schema='event_editing')
    op.alter_column('revisions', 'submitter_id', new_column_name='user_id', schema='event_editing')
    # deal with the "replacement" revisions
    op.execute('''
        WITH revs_lag AS (
            SELECT id, LAG(final_state) OVER (PARTITION BY editable_id ORDER BY created_dt) AS prev_final_state
            FROM event_editing.revisions
        )
        UPDATE event_editing.revisions AS revs
        SET initial_state = 9
        FROM revs_lag
        WHERE revs.id = revs_lag.id AND revs_lag.prev_final_state = 1
    ''')
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
        SET user_id = editor_id, initial_state = 6, comment = revised_rev.comment
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
                               '(type = ANY (ARRAY[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))', schema='event_editing')
    op.drop_column('revisions', 'final_state', schema='event_editing')
    op.drop_column('revisions', 'reviewed_dt', schema='event_editing')
    for rev in new_revisions:
        conn.execute('''
            INSERT INTO event_editing.revisions
            (editable_id, user_id, created_dt, type, is_undone, comment) VALUES
            (%s,          %s,      %s,         %s,   %s,        %s)
        ''', rev)
    op.create_check_constraint('new_revision_not_undone', 'revisions', 'type != 1 OR is_undone = false',
                               schema='event_editing')


def downgrade():
    op.add_column('revisions', sa.Column('reviewed_dt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True), schema='event_editing')
    op.add_column('revisions', sa.Column('final_state', PyIntEnum(_FinalRevisionState), nullable=False), schema='event_editing')
    op.drop_constraint('ck_revisions_new_revision_not_undone', 'revisions', schema='event_editing')
    op.drop_constraint('ck_revisions_valid_enum_type', 'revisions', schema='event_editing')
    op.alter_column('revisions', 'type', new_column_name='inital_state', schema='event_editing')
    op.create_check_constraint('valid_enum_initial_state', 'revisions',
                               '(initial_state = ANY (ARRAY[1, 2, 3]))', schema='event_editing')
    op.drop_column('revisions', 'is_undone', schema='event_editing')
    op.add_column('revisions', sa.Column('editor_id', sa.Integer(), nullable=True), schema='event_editing') # TODO add FK
    op.create_foreign_key(None, 'revisions', 'users', ['editor_id'], ['id'],
                          source_schema='event_editing', referent_schema='users')
    op.alter_column('revisions', 'user_id', new_column_name='submitter_id', schema='event_editing')
    # TODO restore order here
    op.create_check_constraint('valid_state_combination', 'revisions',
                               '(initial_state=1 AND final_state IN (0,1)) OR (initial_state=2) OR '
                               '(initial_state=3 AND (final_state IN (0,3,4,6)))', schema='event_editing')
    op.add_column('comments', sa.Column('undone_judgment', PyIntEnum(_FinalRevisionState), nullable=False), schema='event_editing')
