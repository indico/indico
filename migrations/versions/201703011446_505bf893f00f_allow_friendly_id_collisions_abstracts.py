"""Allow friendly_id collisions with deleted abstracts

Revision ID: 505bf893f00f
Revises: fb7b6aa148e
Create Date: 2017-03-01 14:46:22.996234
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '505bf893f00f'
down_revision = 'fb7b6aa148e'


def upgrade():
    op.drop_constraint('uq_abstracts_friendly_id_event_id', 'abstracts', schema='event_abstracts')
    op.create_index(None, 'abstracts', ['friendly_id', 'event_id'], unique=True,
                    postgresql_where=sa.text('NOT is_deleted'), schema='event_abstracts')


def downgrade():
    op.drop_index('ix_uq_abstracts_friendly_id_event_id', table_name='abstracts', schema='event_abstracts')
    op.create_unique_constraint(None, 'abstracts', ['friendly_id', 'event_id'], schema='event_abstracts')
