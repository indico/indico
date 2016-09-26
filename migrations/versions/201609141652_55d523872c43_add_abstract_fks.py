"""Add abstract FKs

Revision ID: 55d523872c43
Revises: 7f4d95fd173
Create Date: 2016-09-14 16:52:29.196932
"""

from alembic import context, op


# revision identifiers, used by Alembic.
revision = '55d523872c43'
down_revision = '7f4d95fd173'


def upgrade():
    if not context.is_offline_mode():
        # sanity check to avoid running w/o abstracts migrated
        conn = op.get_bind()
        has_new_abstracts = conn.execute("SELECT EXISTS (SELECT 1 FROM event_abstracts.abstracts)").fetchone()[0]
        has_old_abstracts = (conn.execute("SELECT EXISTS (SELECT 1 FROM event_abstracts.legacy_abstracts)")
                             .fetchone())[0]
        if has_new_abstracts != has_old_abstracts:
            raise Exception('Upgrade to {} and run the event_abstracts zodb import first!'.format(down_revision))
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
