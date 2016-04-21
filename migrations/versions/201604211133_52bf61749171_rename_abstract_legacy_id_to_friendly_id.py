"""Rename abstract legacy_id to friendly_id

Revision ID: 52bf61749171
Revises: 3ca8e62e6c36
Create Date: 2016-04-21 11:33:06.488466
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '52bf61749171'
down_revision = '3ca8e62e6c36'


def upgrade():
    op.drop_constraint('uq_abstracts_legacy_id_event_id', 'abstracts', schema='event_abstracts')
    op.alter_column('abstracts', 'legacy_id', new_column_name='friendly_id', schema='event_abstracts')
    op.create_unique_constraint(None, 'abstracts', ['friendly_id', 'event_id'], schema='event_abstracts')


def downgrade():
    op.drop_constraint('uq_abstracts_friendly_id_event_id', 'abstracts', schema='event_abstracts')
    op.alter_column('abstracts', 'friendly_id', new_column_name='legacy_id', schema='event_abstracts')
    op.create_unique_constraint(None, 'abstracts', ['legacy_id', 'event_id'], schema='event_abstracts')
