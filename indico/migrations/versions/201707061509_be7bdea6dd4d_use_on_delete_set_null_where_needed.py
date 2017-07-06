"""Use ON DELETE SET NULL where needed

Revision ID: be7bdea6dd4d
Revises: 563fa8622042
Create Date: 2017-07-06 15:09:36.927545
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'be7bdea6dd4d'
down_revision = '563fa8622042'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('fk_abstracts_submitted_contrib_type_id_contribution_types', 'abstracts',
                       schema='event_abstracts')
    op.create_foreign_key(None,
                          'abstracts', 'contribution_types',
                          ['submitted_contrib_type_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='events',
                          ondelete='SET NULL')

    op.drop_constraint('fk_abstracts_accepted_contrib_type_id_contribution_types', 'abstracts',
                       schema='event_abstracts')
    op.create_foreign_key(None,
                          'abstracts', 'contribution_types',
                          ['accepted_contrib_type_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='events',
                          ondelete='SET NULL')

    op.drop_constraint('fk_abstracts_accepted_track_id_tracks', 'abstracts',
                       schema='event_abstracts')
    op.create_foreign_key(None,
                          'abstracts', 'tracks',
                          ['accepted_track_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='events',
                          ondelete='SET NULL')

    op.drop_constraint('fk_proposed_for_tracks_track_id_tracks', 'proposed_for_tracks', schema='event_abstracts')
    op.create_foreign_key(None,
                          'proposed_for_tracks', 'tracks',
                          ['track_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='events',
                          ondelete='CASCADE')

    op.drop_constraint('fk_reviewed_for_tracks_track_id_tracks', 'reviewed_for_tracks', schema='event_abstracts')
    op.create_foreign_key(None,
                          'reviewed_for_tracks', 'tracks',
                          ['track_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='events',
                          ondelete='CASCADE')

    op.drop_constraint('fk_submitted_for_tracks_track_id_tracks', 'submitted_for_tracks', schema='event_abstracts')
    op.create_foreign_key(None,
                          'submitted_for_tracks', 'tracks',
                          ['track_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='events',
                          ondelete='CASCADE')

    op.drop_constraint('fk_contributions_track_id_tracks', 'contributions', schema='events')
    op.create_foreign_key(None,
                          'contributions', 'tracks',
                          ['track_id'], ['id'],
                          source_schema='events', referent_schema='events',
                          ondelete='SET NULL')


def downgrade():
    op.drop_constraint('fk_contributions_track_id_tracks', 'contributions', schema='events')
    op.create_foreign_key('fk_contributions_track_id_tracks',
                          'contributions', 'tracks',
                          ['track_id'], ['id'],
                          source_schema='events', referent_schema='events')

    op.drop_constraint('fk_submitted_for_tracks_track_id_tracks', 'submitted_for_tracks', schema='event_abstracts')
    op.create_foreign_key('fk_submitted_for_tracks_track_id_tracks',
                          'submitted_for_tracks', 'tracks',
                          ['track_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='events')

    op.drop_constraint('fk_reviewed_for_tracks_track_id_tracks', 'reviewed_for_tracks', schema='event_abstracts')
    op.create_foreign_key('fk_reviewed_for_tracks_track_id_tracks',
                          'reviewed_for_tracks', 'tracks',
                          ['track_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='events')

    op.drop_constraint('fk_proposed_for_tracks_track_id_tracks', 'proposed_for_tracks', schema='event_abstracts')
    op.create_foreign_key('fk_proposed_for_tracks_track_id_tracks',
                          'proposed_for_tracks', 'tracks',
                          ['track_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='events')

    op.drop_constraint('fk_abstracts_accepted_track_id_tracks', 'abstracts',
                       schema='event_abstracts')
    op.create_foreign_key('fk_abstracts_accepted_track_id_tracks',
                          'abstracts', 'tracks',
                          ['accepted_track_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='events')

    op.drop_constraint('fk_abstracts_accepted_contrib_type_id_contribution_types', 'abstracts',
                       schema='event_abstracts')
    op.create_foreign_key('fk_abstracts_accepted_contrib_type_id_contribution_types',
                          'abstracts', 'contribution_types',
                          ['accepted_contrib_type_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='events')

    op.drop_constraint('fk_abstracts_submitted_contrib_type_id_contribution_types', 'abstracts',
                       schema='event_abstracts')
    op.create_foreign_key('fk_abstracts_submitted_contrib_type_id_contribution_types',
                          'abstracts', 'contribution_types',
                          ['submitted_contrib_type_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='events')
