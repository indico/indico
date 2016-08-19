"""Rename abstracts table

Revision ID: 2ce1756a2f12
Revises: 5596683819c9
Create Date: 2016-08-22 14:57:28.005919
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '2ce1756a2f12'
down_revision = '5596683819c9'


def upgrade():
    op.rename_table('abstracts', 'legacy_abstracts', schema='event_abstracts')
    op.execute('''
        ALTER INDEX event_abstracts.ix_abstracts_accepted_track_id RENAME TO ix_legacy_abstracts_accepted_track_id;
        ALTER INDEX event_abstracts.ix_abstracts_accepted_type_id RENAME TO ix_legacy_abstracts_accepted_type_id;
        ALTER INDEX event_abstracts.ix_abstracts_event_id RENAME TO ix_legacy_abstracts_event_id;
        ALTER INDEX event_abstracts.ix_abstracts_type_id RENAME TO ix_legacy_abstracts_type_id;
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
        sa.Column('type_id', sa.Integer(), nullable=True, index=True),
        sa.Column('final_track_id', sa.Integer(), nullable=True, index=True),
        sa.Column('final_type_id', sa.Integer(), nullable=True, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['final_type_id'], ['events.contribution_types.id']),
        sa.ForeignKeyConstraint(['type_id'], ['events.contribution_types.id']),
        sa.ForeignKeyConstraint(['final_track_id'], ['events.tracks.id']),
        sa.UniqueConstraint('friendly_id', 'event_id'),
        sa.PrimaryKeyConstraint('id'),
        schema='event_abstracts'
    )


def downgrade():
    op.drop_table('abstracts', schema='event_abstracts')
    op.rename_table('legacy_abstracts', 'abstracts', schema='event_abstracts')
    op.execute('''
        ALTER INDEX event_abstracts.ix_legacy_abstracts_accepted_track_id RENAME TO ix_abstracts_accepted_track_id;
        ALTER INDEX event_abstracts.ix_legacy_abstracts_accepted_type_id RENAME TO ix_abstracts_accepted_type_id;
        ALTER INDEX event_abstracts.ix_legacy_abstracts_event_id RENAME TO ix_abstracts_event_id;
        ALTER INDEX event_abstracts.ix_legacy_abstracts_type_id RENAME TO ix_abstracts_type_id;
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
