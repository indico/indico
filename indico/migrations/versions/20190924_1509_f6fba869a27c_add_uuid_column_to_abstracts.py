"""Add uuid column to event_abstracts.abstracts

Revision ID: f6fba869a27c
Revises: 0f20a5e4018e
Create Date: 2019-09-04 15:09:33.244329
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'f6fba869a27c'
down_revision = '0f20a5e4018e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('abstracts', sa.Column('uuid', postgresql.UUID(), nullable=True), schema='event_abstracts')
    op.create_index(None, 'abstracts', ['uuid'], unique=True, schema='event_abstracts')
    op.create_check_constraint('uuid_if_invited', 'abstracts', '(state != 7) OR (uuid IS NOT NULL)',
                               schema='event_abstracts')


def downgrade():
    op.drop_constraint('ck_abstracts_uuid_if_invited', 'abstracts', schema='event_abstracts')
    op.drop_column('abstracts', 'uuid', schema='event_abstracts')
