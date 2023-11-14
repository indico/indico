"""Refactor editing revisions

Revision ID: 0af8f63aa603
Revises: a59688f9ba40
Create Date: 2023-08-07 09:44:11.504348
"""

# ruff: noqa: S608

import sqlalchemy as sa
from alembic import context, op

from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime
from indico.util.enum import IndicoIntEnum


# revision identifiers, used by Alembic.
revision = '0af8f63aa603'
down_revision = 'a59688f9ba40'
branch_labels = None
depends_on = None


class _RevisionType(IndicoIntEnum):
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


class _FinalRevisionState(IndicoIntEnum):
    none = 0
    replaced = 1
    needs_submitter_confirmation = 2
    needs_submitter_changes = 3
    accepted = 4
    rejected = 5
    undone = 6


def _create_new_revisions(conn):
    query = f'''
        SELECT id, editable_id, submitter_id, editor_id, reviewed_dt, final_state, comment
        FROM event_editing.revisions AS a
        WHERE a.final_state IN ({_FinalRevisionState.needs_submitter_changes},
                                {_FinalRevisionState.accepted},
                                {_FinalRevisionState.rejected}) AND
              NOT EXISTS (SELECT 1
                          FROM event_editing.revisions AS b
                          WHERE a.id != b.id AND
                                a.editable_id = b.editable_id AND
                                a.final_state = {_FinalRevisionState.needs_submitter_changes} AND
                                b.final_state = {_FinalRevisionState.needs_submitter_changes} AND
                                a.editor_id IS NOT NULL AND
                                a.editor_id = b.editor_id AND
                                a.reviewed_dt IS NOT NULL AND
                                a.reviewed_dt = b.reviewed_dt)
    '''
    new_revisions = []
    for id, editable_id, submitter_id, editor_id, reviewed_dt, final_state, comment in conn.execute(query):
        user_id = editor_id if editor_id is not None else submitter_id
        revision_type = {
            _FinalRevisionState.needs_submitter_changes: (_RevisionType.needs_submitter_changes
                                                          if editor_id is not None
                                                          else _RevisionType.changes_rejection),
            _FinalRevisionState.accepted: (_RevisionType.acceptance
                                           if editor_id is not None
                                           else _RevisionType.changes_acceptance),
            _FinalRevisionState.rejected: _RevisionType.rejection,
        }[final_state]
        # for initial_state=needs_submitter_confirmation revisions approved by the submitter, it is not possible
        # to know who was the approving submitter. thus, we use the submitter of the first revision as a fallback
        if revision_type == _RevisionType.changes_acceptance:
            query = '''
                SELECT submitter_id
                FROM event_editing.revisions
                WHERE editable_id = %s
                ORDER BY created_dt
                LIMIT 1
            '''
            user_id = conn.execute(query, (editable_id,)).scalar()
        # get the comments to transfer to the new revision
        query = '''
            SELECT id
            FROM event_editing.comments
            WHERE revision_id = %s AND
                  created_dt >= %s AND
                  undone_judgment = 0
        '''
        comment_ids = tuple(id_ for id_, in conn.execute(query, (id, reviewed_dt)).fetchall())
        new_revisions.append((editable_id, user_id, reviewed_dt, revision_type, False, comment, comment_ids))
    return new_revisions


def _process_undone_judgment_comments(conn):
    query = f'''
        SELECT r.editable_id, c.user_id, c.created_dt, c.undone_judgment, c.text
        FROM event_editing.comments c
        JOIN event_editing.revisions r ON c.revision_id = r.id
        WHERE c.undone_judgment IN ({_FinalRevisionState.accepted}, {_FinalRevisionState.rejected}) AND
              c.is_deleted = false
    '''
    new_revisions = []
    for editable_id, user_id, created_dt, undone_judgment, text in conn.execute(query):
        revision_type = {
            _FinalRevisionState.accepted: _RevisionType.acceptance,
            _FinalRevisionState.rejected: _RevisionType.rejection,
        }[undone_judgment]
        new_revisions.append((editable_id, user_id, created_dt, revision_type, True, text, []))
    op.execute(f'''
        UPDATE event_editing.comments
        SET is_deleted = true
        WHERE undone_judgment IN ({_FinalRevisionState.accepted}, {_FinalRevisionState.rejected})
    ''')
    return new_revisions


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    # deal with some revisions being reviewed before being created
    # the "request changes with files" are trickier because we can't change the reviewed_dt
    # since it's used to determine their state
    op.execute(f'''
        UPDATE event_editing.revisions AS a
        SET created_dt = reviewed_dt - interval '1 millisecond'
        WHERE reviewed_dt <= created_dt AND
              EXISTS (SELECT 1
                      FROM event_editing.revisions AS b
                      WHERE a.id != b.id AND
                            a.editable_id = b.editable_id AND
                            a.final_state = {_FinalRevisionState.needs_submitter_changes} AND
                            b.final_state = {_FinalRevisionState.needs_submitter_changes} AND
                            a.editor_id IS NOT NULL AND
                            a.editor_id = b.editor_id AND
                            a.reviewed_dt IS NOT NULL AND
                            a.reviewed_dt = b.reviewed_dt AND
                            a.created_dt > b.created_dt)
    ''')
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
    op.execute(f'''
        UPDATE event_editing.revisions
        SET is_undone = true
        WHERE final_state = {_FinalRevisionState.undone}
    ''')
    op.drop_constraint('ck_revisions_valid_state_combination', 'revisions', schema='event_editing')
    op.drop_constraint('ck_revisions_valid_enum_initial_state', 'revisions', schema='event_editing')
    op.alter_column('revisions', 'submitter_id', new_column_name='user_id', schema='event_editing')
    op.execute('''
        ALTER TABLE event_editing.revisions RENAME CONSTRAINT fk_revisions_submitter_id_users TO fk_revisions_user_id_users;
        ALTER INDEX event_editing.ix_revisions_submitter_id RENAME TO ix_revisions_user_id;
    ''')
    # deal with the "replacement" revisions
    op.execute(f'''
        WITH revs_lag AS (
            SELECT id, LAG(final_state) OVER (PARTITION BY editable_id ORDER BY created_dt) AS prev_final_state
            FROM event_editing.revisions
        )
        UPDATE event_editing.revisions AS revs
        SET initial_state = {_RevisionType.replacement}
        FROM revs_lag
        WHERE revs.id = revs_lag.id AND revs_lag.prev_final_state = {_FinalRevisionState.replaced}
    ''')
    # deal with "request changes with files" revisions
    op.execute(f'''
        WITH revised_rev AS (
            SELECT a.id, a.comment
            FROM event_editing.revisions AS a
            WHERE EXISTS (SELECT 1
                          FROM event_editing.revisions AS b
                          WHERE a.id != b.id AND
                                a.editable_id = b.editable_id AND
                                a.final_state = {_FinalRevisionState.needs_submitter_changes} AND
                                b.final_state = {_FinalRevisionState.needs_submitter_changes} AND
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
                            a.final_state = {_FinalRevisionState.needs_submitter_changes} AND
                            b.final_state = {_FinalRevisionState.needs_submitter_changes} AND
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
    op.execute(f'''
        UPDATE event_editing.revisions AS a
        SET comment = ''
        WHERE a.final_state IN ({_FinalRevisionState.needs_submitter_changes}, {_FinalRevisionState.accepted},
                                {_FinalRevisionState.rejected}, {_FinalRevisionState.undone}) AND
              NOT EXISTS (SELECT 1
                          FROM event_editing.revisions AS b
                          WHERE a.id != b.id AND
                                a.editable_id = b.editable_id AND
                                a.final_state = {_FinalRevisionState.needs_submitter_changes} AND
                                b.final_state = {_FinalRevisionState.needs_submitter_changes} AND
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
        res = conn.execute('''
            INSERT INTO event_editing.revisions
            (editable_id, user_id, created_dt, type, is_undone, comment) VALUES
            (%s,          %s,      %s,         %s,   %s,        %s)
            RETURNING id
        ''', rev[:-1])
        revision_id = res.fetchone()[0]
        if rev[-1]:
            conn.execute('UPDATE event_editing.comments SET revision_id = %s WHERE id IN %s', (revision_id, rev[-1]))
    op.create_check_constraint('new_revision_not_undone', 'revisions', 'type != 1 OR NOT is_undone',
                               schema='event_editing')


def downgrade():
    op.add_column('revisions', sa.Column('reviewed_dt', UTCDateTime, nullable=True), schema='event_editing')
    op.add_column('revisions', sa.Column('final_state', PyIntEnum(_FinalRevisionState), nullable=False,
                                         server_default='0'), schema='event_editing')
    op.create_check_constraint('reviewed_dt_set_when_final_state', 'revisions',
                               '((final_state = 0) OR (reviewed_dt IS NOT NULL))', schema='event_editing')
    op.alter_column('revisions', 'final_state', server_default=None, schema='event_editing')
    op.drop_constraint('ck_revisions_new_revision_not_undone', 'revisions', schema='event_editing')
    op.drop_constraint('ck_revisions_valid_enum_type', 'revisions', schema='event_editing')
    op.add_column('revisions', sa.Column('editor_id', sa.Integer(), nullable=True), schema='event_editing')
    op.create_index(None, 'revisions', ['editor_id'], schema='event_editing')
    op.create_foreign_key(None, 'revisions', 'users', ['editor_id'], ['id'],
                          source_schema='event_editing', referent_schema='users')
    op.execute('''
        DELETE FROM event_editing.revision_files
        WHERE revision_id IN (SELECT id FROM event_editing.revisions WHERE is_undone = true)
    ''')
    op.execute('''
        DELETE FROM event_editing.revision_tags
        WHERE revision_id IN (SELECT id FROM event_editing.revisions WHERE is_undone = true)
    ''')
    op.execute(f'''
        DELETE FROM event_editing.revisions
        WHERE type = {_RevisionType.reset} OR is_undone = true
    ''')
    op.execute(f'''
        UPDATE event_editing.revisions
        SET type = {_RevisionType.ready_for_review},
            final_state = {_FinalRevisionState.needs_submitter_changes},
            reviewed_dt = created_dt,
            editor_id = user_id
        WHERE type = {_RevisionType.needs_submitter_changes} AND id IN (SELECT revision_id
                                                                        FROM event_editing.revision_files)
    ''')
    op.execute(f'''
        UPDATE event_editing.revisions
        SET type = {_RevisionType.ready_for_review}
        WHERE type = {_RevisionType.replacement}
    ''')
    op.execute(f'''
        WITH revs_lag AS (
            SELECT id,
                   LEAD(type) OVER (PARTITION BY editable_id ORDER BY created_dt) AS next_type,
                   LEAD(user_id) OVER (PARTITION BY editable_id ORDER BY created_dt) AS next_user_id,
                   LEAD(created_dt) OVER (PARTITION BY editable_id ORDER BY created_dt) AS next_created_dt
            FROM event_editing.revisions
        )
        UPDATE event_editing.revisions AS revs
        SET editor_id = revs_lag.next_user_id, reviewed_dt = revs_lag.next_created_dt, final_state = CASE
            WHEN revs_lag.next_type = {_RevisionType.changes_acceptance} THEN {_FinalRevisionState.accepted}
            WHEN revs_lag.next_type = {_RevisionType.changes_rejection} THEN {_FinalRevisionState.needs_submitter_changes}
            WHEN revs_lag.next_type = {_RevisionType.acceptance} THEN {_FinalRevisionState.accepted}
            WHEN revs_lag.next_type = {_RevisionType.rejection} THEN {_FinalRevisionState.rejected}
            WHEN revs_lag.next_type = {_RevisionType.replacement} THEN {_FinalRevisionState.replaced}
            ELSE {_FinalRevisionState.none}
        END
        FROM revs_lag
        WHERE revs.id = revs_lag.id AND revs_lag.next_type > 3 AND revs.final_state = {_FinalRevisionState.none}
    ''')
    op.execute('''
        UPDATE event_editing.editables AS e
        SET published_revision_id = (SELECT id
                                     FROM event_editing.revisions
                                     WHERE editable_id = e.id AND type <= 3
                                     ORDER BY created_dt DESC
                                     LIMIT 1)
        WHERE published_revision_id IN (SELECT id FROM event_editing.revisions WHERE type > 3)
    ''')
    op.execute('''
        DELETE FROM event_editing.revision_tags
        WHERE revision_id IN (SELECT id FROM event_editing.revisions WHERE type > 3)
    ''')
    op.execute('''
        DELETE FROM event_editing.revisions
        WHERE type > 3
    ''')
    op.alter_column('revisions', 'type', new_column_name='initial_state', schema='event_editing')
    op.create_check_constraint('valid_enum_initial_state', 'revisions',
                               '(initial_state = ANY (ARRAY[1, 2, 3]))', schema='event_editing')
    op.drop_column('revisions', 'is_undone', schema='event_editing')
    op.alter_column('revisions', 'user_id', new_column_name='submitter_id', schema='event_editing')
    op.execute('''
        ALTER TABLE event_editing.revisions RENAME CONSTRAINT fk_revisions_user_id_users TO fk_revisions_submitter_id_users;
        ALTER INDEX event_editing.ix_revisions_user_id RENAME TO ix_revisions_submitter_id;
    ''')
    op.create_check_constraint('valid_state_combination', 'revisions',
                               '(initial_state=1 AND final_state IN (0,1)) OR (initial_state=2) OR '
                               '(initial_state=3 AND (final_state IN (0,3,4,6)))', schema='event_editing')
    op.add_column('comments', sa.Column('undone_judgment', PyIntEnum(_FinalRevisionState), nullable=False,
                                        server_default='0'), schema='event_editing')
    op.alter_column('comments', 'undone_judgment', server_default=None, schema='event_editing')
