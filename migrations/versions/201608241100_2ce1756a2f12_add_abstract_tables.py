"""Add abstracts tables

Revision ID: 2ce1756a2f12
Revises: 4f426059ddd1
Create Date: 2016-08-22 14:57:28.005919
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import UTCDateTime, PyIntEnum
from indico.modules.events.abstracts.models.abstracts import AbstractState
from indico.modules.events.abstracts.models.persons import AuthorType
from indico.modules.events.abstracts.models.reviews import AbstractAction, AbstractCommentVisibility
from indico.modules.users.models.users import UserTitle
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2ce1756a2f12'
down_revision = '4f426059ddd1'


def upgrade():
    op.drop_constraint('fk_contributions_abstract_id_abstracts', 'contributions', schema='events')
    op.drop_constraint('fk_abstract_field_values_abstract_id_abstracts', 'abstract_field_values',
                       schema='event_abstracts')
    op.drop_constraint('fk_judgments_abstract_id_abstracts', 'judgments', schema='event_abstracts')

    op.rename_table('abstracts', 'legacy_abstracts', schema='event_abstracts')
    op.execute('''
        ALTER INDEX event_abstracts.ix_abstracts_accepted_track_id RENAME TO ix_legacy_abstracts_accepted_track_id;
        ALTER INDEX event_abstracts.ix_abstracts_accepted_type_id RENAME TO ix_legacy_abstracts_accepted_type_id;
        ALTER INDEX event_abstracts.ix_abstracts_event_id RENAME TO ix_legacy_abstracts_event_id;
        ALTER INDEX event_abstracts.ix_abstracts_type_id RENAME TO ix_legacy_abstracts_type_id;
        ALTER SEQUENCE event_abstracts.abstracts_id_seq RENAME TO legacy_abstracts_id_seq;
        ALTER TABLE event_abstracts.legacy_abstracts RENAME CONSTRAINT pk_abstracts TO pk_legacy_abstracts;
        ALTER TABLE event_abstracts.legacy_abstracts RENAME CONSTRAINT
            fk_abstracts_accepted_type_id_contribution_types TO fk_legacy_abstracts_accepted_type_id_contribution_types;
        ALTER TABLE event_abstracts.legacy_abstracts RENAME CONSTRAINT
            fk_abstracts_event_id_events TO fk_legacy_abstracts_event_id_events;
        ALTER TABLE event_abstracts.legacy_abstracts RENAME CONSTRAINT
            fk_abstracts_type_id_contribution_types TO fk_legacy_abstracts_type_id_contribution_types;
        ALTER TABLE event_abstracts.legacy_abstracts RENAME CONSTRAINT
            uq_abstracts_friendly_id_event_id TO uq_legacy_abstracts_friendly_id_event_id;
    ''')

    op.create_table(
        'abstracts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('friendly_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('submitter_id', sa.Integer(), nullable=False, index=True),
        sa.Column('modified_by_id', sa.Integer(), nullable=True, index=True),
        sa.Column('submitted_contrib_type_id', sa.Integer(), nullable=True, index=True),
        sa.Column('submitted_dt', UTCDateTime, nullable=False),
        sa.Column('modified_dt', UTCDateTime, nullable=True),
        sa.Column('state', PyIntEnum(AbstractState), nullable=False),
        sa.Column('submission_comment', sa.Text(), nullable=False),
        sa.Column('judge_id', sa.Integer(), nullable=True, index=True),
        sa.Column('judgment_dt', UTCDateTime, nullable=True),
        sa.Column('judgment_comment', sa.Text(), nullable=False),
        sa.Column('accepted_track_id', sa.Integer(), nullable=True, index=True),
        sa.Column('accepted_contrib_type_id', sa.Integer(), nullable=True, index=True),
        sa.Column('merged_into_id', sa.Integer(), nullable=True, index=True),
        sa.Column('duplicate_of_id', sa.Integer(), nullable=True, index=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['submitter_id'], ['users.users.id']),
        sa.ForeignKeyConstraint(['modified_by_id'], ['users.users.id']),
        sa.ForeignKeyConstraint(['submitted_contrib_type_id'], ['events.contribution_types.id']),
        sa.ForeignKeyConstraint(['judge_id'], ['users.users.id']),
        sa.ForeignKeyConstraint(['accepted_contrib_type_id'], ['events.contribution_types.id']),
        sa.ForeignKeyConstraint(['accepted_track_id'], ['events.tracks.id']),
        sa.ForeignKeyConstraint(['merged_into_id'], ['event_abstracts.abstracts.id']),
        sa.ForeignKeyConstraint(['duplicate_of_id'], ['event_abstracts.abstracts.id']),
        sa.UniqueConstraint('friendly_id', 'event_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('(state = 3) OR (accepted_track_id IS NULL)',
                           name='accepted_track_id_only_accepted'),
        sa.CheckConstraint('(state = 3) OR (accepted_contrib_type_id IS NULL)',
                           name='accepted_contrib_type_id_only_accepted'),
        sa.CheckConstraint('(state = 5) = (merged_into_id IS NOT NULL)',
                           name='merged_into_id_only_merged'),
        sa.CheckConstraint('(state = 6) = (duplicate_of_id IS NOT NULL)',
                           name='duplicate_of_id_only_duplicate'),
        sa.CheckConstraint('(state IN (3, 4, 5, 6)) = (judge_id IS NOT NULL)',
                           name='judge_if_judged'),
        sa.CheckConstraint('(state IN (3, 4, 5, 6)) = (judgment_dt IS NOT NULL)',
                           name='judgment_dt_if_judged'),
        schema='event_abstracts'
    )

    op.create_table(
        'submitted_for_tracks',
        sa.Column('abstract_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
        sa.Column('track_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
        sa.ForeignKeyConstraint(['abstract_id'], ['event_abstracts.abstracts.id']),
        sa.ForeignKeyConstraint(['track_id'], ['events.tracks.id']),
        sa.PrimaryKeyConstraint('abstract_id', 'track_id'),
        schema='event_abstracts'
    )

    op.create_table(
        'reviewed_for_tracks',
        sa.Column('abstract_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
        sa.Column('track_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
        sa.ForeignKeyConstraint(['abstract_id'], ['event_abstracts.abstracts.id']),
        sa.ForeignKeyConstraint(['track_id'], ['events.tracks.id']),
        sa.PrimaryKeyConstraint('abstract_id', 'track_id'),
        schema='event_abstracts'
    )

    op.create_table(
        'files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('abstract_id', sa.Integer(), nullable=False, index=True),
        sa.Column('storage_backend', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('storage_file_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['abstract_id'], ['event_abstracts.abstracts.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_abstracts'
    )

    op.create_table(
        'email_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('reply_to_address', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('extra_cc_emails', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('include_submitter', sa.Boolean(), nullable=False),
        sa.Column('include_authors', sa.Boolean(), nullable=False),
        sa.Column('include_coauthors', sa.Boolean(), nullable=False),
        sa.Column('stop_on_match', sa.Boolean(), nullable=False),
        sa.Column('rules', postgresql.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_abstracts'
    )

    op.create_table(
        'abstract_person_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('abstract_id', sa.Integer(), nullable=False, index=True),
        sa.Column('person_id', sa.Integer(), nullable=False, index=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('title', PyIntEnum(UserTitle), nullable=True),
        sa.Column('affiliation', sa.String(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('is_speaker', sa.Boolean(), nullable=False),
        sa.Column('author_type', PyIntEnum(AuthorType), nullable=False),
        sa.ForeignKeyConstraint(['abstract_id'], ['event_abstracts.abstracts.id']),
        sa.ForeignKeyConstraint(['person_id'], ['events.persons.id']),
        sa.UniqueConstraint('person_id', 'abstract_id'),
        sa.PrimaryKeyConstraint('id'),
        schema='event_abstracts'
    )

    op.create_table(
        'abstract_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('abstract_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('modified_by_id', sa.Integer(), nullable=True, index=True),
        sa.Column('created_dt', UTCDateTime, nullable=False),
        sa.Column('modified_dt', UTCDateTime, nullable=True),
        sa.Column('visibility', PyIntEnum(AbstractCommentVisibility), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['abstract_id'], ['event_abstracts.abstracts.id']),
        sa.ForeignKeyConstraint(['modified_by_id'], ['users.users.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_abstracts'
    )

    op.create_table(
        'abstract_review_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('no_score', sa.Boolean(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_abstracts'
    )

    op.create_table(
        'abstract_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('abstract_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('track_id', sa.Integer(), nullable=True, index=True),
        sa.Column('created_dt', UTCDateTime, nullable=False),
        sa.Column('modified_dt', UTCDateTime, nullable=True),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('proposed_action', PyIntEnum(AbstractAction), nullable=False),
        sa.Column('proposed_related_abstract_id', sa.Integer(), nullable=True, index=True),
        sa.Column('proposed_contribution_type_id', sa.Integer(), nullable=True, index=True),
        sa.ForeignKeyConstraint(['abstract_id'], ['event_abstracts.abstracts.id']),
        sa.ForeignKeyConstraint(['proposed_related_abstract_id'], ['event_abstracts.abstracts.id']),
        sa.ForeignKeyConstraint(['proposed_contribution_type_id'], ['events.contribution_types.id']),
        sa.ForeignKeyConstraint(['track_id'], ['events.tracks.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('abstract_id', 'user_id', 'track_id'),
        sa.CheckConstraint("proposed_action = 1 OR (proposed_contribution_type_id IS NULL)",
                           name='prop_contrib_id_only_accepted'),
        sa.CheckConstraint("(proposed_action IN (4, 5)) = (proposed_related_abstract_id IS NOT NULL)",
                           name='prop_abstract_id_only_duplicate_merge'),
        schema='event_abstracts'
    )

    op.create_table(
        'abstract_review_ratings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False, index=True),
        sa.Column('review_id', sa.Integer(), nullable=False, index=True),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['event_abstracts.abstract_review_questions.id']),
        sa.ForeignKeyConstraint(['review_id'], ['event_abstracts.abstract_reviews.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('review_id', 'question_id'),
        schema='event_abstracts'
    )

    op.create_table(
        'proposed_for_tracks',
        sa.Column('review_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
        sa.Column('track_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
        sa.ForeignKeyConstraint(['review_id'], ['event_abstracts.abstract_reviews.id']),
        sa.ForeignKeyConstraint(['track_id'], ['events.tracks.id']),
        sa.PrimaryKeyConstraint('review_id', 'track_id'),
        schema='event_abstracts'
    )

    op.create_table(
        'email_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('abstract_id', sa.Integer(), nullable=False, index=True),
        sa.Column('email_template_id', sa.Integer(), nullable=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('sent_dt', UTCDateTime, nullable=False),
        sa.Column('recipients', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('data', postgresql.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['abstract_id'], ['event_abstracts.abstracts.id']),
        sa.ForeignKeyConstraint(['email_template_id'], ['event_abstracts.email_templates.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_abstracts'
    )

    op.create_table(
        'track_abstract_reviewers',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False, autoincrement=False, index=True),
        sa.Column('event_id', sa.Integer(), nullable=True, autoincrement=False, index=True),
        sa.Column('track_id', sa.Integer(), nullable=True, autoincrement=False, index=True),
        sa.ForeignKeyConstraint(['track_id'], ['events.tracks.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('(track_id IS NULL) != (event_id IS NULL)', name='track_xor_event_id_null'),
        schema='events'
    )

    op.create_table(
        'track_conveners',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False, autoincrement=False, index=True),
        sa.Column('event_id', sa.Integer(), nullable=True, autoincrement=False, index=True),
        sa.Column('track_id', sa.Integer(), nullable=True, autoincrement=False, index=True),
        sa.ForeignKeyConstraint(['track_id'], ['events.tracks.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('(track_id IS NULL) != (event_id IS NULL)', name='track_xor_event_id_null'),
        schema='events'
    )

    op.alter_column('contributions', 'track_id', new_column_name='legacy_track_id', schema='events')
    op.drop_index('ix_contributions_event_id_track_id', table_name='contributions', schema='events')
    op.add_column('contributions', sa.Column('track_id', sa.Integer(), nullable=True), schema='events')
    op.create_index(None, 'contributions', ['track_id'], schema='events')
    op.create_index(None, 'contributions', ['event_id', 'track_id'], schema='events')


def downgrade():
    op.drop_index(op.f('ix_contributions_event_id_track_id'), table_name='contributions', schema='events')
    op.drop_column('contributions', 'track_id', schema='events')
    op.alter_column('contributions', 'legacy_track_id', new_column_name='track_id', schema='events')
    op.create_index(None, 'contributions', ['event_id', 'track_id'], schema='events')

    op.drop_table('track_conveners', schema='events')
    op.drop_table('track_abstract_reviewers', schema='events')
    op.drop_table('email_logs', schema='event_abstracts')
    op.drop_table('proposed_for_tracks', schema='event_abstracts')
    op.drop_table('abstract_review_ratings', schema='event_abstracts')
    op.drop_table('abstract_reviews', schema='event_abstracts')
    op.drop_table('abstract_review_questions', schema='event_abstracts')
    op.drop_table('abstract_comments', schema='event_abstracts')
    op.drop_table('abstract_person_links', schema='event_abstracts')
    op.drop_table('email_templates', schema='event_abstracts')
    op.drop_table('files', schema='event_abstracts')
    op.drop_table('reviewed_for_tracks', schema='event_abstracts')
    op.drop_table('submitted_for_tracks', schema='event_abstracts')
    op.drop_table('abstracts', schema='event_abstracts')
    op.rename_table('legacy_abstracts', 'abstracts', schema='event_abstracts')
    op.execute('''
        ALTER INDEX event_abstracts.ix_legacy_abstracts_accepted_track_id RENAME TO ix_abstracts_accepted_track_id;
        ALTER INDEX event_abstracts.ix_legacy_abstracts_accepted_type_id RENAME TO ix_abstracts_accepted_type_id;
        ALTER INDEX event_abstracts.ix_legacy_abstracts_event_id RENAME TO ix_abstracts_event_id;
        ALTER INDEX event_abstracts.ix_legacy_abstracts_type_id RENAME TO ix_abstracts_type_id;
        ALTER SEQUENCE event_abstracts.legacy_abstracts_id_seq RENAME TO abstracts_id_seq;
        ALTER TABLE event_abstracts.abstracts RENAME CONSTRAINT pk_legacy_abstracts TO pk_abstracts;
        ALTER TABLE event_abstracts.abstracts RENAME CONSTRAINT
            fk_legacy_abstracts_accepted_type_id_contribution_types TO fk_abstracts_accepted_type_id_contribution_types;
        ALTER TABLE event_abstracts.abstracts RENAME CONSTRAINT
            fk_legacy_abstracts_event_id_events TO fk_abstracts_event_id_events;
        ALTER TABLE event_abstracts.abstracts RENAME CONSTRAINT
            fk_legacy_abstracts_type_id_contribution_types TO fk_abstracts_type_id_contribution_types;
        ALTER TABLE event_abstracts.abstracts RENAME CONSTRAINT
            uq_legacy_abstracts_friendly_id_event_id TO uq_abstracts_friendly_id_event_id;
    ''')

    op.create_foreign_key(None,
                          'judgments', 'abstracts',
                          ['abstract_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='event_abstracts')
    op.create_foreign_key(None,
                          'abstract_field_values', 'abstracts',
                          ['abstract_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='event_abstracts')
    op.create_foreign_key(None,
                          'contributions', 'abstracts',
                          ['abstract_id'], ['id'],
                          source_schema='events', referent_schema='event_abstracts')
