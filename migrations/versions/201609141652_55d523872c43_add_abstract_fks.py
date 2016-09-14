"""Add abstract FKs

Revision ID: 55d523872c43
Revises: 2ce1756a2f12
Create Date: 2016-09-14 16:52:29.196932
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '55d523872c43'
down_revision = '2ce1756a2f12'


def upgrade():
    op.create_foreign_key(None,
                          'abstract_field_values', 'abstracts',
                          ['abstract_id'], ['id'],
                          source_schema='event_abstracts', referent_schema='event_abstracts')
    op.create_foreign_key(None,
                          'contributions', 'abstracts',
                          ['abstract_id'], ['id'],
                          source_schema='events', referent_schema='event_abstracts')


def downgrade():
    op.drop_constraint('fk_contributions_abstract_id_abstracts', 'contributions', schema='events')
    op.drop_constraint('fk_abstract_field_values_abstract_id_abstracts', 'abstract_field_values',
                       schema='event_abstracts')
