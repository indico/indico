"""Add predefined affiliations to persons

Revision ID: 1950e5d12ab5
Revises: c39db219f85a
Create Date: 2022-05-12 10:54:33.212208
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '1950e5d12ab5'
down_revision = 'c39db219f85a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('persons', sa.Column('affiliation_id', sa.Integer(), nullable=True),
                  schema='events')
    op.add_column('abstract_person_links', sa.Column('affiliation_id', sa.Integer(), nullable=True),
                  schema='event_abstracts')
    op.add_column('contribution_person_links', sa.Column('affiliation_id', sa.Integer(), nullable=True),
                  schema='events')
    op.add_column('event_person_links', sa.Column('affiliation_id', sa.Integer(), nullable=True),
                  schema='events')
    op.add_column('session_block_person_links', sa.Column('affiliation_id', sa.Integer(), nullable=True),
                  schema='events')
    op.add_column('subcontribution_person_links', sa.Column('affiliation_id', sa.Integer(), nullable=True),
                  schema='events')
    op.create_foreign_key(None, 'persons', 'affiliations', ['affiliation_id'], ['id'],
                          source_schema='events', referent_schema='indico')
    op.create_foreign_key(None, 'abstract_person_links', 'affiliations', ['affiliation_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='indico')
    op.create_foreign_key(None, 'contribution_person_links', 'affiliations', ['affiliation_id'], ['id'],
                          source_schema='events', referent_schema='indico')
    op.create_foreign_key(None, 'event_person_links', 'affiliations', ['affiliation_id'], ['id'],
                          source_schema='events', referent_schema='indico')
    op.create_foreign_key(None, 'session_block_person_links', 'affiliations', ['affiliation_id'], ['id'],
                          source_schema='events', referent_schema='indico')
    op.create_foreign_key(None, 'subcontribution_person_links', 'affiliations', ['affiliation_id'], ['id'],
                          source_schema='events', referent_schema='indico')
    op.create_index(None, 'persons', ['affiliation_id'], unique=False, schema='events')
    op.create_index(None, 'abstract_person_links', ['affiliation_id'], unique=False, schema='event_abstracts')
    op.create_index(None, 'contribution_person_links', ['affiliation_id'], unique=False, schema='events')
    op.create_index(None, 'event_person_links', ['affiliation_id'], unique=False, schema='events')
    op.create_index(None, 'session_block_person_links', ['affiliation_id'], unique=False, schema='events')
    op.create_index(None, 'subcontribution_person_links', ['affiliation_id'], unique=False, schema='events')


def downgrade():
    op.drop_column('subcontribution_person_links', 'affiliation_id', schema='events')
    op.drop_column('session_block_person_links', 'affiliation_id', schema='events')
    op.drop_column('event_person_links', 'affiliation_id', schema='events')
    op.drop_column('contribution_person_links', 'affiliation_id', schema='events')
    op.drop_column('abstract_person_links', 'affiliation_id', schema='event_abstracts')
    op.drop_column('persons', 'affiliation_id', schema='events')
